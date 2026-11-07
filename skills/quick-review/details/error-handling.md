# Error handling

Read this file now, before Pass 1, when the diff adds or changes a catch, a rescue, an error return, a fallback, or a warn or error log.

Each angle below belongs to the pass its number names. Walk it in that pass, give it a disposition, and print its line in the Checklist under that pass.

The Elixir shape of 2.11 is in `language-elixir.md`.

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

- **`const { data } = await supabase.from(...).select(...).single()`** — Supabase JS returns `{ data, error }`. Destructuring only `data` silently swallows DB errors; the call collapses transient outages (`PGRST-…`, connection drops, RLS denials) into "row not found" semantics. The result: the caller returns 404/400/empty-success when the right answer is 500/transient. Required shape: `const { data, error } = await ...; if (error) { logger.error(...); return { kind: 'transient' } /* or apiError(500) */; }` — then handle the `data === null` case separately.
- **`await fetch(...)` without `.ok` / `.status` check** — `fetch` only rejects on network failure; 4xx/5xx return a resolved Response. Code that consumes `await fetch(...).json()` without inspecting `.ok` happily parses an error body as the success shape.
- **`Promise.all([...])` swallowing individual rejections** — if any item rejects, the whole `Promise.all` rejects with the first one; the rest are lost. When that's not the intent (fire-and-forget audits, parallel pushes to N instances), use `Promise.allSettled` and inspect each result.
- **`.catch(() => null)` / `.catch(() => undefined)`** — the JS analogue of `case ... do {:error, _} -> :ok end`. The error reaches no log sink and no retry; the caller treats it as a happy null. Flag any catch that returns a sentinel without logging.
- **`try { ... } catch {}` (empty catch)** — verify there's a log, a retry, or a propagation. If none, the error is gone.

Each of these is the same severity class as the Elixir `_ = call` site. Fix-class.

### 3.6 Silent catch-alls at call boundaries

When function A calls function B (especially across module boundaries — controller calling a context module, a webhook handler calling business logic), read A's handling of B's return. If A uses a catch-all clause (`_ ->`, bare `rescue`, or `{:error, _}` without logging/re-raising), the error's identity is lost. Flag cases where B can return distinguishable errors but A treats them identically or ignores them. A webhook controller that returns `200 OK` regardless of what the called module returns is a bug, not defensive coding.

A catch that logs the error still passes that test, so also follow each catch the diff adds to what a person sees once it has run: the page, the status, the record a reviewer opens. Check that state against each acceptance criterion from the requirement check. If the caught error leaves a record in a state the requirement says must explain itself, and nothing on the page explains it, that is a Fix. The proof is the state a test reaches through the caught path, read where the person reads it, not the value the catch returns.

Measured (2026-10-21): the PR's requirement was that every document needing verification shows its reason. A catch the branch added logged any database error from a document's check and returned `null`, so processing left the file in review with no reason on either page. One review saw that database errors reach the catch and wrote that the outcome "matches the design principle 'hand it to a person rather than failing'". The whole-branch review marked the reason criterion met and answered Pass 3 only for secrets. Neither asked what the person handed the document would see, and an outside reviewer caught it.

### 3.9 Error-class differentiation at catch boundaries

When a catch handles multiple distinguishable error classes, verify the response is correct for EACH class, not just the one the author had in mind. `AbortError`, `TypeError` (network), timeout, and domain errors (`OAuthConfigError`, `DBError`) signal different intents; a fallback correct for one is often wrong for another.

Gate fallbacks on `error instanceof <Expected>` and propagate the rest. Blanket `catch { return fallback }` over a call that can produce >1 error class is a bug unless every class should collapse to the same fallback.

### 3.13 CWE-754 Improper Check for Unusual Conditions

Dead guards, always-truthy checks, distinguishable error classes collapsed into one fallback. Pattern-matches with the template-literal-masks-nil shape (Pass 4): `${maybeUndefined}` produces the truthy string `"undefined"`, defeating the `if (!x)` guard the author thought they wrote.

### 3.14 A failure log names its operation

Each warning or error the diff logs inside an operation that has an id, such as a download, a run, a request, or a job, carries that id among its fields, so a person reading the log can find the operation the failure broke. Proof: quote the log call's fields, and quote where the id is in scope. If the id is in scope and the call leaves it out, that is a Fix.

Measured (2026-10-22): `export_bundle.pdf_unreadable` logged the file id but not the bundle id, though the download had recorded its bundle id before the first byte. Our reviews wrote "nothing new logs" and "3.1–3.9: N/A or clear", and Pass 3 had no angle that asked. The outside reviewer found it. The fix passes `bundleId` to `bundleEntries`, and the test expects it among the warning's fields.
