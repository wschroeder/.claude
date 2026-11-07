# Error handling

1. Read this file now, before Pass 1, when the diff adds or changes a catch, a rescue, an error return, a fallback, or a warn or error log.
2. Walk each angle below in the pass its number names, give it a disposition, and print its line in the Checklist under that pass.
3. Find the Elixir shape of 2.11 in `language-elixir.md`.

## Checklist lines

```
Pass 2:
Pass 3:
  3.6   Silent catch-alls at boundaries  webhook 200 regardless of B's return;
                                          each catch the diff adds: what a person
                                          sees afterward, against each criterion
  3.9   Error-class differentiation      AbortError vs TypeError vs domain
  3.13  CWE-754 unusual-condition checks dead guards; collapsed error classes
  3.14  A failure log names its operation each warn/error inside a download, run,
                                          or request carries that operation's id
```

### 2.11 Discarded error tuple pattern (TS/JS)

1. Flag each of these as Fix-class:
- **`const { data } = await supabase.from(...).select(...).single()`** — destructuring only `data` turns a database error into "row not found". Required shape: `const { data, error } = await ...; if (error) { logger.error(...); return { kind: 'transient' } /* or apiError(500) */; }`, then handle `data === null` separately.
- **`await fetch(...)` without `.ok` / `.status` check** — a 4xx or 5xx resolves, so the error body is parsed as the success shape.
- **`Promise.all([...])` swallowing individual rejections** — where every result matters, such as audits or parallel pushes, use `Promise.allSettled` and inspect each result.
- **`.catch(() => null)` / `.catch(() => undefined)`** — any catch that returns a sentinel without logging.
- **`try { ... } catch {}` (empty catch)** — unless it logs, retries, or propagates.

### 3.6 Silent catch-alls at call boundaries

1. When function A calls function B, especially across a module boundary, read A's handling of B's return.
2. Flag a catch-all, such as `_ ->`, a bare `rescue`, or `{:error, _}` without logging or re-raising, that treats B's distinguishable errors alike or ignores them, including a webhook that returns `200 OK` whatever B returns.
3. Follow each catch the diff adds to what a person sees once it has run, such as the page, the status, or the record a reviewer opens, and check that state against each acceptance criterion from the requirement check.
4. Report a Fix when the caught error leaves a record in a state the requirement says must explain itself and nothing on the page explains it.
5. Prove it with the state a test reaches through the caught path, read where the person reads it, not with the value the catch returns.

### 3.9 Error-class differentiation at catch boundaries

1. When a catch can receive more than one error class, such as `AbortError`, `TypeError`, a timeout, or a domain error, check the response for each class.
2. Require the fallback gated on `error instanceof <Expected>` with the rest propagated, unless every class should take the same fallback.

### 3.13 CWE-754 Improper Check for Unusual Conditions

1. Flag dead guards, always-truthy checks, and distinguishable error classes collapsed into one fallback, including a template literal such as `${maybeUndefined}` that turns a missing value into the truthy string `"undefined"` (Pass 4).

### 3.14 A failure log names its operation

1. Require each warning or error the diff logs inside an operation that has an id, such as a download, a run, a request, or a job, to carry that id among its fields.
2. Quote the log call's fields and where the id is in scope.
3. Report a Fix when the id is in scope and the call leaves it out.
