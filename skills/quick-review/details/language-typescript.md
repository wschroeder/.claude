# Language — TypeScript / JavaScript / Node

Read this file now, before Pass 1, when the diff touches a `.ts`, `.tsx`, `.js`, or `.jsx` file. Each numbered angle belongs to the pass its number names: walk it there and print its line in the Checklist under that pass. The unnumbered shapes at the end go into Pass 2 or Pass 4, wherever the line they sit on is reviewed.

## Contents

- Pass 3
  - 3.2b Logging discipline (TS/JS)
- Pass 4
  - 4.4 Template-literal interpolation masks nil
  - 4.5 Hard-coded `pageSize: N` / `limit: N` / `take: N` against a paginated API
  - 4.6 Index access on unordered Prisma/SQL result
  - 4.7 Remote write before local commit (idempotency hazard)
  - 4.8 Typed-but-fungible session field
  - 4.9 Test-infra DB / IDP / cloud client without env-var validation
  - 4.10 console.log of caller identifier / token / cookie / header / PII
  - 4.11 Error.cause non-enumerable
  - 4.12 AbortSignal.timeout() not available in jsdom / older Node
  - 4.13 Response / Request body not replayable
  - 4.14 Promise not awaited
  - 4.15 `.then(B).catch(H)` chain breadth
  - 4.16 useEffect missing deps / infinite loop
  - 4.17 SSR vs client boundary
  - 4.18 parseInt without radix
  - 4.19 Regex without anchors
- Unnumbered shapes
  - Supabase `{ data }` destructure
  - `await fetch(...)` without `.ok` / `.status` check
  - `Promise.all([...])` swallowing individual rejections
  - `.catch(() => null)` / `.catch(() => undefined)`
  - Empty `try { ... } catch {}`

## Checklist lines

```
Pass 3:
  3.2   Logging discipline               TS/JS: see 3.2b
Pass 4:
  4.4-4.19 TS/JS shapes                each section below
```

## Pass 3

### 3.2b Logging discipline (TS/JS)

Every `console.log` / `console.error` introduced by the diff: structured key only, never raw identifier values, never tokens, never cookies, never auth headers, never password-shaped strings. Test fixtures may use synthetic identifiers today, but the log destination (CI artifacts, journald, screen recordings, build dashboards) is durable and often public for OSS projects.

The fix is mechanical: replace `console.log(\`[op:${fixture.key}] X (${fixture.identifier})\`)` with `console.log(\`[op:${fixture.key}] X\`)` — the fixture key alone identifies the row in CI without leaking the underlying email/username.

## Pass 4

### 4.4 Template-literal interpolation masks nil

Any `` const x = `${maybeUndefined}/...` `` pattern coerces `undefined` → `"undefined"`, producing a truthy string. Subsequent `if (!x)` guards never fire. Idiomatic for must-be-defined values; a bug for env vars, config lookups, and possibly-absent API results. Null-check the interpolated value FIRST, then construct the string. Flag every template literal that interpolates an env-var, config lookup, or nullable API value without a preceding guard.

### 4.5 Hard-coded `pageSize: N` / `limit: N` / `take: N` against a paginated API

Without a follow-up loop is a scale ceiling, not a parameter. If the call returns `{totalPages, pageNumber, ...}` or similar pagination metadata and the code consumes only one page, ask: what happens at production scale when N is exceeded? Authz checks that key on the returned set silently under-grant (the unseen rows look unauthorized → actions denied that should succeed); display lists silently truncate; filter results lie.

Fix-class on security if the cap gates authz; maintainability otherwise. The shape repeats for any wire that paginates — an admin GraphQL `pageSize`, Prisma `take`, REST `?per_page=`, GraphQL `first:`. The fix is either a `fetchAll*` helper that loops `totalPages`, or a documented business-rule rationale for the ceiling.

### 4.6 Index access on unordered Prisma/SQL result

`result[0]` / `result.at(0)` / `result.first` on a query whose `select` / `include` / `findMany` carries no `orderBy` is non-deterministic. Read order across page loads, Postgres planner decisions, or Prisma client versions is unstable. If "the first row" carries semantic weight (primary mapping, default branch, canonical row), filter explicitly (`isPrimary: true`, `default: true`, `where: { canonical: true }`) and assert exactly-one — or pick a deterministic `orderBy`.

Fix-class for correctness regardless of whether today's behavior happens to be stable. The Postgres planner can change row order on a `VACUUM`, an `ANALYZE`, an index rebuild, or a version bump.

### 4.7 Remote write before local commit (idempotency hazard)

A sequence `await remoteSideEffect(...); await prisma.local.update(...)` is not idempotent on retry — a client that re-POSTs after the remote succeeded but the local update failed mints a second remote side-effect. Same shape: Stripe customer create + local user row, S3 presigned URL emit + local download record, third-party assignment mint + local launch row, Twilio SMS dispatch + local message row.

Fix: persist the receipt (assignment id, signed URL, webhook ack, dispatch id) on the LOCAL row BEFORE issuing the remote call (a "claim" row), OR guard subsequent calls with an existence check on the stored receipt before re-minting. The `if (!pa.startedAt) await prisma.update({startedAt})` pattern is a near-miss — it gates the local-write but not the remote-write, so retries between the two writes still mint duplicates.

### 4.8 Typed-but-fungible session field

`session.user.field[idx]` / chained access on a typed-but-runtime-fungible JWT: TypeScript's session type may declare `schoolIds: string[]` non-optional, but the JWT enrichment runs OUTSIDE the type system — a misconfigured IDP, an empty enrichment response, a stale JWT, or a partial migration can yield `undefined` at runtime. For any session field accessed via `[0]` or property chain in a route handler or page component, add `?.[0]` / `?.field` defensive chaining and a 400/redirect path if absent. The cost is one `?.` per access; the upside is no 500s on edge-case sessions.

Same rule for `cookies()`, `headers()`, environment-typed config readers, and any typed-at-edge-but-fungible-at-runtime read.

### 4.9 Test-infra DB / IDP / cloud client without env-var validation

A test helper (`e2e/helpers/*`, `test/setup.ts`, Playwright globalSetup/Teardown, Jest `setupFiles`) that instantiates a real client from `process.env.DATABASE_URL` / `OAUTH_ISSUER_URL` / `AWS_REGION` / `STRIPE_SECRET_KEY` without first validating the env var resolves to a local/safe target is a destructive-action risk. A misconfigured `.env.local` lets an e2e suite wipe a shared DB, hit a real IDP, or charge a real card.

Add a host allowlist check (URL hostname in `localhost`/`127.0.0.1`/`::1`, secret-key prefix in `sk_test_*`, AWS region in a known-test set, etc.) BEFORE the client is created, throwing on mismatch. Apply Pass 2 (Adversarial) reasoning to test infra — the destructive blast radius is the same as production code when the env var resolves wrong.

### 4.10 console.log of caller identifier / token / cookie / header / PII

Test fixtures may use synthetic identifiers today, but the log destination (CI artifacts, journald, screen recordings, build dashboards) is durable and often public for OSS projects. Mirror Pass 3 logging discipline at every `console.log` / `console.error` introduced by the diff: structured key only, never raw identifier values, never tokens, never cookies, never auth headers, never password-shaped strings.

The fix is mechanical: replace `console.log(\`[op:${fixture.key}] X (${fixture.identifier})\`)` with `console.log(\`[op:${fixture.key}] X\`)`.

### 4.11 Error.cause non-enumerable

Invisible to `JSON.stringify`, missed by log pipelines that serialize errors. If the diff sets `Error.cause` and a downstream sink JSON-stringifies the error, the cause is silently dropped.

### 4.12 AbortSignal.timeout() not available in jsdom / older Node

Test env crashes with no surface warning. If the diff uses `AbortSignal.timeout()` in code paths exercised by jsdom-based tests, the test suite throws at instantiation. Pin to a Node-compatible polyfill or guard the call.

### 4.13 Response / Request body not replayable

Without `.clone()`, a second read returns empty. If the diff reads `response.body` (or `.json()`, `.text()`) in two places without `.clone()`, the second read sees `null`.

### 4.14 Promise not awaited

Floating promise, unhandled rejection, out-of-order side effects. Search the diff for `someAsync()` without `await` or `.then(...).catch(...)`.

### 4.15 `.then(B).catch(H)` chain breadth

A trailing `.catch` on a promise chain catches rejections from BOTH the source promise AND any `.then` link in the chain. If H is appropriate for one rejection source (e.g., rollback an optimistic UI update when the source mutation rejects) but inappropriate for another (e.g., rollback even though the mutation already succeeded and only a follow-up refetch failed → server has the persisted state but UI reverts), the recovery semantic leaks across calls.

Verify H is correct for EVERY upstream rejection source in the chain. If not, split: `try { await source() } catch { recover() }; followup().catch(noop)`. Sibling to Pass 3 "Error-class differentiation at catch boundaries" — that rule is about distinguishable error classes from one call; this rule is about distinguishable rejection origins across a chain.

### 4.16 useEffect missing deps / infinite loop

React 18 strict mode amplifies. If the diff adds `useEffect` with a stale or missing dependency, the test suite may pass while the production app re-renders endlessly.

### 4.17 SSR vs client boundary

`localStorage`, `window`, `document` referenced on the server. In Next.js / Remix / Astro server components, any of these throws at SSR. Gate with `typeof window !== "undefined"` or `useEffect`.

### 4.18 parseInt without radix

Octal interpretation of leading-zero strings in older runtimes. `parseInt("08")` returns `0` in some legacy contexts. Always pass radix: `parseInt(x, 10)`.

### 4.19 Regex without anchors

Prefix/suffix match when exact intended. `"abc-".match(/abc/)` succeeds; `/^abc$/` is the exact intent.

## Unnumbered shapes

### Supabase `{ data }` destructure

`const { data } = await supabase.from(...).select(...).single()` silently swallows the `error` field. Required shape:

```ts
const { data, error } = await supabase.from(...).select(...).single();
if (error) { logger.error(...); return { kind: 'transient' }; }
// ... handle data === null separately
```

See Pass 2.11.

### `await fetch(...)` without `.ok` / `.status` check

`fetch` only rejects on network failure; 4xx/5xx return a resolved Response. Code that does `await fetch(...).json()` without `.ok` parses an error body as the success shape. See Pass 2.11.

### `Promise.all([...])` swallowing individual rejections

If any item rejects, the whole call rejects with the first one; the rest are lost. Use `Promise.allSettled` when fire-and-forget. See Pass 2.11.

### `.catch(() => null)` / `.catch(() => undefined)`

JS analogue of `case ... do {:error, _} -> :ok end`. Error reaches no log sink. Flag any catch that returns a sentinel without logging. See Pass 2.11.

### Empty `try { ... } catch {}`

Verify there's a log, a retry, or a propagation. If none, the error is gone. See Pass 2.11.
