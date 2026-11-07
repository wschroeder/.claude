# Routes, endpoints, and credentials

Read this file now, before Pass 1, when the diff adds or changes a route, an endpoint, or a request handler, or mints or consumes a credential. Walk 1.15a-e when the diff mints or consumes a credential, 1.16 when it keys a bucket or audit row by client identity, and 1.17-1.18 when it migrates many call sites or branches on a role.

## Contents

- 1.15 Mint → consume seam (cross-endpoint credential contract)
- 1.16 Network-identifier source-of-truth (IP-keyed bucket integrity)
- 1.17 Mass-migration coverage
- 1.18 Role-discriminator twin check
- 2.3 Defense-in-depth in isolation
- 2.9 Identifier parse/comparison asymmetry
- 2.10 Trigger-vs-precondition ordering
- 5.1 Sibling-endpoint consistency
- 5.10 CORS preflight for browser-callable endpoints

Each angle below belongs to the pass its number names. Walk it in that pass, give it a disposition, and print its line in the Checklist under that pass.

## Checklist lines

```
Pass 1:
Pass 2:
  2.3   Defense-in-depth in isolation    boundary guards independent of caller;
                                          "the page always sends it" drops nothing
                                          proof: post the request without the
                                          field and quote what the server answers
  2.9   Identifier parse/comparison      .startsWith vs .origin; case folding
  2.10  Trigger-vs-precondition order    cheap filter before side-effecting mint
Pass 5:
  5.1   Sibling-endpoint conventions     param source / auth scheme / response /
                                          error vocabulary; same helpers
  5.10  CORS preflight                   OPTIONS on browser-callable endpoints
```

### 1.15 Mint → consume seam (cross-endpoint credential contract)

For every artifact the diff ISSUES — access tokens, refresh tokens, signed URLs, magic links, session keys, API keys, password reset codes, JWT, OTP, presigned upload URLs, anything verifiable — locate the endpoint(s) that CONSUME it and verify the consumer can accept what the issuer produces. This is a system-level invariant the other passes miss because the issuer and consumer are usually different files/functions with no direct call edge.

**Issuer grep patterns:** `mint_*`, `create_token`, `issue_*`, `generate_*`, `sign_*`, `Phoenix.Token.sign`, `Plug.Crypto.sign`, `Joken.generate_and_sign`, presigned-URL helpers, `:crypto.strong_rand_bytes` followed by storage.

**Consumer grep patterns:** `verify_*`, `validate_*`, `decode_*`, `authenticate_*`, `check_*`, `Phoenix.Token.verify`, `*.exchange`, `*.refresh`, `*.consume`.

#### 1.15a Authentication asymmetry

Issuer mints credential X, but consumer requires auth method Y that issuer's clients don't have. *Worked example:* `/oauth/token` mints `refresh_token` for every successful exchange, including PKCE/public clients with no `client_secret`; `/oauth/refresh` requires `client_secret`. PKCE clients receive a refresh token they can never use → silent hard expiry at first access-token rollover. Either suppress issuance for the weaker class (`use_refresh_token: false` for PKCE) or accept the weaker class at the consumer; pick one.

#### 1.15b Scope asymmetry

Issuer grants scopes the consumer's authorization layer doesn't enforce. Token has `scope:admin` but the resolver only checks `current_user.is_admin`. Scope is decorative, not load-bearing.

#### 1.15c Lifecycle asymmetry

Issuer's TTL doesn't match the consumer's expiry check. Signed URL minted with 24h TTL but verifier checks `created_at + 1h`; presigned upload valid for 7d but caller throws away the URL after 1h.

#### 1.15d Revocation asymmetry

Issuer mints something durable, but no consumer-side revocation check. API key minted, no `is_active` filter on the auth lookup; refresh chain rotated, no descendant-revocation walk.

#### 1.15e Verifier missing

Issuer signs/encrypts, but no consumer reads the signature. Signed cookie issued, cookie reader trusts the body without verification.

### 1.16 Network-identifier source-of-truth (IP-keyed bucket integrity)

Whenever the diff uses a network identifier as a SECURITY or FAIRNESS key — rate-limit bucket, abuse counter, IDS fingerprint, idempotency salt, audit trail, geofence allowlist, anti-CSRF binding, ABAC subject IP — verify the value is the REAL client identifier under the deployment topology, not the load balancer's IP.

**Grep targets:** `conn.remote_ip`, `request.remote_ip`, `socket.remote_ip`, `req.ip`, `request.client_ip`, `getClientIp`, raw `x-real-ip` / `x-forwarded-for` reads, `RemoteAddr`, `HttpContext.Connection.RemoteIpAddress`.

Behind ALB / CloudFront / Cloudflare / nginx / GCLB / Envoy / Traefik, the raw socket IP is the LB's private address unless an upstream plug parses `X-Forwarded-For` against a trusted-proxy list (`Plug.RemoteIp` in Elixir, `app.set('trust proxy', ...)` in Express, `UseForwardedHeaders` in ASP.NET, `RealIPFrom`/`set_real_ip_from` in nginx).

**Bucket collapse failure mode:** every client behind the LB shares one bucket — one noisy client 429s everyone; one attacker burns shared quota for all peers; per-IP audit logs all attribute to the LB.

Spoof-resistance requires RIGHTMOST-untrusted XFF walking with a trust precondition that `conn.remote_ip` is itself a trusted proxy — leftmost is attacker-controllable because most proxies (including ALB) APPEND to existing XFF rather than replace.

A new rate-limit / throttle / abuse-prevention plug whose key is `conn.remote_ip` (or equivalent) WITHOUT an upstream `Plug.RemoteIp` mounted, AND without in-plug XFF parsing, is Fix-class — improves security AND fairness. **Discovery shape:** grep for the rate-limiter primitive (`Hammer`, `ExRated`, `:limiter`, `rateLimit`, custom counters) and trace one call hop back to find the bucket key derivation. If the derivation is bare `remote_ip`, look upstream for the trusted-proxy plug; absent, flag.

### 1.17 Mass-migration coverage

When a diff replaces N call sites of a pre-existing primitive (raw `fetch` → `authedFetch`, raw query → context function, manual logging → structured logger, etc.), each migrated site receives at least one Pass 2 (adversarial) and one Pass 4 (correctness) attempt. A blanket review of the wrapper does not cover per-site hazards the wrapper can't catch — env-var guards in the caller, local nil handling, inherited dead code, template-literal interpolation, off-by-one slice sizes. Enumerate the migrated sites up front; check each one.

### 1.18 Role-discriminator twin check

When the diff adds or modifies a guard inside one branch of an `if (role === X)` / `case role` / role-typed discriminator (typed roles like `UserRole.SCHOOL_ADMIN`, `UserRole.DISTRICT_ADMIN`, `:teacher` / `:admin`, tenant scopes, ABAC subject classes), enumerate EVERY OTHER BRANCH on the same discriminator. Each twin must:
- **(a)** carry the equivalent guard, OR
- **(b)** be admitted by a separate guard that's at least as strict, OR
- **(c)** carry an in-source justification that names the threat model under which the asymmetry is safe.

An admit comment that punts to "the UI scopes implicitly" / "their admin surface is scoped" / "the read-side filter hides it" is NOT (c) — UI scope is not server-side scope, and a read-side filter on the actor's own page is not authz for a sibling DA's page. Per Pass 2 Defense-in-depth, the function boundary owns its own check.

The asymmetric branch is a Fix-class server-side authz finding when (a)/(b)/(c) all miss.

**Discovery method:** for every `if (...role === ...)` or `switch (role)` introduced or modified, mechanically list each branch's authz/scope/validation surface in a 2-column table (branch, guards-present); a row with fewer guards than its siblings is the finding.

### 2.3 Defense-in-depth in isolation

Read each new/changed function assuming an UNTRUSTED caller — not the nice caller you're reviewing. If the function relies on "my caller validated X before calling me," grep every live caller to verify. More importantly, guard at the function boundary too. Any future refactor can break the caller's validation without touching this function; the boundary guard is insurance.

A function that returns `:ok` for a sentinel (e.g., "no challenge stored → pass") is fail-safe only if a sibling function in the call chain still enforces authentication; if that sibling is ever loosened, the sentinel becomes a fail-open.

"The page always sends it" is not a reason to drop a finding, and neither is a guard further down that still refuses the worst case. Anyone can post the request without the field. Post it that way, through the route, and quote what the server answers. The proof is that answer, not a reading of the form.

Measured (2026-10-22): `downloadBundle` skipped its changed-since-preview check when `previewedKey` was absent. Our review dropped it twice: once because the bar's Download button only posts to the preview, and once because the server still refused blocked files. A request with no key downloaded whatever the selection held at that moment, without the preview the spec requires. The outside reviewer found it, and the fix made the key required and answered 409 with the current preview.

### 2.9 Identifier parse/comparison asymmetry

When code compares a parsed URL/path/header/token component against an allowlist, name the components the parser strips. Does the stripped piece matter for security?

For URL authz:
- **`.host`** strips scheme (http-downgrade bypass)
- **`.hostname`** strips port (port-hopping)
- **`.pathname`** strips query (acl bypass)
- The correct primitive for scoping bearer/cookie delivery is **`.origin`** (scheme+host+port)

Apply the same reasoning to:
- Path allowlists (normalization: trailing slash, `../`, `%2e%2e`)
- Header comparisons (case folding, whitespace)
- Secret/token comparisons (constant-time vs `===`)

The `.startsWith(issuer)` URL-comparison is the canonical anti-pattern — `https://app.example.com.evil.tld` passes a prefix check against `https://app.example.com`. Use `URL.origin` compare with try/catch on parse failure.

### 2.10 Trigger-vs-precondition ordering

For any check in a `with` chain (or imperative sequence) whose failure has a SIDE EFFECT — writes a row, sends a notification, kills sessions, revokes other state, increments a breach counter, broadcasts an event, **mints or rotates a single-use credential** — verify natural-flow filters that should reject benign cases run FIRST. The side-effecting check must never see input it didn't need to act on.

**Concrete shapes:**

- **Elixir/Phoenix:** if `ensure_not_revoked/1` triggers chain revocation when descendants exist, and `ensure_refresh_window_open/1` rejects expired tokens, then `ensure_refresh_window_open` MUST come before `ensure_not_revoked` — otherwise a replayed expired token from a legitimate user reaches the revocation trigger and DoS's the user via a benign-cause path.

- **Credential mint before authorization / quota / allowance:** an entrypoint that performs `getValidUserToken(userId)` (which rotates a single-use refresh token at the IdP), `presignS3Url(...)` (which produces a durable URL), `createStripeCustomer(...)` (which provisions a billable artifact), or any other side-effecting mint BEFORE the request's authorization, quota, allowance, or anti-abuse checks pass. A denied request that has already minted credentials has burned a rotation, polluted an audit log, or produced a usable artifact for a caller who should not have been allowed past the gate. Fix: reorder cheap filters first (request-shape, auth/identity), authorization next, quota/allowance next, side-effecting mints last.

- **Webhook handler that emits an outbound call before signature verification:** any code that fires an idempotency event, audits a request, or notifies a downstream system before the inbound signature is verified leaks abuse-burst potential. Verify the signature first; side-effect after.

Enumerate every step in the chain by side-effect-class; non-side-effecting filters always precede side-effecting triggers. If two side-effecting triggers must coexist, document the ordering invariant inline. Flag any reordering of an existing chain that moves a trigger ahead of a filter, AND any new entrypoint that introduces a side-effecting trigger above an existing filter wall.

### 5.1 Sibling-endpoint consistency

When the diff adds a new public action (controller action, route, GraphQL resolver, RPC handler) to a module that ALREADY has sibling actions of the same shape (e.g. `/oauth/refresh` and `/oauth/revoke` joining `/oauth/token`), enumerate the conventions the existing siblings establish before the new one is reviewed:

- **Parameter source** — body params vs query params vs header params; multipart vs JSON; `conn.body_params` vs `conn.query_params` vs `get_req_header/2`. New siblings must consume params the same way unless an explicit reason exists.
- **Auth scheme** — Basic vs Bearer vs HMAC vs no-auth; which plug pipeline is mounted; which fields the auth helper extracts. A new endpoint mounted on a different pipeline than its siblings is a maintainability and DX bug — clients reusing their auth pattern from one endpoint break on the other. Auth scheme also covers in-action behavior, not just pipeline mounting: if a sibling action calls a helper to merge Basic-header credentials into params (`merge_basic_auth_credentials`, `extract_bearer`, `parse_jwt_header`), the new action MUST call the same helper. Mounting the same pipeline does NOT propagate the helper call — it must be invoked explicitly inside each action body.
- **Response shape** — top-level keys (`{access_token, refresh_token, expires_in}`), success status codes (200 vs 201 vs 204), encoding (JSON vs form-encoded), header conventions (`Cache-Control`, `Pragma`).
- **Error vocabulary** — RFC 6749 error codes (`invalid_grant`, `invalid_client`), HTTP status mapping, error body shape (`{error, error_description}` vs `{errors: [...]}` vs `{message}`). Sibling endpoints that emit different error shapes for the same failure class force every client to branch.
- **Helper functions called** — same `validate_*`, `authorize_*`, `audit_*` helpers as siblings; not a parallel reimplementation.

List the siblings' conventions explicitly before classifying findings; an unjustified deviation is a Fix-class maintainability finding (per the "yes to any" gate).

### 5.10 CORS preflight for browser-callable endpoints

For any new POST/PUT/DELETE endpoint added to a scope that may be called from a browser (auth flows, public APIs, OAuth endpoints), enumerate how OPTIONS preflight is handled. Three valid patterns:

1. Endpoint-level CORS plug that intercepts OPTIONS before routing (e.g., `MyAppWeb.Plug.OAuthCORS` mounted in `endpoint.ex`)
2. Explicit `options "/path", CorsController, :noop` route in a cors-only scope
3. Corsica plug with `allow_methods: :all` mounted in the scope's pipeline

Verify ONE of these covers the new endpoint; do NOT assume the parent scope's `:cors` pipeline auto-handles OPTIONS. RFC 9700 (OAuth 2.0 for Browser-Based Apps) recommends CORS support on token endpoints for SPA clients using authorization-code + PKCE.
