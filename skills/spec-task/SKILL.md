---
name: spec-task
description: Turns a design conversation into two things and no third — the design documents updated with whatever the conversation settled about the product, and a slice of cards whose acceptance criteria are EARS requirements, each carrying the command that proves it and a status derived from running that command. Writes the design documents itself, because the conversation was the approval, and draws the line at literal code: a source file, a function, a test, a stylesheet value, a configuration key. Takes the definition of released from the project where it states one. On a returning initiative it also decides and sizes the next slice, from the design, the backlog, and the last retro's findings, then cuts it into sized tasks with the exact bd (beads) commands that will create them, while everything beyond it stays one line and a dependency edge. Hands those commands to backlog-task, which creates and verifies the cards. Use when asked to write a spec, spec something out, turn a design or a discussion into requirements, define acceptance criteria, decide or size the next slice, or break designed work into tickets or a backlog — and when work has been designed but nothing durable has been written down.
---

# spec-task — design conversation in, a changed design and a backlog out

For the design conversation named in $ARGUMENTS, respond with the sections
below in order. If $ARGUMENTS is empty, the design conversation is this
session's own history — say so, and name where it starts. The deliverables are
the two in Section 5: the design document edits, written and committed by
Section 8, and the cards, created by `backlog-task`. Section 9 reviews both.
Section 8 writes and commits without asking.
This template touches bd only to read it; the backlog is created by
`backlog-task`, which Section 10 hands to. Section 1 stops for approval
of the slice itself on a returning initiative; `backlog-task` holds the
other stop, approval of the cards built from it.

## The design documents hold the product, and the cards hold the work

**A design document describes the product.** The rules of the game or the
business logic of the application, the aesthetic, and the main ideas,
written so a reader finishes knowing how the thing behaves. No formulae and
no code, and no account of how any of it is built: no source file, no
function, no test, no engine setting, no configuration key. No slice,
ticket or card either, because those describe a schedule. One exception
stands on purpose — a tag on an element saying the build holds it.

**When the conversation settles how the product behaves, write it into the
design document in this run.** The conversation is the approval. Do not park
it in a card, a plan, or a note for the operator to rule on later: they have
just ruled on it, and a decision recorded anywhere else is a decision the next
reader of the design will not find. Measured on one project: a blink rate, the
rule for where Enter lands, and twenty-six other behaviours sat in a plan file
across six slices, because a rule reading "correcting it is the operator's
call" gave nobody a moment to make the call in.

**The line is literal code.** An implementation detail is a source file, a
function, a test, a stylesheet value, a configuration key — the things that
change when somebody refactors and the product does not. Everything else is the
product. The test to apply: can a person using the thing tell the difference?
They can tell one blink rate from two, so how many rates there are is design.
They cannot tell a grid of elements from a canvas, so that is code, and it
belongs in the code.

**The cards are what is being built next.** One card per task, its acceptance
criteria carrying the requirement and the command that proves it. There is no
third document: no plan file, no index, no per-slice leaf, and no separate
record of decisions already made. A decision about the product is in the
design, a decision about the code is in the code, and everything not yet done
is a card.

Deciding an unclear case: ask who would have to open the file to keep the
sentence true, and whether they have any reason to. Nobody renaming a
function opens a design document, which is why prose may not point at code
while a doc comment may point at a design section. The argument in full,
the research behind it, and the run that produced the rule:
[references/two-documents.md](references/two-documents.md).

The **current slice** is the only part specified deeply — EARS text, a proof
command, acceptance criteria on the card. Everything past it is one sentence in
the repository's look-ahead sketch, if it keeps one, and at most a card title
carrying its dependency edges. Sketching ahead is cheap; specifying ahead is
not.

**On a returning initiative the design documents and the open cards are the
input, not something to re-derive.** Take Sections 1, 2 and 3 from them: the
definition of released the project states, the product rules the design already
settles, and the questions the open cards already hold. Section 4 specifies only
the slice Section 1 names. Nothing already settled is researched again or asked
again.

Order is enforced: each section is built from the one above it and checked
by the one below.

This template is new. If a section fights the work rather than catching
something, say so in the response instead of quietly skipping it.

## 0. Before Section 1, read your own room

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

Past the ceiling it reports, hand off BEFORE starting this template rather than
after finishing it: say so, say that no section has run, and let the operator
clear, per `clear-task`. A template is a session's worth of work, so a session
that begins one already over the line ends it far over, and every section it
writes on the way is written in a session that should have stopped. Measured: a
session printed "turn 72, context 231,229 of 170,000 — hand off", quoted that
verdict back in its own evidence block, created ten cards over the next two
hours, printed the same verdict again at 251,737, and ended at 263,205.

This is the only budget check in this template, and it is deliberately at the
front: planning a slice is where a session's context grows fastest, so the
question worth asking is whether to start, not whether to carry on.

## 1. Setup, boundaries, and what "released" means here

Real output, not paraphrase:

```
$ pwd && git rev-parse --show-toplevel
$ ls -d .beads 2>&1
$ bd list --status open 2>&1 | tail -3
$ ls -d docs design specs 2>/dev/null
```

State the repository root, whether bd is already initialized here, the
issue prefix in use, and the directory the design documents live in.

**Then find the design documents and read them.** They are the description
of the product this work changes, and a slice cut without them specifies a
product nobody described. Name the directory and how you found it, list
what is in it, and read enough to state in two or three sentences what the
product does — from the documents, not from the conversation. Where the
repository holds no design documents at all, say so in one line and carry on;
the cards are then the only durable writing, and that is a finding worth
reporting rather than a blocker.

Take three things from them: the definition of released if they state one, the
behaviour the current slice has to match, and the questions they leave open.
Do not restate their rules anywhere else — a copy is a second place for that
rule to be wrong. Where this conversation settles something they get wrong or
leave unsaid about the product, Section 5 writes it in and Section 8 commits
it.

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
Otherwise, read the repository's look-ahead sketch if it keeps one, the
backlog, and — following a retro — its findings, and name the next slice:

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

**One slice is one feature.** Write the `a person can` line as a single
sentence naming one capability, and where that sentence needs an "and" to
join two capabilities a player would think of separately, cut it there and
specify the first half. The operator has to be able to hold the slice in
mind as one coherent step of progress when they open the project, so what
decides the cut is what the sentence names rather than how many tasks fall
out of it. A slice that failed this test, and what it cost:
[references/slice-size.md](references/slice-size.md).

**On a returning initiative, stop here before Section 2's research
begins.** Nothing past this point has been written yet, which is what
makes this the cheap place to catch a wrong slice — catching it after
Sections 2 through 9 have run costs the whole pass. This stop asks one
question, the one below. Section 3's open questions wait for Section 3;
carrying them into this stop puts them to the operator before the check
that would have answered some of them has run.

**Unattended, this stop is a line in a file.** Inside a `session-loop` run
nobody reads a question in the transcript, so write `HANDOFF.md` through
`clear-task` with a first line reading `BLOCKED:` and one sentence naming the
slice awaiting confirmation, and stop — nothing here has been written yet, so
there is nothing to commit first. Write it through the skill rather than by
hand, however close the ceiling is: the handoff point is a budget and not a
limit.

**Open the ask with the phase line**, directly above the question — the
four phases in order, this stop's capitalized. Measured: the operator asked
"What phase are we in?" twice inside one planning pass; the line was already
in this template and nothing told anyone to print it.

```
PLAN -> build -> demo -> retro
```

Proceed with the slice above, or name a different one?

## 2. Source lines from the design conversation

Real quotes with locations. One record per decision this slice rests on:

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

Each question gets one of three outcomes, and no fourth. Check the first
before either of the others:

- The slice's own scope — what the operator approved in Section 1 and what
  it leaves out — or a source line in Section 2 already settles it. Answer
  it from that line, quoted, and do not put it to the operator. Measured:
  a handoff listed "turning a battalion at deployment" among what the
  slice leaves out and, further down, asked the operator whether a
  battalion may turn at deployment.
- The operator answers it, and the answer becomes a new source line in
  Section 2.
- Nobody answers it, and it goes verbatim into the out-of-scope list in
  Section 5.

Do not answer them yourself. Quoting the slice's own scope or a source line
is not answering yourself; it is reading an answer already given. If an
unanswered question would change what the requirements say, stop and ask —
CLAUDE.md rule 2, a missing precondition is a stop rather than a guess.

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

## 5. What this run writes, and where each piece lands

Two outputs and no third. Print both in full before writing either.

**The design document edits.** Every product decision the conversation
settled, as the exact prose that will land, naming the document and the
section that will hold it. A decision with no home named is a decision that
will not be written, so name one. Where the conversation settled nothing
about the product, say that in one line rather than inventing an edit.

These are the product's rules, so they read as the document reads: present
tense, a person as the actor, and no mention of a slice, a card, a source
file, or this run. A reader a year from now cannot tell which conversation
produced the sentence, and does not need to.

**The cards.** The Section 4 records for the current slice, one card each,
and the one-line later requirements for everything past it. A card carries
its requirement as acceptance criteria, the command that proves it, and the
design document it serves as its spec id. A test seam — the function,
endpoint or command-line boundary a proof command drives, and any fixture
that has to exist first — goes on the card whose proof needs it.

Nothing else is written. No plan file, no index, no leaf, no separate record
of decisions already made, and no user-story list on disk: the stories are how
Section 6 reports the work to the operator, and the cards are how it is
recorded. Where the repository keeps a one-line look-ahead sketch, the later
requirements go there and carry no requirement text, no proof command, no
status, and no slice number.

Two rules about status. A requirement's status is **derived by running its
proof command**, never typed from memory — `built` means the command was run
in this session and passed. And a `stubbed` requirement names the slice that
will replace it, so a deliberate fake in a walking skeleton cannot be mistaken
for finished work.

Prose follows CLAUDE.md "Communication Style": plain sentences, a named actor
and verb, no invented compound-noun labels.

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
reads. `--spec-id` carries the design document the card serves, which is the
link from a card back to the product rule it is building.

Use this per-issue form, or `bd create --file` with the section format
`backlog-task` Section 3 gives. Neither `--file` nor `--graph` creates a
dependency or sets a spec id, so list `bd dep add` and `bd update --spec-id`
after either. Do not use `bd create --graph` at all: it reports success while
dropping the acceptance criteria, which is the one field this template exists
to produce. Measured output for all three forms, and what each flag renders as:
[references/bd-behavior.md](references/bd-behavior.md).

Where Section 1 found no `.beads/`, this list's first line is
`bd init --skip-agents --skip-hooks -p <prefix>`, both flags required per
Section 1. Section 9 regenerates the whole list on every round, and
`backlog-task` runs the list as Section 7 leaves it.

## 8. Write the design document edits

Write Section 5's edits into the documents they named. Do not ask first, and
do not stop here: the conversation was the approval, and Section 9's loop
revises the documents in place.

Write only what Section 5 printed. A sentence that appears in a document and
not in that block was composed while editing, which is where the worst design
changes come from — go back and add it to the block, or drop it.

**Write no status tag and no card id into a design document.** Neither belongs
to the product, and both rot. Where the repository generates a document, edit
its source rather than the file, and say which.

Then run whatever the repository uses to check its own documents, name it, and
report what it printed. Where it cannot run here, say so and say why.

**Then commit, without asking.** Committing is covered by the standing
permission in `git-commit`. Stage the documents by path, per `git-commit`.
Nothing here is published anywhere, per CLAUDE.md "Local Files by Default, No
Publishing Without Asking".

If the directory is not tracked by git at all, say so as a finding and stop,
because that is a precondition rather than something to fix silently.

## 9. Review for gaps, and re-review until a round changes nothing

This is a loop, not a single pass. One pass finds the gaps in the slice as
first cut and none of the gaps its own fixes introduce.

**One round is these five steps.**

1. Run `design-gap-task` over the design documents' directory. That template
   hunts for holes in a described product — a rule that sorts things into
   categories without covering every case, an entity created and never
   removed. Its findings are holes in the product, and step 3 says where each
   one goes.
2. Then check the slice itself, which `design-gap-task` has not read. Two
   sweeps. **Every requirement making a factual claim about an existing
   system, checked against its cited source** — that sweep looks for what
   is missing, and a requirement that is present and wrong passes it
   untouched. And **every requirement checked against the design documents
   for a rule it contradicts**, because a slice specifying behaviour the
   product was never designed to have will be built and then argued about.
3. Act on every finding, one of four ways:
   - A hole in the product the operator has **already settled** in
     conversation becomes a design document edit, written the way Section 5
     writes one.
   - A hole in the product **nobody has settled** becomes a card asking the
     question and naming the document that will hold the answer. This is the
     only finding that waits for the operator, and it waits because nobody
     has decided yet rather than because a template needs permission.
   - A missing rule **inside the current slice** becomes a new requirement in
     Section 4, with its own proof command, and a task in Section 6. Outside
     it, one line in the look-ahead sketch and at most a sketched card title.
   - A finding you reject gets one line saying why.
4. Revise, and say what changed in each place you changed it.
5. Re-enter at Section 4 and come forward through 6 and 7: renumber the
   requirements, re-run the coverage check, regenerate the command list.
   Do not patch those in place — the approval `backlog-task` asks for is on
   a list built from the requirements as they now stand. A design document
   edit from step 3 is written by Section 8 like any other.

**When the loop ends.** A round producing no new or changed requirement
ends it. A finding landing only in out-of-scope, or getting a one-line
rejection, does not start another round. Print how many rounds ran and
what the last one found.

**The ceiling.** If a fourth round still changes a requirement, stop and
hand the operator the remaining findings rather than continuing. Then ask
which of them to fold in and which to leave, as the last thing in the
message. What bounds the loop in the ordinary case is step 3's routing of
out-of-slice findings.

A round that only edits design documents does not start another one either.
Those edits change the product's description rather than the slice, and the
next round's `design-gap-task` reads them as they now stand.

**Anti-anchoring.** The previous round's report is context, not precedent.
Round two runs `design-gap-task` again — step 1 is not optional on a later
round — and lets the filter drop duplicates on their own merits.

This loop closes before any card exists: reviewing after the backlog is
created means fixing the slice and the cards both.

## 10. Hand the backlog to `backlog-task`

The design documents are written, reviewed and committed. Creating the cards is
`backlog-task`: it checks the tree is clean, reprints Section 6's stories for
the one approval, runs the Section 7 list, and reads bd back to prove the
acceptance criteria and the blocking edges stored.

Name three things and load it: the design documents this slice serves, the
slice being cut, and the Section 7 list it is to run. Load nothing else — the
slice is cut and the list is generated, and rebuilding either there would
specify something this run did not say.
