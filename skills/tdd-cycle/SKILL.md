---
name: tdd-cycle
description: Drives the probe → test → green → refactor TDD cycle — probing unfamiliar boundaries before writing the test, then writing one test that fails (red) against the observed shape, making it pass minimally, and refactoring with DRY locally and Open-Closed for additions across files. Use when implementing new features test-first or when asked to use TDD, write tests first, follow red-green-refactor, or probe before building.
activation:
  - "tdd"
  - "test-driven"
  - "test driven development"
  - "write test first"
  - "red green refactor"
---

## Purpose
Guide through a test-driven development cycle, helping build incrementally with tests leading the way.

## Companion skill — load first, every language

Load `writing-code` before writing the test. This skill drives the loop; `writing-code` governs how the code and tests get written — comment discipline, naming over narration, and which language skill applies. For Elixir it routes on to `elixir-development` (pipe-style Ecto, schema `changeset/2` over `Ecto.Changeset.change/2`, test hygiene, `capture_log`, `Mock` requiring `async: false`). Skipping it means writing the green code blind to the conventions it must follow.

`writing-code` and `elixir-development` are both global. The TypeScript skills and `elixir-migrations` live in a single project and will not load elsewhere.

## Execution Setup

Before running any `mix` commands, load the direnv environment (per `elixir-development`):
```bash
cd /path/to/project
eval "$(direnv export bash)"
mix test path/to/test.exs
```

## TDD Cycle

The cycle is **Probe → Gray → Red → Green → Refactor**. Probe observes unfamiliar boundaries before any test exists. Gray is the state where the test has been written but not yet run — its outcome is unknown. Red is what happens when you run it and it fails (the *result* of running, not a starting phase). Green is when it passes. Refactor is when you clean up.

### 0. Probe Boundaries (before writing the test)

Before writing the test, identify boundaries it will touch — external APIs, database schemas, libraries you haven't used in this session, framework conventions you're uncertain about. For each, write a throwaway probe and paste its actual output into the conversation.

**Project probe mechanics.** If `project-probe` appears in the available skills, load it before writing the probe — it holds how this project builds, runs and cleans up a throwaway probe, including the failure modes that report success. Where nothing is listed, run the probe by hand and say in one line that the project supplies no probe helper.

- A probe is one-shot: a curl, a SQL query, an IEx snippet, a small script. Its purpose is to confirm the shape of the boundary before you encode an expectation about it.
- The probe's output becomes a REF. The test you write in step 1 is anchored to that observation, not to a pattern-matched guess.
- A probe is something that **ran on this machine in the last few minutes and produced output in the chat.** "The docs say," "I've used this before," and "based on the schema file" are not probes — see Rule 11 in the global Evidence Format.
- Pure internal logic is exempt. Probes are for boundaries you don't own; tests cover the surfaces you do.

Without this step, the test in step 1 encodes an assumption rather than an observation, and Red → Green can both pass while the live boundary behaves differently — the test was wrong, not the code.

### 1. Write the Test (Gray) and Run It (Red)
- Ask what functionality needs to be implemented
- Anchor the test against the probe output from step 0 — the test asserts behavior you've observed at the boundary, not behavior you've imagined
- Write a single, focused test for that functionality. At this point the test exists but hasn't run yet — that's Gray.
- Run the test; it should fail (Red) because the implementation doesn't exist yet
- Verify the test is actually testing what you think it is — a test that passes too easily, or fails for the wrong reason, doesn't count

### 2. Implement Minimum Code (Green)
- Write the minimum code needed to make the test pass
- Don't add extra features or abstractions yet
- Focus on making the test pass, not on perfect code
- Run the test to verify it passes (Green)

### 3. Refactor
- Improve the code quality while keeping tests passing
- Consider edge cases or improvements
- **(a) DRY pass.** Collapse in-function and single-file duplication. Extract helpers, fold parallel branches, kill copy-paste within the unit you just touched.
- **(b) Readability pass.** With the green tests as your safety net: rename accurate-but-unclear names so the next reader doesn't have to decode them (distinct from 4a, which fixes names that *lie* — here you improve names that are truthful but hard to read); remove dead code the change orphaned — now-unreachable branches, unused helpers, commented-out blocks; and audit the comments you touched, deleting any that narrate *what* the code does and keeping only those that explain a non-obvious *why*.
- **(c) Rule-of-three pass.** If this green just landed the **3rd** same-shape edit across files (dispatcher arms, schema fields, registry registrations, event subscribers, dashboard tiles), pause and consider lifting to a registry / behaviour / dispatch table / extension point — but ONLY if you can name the next concrete feature that will land against it: a file path, ticket, or named feature, not a vague articulation. If you can't name the follow-on, ship the lockstep edit and revisit when a 4th case shows up. One is a function; two is a coincidence; three is a pattern; lifting without a named follow-on is premature abstraction.
- **(d) Hindsight Open-Closed (in retrospect, not speculative).** Don't design abstractions ahead of time. *Recognize* them in retrospect — when (c) triggers AND you have a named follow-on, prefer OCP-shaped lift targets: extension points where new cases **register themselves** rather than require editing a central dispatcher. Behaviours, registries, dispatch tables, plug pipelines — over a `case`/`cond` that grows an arm per case. The signal is always backwards-looking: "this case I just landed required edits across N existing files; the next one will too unless I lift now."

  **The measurement: count *modifications to existing files*, not total files touched.** A new feature/case under an OCP-compliant design lands almost entirely in *new* files (a new module plus its registration). The smell is when adding a case forces edits to many existing files — dispatcher + call sites + tests + docs + schema. Fixes naturally update existing code; that's not the OCP signal. The OCP signal is when **additions** require lockstep edits across the existing codebase. A new case should add ~1 line to an existing registration point and otherwise live in new files; needing to modify 8 existing files to introduce one new case means the structure is closed to the extension you're actually trying to perform.

  **Run the count. Do not estimate it.** Before declaring the green done:

  ```bash
  # uncommitted work
  git status --porcelain | awk '{c=substr($0,1,2); p=substr($0,4)} c=="??"{n++; new=new"\n    + "p; next} {m++; mod=mod"\n    ~ "p} END{printf "OCP count: %d new file(s), %d existing file(s) modified%s%s\n", n+0, m+0, new, mod}'

  # a commit that already landed
  git show --name-status --format='' <ref> | awk -F'\t' '$1=="A"{n++; new=new"\n    + "$2; next} $1=="M"{m++; mod=mod"\n    ~ "$2} END{printf "OCP count: %d new file(s), %d existing file(s) modified%s%s\n", n+0, m+0, new, mod}'
  ```

  Drop generated paths from the count before reading it — lockfiles, `.uid` and `.import` sidecars, anything a build step writes. Then act on the number:

  - **2 or fewer existing files modified.** Nothing to do.
  - **3 to 7.** Read the modified list, not just the count. If the same file shows up for the same reason on consecutive additions, that file is the dispatcher. Name it in the handoff even if you do not lift it now.
  - **8 or more.** Stop. Either name the extension point and lift, or write one line in the commit body saying why the lockstep edit is right this time. Do not pass this silently.

  A fix is exempt — fixes change existing code by definition. The count governs a change that *adds* a case, a feature, or a variant.

  Print the count when you report the change, the same way the test result gets printed. A measurement nobody prints is a measurement nobody makes.

  **Why this matters in the AI era.** Modifying many existing files burns scarce context on two fronts: humans can only hold so much in their head before the structure calcifies, and AI agents have bounded context windows plus per-token costs that scale with files-read-and-edited per change. OCP isn't aesthetic — it's a hard cost lever on both human cognitive load and agent token spend, and a codebase that violates OCP gets disproportionately more expensive to evolve as it grows.
- **(e) Re-run tests** to ensure nothing broke.

### 4. Self-Review (mandatory before declaring done)

After GREEN and before handing off or saying "complete", walk this checklist against your own diff. Each item is a gate — not a suggestion. If any check fails, return to RED or REFACTOR. Do NOT declare done with open items.

A failing gate is fixed in the loop, not reclassified as a "design question" and handed to the user to defer it. Hand a decision to the user only when their answer changes the design or product behavior (which type, which name, clear-vs-error). A missing validation, an unguarded write, or a robustness fix is a gate to close, not a question to ask — the tell that you are rationalizing a deferral is catching yourself writing "this is the user's call" or "doesn't block."

**4a. Doc/code coherence.** Every comment, docstring, `@moduledoc`, `@doc`, function name, and variable name you touched OR left adjacent to touched code: verify the code now does exactly what the prose/name says. Stale comments and misleading names are the #1 class of bug that passes tests and fails review. A function named `validate_*` must actually validate. A comment claiming "X is checked" must be checked in the body below it.

**4b. Adjacent-pattern symmetry.** If you fixed one bang-call / missing guard / silent swallow / unsafe interpolation, grep the same file for siblings. Same bug class in a neighbor function? Fix or justify skipping. If you added a guard clause, does a parallel code path need the same guard?

**4c. Failure-path coverage.** Every new `{:error, _}` branch needs a test that exercises it. Every external call (library, API, DB) with a new error shape needs a failure-path test. New `else` arm? Test it. A test that asserts only happy-path behavior is half a test.

**4d. Error handling consistency.** New error tuples must flow through existing `else` / `case` branches. No silent fall-through. No `{:error, _}` shapes that callers pattern-match but don't handle. Error return types must match what callers destructure.

**4e. Test hygiene.** Test modules using `import Mock` / `with_mock` / `:meck` MUST be `async: false` (:meck patches modules process-globally). Tests assert observable outcomes (DB state, return values, status codes, session keys) — not log content, unless the log IS the ops-facing contract. No `capture_log` wrapping a test that makes no log assertion.

**4f. Scope.** You implemented exactly the ask — no drive-by refactors, no speculative abstractions, no unrelated cleanup. Every file in `git diff --stat` is directly required by the change. If one isn't, revert it.

**4g. Sensitive data in logs.** No log line contains raw tokens, codes, verifiers, secrets, emails, IPs, request bodies, full changesets, or `inspect` of structs that may include any of those. Warnings are noise: a log that fires on expected behavior → delete it; a log that needs human attention → `Logger.error` with presence flags / field keys only, never raw content.

**4h. Diff sweep.** Read your own `git diff` end-to-end one final time. Line count proportional to the ask (a 1-line bug should not have a 200-line diff). Anything you wouldn't be comfortable explaining to a reviewer, fix or remove before declaring done.

**4i. Behavioral regression.** For every touched function with existing callers, compare the new return / side-effect to what the old code produced. Read the pre-change version — don't just trust the new tests. If the new behavior differs from what callers received before, either that's the bug you intentionally fixed (document it) or it's an unintended regression (revert or adjust). Silent contract changes are the most expensive class of review miss.

**4j. Defense-in-depth in isolation.** Read each new/changed function assuming an UNTRUSTED caller — not the nice caller you designed around. If the function relies on "my caller validates X before calling me," guard at the function boundary too. Any future refactor can break the caller's validation without touching this function; the boundary guard is insurance.

**4k. Same-module sibling consistency (static).** Grep sibling functions with similar signatures in the same file. If `find/3` has `when is_binary(x)` + a fallback clause but `find_and_do/4` doesn't, the inconsistency is a latent bug even if nobody triggers it today. Don't require an upstream change to justify the fix — static inconsistency alone is the finding.

**4l. Test intent vs test effect.** Read each new test's body end-to-end. Does execution actually reach the branch the test's name claims to exercise, or does an earlier guard / validation / nil check short-circuit before that branch runs? A "rejects malformed JSON" test that hits a session-nil check before JSON parsing has never exercised malformed-JSON handling. The test's name lies; the code path is untested.

**4m. Test-to-test assertion symmetry.** Sibling tests (same setup pattern, adjacent in the file, testing the same surface from different angles) should assert the same invariants. If one test in a group checks `used_at is nil` / `:counters.get(_, 1) == 0` / a specific error shape, the siblings should too — otherwise the invariant is enforced in only one branch, and the next regression hides in the siblings.

**4n. Data precedes code.** When the diff adds validation at write-time (registration, insertion, changeset) that didn't exist before, ask: do pre-existing rows in the DB satisfy the new invariant? A hardening that tightens what `create_foo` accepts does NOT retroactively validate rows inserted before. If consumers trust the stored field (e.g., exact-match on a redirect URI), they'll accept legacy rows that the new write-path would reject. Either add a read-time guard that re-validates each row OR plan a data migration. Grep every stored field the new validation protects; check every consumer for re-validation.

**4o. Assertion strength — prove it by mutation, not by reading.** For each assertion the diff adds on a behavior that matters, mutate the production code to a wrong-but-plausible value and re-run that one test. If it STILL PASSES, the assertion doesn't pin the behavior — that gap is real, and the green-on-broken-code output is your proof of it. Tighten the assertion (pin to the exact value: `== 502` not `in [400, 502]`; the exact message not `=~ "error"`; `== expected` not `refute is_nil`) and re-run until the same mutation makes it FAIL. A range assertion that survives mutation requires explicit justification — it is not default good practice. Judging an assertion "specific enough" by reading it is the satisficing this gate exists to kill; the mutation is the disposition, the sentence is not.

**4p. Empty-value semantics.** For every field in the diff that could be empty (`[]`, `""`, `0`, missing key, empty MapSet), trace the application's behavior when it IS empty. Three distinct meanings often collapse in code: "nothing requested" (fall back / no-op), "everything" (wildcard — often dangerous), or "invalid — reject." Pick explicitly and confirm the code matches the product intent. A predicate that returns `false` for an empty input (e.g., `covers?(_, _, [])` returning `false`) can silently break UX loops like consent prompts that re-fire forever. Ask: "does the UX make sense if this is empty?"

### 5. Repeat
- Ask if there are more test cases to add
- Continue the cycle
- Build up functionality incrementally

## Key Principles

- **One test at a time**: Don't write multiple tests upfront
- **Small steps**: Each test should cover one small piece of functionality
- **Build incrementally**: Better to have working code piece-by-piece than a whole module that might get thrown away
- **Let tests guide design**: Tests reveal the API and structure naturally

## Autonomous Behavior

When activated:
1. **Ask what to test**: "What functionality should we implement next?"
2. **Probe the boundaries it touches**: For each external API, schema, or unfamiliar library the test will touch, run a throwaway probe and paste the output into the chat. Skip only for pure internal logic.
3. **Write one test**: Create a focused test anchored to the probe output for that specific functionality
4. **Run it (should fail)**: Verify the test fails as expected (Red is the result, not a phase you start in)
5. **Implement minimum code**: Write just enough to pass
6. **Run it (should pass)**: Verify it works
7. **Refactor if needed**: Clean up while tests pass
8. **Self-Review**: Walk the Step 4 checklist (4a–4p) against your own diff. Do NOT skip. If any gate fails, return to step 3 or step 7 before moving on.
9. **Ask about next test**: "Should we add another test case, or move to different functionality?"

## Example Flow

**User**: "I need a function to validate email addresses"

**Claude**:
```elixir
# Step 1: Write test (Red)
test "validate_email returns :ok for valid email" do
  assert Validator.validate_email("user@example.com") == :ok
end
```

Run test - should fail since function doesn't exist.

```elixir
# Step 2: Implement minimum (Green)
def validate_email(email) when is_binary(email) do
  :ok
end
```

Run test - passes!

**Claude**: "Should we add test cases for invalid emails?"

**User**: "Yes"

```elixir
# Step 3: Next test (Red again)
test "validate_email returns error for invalid email" do
  assert Validator.validate_email("not-an-email") == {:error, :invalid_format}
end
```

And so on...

## What NOT to Do

❌ Don't write production code before tests
❌ Don't write a test against an unfamiliar boundary without probing it first
❌ Don't substitute "the docs say" or "I've seen this API before" for an actual probe
❌ Don't write multiple tests at once
❌ Don't skip the refactor step
❌ Don't add features not driven by tests
❌ Don't write complex implementations on first pass
❌ Don't ship an "extension" that requires modifying N existing files in lockstep — that's the OCP violation, not a successful refactor

## What TO Do

✅ Probe unfamiliar boundaries before writing the test
✅ Write one failing test against the observed shape
✅ Write minimum code to pass
✅ Refactor while green
✅ Two refactor levers, named: **(1) DRY** locally, **(2) Hindsight Open-Closed** when *adding* a case requires editing many existing files. Apply in retrospect, never speculatively.
✅ Repeat
✅ Let tests guide the design
