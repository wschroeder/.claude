# Language — Elixir / Phoenix / Ecto / OTP

Read this file now, before Pass 1, when the diff touches a `.ex` or `.exs` file. Each numbered angle belongs to the pass its number names: walk it there and print its line in the Checklist under that pass. The unnumbered shapes at the end go into whichever pass reviews the line they sit on.

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

Search the diff for `_ =` on the LHS of any function call. If the function returns an `{:ok, _} | {:error, _}` shape — `Repo.*`, `Ecto.Multi.*`, `AccessTokens.revoke/*`, `send_*`, `broadcast_*`, `:telemetry.execute` (when the handler is fallible), `ExAws.request`, HTTP clients — that's a discarded-error site. Verify the caller's response/state does not hinge on success. RFC 7009 §2.2.1, for example, allows 503 on retryable revoke errors; silently swallowing the `{:error, _}` and returning 200 is a spec violation, not defensive coding.

Side-effect-named verbs are the trap: `revoke`, `notify`, `flush`, `expire`, `invalidate` SOUND like fire-and-forget but the function still returns `{:ok | :error}`. Surface every `_ = fallible_call()` as a Fix unless the caller can prove the failure is genuinely uninteresting.

The `_ = fallible_call()` shape is one syntactic form. The same bug class also hides in `case fallible_call() do {:ok, _} -> ...; {:error, _} -> <fall-through> end` patterns where the `{:error, _}` arm does NOT log, retry, or propagate the error. Audit every `{:error, _}` (or `{:error, _reason}`) arm in `case` / `with` blocks: if the arm produces no `Logger.*` call AND no retry AND no propagation upward (the function returns `:ok` / a default counter / a sentinel as if the call succeeded), flag as Fix-class.

**Concrete failure shape:** `case AccessTokens.revoke(descendant) do {:ok, _} -> count + 1; {:error, _} -> count end` inside a chain-walk — the failure neither increments a counter nor logs, so a chain-walk that fails every revoke silently swallows the breach signal AND leaves descendants live. Both observability AND security degrade.

### 3.2a Logging discipline (Elixir — codebase convention)

This codebase uses TWO log levels only — `Logger.info` and `Logger.error`. There is no "warning that's not an error" tier, and tracing belongs in telemetry / `:dbg` / `:recon` / dev-only `IO.inspect`, not in `Logger.debug`. For every `Logger.<level>` call introduced, modified, or relocated by the diff, classify the level:

- `Logger.info` — operationally visible state change a human should see (acceptable).
- `Logger.error` — problem requiring investigation (acceptable).
- `Logger.warning` / `Logger.warn` — flag for replacement. Decide per-site: (a) if it should be visible and acted on, change to `Logger.error`; (b) if it shouldn't be visible to humans (it's a metric or a trace), delete the call and emit telemetry instead. "Warning" is not a tier here.
- `Logger.debug` — flag for replacement. Either delete (the runtime cost of debug-level logs is real even when the level is filtered) or move to a dev-only `IO.inspect` / `:dbg.tp` / explicit telemetry counter. Production tracing uses Erlang's tracing primitives, not `Logger.debug`.
- Bare `Logger.log(level, ...)` with a runtime level — flag for the same audit; the level may resolve to `:warning` or `:debug`.

Apply the same audit to test files: `Logger.warning` / `Logger.error` calls intentionally emitted by code under test must be wrapped in `capture_log/1` (per `code-quality-checklist`), or the suite leaks new warnings/errors. A test that triggers an expected error path without `capture_log` violates the project guideline regardless of whether the assertions pass.

### 3.5 capture_log assertion shape — no-output paths

When `capture_log` wraps a path that should emit NO logs (a happy-path that the diff just made silent, a refactor that moved a Logger call), the assertion must be `assert log == ""`, not `refute log =~ "specific phrase"`. The `refute log =~ ...` shape only catches one specific phrase — any OTHER unexpected log (a new `Logger.error` from a side path, a noisy library, a fresh telemetry warning) slips through and the test passes silently. That defeats the entire purpose of `capture_log` as a regression guard.

The right shapes are:
- **Path should emit nothing:** `assert log == ""` (catches anything).
- **Path should emit a SPECIFIC line:** `assert log =~ "expected phrase"` (positive — fails if missing).
- **Path should NOT emit a SPECIFIC line, but other logs are tolerated:** `refute log =~ "phrase"` (rare; document why).

A `refute` over a path documented as "no output" is a test-quality gap, not a style choice. Flag every `refute log =~ ...` in the diff and ask whether the underlying intent is "no output" — if yes, change to `assert log == ""`.

### 3.7 with-chain escape hatches

In `with` blocks, check the `else` clause. If the else matches `_ ->` or `{:error, _} ->` without distinguishing which step failed, errors from different steps are conflated. Each fallible step in the `with` should either produce a distinguishable error or the else must handle the union of all possible failures explicitly.

### 3.8 with-chain over-gating

When a non-critical step in a `with` chain (e.g., setting a customer default, sending a notification) gates a critical step (e.g., creating a subscription, completing a transaction), a failure in the optional step short-circuits the essential one. If a step is best-effort or self-healing, it should not be in the `with` chain — move it after the chain or wrap it in a separate error-handling block.

### 5.9 Behaviour declaration consistency

For modules implementing `init/1` and `call/2` (or other named behaviour callbacks), check whether sibling modules in the same package declare `@behaviour <Name>` and `@impl <Name>`. Asymmetric behaviour declarations (one plug declares, the next doesn't) prevent the compiler from catching callback drift on a future refactor — Fix-class maintainability, not Note-class.

### 5.11 Pipeline shared-assign precedence

For any change to a Plug pipeline, enumerate every plug in the pipeline that writes a particular `conn.assigns[:key]` (commonly `:current_user`, `:current_account`, `:current_actor`, `:current_session`, `:tenant`, `:claims`). With N writers and no explicit precedence rules, the LAST plug that runs and matches its conditions wins.

A request carrying multiple credentials (Bearer header + cookie session + network-proxy identity + app-issued token + LTI claims) executes all matching plugs in order — silent precedence inversion if a downstream plug overwrites an earlier valid identity. Concrete shape: `:graphql2` pipeline with order `ProxyIdentity → AppToken → OAuth2BearerAdapter → TokenAuth` lets `TokenAuth` overwrite a Bearer-derived `:current_user` if the request also carries a cookie session — the bearer caller silently impersonates the cookie session, or vice versa.

For each plug that writes the shared assign, classify its behavior on dual-presence:
- **Overwrite** — replaces whatever was there. Last-writer-wins. Must be intentional.
- **No-op when already set** — checks `conn.assigns[:key]` and skips. Safe under multi-credential.
- **Fail-closed on dual presence** — halts with 400 if the assign is already set AND a fresh credential is presented. Most defensible.

Multiple "overwrite" writers without explicit precedence is a precedence-inversion risk — Fix-class. Document the intended winner inline (a comment naming the resolution rule), and add a fail-closed check or `no-op when set` guard at every writer not designated as the winner.

### 9.2 `:dbg.tp(<Module>, ...)` and `:dbg.p(...)`

BEAM tracing on a touched module is almost always paired with a literal call-count assertion downstream. If a tracer attaches to a function the diff intentionally calls fewer/more times, the test will silently break in CI on an unrelated PR. Grep `:dbg.tp` and `:dbg.p` and check whether the target module is in the diff's call graph.

### 9.3 `:meck.new(<Module>, ...)` and `:meck.expect(<Module>, ...)`

If a touched module is mocked anywhere, that test owns a contract on its surface. A signature change, a renamed function, or a removed clause breaks the mock — sometimes silently, when `:meck` happily stubs the new signature with the old return shape.

### 9.4 `Mock.expect(...)`, `with_mock(<Module>, ...)`, `Mox.expect(<Mock>, ...)`

Same concern across the other mock libraries the codebase uses. Each library has its own miss profile (Mox is contract-checked at compile, Mock/`:meck` are not).

### 9.6 `assert_called` / `assert_received` patterns

Message-based assertions that reference the touched module by name in pattern syntax. Grep for `assert_received {:<atom>` where `<atom>` matches a touched module's emitted message tag.

### 9.7 Telemetry handlers

`:telemetry.attach(...)` / `:telemetry.attach_many(...)` / `:telemetry.detach(...)` for events the touched module emits or consumes. A diff that adds, removes, or renames a telemetry event invalidates every handler that listened for the old name.

## Unnumbered shapes

### `case` without catch-all

`FunctionClauseError` at runtime. Always include a `_ -> ` or `:error -> ` final clause unless the inputs are statically constrained.

### `Ecto.Query` raw SQL interpolation

Injection via `fragment("... #{user_input} ...")` or query-string concatenation. Use parameterized fragments: `fragment("upper(?)", ^user_input)`.

### `with` else that loses error identity

All failures collapse to one shape. Each fallible step should produce a distinguishable error, or the else clause must handle the union of all possible failures explicitly. See Pass 3.7.

### `Mock` / `:meck` combined with `async: true`

Process-global patch observable by concurrent tests in other files. Requires `async: false` on any module using Mock. See Pass 7.12.

### `Repo.all` without limit on user-controlled input

Unbounded result set. Wrap with `limit/2` or paginate.

### Changeset cast without `validate_required`

Fields the downstream code requires need explicit validation.

### Timezone boundary bugs

UTC vs local, `~U[...]` vs `DateTime`, `Date` arithmetic across DST.

### New `where` / `order_by` filter without covering migration index

See Pass 1.1 Schema-query alignment. Hot-path lookups (auth, refresh tokens, sessions, billing, breach response) without index coverage are PERF + SEC findings, not stylistic ones.

### `Logger.warning` / `Logger.warn` / `Logger.debug`

Codebase uses two-tier logging only (`info` and `error`); see Pass 3.2a Logging discipline. Test files emitting `Logger.warning` / `Logger.error` without `capture_log/1` violate `code-quality-checklist`.

### `_ = fallible_call()` discarded error tuple

If the function returns `{:ok, _} | {:error, _}`, this is a discarded-error site. See Pass 2.12 for the full shape and the `case ... {:error, _} -> :ok` twin.

### `Ecto.Multi` without explicit transaction error handling

`Repo.transaction(multi)` returns `{:ok, results} | {:error, name, value, results_so_far}`. The `{:error, name, _, _}` shape is rarely handled with the same care as direct `{:error, reason}`.

### `Ecto.Schema` `field :foo, T, default: X` vs migration default

See Pass 4.2 Schema default ≠ DB default. The Ecto struct default is NOT a DB default — nil is reachable for rows inserted via raw SQL, admin scripts, or older migrations.

### `:meck.new(<Module>)` without `:meck.unload`

Test-cleanup leak: the stub persists across tests in the same module unless explicitly unloaded.

### `Ecto.Sandbox` ownership without `allow`

`setup_all` opens a DB connection; async tests spawn tasks that see DB state from siblings unless `Ecto.Adapters.SQL.Sandbox.allow/3` is called per spawned process. See Pass 7.14.

### `Phoenix.Token` vs DB-backed tokens

In-memory signed tokens (no revocation) vs DB-backed tokens (revocable, replay-detectable). Reviews must distinguish when reasoning about auth flows. A `Phoenix.Token` revocation finding is incorrect at the level — revocation isn't a property of in-memory signed tokens.

### `:dbg.p(:all, :c)` global tracer in tests

Attaches the tracer to ALL processes in the BEAM, not just the test process. Concurrent tests can contaminate the receiver's count. Recommend `:dbg.p(specific_pid, :c)`. See Pass 7.17.

### SSM string-coercion (project rule)

SSM stores everything as strings; runtime config readers MUST coerce (`config[:enabled] == true || config[:enabled] == "true"`). A function like `refresh_token_ttl_seconds/0` that returns the raw config value without coercion fails open or closed depending on which type the surrounding code expects.

### SSM-secrets vs env-vars policy (project rule)

New sensitive configs SHOULD be SSM-backed. A new `System.get_env(...)` reading a secret is a policy violation, not a style choice.

### Direnv-required mix invocation

Running `mix` without `direnv` loaded picks up the wrong Elixir/OTP and silently misses compile-time checks. Tests authored without direnv may not have run at all.
