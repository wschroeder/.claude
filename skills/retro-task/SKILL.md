---
name: retro-task
description: Closes the process cycle after a slice ships — reads the run's own transcripts to find what each of last round's changes actually did, hears the operator's experience before interpreting it, answers their feedback against transcript evidence, then proposes the next batch of skill and CLAUDE.md changes as named options and stops for signoff. Inspects the process, not the product; the demo and the product's feedback belong to `demo-task`. Investigate-only until signoff, and every accepted change ends as a commit rather than a note. Use after a slice is demoed and its feedback taken, when asked to retro a run or hold a retrospective, to review how the process itself went, to work out what should change about the skills or a CLAUDE.md, or when a run's transcripts need reading to find why a rule did or did not fire — "retro this run", "how did that go", "what should we change".
---

# retro-task — the process cycle closes, the next one opens

For the run named in $ARGUMENTS, respond with the sections below in order. If
$ARGUMENTS is empty, the run is everything shipped since the last round was
recorded — say which commit you measured from, and where you read it.

This template inspects the process. What was built and whether it works
belong to `demo-task`, deciding what comes next belongs to `spec-task`, and
a finding about the product goes to the design document rather than here.

The deliverable is the change batch in Section 7. Sections 1 through 6 read and
write nothing. Order is enforced because each section is built from the one
above it: a finding written before Section 3 has run is an impression rather
than a measurement, and a change proposed before Section 4 is your reading of a
run the operator actually sat through.

Evidence discipline is CLAUDE.md's, "Evidence Format (HARD CONSTRAINTS)", and
this template adds nothing to it. Three of its rules carry most of the weight
here: a pattern label is a hypothesis (7), recognition is a starting point
rather than a conclusion (8), and a ref that locates is not a ref that proves
(13).

## 1. Scope the round

Real output, not paraphrase:

    $ git -C <skill repo> log --oneline <last recorded round>..HEAD
    $ git -C <product repo> log --oneline | head -5
    $ git -C <product repo> status --porcelain
    $ ls -lat ~/.claude/projects/<slug>/*.jsonl | head -25

Three things reach the response: the changes shipped last round, where the
product repository stands now, and every transcript whose mtime is later than
the newest of those changes. A transcript older than that was written before
the changes landed and is not evidence about them.

Say plainly when the product repository has been rebuilt. Card ids and commit
hashes from earlier rounds are then dead, and a finding citing one cites
nothing.

## 2. The session map

One line per session in scope: id, local start and end, the model, how many
operator turns it carried, and what it did in the run. Subagent transcripts sit
under `<session-id>/subagents/` and are counted separately.

Read `session-loop/scripts/session_budget.py <project>` for where each session
handed off rather than counting tokens by hand.

The map is what makes Section 3 answerable, because a change that fired only in
an unattended session has not been tested with a person present, and only the
map says which sessions those were.

## 3. What last round's changes actually did

One record per change in Section 1's list:

    change:   <what shipped>
    fired:    <the verbatim transcript line and its timestamp, or "did not fire">
    untested: <the case this run never exercised, or "none">

A change with no transcript line behind it did not fire, whatever the file
says. Write that.

Quote the line. A grep that found the changed file locates the change and
proves nothing about its behavior — CLAUDE.md rule 13.

A round where every change fired and nothing is untested is a round to
re-examine before believing. The usual cause is a search that only looked where
the change would have succeeded.

## 4. Stop — the operator's experience of the run

Hear them before interpreting. Nothing above this line is offered as a
conclusion yet, and nothing below it is written until they have answered.

Say what Section 3 found, in at most a screen, then ask what they saw that is
not in it. That is the whole ask. Do not propose a change here, and do not ask
them to choose between changes whose case they have not heard.

They sat through the run and you read its transcripts. Those are different
evidence, and theirs is heard first because yours would otherwise frame it.

**Open the ask with the phase line**, directly above the question — the
four phases in order, this stop's capitalized:

```
plan -> build -> demo -> RETRO
```

**Unattended, this stop ends the run.** Inside a `session-loop` run nobody is
there to answer, and no amount of transcript reading substitutes for the
operator's own account. So commit what is already done, make the first line of
`HANDOFF.md` read `BLOCKED:` and one sentence saying a retro is waiting on
their experience of the run, and stop.

## 5. Where the readings diverge

Answer each thing they raised against transcript evidence, and say plainly
where your reading and theirs differ. Something they remember that the
transcripts do not show is your finding to report rather than theirs to defend.

Their account is evidence about how the run felt to run. It is not evidence
about a mechanism. Both belong in the response, each labelled as what it is.

## 6. The findings

One record per finding. The mechanism is the finding; the category is not:

    finding:    <a sentence naming who did what>
    observed:   <the transcript line, with its timestamp>
    mechanism:  <the instruction, line, or absence that produced it>
    competing:  <the instruction it lost to, where there was one>

Where the mechanism line is empty, the record is a `hypothesis:` and says so in
those words. Matching this run's trouble to a shape seen before is where a
reading usually stops one step early — CLAUDE.md rules 7 and 8.

Two mechanisms have come up often enough to check for by name. A rule stated
far from the output it governs does not reach that output. And where two
instructions cover the same moment, the nearer one wins unless precedence is
stated, however much more correct the other is.

## 7. Stop — the change batch, then signoff

A separate approval from Section 4. Lead with what changes and why, one
paragraph each, in the operator's terms.

Every Section 6 finding reaches one of four outcomes, and no fifth: a change
proposed, a change deliberately not made with one line saying why, a finding
that needs another run before anyone can act on it, or a finding that turns out
to be the operator's call about the product and goes to the design document
instead.

Where the choice between two changes is real, put them up as named options per
CLAUDE.md, "Choices and options get visual separation", and recommend one. Do
not hand the operator a blank space to invent a third in.

**Open the ask with the phase line**, directly above the question — the
four phases in order, this stop's capitalized:

```
plan -> build -> demo -> RETRO
```

Then ask, per CLAUDE.md, "When you need an answer, the ask goes last and says
what to do". One decision: make this batch, or strike the parts they do not
want. The ask is the last thing in the message.

Nothing is written until they answer, and signoff here covers this batch and no
later one — `git-commit`, "Safety".

## 8. Record and commit

Each accepted change goes through the skill that owns it: `systematize` for an
edit to an existing skill or a new ordinary one, `create-task-skill` for a new
task-shaped one. A CLAUDE.md change is made directly, and a new skill's routing
row lands in the same edit as the skill.

Then write the round down. Where a CLAUDE.md names a process log, append it
there: what was measured, what changed, and what is still unmeasured. Where
none is named, the commit message is the record, and say so.

Commit last, through `git-commit`, staging by path. An accepted change left
uncommitted is a note, and the next round finds the same finding again.

Before handing off, read your own room:

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

Past the ceiling it reports, hand off instead of continuing: say so and let
the operator clear, per `clear-task`.

Otherwise, hand to `spec-task`, in the same turn. `spec-task` decides and
specifies whatever slice comes next — this template does not pull one for
it. The process cycle is closed, and the next one starts at planning.

## Notes on what this template does NOT do

- Does not demo the product, take product feedback, or reconcile a design
  document. That is `demo-task`.
- Does not decide or size the next slice. That is `spec-task`.
- Does not edit a skill itself. Section 8 routes every change to the skill that
  owns it.
- Does not run the work again, re-open a slice, or fix what a finding describes
  in the product.
- Does not take over the retroed session's tasks or write as though it were
  that session.
- Does not treat adoption counts, effort estimates, or a change's presence in a
  file as evidence that it fired.
- Does not push, and does not send anything outward. The log and the skill
  repository stay local.
