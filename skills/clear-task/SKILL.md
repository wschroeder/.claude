---
name: clear-task
description: Produces a copy-paste continuation prompt for resuming work in a fresh chat after /clear. Frontloads every handoff consideration into ordered sections, then emits the finished prompt as the terminal code block. Writes the sections from what the session already holds rather than re-probing for it. Settles whether a session-loop worker or the operator reads the prompt next, and writes it to HANDOFF.md only for a worker. Carries the words typed after /clear-task into the prompt word for word, as the next session's first step. Use when wrapping up a session before clearing, writing a handoff or continuation prompt, or carrying in-flight work into a fresh chat — "hand this off", "I'm about to /clear", "write me a continuation prompt".
model: sonnet
---

# clear-task — frontload the handoff, then emit the prompt

For the current session's work, produce a continuation prompt that a fresh chat
(after /clear) can act on without re-reading this conversation. Respond with the
sections below in order. The continuation prompt is the LAST thing in your
response — a single fenced code block with nothing after it.

Write every consideration into the ordered sections below FIRST, and assemble
the prompt from them LAST. If you discover a missing consideration while
writing the prompt, that is a defect in the Completeness gate (§12): return
there, add it, and regenerate the prompt. Never append to the prompt.

## 0. Who reads this next (settle it before writing anything)

This template emits one of two artifacts, and one question separates them:
does a `session-loop` worker read this prompt next, or does the operator? A
worker has no other way to receive a prompt, so a worker gets `HANDOFF.md`.
The operator copies a block, so the operator gets the block.

Read the prompt this session opened with. It is already in context, so settling
this costs nothing:

- That opening prompt carries the unattended-loop protocol — the words "You are
  one iteration of an unattended loop", and an instruction to write `HANDOFF.md`
  through this skill. A worker reads this next, and the artifact is the file.
- `session-loop` step 2 is seeding a repository that holds no handoff yet, or
  the operator asked for the file in their own words. A worker reads this next.
- Anything else, the operator included. The artifact is the block.

Then write one line naming the reader and what settled it:

    reader: the operator — this session opened on a request they typed, and
    nothing in it carried the loop protocol

**Do not run `pgrep` to decide this.** That check asks whether any driver is
alive anywhere on the machine, and the question here is whether a worker is
waiting on *this* session's handoff.

## 1. Objective

The north star. One or two sentences in the operator's terms: what is
the overall task, and what does "done" look like? If the session had
several goals, list them and mark each complete / in-flight. No process
recap — state the goal, not the history of how you got here.

## 2. Verified state (the tool output this session already produced)

The ground truth the fresh chat inherits, quoted from what the commands printed
when this session ran them: the branch, the commit subjects and hashes, what the
last `git status` said, the test counts the suite reported, the query result,
the file written. Say when each one ran, because the reader needs to know how
old it is.

Where this session never ran the command, say that instead of filling the gap
in. "No `git status` since the commit at f30be46" is a fact the fresh chat can
act on; an invented status line is not.

**Do not re-run anything to fill this section in.** This skill fires at the
fullest point of a session, where one more turn re-reads all of it. Re-running
buys the reader nothing either, because the state moves between writing the
prompt and reading it. §8's first step is what protects them, and it also
catches a fabricated "done", since the fresh chat's own `git log` shows the
commit is absent.

This section is what every "completed work" claim in §3 must reconcile against.
A "done" claim with no command output behind it is unverified
(~/.claude/CLAUDE.md rule 1, "Verify before claiming"), and it is labelled that
way rather than probed into shape.

## 3. Completed work (each item reconciled against §2)

What was actually accomplished. Tag every item:

- `verified` — backed by a specific line in §2. Cite it (a commit hash,
  a status line, a file).
- `unverified` — done in narrative but not reflected in §2 (an unsaved
  edit, a claim you cannot back with tool output). Say so plainly; do
  not let it read as done.

## 4. Decisions, constraints, and dead-ends

The context most often lost across a /clear:

- Decisions made this session and the reason — so the fresh chat does
  not relitigate them.
- Constraints discovered — an API shape, a schema quirk, an env gotcha,
  a rule that bit.
- Dead-ends — approaches tried that FAILED, and why they failed. This is
  the highest-value, most-forgotten content: without it the fresh chat
  repeats the same failed attempt.

Tag every item here the way §3 tags completed work. A constraint, a
diagnosis, or a reason a thing failed is a claim about the system, and the
fresh chat will act on it without re-deriving it:

- `verified` — name the probe, command, or query that showed it, and quote
  enough of the output that the claim stands on its own.
- `hypothesis:` — everything else. An explanation you find convincing but
  did not measure is a hypothesis, however obvious it feels right now.

Split the observation from the explanation BEFORE tagging either one. A
reading and the diagnosis you drew from it are two claims; one `verified`
covering both launders the diagnosis into a measurement, and the fresh
chat builds on it and finds out the hard way. Write:

    verified: forward vs reversed field order diverges, 4 of 4 blocks, at
      cdfbe35 — sweep output above.
    hypothesis: the rout/flee path is what makes it order-dependent.

NOT "MEASURED: order diverges because the rout path is order-dependent."
That is ~/.claude/CLAUDE.md rules 4 and 10 applied to the handoff itself:
one tag covers one fact, and a causal connector starts a new claim.

**A dead-end is recorded against the mechanism that failed, never against
the class of evidence it was serving.** "macOS `screencapture` returns a
uniform black image in this sandbox" is a dead-end. "Do not retry pixel
screenshots" is a ban, and the fresh chat will obey it in cases the failure
never covered. Name the tool, the call, or the path that failed. Where
another route to the same evidence exists, name that route instead of
closing the subject.

**Something the operator approved is a decision, and it goes here in their
terms.** A design they signed off, a layout they accepted, or a scope they
agreed to goes into this section with the time of the approval, stated in full.
It never goes in as a clause inside a next step in §8: that list gets reordered
and rewritten every session, and a design that lives there shrinks with each
rewrite.

**A decision that already rode the last handoff does not leave this list in
silence.** For every decision in the prompt this session opened with, do one of
three things and say in one line which. Carry it forward word for word, where
it still holds. Record it in the project's own design documents, and point to
the file, where someone should have written it down already. Or strike it,
naming what replaced it or who withdrew it. A shorter restatement is not one of
the three: it drops whatever the restatement left out, and nobody notices.

## 5. Principles the operator highlighted

The operating rules the operator stated this session — how they want the
work done, not what the work is. These are the "always do it this way" /
"never touch that" / "remember to X" instructions the operator emphasized
in their own words: a preferred strategy, a guardrail, a sequencing rule.
They are meant to outrank the fresh chat's own instincts, so they must
survive the /clear verbatim. Distinguish from §4: §4 holds decisions you
reached and why; §5 holds directives the operator handed you. Each
principle should name the concrete behavior, not a label for it
(~/.claude/CLAUDE.md "Communication Style"). If the operator highlighted
no principle this session, write `None` — do not invent one.

**A directive that already rode the last handoff does not leave this list in
silence.** For every directive this session inherited in the prompt it opened
with, do one of three things and say in one line which: carry it forward here,
where it still binds; record it where it belongs, as a card or as a line in
the design document, where it has become part of the plan or the product; or
strike it, where the session carried it out or the operator withdrew it.
Dropping it without a word is not one of the three, and neither is deciding
that a directive you did not hear the operator speak was never yours.

## 6. Learned this session

The significant, durable discoveries — facts about the system that hold
beyond this task and are worth carrying forward: a non-obvious behavior, a
confirmed mechanism, a measured result, a corrected misconception. The
test is durability: if the insight would matter to someone who is NOT
doing this exact task, it belongs here. Contrast with §4 — §4's
constraints and dead-ends exist to stop the fresh chat repeating this
session's mistakes; §6 is knowledge that stands on its own. State each
learning specifically enough to act on, and say where it was verified — a
probe, a query, a measurement (~/.claude/CLAUDE.md rule 1). The splitting
rule from §4 applies here too: what you measured and what you concluded
from it are two entries, tagged separately. If nothing rose to
"significant," write `None`.

## 7. Credentials and test access

The test credentials and access details the operator handed over this
session, so the fresh chat can reach the same systems without asking
again: test logins, sandbox API keys, a sample account id, the
environment they belong to. Capture the literal values — these are
throwaway test credentials, and the continuation prompt's whole purpose is
to be self-contained (§13). Note which environment each credential is for
and what it unlocks. If the operator handed over no credentials, write
`None` here — and then leave the whole credentials heading OUT of the
prompt in §13. An empty section in the prompt costs the reader a heading
and tells them nothing.

## 8. Next steps (ordered, next action first)

The remaining plan, ordered by execution sequence, not importance. The
first item is the single concrete next action the fresh chat should
take. If a step depends on an open question in §10, name the dependency.

The first step also says what to re-check before acting on it. Time passes
between writing this prompt and reading it, and a background agent, a
running server, a branch, or a teammate's push can move underneath it.
Name the specific thing that could have changed and the command that
settles it — not "confirm state," but "run `<command>`; the handoff
assumed `<X>`, act only if that still holds."

**The operator's instruction for the next session is the first step.** Where
§11 says what the next session should do, step 1 is that instruction in the
operator's words. Only the re-check above runs before it: no owed work, no
review, and no re-measurement. Where it asks for a conversation, such as "let's
discuss", "I want to understand where we are", or "wait for my feedback", step 1
tells the fresh chat to say where things stand and what is left, and then to
stop and wait for the operator. List the work this session would have scheduled
as what is left, for the operator to decide on, and do not file cards for it
first, even where the phase has ended: the conversation decides what happens to
that list.

**Nothing here declares a stage of the work finished.** This template sees one
session, not the checklist the work is running against, so a sentence saying a
stage is over is a claim it cannot check — and the fresh chat reads it as
settled and never looks again.

A step that builds something the operator approved points to that decision in
§4, or to the file that holds it, and does not restate it.

Where a skill handed off to this one, it says which step it was on and what
that step still owes. Put that right after the operator's instruction above,
owed work ahead of new work, in the words it used. Where nothing said, write
that nothing did, and let the fresh chat find out rather than assume.

**Owed work belongs to the phase that owes it, and a finished phase files it in
the backlog rather than handing it to the next session.** The paragraph above is
for a step the next session is still inside. Where the phase that owed the work
has ended — the build is over, the demo is given, the findings are signed off —
create the card before you generate the prompt, and name that card here instead
of writing the work in as a numbered step. A numbered step is the first thing the
next session does, and it does that inside a template written for a different
phase, so the session handed the new phase spends its budget finishing the old
one.

**And no sentence says what the product can do unless a command showed it.**
"A person can play a whole turn with the mouse" is the same unchecked claim as
"the demo is over", and it reads worse: the fresh chat takes it as the ground it
is standing on and spends the session confirming rather than testing. So every
capability sentence carries the command that demonstrated it and what that
command printed, or it comes out. Closed cards, a passing suite and a green gate
are what you can write instead, because those are what you ran.

## 9. Pointers (paths, links, skills, commands, environment)

The lookup table that saves the fresh chat from rediscovering what you
already found. These are exactly the "oh, also remember to..." items —
enumerate them HERE, not after the prompt:

- Paths, each with the greppable identifier inside it that the work turns on
  — a function name, a heading, a constant, a quoted phrase. Never a line
  number: it is wrong the next time anybody edits that file, and it stays
  confidently wrong. Take these from what this session actually opened rather
  than re-opening files to confirm them. A path you are recalling, that nothing
  this session touched, is a guess — mark it `hypothesis:` and let the fresh
  chat find out.
- Links — PR, ticket / Trello, design doc, the relevant chat.
- Skills the fresh chat should load first, by name, and why.
- Setup to reach a working state — workspace dir, `eval "$(direnv export bash)"`,
  test command, dev-server port.
- Which environment / workspace, and any secret/env switch in effect.

## 10. Open questions / blockers

Anything unresolved that needs an operator decision before or during the
next steps. If there are none, write `None`. Do not invent decisions; do
not bury a real blocker inside §8.

**A question that already rode the last handoff leaves this list.** For every
question this session inherited in the prompt it opened with, and is about to
send on unanswered, do one of three things: file it as a card, so the backlog
holds it and a session can be scheduled to answer it; write the answer into
the design document that should have held it, where the session settled the
question and nobody recorded it; or strike it, where nobody needs it answered.
Carrying it a third time is not one of the three. A question copied forward
reads as though someone is tracking it, when no card holds it and no session
owns answering it, and every fresh chat pays to read it again.

**A decision that lives only in handoffs is an open question.** Where §4
carries something the operator approved and no design document in the project
holds it yet, list it here: what was approved, when, and that the project's
design documents do not hold it. Use the project's own name for those
documents, whatever that is ("the spec" and `docs/spec/` in one repository,
"the design docs" in another). The three outcomes above then apply to it, so
the next session either writes it in, files a card for it, or strikes it.

## 11. The operator's last words, verbatim

The operator's final turn before the clear, quoted exactly — all of it, in a
block quote, with its timestamp. Not a summary, not the half that looked
relevant to the next steps, and not your reading of what they were asking for.
If they wrote three paragraphs, all three go here.

**Words the operator typed after `/clear-task` are that final turn.** Where the
line that invoked this skill carries text after the command, quote that text,
not the turn before it. Operators use those words to say what the next session
does first, as in "and we'll discuss how we can wrap this up" or "wait for me
to give my feedback", and §8's first step carries it out. Where the invocation
carries no text, the final turn is the one before it.

Quote it even where §5 and §8 already carry what it said. The duplication is
the point: a directive rewritten as a next step has been through your judgment
about what it asked for, and this is the copy that has not.

**A quote that rode the last handoff stays until a session does what it
asked.** Where nobody typed anything this session beyond the pasted handoff, as
with a `session-loop` worker handing off on its own budget, carry the last
handoff's quote forward word for word, with its original timestamp, and say
that it is inherited. Once
a session has done what the quote asked, that session strikes it in one line
naming what it did. Write `None` only where this session has no final turn and
the prompt it opened with carried no quote. Then leave the heading out of the
prompt in §13, the way §7 works.

Treat this section as the second lock rather than the only one. The first is
§5's rule about directives this session inherited.

## 12. Completeness gate (the frontloading forcing function)

Before writing the prompt, interrogate §1–§11 out loud. Answer each:

- If the fresh chat read only §1–§11, what would it still get wrong or
  have to ask?
- What did this session try that failed, that §4 does not yet name?
- What rule or preference did the operator state that §5 does not yet
  capture?
- What significant, durable thing did this session learn that §6 does not
  yet record?
- What credential or test access did the operator hand over that §7 does
  not yet list, that the next action in §8 needs?
- What path, link, command, or skill does §9 not yet list that the next
  action in §8 needs?
- What "obvious to me right now" fact is implicit and would be invisible
  after /clear?
- Which claim in §4 or §6 is an explanation I never measured, still
  sitting there untagged or riding on a neighbouring `verified`? Read every
  "because", "so", "due to", "caused by", "which is why" in those two
  sections: each one starts a claim of its own. Split it out and mark it
  `hypothesis:`.
- Which reference anywhere in §1–§11 names a line rather than something the
  reader can grep for? Rewrite each one as the identifier sitting at that line.
- What could change between now and when this prompt is read, that §8's
  first step does not tell the reader to re-check?
- Is §11 the operator's final turn word for word, or a version of it I
  shortened, tidied, or cut to the part I thought mattered?
- Did the line that invoked this skill carry words after `/clear-task`? Is
  that the text §11 quotes, and does the block carry it under its own heading?
- Is §8's first step what §11 asks for? Name anything placed ahead of it, and
  move it behind that step or into the list of what is left.
- Does the artifact I am about to emit match what §0 settled?
- Going through the prompt this session opened with, item by item: which of
  its decisions, directives, and questions have I carried, recorded, or
  struck, and which have I dropped or shortened? Write the list out. Compare
  each line against the inherited text, not against your memory of it.
- Which term in §1–§11 did a session coin, a word the operator never used for
  the thing it names? Each one gets a plain definition at its first appearance
  in this response and again at its first appearance in the block, because
  both are output the operator reads. Or replace the term with the plain words.

Every gap found here is integrated into the relevant section above —
§1–§11 — NOT appended to the prompt. Proceed to §13 only when this
interrogation surfaces nothing new.

Write §0 through §12 as thirteen separate headings, in order, every time.
Do not merge neighbours into a combined heading such as "8–10" or "9–11",
and never skip §12.

Each section holds its own content. A section whose body only points at the
block ("they are in the block below") has been skipped under its own heading:
§12 has nothing there to check, and the block is then written from nothing
§1–§11 hold. Where a section is genuinely empty, write `None`.

## 13. The continuation prompt (terminal output)

A single fenced code block, assembled from §1–§11, written in plain
English for the reader — a fresh AI plus the operator (~/.claude/CLAUDE.md
"Communication Style"). It is the LAST thing in your response: no prose,
no postscript, no "let me know if..." after it.

Where §0 settled that a worker reads this next, this same assembled text goes
to that file and the path and line count take the block's place as the last
thing in the response. See "Stop" below. Nothing else about this section
changes. Every line in the prompt must trace to a consideration already written
above; if while assembling it you reach for something not in §1–§11, STOP —
that is a §12 miss. Return to the relevant section, add it, regenerate the
whole block.

Shape:

```
We are continuing work on <objective + definition of done>.

The operator's last words are below, word for word. Do what they ask before
anything else in this prompt, running only step 1's re-check first. Treat every
line marked verified as settled, and do not re-measure it:
<from §11 — omit this heading entirely if §11 is None>

Where things stand:
<verified state + completed work; verified vs unverified marked>

Watch out for (decisions already made — do not relitigate; dead-ends
already tried — do not repeat). Each line keeps the tag it carries in §4;
anything marked `hypothesis:` is unmeasured — reproduce it before you
build on it:
<from §4, tags intact>

Operating principles the operator set (follow these over your own
instincts):
<from §5>

Learned this session (tags intact — `verified` names the probe,
`hypothesis:` does not):
<from §6>

Credentials / test access (paste literal values):
<from §7 — omit this heading entirely if §7 is None>

Next steps, in order:
1. <next concrete action, and what to re-check first in case it moved>
2. ...

Pointers:
- Paths: <path, and the identifier to grep for inside it>
- Links: <PR / ticket / doc>
- Load these skills first: <names>
- Setup: <cd ...; direnv; test/dev command; port; env>

Open questions for you:
<from §10, or "None">
```

Use real values, not placeholders. The block must be self-contained —
the fresh chat must not need this conversation. Nothing follows it.

## Stop — the prompt is the terminal artifact

This template produces text and nothing else. It does NOT run /clear, does
NOT begin executing the next steps, and does NOT write the prompt to a file
unless §0 settled that a worker reads it next, or the operator explicitly
asks. The operator copies the block and starts the new chat.

**A written handoff is a document, not a stop signal.** The stop above is the
template's, and it says only that the template does not start the next steps on
its own. When a session has written its handoff and is still under the ceiling,
it has not lost the right to keep working if the operator asks it to; it
rewrites the prompt when it does stop.

**Where §0 settled on a worker, the artifact is that file.** Print no block
beside it. Write §1-§11 exactly as always, then write the assembled prompt to
`HANDOFF.md`, and report the path and its line count in place of printing the
block. Everything else holds: considerations first, one artifact, nothing after
it.

**Writing the file costs exactly one more turn, and that turn is the whole
report.** A tool call ends the response that makes it, so a session that writes
`HANDOFF.md` always gets one turn after the write and cannot decline it. That
turn carries the path and the line count and nothing else: no recap of the
sections, no summary of what the handoff says, no reprint of its text. The run
ends there: take no further turn of your own. If the operator types something
after it, that is a new instruction, and the paragraph above on a handoff not
being a stop signal is what governs it.

**A stale `HANDOFF.md` lying in the repository decides nothing.** A leftover
is a reason to delete that file, never a reason to write over it, and §0 is
what says whether anyone is coming for it.

The argument for the template's shape, and the measured cases behind the rules
in §0, §2, §4, §5, §8, §10, §11, §12, and this section, are in
[references/measurements.md](references/measurements.md).

## Notes on what this template does NOT do

- Does not run /clear or start a new session — that is the operator's
  manual step.
- Does not begin the next steps; it only describes them.
- Does not write, commit, push, or post anything, save the one
  `HANDOFF.md` that §0 calls for and the backlog card §8 requires for
  a finished phase's owed work. No destructive action either way.
- Does not append anything after the prompt code block. A late
  consideration is a §12 miss, fixed by regenerating the block — never by a
  postscript.
- Does not take a second turn after writing `HANDOFF.md`. The tool call forces
  one turn, that turn reports the path and the line count, and the run ends on
  it.
- Does not fabricate completed work: a claim with no backing line in §2 is
  labelled `unverified` (~/.claude/CLAUDE.md rule 1).
- Does not hand a diagnosis to the fresh chat as a measurement. An
  explanation you did not measure goes across as `hypothesis:`, separate
  from the reading it explains, in §4 and §6 alike.
- Does not merge or drop sections. Thirteen headings before the block, in
  order, §0 and §12 included.
- Does not print an empty section. A `None` in §7 means the credentials
  heading does not appear in the prompt at all.
- Does not chain to any other skill. It emits the artifact and stops,
  `session-loop` included — that skill resumes on its own.
