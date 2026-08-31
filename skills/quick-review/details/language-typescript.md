# Language — TypeScript / JavaScript / Node

TS/JS-specific bug shapes that recur in this codebase. Pair with Pass 4 (data correctness) and Pass 2 (adversarial). The angles below are language-specific cues that the reviewer should add to the relevant pass when the diff contains `.ts` / `.tsx` / `.js` / `.jsx`.

## Template-literal masks nil

`` const x = `${maybeUndefined}/...` `` coerces `undefined` → `"undefined"` (truthy string). Subsequent `if (!x)` never fires.

Idiomatic for must-be-defined values; a bug for env vars, config lookups, possibly-absent API results. Null-check FIRST, then build the string.

Flag every template literal that interpolates an env-var, config lookup, or nullable API value without a preceding guard.

## `Error.cause` is non-enumerable

Invisible to `JSON.stringify`, missed by log pipelines that serialize errors. If the diff sets `Error.cause` and a downstream sink JSON-stringifies the error, the cause is silently dropped.

## `AbortSignal.timeout()` not available in jsdom / older Node

Test env crashes with no surface warning. Guard or polyfill.

## `Response` / `Request` body is not replayable

Without `.clone()`, the second read returns empty. If the diff reads body in two places, `.clone()` first.

## Promise not awaited

Floating promise, unhandled rejection, out-of-order side effects. Grep for unbound `someAsync()` calls.

## `.then(B).catch(H)` chain breadth

A trailing `.catch` catches rejections from BOTH the source promise AND any `.then` link. If H is appropriate for one rejection source but inappropriate for another, the recovery semantic leaks across calls.

**Worked example:** the source mutation rejects → H rolls back the optimistic UI (correct). The source mutation succeeds but a follow-up refetch rejects → H rolls back even though the server has the persisted state (incorrect; UI reverts despite successful write).

Verify H is correct for EVERY upstream rejection source. If not, split:

```ts
try { await source() } catch { recover() };
followup().catch(noop);
```

Sibling to Pass 3 "Error-class differentiation at catch boundaries" — that rule is about distinguishable error classes from one call; this rule is about distinguishable rejection origins across a chain.

## `useEffect` missing deps / infinite loop

React 18 strict mode amplifies. ESLint catches most cases; verify the rule isn't disabled on the file.

## SSR vs client boundary

`localStorage`, `window`, `document` referenced on the server. In Next.js / Remix / Astro server components, any of these throws at SSR. Gate with `typeof window !== "undefined"` or `useEffect`.

## `parseInt` without radix

Octal interpretation of leading-zero strings in older runtimes. `parseInt("08")` returns `0` in some legacy contexts. Always: `parseInt(x, 10)`.

## Regex without anchors

Prefix/suffix match when exact intended. `/abc/` matches `"abc-suffix"`; `/^abc$/` is exact.

## Hard-coded `pageSize: N` / `limit: N` / `take: N`

A paginated API consumed without iterating `totalPages` is a scale ceiling, not a parameter. Authz checks that key on the returned set silently under-grant. See Pass 4.5.

## Index access on unordered Prisma/SQL result

`result[0]` / `result.at(0)` on a query without `orderBy` is non-deterministic. Filter explicitly (`isPrimary: true`) and assert exactly-one, or pick a deterministic `orderBy`. See Pass 4.6.

## Remote write before local commit (idempotency hazard)

`await remoteSideEffect(...); await prisma.local.update(...)` is not idempotent on retry. Persist the receipt on the LOCAL row BEFORE issuing the remote call. See Pass 4.7.

## `session.user.field[idx]` / typed-but-fungible JWT

TypeScript's session type may declare `schoolIds: string[]` non-optional, but JWT enrichment runs OUTSIDE the type system. Defensive chaining: `?.[0] ?? null`. See Pass 4.8.

## Test-infra DB / IDP client without env-var validation

Helper that instantiates a real client from `process.env.DATABASE_URL` without first validating the URL hostname is in `localhost`/`127.0.0.1`/`::1`. See Pass 4.9.

## `console.log` of caller identifier / token / cookie / header / PII

CI artifacts are durable. Structured key only, never raw identifier. See Pass 4.10 + Pass 3.2b.

## Supabase `{ data }` destructure

`const { data } = await supabase.from(...).select(...).single()` silently swallows the `error` field. Required shape:

```ts
const { data, error } = await supabase.from(...).select(...).single();
if (error) { logger.error(...); return { kind: 'transient' }; }
// ... handle data === null separately
```

See Pass 2.11.

## `await fetch(...)` without `.ok` / `.status` check

`fetch` only rejects on network failure; 4xx/5xx return a resolved Response. Code that does `await fetch(...).json()` without `.ok` parses an error body as the success shape. See Pass 2.11.

## `Promise.all([...])` swallowing individual rejections

If any item rejects, the whole call rejects with the first one; the rest are lost. Use `Promise.allSettled` when fire-and-forget. See Pass 2.11.

## `.catch(() => null)` / `.catch(() => undefined)`

JS analogue of `case ... do {:error, _} -> :ok end`. Error reaches no log sink. Flag any catch that returns a sentinel without logging. See Pass 2.11.

## Empty `try { ... } catch {}`

Verify there's a log, a retry, or a propagation. If none, the error is gone. See Pass 2.11.
