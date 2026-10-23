# Language — Elixir / Phoenix / Ecto / OTP

Elixir-specific bug shapes that recur in this codebase. Pair with the language skill `elixir-development` (Pass 5 conventions, Pass 7 tests). The angles below are language-specific cues that the reviewer should add to the relevant pass when the diff contains `.ex` / `.exs`.

## `case` without catch-all

`FunctionClauseError` at runtime. Always include a `_ -> ` or `:error -> ` final clause unless the inputs are statically constrained.

## `Ecto.Query` raw SQL interpolation

Injection via `fragment("... #{user_input} ...")` or query-string concatenation. Use parameterized fragments: `fragment("upper(?)", ^user_input)`.

## `with` else that loses error identity

All failures collapse to one shape. Each fallible step should produce a distinguishable error, or the else clause must handle the union of all possible failures explicitly. See Pass 3.7.

## `Mock` / `:meck` combined with `async: true`

Process-global patch observable by concurrent tests in other files. Requires `async: false` on any module using Mock. See Pass 7.12.

## `Repo.all` without limit on user-controlled input

Unbounded result set. Wrap with `limit/2` or paginate.

## Changeset cast without `validate_required`

Fields the downstream code requires need explicit validation.

## Timezone boundary bugs

UTC vs local, `~U[...]` vs `DateTime`, `Date` arithmetic across DST.

## New `where` / `order_by` filter without covering migration index

See Pass 1.1 Schema-query alignment. Hot-path lookups (auth, refresh tokens, sessions, billing, breach response) without index coverage are PERF + SEC findings, not stylistic ones.

## `Logger.warning` / `Logger.warn` / `Logger.debug`

Codebase uses two-tier logging only (`info` and `error`); see Pass 3.2a Logging discipline. Test files emitting `Logger.warning` / `Logger.error` without `capture_log/1` violate `code-quality-checklist`.

## `_ = fallible_call()` discarded error tuple

If the function returns `{:ok, _} | {:error, _}`, this is a discarded-error site. See Pass 2.12 for the full shape and the `case ... {:error, _} -> :ok` twin.

## `Ecto.Multi` without explicit transaction error handling

`Repo.transaction(multi)` returns `{:ok, results} | {:error, name, value, results_so_far}`. The `{:error, name, _, _}` shape is rarely handled with the same care as direct `{:error, reason}`.

## `Ecto.Schema` `field :foo, T, default: X` vs migration default

See Pass 4.2 Schema default ≠ DB default. The Ecto struct default is NOT a DB default — nil is reachable for rows inserted via raw SQL, admin scripts, or older migrations.

## `:meck.new(<Module>)` without `:meck.unload`

Test-cleanup leak: the stub persists across tests in the same module unless explicitly unloaded.

## `Ecto.Sandbox` ownership without `allow`

`setup_all` opens a DB connection; async tests spawn tasks that see DB state from siblings unless `Ecto.Adapters.SQL.Sandbox.allow/3` is called per spawned process. See Pass 7.14.

## `Phoenix.Token` vs DB-backed tokens

In-memory signed tokens (no revocation) vs DB-backed tokens (revocable, replay-detectable). Reviews must distinguish when reasoning about auth flows. A `Phoenix.Token` revocation finding is incorrect at the level — revocation isn't a property of in-memory signed tokens.

## `:dbg.p(:all, :c)` global tracer in tests

Attaches the tracer to ALL processes in the BEAM, not just the test process. Concurrent tests can contaminate the receiver's count. Recommend `:dbg.p(specific_pid, :c)`. See Pass 7.17.

## SSM string-coercion (project rule)

SSM stores everything as strings; runtime config readers MUST coerce (`config[:enabled] == true || config[:enabled] == "true"`). A function like `refresh_token_ttl_seconds/0` that returns the raw config value without coercion fails open or closed depending on which type the surrounding code expects.

## SSM-secrets vs env-vars policy (project rule)

New sensitive configs SHOULD be SSM-backed. A new `System.get_env(...)` reading a secret is a policy violation, not a style choice.

## Direnv-required mix invocation

Running `mix` without `direnv` loaded picks up the wrong Elixir/OTP and silently misses compile-time checks. Tests authored without direnv may not have run at all.
