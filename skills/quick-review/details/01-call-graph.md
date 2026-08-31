# Pass 1 — Call-graph and seam analysis

Discovery methods and worked examples for the named angles in SKILL.md Pass 1. The AI Reads this file when working through Pass 1; angle numbering matches SKILL.md.

## 1.1 Schema-query alignment (index coverage)

For every new `where`, `order_by`, `join … on`, raw SQL filter, or Ecto preload-with-where introduced by the diff, identify the column(s) being filtered or sorted. Search the migrations directory for a `create index`, `create unique_index`, or schema-level `@index` covering those column(s). If the column lacks an index AND the query is on a hot path (request-handling, breach response, billing, auth, refresh-token lookup, session validation), flag as both PERF and SEC — slow breach response IS a security concern (e.g., a refresh-token-reuse detection query that scans the table cannot meet its design SLA).

For composite filters (`WHERE a = ? AND b = ?`), a single-column index on the lower-cardinality column is usually inadequate; require a composite index or document why.

Always-required: a NEW lookup column on a NEW or pre-existing hot table needs an index in the SAME migration that introduces the column or query, not "a follow-up."

## 1.2 Query consistency

When new code queries a table/schema, grep for all other queries on that same table for the same logical entity (e.g., same ID field). Compare WHERE clauses. If another function uses a broader or different lookup (e.g., `field_a OR field_b`), the new query must account for the same cases or explain why not.

## 1.3 Return-value assumptions (recovered-error checkpoints are not terminal)

For each new private function, trace its return value through at least 3 caller levels. What does the caller do with the result? What does the caller's caller assume was filtered or transformed? Does the new function's contract satisfy those assumptions?

**Recovered-error checkpoints are not terminal.** A handler returning `:ok` on a recovered error path (race, unique-constraint violation, retry-exhausted, not-found fallback) is NOT the end of the trace — it is a checkpoint. Continue tracing until the terminal side effect (DB write, API response, token minted, redirect emitted). The invariant to prove is that the terminal side effect matches the persisted state, not that the handler returned a success tuple.

When you see `case some_fallible_call() do :ok -> ...; :already_exists -> :ok end`, ask: does the next step operate on the CALLER's intended payload or on the STORED payload? If the former, the race has decoupled "what the user agreed to" from "what the DB says they agreed to" — a silent integrity break.

## 1.4 Handoff completeness

When new code produces output later consumed by unchanged code, read the unchanged consumer. Does the new code's output cover all cases the consumer expects? Pay special attention to `Repo.one()` downstream — if it can match on multiple criteria, the upstream filter must exclude on all those criteria.

## 1.5 Spec contract changes

For any function whose `@spec`, return type, or error shape changed in the diff, grep the codebase for all call sites. Verify each caller handles the new return shape — especially callers in files not touched by the diff. A function that previously returned `:noop` and now returns `{:ok, _} | {:error, _}` has changed its contract; every consumer must be checked.

## 1.6 Extracted-but-not-forwarded

For each value extracted, parsed, or created in a function within the diff (params, decoded fields, API response values, IDs), trace it forward through every downstream function call in the diff. If function A extracts `promo_code` from params but function B (called later in the chain) does not receive it in its arguments, flag it. The trace must follow the full call chain, not just the immediate caller — a value lost at hop 2 of 4 is invisible without end-to-end tracing.

## 1.7 New fields not threaded

When a function adds a new key to a map/struct or a new parameter to its signature, check every call site within the diff that invokes downstream functions. If the downstream function's signature or pattern match does not include the new field, it is silently dropped. This includes pipeline stages where a map is built up and then passed to a function that only destructures known keys.

## 1.8 Filter-dimension gaps

When new code queries with specific filters (e.g., `WHERE status = 'active'`), and the result feeds into a function that queries the same entity with additional filter dimensions (e.g., also filtering by `org_id`), the upstream query must include all dimensions the downstream consumer assumes were already applied. Read the downstream function to identify its assumptions.

## 1.9 Control-flow coupling of independent side effects

When two independent operations (e.g., writing an audit log + sending a notification) share a `case`/`if` branch with no data dependency between them, one's failure suppresses the other. If neither operation consumes the other's output, they should not be gated by the same branch — separate them so each can fail independently.

## 1.10 Behavioral regression

For every touched function with pre-existing callers, compare the new return/side-effect to what the old code produced. Read the pre-change version with `git show <base>:<path>`, not just the new tests. If the new behavior differs from what the old call patterns yielded, either that's the bug the author intentionally fixed (the PR body should say so) or it's an unintended regression.

Silent contract changes are the most expensive class of review miss: a function that used to merge two inputs and now only returns one is a regression, but tests pass because they were written against the new shape.

## 1.11 Documented-placeholder behavior is itself a finding

When a function or branch in the diff carries a comment that describes intentionally-broken-pending-followup behavior — "silent zero-row", "always returns false until P6.5", "Q1=A interim", "no-op until X lands", "placeholder until the column re-keys" — treat the placeholder as a finding to surface. The deviation is NOT the diff drifting from the placeholder's claim; the deviation is the placeholder's existence in production code.

Three valid paths, pick one:
- **(a) Hide behind a feature flag** so the placeholder can't fire for real users.
- **(b) Replace with an actionable error** that tells the user what's happening (`503 "Imports are temporarily unavailable while we migrate identity sources"` beats a silently-empty list).
- **(c) Document the visible impact** in the user-facing empty state ("DAs may see no imports until the identity migration completes — see <link>") so the placeholder's UX surface is honest.

A silent placeholder that compiles to misleading UX is Fix-class regardless of how well-documented it is in the source. The "Author-acknowledged deviation is not exempt" rule handles the in-source comment side; this rule handles the user-facing UX side. A row that's in the DB but not in the UI is a bug from the user's perspective, even if the comment says so.

## 1.12 Closure lexical capture vs accumulator threading

In `Enum.reduce`, `Stream.transform`, fold-like functions, or any higher-order function that takes an accumulator + closure: variables referenced inside the closure that come from the OUTER scope are captured at closure-creation time, not threaded across iterations. If the outer-scope value carries intent that should accumulate (a `MapSet` of seen items, a counter, a running sum), it must live in the ACCUMULATOR, not just the lexical capture.

Concrete failure shape: `Enum.reduce(items, count, fn x, acc -> walk(x, seen, acc) end)` — `seen` is captured fresh per iteration; updates inside `walk` do not propagate to the next sibling. Fix: change accumulator to `{seen, count}` and destructure in the closure (`fn x, {seen, acc} -> ... end`).

Comment audit pair: if a comment claims the guard "accumulates across the whole walk" but the accumulator type doesn't match, that's comment/code drift — flag both.

## 1.13 Magic constant aligned to configurable parameter

When a function or plug exposes a numeric parameter via `init/1` opts, function args, or module attributes (`@scale_ms 60_000`, `init: [scale_ms: 60_000]`, `def f(opts)`), scan its body for any literal value that's mathematically derivable from that parameter. If a related response value (a `Retry-After: "60"` header, a `cache-control: max-age=60` directive, an inline log line claiming "60s", a documented timeout, an emitted metric) is hardcoded but represents the SAME quantity in different units, the literal is a regression timer — correct today only because every caller happens to pass the matching value.

Replace with a derivation: `Integer.to_string(div(scale_ms, 1000))` for ms→s, `to_string(scale_ms)` when units already match.

Examples to flag: `Retry-After` header next to a `scale_ms` opt, `expires_in: 3600` next to a `ttl_seconds` config, `Cache-Control: max-age=N` next to a `:cache_ttl` arg. The deletion test: if you change the param, does the literal still describe the truth? If no, derive it.

## 1.14 Time-window ceiling (round up, never truncate)

Time-derived integer headers and fields — `Retry-After`, `Cache-Control: max-age=`, `expires_in`, `crl-next-update`, any "seconds until X" value — must round UP to the full window, not truncate. `div(scale_ms, 1000)` is the wrong primitive when `scale_ms` is not a clean multiple of 1000: for `scale_ms = 1500`, `div(1500, 1000) = 1`, but the bucket is still active for another 0.5s. A client honoring `Retry-After: 1` retries at t=1.0s and gets denied again — the header lied.

Use ceiling division: `div(scale_ms + 999, 1000)` for ms→s, or the language-equivalent (`Math.ceil` in JS, `(x + n - 1) / n` in any int-only system).

The deletion test: change the configurable param so it's NOT a multiple of the unit (e.g., `scale_ms: 1500`). Does the emitted header still describe the truth? Under-reporting causes early retries (rate-limit thundering); over-reporting causes unnecessary delays. Round up is the safe direction for retry/expiry; round down for "you have at most N" budgets.

## 1.15 Mint → consume seam (cross-endpoint credential contract)

For every artifact the diff ISSUES — access tokens, refresh tokens, signed URLs, magic links, session keys, API keys, password reset codes, JWT, OTP, presigned upload URLs, anything verifiable — locate the endpoint(s) that CONSUME it and verify the consumer can accept what the issuer produces. This is a system-level invariant the other passes miss because the issuer and consumer are usually different files/functions with no direct call edge.

**Issuer grep patterns:** `mint_*`, `create_token`, `issue_*`, `generate_*`, `sign_*`, `Phoenix.Token.sign`, `Plug.Crypto.sign`, `Joken.generate_and_sign`, presigned-URL helpers, `:crypto.strong_rand_bytes` followed by storage.

**Consumer grep patterns:** `verify_*`, `validate_*`, `decode_*`, `authenticate_*`, `check_*`, `Phoenix.Token.verify`, `*.exchange`, `*.refresh`, `*.consume`.

### 1.15a Authentication asymmetry

Issuer mints credential X, but consumer requires auth method Y that issuer's clients don't have. *Worked example:* `/oauth/token` mints `refresh_token` for every successful exchange, including PKCE/public clients with no `client_secret`; `/oauth/refresh` requires `client_secret`. PKCE clients receive a refresh token they can never use → silent hard expiry at first access-token rollover. Either suppress issuance for the weaker class (`use_refresh_token: false` for PKCE) or accept the weaker class at the consumer; pick one.

### 1.15b Scope asymmetry

Issuer grants scopes the consumer's authorization layer doesn't enforce. Token has `scope:admin` but the resolver only checks `current_user.is_admin`. Scope is decorative, not load-bearing.

### 1.15c Lifecycle asymmetry

Issuer's TTL doesn't match the consumer's expiry check. Signed URL minted with 24h TTL but verifier checks `created_at + 1h`; presigned upload valid for 7d but caller throws away the URL after 1h.

### 1.15d Revocation asymmetry

Issuer mints something durable, but no consumer-side revocation check. API key minted, no `is_active` filter on the auth lookup; refresh chain rotated, no descendant-revocation walk.

### 1.15e Verifier missing

Issuer signs/encrypts, but no consumer reads the signature. Signed cookie issued, cookie reader trusts the body without verification.

## 1.16 Network-identifier source-of-truth (IP-keyed bucket integrity)

Whenever the diff uses a network identifier as a SECURITY or FAIRNESS key — rate-limit bucket, abuse counter, IDS fingerprint, idempotency salt, audit trail, geofence allowlist, anti-CSRF binding, ABAC subject IP — verify the value is the REAL client identifier under the deployment topology, not the load balancer's IP.

**Grep targets:** `conn.remote_ip`, `request.remote_ip`, `socket.remote_ip`, `req.ip`, `request.client_ip`, `getClientIp`, raw `x-real-ip` / `x-forwarded-for` reads, `RemoteAddr`, `HttpContext.Connection.RemoteIpAddress`.

Behind ALB / CloudFront / Cloudflare / nginx / GCLB / Envoy / Traefik, the raw socket IP is the LB's private address unless an upstream plug parses `X-Forwarded-For` against a trusted-proxy list (`Plug.RemoteIp` in Elixir, `app.set('trust proxy', ...)` in Express, `UseForwardedHeaders` in ASP.NET, `RealIPFrom`/`set_real_ip_from` in nginx).

**Bucket collapse failure mode:** every client behind the LB shares one bucket — one noisy client 429s everyone; one attacker burns shared quota for all peers; per-IP audit logs all attribute to the LB.

Spoof-resistance requires RIGHTMOST-untrusted XFF walking with a trust precondition that `conn.remote_ip` is itself a trusted proxy — leftmost is attacker-controllable because most proxies (including ALB) APPEND to existing XFF rather than replace.

A new rate-limit / throttle / abuse-prevention plug whose key is `conn.remote_ip` (or equivalent) WITHOUT an upstream `Plug.RemoteIp` mounted, AND without in-plug XFF parsing, is Fix-class — improves security AND fairness. **Discovery shape:** grep for the rate-limiter primitive (`Hammer`, `ExRated`, `:limiter`, `rateLimit`, custom counters) and trace one call hop back to find the bucket key derivation. If the derivation is bare `remote_ip`, look upstream for the trusted-proxy plug; absent, flag.

## 1.17 Mass-migration coverage

When a diff replaces N call sites of a pre-existing primitive (raw `fetch` → `authedFetch`, raw query → context function, manual logging → structured logger, etc.), each migrated site receives at least one Pass 2 (adversarial) and one Pass 4 (correctness) attempt. A blanket review of the wrapper does not cover per-site hazards the wrapper can't catch — env-var guards in the caller, local nil handling, inherited dead code, template-literal interpolation, off-by-one slice sizes. Enumerate the migrated sites up front; check each one.

## 1.18 Role-discriminator twin check

When the diff adds or modifies a guard inside one branch of an `if (role === X)` / `case role` / role-typed discriminator (typed roles like `UserRole.SCHOOL_ADMIN`, `UserRole.DISTRICT_ADMIN`, `:teacher` / `:admin`, tenant scopes, ABAC subject classes), enumerate EVERY OTHER BRANCH on the same discriminator. Each twin must:
- **(a)** carry the equivalent guard, OR
- **(b)** be admitted by a separate guard that's at least as strict, OR
- **(c)** carry an in-source justification that names the threat model under which the asymmetry is safe.

An admit comment that punts to "the UI scopes implicitly" / "their admin surface is scoped" / "the read-side filter hides it" is NOT (c) — UI scope is not server-side scope, and a read-side filter on the actor's own page is not authz for a sibling DA's page. Per Pass 2 Defense-in-depth, the function boundary owns its own check.

The asymmetric branch is a Fix-class server-side authz finding when (a)/(b)/(c) all miss.

**Discovery method:** for every `if (...role === ...)` or `switch (role)` introduced or modified, mechanically list each branch's authz/scope/validation surface in a 2-column table (branch, guards-present); a row with fewer guards than its siblings is the finding.
