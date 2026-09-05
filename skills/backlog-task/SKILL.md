---
name: backlog-task
description: Creates and verifies the bd (beads) backlog for one approved slice from a design document that already exists — checks preconditions against the document, reprints the slice's stories for a single approval, runs the create, dependency and label commands one at a time, then reads bd back to prove the acceptance criteria and blocking edges actually stored. Use after spec-task has written and reviewed a design document, when asked to create the cards or tickets for a specced slice, to put an approved slice into the backlog, or when a bd create batch needs verifying — "make the cards", "create the backlog", "file the tickets for S2".
---

# backlog-task — a reviewed design document in, a verified backlog out

For the design document and slice named in $ARGUMENTS, respond with the
sections below in order. If $ARGUMENTS is empty, the document is the one
`spec-task` just wrote and the slice is the one it marked `building` — say
which, with its path.

`spec-task` produces the input and stops here. The first bd write happens
after Section 2 is approved, and Section 2 is this template's only stop.

Order is enforced: Section 1's command list is what Section 3 runs, and
Section 3's real ids are what Section 4 reads back. A Section 3 that
reported success while creating nothing surfaces in Section 4 as a
`bd show` that fails on its own pasted id.

## 1. Preconditions, read from the document

Real output, not paraphrase:

```
$ pwd && git rev-parse --show-toplevel
$ ls -d .beads 2>&1
$ git status --short <document path>
$ grep -c '^\[R' <document path>
```

State four things: the document's path, the slice being created, whether
bd is initialized here, and whether the document is committed.

**Stop when the document has uncommitted changes.** `spec-task` Section 8
commits it, and on a dirty tree the beads would point at a path whose
content is absent from history. Say which file is dirty and wait.

Where `.beads/` is absent, the first line of Section 3's list is
`bd init --skip-agents --skip-hooks -p <prefix>`. `spec-task` Section 1
carries the measurements behind both flags.

Then print the command list verbatim, as `spec-task` Section 7 generated
it. A list rebuilt here would specify something the reviewed document does
not.

## 2. Stop — approval before the first bd write

The operator is approving a slice of behavior. Two things reach them, in
this order.

**Lead with the stories, in full**, in the shape `spec-task` Section 6
printed them — role, what they can do, the tasks, the proof. That list is
the whole of what they should have to read to decide.

**A story the operator can decide on has no unknowns left inside it.** Each
one names who it is for and what they will be able to do, carries the
acceptance criteria its card will be created with, and leaves them nothing to
look up. Where a story still holds an open question, that question is the ask
instead, and the creation waits behind it.

Then the mechanics, in at most three lines: whether `bd init` runs first,
how many issues get created, and whatever else in the repository changes.

**Open the ask with the phase line**, directly above the question — the
four phases in order, this stop's capitalized:

```
PLAN -> build -> demo -> retro
```

Then ask, per CLAUDE.md "When you need an answer, the ask goes last and
says what to do". One decision: build these stories, or change the slice.
Recommend building them, and say the alternative is naming a story to hold
back. The ask names the decision and ends the message.

**Unattended, this stop is a line in a file.** Inside a `session-loop` run
nobody reads a question in the transcript, so create nothing, make the first
line of `HANDOFF.md` read `BLOCKED:` and one sentence naming the slice
awaiting approval, and stop. A section that prints the stories and then runs
`bd create` in the same turn has not stopped.

Approval here covers this creation. A later slice asks again, and pushing
asks separately — `git-commit`, "Safety".

## 3. Creation, one command at a time

Run the Section 1 list and paste the real ids as they come back.

Create them one at a time, in the per-issue form. The batch forms
`bd create --file` and `bd create --graph` report success while dropping
the acceptance criteria and the dependency, which is the one field this
work exists to produce:
[../spec-task/references/bd-behavior.md](../spec-task/references/bd-behavior.md).
Everything stays on this machine.

The created ids live in bd alone. A copy in the design document goes stale
the first time a card splits.

## 4. Verification, by reading bd back

Real output, not a claim that it worked:

```
$ bd ready
$ bd show <first created id>
$ bd list --label slice:S<n> --status open
```

Check three things against what Section 3 pasted: that `ACCEPTANCE
CRITERIA` is present on the issue and matches the requirement text, that
the ready list holds exactly the tasks with no blocker, and that the slice
lane holds exactly the cards this run created. The batch forms fail
silently in this exact spot, and this read-back is what catches it.

Report a mismatch and leave it for `spec-task` to fix.

## 5. Where the work goes next

Name both handoffs, in one line each. `tdd-cycle` takes the cards, and
each task's proof command is the test to drive to red first. When the
slice's last card closes, `tdd-cycle` step 4d hands to `demo-task` for the
demo; `demo-task` hands to `retro-task`, which inspects the run itself and
then returns to `spec-task`, which decides the next slice and returns
here.

Before either handoff, read your own room:

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

Past the ceiling it reports, hand off instead of starting to build: say so and
let the operator clear, per `clear-task`. Planning a slice and building it are
two sessions' work and this is the seam.

## 6. Notes on what this template does NOT do

- Does not write or revise the design document. That is `spec-task`.
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
