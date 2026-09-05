---
name: tdd-cycle
description: Drives the probe → test → green → refactor TDD cycle — probing unfamiliar boundaries before writing the test, naming the public interface the test will assert against, writing one test that fails (red) against the observed shape, making it pass minimally, and refactoring structure only (rule-of-three, Open-Closed for additions across files; collapsing duplication and polishing names belong to the review that follows). Use when implementing new features test-first, when asked to use TDD, write tests first, follow red-green-refactor, or probe before building, and when told to continue implementing or build the next card. Reads `bd ready` to name the card each cycle closes, and closes it after the commit with a reason carrying what the code does, the mutation receipt and the commit id.
---

## Purpose
Guide through a test-driven development cycle, helping build incrementally with tests leading the way.

## Companion skill — load first, every language

Load `writing-code` before writing the test. This skill drives the loop; `writing-code` governs how the code and tests get written — comment discipline, naming over narration, error returns that match what callers destructure, keeping raw secrets out of logs, guarding at the function boundary, and which language skill applies. For Elixir it routes on to `elixir-development` (pipe-style Ecto, schema `changeset/2` over `Ecto.Changeset.change/2`, test hygiene, `capture_log`, `Mock` requiring `async: false`). Skipping it means writing the green code blind to the conventions it must follow.

`writing-code` and `elixir-development` are both global. The TypeScript skills and `elixir-migrations` live in a single project and will not load elsewhere.

## Execution Setup

Before running any `mix` commands, load the direnv environment (per `elixir-development`):
```bash
cd /path/to/project
eval "$(direnv export bash)"
mix test path/to/test.exs
```

## TDD Cycle

The cycle is **Probe → Gray → Red → Green → Refactor**. Probe observes unfamiliar boundaries before any test exists. Gray is the state where the test has been written but not yet run — its outcome is unknown. Red is what happens when you run it and it fails (the *result* of running, not a starting phase). Green is when it passes. Refactor is when you fix structure — what the next test will attach to — not when you tidy names, comments or duplication; those belong to the review that follows.

### Before the cycle: name the card you are building

If the repository has a `.beads` directory, run `bd ready` and name the card this cycle will close — its id, its title, and the proof command in its acceptance criteria. `backlog-task` created these cards from a design document and put that proof command there; `bd show <id>` prints its `--spec-id` when you need the requirement behind it. That proof command is the test to drive to red in step 1. You are not choosing what to build here; you are reading which card is unblocked.

If `bd ready` returns nothing while open cards exist, name the blocker holding them and stop rather than picking one anyway. If there is no `.beads` directory, say so in one line and carry on — the cycle does not require a backlog.

### 0. Probe Boundaries (before writing the test)

Before writing the test, identify boundaries it will touch — external APIs, database schemas, libraries you haven't used in this session, framework conventions you're uncertain about. For each, write a throwaway probe and paste its actual output into the conversation.

**Project probe mechanics.** If `project-probe` appears in the available skills, load it before writing the probe — it holds how this project builds, runs and cleans up a throwaway probe, including the failure modes that report success. Where nothing is listed, run the probe by hand and say in one line that the project supplies no probe helper.

- A probe is one-shot: a curl, a SQL query, an IEx snippet, a small script. Its purpose is to confirm the shape of the boundary before you encode an expectation about it.
- The probe's output becomes a REF. The test you write in step 1 is anchored to that observation, not to a pattern-matched guess.
- A probe is something that **ran on this machine in the last few minutes and produced output in the chat.** "The docs say," "I've used this before," and "based on the schema file" are not probes — see Rule 11 in the global Evidence Format.
- Pure internal logic is exempt. Probes are for boundaries you don't own; tests cover the surfaces you do.
- Detail, exemptions and rationale: [references/probing.md](references/probing.md).

Without this step, the test in step 1 encodes an assumption rather than an observation, and Red → Green can both pass while the live boundary behaves differently — the test was wrong, not the code.

### 1. Write the Test (Gray) and Run It (Red)
- Ask what functionality needs to be implemented
- **Name the interface before the test file exists.** Say which public function or module the assertion will be written against, and in one line what a test there catches that a test one level up would miss. Leave it unnamed and the assertion lands wherever it is cheapest to write, which is usually an internal — and step 4a cannot catch that, because mutating an internal the test calls directly always fails the test.
- Anchor the test against the probe output from step 0 — the test asserts behavior you've observed at the boundary, not behavior you've imagined
- Write a single, focused test for that functionality. At this point the test exists but hasn't run yet — that's Gray.
- Run the test; it should fail (Red) because the implementation doesn't exist yet
- Verify the test is actually testing what you think it is — a test that passes too easily, or fails for the wrong reason, doesn't count

### 2. Implement Minimum Code (Green)
- Write the minimum code needed to make the test pass
- Don't add extra features or abstractions yet
- Focus on making the test pass, not on perfect code
- Run the test to verify it passes (Green)

### 3. Refactor (structure only)
- Improve structure while keeping tests passing
- Consider edge cases or improvements
- **What does NOT happen here.** Collapsing duplication, renaming for readability, and auditing comments. `writing-code` governs names and comments as the code is written, and the review that follows this loop owns what is left: `quick-review` 5.5 runs the deletion test on near-identical helpers, 2.2 and 6.3 catch names and comments that lie. Running those passes here means paying for them twice.
- **(a) Dead code the change orphaned.** With the green tests as your safety net, remove now-unreachable branches, helpers the change left with no caller, and commented-out blocks it stranded. This one stays in the loop: no review pass downstream looks for it, and you are the only reader who knows what this change orphaned.
- **(b) Rule-of-three pass.** If this green just landed the **3rd** same-shape edit across files (dispatcher arms, schema fields, registry registrations, event subscribers, dashboard tiles), pause and consider lifting to a registry / behaviour / dispatch table / extension point — but ONLY if you can name the next concrete feature that will land against it: a file path, ticket, or named feature, not a vague articulation. If you can't name the follow-on, ship the lockstep edit and revisit when a 4th case shows up. One is a function; two is a coincidence; three is a pattern; lifting without a named follow-on is premature abstraction.
- **(c) Hindsight Open-Closed (in retrospect, not speculative).** Don't design abstractions ahead of time. *Recognize* them in retrospect — when (b) triggers AND you have a named follow-on, prefer OCP-shaped lift targets: extension points where new cases **register themselves** rather than require editing a central dispatcher. Behaviours, registries, dispatch tables, plug pipelines — over a `case`/`cond` that grows an arm per case. The signal is always backwards-looking: "this case I just landed required edits across N existing files; the next one will too unless I lift now."

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
  Rationale: [references/open-closed.md](references/open-closed.md).
- **(d) Re-run tests** to ensure nothing broke.

### 4. Self-Review (mandatory before declaring done)

After GREEN and before handing off or saying "complete", close these gates.
A failing gate is fixed in the loop, not reclassified as a "design question" and
handed to the user to defer it. Hand a decision to the user only when their answer
changes the design or product behavior (which type, which name, clear-vs-error). A
missing validation, an unguarded write, or a robustness fix is a gate to close, not
a question to ask — the tell that you are rationalizing a deferral is catching
yourself writing "this is the user's call" or "doesn't block."

**4a. Assertion strength — prove it by mutation, not by reading.** Mutate the production code to a wrong-but-plausible value and re-run that one test. If it STILL PASSES, the assertion doesn't pin the behavior — that gap is real, and the green-on-broken-code output is your proof of it. Tighten the assertion (pin to the exact value: `== 502` not `in [400, 502]`; the exact message not `=~ "error"`; `== expected` not `refute is_nil`) and re-run until the same mutation makes it FAIL. A range assertion that survives mutation requires explicit justification — it is not default good practice. Judging an assertion "specific enough" by reading it is the satisficing this gate exists to kill; the mutation is the disposition, the sentence is not.

**Which assertions.** Every assertion named by a requirement's proof command, plus every assertion the diff adds on a behavior a caller depends on. "A behavior that matters" is not the scope, because the judgement of what matters is made by the same reasoning that is about to skip the check. Measured: in one run, three assertions survived mutation — a four-cell shape cut to three cells, and an entire rotation state replaced with garbage, both left a 17-test suite fully green — and all three sat under assertions their author had judged not to matter.

**The receipt.** Name the mutation and paste the line the run printed:

```
mutated <file>:<line>  <original expression> -> <mutated expression>
  15 successes / 2 failures        caught
```

"Assertions mutation-verified" is a summary, and a summary cannot be checked without redoing the work. Five beads in that same run closed carrying exactly that phrase; three of them do not survive checking. The receipt goes wherever the next reader looks — the commit message, the issue's close reason, or the handoff.

**4b. Scope.** You implemented exactly the ask — no drive-by refactors, no
speculative abstractions, no unrelated cleanup. Every file in `git diff --stat` is
directly required by the change; if one isn't, revert it. Line count proportional to
the ask: a one-line bug does not carry a 200-line diff.

**4c. The close, when the work came from a tracked issue.** Skip this when nothing tracks the work, and say in one line that you did.

Commit before closing, and name the issue in the subject. **Stage by path, never `git add -u`** — `bd close` writes `.beads/interactions.jsonl`, so the close you are about to run dirties a tracked file that the next card would otherwise sweep into its commit. Then close with a reason carrying three things: what the code now does, the 4a receipt, and the commit. Nothing is closed on a working tree that still holds the change:

```
$ git commit -m "<id>: <what changed>"
$ bd close <id> --reason "Board.can_move_down checks is_free(col, row+1) for
  every cell. Mutated cell.row + 1 -> cell.row: 15 successes / 2 failures,
  caught. Commit a1b2c3d."
```

A closed issue with no commit is a claim that work happened, contradicted by the repository. Measured: one run closed six issues while the tree held one commit — `bd init` — and five files that had never been committed at all.

Everything else the finished diff owes — doc and code agreeing, sibling symmetry,
duplication across near-identical helpers, names and comments that lie, behavioral
regression, whether a test reaches the branch it names, empty-value semantics — is
`quick-review`'s catalog, walked once by the review that follows this loop instead
of twice. How the code and its logs are written is `writing-code`.

**4d. The slice, when the card you just closed was its last.** Run `bd ready`
and `bd list --label slice:S<n> --status open`. When the slice's lane comes
back empty, **the slice is finished and this loop is over — hand to
`demo-task`.** It runs every proof command, builds the demo the
operator operates themselves, and takes their feedback; none of that is
this skill's job and none of it happens if you go straight to the next
slice. Say in one line that the slice closed, then **invoke
`demo-task` in that same turn**. Do not end the turn first: naming the
hand-off and stopping leaves the operator to type the instruction this step
exists to make unnecessary. Do not specify the next slice, and do not
summarize the slice in place of the demo.

### 5. Repeat
- Ask if there are more test cases to add
- **Failure paths are the next tests, not a gate at the end.** Every new error
  branch, every external call with a new error shape, every new `else` arm gets
  its own test. A test that asserts only happy-path behavior is half a test.
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
3. **Name the interface, then write one test**: say which public function or module the assertion attaches to, then create a focused test anchored to the probe output for that specific functionality
4. **Run it (should fail)**: Verify the test fails as expected (Red is the result, not a phase you start in)
5. **Implement minimum code**: Write just enough to pass
6. **Run it (should pass)**: Verify it works
7. **Refactor structure if needed**: dead code the change orphaned, rule-of-three, the Open-Closed count — while tests pass. Duplication and name polish are review's, not this loop's
8. **Self-Review**: Close the Step 4 gates — mutation, scope, and the commit-and-close receipt when an issue tracks the work — against your own diff. If one fails, return to step 3 or step 7 before moving on.
9. **Ask about next test**: "Should we add another test case, or move to different functionality?"
10. **Run the review sequence**: once the feature is done, run `quick-review` then `security-review` against the diff and work the fix loop — see `writing-code`, "After the edit: the review sequence is owed". The Step 4 gates close your own loop; they do not stand in for the review.

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
❌ Don't write a test at an interface you haven't named out loud first
❌ Don't write a test against an unfamiliar boundary without probing it first
❌ Don't substitute "the docs say" or "I've seen this API before" for an actual probe
❌ Don't write multiple tests at once
❌ Don't skip the refactor step
❌ Don't collapse duplication or polish names inside the loop — that is review's pass, and doing it here pays for it twice
❌ Don't add features not driven by tests
❌ Don't write complex implementations on first pass
❌ Don't ship an "extension" that requires modifying N existing files in lockstep — that's the OCP violation, not a successful refactor

## What TO Do

✅ Probe unfamiliar boundaries before writing the test
✅ Name the interface the test asserts against before the test file exists
✅ Write one failing test against the observed shape
✅ Write minimum code to pass
✅ Refactor structure while green; leave duplication and name polish to review
✅ Two structural levers, named: **(1) rule-of-three**, **(2) Hindsight Open-Closed** when *adding* a case requires editing many existing files. Apply in retrospect, never speculatively.
✅ Repeat
✅ Let tests guide the design
✅ Hand the finished diff to the review sequence — green is not done
