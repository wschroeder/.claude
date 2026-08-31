# Pass 7 — Test coverage

What's tested, what isn't, edge cases, trivially passing assertions. **You must have read the FULL test diff before claiming a coverage gap.** If the test diff was truncated or partially read, re-read the remainder before this pass. A false "missing test" flag wastes more time than any real gap.

**Tests must assert outcomes, not implementation.** A test that checks "this function was called" or "the query contains this clause" is testing wiring, not behavior. The correct test asserts the observable result: the DB row exists with the right values, the API returned the right response, the error was the expected one. Mock call_history assertions are a smell — they prove a code path ran, not that it worked.

**Tests over eyeballing.** The review's primary job is to identify behaviors that lack test coverage — not to substitute for tests by reading code carefully. For every finding in passes 1-5, ask: "is there a test that would catch this?" If yes, the finding is already guarded. If no, the missing test IS the finding.

## 7.1 Failure path coverage

For every external API call or side-effecting operation, is there a test for when it fails? A missing failure-path test is more dangerous than any code pattern, because the pattern can be refactored away silently.

## 7.2 Side-effect coverage

For operations with multiple side effects (e.g., attach payment method AND set as default), is each side effect independently asserted? A test that only checks the first side effect won't catch the second being dropped.

## 7.3 Refactored-code coverage

When code is extracted into a new function or restructured, identify behaviors that had no test coverage before the refactor. Those are the landmines — the refactor is safe if tests existed, dangerous if they didn't. Flag the missing test, not the refactoring.

## 7.4 End-to-end path coverage

For each modified code path that crosses module boundaries (e.g., GraphQL mutation → context module → external API), check whether an integration test exercises the full chain end-to-end — not just individual units in isolation.

## 7.5 New external API without test mocks

When the diff adds a call to an external service (Stripe, Clever, AWS, any HTTP client), check that test files include a corresponding mock or fixture for that call. A missing mock means CI will either hit the real API (flaky, slow, dangerous) or fail with a connection error — both of which indicate the test suite does not cover the new path.

## 7.6 Partial-chain tests masking gaps

When tests exist for the entry point (e.g., the controller test) but those tests mock out the middle layer, and the diff changed behavior in that middle layer, the existing tests are not exercising the changed code. Flag this — the test passes but does not cover the change.

## 7.7 Symmetry cross-check (Pass 5 × Pass 6)

For each production code change identified in Pass 5 as a symmetric/sibling application (function B received the same change as function A), verify that B's change has corresponding test coverage. When A's change has a dedicated test but B's does not, flag it — the model's tendency is to see extensive test additions and conclude "tests look good" without per-path verification.

## 7.8 Test intent vs test effect

Read each new test's body end-to-end. Does execution actually reach the branch the test's name claims to exercise, or does an earlier guard / validation / nil check / regex / length check short-circuit before that branch runs? A test named "rejects malformed JSON" that hits a session-nil check *before* JSON parsing has never touched malformed-JSON code; a test named "rejects wrong PKCE verifier" that uses a 22-char string fails the 43-char length regex *before* reaching `secure_compare`. The test's name lies; the code path is untested.

For every test whose name describes a specific rejection or code path, trace execution setup → assertion and confirm the claimed code path fires. If earlier validations short-circuit, fix the test inputs to pass those validations so the target branch is reached.

**This angle applies to EVERY added or modified test in the diff — not just the test the reviewer's prompt points at.**

## 7.9 Test-to-test assertion symmetry

Sibling tests (same setup pattern, adjacent in the file, testing the same surface from different angles) should assert the same invariants. If test A checks `used_at is nil` / `:counters.get(_, 1) == 0` / a specific error shape, the siblings should too — otherwise the invariant is enforced in only one branch, and the next regression hides in the siblings. Group tests by setup/target and flag assertion asymmetry within the group.

## 7.10 Range-assertions are correctness gaps, not style

An assertion that permits multiple distinct values when the correct value is known (`conn.status in [400, 502]` instead of `== 502`, `body =~ "error"` when the exact message is specified, `refute is_nil(x)` when `== expected_value` is meant) is a test-quality gap, NOT a style nit. A regression into the wrong-but-permitted value passes CI silently.

If the test author knows exactly which status/message/value should be returned, the assertion must pin to that value. Only permit a range when the test genuinely tolerates all values in the range (rare; document why).

## 7.11 Tests added by the current review loop are not authoritative

When a test was WRITTEN during the current review (not pre-existing), ask: does the test VERIFY behavior the mission claims, or does it DOCUMENT the behavior the code happens to produce? A test that locks the status quo of code we just wrote can freeze a wrong design.

For every test authored in-loop, re-evaluate its assertion against the mission, not against the code. This is the dual of the anti-anchoring rule: anti-anchoring says prior dismissals don't bind; this says prior in-loop additions don't certify.

## 7.12 Global-mock + async combination

`use *Case` that defaults to `async: true` combined with `import Mock` / `with_mock` / `:meck.new/*`. `:meck` patches modules process-globally; concurrent tests in other files can observe the stubbed module. Requires `async: false` on any module using Mock. Flag as LEGIT — known flakiness hazard, not a style nit.

## 7.13 Mox in :global mode without `set_mox_from_context`

Similar concern when Mox is used across process boundaries.

## 7.14 Ecto Sandbox ownership leaks

`setup_all` that opens a DB connection without `allow`ing spawned processes — async tests that spawn tasks will see DB state from siblings.

## 7.15 Shared ETS / named processes

Tests that write to a named GenServer or ETS table without teardown leak state between runs.

## 7.16 Timer/clock reliance

`Process.sleep`, `DateTime.utc_now()` comparisons in assertions — flaky under load.

## 7.17 `:dbg.p(:all, :c)` global tracer

`:dbg.p(:all, :c)` attaches the tracer to ALL processes in the BEAM, not just the test process. Concurrent tests (especially `async: true` modules in the same VM) can fire trace events that contaminate the receiver's count.

Recommend `:dbg.p(specific_pid, :c)` scoped to the test's spawned process, or a baseline-diff approach (snapshot a counter before and after and assert on the delta) instead of an absolute count. Treat any `:dbg.p(:all, ...)` in a test file as LEGIT — it is a latent contaminator regardless of whether today's suite happens to pass.

## 7.18 Literal-integer call-count assertions

`assert 4 == :counters.get(...)`, `assert 2 == length(call_history)`, `assert N == Enum.count(...)` patterns are brittle to UNRELATED PR changes. A refactor that legitimately reduces a call count by one breaks the test even when behavior is correct, and a refactor that legitimately ADDS a call (e.g. a new audit log) does the same.

Prefer asserting outcome correctness (the right row exists, the right response shape is returned) plus, if Redis-traffic / call-count regression guards are genuinely needed, a SEPARATE telemetry-counted test isolated from outcome tests. When you see a literal-integer count assertion in a test, ask: "what does this break on if someone adds an unrelated call site?" — the answer is usually "this test, silently, in a different PR's CI."

## 7.19 `describe.skip` / `test.skip` / `it.skip` without an inline tracker reference

A skipped describe block silently accumulates into permanent dead coverage if the tracker isn't self-evident in the describe string. The skip target's name should carry an issue id or tracking-doc reference (`[P7.x — see TODO.md]`, `[LEG-123]`, `[blocked by ticket X]`) so a CI reporter shows the deferral without the reader having to grep the codebase.

A head-comment in the file is not a substitute — CI reporters render the describe string, not the comment. This is the test-suite analogue of "Author-acknowledged deviation is not exempt": the skip itself is the trigger to enforce a tracker reference.

The fix is mechanical: append `[<tracker-ref>]` to the skip string. Apply per-skip in the diff; do not bundle "all 21 skips" into a separate cleanup PR — the skip is touched by the diff just by existing in a file the diff modified.

## 7.20 `as any` / `as unknown as X` in test mocks

ESLint usually catches `as any` but it's worth flagging during review because mocks are where the type system is most often bypassed and where the runtime contract drifts silently. Tests should declare reusable mock types once (`type SessionMock = Awaited<ReturnType<typeof auth>>`) and reuse them across cases; the `as any` shortcut accumulates entropy as the test suite grows.

## 7.21 Test URL / response-shape assertions with weak regex

Per 7.10 Range-assertions: if the test setup knows exactly which fixture value should land in the assertion (a specific school id, a specific status, a specific message), pin to that value. A regex like `/school=/` matching ANY value can silently pass on broken scope filtering — the assertion proves a `school=` param appears, not that the RIGHT param appears. Same for `expect(body).toContain("error")` when the exact error string is known.

Mechanical fix: replace `/.../ ` with `/...=<expected-value>(?:[&#]|$)/` or `toEqual(specificValue)`.

---

These (7.12-7.21) are production-of-correctness issues, not style. A test suite with one of these hazards will eventually produce false greens on a PR that the review cannot catch by reading the diff alone.
