# Tests the diff adds or changes

1. Read this file now, before Pass 1, when the diff adds, changes, or deletes a test. Angles 7.2, 7.8, 7.11, and 7.23 stay in the body.

## Contents

- 7.1 Failure path coverage
- 7.3 Refactored-code coverage
- 7.4 End-to-end path coverage
- 7.5 New external API without test mocks
- 7.6 Partial-chain tests masking gaps
- 7.7 Symmetry cross-check (Pass 5 × Pass 6)
- 7.9 Test-to-test assertion symmetry
- 7.10 Range-assertions are correctness gaps, not style
- 7.12 Global-mock + async combination
- 7.13 Mox in :global mode without `set_mox_from_context`
- 7.14 Ecto Sandbox ownership leaks
- 7.15 Shared ETS / named processes
- 7.16 Timer/clock reliance
- 7.17 `:dbg.p(:all, :c)` global tracer
- 7.18 Literal-integer call-count assertions
- 7.19 `describe.skip` / `test.skip` / `it.skip` without an inline tracker reference
- 7.20 `as any` / `as unknown as X` in test mocks
- 7.21 Test URL / response-shape assertions with weak regex
- 7.22 A fixed bug's test belongs to the feature, and asserts the symptom

1. Walk each angle below in the pass its number names, give it a disposition, and print its line in the Checklist under that pass.
2. Delete a test of screen markup that the diff breaks; do not update its expectation.
3. Walk 7.12-7.21, the hazards of test infrastructure, for every test the diff adds or edits.

## Checklist lines

```
Pass 7:
  7.1   Failure path coverage            test exists for external-call failure
  7.3   Refactored-code coverage         pre-refactor tests exist; if not, flag
  7.4   End-to-end path coverage         integration test for cross-module flow
  7.5   New external API without mocks   test files include fixture/mock
  7.6   Partial-chain tests masking gaps middle-layer mocked despite change
  7.7   Symmetry cross-check (Pass 5×6)  symmetric production changes → symmetric tests
  7.9   Test-to-test assertion symmetry  siblings assert same invariants
  7.10  Range-assertions correctness gap pin to exact value when known
  7.22  A fixed bug's test               the assertion goes into the feature test
                                          that had the hole, and asserts the
                                          symptom a person saw
                                          proof: quote that feature test's title
                                          and the line asserting the symptom; a
                                          test named for the bug, or no symptom
                                          line → finding
```

### 7.1 Failure path coverage

1. For every external call or side-effecting operation, check that a test covers its failure.

### 7.3 Refactored-code coverage

1. When code is extracted or restructured, name each behavior that had no test before the refactor.
2. Flag the missing test, not the refactoring.

### 7.4 End-to-end path coverage

1. For each changed path that crosses module boundaries, check that an integration test exercises the whole chain, not only each unit alone.

### 7.5 New external API without test mocks

1. When the diff adds a call to an outside service, check that the tests carry a mock or fixture for that call.

### 7.6 Partial-chain tests masking gaps

1. When the entry point's tests mock out a middle layer whose behavior the diff changed, flag that those tests do not exercise the change.

### 7.7 Symmetry cross-check (Pass 5 × Pass 6)

1. For each sibling change Pass 5 found, where function B got the same change as function A, check that B's change has its own test.
2. Flag B when only A's change has a test, even when the diff adds many tests.

### 7.9 Test-to-test assertion symmetry

1. Group sibling tests by setup and target.
2. Flag any invariant that one test in the group asserts and its siblings do not.

### 7.10 Range-assertions are correctness gaps, not style

1. Flag an assertion that permits several values when the correct value is known as a test-quality gap, never a style nit, such as a status in a list, a substring match on a specified message, or a not-nil check where an exact value is meant.
2. Require the assertion to pin the known status, message, or value.
3. Permit a range only when the test truly accepts every value in it, with a comment saying why.

### 7.12 Global-mock + async combination

1. Flag as LEGIT a module that runs `async: true`, including through a `use *Case` default, and uses `import Mock`, `with_mock`, or `:meck.new/*`.
2. Require `async: false` on any module that uses Mock.

### 7.13 Mox in :global mode without `set_mox_from_context`

1. Flag Mox in `:global` mode without `set_mox_from_context` when the mock crosses process boundaries, as for 7.12.

### 7.14 Ecto Sandbox ownership leaks

1. Flag a `setup_all` that opens a database connection without `allow`ing the processes the tests spawn.

### 7.15 Shared ETS / named processes

1. Flag a test that writes to a named GenServer or ETS table without teardown.

### 7.16 Timer/clock reliance

1. Flag `Process.sleep` and `DateTime.utc_now()` comparisons in assertions.

### 7.17 `:dbg.p(:all, :c)` global tracer

1. Treat any `:dbg.p(:all, ...)` in a test file as LEGIT, whether or not today's suite passes.
2. Recommend `:dbg.p(specific_pid, :c)` scoped to the test's spawned process, or a count taken before and after with the assertion on the difference.

### 7.18 Literal-integer call-count assertions

1. Flag an assertion of a literal call count, such as `assert 4 == :counters.get(...)` or `assert 2 == length(call_history)`.
2. Recommend asserting the outcome, such as the right row or the right response shape.
3. If a call-count guard is truly needed, recommend a separate telemetry-counted test kept apart from the outcome tests.

### 7.19 `describe.skip` / `test.skip` / `it.skip` without an inline tracker reference

1. Require every skipped test or describe block in a file the diff touches to carry an issue id or tracking-document reference in its name string, such as `[ABC-123]`.
2. Count a comment in the file as no reference.
3. Ask for the fix on each skip in this diff, by appending `[<tracker-ref>]` to the skip string, and never defer it to a separate cleanup.

### 7.20 `as any` / `as unknown as X` in test mocks

1. Flag `as any` and `as unknown as X` in test mocks.
2. Recommend declaring a mock type once, such as `type SessionMock = Awaited<ReturnType<typeof auth>>`, and reusing it across cases.

### 7.21 Test URL / response-shape assertions with weak regex

1. Apply 7.10 to URL and response assertions: when the setup knows the fixture value that should land, pin to it rather than to a regex that matches any value.
2. Give the fix as `/...=<expected-value>(?:[&#]|$)/` or `toEqual(specificValue)`.

### 7.22 A fixed bug's test belongs to the feature, and asserts the symptom

1. Put the assertion for a fixed bug into the feature test that missed it, never into a new test named after the bug.
2. Assert the symptom a person saw, such as the flag, the message, the status, or the page text, and never only a figure that implies it.
