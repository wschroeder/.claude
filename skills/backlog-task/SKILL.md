---
name: backlog-task
description: Creates and verifies the bd (beads) backlog for one slice spec-task has already cut — checks preconditions against the design documents the cards will serve, reprints the slice's stories for a single approval, runs the create, dependency, label and spec-id commands, then reads bd back to prove the acceptance criteria and blocking edges actually stored. Use after spec-task has cut and reviewed a slice, when asked to create the cards or tickets for a specced slice, to put an approved slice into the backlog, or when a bd create batch needs verifying — "make the cards", "create the backlog", "file the tickets for S2".
---

# backlog-task — a cut slice in, a verified backlog out

1. For the slice named in $ARGUMENTS, respond with the sections below in order.
2. If $ARGUMENTS is empty, take the slice `spec-task` just cut, say which, and name the design documents its cards serve.
3. Make no bd write before Section 2 is approved; Section 2 is this template's only stop.
4. Run Section 1's command list in Section 3, and read Section 3's real ids back in Section 4.

## 0. Before Section 1, read your own room

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

1. If you are past the ceiling it reports, hand off BEFORE starting this template: say so, say that no section has run, write the handoff through `clear-task` yourself, and ask the operator to `/clear`. See [references/measurements.md](references/measurements.md).
2. Treat this check as deciding whether this phase starts here, separate from the check at the end, which governs the hand to the next phase.

## 1. Preconditions

1. Paste real output, not paraphrase:

```
$ pwd && git rev-parse --show-toplevel
$ ls -d .beads 2>&1
$ bd where 2>&1
$ git status --short
$ bd statuses
```

2. State four things: the slice being created, the design documents its cards will name as their spec id, whether bd is initialized here, and whether the tree is clean.
3. Count bd as initialized if `bd where` prints a database path, even when `ls` finds no `.beads/`, because inside a git worktree bd uses the main checkout's `.beads/`.
4. **Stop when the tree has uncommitted changes**, because a card's spec id would name a document whose content is absent from history. Say which file is dirty and wait.
5. **Say whether `demoable` is among the statuses.** If it is missing, put registering it, `bd config set status.custom "demoable:wip"`, into the same approval Section 2 asks for. See [references/measurements.md](references/measurements.md).
6. **Do not put bd, or any other tool of your own, into a repository the operator did not start.** Compare `git log --reverse --format=%ae | head -1` with the operator's address; if they differ and bd finds no database, create no cards, because `tdd-cycle` step 4d reads the tasks from the handoff.
7. If bd finds no database, make the first line of Section 3's list `bd init --skip-agents --skip-hooks -p <prefix>`; `spec-task/references/bd-commands.md` says why both flags are required.
8. Then print the command list verbatim, as `spec-task` Section 7 generated it, never rebuilt here.

## 2. Stop — approval before the first bd write

1. **Show the operator the stories and nothing below them**: who each one is for, what they will be able to do, and what they will look at to see it working. Leave out the tasks, requirement ids, blocking edges, and issue counts.
2. Leave no unknowns inside a story: each names who it is for and what they will be able to do, carries the acceptance criteria its card will be created with, and leaves them nothing to look up.
3. If a story still holds an open question, make that question the ask instead, and hold the creation behind it.
4. If `bd init` has to run first, say so in one line.
5. **Open the ask with the phase line**, directly above the question: the three phases in order, this stop's capitalized:

```
SPEC -> build -> demo
```

6. Then end the message with one question on one decision: build these stories, or change the slice. Recommend building them, and say the alternative is naming a story to hold back.
7. **Unattended, this stop is a line in a file.** Inside a `session-loop` run, create nothing, write `HANDOFF.md` through `clear-task` with a first line reading `BLOCKED:` and one sentence naming the slice awaiting approval, and stop. Write it through the skill rather than by hand, however close the ceiling is.
8. Never print the stories and run `bd create` in the same turn.
9. Treat approval here as covering this creation only; a later slice asks again, and pushing asks separately under `git-commit`, "Safety".

## 3. Creation

1. Run the Section 1 list and paste the real ids as they come back.
2. Use the per-issue form, one command per card, or `bd create --file` with a markdown file whose cards are `##` headings and whose fields are `###` sections: Description, Design, Acceptance Criteria, Labels, Priority, Type.
3. After any batch form, set each dependency with `bd dep <blocker> --blocks <blocked>` and each spec id with `bd update <id> --spec-id <document>`, because no batch form stores them.
4. Keep the cards flat, with no parent or epic cards.
5. Link two cards that touch without one waiting on the other with `bd dep relate <id> <related-id>`, never with a blocking edge.
6. Never use `bd create --graph` at any size, because it drops the acceptance criteria and only warns.
7. Never use the flat `Key: value` shape, because bd reports success and lands every field in the description as prose. bd's output for all three forms is in [../spec-task/references/bd-behavior.md](../spec-task/references/bd-behavior.md).
8. Write the file outside the repository, in a scratchpad, never as a new markdown file in the project.

## 4. Verification, by reading bd back

1. Paste real output, not a claim that it worked:

```
$ bd ready
$ bd show <first created id>
$ bd show <an id you expect to be blocked>
$ bd list --label slice:S<n> --status open
```

2. Check four things against what Section 3 pasted: `ACCEPTANCE CRITERIA` is present on the issue and matches the requirement text, `Spec:` names the design document the card serves, the ready list holds exactly the tasks with no blocker, and the slice lane holds exactly the cards this run created.
3. Check the dependency and the spec id on a card you expect to be blocked as well as on the first one.
4. Report a mismatch and leave it for `spec-task` to fix.

## 5. Where the work goes next

1. Name both handoffs, in one line each: `tdd-cycle` takes the cards, with each task's proof command as the test to drive to red first; when the slice's last card closes, `tdd-cycle` step 4d hands to `demo-task`, which hands to `spec-task`, which decides the next slice and returns here.
2. **The build runs as a `session-loop` run, not as a string of sessions the operator clears by hand.** Hand to `session-loop` rather than to a prompt for the operator to paste. See [references/measurements.md](references/measurements.md).
3. Commit the new cards before invoking it, because the loop refuses a dirty tree.
4. Run `bd export -o .beads/issues.jsonl` right before you stage that file, because bd writes its own export up to a minute late ([bd-behavior.md](../spec-task/references/bd-behavior.md)). In a git worktree, skip it, as that file's worktree section says. See [references/measurements.md](references/measurements.md).
5. Before invoking it, read your own room:

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

6. **Then invoke `session-loop`, in this turn, whatever that number says**, never only name it in a handoff. See [references/measurements.md](references/measurements.md).
7. If you are past the ceiling, invoke it anyway, because the loop's own step 2 writes the handoff through `clear-task`; say which section you stopped at and what it still owes, such as a record you have not worked or an answer the operator is waiting on.

## 6. Notes on what this template does NOT do

- Does not write or revise a design document. That is `spec-task`, which
  commits its edits before this template runs.
- Does not write to a design document. Nothing here does; see `spec-task`,
  "Two documents".
- Does not re-cut the slice or re-review the document. A gap found here is
  reported and left for `spec-task`.
- Does not implement, close, claim or update issues. That is `tdd-cycle`.
- Does not demo or take feedback. That is `demo-task`. Does not choose or
  size the next slice. That is `spec-task`.
- Does not run `bd init` before the Section 2 approval, or without
  `--skip-agents --skip-hooks`.
- Does not commit. `bd close` writes a tracked file, so staging belongs to
  whoever commits next, per `git-commit`.
- Does not push anything outward. The backlog stays local.
