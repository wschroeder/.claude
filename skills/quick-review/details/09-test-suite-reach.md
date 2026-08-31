# Pass 9 — Test-suite reach

The diff is not the only place that talks about the diff's symbols. Tests scattered across the repo can encode call counts, side-effect signatures, and mock expectations on the very functions you just changed — and a CI run is the first time most reviewers find out.

This pass is mechanical and broad: scan the entire `test/` tree for INDIRECT assertions on every public function/module touched by the diff. Each grep is one attempt; the pass's 12 attempts must distribute across the targets below.

For every public function/module name introduced, renamed, deleted, or behaviorally changed by the diff, run `grep -rn` across `test/` for:

## 9.1 The bare name

Function name, module name, GenServer name, struct/atom key. Hits in test files that the diff did not modify are the highest-value finding source.

## 9.2 `:dbg.tp(<Module>, ...)` and `:dbg.p(...)`

BEAM tracing on a touched module is almost always paired with a literal call-count assertion downstream. If a tracer attaches to a function the diff intentionally calls fewer/more times, the test will silently break in CI on an unrelated PR. Grep `:dbg.tp` and `:dbg.p` and check whether the target module is in the diff's call graph.

## 9.3 `:meck.new(<Module>, ...)` and `:meck.expect(<Module>, ...)`

If a touched module is mocked anywhere, that test owns a contract on its surface. A signature change, a renamed function, or a removed clause breaks the mock — sometimes silently, when `:meck` happily stubs the new signature with the old return shape.

## 9.4 `Mock.expect(...)`, `with_mock(<Module>, ...)`, `Mox.expect(<Mock>, ...)`

Same concern across the other mock libraries the codebase uses. Each library has its own miss profile (Mox is contract-checked at compile, Mock/`:meck` are not).

## 9.5 Literal call-count assertions

`assert N == :counters.get(...)`, `assert N == length(...)`, `assert N == Enum.count(...)`, `assert_called <Module>.<fun>(_, _)` (Mock), `verify!(...)` (Mox). If the diff changes how often a touched function is invoked, every literal-count assertion on its call graph is now stale.

## 9.6 `assert_called` / `assert_received` patterns

Message-based assertions that reference the touched module by name in pattern syntax. Grep for `assert_received {:<atom>` where `<atom>` matches a touched module's emitted message tag.

## 9.7 Telemetry handlers

`:telemetry.attach(...)` / `:telemetry.attach_many(...)` / `:telemetry.detach(...)` for events the touched module emits or consumes. A diff that adds, removes, or renames a telemetry event invalidates every handler that listened for the old name.

## 9.8 Comment-thread stitches

Test files that reference a touched function name in a `#` comment, in `describe`/`test` description strings, or in a `@moduletag`. These are almost always load-bearing — a developer wrote the comment because the test depends on the named function's behavior.

---

## Classifying hits

For each hit, classify as:

- **Maintenance gap** — the test encodes behavior the diff INTENTIONALLY changes (e.g., a literal call-count assertion that the diff was designed to reduce). The test must be updated in the same PR or it will fail in CI. Flag with file path, line number, and the specific assertion that needs updating.
- **Hidden contract** — the test encodes a behavior the diff did not realize it was changing. This is a behavioral regression hiding behind a passing CI on the local file's tests but a red CI elsewhere. Treat as a Fix-class finding.
- **Stale reference** — comments, descriptions, or `@moduletag` strings that mention the old name/behavior. Doc/code drift; flag for the same-PR cleanup.

This pass is the structural fix for "the call-graph and test-coverage passes are scoped to whatever the orchestrator's prompt mentions." The orchestrator's prompt should NOT enumerate which test files to check — this pass discovers them mechanically from the diff's symbol set, every time, regardless of what the prompt says.

If you find no hits, this angle is `DEMONSTRATED` clean — the greps are the artifact. Record "ran greps for <symbols>, 0 hits", and only after running the actual greps. A bare "no references" without the greps having run is the satisficing this pass exists to prevent.
