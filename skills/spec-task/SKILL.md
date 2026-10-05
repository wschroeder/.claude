---
name: spec-task
description: Turns a design conversation into updated design documents and a slice of cards whose acceptance criteria are EARS requirements, each with the command that proves it. Writes the design documents itself and stops short of literal code. On a returning initiative it decides and sizes the next slice from the design, the backlog, and the last retro, and cuts it into sized tasks; where the project uses bd (beads), it also writes the create commands and hands them to backlog-task. Use when asked to write a spec, spec something out, turn a design or a discussion into requirements, define acceptance criteria, decide or size the next slice, or break designed work into tickets or a backlog, and when work has been designed but nothing durable has been written down.
---

# spec-task — design conversation in, a changed design and a backlog out

For the design conversation named in $ARGUMENTS, respond with the sections
below in order. If $ARGUMENTS is empty, the design conversation is this
session's own history — say so, and name where it starts. The deliverables are
the two in Section 5: the design document edits, written and committed by
Section 8, and the cards, created by `backlog-task`. Section 9 reviews both.
Section 8 writes and commits without asking.
Where the repository keeps its cards in bd, this template only reads it; the
cards are created by `backlog-task`, which Section 10 hands to. Section 1
stops for approval of the slice itself on a returning initiative;
`backlog-task` holds the other stop, approval of the cards built from it.

Why each rule says what it says, and the run that produced it, is in
[references/why.md](references/why.md). Read it only when you dispute a
rule.

## The design documents hold the product, and the cards hold the work

**A design document describes the product.** The rules of the game or the
business logic of the application, the aesthetic, and the main ideas,
written so a reader finishes knowing how the thing behaves. No formulae and
no code, and no account of how any of it is built: no source file, no
function, no test, no engine setting, no configuration key. No slice,
ticket or card either. One exception: a tag on an element saying the build
holds it.

**When the conversation settles how the product behaves, write it into the
design document in this run.** Do not park it in a card, a plan, or a note
for the operator to rule on later.

**Write only what the conversation has settled.** While the operator is still
talking the design through, do not put into the design document a rule they
never stated or an open question they never raised. Settle it with them
first.

**The line is literal code.** An implementation detail is a source file, a
function, a test, a stylesheet value, a configuration key. Everything else is
the product. The test to apply: can a person using the thing tell the
difference?
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
sentence true, and whether they have any reason to. Design prose may not
point at code; a doc comment may point at a design section. The argument in
full, the research behind it, and the run that produced the rule:
[references/two-documents.md](references/two-documents.md).

The **current slice** is the only part specified deeply — EARS text, a proof
command, acceptance criteria on the card. Everything past it is one sentence in
the repository's look-ahead sketch, if it keeps one, and at most a card title
carrying its dependency edges.

**On a returning initiative the design documents and the open cards are the
input, not something to re-derive.** Take Sections 1, 2 and 3 from them: the
definition of released the project states, the product rules the design already
settles, and the questions the open cards already hold. Section 4 specifies only
the slice Section 1 names. Nothing already settled is researched again or asked
again.

Order is enforced: each section is built from the one above it and checked
by the one below.

If a section fights the work rather than catching something, say so in the
response instead of quietly skipping it.

## Product rules every design starts from

Apply these when Section 3 answers a question, when Section 4 writes a
requirement, and when Section 5 writes a design edit. A question one of them
settles is not an open question.

- Keep the project's purpose in view, and automate wherever possible.
- Where automation cannot settle a record, a person decides instead of the
  record failing, and their decision wins. Where even a reviewer cannot settle
  it, the record stays blocked.
- Keep a single source of truth: the system of record wins over a local edit.
- Business facts that users know are data they can edit, never code.
- The domain sets how strict a check is.
- Never guess at ambiguous input, and never normalize away text that may carry
  meaning.
- When a value is unknown, store nothing, derive the default when reading, and
  use the conservative default.
- State a change's impact as the number affected out of the total.
- When two records turn out to be one, move the data to the survivor before
  removing the duplicate.

## 0. Before Section 1, read your own room

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

Past the ceiling it reports, hand off BEFORE starting this template rather
than after finishing it: say so, say that no section has run, write the
handoff through `clear-task` yourself, and then ask the operator to `/clear`.
This is the only budget check in this template.

Where you stop partway anyway, because the next section will not fit, stop at a
section boundary and write the handoff through `clear-task` yourself in that
turn. Do not recommend that the operator run it.

## 1. Setup, boundaries, and what "released" means here

Real output, not paraphrase:

```
$ pwd && git rev-parse --show-toplevel
$ ls -d .beads 2>&1
$ git log --reverse --format=%ae | head -1
$ ls -d docs design specs 2>/dev/null
```

State the repository root and the directory the design documents live in.

**Then say whether this repository keeps its cards in bd.** It does where
`.beads/` exists. Where `.beads/` is absent, it does only if the first commit's
address is the operator's: never bring bd into a repository the operator did
not start. Where it keeps its cards in bd, read
[references/bd-commands.md](references/bd-commands.md) now. Where it does not,
Section 6's stories and task records are the backlog, and Sections 7 and 10
say what that changes.

**Then find the design documents and read them.** Name the directory and
how you found it, list what is in it, and read enough to state in two or
three sentences what the product does — from the documents, not from the
conversation. Where the repository holds no design documents at all, say so
in one line as a finding, not a blocker, and carry on.

Take three things from them: the definition of released if they state one, the
behaviour the current slice has to match, and the questions they leave open.
Do not restate their rules anywhere else. Where this conversation settles
something they get wrong or leave unsaid about the product, Section 5 writes
it in and Section 8 commits it.

**Then settle the definition of released.** It is the operator's to decide
— for one team a deployment behind a feature flag, for another "runs on
this machine".

- If a design document or an existing plan in this repository already
  states a definition of released, quote it with its file and line, treat
  it as settled, and do not ask. That sentence is the answer.
- If a `project-definition-of-done` skill is listed in the available
  skills, load it and use what it says. Say that you did.
- If the handoff this session opened on quotes the operator's definition of
  released, use it, say that it came from the handoff, and do not offer to
  record it in the project.
- If none of these exists, ask the operator with AskUserQuestion and quote the
  answer as a source line in Section 2. Then offer, in the same turn, to
  record it as that skill.

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

A path through the system, not a layer of it. Resize or split the sketch's
slice if it no longer fits what now exists. Only the next slice is decided
here.

**One slice is one feature.** Write the `a person can` line as a single
sentence naming one capability, and where that sentence needs an "and" to
join two capabilities a player would think of separately, cut it there and
specify the first half. What the sentence names decides the cut, not how
many tasks fall out of it. A slice that failed this test, and what it cost:
[references/slice-size.md](references/slice-size.md).

**On a returning initiative, stop here before Section 2's research
begins.** This stop asks one question, the one below. Keep Section 3's open
questions for Section 3.

**Unattended, this stop is a line in a file.** Inside a `session-loop` run,
write `HANDOFF.md` through `clear-task` with a first line reading `BLOCKED:`
and one sentence naming the slice awaiting confirmation, and stop. There is
nothing to commit first. Write it through the skill rather than by hand,
however close the ceiling is.

**Open the ask with the phase line**, directly above the question — the
four phases in order, this stop's capitalized.

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
and belongs in Section 3. Per CLAUDE.md rule 13, the quote is the ref, not
its location.

If the design has not been stress-tested, run `grill-me` before this
section, and quote its interview as the conversation.

**Before spawning anything to research a source line, load `subagents`.**
Use a fresh agent, never a fork.

## 3. Open questions — what the design does not settle

List what the source lines leave undetermined. At minimum, sweep these
five: what happens on invalid input; what happens when something the
system depends on is unavailable; what happens at the limits (empty, one,
very many, concurrent); who is allowed to do it; and what is deliberately
not being built.

Each question gets one of four outcomes, and no fifth. Check the first two
before either of the others:

- The slice's own scope — what the operator approved in Section 1 and what
  it leaves out — or a source line in Section 2 already settles it. Answer
  it from that line, quoted, and do not put it to the operator.
- It is a question of fact that the project can already answer: the
  recorded data, the code, or the work done so far. Research it, and answer
  it from what you found, quoted. Only a question about how the product
  should behave goes to the operator.
- The operator answers it, and the answer becomes a new source line in
  Section 2. The question you ask them quotes every fact you already found
  that bears on it. Each option says what the person will see and do, in
  the product's own terms. Where an option keeps something that exists
  today, it says what that thing looks like on screen rather than naming it.
- Nobody answers it, and it goes verbatim into the out-of-scope list in
  Section 5.

Do not answer them yourself. Quoting the slice's own scope or a source line
is not answering yourself; it is reading an answer already given. If an
unanswered question would change what the requirements say, stop and ask,
per CLAUDE.md rule 2.

**End this section by saying which it was.** Either the numbered questions
the operator has to answer, asked with AskUserQuestion, with nothing
written after them — or the one plain sentence that every question went to
out of scope and there is nothing here for them to do.

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
movement is real", "after the HUD exists" — but never with an `S<n>` tag.
They are promoted to the full record, slice number included, by the run
that pulls their slice.

Rules for this section:

- No user stories in the requirement. Section 6 groups these requirements
  into stories for the operator.
- The proof command names a specific test, check or query — for example
  `go test ./ears -run TestUbiquitous`, or
  `curl -s localhost:8080/health | jq -e '.ok'`. "The tests pass" is not a
  proof command.
- Run every proof command now, and **read the count of tests it ran, not
  its exit code**.
- If a proof command already passes, then the requirement is `built` — mark
  it and keep it out of Section 6. One that fails with "no such test" is the
  expected shape of unbuilt work.
- A command that cannot be run yet says so and says why, per CLAUDE.md
  rule 3. Do not paste an imagined result.
- **Anything the operator rejected gets its own requirement saying it is
  gone**, in the unwanted or state-driven pattern ("the system shall not
  show …"), with a proof command that fails while it is still there.
- **A requirement that describes how an existing system behaves cites
  where that behavior was observed.** Anything of the form "like X does",
  "matching Y", or any claim about a protocol, format or product this work
  reproduces carries a source: a URL, a file path, a command whose output
  shows it.
- **A requirement to compare the work against reference material carries a
  proof that fails when no reference is saved.** Name the directory outside
  the repository where the reference images go, and make the proof command
  list at least one image there beside the capture, for example
  `ls "$TMPDIR/ref"/*.png && node tests/capture.js "$TMPDIR/shots"`. The
  requirement also says that the card's note names each reference image the
  comparison used. A search result with no picture in it is not a reference.
- **Every slice ends in a requirement whose proof produces something a
  person can look at and operate.** It is written like any other
  requirement, and its proof command is the one that produces the artifact.
  If every requirement in the slice is an internal module, the cut was
  horizontal.
- **Where the definition of released says a person operates the thing, one
  requirement in the slice is proved by the input that person sends.** Not
  by calling the code that input would have reached — by the press, the
  keystroke or the request itself, arriving the way it arrives in the
  assembled product. Write it as a requirement here, at planning. For how
  to send this product real input, load `project-drive` if it appears in the
  available skills; if nothing is listed, say so in one line and write the
  requirement anyway.
- **That input is aimed at the thing as a person sees it, not at a
  coordinate the code returns.** Never take the target's position from the
  module the assertion reads. The requirement names the target from what is
  on the screen — the drawn extent, the rendered label, the visible control —
  and compares the ground that answers the input against the ground the
  person is aiming at.

## 5. What this run writes, and where each piece lands

Two outputs and no third. Print both in full before writing either.

**The design document edits.** Every product decision the conversation
settled, as the exact prose that will land, naming the document and the
section that will hold it. Name a home for every decision. Where the
conversation settled nothing about the product, say that in one line rather
than inventing an edit.

Write them as the document reads: present tense, a person as the actor, and
no mention of a slice, a card, a source file, or this run.

**The cards.** The Section 4 records for the current slice, one card each,
and the one-line later requirements for everything past it. A card carries
its requirement as acceptance criteria, the command that proves it, and the
design document it serves as its spec id. A test seam — the function,
endpoint or command-line boundary a proof command drives, and any fixture
that has to exist first — goes on the card whose proof needs it.

Nothing else is written. No plan file, no index, no leaf, no separate record
of decisions already made, and no user-story list on disk. Where the
repository keeps a one-line look-ahead sketch, the later requirements go there
and carry no requirement text, no proof command, no status, and no slice
number.

Two rules about status. A requirement's status is **derived by running its
proof command**, never typed from memory — `built` means the command was run
in this session and passed. And a `stubbed` requirement names the slice that
will replace it.

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
     related:    [T<n>] | none
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

Section 9's review loop re-runs this check on every round.

**A card says what has to be true, never how to build it.** Keep the cards
flat, with no parent or epic cards. Where nobody knows yet how to build a
task, cut a spike card ahead of it that answers the question. Mark two cards
that touch without one waiting on the other as related, and keep `blocked-by`
for a card that cannot start until another finishes.

A current-slice task with no proof command is not a task. Fold it into one
that has, or drop it. A sketched later task has no proof command.

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

When a task fits no story, say so instead of inventing a story around it.
Writing "As a developer" is inventing one.

## 7. The card commands

Where Section 1 found that the repository keeps its cards in bd, write the
command list that [references/bd-commands.md](references/bd-commands.md)
describes. Section 9 regenerates the whole list on every round, and
`backlog-task` runs the list as Section 7 leaves it.

Where it does not, there is no list: Section 6's stories and task records are
the backlog, and Section 10 says where they go.

## 8. Write the design document edits

Write Section 5's edits into the documents they named. Do not ask first, and
do not stop here.

Write only what Section 5 printed. If you compose a sentence while editing,
add it to that block or drop it.

**Write no status tag and no card id into a design document.** Where the
repository generates a document, edit its source rather than the file, and
say which.

Then run whatever the repository uses to check its own documents, name it, and
report what it printed. Where it cannot run here, say so and say why.

**Then commit, without asking.** Stage the documents by path, per
`git-commit`. Publish nothing, per CLAUDE.md "Local Files by Default, No
Publishing Without Asking".

If the directory is not tracked by git at all, say so as a finding and stop.

## 9. Review for gaps, and re-review until a round changes nothing

This is a loop, not a single pass.

**One round is these five steps.**

1. Run `design-gap-task` over the design documents' directory. Step 3 says
   where each of its findings goes.
2. Then check the slice itself, which `design-gap-task` has not read. Two
   sweeps: **every requirement making a factual claim about an existing
   system, checked against its cited source**, and **every requirement
   checked against the design documents for a rule it contradicts**.
3. Act on every finding, one of five ways:
   - A problem that predates this branch is not this slice's to spec or fix.
     It goes to out of scope, in one line naming it.
   - A hole in the product the operator has **already settled** in
     conversation becomes a design document edit, written the way Section 5
     writes one.
   - A hole in the product **nobody has settled** becomes a card asking the
     question and naming the document that will hold the answer. This is the
     only finding that waits for the operator.
   - A missing rule **inside the current slice** becomes a new requirement in
     Section 4, with its own proof command, and a task in Section 6. Outside
     it, one line in the look-ahead sketch and at most a sketched card title.
   - A finding you reject gets one line saying why.
4. Revise, and say what changed in each place you changed it.
5. Re-enter at Section 4 and come forward through 6 and 7: renumber the
   requirements, re-run the coverage check, regenerate the command list
   where there is one. Do not patch those in place. Section 8 writes a
   design document edit from step 3 like any other.

**When the loop ends.** A round producing no new or changed requirement
ends it. A finding landing only in out-of-scope, or getting a one-line
rejection, does not start another round. Print how many rounds ran and
what the last one found.

**The ceiling.** If a fourth round still changes a requirement, stop and
hand the operator the remaining findings rather than continuing. Then ask
which of them to fold in and which to leave, as the last thing in the
message.

A round that only edits design documents does not start another one either.

**Anti-anchoring.** The previous round's report is context, not precedent.
Round two runs `design-gap-task` again — step 1 is not optional on a later
round — and lets the filter drop duplicates on their own merits.

This loop closes before any card exists.

## 10. Hand the backlog on

The design documents are written, reviewed and committed.

Where the repository does not keep its cards in bd, write Section 6's stories
and task records into the handoff through `clear-task`. `tdd-cycle` reads its
task list there, and nothing else in this section applies.

Where it does, creating the cards is `backlog-task`: it checks the tree is
clean, reprints Section 6's stories for the one approval, runs the Section 7
list, and reads bd back to prove the acceptance criteria and the blocking
edges stored.

Name three things and load it: the design documents this slice serves, the
slice being cut, and the Section 7 list it is to run. Load nothing else.
