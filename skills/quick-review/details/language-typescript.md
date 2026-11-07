# Language — TypeScript / JavaScript / Node

1. Read this file now, before Pass 1, when the diff touches a `.ts`, `.tsx`, `.js`, or `.jsx` file.
2. Walk each numbered angle in the pass its number names, and print its line in the Checklist under that pass.
3. Walk each unnumbered shape at the end in Pass 2 or Pass 4, wherever the line it sits on is reviewed.

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

1. At every `console.log` or `console.error` the diff introduces, log a structured key only: never a raw identifier value, a token, a cookie, an auth header, or a password-shaped string, because log destinations such as CI artifacts are durable and often public.
2. Replace `console.log(\`[op:${fixture.key}] X (${fixture.identifier})\`)` with `console.log(\`[op:${fixture.key}] X\`)`.

## Pass 4

### 4.4 Template-literal interpolation masks nil

1. Flag every template literal that interpolates an env var, a config lookup, or a nullable API value without a preceding guard, because `undefined` becomes the truthy string `"undefined"` and a later `if (!x)` never fires.
2. Null-check the interpolated value first, then build the string.

### 4.5 Hard-coded `pageSize: N` / `limit: N` / `take: N` against a paginated API

1. Flag a hard-coded page size, such as a GraphQL `pageSize`, Prisma `take`, REST `?per_page=`, or GraphQL `first:`, whose call returns pagination metadata while the code consumes one page.
2. Ask what happens at production scale when N is exceeded, and rate it Fix-class security if the cap gates authorization, maintainability otherwise.
3. Fix it with a `fetchAll*` helper that loops `totalPages`, or with a documented business reason for the ceiling.

### 4.6 Index access on unordered Prisma/SQL result

1. Rate `result[0]`, `result.at(0)`, or `result.first` on a query with no `orderBy` Fix-class for correctness, even when today's order looks stable.
2. If "the first row" carries meaning, then filter explicitly, such as `isPrimary: true`, and assert exactly one, or pick a deterministic `orderBy`.

### 4.7 Remote write before local commit (idempotency hazard)

1. Flag `await remoteSideEffect(...); await prisma.local.update(...)`, because a retry after the remote call succeeded and the local update failed mints a second remote side effect.
2. Fix it by persisting the receipt, such as an id, a signed URL, or a dispatch id, on the local row before the remote call, or by checking for a stored receipt before re-minting.
3. Reject a guard that gates only the local write, such as `if (!pa.startedAt) await prisma.update({startedAt})`.

### 4.8 Typed-but-fungible session field

1. For any session field read via `[0]` or a property chain in a route handler or page component, add `?.[0]` or `?.field` and a 400 or redirect path when it is absent, because JWT enrichment runs outside the type system.
2. Apply the same rule to `cookies()`, `headers()`, environment-typed config readers, and any read that is typed at the edge but can vary at runtime.

### 4.9 Test-infra DB / IDP / cloud client without env-var validation

1. Flag a test helper, such as `e2e/helpers/*`, `test/setup.ts`, Playwright globalSetup or Teardown, or Jest `setupFiles`, that builds a real client from `process.env.DATABASE_URL`, `OAUTH_ISSUER_URL`, `AWS_REGION`, or `STRIPE_SECRET_KEY` without first checking that it resolves to a local or safe target.
2. Require an allowlist check before the client is created, such as a hostname in `localhost`/`127.0.0.1`/`::1`, a secret-key prefix of `sk_test_*`, or an AWS region in a known test set, throwing on mismatch.
3. Apply Pass 2 (Adversarial) reasoning to test infrastructure.

### 4.10 console.log of caller identifier / token / cookie / header / PII

1. Apply 3.2b at every `console.log` or `console.error` the diff introduces.

### 4.11 Error.cause non-enumerable

1. If the diff sets `Error.cause` and a downstream sink JSON-stringifies the error, then flag it, because `JSON.stringify` drops the cause.

### 4.12 AbortSignal.timeout() not available in jsdom / older Node

1. If the diff uses `AbortSignal.timeout()` in code that jsdom-based tests exercise, then pin a Node-compatible polyfill or guard the call.

### 4.13 Response / Request body not replayable

1. If the diff reads `response.body`, `.json()`, or `.text()` in two places, then require `.clone()`, because the second read sees `null`.

### 4.14 Promise not awaited

1. Search the diff for `someAsync()` without `await` or `.then(...).catch(...)`.

### 4.15 `.then(B).catch(H)` chain breadth

1. Check that a trailing `.catch(H)` is correct for every rejection source in the chain, the source promise and each `.then` link alike.
2. If it is not, then split it: `try { await source() } catch { recover() }; followup().catch(noop)`.

### 4.16 useEffect missing deps / infinite loop

1. Check every `useEffect` the diff adds for a stale or missing dependency.

### 4.17 SSR vs client boundary

1. Gate `localStorage`, `window`, and `document` in Next.js, Remix, or Astro server components with `typeof window !== "undefined"` or `useEffect`.

### 4.18 parseInt without radix

1. Always pass a radix: `parseInt(x, 10)`.

### 4.19 Regex without anchors

1. Anchor a regex meant as an exact match, as in `/^abc$/`.

## Unnumbered shapes

### Supabase `{ data }` destructure

1. Never destructure only `{ data }`, which drops the `error` field. Required shape:

```ts
const { data, error } = await supabase.from(...).select(...).single();
if (error) { logger.error(...); return { kind: 'transient' }; }
// ... handle data === null separately
```

2. See Pass 2.11.

### `await fetch(...)` without `.ok` / `.status` check

1. Check `.ok` or `.status` before parsing a `fetch` response, because 4xx and 5xx resolve. See Pass 2.11.

### `Promise.all([...])` swallowing individual rejections

1. Use `Promise.allSettled` for fire-and-forget work, because `Promise.all` keeps only the first rejection. See Pass 2.11.

### `.catch(() => null)` / `.catch(() => undefined)`

1. Flag any catch that returns a sentinel without logging. See Pass 2.11.

### Empty `try { ... } catch {}`

1. Check for a log, a retry, or a propagation, and flag the catch if it has none. See Pass 2.11.
