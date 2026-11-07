# Routes, endpoints, and credentials

1. Read this file now, before Pass 1, when the diff adds or changes a route, an endpoint, or a request handler, or mints or consumes a credential.
2. Walk 1.15a-e when the diff mints or consumes a credential, 1.16 when it keys a bucket or audit row by client identity, and 1.17-1.18 when it migrates many call sites or branches on a role.

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

3. Walk each angle below in the pass its number names, give it a disposition, and print its line in the Checklist under that pass.

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

1. For every artifact the diff issues, such as an access or refresh token, a signed or presigned URL, a magic link, a session or API key, a reset code, a JWT, or an OTP, find the endpoints that consume it and check that each consumer accepts what the issuer produces.
2. Find issuers with `mint_*`, `create_token`, `issue_*`, `generate_*`, `sign_*`, `Phoenix.Token.sign`, `Plug.Crypto.sign`, `Joken.generate_and_sign`, presigned-URL helpers, and `:crypto.strong_rand_bytes` followed by storage.
3. Find consumers with `verify_*`, `validate_*`, `decode_*`, `authenticate_*`, `check_*`, `Phoenix.Token.verify`, `*.exchange`, `*.refresh`, and `*.consume`.

#### 1.15a Authentication asymmetry

1. Flag an issuer that mints a credential for a client class, such as a PKCE client with no `client_secret`, whose consumer demands an auth method that class lacks.
2. Fix it by suppressing issuance for the weaker class or accepting it at the consumer, choosing one.

#### 1.15b Scope asymmetry

1. Flag a scope the issuer grants that the consumer's authorization layer never checks.

#### 1.15c Lifecycle asymmetry

1. Flag an issuer TTL that differs from the consumer's expiry check.

#### 1.15d Revocation asymmetry

1. Flag a durable credential whose consumer has no revocation check, such as an API-key lookup with no `is_active` filter or a rotated refresh chain with no descendant-revocation walk.

#### 1.15e Verifier missing

1. Flag a signed or encrypted artifact whose reader trusts the body without verifying it.

### 1.16 Network-identifier source-of-truth (IP-keyed bucket integrity)

1. Wherever the diff uses a network identifier as a security or fairness key, such as a rate-limit bucket, an abuse counter, an idempotency salt, an audit trail, an allowlist, or an anti-CSRF binding, check that the value is the real client address under the deployment topology, not the load balancer's.
2. Grep `conn.remote_ip`, `request.remote_ip`, `socket.remote_ip`, `req.ip`, `request.client_ip`, `getClientIp`, raw `x-real-ip` / `x-forwarded-for` reads, `RemoteAddr`, and `HttpContext.Connection.RemoteIpAddress`.
3. Behind a load balancer or proxy, require an upstream trusted-proxy parser of `X-Forwarded-For`, such as `Plug.RemoteIp` in Elixir, `app.set('trust proxy', ...)` in Express, `UseForwardedHeaders` in ASP.NET, or `set_real_ip_from` in nginx.
4. Require the parser to walk `X-Forwarded-For` from the rightmost untrusted entry, with a precondition that `conn.remote_ip` is itself a trusted proxy, because the leftmost entry is attacker-controlled.
5. Find each rate limiter, such as `Hammer`, `ExRated`, `:limiter`, `rateLimit`, or a custom counter, trace one hop back to its bucket key, and if the key is bare `remote_ip` with no upstream trusted-proxy plug and no in-plug parsing, then rate it Fix-class.

### 1.17 Mass-migration coverage

1. When a diff replaces many call sites of an existing primitive, such as raw `fetch` with `authedFetch`, list the migrated sites up front and give each at least one Pass 2 and one Pass 4 attempt, because a review of the wrapper misses per-site hazards.

### 1.18 Role-discriminator twin check

1. When the diff adds or changes a guard inside one branch of a role discriminator, such as `if (role === X)`, `case role`, a typed role enum, a tenant scope, or an ABAC subject class, list every other branch on the same discriminator.
2. Require each twin to:
- **(a)** carry the equivalent guard, OR
- **(b)** be admitted by a separate guard that's at least as strict, OR
- **(c)** carry an in-source justification that names the threat model under which the asymmetry is safe.
3. Never accept "the UI scopes it" or a read-side filter as (c).
4. Rate a branch that misses (a), (b), and (c) a Fix-class server-side authorization finding.
5. For each such discriminator, list each branch's authorization, scope, and validation guards side by side, and report the branch with fewer guards than its siblings.

### 2.3 Defense-in-depth in isolation

1. Read each new or changed function as if an untrusted caller calls it, grep every live caller for any validation it relies on, and guard at the function boundary too.
2. Flag a function that passes on a sentinel, such as "no challenge stored", unless a sibling in the call chain still enforces authentication.
3. Never drop a finding because "the page always sends it" or because a guard further down refuses the worst case: post the request without the field, through the route, and quote what the server answers.

### 2.9 Identifier parse/comparison asymmetry

1. When code compares a parsed URL, path, header, or token component against an allowlist, name the components the parser strips and decide whether each matters for security.
2. For URL authz:
- **`.host`** strips scheme (http-downgrade bypass)
- **`.hostname`** strips port (port-hopping)
- **`.pathname`** strips query (acl bypass)
- The correct primitive for scoping bearer/cookie delivery is **`.origin`** (scheme+host+port)
3. Apply the same reasoning to:
- Path allowlists (normalization: trailing slash, `../`, `%2e%2e`)
- Header comparisons (case folding, whitespace)
- Secret/token comparisons (constant-time vs `===`)
4. Flag a `.startsWith(issuer)` URL comparison, and compare `URL.origin` with a try/catch on parse failure instead.

### 2.10 Trigger-vs-precondition ordering

1. For any check whose failure has a side effect, such as writing a row, notifying, killing sessions, revoking state, counting a breach, broadcasting, or minting or rotating a single-use credential, check that the filters rejecting benign cases run first.
2. Order an entrypoint's steps as cheap filters first (request shape, identity), then authorization, then quota and allowance, and side-effecting mints last.
3. Verify an inbound webhook signature before any outbound call, audit, or notification.
4. If two side-effecting triggers must coexist, then require a comment stating the ordering rule.
5. Flag any reordering that moves a trigger ahead of a filter, and any new entrypoint that adds a side-effecting trigger above an existing filter.

### 5.1 Sibling-endpoint consistency

1. When the diff adds a public action, such as a controller action, route, GraphQL resolver, or RPC handler, to a module that already has siblings of the same shape, list the siblings' conventions before reviewing the new one:
- **Parameter source** — body, query, or header params; multipart or JSON.
- **Auth scheme** — which pipeline is mounted and which fields the auth helper extracts, and any helper a sibling calls inside the action body, such as `merge_basic_auth_credentials`, which the new action must call explicitly too.
- **Response shape** — top-level keys, success status codes, encoding, and header conventions such as `Cache-Control` and `Pragma`.
- **Error vocabulary** — error codes such as RFC 6749's `invalid_grant` and `invalid_client`, the HTTP status mapping, and the error body shape.
- **Helper functions called** — same `validate_*`, `authorize_*`, `audit_*` helpers as siblings; not a parallel reimplementation.
2. Rate an unjustified deviation a Fix-class maintainability finding under the Yes-to-any gate.

### 5.10 CORS preflight for browser-callable endpoints

1. For any new POST, PUT, or DELETE endpoint a browser may call, such as an auth flow, a public API, or an OAuth endpoint, check that one of these handles OPTIONS preflight:

1. Endpoint-level CORS plug that intercepts OPTIONS before routing (e.g., `MyAppWeb.Plug.OAuthCORS` mounted in `endpoint.ex`)
2. Explicit `options "/path", CorsController, :noop` route in a cors-only scope
3. Corsica plug with `allow_methods: :all` mounted in the scope's pipeline

2. Never assume the parent scope's `:cors` pipeline handles OPTIONS.
3. Support CORS on token endpoints for single-page apps using authorization code with PKCE, as RFC 9700 recommends.
