---
name: backlog-task
description: Creates and verifies the bd (beads) backlog for one slice spec-task has already cut — checks preconditions against the design documents the cards will serve, reprints the slice's stories for a single approval, runs the create, dependency, label and spec-id commands, then reads bd back to prove the acceptance criteria and blocking edges actually stored. Use after spec-task has cut and reviewed a slice, when asked to create the cards or tickets for a specced slice, to put an approved slice into the backlog, or when a bd create batch needs verifying — "make the cards", "create the backlog", "file the tickets for S2".
model: sonnet
---

# backlog-task — a cut slice in, a verified backlog out

For the slice named in $ARGUMENTS, respond with the sections below in order.
If $ARGUMENTS is empty, the slice is the one `spec-task` just cut — say which,
and name the design documents its cards serve.

`spec-task` produces the input and stops here. The first bd write happens
after Section 2 is approved, and Section 2 is this template's only stop.

Order is enforced: Section 1's command list is what Section 3 runs, and
Section 3's real ids are what Section 4 reads back. A Section 3 that
reported success while creating nothing surfaces in Section 4 as a
`bd show` that fails on its own pasted id.

## 0. Before Section 1, read your own room

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

Past the ceiling it reports, hand off BEFORE starting this template rather than
after finishing it: say so, say that no section has run, and let the operator
clear, per `clear-task`. A template is a session's worth of work, so a session
that begins one already over the line ends it far over, and every section it
writes on the way is written in a session that should have stopped. Measured: a
session printed "turn 72, context 231,229 of 170,000 — hand off", quoted that
line back in its own evidence block, created ten cards over the next two
hours, printed the same line again at 251,737, and ended at 263,205.

The check below at the end of this template governs the hand to the next phase.
This one governs whether this phase starts here at all, and they are not the
same question.

## 1. Preconditions

Real output, not paraphrase:

```
$ pwd && git rev-parse --show-toplevel
$ ls -d .beads 2>&1
$ git status --short
$ bd statuses
```

State four things: the slice being created, the design documents its cards will
name as their spec id, whether bd is initialized here, and whether the tree is
clean.

**Stop when the tree has uncommitted changes.** `spec-task` Section 8 commits
the design document edits, and on a dirty tree a card's spec id would name a
document whose content is absent from history. Say which file is dirty and
wait.

**Say whether `demoable` is among the statuses.** `tdd-cycle` moves a built card
there and `demo-task` closes it from there, so a project without it has cards
going straight from in progress to done with nobody having watched them work.
Registering it is `bd config set status.custom "demoable:wip"`, one line, and
it belongs in the same approval Section 2 asks for. Measured: unsetting that key
reports success and leaves the status registered, and only setting it to an
empty string removes it.

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
nobody reads a question in the transcript, so create nothing, then write
`HANDOFF.md` through `clear-task` with a first line reading `BLOCKED:` and one
sentence naming the slice awaiting approval, and stop. Write it through the
skill rather than by hand, however close the ceiling is: the handoff point is a
budget and not a limit. A section that prints the stories and then runs
`bd create` in the same turn has not stopped.

Approval here covers this creation. A later slice asks again, and pushing
asks separately — `git-commit`, "Safety".

## 3. Creation

Run the Section 1 list and paste the real ids as they come back.

Two forms work. The per-issue form, one command per card. Or `bd create --file`
with a markdown file whose cards are `##` headings and whose fields are `###`
sections — Description, Design, Acceptance Criteria, Labels, Priority, Type.
Measured: in that shape it stores all six, and `bd show` prints the acceptance
criteria under its own heading.

**What no batch form stores is a dependency or a spec id.** Both need their own
command afterwards, `bd dep <blocker> --blocks <blocked>` and
`bd update <id> --spec-id <document>`, and Section 4 is what catches you
forgetting. Do not use `bd create --graph` at any size: it drops the acceptance
criteria and warns rather than failing.

The flat `Key: value` shape is the trap. bd does not parse it, reports success,
and lands every field in the description as prose. Measured output for all three
forms:
[../spec-task/references/bd-behavior.md](../spec-task/references/bd-behavior.md).
Everything stays on this machine.

Write the file outside the repository — a scratchpad, not a new markdown file in
the project. The created ids live in bd alone.

## 4. Verification, by reading bd back

Real output, not a claim that it worked:

```
$ bd ready
$ bd show <first created id>
$ bd show <an id you expect to be blocked>
$ bd list --label slice:S<n> --status open
```

Check four things against what Section 3 pasted: that `ACCEPTANCE CRITERIA` is
present on the issue and matches the requirement text, that `Spec:` names the
design document the card serves, that the ready list holds exactly the tasks
with no blocker, and that the slice lane holds exactly the cards this run
created.

The dependency and the spec id are the two a batch create does not store, and
this read-back is the only thing standing between a silent drop and a slice of
cards carrying neither. Check them on a card you expect to be blocked as well as
on the first one.

Report a mismatch and leave it for `spec-task` to fix.

## 5. Where the work goes next

Name both handoffs, in one line each. `tdd-cycle` takes the cards, and
each task's proof command is the test to drive to red first. When the
slice's last card closes, `tdd-cycle` step 4d hands to `demo-task` for the
demo; `demo-task` hands to `retro-task`, which inspects the run itself and
then returns to `spec-task`, which decides the next slice and returns
here.

**The build runs as a `session-loop` run, not as a string of sessions the
operator clears by hand.** The cards exist now and nothing between here and the
demo needs the operator, so hand to `session-loop` rather than to a prompt for
them to paste. It writes `HANDOFF.md`, stops once for a `/clear`, and then
drives `tdd-cycle` card after card to the end of the slice, holding each session
to the ceiling with a hook instead of a judgment call. Measured: across two
projects in one month, twenty-nine handoffs were written by hand and the loop
was invoked zero times; one of those builds closed seven cards over five
sessions, four of them closing exactly one card each, while a session that kept
going closed its second and third cards for 21,239 and 14,670 tokens against the
114,028 its first one cost.

Before invoking it, read your own room:

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

**Then invoke `session-loop`, in this turn, whatever that number says.** Naming
it in a handoff is not handing to it: the next session reads a prompt whose
first step names `tdd-cycle`, loads that instead, and the build becomes the
string of hand-cleared sessions this rule exists to prevent. Measured: one
planning session wrote a handoff naming `session-loop` zero times, and the
operator pasted eleven more prompts over the thirteen hours that followed.

Being past the ceiling changes nothing here. The loop's own step 2 writes the
handoff through `clear-task`, which is the work handing off would have cost
anyway, so say which section you stopped at and what it still owes — a record
you have not worked, an answer the operator is waiting on — and let the loop
carry it rather than the operator. Planning a slice and building it are two
sessions' work, and this is the seam.

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
