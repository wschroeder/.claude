---
name: spec-task
description: Turns a design conversation into a plan whose acceptance criteria are EARS requirements, each carrying the command that proves it and a status derived from running that command. Reads the repository's design documents — the rules of the product, which it never writes to — and takes the definition of released from them where they state one. On a returning initiative it also decides and sizes the next slice itself, from the plan's own sketch, the backlog, and the last retro's findings, then cuts that slice into sized tasks with the exact bd (beads) commands that will create them, while everything beyond it stays a loose sketch and a dependency edge. Hands those commands to backlog-task, which creates and verifies the cards. Use when asked to write a spec, spec something out, turn a design or a discussion into requirements, define acceptance criteria, decide or size the next slice, or break designed work into tickets or a backlog — and when work has been designed but nothing durable has been written down.
---

# spec-task — design conversation in, a plan plus a backlog out

For the design conversation named in $ARGUMENTS, respond with the sections
below in order. If $ARGUMENTS is empty, the design conversation is this
session's own history — say so, and name where it starts. The deliverable
is the plan in Section 5, written and committed by Section 8
and reviewed by Section 9. Section 8 writes and commits without asking.
This template touches bd only to read it; the backlog is created by
`backlog-task`, which Section 10 hands to. Section 1 stops for approval
of the slice itself on a returning initiative; `backlog-task` holds the
other stop, approval of the cards built from it.

## Two documents, and this template writes only one of them

**A design document describes the product.** The rules of the game or the
business logic of the application, the aesthetic, and the main ideas,
written so a reader finishes knowing how the thing behaves. No formulae and
no code, and no account of how any of it is built: no source file, no
function, no test, no engine setting, no configuration key. No slice,
ticket or card either, because those describe a schedule. One exception
stands on purpose — a tag on an element saying the build holds it.

**A plan describes what is being built next.** Problem, definition of
released, solution, slices, requirements, test seams, implementation
decisions, out of scope. It holds exactly what a design document may not,
it goes stale on purpose, and it is rewritten every slice.

This template reads the design documents and writes the plan. It never
writes to a design document, and it never copies the product's rules into
the plan. Where the two disagree about how the product behaves, the design
document is right, and correcting it is the operator's call.

Deciding an unclear case: ask who would have to open the file to keep the
sentence true, and whether they have any reason to. Nobody renaming a
function opens a design document, which is why prose may not point at code
while a doc comment may point at a design section. The argument in full,
the research behind it, and the run that produced the rule:
[references/two-documents.md](references/two-documents.md).

The plan covers the whole initiative and outlives this run. The
**current slice** is the only part specified deeply — EARS text, a proof
command, acceptance criteria on the bead. Everything past it is one
sentence in the plan and, at most, a bead title carrying its dependency
edges. Sketching ahead is cheap; specifying ahead is not.

**When the plan already exists, it is the input, not something
to re-derive.** Take Sections 1, 2, 3 and 5 from what the plan says:
the definition of released it states, the decisions it records as source
lines, the questions it lists as out of scope, and its own structure.
Section 4 specifies only the slice Section 1 names. Nothing the plan
already settles is researched again or asked again.

Order is enforced: each section is built from the one above it and checked
by the one below.

This template is new. If a section fights the work rather than catching
something, say so in the response instead of quietly skipping it.

## 1. Setup, boundaries, and what "released" means here

Real output, not paraphrase:

```
$ pwd && git rev-parse --show-toplevel
$ ls -d .beads 2>&1
$ bd list --status open 2>&1 | tail -3
$ ls -d docs design specs 2>/dev/null
```

State the repository root, whether bd is already initialized here, the
issue prefix in use, and the directory the plan will live in.

**Then find the design documents and read them.** They are the description
of the product this work changes, and a plan written without them specifies
a product nobody described. Name the directory and how you found it, list
what is in it, and read enough to state in two or three sentences what the
product does — from the documents, not from the conversation. Where the
repository holds no design documents at all, say so in one line and carry
on; the plan is then the only durable writing, and that is a finding worth
reporting rather than a blocker.

Take three things from them, and nothing else: the definition of released
if they state one, the behavior the current slice has to match, and the
questions they leave open. Do not restate their rules in the plan, do not
edit them, and do not write into them. A change they need is the
operator's call, made in its own turn.

If `.beads/` is absent, do NOT run `bd init` here. Record it as a
precondition for `backlog-task`, in exactly this form:

```
$ bd init --skip-agents --skip-hooks -p <prefix>
```

**Both flags are required.** Without them bd writes a `CLAUDE.md`, an
`AGENTS.md`, a SessionStart hook and five git hooks whose instructions
contradict this machine's, and none of those hooks does measured work.
What was measured: [references/bd-behavior.md](references/bd-behavior.md).

bd makes its own commit on init whatever flags it is given. Expect that
commit, and do not report it as work this session did.

**Then settle the definition of released.** It is the operator's to decide
— for one team a deployment behind a feature flag, for another "runs on
this machine".

- If a design document or an existing plan in this repository already
  states a definition of released, quote it with its file and line, treat
  it as settled, and do not ask. That sentence is the answer.
- If a `project-definition-of-done` skill is listed in the available
  skills, load it and use what it says. Say that you did.
- If neither exists, ask the operator with AskUserQuestion and quote the
  answer as a source line in Section 2. Then offer to record it as that
  skill so the next initiative in this repository inherits it — make that
  offer in the same turn, not as something noted for later.

Do not answer this yourself, and do not proceed without it.

**It describes a shape, not a scope.** "Runs on this machine and the tests
pass" is a definition of released; "launches a fully playable build" is the
finished product wearing the same hat. The words *fully*, *complete*, *all*
and *end to end* are the tell. Offer options that pass that test, and
rewrite one the operator supplies that does not.

**Then decide which slice this pass specifies.** On a brand-new initiative
there is no slice yet — that is the walking skeleton Section 4 cuts.
Otherwise, read the plan's sketch, the backlog, and — following
a retro — its findings, and name the next slice:

```
  slice:      S<n> — <name>
  a person can: <what they will be able to see or do when it is finished>
  retires:    <which stubs it replaces, by requirement id>
  inherits:   <failing proof commands the prior slice left behind>
  carries:    <requirements the last demo's feedback added, by id>
```

A path through the system, not a layer of it. The document's own sketch is
a starting point rather than a decision — resize or split it if it no
longer fits now that something real exists to compare it against. Only the
next slice is decided here.

**On a returning initiative, stop here before Section 2's research
begins.** Nothing past this point has been written yet, which is what
makes this the cheap place to catch a wrong slice — catching it after
Sections 2 through 9 have run costs the whole pass.

**Unattended, this stop is a line in a file.** Inside a `session-loop` run
nobody reads a question in the transcript, so make the first line of
`HANDOFF.md` read `BLOCKED:` and one sentence naming the slice awaiting
confirmation, and stop — nothing here has been written yet, so there is
nothing to commit first.

**Open the ask with the phase line**, directly above the question — the
four phases in order, this stop's capitalized. Measured: the operator asked
"What phase are we in?" twice inside one planning pass; the line was already
in this template and nothing told anyone to print it.

```
PLAN -> build -> demo -> retro
```

Proceed with the slice above, or name a different one?

## 2. Source lines from the design conversation

Real quotes with locations. One record per decision the plan rests on:

```
[S1] <file:line, or "session, operator message beginning '<first six words>'">
     "<the quoted line>"
```

A decision you cannot quote is not a source line — it is an open question,
and belongs in Section 3. Per CLAUDE.md rule 13, a ref that only locates
proves nothing about what was decided; the quote is the ref.

If the design has not been stress-tested, run `grill-me` before this
section. It interviews and writes nothing, so its output is the
conversation this section quotes.

**Before spawning anything to research a source line, load `subagents`.**
Research is a job that can be written down, which makes it a fresh agent
and never a fork. Measured: one run of this template opened two forks side
by side, never having loaded the skill that forbids exactly that.

## 3. Open questions — what the design does not settle

List what the source lines leave undetermined. At minimum, sweep these
five: what happens on invalid input; what happens when something the
system depends on is unavailable; what happens at the limits (empty, one,
very many, concurrent); who is allowed to do it; and what is deliberately
not being built.

Each question gets one of two outcomes, and no third:

- The operator answers it, and the answer becomes a new source line in
  Section 2.
- Nobody answers it, and it goes verbatim into the out-of-scope list in
  Section 5.

Do not answer them yourself. If an unanswered question would change what
the requirements say, stop and ask — CLAUDE.md rule 2, a missing
precondition is a stop rather than a guess.

**End this section by saying which it was.** Either the numbered questions
the operator has to answer, asked with AskUserQuestion, with nothing
written after them — or the one plain sentence that every question went to
out of scope and there is nothing here for them to do. A section headed
"open questions" that silently answers all of them leaves the operator
guessing whether their turn has come.

**Where there are questions, open the ask with the phase line**, directly
above them — the four phases in order, this stop's capitalized:

```
PLAN -> build -> demo -> retro
```

## 4. Requirements in EARS, each with the command that proves it

**On a first slice, cut the walking skeleton before writing a single
requirement**, print the record, and hold it to five behaviors or fewer.

On a later slice there is no skeleton to cut: print the slice named in
Section 1 and go straight to the patterns below.

The patterns, in Mavin's own casing — the keywords are ordinary words, not
capitals:

```
ubiquitous        The <system> shall <response>
state driven      While <precondition>, the <system> shall <response>
event driven      When <trigger>, the <system> shall <response>
optional feature  Where <feature is included>, the <system> shall <response>
unwanted          If <trigger>, then the <system> shall <response>
complex           While <precondition>, when <trigger>, the <system>
                  shall <response>
```

**Requirements in the current slice** get the full record:

```
[R1] pattern:  <one of the six above>
     text:     <the requirement in that pattern, one sentence>
     source:   [S<n>]
     slice:    S<n>
     proof:    $ <command>
     output:   <real output from running it now, its failure included>
     status:   planned | stubbed→S<n> | built | demoed
```

**`built` records what was already true when this section began**, from an
earlier slice or an existing system — never a command this pass made pass.
This template writes no product file; `tdd-cycle` does, after approval.

**Requirements beyond the current slice** get one line and nothing else:

```
[R9] later — <one sentence saying what will have to be true>
```

They carry no EARS text, no proof command, no status, and no slice number.
A one-liner may say roughly when it's likely to matter, in prose — "once
movement is real", "after the HUD exists" — but a fixed `S<n>` tag invites
treating the sketch as decided, which is exactly what it is not. They are
promoted to the full record, slice number included, by the run that pulls
their slice.

Rules for this section:

- No user stories in the requirement. "As a user I want…" states a wish,
  not a checkable condition. Section 6 groups these requirements into
  stories for the operator; the requirement itself stays checkable.
- The proof command names a specific test, check or query — for example
  `go test ./ears -run TestUbiquitous`, or
  `curl -s localhost:8080/health | jq -e '.ok'`. "The tests pass" is not a
  proof command.
- Run every proof command now, and **read the count of tests it ran, not
  its exit code**: a command that runs nothing can still exit 0.
- A command that already passes means the requirement is `built` — mark it
  and keep it out of Section 6. One that fails with "no such test" is the
  expected shape of unbuilt work.
- A command that cannot be run yet says so and says why, per CLAUDE.md
  rule 3. Do not paste an imagined result.
- **A requirement that describes how an existing system behaves cites
  where that behavior was observed.** Anything of the form "like X does",
  "matching Y", or any claim about a protocol, format or product this work
  reproduces carries a source: a URL, a file path, a command whose output
  shows it.
- **Every slice ends in a requirement whose proof produces something a
  person can look at and operate.** It is written like any other
  requirement, and its proof command is the one that produces the artifact.
  A slice whose requirements are all internal modules cannot produce one,
  and that is the signal the cut was horizontal.
- **Where the definition of released says a person operates the thing, one
  requirement in the slice is proved by the input that person sends.** Not
  by calling the code that input would have reached — by the press, the
  keystroke or the request itself, arriving the way it arrives in the
  assembled product. Write it as a requirement here, at planning, because
  it is the only place cheap enough: every layer below this one is
  satisfied by a public method with the right name, and nothing downstream
  asks whether anybody can reach it. For how to send this product real
  input, load `project-drive` if it appears in the available skills; if
  nothing is listed, say so in one line and write the requirement anyway.
  Measured: a slice built to let two players play a battle shipped eleven
  requirements, not one of them proved by an input a person sends — the ones
  that reached the planning screen called its own methods — and the
  operator's first act was to open the game and find that no press reached
  it.
- **That input is aimed at the thing as a person sees it, not at a
  coordinate the code returns.** Where the target's position comes from the
  same module the assertion reads, the requirement only shows the code
  agreeing with itself, and says nothing about whether anybody can hit it.
  So the requirement names the target from what is on the screen — the drawn
  extent, the rendered label, the visible control — and compares the ground
  that answers the input against the ground the person is aiming at.
  Measured: seven requirements drove real presses into a running game, every
  one of them at the centre the game's own layout function returned, and
  every one passed over a battalion painted 51 pixels wide that answered a
  press over 3 of them.

## 5. The plan

The full text, exactly as the file will read, in a fenced block. Every
Section 4 record appears here in full. A pointer standing in for content —
"specified above", "see the spec history", "as listed earlier" — means the
block is not the plan, and the file Section 8 writes will not be the
file shown here.

Nothing here restates a design document. Where a requirement needs the
product's own rule to make sense, name the rule in the requirement's own
words and leave the design document to hold it — a plan that carries a copy
has created a second place for that rule to be wrong.

**The document is an index plus leaves, not one growing file.** A session
that has to read the whole thing to specify one slice pays for every slice
already finished. The index is the file every session opens; a leaf is
opened only when its content is needed.

- The **index** carries Problem, Definition of released, Solution, Slices,
  the current slice's requirements, the current slice's test seams, the
  one-line later requirements, Out of scope, and one link line per leaf.
- A **leaf** holds one completed slice's requirements, or the
  implementation decisions, or the source lines. Each lives beside the
  index and is named for what it holds.
- **The index stops at 200 lines.** When it passes, move the oldest
  completed slice's requirements into a leaf of their own and link it.
- Every leaf is a leaf. A leaf never links to another leaf, so following
  one link is the whole cost of following it.

These sections in this order, and nothing else:

- **Problem** — what is wrong now, in the operator's own terms
- **Definition of released** — the sentence Section 1 settled, verbatim
- **Solution** — what exists when this is done; revised every iteration
- **Slices** — the current slice, in full: `S<n> <name> — <what a person can
  see or do>`, marked `building`. Everything after it is a loose sketch for
  orientation, not a plan: a phrase or two per anticipated chunk, numbering
  optional, none of it a commitment — Planning re-derives the next cut
  fresh each time rather than reading this list as decided
- **Requirements** — the Section 4 records, full for the current slice and
  one line for the rest
- **Test seams** — where each proof command attaches: the function,
  endpoint or CLI boundary it drives, and any fixture that has to exist
  before it can run
- **Implementation decisions** — choices already made, and why, so the
  executor does not re-derive them
- **Out of scope** — every unanswered question from Section 3, plus
  whatever the conversation ruled out

Two rules about status. A requirement's status is **derived by running its
proof command**, never typed from memory — `built` means the command was
run in this session and passed. And a `stubbed` requirement names the slice
that will replace it, so a deliberate fake in a walking skeleton cannot be
mistaken for finished work.

No user-story list in the plan. Stories are how Section 6 reports the
work to the operator, not how the plan records it. Prose follows
CLAUDE.md "Communication Style": plain
sentences, a named actor and verb, no invented compound-noun labels.

## 6. Task breakdown and sizing

Cut **the current slice's** unbuilt requirements into tasks. A task is the
smallest unit carrying its own red-green-refactor cycle and worth a fresh
reviewer opening the diff — aim for 2–5 minutes of agent time, a number to
re-measure rather than obey.

```
[T1] title:      <imperative, one line>
     covers:     [R1] [R3]
     proof:      $ <the command that closes it>
     estimate:   <minutes>
     blocked-by: [T<n>] | none
     design:     <one or two sentences the executor needs and cannot
                  re-derive from the code>
```

Work expected in later slices may be sketched as a title and its blocking
edges, and nothing more:

```
[T9] title:      <imperative, one line>
     blocked-by: [T<n>] | none
     slice:      later
```

Then run the coverage check against the two lists rather than by eye, and
print the result: every unbuilt requirement **in the current slice**
appears in exactly one task. Print the requirement ids that reached no
task. A non-empty list means the breakdown is unfinished.

Section 9's review loop re-runs this check on every round. A requirement
that loop adds has never been through it.

A current-slice task with no proof command is not a task. Fold it into one
that has, or drop it. A sketched later task has no proof command by
definition — that is what makes it cheap.

Name the two boundaries where a task hands work to another: which function
or data shape one produces and the next consumes.

**Then print the stories, above the task records.** The task records are
the working material and they stay; the stories are what the operator
reads. One record per story, and every current-slice task belongs to
exactly one:

```
Story: As a <person who uses the product>, I can <what they can do>.
  tasks:  [T<n>] [T<n>]
  proof:  <the command, or the thing to look at>
```

**The role is someone who uses the product. Never the developer.** Work that
only helps the developer stays in the slice — the test suite, the local run,
the pinned toolchain — attached to the story whose behavior it proves and
named on that story's `proof` line.

A task that fits no story is a module rather than a step toward something a
person can do. Say so instead of inventing a story around it. Writing "As a
developer" is inventing one.

`backlog-task` presents this same list when it asks for approval, so write
them here to be read there.

## 7. The bd command list

The exact commands, not yet run. One `bd create` per task, one
`bd dep add` per blocking edge, one `bd label add` per current-slice task.

Current-slice tasks get the full form:

```
bd create "<title>" -t task -p <0-4> \
  --acceptance "<EARS text>  Check: <proof command>" \
  --design "<design line>" \
  --spec-id "<plan path from Section 5>" \
  -e <estimate in minutes> --silent
bd dep add <blocked-id> <blocker-id>
bd label add <id> slice:S<n>
```

Sketched later tasks get the title and the edges only — no `--acceptance`,
no `-e`, and no slice label:

```
bd create "<title>" -t task --silent
bd dep add <blocked-id> <blocker-id>
```

The slice label is what separates the board's lanes that `demo-task`
reads. `--spec-id` carries the plan's path, which is the link from a bead
back to the requirement it came from.

Use this per-issue form. Do not use `bd create --file` or
`bd create --graph`: both report success while dropping the acceptance
criteria and the dependency, which is the one field this template exists
to produce. Measured output for both, and what each flag renders as:
[references/bd-behavior.md](references/bd-behavior.md).

Where Section 1 found no `.beads/`, this list's first line is
`bd init --skip-agents --skip-hooks -p <prefix>`, both flags required per
Section 1. Section 9 regenerates the whole list on every round, and
`backlog-task` runs the list as Section 7 leaves it.

## 8. Write the plan

Write the Section 5 text to the path Section 1 named. Do not ask first, and
do not stop here. The plan is a local file in a git repository, Section
9's loop revises it in place, and nothing leaves this machine.

Then report the path and the byte count, taken from `wc -c` on the file
that now exists rather than estimated from the text above.

The plan is not published anywhere, per CLAUDE.md "Local Files by
Default, No Publishing Without Asking".

**Then commit it, without asking.** Committing is covered by the standing
permission in `git-commit`. Stage the plan and its leaves by path, per
`git-commit`.

**Write nothing to a design document here, or anywhere in this template.**
Not a status tag, not a correction, not a link back to the plan. Where the
work has shown a design document to be wrong, say so as a finding and let
the operator decide.

If the directory is not tracked by git at all, say so as a finding and
stop, because that is a precondition rather than something to fix silently.

## 9. Review the plan for gaps, and re-review until a round changes nothing

This is a loop, not a single pass. One pass finds the gaps in the plan
as first written and none of the gaps its own fixes introduce.

**One round is these five steps.**

1. Run `design-gap-task`, and **pass it the design documents' directory,
   never the plan's.** That template hunts for holes in a described
   product — a rule that sorts things into categories without covering
   every case, an entity created and never removed — and the plan is a
   schedule, so pointed at the plan it reports on the wrong artifact and
   the product's own holes go unlooked-at. Where the two directories are
   the same one, say so and name which files it is reading. Its findings
   are about the product, so none of them edits a design document here:
   a finding inside the current slice becomes a requirement by step 3, and
   the rest go to the operator.
2. Then check the plan itself, which `design-gap-task` has not read. Two
   sweeps. **Every requirement making a factual claim about an existing
   system, checked against its cited source** — that sweep looks for what
   is missing, and a requirement that is present and wrong passes it
   untouched. And **every requirement checked against the design documents
   for a rule it contradicts**, because a plan that specifies behavior the
   product was never designed to have is a plan that will be built and
   then argued about.
3. Act on every finding, one of four ways:
   - A missing rule **inside the current slice** becomes a new requirement
     in Section 4, with its own proof command, and a task in Section 6.
   - A missing rule **outside the current slice** becomes a one-line later
     requirement in Section 4 and, at most, a sketched task title in
     Section 6. No EARS text, no proof command, no status.
   - A finding the conversation deliberately ruled out goes into the
     out-of-scope list.
   - A finding you reject gets one line saying why.
4. Revise the plan and say what changed.
5. Re-enter at Section 4 and come forward through 6 and 7: renumber the
   requirements, re-run the coverage check, regenerate the command list.
   Do not patch those in place — the approval `backlog-task` asks for is on
   a list built from the requirements as they now stand.

**When the loop ends.** A round producing no new or changed requirement
ends it. A finding landing only in out-of-scope, or getting a one-line
rejection, does not start another round. Print how many rounds ran and
what the last one found.

**The ceiling.** If a fourth round still changes a requirement, stop and
hand the operator the remaining findings rather than continuing. Then ask
which of them to fold in and which to leave, as the last thing in the
message. What bounds the loop in the ordinary case is step 3's routing of
out-of-slice findings.

**Anti-anchoring.** The previous round's report is context, not precedent.
Round two runs `design-gap-task` again — step 1 is not optional on a later
round — and lets the filter drop duplicates on their own merits.

This loop closes before any bead exists: reviewing after the backlog is
created means fixing the plan and the issues both.

## 10. Hand the backlog to `backlog-task`

The document is written, reviewed and committed. Creating the beads is
`backlog-task`: it checks the plan is clean, reprints Section 6's
stories for the one approval, runs the Section 7 list one command at a
time, and reads bd back to prove the acceptance criteria and the blocking
edges stored.

Name three things and load it: the plan's path, the slice marked
`building`, and the Section 7 list it is to run. Load nothing else — the
slice is cut and the list is generated, and rebuilding either there would
specify something this document does not say.
