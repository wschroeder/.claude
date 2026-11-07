# Callers and contracts

Read this file now, before Pass 1, when the diff adds a function or changes one's arguments, return value, or error shape.

## Contents

- 1.3 Return-value assumptions (recovered-error checkpoints are not terminal)
- 1.5 Spec contract changes
- 1.9 Control-flow coupling of independent side effects
- 1.14 Time-window ceiling (round up, never truncate)
- 2.1 Discarded results
- 2.16 Resource not released
- 2.17 Unbounded growth
- 4.3 Redaction/truncation completeness
- 5.6 Helper functions called
- 5.8 Within-function return-shape consistency
- 5.15 Codebase-wide reuse
- 4.21 CWE-193 off-by-one
- 4.22 CWE-697 incorrect comparison

Each angle below belongs to the pass its number names. Walk it in that pass, give it a disposition, and print its line in the Checklist under that pass.

**Angles 1.3 and 2.1 owe one line per item.** List every function in the diff that is new or whose arguments or return value changed. Each one gets its own 1.3 line naming every caller, including callers outside the diff, with the grep and its hit count printed beside the list, and its own 2.1 line saying what that caller does with the result. One example standing in for the whole diff is not a disposition.

## Checklist lines

```
Pass 1:
  1.3   Return-value assumptions         3-level caller trace; recovered-error
                                          checkpoints are NOT terminal; each early return
                                          names every state reaching it, another row too
  1.5   Spec contract changes            @spec change → every caller updated
  1.9   Control-flow coupling            independent side-effects in one branch
  1.14  Time-window ceiling              round up, never truncate
Pass 2:
  2.1   Discarded results                fallible call result ignored; a void or
                                          detached promise doing durable work names the
                                          stored record that reruns it after a restart,
                                          or it is a Fix
  2.16  Resource not released            handle / socket / listener / timer /
                                          process opened with no close path
  2.17  Unbounded growth                 cache / map / table / state only added to;
                                          a whole file, response, or archive held
                                          in memory names what limits its size,
                                          in helpers the diff calls too
                                          proof: the quoted limit, or peak memory
                                          with one input as large as expected
                                          measured at the largest size the
                                          deployment allows
Pass 4:
  4.3   Redaction/truncation completeness all sinks (throw, log, cause) use redacted
  4.21  CWE-193 off-by-one               slice/loop/buffer bounds; two paths
                                          bounding the same thing differently:
                                          see 5.7
  4.22  CWE-697 incorrect comparison     `==` vs `===`; loose equality
Pass 5:
  5.6   Helper functions called          same validate_*/authorize_*/audit_*
  5.8   Within-function return-shape     all branches same shape (no :ok mix)
  5.15  Codebase-wide reuse              grep repo for an existing function that
                                          already does, or could do, the new job
```

### 1.3 Return-value assumptions (recovered-error checkpoints are not terminal)

For each function the diff adds, and each existing function whose arguments or return value it changes, trace its return value through at least 3 caller levels. Read the callers whether or not the diff touches them: a caller outside the diff is where a changed contract goes unhandled. What does the caller do with the result? What does the caller's caller assume was filtered or transformed? Does the new function's contract satisfy those assumptions?

**Recovered-error checkpoints are not terminal.** A handler returning `:ok` on a recovered error path (race, unique-constraint violation, retry-exhausted, not-found fallback) is NOT the end of the trace — it is a checkpoint. Continue tracing until the terminal side effect (DB write, API response, token minted, redirect emitted). The invariant to prove is that the terminal side effect matches the persisted state, not that the handler returned a success tuple.

Worked example: a fix scoped a domain delete to the document in the URL and made it return `false` when the line item belonged to another document. The diff touched only the domain, the application layer, and a test. The route that called it sat outside the diff: it looked the line item up by its id alone before the delete, and it wrote an "item deleted" audit event whether or not the delete returned `false`. So the route recorded another document's line item against this one. The review checked the changed query, answered 1.3 with one example from a different function, and passed 2.1 as "audit writes are best-effort". An outside reviewer caught it on the PR. One 1.3 line for the changed delete would have opened that route.

Name every caller, and print the grep and its hit count beside the list, so a reader can see the list is whole. Worked example: a pull request taught `matchRecord` to match remembered numbers. Our review wrote "matchRecord ← processing :1187", one caller of two. The other, `resolveDocumentMatch` in the route, ran on every page open and moved documents as a side effect. An outside reviewer caught it.

**Early returns name every state that reaches them.** For each early return the diff adds, list every state of the rows that leads there, including one where another row also holds the same value. A new early return that matches an existing one is not proof: the existing one may only ever have been reached from one of those states.

Worked example: a pull request returned early when the record a reviewer chose already remembered the number. When two records remembered the same number, holder, and parent, choosing either one reached that return. The other record kept its copy, its waiting documents never moved, and later documents stayed ambiguous although the reviewer had chosen. Our review wrote "The new early `null` matches the existing early return for "this record already holds the number"." and stopped there. An outside reviewer caught it.

When you see `case some_fallible_call() do :ok -> ...; :already_exists -> :ok end`, ask: does the next step operate on the CALLER's intended payload or on the STORED payload? If the former, the race has decoupled "what the user agreed to" from "what the DB says they agreed to" — a silent integrity break.

### 1.5 Spec contract changes

For any function whose `@spec`, return type, or error shape changed in the diff, grep the codebase for all call sites. Verify each caller handles the new return shape — especially callers in files not touched by the diff. A function that previously returned `:noop` and now returns `{:ok, _} | {:error, _}` has changed its contract; every consumer must be checked.

### 1.9 Control-flow coupling of independent side effects

When two independent operations (e.g., writing an audit log + sending a notification) share a `case`/`if` branch with no data dependency between them, one's failure suppresses the other. If neither operation consumes the other's output, they should not be gated by the same branch — separate them so each can fail independently.

### 1.14 Time-window ceiling (round up, never truncate)

Time-derived integer headers and fields — `Retry-After`, `Cache-Control: max-age=`, `expires_in`, `crl-next-update`, any "seconds until X" value — must round UP to the full window, not truncate. `div(scale_ms, 1000)` is the wrong primitive when `scale_ms` is not a clean multiple of 1000: for `scale_ms = 1500`, `div(1500, 1000) = 1`, but the bucket is still active for another 0.5s. A client honoring `Retry-After: 1` retries at t=1.0s and gets denied again — the header lied.

Use ceiling division: `div(scale_ms + 999, 1000)` for ms→s, or the language-equivalent (`Math.ceil` in JS, `(x + n - 1) / n` in any int-only system).

The deletion test: change the configurable param so it's NOT a multiple of the unit (e.g., `scale_ms: 1500`). Does the emitted header still describe the truth? Under-reporting causes early retries (rate-limit thundering); over-reporting causes unnecessary delays. Round up is the safe direction for retry/expiry; round down for "you have at most N" budgets.

### 2.1 Discarded results

Is the return value bound and checked? A fallible call whose result is ignored (e.g., `Stripe.Subscription.delete(id)` on its own line) is a bug — the failure case is invisible.

A result can also be bound and still ignored: `const deleted = await remove(...)` followed by a side effect that runs whatever `deleted` holds, such as an audit event, a notification, or a success response. Check that every side effect after the call depends on the result. Give each changed function its own line here, not one line for the diff.

A promise that is not awaited (`void`, fire-and-forget) and does durable work dies with the process. Name the stored record that reruns that work after a restart, or the angle is a Fix. Worked example: a reviewer's save moved a document and started its verification check without awaiting it, and the worker step cleared the request before the check ran. Our review wrote "deliberately not awaited (void) and catches its own errors" and filed the lost retry as a Note. An outside reviewer caught it; the fix stored the request and cleared it only after the check finished.

### 2.16 Resource not released

For every resource the diff opens, find the line that releases it on every exit path, including the error path:

- files, sockets, and database connections checked out by hand
- event listeners, subscriptions, observers, and PubSub subscriptions
- timers and intervals (`setInterval`, `setTimeout` held in a ref, `Process.send_after` loops, `:timer.send_interval`)
- processes and tasks started outside a supervisor (`spawn`, `Task.start`, a bare `GenServer.start`)
- React effects that attach anything without returning a cleanup function

A resource with no release line, or one released only on the success path, is the finding. The artifact is the line that opens it and the absence of a close on the error branch.

### 2.17 Unbounded growth

Any structure the diff adds to without a bound: a module-level cache or array, a map held in process state, an ETS table, a `Map.put` accumulator that lives across requests, a memoization table. Check for an eviction rule, a TTL, or a size cap.

If none exists, construct the input that fills it: the key the caller controls (a user id, a URL, a query string) and the rate at which a caller can mint new keys. A key the caller controls with no cap is also CWE-770 and a denial-of-service shape; route it through the security axis of the Yes-to-any gate.

One request can grow without bound too. A whole file, response body, or archive that the diff builds in memory must name what limits its size: a quoted cap, or a stream. If it names neither, measure peak memory at the largest size the deployment allows, and compare it with the container's memory limit. "No handles or caches" does not answer this angle, and a security review's exclusion of denial of service does not drop it either, because the person it hurts is the one ordinary user whose download is big.

Measured (2026-10-22): `zipStored` built the whole export bundle in memory, PDFs included. One review listed it as a hypothesis and never measured it, security-review dropped it under its exclusion for denial of service, and a third answered 2.16 and 2.17 with "N/A, no handles or caches". The outside reviewer saw memory climb to 1.5 GiB, and the deployed containers get 2 GiB. The fix streamed one document at a time, and a 500 MiB zip then peaked at 71 MiB of buffers.

Follow each read the diff calls into, including helpers in files the diff does not touch, such as a storage download or a file read. A helper that gathers a whole blob before writing it holds that blob in memory however carefully the caller streams. Run the memory proof with one input as large as the biggest one expected, not only with many small ones: many small files keep the peak low while each one is held whole.

Measured (2026-10-22): after that fix, the bundle still copied each stored PDF to disk through `materializeFile`, which gathered the whole blob into one buffer first. The next review answered 2.17 with "POST bodies" and "note on bodyLimit", and its memory proof measured the whole zip. A second outside review found the buffer. Against Azurite, a 100 MB blob grew buffers by 116 MB with the old helper and by 10 MB once it piped the download stream to the file.

### 4.3 Redaction/truncation completeness

When a variable is redacted, truncated, or masked before one sink (log, response, storage), grep every other sink it reaches: throw, rethrow via `cause`, serialize, propagate. ALL sinks must use the redacted form. One unredacted sink defeats the redaction.

### 5.6 Helper functions called

Same `validate_*`, `authorize_*`, `audit_*` helpers as siblings; not a parallel reimplementation. Grep for the helper name in the touched controller; if any sibling action calls it and the new one doesn't, that's the finding.

### 5.8 Within-function return-shape consistency

For each function in the diff, statically enumerate its return paths across every branch (every `case`/`cond`/`if`/early-return/`with`-else). Verify all branches produce the same shape — either all `:ok` or all `{:ok, value}`, either all `{:error, reason}` or all `:error`, never a mix. Asymmetric branches force callers to handle multiple shapes; silent callers that pattern-match on only one shape crash with `MatchError` on the other.

Docstrings that paper over the mismatch ("safe to call if no row exists") do not fix the contract — they document the bug. This is the branch-level analogue of sibling consistency: the function is consistent with ITSELF across its own return paths.

### 5.15 Codebase-wide reuse

5.5 compares helpers inside one module. This angle searches the rest of the repository. For every new public function, module, component, hook, or query the diff adds:

1. Take the core of what it does: the query it runs, the API it calls, the transformation it applies, the regex it matches.
2. Grep the repository for that core, and for the name's stem (`format_currency` → `currency`, `format_money`, `to_money`). Include `lib/`, `src/`, shared packages, and utility directories.
3. Read each hit.

If an existing function already does the job, the new one is a Fix: call the existing one and delete the copy. If an existing function would do the job with one more parameter or option, it is a Flag naming that function and the extension. The artifact is the grep command and its hits; "no similar function exists" without the grep is not a disposition.

### 4.21 CWE-193 off-by-one

Slice sizes, loop bounds, buffer lengths. Two paths bounding the same thing differently go to 5.7.

### 4.22 CWE-697 incorrect comparison

Type coercion (`==` vs `===`), loose equality, template-literal truthiness over `undefined`.
