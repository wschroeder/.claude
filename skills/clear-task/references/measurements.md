# clear-task — the measured cases behind its rules

The skill body states each rule. This file holds the run that prompted it, for
a reader who disputes one.

## §0 — the opening prompt settles the reader, not `pgrep`

On 2026-09-17, `pgrep -af run-loop.sh` matched a driver on `ansimation-editor`
while the session asking the question was an interactive one in a different
directory, whose only reachable `HANDOFF.md` belonged to the loop that was
mid-run.

Across 183 runs of this skill, 59 of the 64 sessions a driver launched wrote the
file, against 19 of the 119 interactive ones. Five runs wrote it and then
deleted it again.

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

## §10 — a question carried forward with nobody owning it

"Whether weapons stay in the game" appears in 29 of one project's transcripts,
and its backlog holds no card for it.

## §11 — the operator's last words

The operator asked for this section: "This isn't the first time I've seen my
final prompt be lost, so maybe it deserves a word-for-word section in
clear-task final output." On that run their final turn had in fact been
carried across, and the next session read past it anyway.

## §12 — a coined term, and sections that point at the block

On 2026-09-22 a session coined "cassette" for the file of recorded OpenAI
responses. It first showed the operator the word at 12:33 local time, with no
definition: "Before designing the cassette key, one boundary claim needs
measuring". The next three handoffs used it without defining it, until the
operator asked at 14:13: "Somewhere along the line this term "casette" was
introduced. What is that?"

The handoff from session `e3b5deb5` reduced §6 through §11 to pointers such as
"§9 Pointers: They are in the block below."

## Stop — the forced turn after writing `HANDOFF.md`

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
