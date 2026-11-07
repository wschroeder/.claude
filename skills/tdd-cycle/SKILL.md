---
name: tdd-cycle
description: Drives the probe → test → green → refactor TDD cycle — probing unfamiliar boundaries before writing the test, naming the public interface the test will assert against, writing one test that fails (red) against the observed shape, making it pass minimally, and refactoring structure only (rule-of-three, Open-Closed for additions across files; collapsing duplication and polishing names belong to the review that follows). Use when implementing new features test-first, when asked to use TDD, write tests first, follow red-green-refactor, or probe before building, and when told to continue implementing or build the next card. Reads `bd ready` to name the card each cycle builds, and after the commit moves it to demoable with a note carrying what the code does, each criterion clause marked met or not met, and the commit id — closing it belongs to demo-task, once somebody has watched it work.
---


## Purpose

1. Use this skill to build incrementally through a test-driven cycle, with tests leading the way.

## Companion skill — load first, every language

1. Load `writing-code` before writing the test: this skill drives the loop, and `writing-code` governs how the code and tests get written and which language skill applies.
2. For Elixir, let `writing-code` route on to `elixir-development` (pipe-style Ecto, schema `changeset/2` over `Ecto.Changeset.change/2`, test hygiene, `capture_log`, `Mock` requiring `async: false`).
3. Expect `writing-code` and `elixir-development` to load anywhere; the TypeScript skills and `elixir-migrations` live in a single project and will not load elsewhere.

## Execution Setup

1. Before running any `mix` commands, load the direnv environment (per `elixir-development`):
```bash
cd /path/to/project
eval "$(direnv export bash)"
mix test path/to/test.exs
```

## TDD Cycle

1. Run the cycle as **Probe → Gray → Red → Green → Refactor**: Probe observes unfamiliar boundaries before any test exists, Gray is a test written but not yet run, Red is the result of running it and seeing it fail, Green is when it passes, and Refactor fixes structure.
2. In Refactor, fix what the next test will attach to, and leave names, comments, and duplication to the review that follows.

### Before the cycle: name the card you are building

1. If the repository has a `.beads` directory, run `bd ready` and name the card this cycle will build: its id, its title, and the proof command in its acceptance criteria.
2. Run `bd show <id>` for its spec id, which names the design document holding the product rule behind it.
3. Drive that proof command to red in step 1; you are reading which card is unblocked, not choosing what to build.
4. If `bd ready` returns nothing while open cards exist, name the blocker holding them and stop rather than picking one anyway.
5. If no ready card covers the change you were asked for, edit nothing: say in one line that no card covers it, and hand the work to `spec-task`, both when the operator names the change directly and when it fixes something broken in a deployment.
6. Make one exception: for a fault the current slice made that its own demo found, `demo-task` sends it back here with no card, so name the demo finding in place of the card and build the fix.
7. If there is no `.beads` directory, say so in one line and carry on.

### A screen-only card skips the test

1. Treat a card as screen-only when its change alters only what a screen shows: markup, styles, wording, or images.
2. Treat a change that also reaches what the app stores, what it computes, or which route or permission serves a page as not screen-only.
3. For a screen-only card, write no test: build the change, open the screen and look at it after every edit (`writing-code` step 0), then run step 4's clause check and 4c.

### 0. Probe Boundaries (before writing the test)

1. Before writing the test, identify the boundaries it will touch: external APIs, database schemas, libraries you haven't used in this session, and framework conventions you're uncertain about.
2. For each, write a throwaway probe and paste its actual output into the conversation.
3. **Project probe mechanics.** If `project-probe` appears in the available skills, load it before writing the probe. If nothing is listed, run the probe by hand and say in one line that the project supplies no probe helper.
4. Make a probe one-shot: a curl, a SQL query, an IEx snippet, or a small script that confirms the shape of the boundary.
5. Cite the probe's output as a REF, and anchor step 1's test to that observation.
6. Count as a probe only something that **ran on this machine in the last few minutes and produced output in the chat**, never "the docs say", "I've used this before", or "based on the schema file", under the global Evidence Format's rule that design docs describe intent.
7. Exempt pure internal logic: probes are for boundaries you don't own.
8. Treat code you own that reads data a boundary produced, such as a model's reply, an uploaded file, or a third-party payload, as a boundary, and probe a real sample of that data before you write the test.
9. If fetching a fresh sample costs money, read one the app already stored from a fictional file, and if none exists, say so in the card note.
10. Read [references/probing.md](references/probing.md) for detail and exemptions.

### 1. Write the Test (Gray) and Run It (Red)

1. Ask what functionality needs to be implemented.
2. **Test what the audience sees, at the level of the feature, never a single module.**
3. **Write no test for behavior someone checked by hand when automating the check costs too much**, such as repeated calls to a paid API or a change that only moves a setting; say in one line who ran the hand check and what it found, then move on.
4. **Write no test for a constant**, such as a label's text, a list's members, or a setting, and no test that asserts only that a thing exists; `spec-task` proves a constant by reading it.
5. **Give each behavior one test, at the lowest level that can observe it.** Before you write a test, find the one that already proves this behavior, and add your case there or write nothing.
6. **Assert only what the test's title names**, and put an assertion about another step's output in that step's test.
7. **Assert what a person reads or what the system stores, never the markup around it.** If a state shows only through styling, add a stable attribute to the markup (`data-state="done"`) and assert that.
8. **Pin no output the code derives from another source**, such as a literal generated from a schema, a validator, or a table; test the conversion once, for every caller.
9. **Vary one thing per test**, and give a new input variant its own case.
10. **A card that only changes fixed text a person reads has no red step.** Apply the card's wording, run its read check until it prints what the card expects, and commit, all in one pass, with no probe.
11. Treat a sentence the app builds from data as behavior, which takes the full cycle.
12. **When the bug is something you saw on screen, test what it stopped the person doing**: perform that action in the test and assert the values the person reads afterward.
13. Run a layout test, such as whether a control fits its cell, only while working the design toward what the operator has in mind, delete it once the operator has looked at the result, and do not count the action test as covering the layout.
14. **A UI end-to-end test is temporary.** Use it while you build, keep it out of the feature's commit, and delete it once the operator has seen the result.
15. **Keep every test fast**, and never sleep in a test: wait on the condition itself, or control the clock.
16. **Name the interface before the test file exists**: say which public function or module the assertion will be written against, and in one line what a test there catches that a test one level up would miss.
17. Anchor the test against the probe output from step 0.
18. Write a single, focused test for that functionality (Gray).
19. Run the test and see it fail (Red) because the implementation doesn't exist yet.
20. Verify the test is testing what you think it is; a test that passes too easily, or fails for the wrong reason, doesn't count.

### 2. Implement Minimum Code (Green)

1. Write the minimum code needed to make the test pass, with no extra features or abstractions.
2. Run the test to verify it passes (Green).

### 3. Refactor (structure only)

1. Improve structure while keeping tests passing, and consider edge cases.
2. **What does NOT happen here.** Do not collapse duplication, rename for readability, or audit comments: `writing-code` governs those as the code is written, and `quick-review` 5.5, 2.2, and 6.3 own what is left.
3. **(a) Dead code the change orphaned.** With the green tests as your safety net, remove now-unreachable branches, helpers the change left with no caller, and commented-out blocks it stranded.
4. **(b) Rule-of-three pass.** If this green just landed the **3rd** same-shape edit across files, such as dispatcher arms, schema fields, registry registrations, event subscribers, or dashboard tiles, consider lifting to a registry, behaviour, dispatch table, or extension point, but ONLY if you can name the next concrete feature that will land against it: a file path, ticket, or named feature.
5. If you can't name the follow-on, ship the lockstep edit and revisit when a 4th case shows up.
6. **(c) Hindsight Open-Closed (in retrospect, not speculative).** When (b) triggers and you have a named follow-on, prefer extension points where new cases **register themselves**, such as behaviours, registries, dispatch tables, or plug pipelines, over a `case`/`cond` that grows an arm per case.
7. **Count *modifications to existing files*, not total files touched.** Treat additions that require lockstep edits across existing files as the signal, and expect a new case to add about one line to an existing registration point and otherwise live in new files.
8. **Run the count. Do not estimate it.** Before declaring the green done:

  ```bash
  # uncommitted work
  git status --porcelain | awk '{c=substr($0,1,2); p=substr($0,4)} c=="??"{n++; new=new"\n    + "p; next} {m++; mod=mod"\n    ~ "p} END{printf "OCP count: %d new file(s), %d existing file(s) modified%s%s\n", n+0, m+0, new, mod}'

  # a commit that already landed
  git show --name-status --format='' <ref> | awk -F'\t' '$1=="A"{n++; new=new"\n    + "$2; next} $1=="M"{m++; mod=mod"\n    ~ "$2} END{printf "OCP count: %d new file(s), %d existing file(s) modified%s%s\n", n+0, m+0, new, mod}'
  ```

9. Drop generated paths from the count before reading it, such as lockfiles, `.uid` and `.import` sidecars, and anything a build step writes. Then act on the number:
   - **2 or fewer existing files modified.** Nothing to do.
   - **3 to 7.** Read the modified list, not just the count. If the same file shows up for the same reason on consecutive additions, that file is the dispatcher. Name it in the handoff even if you do not lift it now.
   - **8 or more.** Stop. Either name the extension point and lift, or write one line in the commit body saying why the lockstep edit is right this time.
10. Exempt a fix; the count governs a change that *adds* a case, a feature, or a variant.
11. Print the count when you report the change, the same way the test result gets printed.
12. **(d) Re-run tests** to ensure nothing broke.

### 4. Self-Review (mandatory before declaring done)

1. After GREEN and before handing off or saying "complete", close these gates, and fix a failing gate in the loop.
2. Hand a decision to the user only when their answer changes the design or product behavior, such as which type, which name, or clear-vs-error; close a missing validation, an unguarded write, or a robustness fix yourself.
3. If you catch yourself writing "this is the user's call" or "doesn't block", treat it as a deferral and close the gate.

**4a. Check every clause against what you built, with or without tests.**

1. Split each acceptance criterion into its clauses: each bound, count, quantifier, and condition ("ten or fewer", "every"), and each member of a list a condition names ("a draft or an archived record" is two clauses).
2. Before the card moves, mark each clause met or not met, with its evidence beside it: the test that proves it and the run that printed its result, or, on a screen-only card, the screenshot that shows it.
3. Leave how strongly a test pins its clause to `quick-review`'s mutation check.
4. Mark a partly met clause not met, keep a card with any clause not met `in_progress`, and name the clause in its note.
5. Run this check even when the operator has turned tests off.
6. **If the data as it stands cannot meet a clause, build the data**: add records to the project's fictional data, or put existing fictional records into the state the clause needs and restore them afterwards.
7. Ask the operator only when no data you could make would meet the clause.
8. **No conditional assertions, and no skipped tests.** When the test controls its data, assert on that data every time it runs, never inside `if result:` or `if rows:`.
9. If the test does not control its data yet, give it a setup step that does.
10. If a test is marked skip, delete it.

**4b. Scope.**

1. Implement exactly the ask, with no drive-by refactors, no speculative abstractions, and no unrelated cleanup.
2. Revert any file in `git diff --stat` that the change does not directly require.
3. Keep the line count proportional to the ask.

**4c. The hand-off, when the work came from a tracked issue.**

1. Skip this when nothing tracks the work, and say in one line that you did.
2. Commit first, with no card id anywhere in the message, as `git-commit` requires.
3. **Stage by path, never `git add -u`**, because moving the card writes `.beads/interactions.jsonl`.
4. In a git worktree, skip the next two rules; you are in one when `bd where` prints a directory outside the current checkout.
5. Outside one, unstage bd's own `.beads/issues.jsonl` from a code commit with `git restore --staged .beads/issues.jsonl`.
6. Run `bd export -o .beads/issues.jsonl` right before you stage it for a commit that carries card changes.
7. Then move the card, with a note carrying three things: what the code now does, the clause list with its evidence, and the commit.
8. Move nothing on a working tree that still holds the change.
9. **The card moves only after step 10's reviews have run on its diff.** If you commit before them, leave the card `in_progress`, and if you hand off before they run, name in the handoff each card and the reviews it still owes. The order:

```
$ git commit -m "<what changed>"
  load quick-review with the Skill tool and run it on the commit, then
  security-review where writing-code's list calls for one; fix what they find
  and commit the fixes
$ bd update <id> --status demoable
$ bd note <id> "Board.can_move_down checks is_free(col, row+1) for every cell.
  Clause "every cell": board_test.exs:41 passed, 17 tests, 0 failures.
  Commit a1b2c3d. quick-review's full report printed in this session at
  14:02Z: 1 fix, 0 flags. Re-round after the fix to can_move_down re-read
  the diff with `git diff 9f8e7d6 -- .` at 14:09Z: nothing new."
```

10. **The card moves only after quick-review's full Output block has printed in this session's own output.** Make the note point to that printed report, with the time it printed and its count of fixes and flags; never let it stand in for the report.
11. If no Output block printed, the review did not run: leave the card `in_progress` and write `quick-review owed` in the note and the handoff.
12. Do not treat a budget line saying `finish the step you are on` as finishing a review that has not printed.
13. **Built is not done, and this loop cannot say it is.** Move the card to `demoable`, never closed; `demo-task` closes it once the operator has watched it work.
14. If `bd update --status demoable` is rejected, say in one line that the project has not registered the status, close the card with `bd close --reason` carrying the same three things, and carry on.
15. Leave the registering command, `bd config set status.custom "demoable:wip"`, to the project.
16. Never move a card with no commit behind it.
17. Leave everything else the finished diff owes to `quick-review`'s catalog, walked once by the review that follows this loop, and how the code and its logs are written to `writing-code`.

**4d. The slice, when the card you just moved was its last.**

1. Run `bd ready` and `bd list --label slice:S<n> --status open`.
2. If there is no `.beads` and the tasks live in the handoff, read its task list instead; every task done is the same empty lane.
3. When the slice's lane comes back empty, **the slice is built and this loop is over — hand to `demo-task`.**
4. Say in one line that the slice is built, then **invoke `demo-task` in that same turn**, without ending the turn first.
5. Do not specify the next slice, and do not summarize the slice in place of the demo.

### 5. Repeat

1. **A turn that names its own next step takes it, in the same turn**, such as the next card, the probe before it, or the section still to write.
2. If the next step needs the operator, such as an approval or a question only they can answer, put the ask last and say what to do.
3. Work out whether there are more test cases to add.
4. **Failure paths are the next tests, not a gate at the end.** Give every new error branch, every external call with a new error shape, and every new `else` arm its own test.
5. Continue the cycle, building up functionality incrementally.

## Key Principles

1. **One test at a time**: don't write multiple tests upfront.
2. **Small steps**: make each test cover one small piece of functionality.
3. **Build incrementally**: prefer working code piece by piece to a whole module that might get thrown away.
4. **Let tests guide design**: let the tests reveal the API and structure.

## Autonomous Behavior

When activated:
1. **Name what to test**: read `bd ready` for the card, or take the next
   failing case from the work in hand. Do not hand the choice back when you
   can make it.
2. **Probe the boundaries it touches**: For each external API, schema, or unfamiliar library the test will touch, run a throwaway probe and paste the output into the chat. Skip only for pure internal logic.
3. **Name the interface, then write one test**: say which public function or module the assertion attaches to, then create a focused test anchored to the probe output for that specific functionality
4. **Run it (should fail)**: Verify the test fails as expected (Red is the result, not a phase you start in)
5. **Implement minimum code**: Write just enough to pass
6. **Run it (should pass)**: Verify it works. Where the change reaches something a person sees or plays — a web page, a game scene, a desktop window, a terminal screen — run that thing too and use it by hand, then look at what changed before the next test, every green, not once at the end. `writing-code` step 0 says how
7. **Refactor structure if needed**: dead code the change orphaned, rule-of-three, the Open-Closed count — while tests pass. Duplication and name polish are review's, not this loop's
8. **Self-Review**: Close the Step 4 gates — every clause of each criterion marked met or not met with its evidence, scope, and the commit-and-hand-off receipt when an issue tracks the work — against your own diff. If one fails, return to step 3 or step 7 before moving on.
9. **Ask about next test**: "Should we add another test case, or move to different functionality?"
10. **Run the review sequence**: once the feature is done, use the running thing by hand one last time (`writing-code` step 0), then run `quick-review`, then `security-review` when `writing-code`'s list says the diff needs one, and work the fix loop — see `writing-code`, "After the edit: the review sequence is owed". The Step 4 gates close your own loop; they do not stand in for the review.

## After each task, read your own room

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

1. Run it each time a card or a handoff task passes its proof, and after every commit, before you start the next one.
2. If the reading is past the ceiling, hand off rather than starting the next card: write the handoff through `clear-task` and say you have, in the same turn, without asking permission first.
3. **On `finish the step you are on`, finish the card in hand, commit it, write the handoff through `clear-task` yourself, and stop.** Do not start the next card.
4. **On `keep going`, keep going**, and do not price the next card at what this whole session has cost.

## What NOT to Do

1. Don't write production code before tests.
2. Don't write a test at an interface you haven't named out loud first.
3. Don't write a test against an unfamiliar boundary without probing it first.
4. Don't substitute "the docs say" or "I've seen this API before" for an actual probe.
5. Don't write multiple tests at once.
6. Don't skip the refactor step.
7. Don't collapse duplication or polish names inside the loop; that is review's pass.
8. Don't add features not driven by tests.
9. Don't write complex implementations on first pass.
10. Don't ship an "extension" that requires modifying N existing files in lockstep.

## What TO Do

1. Probe unfamiliar boundaries before writing the test.
2. Name the interface the test asserts against before the test file exists.
3. Write one failing test against the observed shape.
4. Write minimum code to pass.
5. Refactor structure while green; leave duplication and name polish to review.
6. Use two structural levers, **(1) rule-of-three** and **(2) Hindsight Open-Closed** when *adding* a case requires editing many existing files, in retrospect and never speculatively.
7. Repeat, and let tests guide the design.
8. Hand the finished diff to the review sequence, because green is not done.
