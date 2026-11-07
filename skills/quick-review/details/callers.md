# Callers and contracts

1. Read this file now, before Pass 1, when the diff adds a function or changes one's arguments, return value, or error shape.

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

1. Walk each angle below in the pass its number names, give it a disposition, and print its line in the Checklist under that pass.
2. List every function in the diff that is new or whose arguments or return value changed, and give each its own 1.3 line and its own 2.1 line; one example never stands in for the whole diff.
3. On each 1.3 line, name every caller, including callers outside the diff, with the grep and its hit count beside the list.
4. On each 2.1 line, say what that caller does with the result.

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

1. For each function the diff adds, and each existing function whose arguments or return value it changes, trace its return value through at least 3 caller levels, reading callers whether or not the diff touches them.
2. At each level, ask what the caller does with the result, what the caller's caller assumes was filtered or transformed, and whether the new contract satisfies those assumptions.
3. Treat a handler that returns `:ok` on a recovered error path, such as a race, a unique-constraint violation, exhausted retries, or a not-found fallback, as a checkpoint, and keep tracing to the terminal side effect, such as a DB write, an API response, a minted token, or a redirect.
4. Prove that the terminal side effect matches the persisted state, not that the handler returned a success tuple.
5. For each early return the diff adds, list every state of the rows that leads there, including one where another row also holds the same value; matching an existing early return is not proof.
6. At `case some_fallible_call() do :ok -> ...; :already_exists -> :ok end`, check whether the next step acts on the caller's intended payload or on the stored one, and flag it if it acts on the caller's.

### 1.5 Spec contract changes

1. For any function whose `@spec`, return type, or error shape changed, grep the codebase for every call site, and check that each caller handles the new shape, especially callers in files the diff does not touch.

### 1.9 Control-flow coupling of independent side effects

1. When two independent operations, such as writing an audit log and sending a notification, share a `case` or `if` branch with no data dependency between them, separate them so each can fail independently.

### 1.14 Time-window ceiling (round up, never truncate)

1. Round time-derived integer headers and fields, such as `Retry-After`, `Cache-Control: max-age=`, `expires_in`, `crl-next-update`, or any "seconds until X" value, up to the full window, never truncating.
2. Use ceiling division: `div(scale_ms + 999, 1000)` for ms→s, or the language-equivalent (`Math.ceil` in JS, `(x + n - 1) / n` in any int-only system).
3. Test it by setting the configurable parameter to a value that is not a multiple of the unit, such as `scale_ms: 1500`, and checking that the emitted header still tells the truth.
4. Round up for retry and expiry, and round down for "you have at most N" budgets.

### 2.1 Discarded results

1. Check that every fallible call's return value is bound and checked.
2. Check that every side effect after the call, such as an audit event, a notification, or a success response, depends on the bound result.
3. Give each changed function its own line here, not one line for the diff.
4. For a promise that is not awaited and does durable work, name the stored record that reruns that work after a restart, or rate the angle a Fix.

### 2.16 Resource not released

1. For every resource the diff opens, find the line that releases it on every exit path, including the error path:
   - files, sockets, and database connections checked out by hand
   - event listeners, subscriptions, observers, and PubSub subscriptions
   - timers and intervals (`setInterval`, `setTimeout` held in a ref, `Process.send_after` loops, `:timer.send_interval`)
   - processes and tasks started outside a supervisor (`spawn`, `Task.start`, a bare `GenServer.start`)
   - React effects that attach anything without returning a cleanup function
2. Report a resource with no release line, or one released only on the success path, citing the line that opens it and the missing close on the error branch.

### 2.17 Unbounded growth

1. For any structure the diff adds to, such as a module-level cache or array, a map in process state, an ETS table, an accumulator that lives across requests, or a memoization table, check for an eviction rule, a TTL, or a size cap.
2. If none exists, then construct the input that fills it: the key the caller controls and the rate at which a caller can mint new keys.
3. Route a caller-controlled key with no cap through the security axis of the Yes-to-any gate as CWE-770.
4. Require a whole file, response body, or archive that the diff builds in memory to name what limits its size: a quoted cap, or a stream.
5. If it names neither, then measure peak memory at the largest size the deployment allows, with one input as large as the biggest one expected, and compare it with the container's memory limit.
6. Follow each read the diff calls into, including helpers in files the diff does not touch, such as a storage download or a file read, and flag a helper that gathers a whole blob before writing it.
7. Never answer this angle with "no handles or caches", and never drop it under a security review's exclusion of denial of service.

### 4.3 Redaction/truncation completeness

1. When a variable is redacted, truncated, or masked before one sink, grep every other sink it reaches, such as a throw, a rethrow via `cause`, a serializer, or propagation, and require the redacted form in all of them.

### 5.6 Helper functions called

1. Grep the touched controller for the `validate_*`, `authorize_*`, and `audit_*` helpers its sibling actions call, and report the new action if it skips one or reimplements it.

### 5.8 Within-function return-shape consistency

1. For each function in the diff, list its return paths across every `case`, `cond`, `if`, early return, and `with`-else.
2. Require every branch to produce the same shape: all `:ok` or all `{:ok, value}`, and all `{:error, reason}` or all `:error`, never a mix.
3. Never accept a docstring that papers over a mismatch as a fix.

### 5.15 Codebase-wide reuse

For every new public function, module, component, hook, or query the diff adds:

1. Take the core of what it does: the query it runs, the API it calls, the transformation it applies, the regex it matches.
2. Grep the repository for that core, and for the name's stem (`format_currency` → `currency`, `format_money`, `to_money`). Include `lib/`, `src/`, shared packages, and utility directories.
3. Read each hit.
4. If an existing function already does the job, then rate the new one a Fix: call the existing one and delete the copy.
5. If an existing function would do the job with one more parameter or option, then raise a Flag naming that function and the extension.
6. Print the grep command and its hits as the artifact; "no similar function exists" without the grep is not a disposition.

### 4.21 CWE-193 off-by-one

1. Check slice sizes, loop bounds, and buffer lengths, and send two paths that bound the same thing differently to 5.7.

### 4.22 CWE-697 incorrect comparison

1. Check type coercion (`==` vs `===`), loose equality, and template-literal truthiness over `undefined`.
