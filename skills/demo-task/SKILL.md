---
name: demo-task
description: Closes a finished slice — runs every proof command to find where it actually stands, assembles a demo the operator can reproduce and operate themselves, takes their feedback verbatim, reconciles the plan's requirement statuses from measured results, and records what that feedback changed before handing to `retro-task`. Use when a slice is finished, when asked to demo what was built, or to review how a slice landed — "demo this slice", "show me S2", "close out this iteration". Does not decide or size what comes next; that is `spec-task`, once `retro-task` has run.
---

# demo-task — the slice is shown, the feedback is recorded

For the slice named in $ARGUMENTS, respond with the sections below in
order. If $ARGUMENTS is empty, the slice is the one the plan
marks as building — say which one, and where you read it.

The deliverables are the demo in Section 3 and the revised plan
in Section 6. Section 4 is this template's one stop; everything after it
records what the operator already said there rather than asking something
new.

**Everything the operator reads here is plain English.** They have not been
in the session, they do not know what R7 is, and a label this run invented
means nothing to them. So the demo opens with a paragraph anyone could
follow, and reference tags, requirement ids, bead ids and coined vocabulary
stay out of every part addressed to them. Measured: one run opened its demo
with an evidence block of twelve refs and ten labelled records, and the
operator's whole reply was that they did not understand any of it. The
records were correct. Nobody could read them.

Order is enforced because each section is built from the one above it. A
status tag written before Section 2's commands have run is a claim rather
than a measurement.

This template is new. If a section fights the work rather than catching
something, say so in the response instead of quietly skipping it.

## 1. Setup and boundaries

Real output, not paraphrase:

```
$ pwd && git rev-parse --show-toplevel
$ ls docs design specs 2>/dev/null
$ bd list --label slice:<current> --status open
$ bd list --label slice:<current> --status in_progress
$ bd list --label slice:<current> --status closed
$ bd list --no-labels
```

Those four queries are the board. Name which slice is current, and state
the counts:

```
  Backlog      bd list --no-labels                              known, not pulled
  TODO         bd list --label slice:<n> --status open          pulled, not started
  In progress  bd list --label slice:<n> --status in_progress
  Done         bd list --label slice:<n> --status closed
```

State the plan's path and the definition of released it records.
If the plan has no definition of released, stop — Section 3 cannot say
whether the slice is finished without it, and inventing one here would
answer a question that belongs to the operator.

**Then check that there is a slice to close.** If the current slice has no
closed bead and not one of its proof commands passes, the slice has not
started, and this is the wrong template. Say so in one line, say that
building it is `tdd-cycle`, and stop. Do not run Sections 2 through 6.
There is no demo to assemble, no status to reconcile from a measurement,
and no feedback to take on work nobody has seen.

## 2. Where the slice actually stands

Run every proof command belonging to the current slice's requirements, then
write this section in three parts, in this order — the order the operator
reads, which is the reverse of the order you did the work in.

**First, one paragraph in plain English.** What was built, and what a person
can now do that they could not do before. No reference tag, no requirement
id, no bead id, no command, no count, and no word this project invented. If
someone who has not been in the session cannot follow it, it has failed, and
the rest of the section will fail with it — this paragraph is what the
operator is asking for when they ask what you did this iteration.

Where the slice built something a person cannot do anything with — a
checker, a pinned toolchain, a test harness — say that plainly in the same
paragraph, in terms of what it does for them. "The build now refuses to
pass when a citation goes stale" is the paragraph. A slice with nothing to
say here is a finding: name it, and let Section 3 report there is no demo.

**Then the stories.** A requirement id names a rule; a story names
something a person can do, which is why the operator reads these and not
the records:

```
Story: As a <person who uses the product>, I can <what they can do>.
  beads:  <ids>
  proof:  <the command, or the thing to look at>
  status: <n> of <m> closed
```

**The role is someone who uses the product. Never the developer.** A slice
whose beads are all toolchain still rolls up to something a person can now do
— launch it and see it run — and the pinned shell, the build and the test
suite are how that happens, named on the `proof` line. "As a developer, I can
check out the repository and run the suite" names the audience the work was
easy to explain to rather than the audience it is for.

A story whose beads are all closed but whose proof command fails is the
finding worth leading with.

**Last, the per-requirement records.** They are the measurement, they stay,
and they are for you rather than for the operator:

```
[R<n>] $ <the proof command>
       <the last line of real output>
       result: passes | fails | ran nothing
```

Three rules for reading the results:

- **A command that ran no tests is a failure, not a pass.** A filtered test
  command whose filter matches nothing exits 0 and reports zero tests.
  Read the count of tests it ran, never the exit code alone.
- **Do not repair a failing proof command here.** Record it. It becomes
  work the next slice inherits, in Section 6.
- **Do not skip a command because the bead that owned it is closed.** A
  closed bead is a claim about the past; the command is the measurement
  now.

Then write the dependency graph to a file and say where it is:

```
$ bd graph --all --html > <path>/graph.html
```

It is one self-contained file, colored by status with a legend — open
blue, in progress orange, blocked red, closed green. `--dot` is the
alternative when a static image is wanted, piped to `dot -Tsvg`.

## 3. The demo

The demo shows the definition of released being met. Not the tests
passing — the thing itself, doing what the slice promised.

One record:

```
  shows:      <which requirements, by id>
  artifact:   <path to the screenshot, recording, file or output>
  produced by: $ <the exact command that made it>
  drove it:   <the input you sent it, and the capture either side of that>
  operate it: $ <the exact command the operator runs to drive it themselves>
```

Rules:

- **The operator may drive it themselves, so the reproduction command is
  part of the demo.** An artifact nobody else can regenerate is a claim,
  not proof. Both commands above are required, and both have been run.
- **Show yourself driving it, not one frame of it.** Where the definition
  of released says you operate the thing too, one capture proves only that
  it started. Send it an input — a key, a request, a typed command — capture
  it again, and name the input between the two, so the pair shows the thing
  responding rather than sitting there. Where you cannot drive it at all,
  say so in one line and name what is missing, rather than letting a picture
  of the opening state stand in for your half of released. Measured: a demo
  of a slice whose whole promise was landing the player in a named world
  showed two opening frames, sent the game no input, and left the operator
  asking whether the assistant could move the character at all.
- If the slice cannot produce an artifact a person can look at, say so
  plainly and name what is missing. A slice with no demo is the finding —
  it means the work was cut along module lines rather than through the
  system, and Planning has to correct that for the next one.
- **Show it, do not name it.** Read the artifact so it renders in the
  conversation. A path the operator has to open themselves is not a demo.
  It stays a local file; sending it anywhere needs their word first, per
  CLAUDE.md "Local Files by Default".
- **A capture that fails is not a slice that cannot be shown.** Exhaust the
  program's own capture before writing that no artifact exists: a graphical
  program can usually photograph its own framebuffer when the operating
  system refuses to photograph the screen, a server can be asked for the
  page it rendered, and a command-line tool can be told to write its output
  to a file. The rule above about a slice with no demo is for work cut along
  module lines, not for a capture tool that came back blank. Where the
  program's own capture works, say which call produced the file, so the next
  session does not rediscover it.

## 4. Stop — show the operator and take the feedback

Post Sections 2 and 3 and stop. Do not continue to status reconciliation,
do not propose a next slice, and do not start fixing anything.

**Open the ask with the phase line**, directly above the question — the
four phases in order, this stop's capitalized:

```
plan -> build -> DEMO -> retro
```

**Ask for one thing: that the operator run the demo themselves and say what
is wrong with it.** Give them the exact command from Section 3 and name the
two or three things worth looking at. Do not ask what they would like to do
next — deciding what comes after this slice is Planning's job, not this
stop's. The ask is the last thing in the message, per CLAUDE.md "When you
need an answer, the ask goes last and says what to do".

Record what comes back verbatim, one record per point:

```
[F<n>] "<the operator's own words>"
```

Feedback you paraphrase is feedback you have already decided about. Quote
first; interpret in Section 6.

**Unattended, this stop is a line in a file.** Inside a `session-loop` run
nobody reads a question in the transcript and nobody runs the demo, so commit
what is already done, make the first line of `HANDOFF.md` read `BLOCKED:` and
one sentence naming the slice waiting to be demoed, and stop. No requirement
reaches `demoed` from an unattended run, because that status is what a person
looking at the thing produces; they stay `built` until someone has looked. A
section that posts the demo and then carries on into Section 5 has not
stopped.

## 5. Status reconciliation

Rewrite each requirement's status tag in the plan from
Section 2's results. The four values:

```
  planned       no proof command yet, or it fails
  stubbed→S<n>  deliberately faked, naming the slice that will fill it
  built         the proof command passes
  demoed        the operator accepted it at Section 4
```

**`built` is derived, never typed.** It is what Section 2 measured, and a
requirement whose command failed or ran nothing goes back to `planned` even
if it was `built` last iteration. `stubbed` and `demoed` are the two a
person declares: a stub is an authoring decision, and acceptance is the
operator's.

A stub whose successor slice no longer exists in the slice map is a
finding. Name it.

## 6. What the feedback changed

Work every Section 4 record to one of six outcomes, and no seventh:

- A request to do something before this phase ends. Do it in this phase, and
  say what came of it. The operator asking for research, a second look, or a
  conversation about a design is not a requirement for a later slice, and
  filing it as one answers a question they did not ask. Measured: "I highly
  recommend researching it and circling with me on this design. Now, I think
  that can naturally happen during this phase" became three later requirements
  and no research.
- Accepted as it stands, changing nothing. Say so in one line. This is the
  ordinary answer to a demo that worked, and it is not a rejection.
- A new requirement. Write it into the plan, coarse — one
  sentence, no EARS text and no proof command, unless it lands in the next
  slice.
- A revision to the solution or the definition of released. Change that
  section and quote what it said before.
- A requirement that is dropped. Move it to out of scope with the `[F<n>]`
  that killed it.
- Rejected, with one line saying why.

**The slice just demoed is closed, and no outcome above reopens it.** A new
requirement or a revision is work for a later slice; `spec-task` places it
and writes its EARS text once Planning decides to pull that slice. Never
file a card carrying the demoed slice's label to fix what the demo found.
Doing what the operator asked for before this phase ends is not reopening the
slice: it closes no card and changes no code, and it writes to the same plan
this section already revises.

Then revise the plan and say what changed. State the path and
the byte count before and after.

## 7. Hand to `retro-task`

Before handing off, read your own room:

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

Past the ceiling it reports, hand off instead of continuing: say so and let
the operator clear, per `clear-task`. Tell it which section you stopped at
and what that section still owes — a record you have not worked, an answer
the operator is waiting on — so the handoff cannot write this phase down as
finished.

Otherwise, hand to `retro-task` now, in the same turn, before anything is
specified. The demo is over and its feedback is recorded, which is the
moment the process cycle closes. `retro-task` reads the run itself, takes
its own signoff, commits what was accepted, and hands on to `spec-task`,
which decides and specifies whatever slice comes next. Do not skip the
hand-off because the slice was small, and do not ask whether to run it — a
retro that waits to be asked for does not happen.

## What this template does NOT do

- Does not decide, size, or pull the next slice. That is `spec-task`, once
  `retro-task` has run.
- Does not write requirements in EARS or author proof commands. That is
  `spec-task`.
- Does not run the work. That is `tdd-cycle`, and `session-loop` when the
  run is unattended.
- Does not inspect the process, read the run's own transcripts, or change a
  skill. That is `retro-task`, which Section 7 hands to.
- Does not close beads or repair failing proof commands.
- Does not decide the definition of released. The operator settles it, and
  `spec-task` Section 1 is where that conversation happens.
- Does not push anything outward. The backlog and the plan stay
  local.
