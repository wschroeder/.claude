---
name: spec-task
description: Turns a design conversation into updated design documents and a slice of cards whose acceptance criteria are EARS requirements, each with the command that proves it. Writes the design documents itself and stops short of literal code. On a returning initiative it decides and sizes the next slice from the design, the backlog, and the last demo's feedback, and cuts it into sized tasks; where the project uses bd (beads), it also writes the create commands and hands them to backlog-task. Use when asked to write a spec, spec something out, turn a design or a discussion into requirements, define acceptance criteria, decide or size the next slice, or break designed work into tickets or a backlog, and when work has been designed but nothing durable has been written down.
---

# spec-task — design conversation in, a changed design and a backlog out

1. For the design conversation named in $ARGUMENTS, respond with the sections below in order.
2. If $ARGUMENTS is empty, take this session's own history as the design conversation, say so, and name where it starts.
3. Produce the two deliverables in Section 5: the design document edits, which Section 8 writes and commits without asking, and the cards, which `backlog-task` creates. Section 9 reviews both.
4. Where the repository keeps its cards in bd, only read bd here; Section 10 hands the creating to `backlog-task`.
5. Stop for approval of the slice in Section 1 on a returning initiative; `backlog-task` holds the other stop, approval of the cards.

## The design documents hold the product, and the cards hold the work

1. Write a design document to describe the product: its rules or business logic, its aesthetic, and its main ideas, so a reader finishes knowing how the thing behaves.
2. Keep out of a design document every formula, every piece of code, and every account of how the product is built: source files, functions, tests, engine settings, configuration keys, slices, tickets, and cards. The one exception is a tag on an element saying the build holds it.
3. When the conversation settles how the product behaves, write it into the design document in this run, never into a card, a plan, or a note for later.
4. Write only what the conversation has settled; settle any rule the operator never stated, or open question they never raised, with them first.
5. Draw the line at literal code: a source file, a function, a test, a stylesheet value, or a configuration key is code, and everything else is product. Ask whether a person using the thing can tell the difference.
6. Write one card per task, its acceptance criteria carrying the requirement and the command that proves it.
7. Keep no third document: no plan file, no index, no per-slice leaf, and no record of decisions already made. A product decision goes in the design, a code decision in the code, and everything not yet done is a card.
8. For an unclear case, ask who would have to open the file to keep the sentence true, and whether they have any reason to. Design prose never points at code; a doc comment may point at a design section.
9. Specify only the current slice deeply, with EARS text, a proof command, and acceptance criteria on the card; give everything past it one sentence in the look-ahead sketch, if the repository keeps one, and at most a card title with its dependency edges.
10. On a returning initiative, take Sections 1, 2, and 3 from the design documents and open cards: the stated definition of released, the product rules already settled, and the questions the open cards hold. Research and ask nothing already settled, and specify only the slice Section 1 names.
11. Build each section from the one above it, and check it with the one below.
12. If a section fights the work rather than catching something, say so in the response instead of skipping it.

## Product rules every design starts from

1. Apply these when Section 3 answers a question, Section 4 writes a requirement, and Section 5 writes a design edit; a question one of them settles is not open.
2. Where the slice gives one kind a behavior that a sibling kind already has a rule for, apply the sibling's rule first, over the list below. Make any departure an open question that names it, and label any option that departs.

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

1. If it reports you are past the ceiling, hand off before Section 1: say so, say no section has run, write the handoff through `clear-task` yourself and end the turn, so the auto-clear mod clears the session.
2. Run no other budget check in this template.
3. If you stop partway because the next section will not fit, stop at a section boundary and write the handoff through `clear-task` yourself in that turn, never recommending that the operator run it.

## 1. Setup, boundaries, and what "released" means here

1. Print the real output of:

```
$ pwd && git rev-parse --show-toplevel
$ ls -d .beads 2>&1
$ bd where 2>&1
$ git log --reverse --format=%ae | head -1
$ ls -d docs design specs 2>/dev/null
```

2. State the repository root and the design documents' directory.
3. Say whether the repository keeps its cards in bd: it does where `.beads/` exists or `bd where` prints a database path. Inside a git worktree, rely on `bd where`, because bd keeps `.beads/` in the main checkout.
4. If both come back empty, treat it as a bd repository only when the first commit's address is the operator's; never bring bd into a repository the operator did not start.
5. If it keeps its cards in bd, read [references/bd-commands.md](references/bd-commands.md) now. If not, Section 6's stories and task records are the backlog, and Sections 7 and 10 say what that changes.
6. Find the design documents: name the directory and how you found it, list it, and state in two or three sentences what the product does, from the documents, not the conversation.
7. If the repository holds no design documents, say so in one line as a finding and carry on.
8. Take three things from them: the definition of released, if stated; the behavior the current slice must match; and the questions they leave open.
9. Restate none of their rules elsewhere; where this conversation corrects or adds to them about the product, Section 5 writes it and Section 8 commits it.
10. Settle the definition of released, which is the operator's to decide, by the first of these that applies:
    - If a design document or existing plan in this repository states one, quote it with file and line, treat it as settled, and do not ask.
    - If a `project-definition-of-done` skill is listed, load it, use it, and say so.
    - If the handoff this session opened on quotes the operator's definition, use it, say it came from the handoff, and do not offer to record it.
    - Otherwise ask the operator with AskUserQuestion, quote the answer as a source line in Section 2, and offer in the same turn to record it as that skill.
11. Never answer the definition of released yourself, and never proceed without it.
12. Make the definition describe a shape, not a scope; words such as *fully*, *complete*, *all*, and *end to end* mean it describes the finished product. Offer only options that pass, and rewrite one the operator supplies that does not.
13. Decide which slice this pass specifies. On a brand-new initiative, the slice is the walking skeleton Section 4 cuts. Otherwise read the look-ahead sketch if one exists, the backlog, the last demo's feedback, and any retro findings from a review, and name the next slice:

```
  slice:      S<n> — <name>
  a person can: <what they will be able to see or do when it is finished>
  retires:    <which stubs it replaces, by requirement id>
  inherits:   <failing proof commands the prior slice left behind>
  carries:    <requirements the last demo's feedback added, by id>
```

14. Cut a path through the system, not a layer of it, and resize or split the sketch's slice if it no longer fits what exists. Decide only the next slice.
15. Make one slice one feature: write the `a person can` line as one sentence naming one capability. If it needs an "and" to join two capabilities a user would think of separately, cut there and specify the first half. Let the sentence decide the cut, never the task count.
16. On a returning initiative, stop here before Section 2's research, asking only the question below; keep Section 3's questions for Section 3.
17. Inside a `session-loop` run, make this stop a `HANDOFF.md` written through `clear-task`, whose first line reads `BLOCKED:` with one sentence naming the slice awaiting confirmation, and stop. Write it through the skill, never by hand, however close the ceiling is.
18. Open the ask with the phase line directly above the question, this stop's phase capitalized:

```
SPEC -> build -> demo
```

Proceed with the slice above, or name a different one?

## 2. Source lines from the design conversation

1. Write one record per decision this slice rests on, with a real quote and its location:

```
[S1] <file:line, or "session, operator message beginning '<first six words>'">
     "<the quoted line>"
```

2. Move a decision you cannot quote to Section 3 as an open question; the quote is the ref, not its location.
3. Load `subagents` before spawning anything to research a source line, and use a fresh agent, never a fork.

## 3. Open questions — what the design does not settle

1. List what the source lines leave undetermined, sweeping at least: invalid input; something the system depends on being unavailable; the limits (empty, one, very many, concurrent); who is allowed to do it; and what is deliberately not being built.
2. Give each question one of four outcomes, checking the first two before the others:
   - If the slice's approved scope, or a Section 2 source line, settles it, answer it from that line, quoted, and do not ask the operator.
   - If it is a question of fact the recorded data, the code, or the work so far can answer, research it and answer from what you found, quoted. Send only questions about how the product should behave to the operator.
   - Otherwise the operator answers it, and the answer becomes a new Section 2 source line. Quote every fact you found that bears on it in the question, word each option as what the person will see and do in the product's terms, and describe anything kept from today by how it looks on screen rather than its name.
   - If nobody answers it, put it verbatim in Section 5's out-of-scope list.
3. Never answer a question yourself; quoting the approved scope or a source line is reading an answer already given.
4. If an unanswered question would change what the requirements say, stop and ask.
5. If two design rules disagree about an item in this slice, ask the operator which wins before cutting cards, never carrying it to the demo.
6. Never recommend leaving an item out, narrowing a rule's reach, or deferring an item because of the work it takes.
7. End the section with either the numbered questions, asked with AskUserQuestion and nothing written after them, or one plain sentence saying every question went to out of scope.
8. If there are questions, open the ask with the phase line directly above them, this stop's phase capitalized:

```
SPEC -> build -> demo
```

## 4. Requirements in EARS, each with the command that proves it

1. On a first slice, cut the walking skeleton before writing any requirement, print its record, and hold it to five behaviors or fewer.
2. On a later slice, print the slice Section 1 named and go straight to the patterns.
3. Use the patterns in Mavin's own casing, with the keywords as ordinary words:

```
ubiquitous        The <system> shall <response>
state driven      While <precondition>, the <system> shall <response>
event driven      When <trigger>, the <system> shall <response>
optional feature  Where <feature is included>, the <system> shall <response>
unwanted          If <trigger>, then the <system> shall <response>
complex           While <precondition>, when <trigger>, the <system>
                  shall <response>
```

4. Give each requirement in the current slice the full record:

```
[R1] pattern:  <one of the six above>
     text:     <the requirement in that pattern, one sentence>
     source:   [S<n>]
     slice:    S<n>
     proof:    $ <command>
     output:   <real output from running it now, its failure included>
     status:   planned | stubbed→S<n> | built | demoed
```

5. If a requirement quotes a sentence a person will read on screen, such as a warning or help text, load `writing-prose` and write it through that skill before the slice goes up for approval.
6. If a requirement adds help text or user documentation, check each passage against the screen it explains: cut what the screen already shows, and keep what a figure means and where it comes from.
7. Mark `built` only for what was already true when this section began, never for a command this pass made pass; this template writes no product file.
8. Give each requirement beyond the current slice one line and nothing else:

```
[R9] later — <one sentence saying what will have to be true>
```

9. Give a later line no EARS text, proof command, status, or slice number; it may say roughly when it will matter in prose, never with an `S<n>` tag. The run that pulls its slice promotes it.
10. Put no user stories in a requirement; Section 6 groups requirements into stories.
11. Before any requirement becomes a card, set it beside the design principles in the project's `CLAUDE.md` and quote each principle it touches. If it contradicts one, ask the operator which wins before Section 6 cuts it, even when a spec sentence agrees with the requirement. If the `CLAUDE.md` names no design principles, say so in one line.
12. Make each proof command name a specific test, check, or query, never "the tests pass".
13. Run every proof command now, and read the count of tests it ran, not its exit code.
14. If a proof command already passes, mark the requirement `built` and keep it out of Section 6; a "no such test" failure is the expected shape of unbuilt work.
15. If a requirement concerns a constant of any kind, then it gets no script, no test, and no one-off proof command. A constant is any fixed value: text a person reads, a label, a list of options, a setting, a version, a pinned digest, or a revision hash. Treat a requirement that a thing merely exists the same way. Write a constant into a design document only where that document already names it.
16. If a command cannot run yet, say so and why, and never paste an imagined result.
17. Give anything the operator rejected its own requirement saying it is gone, in the unwanted or state-driven pattern, with a proof that fails while it is still there.
18. Cite where it was observed for any requirement describing how an existing system behaves, such as "like X does" or a claim about a protocol, format, or product: a URL, a file path, or a command whose output shows it.
19. Give a requirement to compare against reference material a proof that fails when no reference is saved: name a directory outside the repository for the reference images, and make the proof list at least one image there beside the capture. Require the card's note to name each reference image used; a search result with no picture is not a reference.
20. End every slice in a requirement whose proof command produces something a person can look at and operate. If every requirement is an internal module, the cut was horizontal.
21. Where the slice's behavior is reachable only by a request the product's own screens never send, such as a server refusing a save no edit can produce, say so in that last requirement. Prove it with the test that sends the request, have the demo show the screens behaving as before, and never forge the request at the demo.
22. Where the definition of released says a person operates the thing, prove one requirement by the input that person sends, the press, keystroke, or request itself arriving as it does in the assembled product, never by calling the code it would reach. If `project-drive` is listed, load it for how to send real input; if not, say so in one line and write the requirement anyway.
23. Have the card carrying that requirement write the operator's steps and commit no script: its design writes the demo file's operate-it steps into `/.tmp/demos/<date>-<slug>/demo.md` by `demo-task` Section 3's method, with a "check after" line for each thing the person will see, and its check reads "walked at the demo". Add no browser test, drive script, or driver to the repository.
24. Aim that input at the thing as a person sees it, never at a coordinate the code returns: name the target from the screen, and compare what answers the input against what the person aims at.

## 5. What this run writes, and where each piece lands

1. Print both outputs in full before writing either.
2. Print the design document edits: every product decision the conversation settled, as the exact prose that will land, naming the document and section for each. If the conversation settled nothing about the product, say so in one line.
3. Write the edits as the document reads: present tense, a person as the actor, and no mention of a slice, a card, a source file, or this run.
4. Print the cards: one per Section 4 record in the current slice, plus the one-line later requirements. Give each card its requirement as acceptance criteria, its proof command, and the design document it serves as its spec id.
5. Put a test seam, the boundary a proof command drives and any fixture it needs, on the card whose proof needs it.
6. Write nothing else: no plan file, index, leaf, decision record, or user-story list on disk. Where a look-ahead sketch exists, put the later requirements there with no requirement text, proof command, status, or slice number.
7. Derive a requirement's status by running its proof command in this session, never from memory.
8. Name the slice that will replace each `stubbed` requirement.
9. Write the prose by CLAUDE.md "Communication Style".

## 6. Task breakdown and sizing

1. Cut the current slice's unbuilt requirements into tasks, each the smallest unit with its own red-green-refactor cycle and worth a fresh reviewer's look; aim for 2–5 minutes of agent time, and re-measure that number rather than obey it.

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

2. Sketch later-slice work as a title and blocking edges only:

```
[T9] title:      <imperative, one line>
     blocked-by: [T<n>] | none
     slice:      later
```

3. Run the coverage check against the two lists, not by eye: every unbuilt current-slice requirement appears in exactly one task. Print the ids that reached no task; a non-empty list means the breakdown is unfinished.
4. Say on each card what has to be true, never how to build it.
5. Keep the cards flat, with no parent or epic cards.
6. If nobody knows yet how to build a task, cut a spike card ahead of it.
7. Mark cards that touch without waiting on each other as related, and keep `blocked-by` for a card that cannot start until another finishes.
8. Put a case that would make an earlier card's path fail in that earlier card, never in one queued after it.
9. Before cutting cards, read the project's `CLAUDE.md` for every rule that an edit lands in the same change as another, and put both edits on the card that changes the code, cutting no card for the second edit alone.
10. Fold or drop any current-slice task with no proof command; the one exception is the card whose check reads "walked at the demo". A sketched later task has no proof command.
11. Name the two boundaries where a task hands work to another: which function or data shape one produces and the next consumes.
12. Print the stories above the task records, one record per story, with every current-slice task in exactly one:

```
Story: As a <person who uses the product>, I can <what they can do>.
  tasks:  [T<n>] [T<n>]
  proof:  <the command, or the thing to look at>
```

13. Make the role someone who uses the product, never the developer. Attach developer-only work, such as the test suite or the pinned toolchain, to the story whose behavior it proves, named on that story's `proof` line.
14. If a task fits no story, say so rather than inventing one; "As a developer" is inventing one.

## 7. The card commands

1. Where Section 1 found the repository keeps its cards in bd, write the command list [references/bd-commands.md](references/bd-commands.md) describes. Section 9 regenerates it every round, and `backlog-task` runs it as left here.
2. Where it does not, write no list; Section 6's stories and task records are the backlog, and Section 10 says where they go.

## 8. Write the design document edits

1. Write Section 5's edits into the documents they named, without asking and without stopping.
2. Write only what Section 5 printed; add any sentence you compose while editing to that block, or drop it.
3. Write no status tag and no card id into a design document.
4. Where the repository generates a document, edit its source, and say which.
5. Run whatever the repository uses to check its documents, name it, and report its output; if it cannot run here, say so and why.
6. Commit without asking, staging the documents by path per `git-commit`, and publish nothing.
7. If the directory is not tracked by git, say so as a finding and stop.

## 9. Review for gaps, and re-review until a round changes nothing

1. Run this as a loop of rounds, each of five steps:
   1. Run `design-gap-task` over the design documents' directory.
   2. Check the slice itself with two sweeps: every requirement making a factual claim about an existing system, against its cited source; and every requirement, against the design documents for a rule it contradicts.
   3. Act on every finding one of five ways:
      - A problem that predates this branch goes to out of scope, in one line naming it.
      - A product hole the operator already settled in conversation becomes a design document edit, written as Section 5 writes one.
      - A product hole nobody settled becomes a card asking the question and naming the document that will hold the answer; only this kind waits for the operator.
      - A missing rule inside the current slice becomes a new Section 4 requirement with its own proof and a Section 6 task; outside it, one line in the look-ahead sketch and at most a sketched card title.
      - A finding you reject gets one line saying why.
   4. Revise, and say what changed in each place.
   5. Re-enter at Section 4 and come forward through 6 and 7: renumber the requirements, re-run the coverage check, and regenerate the command list where there is one, never patching in place. Section 8 writes a design edit from step 3 like any other.
2. End the loop when a round produces no new or changed requirement; a finding that lands only in out of scope, a one-line rejection, or a design-document-only edit starts no new round. Print how many rounds ran and what the last found.
3. If a fourth round still changes a requirement, stop, hand the operator the remaining findings, and end the message asking which to fold in and which to leave.
4. Treat the previous round's report as context, not precedent: run `design-gap-task` again every round, and let its filter drop duplicates on their merits.
5. Close this loop before any card exists.

## 10. Hand the backlog on

1. Where the repository does not keep its cards in bd, write Section 6's stories and task records into the handoff through `clear-task`, where `tdd-cycle` reads its task list, and stop.
2. Where it does, load `backlog-task`, naming three things only: the design documents this slice serves, the slice being cut, and the Section 7 list it is to run. Load nothing else.
