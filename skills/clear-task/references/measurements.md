# clear-task — the argument and the measured cases behind its rules

The skill body states each rule. This file holds the run that prompted it, and
the argument where no single run did, for a reader who disputes one.

- The template's shape
- The reason behind each rule, section by section
- §0 — the opening prompt settles the reader, not `pgrep`
- §2 — why a re-run costs so much here
- §4 — an approved decision shrinks when a next step restates it
- §5 — an inherited directive lasted one handoff
- §8 — a stage declared over, owed work, and an unchecked capability
- §10 — a question carried forward with nobody owning it
- §11 — the operator's last words
- §12 — a coined term, and sections that point at the block
- Stop — a written handoff is not a stop signal
- Stop — the forced turn after writing `HANDOFF.md`

## The template's shape

Tokens are generated left to right, so once you start writing the prompt you
cannot revise its earlier lines. A consideration that surfaces mid-prompt gets
tacked on as a postscript after the code block, where the operator, who copies
only the block, never sees it. The ordered sections fix that structurally, and
the skill follows the rule it teaches: all considerations come before the
artifact, and the artifact is terminal. §12 is where remembering is supposed to
happen, before the prompt is committed, and the tail sections are the ones the
momentum of a long session eats first, which is why §12 is never skipped.

§2 and §3 stay apart because your memory of what the session did is narrative
and §2 is the measurement. Conflating them is the same error as citing a design
document for a runtime claim (`~/.claude/CLAUDE.md` rule 11).

A worker gets the file and no block beside it because the driver hands the file
to every fresh session and nobody copies anything. A printed block would be a
second copy going stale from the moment it appeared.

## The reason behind each rule, section by section

- §0: a worker has no other way to receive a prompt, so it gets the file; the
  operator copies a block, so they get the block. `pgrep` asks whether any
  driver is alive anywhere on the machine, and the question is whether a
  worker is waiting on *this* session's handoff.
- §1: a handoff that named MBG-108 where the task was MBG-106 sent the next
  session to the wrong card. "Mentioned, not ours" stops the next session
  mistaking a neighbouring card for the work.
- §2: the state moves between writing the prompt and reading it, so a re-run
  buys the reader nothing (see "§2 — why a re-run costs so much here" for the
  cost). A "done" claim with no output behind it is `~/.claude/CLAUDE.md` rule
  1, "Verify before claiming".
- §4: dead-ends are the highest-value, most-forgotten content; without them
  the fresh chat repeats the same failed attempt. A constraint, a diagnosis, or
  a reason a thing failed is a claim the fresh chat acts on without re-deriving
  it, which is why each carries a tag. One `verified` covering a reading and
  its diagnosis launders the diagnosis into a measurement, and the fresh chat
  builds on it and finds out the hard way: that is `~/.claude/CLAUDE.md` rules
  4 and 10 applied to the handoff. A ban written against a class of evidence
  gets obeyed in cases the failure never covered. §8 gets reordered and
  rewritten every session, so an approval that lives there shrinks with each
  rewrite. A shorter restatement of an inherited decision drops whatever it
  left out, and nobody notices.
- §5: the operator's principles are meant to outrank the fresh chat's own
  instincts, so they survive the clear verbatim. Naming the behavior rather
  than a label is `~/.claude/CLAUDE.md` "Communication Style".
- §6: §4's constraints and dead-ends exist to stop the fresh chat repeating
  this session's mistakes; §6 is knowledge that stands on its own.
- §7: these are throwaway test credentials, and the prompt's whole purpose is
  to be self-contained. An empty section in the prompt costs the reader a
  heading and tells them nothing.
- §8: time passes between writing the prompt and reading it, which is why step
  1 names a re-check. A "not yet" or "hold off" in the middle of a discussion
  can mean "not before we finish talking". A sentence saying a stage is over is
  a claim the template cannot check, and the fresh chat reads it as settled and
  never looks again. A numbered step is the first thing the next session does,
  inside a template written for a different phase, so the session handed the
  new phase spends its budget finishing the old one. "A person can play a whole
  turn with the mouse" is the same unchecked claim as "the demo is over", and
  it reads worse: the fresh chat takes it as the ground it stands on and spends
  the session confirming rather than testing. A line number is wrong the next
  time anybody edits the file, and it stays confidently wrong.
- §10: a question copied forward reads as though someone is tracking it, when
  no card holds it and no session owns answering it, and every fresh chat pays
  to read it again. A paraphrase such as "stays recorded" turns a dismissal
  into an obligation the next writer keeps alive.
- §11: a directive rewritten as a next step has been through your judgment
  about what it asked for, and the quote is the copy that has not. §11 is the
  second lock rather than the only one; the first is §5's rule about inherited
  directives.
- §12: a section that only points at the block leaves §12 nothing to check
  there, and the block is then written from nothing §1–§11 hold.
- Stop: a tool call ends the response that makes it, so a session that writes
  `HANDOFF.md` always gets one turn after the write and cannot decline it.

## §0 — the opening prompt settles the reader, not `pgrep`

The `pgrep` check and the question §0 asks come apart whenever a loop runs
against one repository while you work in another. The opening prompt settles
it because nobody retypes it, and it is the text the driver itself wrote.

On 2026-09-17, `pgrep -af run-loop.sh` matched a driver on `ansimation-editor`
while the session asking the question was an interactive one in a different
directory, whose only reachable `HANDOFF.md` belonged to the loop that was
mid-run.

Across 183 runs of this skill, 59 of the 64 sessions a driver launched wrote the
file, against 19 of the 119 interactive ones. Five runs wrote it and then
deleted it again.

## §2 — why a re-run costs so much here

This skill fires at the fullest point of a session: measured at a median of
187,000 tokens of context already loaded, where one more turn re-reads all of
it. The turns beyond the first account for 61% of what this skill costs.

## §4 — an approved decision shrinks when a next step restates it

On 2026-09-22 the operator approved a report design at 11:25 in session
`8659b2ef` of `mbc-brokeragecollateral`: "I'm going to ok this version of it
for now." Each of the next four handoffs held the design only as sub-bullets of
a "build the HTML report generator" step in §8 and the block, never in §4 or §5.
The handoffs dropped "roll-up" at the first of them, "tooltip" at the second,
and "status word" at the fourth, although §5's rule about inherited directives
fired in every one. `docs/spec/` never held the design. At 14:27 the operator
wrote: "It seems like you've lost that original design. But it's in our
history."

## §5 — an inherited directive lasted one handoff

The operator typed "let's undo that commit" at 08:51. The handoff written at
08:54 carried those words, the handoffs written at 09:12 and 09:32 did not
mention them, and the commit is still in the log. Nobody undid it, and nobody
told the operator it had not been undone.

## §8 — a stage declared over, owed work, and an unchecked capability

A handoff written five minutes after the operator asked for research before
the current stage ended opened its next steps with "the demo is over and its
feedback is recorded". The session that read it went straight on to the
following stage.

A retro handoff opened with "Run `quick-review` and then `security-review` over
plan/demo/s5/drive-demo.js ... This is owed work from the demo, ahead of
anything new". The session that read it spent 21 of its 31 turns on that
review, about two thirds of its cost, before it loaded `retro-task` at turn 24.

A handoff opened "A person can launch the game and play a whole turn with the
mouse and keyboard". Someone wrote it the evening before the operator opened
that game and found that no press reached a battalion.

On 2026-09-23 the tenth handoff in `mbc-brokeragecollateral` (session
`82477098`) put the operator's request to discuss at step 5, behind three items
it called owed: integration mutations, a review write-up, and a spec paragraph.
It gave the reason as work "owed after the recording ends" in the prior
handoff. The session that read it ran those steps and never opened the
conversation.

A question answered in the handoff's own response was treated as closed. The
operator's final turn asked whether a reworded commit changed a proposal for a
skill, said "We aren't going to update git-commit yet", and invoked
`/clear-task` in the same message. The handoff answered the question, recorded
the skill work as "deferred by the operator", and told the next session the
question was "already answered". The next session opened on the project's
status, and the operator had to say they were still discussing the skill.

## §10 — a question carried forward with nobody owning it

"Whether weapons stay in the game" appears in 29 of one project's transcripts,
and its backlog holds no card for it.

The operator's "no" never became a strike. They said a session was "overly
concerned about the failures at this stage", and the next handoff recorded
three deferred problems as staying "recorded and unfixed". The §10 rule then
made them an open question. Asked whether to add them to the spec, the operator
answered "(Not interested in adding the problems.)". The next handoff recorded
only "stay out of the spec" and asked whether to file a Jira ticket instead.
Mentions of the problems in five consecutive opening handoffs ran 2, 3, 5, 8,
and 8.

## §11 — the operator's last words

The operator asked for this section: "This isn't the first time I've seen my
final prompt be lost, so maybe it deserves a word-for-word section in
clear-task final output." On that run their final turn had in fact been
carried across, and the next session read past it anyway.

Across every transcript under `~/.claude/projects` on 2026-09-23, 41 of 46
`/clear-task` invocations carried words after the command, such as "and we will
pick up where we left off" and "after we clear and come back in, wait for me to
give my feedback". The first 40 characters of those words reached the finished
block in 3 of the 41.

At 13:40 UTC that day, in session `82477098` of `mbc-brokeragecollateral`, the
operator typed `/clear-task` followed by "and we'll discuss how we can wrap this
up. I think we have reached a "good enough" point for now. My goal is to have
this ready for someone else to run, and I want to understand where we currently
are and what we still need to do. I want to approve it." The handoff quoted an
earlier turn as the last words, mentioned these only in a parenthetical, and
printed a block without the last-words heading. The next session, `71d03ac4`,
had no operator turn beyond the paste and wrote §11 as "None of their own". At
14:25 UTC, in the session after that, the operator wrote: "I don't understand
why I just went through a cycle and a half of additional work here".

## §12 — a coined term, and sections that point at the block

On 2026-09-22 a session coined "cassette" for the file of recorded OpenAI
responses. It first showed the operator the word at 12:33 local time, with no
definition: "Before designing the cassette key, one boundary claim needs
measuring". The next three handoffs used it without defining it, until the
operator asked at 14:13: "Somewhere along the line this term "casette" was
introduced. What is that?"

The handoff from session `e3b5deb5` reduced §6 through §11 to pointers such as
"§9 Pointers: They are in the block below."

## Stop — a written handoff is not a stop signal

A supervising session at about 157,000 of 170,000 declined to open a signoff
gate at 10:46 because it had written its handoff, and the operator overrode it
at 13:32.

## Stop — the forced turn after writing `HANDOFF.md`

Nobody is waiting for a recap in that turn. A driver sends the session's whole
output to a log file (grep `RUN_LOG` in `session-loop/scripts/run-loop.sh`),
and the summary that reads the log back takes `terminal_reason`, `num_turns`,
`permission_denials`, and `is_error` out of it, never the assistant's text.

Across 187 runs of this skill on 2026-09-17, all 164 responses that wrote the
file ended on the tool call, so every one of them forced a turn. Those forced
turns ran to a median of 2,281 characters against the one line they owed, and
cost $18.13. Eleven runs then took a further turn beyond the forced one, writing
a median of 27,831 characters each — the whole handoff again, beside the copy
already on disk — for another $3.99. Together that is 10.2% of what this skill
costs.

A retrospective session recommended writing the file for its own clear, having
argued that a block alone would leave the stale one as a trap. The operator
overrode it by typing `/clear-task instead`.
