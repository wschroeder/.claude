# Language — Elixir / Phoenix / Ecto / OTP

1. Read this file now, before Pass 1, when the diff touches a `.ex` or `.exs` file.
2. Walk each numbered angle in the pass its number names, and print its line in the Checklist under that pass.
3. Walk each unnumbered shape at the end in whichever pass reviews the line it sits on.

## Contents

  - 2.12 Discarded error tuple pattern (Elixir)
  - 3.2a Logging discipline (Elixir — codebase convention)
  - 3.5 capture_log assertion shape — no-output paths
  - 3.7 with-chain escape hatches
  - 3.8 with-chain over-gating
  - 5.9 Behaviour declaration consistency
  - 5.11 Pipeline shared-assign precedence
  - 9.2 `:dbg.tp(<Module>, ...)` and `:dbg.p(...)`
  - 9.3 `:meck.new(<Module>, ...)` and `:meck.expect(<Module>, ...)`
  - 9.4 `Mock.expect(...)`, `with_mock(<Module>, ...)`, `Mox.expect(<Mock>, ...)`
  - 9.6 `assert_called` / `assert_received` patterns
  - 9.7 Telemetry handlers
- Unnumbered shapes
  - `case` without catch-all
  - `Ecto.Query` raw SQL interpolation
  - `with` else that loses error identity
  - `Mock` / `:meck` combined with `async: true`
  - `Repo.all` without limit on user-controlled input
  - Changeset cast without `validate_required`
  - Timezone boundary bugs
  - New `where` / `order_by` filter without covering migration index
  - `Logger.warning` / `Logger.warn` / `Logger.debug`
  - `_ = fallible_call()` discarded error tuple
  - `Ecto.Multi` without explicit transaction error handling
  - `Ecto.Schema` `field :foo, T, default: X` vs migration default
  - `:meck.new(<Module>)` without `:meck.unload`
  - `Ecto.Sandbox` ownership without `allow`
  - `Phoenix.Token` vs DB-backed tokens
  - `:dbg.p(:all, :c)` global tracer in tests
  - SSM string-coercion (project rule)
  - SSM-secrets vs env-vars policy (project rule)
  - Direnv-required mix invocation

## Checklist lines

```
  3.2   Logging discipline               Elixir: see 3.2a
  3.5   capture_log assertion shape      `assert log == ""` vs `refute log =~`
  3.7   with-chain escape hatches        else `_ ->` conflates step failures
  3.8   with-chain over-gating           optional step gates critical step
  5.9   Behaviour declaration consistency `@behaviour`/`@impl` symmetry across siblings
  5.11  Pipeline shared-assign precedence multiple plug writers → last-wins risk
  9.2   BEAM mock/tracer targeting       :dbg, :meck, Mock, Mox: see 9.2-9.4
  9.6   assert_called / assert_received  message-pattern references
  9.7   Telemetry handlers               attach/detach for touched events
  2.12  Discarded error tuple (Elixir)   see 2.12
```

### 2.12 Discarded error tuple pattern (Elixir)

1. Search the diff for `_ =` on the left of any function call that returns an `{:ok, _} | {:error, _}` shape, such as `Repo.*`, `Ecto.Multi.*`, `send_*`, `broadcast_*`, a fallible `:telemetry.execute`, `ExAws.request`, or an HTTP client.
2. Treat side-effect verbs such as `revoke`, `notify`, `flush`, `expire`, and `invalidate` as fallible too, because they still return `{:ok | :error}`.
3. Surface every `_ = fallible_call()` as a Fix unless the caller can prove the failure is genuinely uninteresting, and check that the caller's response or state does not hinge on success.
4. Audit every `{:error, _}` arm in `case` and `with` blocks, and flag it as Fix-class when it neither logs, retries, nor propagates the error but returns `:ok`, a default counter, or a sentinel as if the call succeeded.

### 3.2a Logging discipline (Elixir — codebase convention)

1. Classify the level of every `Logger.<level>` call the diff introduces, modifies, or relocates, because this codebase uses only `Logger.info` and `Logger.error`.
2. Accept `Logger.info` for an operationally visible state change a human should see, and `Logger.error` for a problem requiring investigation.
3. Flag `Logger.warning` and `Logger.warn` for replacement: change it to `Logger.error` if it should be visible and acted on, or delete it and emit telemetry if it is a metric or a trace.
4. Flag `Logger.debug` for replacement: delete it, or move it to a dev-only `IO.inspect`, `:dbg.tp`, or an explicit telemetry counter.
5. Flag a bare `Logger.log(level, ...)` with a runtime level for the same audit.
6. In test files, flag any `Logger.warning` or `Logger.error` that code under test emits on purpose without a `capture_log/1` wrapper (per `code-quality-checklist`), whether or not the assertions pass.

### 3.5 capture_log assertion shape — no-output paths

1. Assert `assert log == ""` when `capture_log` wraps a path that should emit no logs.
2. Assert `assert log =~ "expected phrase"` when the path should emit a specific line.
3. Accept `refute log =~ "phrase"` only when other logs are tolerated and the test says why.
4. Flag every `refute log =~ ...` in the diff and ask whether the intent is "no output"; if yes, then change it to `assert log == ""`.

### 3.7 with-chain escape hatches

1. Check the `else` of every `with` block, and flag an `_ ->` or `{:error, _} ->` that does not say which step failed.
2. Require each fallible step to produce a distinguishable error, or the `else` to handle the union of all possible failures explicitly.

### 3.8 with-chain over-gating

1. Flag a non-critical step in a `with` chain, such as setting a default or sending a notification, that gates a critical step, such as creating a subscription or completing a transaction.
2. Move a best-effort or self-healing step after the chain, or wrap it in a separate error-handling block.

### 5.9 Behaviour declaration consistency

1. For a module implementing `init/1` and `call/2` or other named behaviour callbacks, check whether sibling modules in the same package declare `@behaviour <Name>` and `@impl <Name>`.
2. Flag an asymmetric declaration as Fix-class maintainability, because it stops the compiler from catching callback drift.

### 5.11 Pipeline shared-assign precedence

1. For any change to a Plug pipeline, list every plug that writes the same `conn.assigns[:key]`, such as `:current_user`, `:current_account`, `:current_actor`, `:current_session`, `:tenant`, or `:claims`.
2. Classify each writer's behaviour when a request carries several credentials:
   - **Overwrite** — replaces whatever was there. Last-writer-wins. Must be intentional.
   - **No-op when already set** — checks `conn.assigns[:key]` and skips. Safe under multi-credential.
   - **Fail-closed on dual presence** — halts with 400 if the assign is already set AND a fresh credential is presented. Most defensible.
3. Flag more than one overwrite writer without explicit precedence as Fix-class.
4. Require a comment naming the intended winner, and a fail-closed check or a no-op-when-set guard at every other writer.

### 9.2 `:dbg.tp(<Module>, ...)` and `:dbg.p(...)`

1. Grep `:dbg.tp` and `:dbg.p`, and check whether the target module is in the diff's call graph, because a tracer usually pairs with a literal call-count assertion.

### 9.3 `:meck.new(<Module>, ...)` and `:meck.expect(<Module>, ...)`

1. If a touched module is mocked anywhere, check the mock against every signature change, renamed function, or removed clause, because `:meck` can stub the new signature with the old return shape.

### 9.4 `Mock.expect(...)`, `with_mock(<Module>, ...)`, `Mox.expect(<Mock>, ...)`

1. Apply 9.3 to the other mock libraries too, remembering that Mox is contract-checked at compile time and Mock and `:meck` are not.

### 9.6 `assert_called` / `assert_received` patterns

1. Grep for `assert_received {:<atom>` where `<atom>` matches a message tag a touched module emits.

### 9.7 Telemetry handlers

1. Grep `:telemetry.attach(...)`, `:telemetry.attach_many(...)`, and `:telemetry.detach(...)` for events a touched module emits or consumes, and check every handler when the diff adds, removes, or renames an event.

## Unnumbered shapes

### `case` without catch-all

1. Require a final `_ -> ` or `:error -> ` clause unless the inputs are statically constrained, because a missing one raises `FunctionClauseError`.

### `Ecto.Query` raw SQL interpolation

1. Flag `fragment("... #{user_input} ...")` and query-string concatenation, and use a parameterized fragment such as `fragment("upper(?)", ^user_input)`.

### `with` else that loses error identity

1. Apply Pass 3.7.

### `Mock` / `:meck` combined with `async: true`

1. Require `async: false` on any test module using Mock, because the patch is process-global. See Pass 7.12.

### `Repo.all` without limit on user-controlled input

1. Wrap it with `limit/2` or paginate.

### Changeset cast without `validate_required`

1. Require explicit validation for every field the downstream code requires.

### Timezone boundary bugs

1. Check UTC against local time, `~U[...]` against `DateTime`, and `Date` arithmetic across DST.

### New `where` / `order_by` filter without covering migration index

1. Apply Pass 1.1 Schema-query alignment, and rate a hot-path lookup without index coverage, such as auth, refresh tokens, sessions, billing, or breach response, as a PERF and SEC finding.

### `Logger.warning` / `Logger.warn` / `Logger.debug`

1. Apply Pass 3.2a Logging discipline.

### `_ = fallible_call()` discarded error tuple

1. Apply Pass 2.12, including the `case ... {:error, _} -> :ok` twin.

### `Ecto.Multi` without explicit transaction error handling

1. Check that `Repo.transaction(multi)`'s `{:error, name, value, results_so_far}` shape is handled with the same care as a direct `{:error, reason}`.

### `Ecto.Schema` `field :foo, T, default: X` vs migration default

1. Apply Pass 4.2 Schema default ≠ DB default, because nil stays reachable for rows inserted by raw SQL, admin scripts, or older migrations.

### `:meck.new(<Module>)` without `:meck.unload`

1. Require `:meck.unload`, or the stub persists across tests in the same module.

### `Ecto.Sandbox` ownership without `allow`

1. Require `Ecto.Adapters.SQL.Sandbox.allow/3` for each process an async test spawns. See Pass 7.14.

### `Phoenix.Token` vs DB-backed tokens

1. Distinguish in-memory signed tokens, which cannot be revoked, from DB-backed tokens, which can, and reject a revocation finding against a `Phoenix.Token`.

### `:dbg.p(:all, :c)` global tracer in tests

1. Recommend `:dbg.p(specific_pid, :c)`, because `:all` traces every process and concurrent tests contaminate the count. See Pass 7.17.

### SSM string-coercion (project rule)

1. Require every runtime config reader to coerce, as in `config[:enabled] == true || config[:enabled] == "true"`, because SSM stores everything as strings.

### SSM-secrets vs env-vars policy (project rule)

1. Flag a new `System.get_env(...)` that reads a secret as a policy violation; back new sensitive config with SSM.

### Direnv-required mix invocation

1. Run `mix` only with `direnv` loaded, and treat tests authored without it as possibly never run.
