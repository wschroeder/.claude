# Why spec-task's rules say what they say

Each entry names a rule from SKILL.md, why it holds, and, where one exists, the
run that produced it. Entries sit under the heading of the SKILL.md section
that holds the rule.

## Contents

- [The design documents hold the product, and the cards hold the work](#the-design-documents-hold-the-product-and-the-cards-hold-the-work)
- [0. Before Section 1, read your own room](#0-before-section-1-read-your-own-room)
- [1. Setup, boundaries, and what "released" means here](#1-setup-boundaries-and-what-released-means-here)
- [2. Source lines from the design conversation](#2-source-lines-from-the-design-conversation)
- [3. Open questions — what the design does not settle](#3-open-questions--what-the-design-does-not-settle)
- [4. Requirements in EARS, each with the command that proves it](#4-requirements-in-ears-each-with-the-command-that-proves-it)
- [5. What this run writes, and where each piece lands](#5-what-this-run-writes-and-where-each-piece-lands)
- [6. Task breakdown and sizing](#6-task-breakdown-and-sizing)
- [8. Write the design document edits](#8-write-the-design-document-edits)
- [9. Review for gaps, and re-review until a round changes nothing](#9-review-for-gaps-and-re-review-until-a-round-changes-nothing)
- [10. Hand the backlog on](#10-hand-the-backlog-on)

## The design documents hold the product, and the cards hold the work

Rule: no slice, ticket or card in a design document.

Why: those describe a schedule, not the product. The tag saying the build
holds an element is the one exception, and it is deliberate.

Rule: when the conversation settles how the product behaves, write it into the
design document in this run.

Why: the conversation is the approval. The operator has just decided, and a
decision recorded anywhere else is one the next reader of the design will not
find.

Measured on one project: a blink rate, the rule for where Enter lands, and
twenty-six other behaviours sat in a plan file across six slices, because a
rule reading "correcting it is the operator's call" gave nobody a moment to
make the call in.

Rule: write only what the conversation has settled.

Measured: a session wrote a rule of its own and two new open questions into the
documents mid-design, and the operator replied, "Maybe we should finish
designing our solution here before slapping around text like that?"

Rule: the line is literal code.

Why: a source file, a function, a test, a stylesheet value, and a
configuration key change when somebody refactors, and the product does not.

Rule: design prose may not point at code, and a doc comment may point at a
design section.

Why: nobody renaming a function opens a design document, so a pointer from
the design into the code goes stale unnoticed. The argument in full is in
[two-documents.md](two-documents.md).

Rule: only the current slice is specified deeply.

Why: sketching ahead is cheap, and specifying ahead is not.

Rule: if a section fights the work, say so instead of skipping it.

Why: the template is new, and a section that fights the work is how it shows
where it is wrong.

## 0. Before Section 1, read your own room

Rule: if the session is past the ceiling that `session_budget.py` reports, hand
off before starting the template.

Why: a template is a session's worth of work, so a session that begins one
already over the line ends it far over, and every section it writes on the way
is written in a session that should have stopped.

Measured: a session printed "turn 72, context 231,229 of 170,000 — hand off",
quoted that line back in its own evidence block, created ten cards over the
next two hours, printed the same line again at 251,737, and ended at 263,205.

Rule: this is the only budget check in the template.

Why: planning a slice is where a session's context grows fastest, so the
question worth asking is whether to start, not whether to carry on.

Rule: if you stop partway, write the handoff through `clear-task` yourself
instead of recommending that the operator run it.

Measured: a session stopped before Section 9 with 51,592 of room, edited
HANDOFF.md by hand, and recommended `/clear-task`; the operator had to ask "Did
you write the handoff?"

## 1. Setup, boundaries, and what "released" means here

Rule: find the design documents and read them before cutting a slice.

Why: they describe the product this work changes, and a slice cut without them
specifies a product nobody described. Where none exist, the cards are the only
durable writing, which is worth reporting but does not stop the work.

Rule: do not restate the design documents' rules anywhere else.

Why: a copy is a second place for that rule to be wrong.

Rule: a definition of released taken from the handoff is not offered back for
the project.

Why: an operator working in a repository they do not own may keep it in the
handoff on purpose, and recording it in the project is theirs to raise.

Rule: a definition of released the operator gives you is offered as a
`project-definition-of-done` skill in the same turn.

Why: the next initiative in the repository then inherits it, and an offer
noted for later does not get made.

Rule: resize or split the sketch's slice if it no longer fits.

Why: the sketch was written before anything real existed to compare it
against, so it is a starting point rather than a decision.

Rule: one slice is one feature, and the sentence decides the cut.

Why: the operator has to be able to hold the slice in mind as one coherent
step of progress when they open the project. What it cost when a slice failed
this is in [slice-size.md](slice-size.md).

Rule: on a returning initiative, stop before Section 2's research, and keep
Section 3's questions out of the stop.

Why: nothing past this point has been written yet, which makes it the cheap
place to catch a wrong slice. Catching it after Sections 2 through 9 costs the
whole pass. Open questions brought into this stop reach the operator before
the check that would have answered some of them.

Rule: unattended, the stop is a `BLOCKED:` line in `HANDOFF.md`, written
through `clear-task`.

Why: inside a `session-loop` run nobody reads a question in the transcript.
Nothing has been written yet, so there is nothing to commit. The handoff point
is a budget rather than a limit, so being close to it is no reason to write
the file by hand.

Rule: open the ask with the phase line, directly above the question.

Measured: the operator asked "What phase are we in?" twice inside one planning
pass; the line was already in this template and nothing told anyone to print
it.

## 2. Source lines from the design conversation

Rule: the quote is the ref, not its location.

Why: a ref that only locates proves nothing about what was decided.

Rule: quote `grill-me`'s interview as the conversation.

Why: `grill-me` interviews and writes nothing, so its output exists only as
conversation.

Rule: before spawning anything to research a source line, load `subagents`,
and use a fresh agent rather than a fork.

Why: research is a job that can be written down, which makes it a fresh
agent's job.

Measured: one run of this template opened two forks side by side, never having
loaded the skill that forbids exactly that.

## 3. Open questions — what the design does not settle

Rule: if the slice's scope or a source line already settles a question, answer
it from that line instead of putting it to the operator.

Measured: a handoff listed "turning a battalion at deployment" among what the
slice leaves out and, further down, asked the operator whether a battalion may
turn at deployment.

Rule: research a question of fact yourself, and put only questions about how
the product should behave to the operator.

Measured: asked whether to check the recorded page readings for a case, the
operator replied, "things like that aren't real open questions; you can
research it based on what you've already done."

Rule: a question put to the operator quotes every fact you already found that
bears on it.

Why: then they never have to ask you for it.

Measured: a session found "firm names are free text today", then asked the
operator a question that left the fact out, and they replied, "We currently
don't track firms at all, right?"

Rule: each option says what the person will see and do, and an option that
keeps something from today says what it looks like on screen.

Why: a name for today's mechanism is opaque to someone who never read the
code, so they pick by the label and get the thing they turned down.

Measured: the operator called the common room's list "really poor", then chose
"At a table, same choice" over "Keep the list for now". The chosen option said
"using today's choose-and-confirm", which is the list, and the build kept the
list. At the demo the operator called it "a leftover thing".

Rule: stop and ask when an unanswered question would change the requirements.

Why: a missing precondition is a stop rather than a guess.

Rule: end the section by saying whether the operator has anything to answer.

Why: a section headed "open questions" that silently answers all of them
leaves the operator guessing whether their turn has come.

## 4. Requirements in EARS, each with the command that proves it

Rule: later requirements carry no `S<n>` tag.

Why: a fixed slice number invites treating the sketch as decided, which is
exactly what it is not.

Rule: anything the operator rejected gets a requirement saying it is gone,
with a proof that fails while it remains.

Why: a requirement that only names what is added can pass with the rejected
thing still on screen.

Measured: Rhen's requirement said he joins "by choose then confirm" and passed
with the common room list still opening, though the operator had chosen the
option that removed it.

Rule: no user stories in the requirement.

Why: "As a user I want…" states a wish, not a checkable condition.

Rule: read the count of tests a proof command ran, not its exit code.

Why: a command that runs nothing can still exit 0.

Rule: a requirement to compare the work against reference material carries a
proof that fails when no reference image is saved.

Measured: a card whose proof checked only that the captures were saved passed a
"comparison" that saw nothing but a list of page titles, and the demo found
pincers that looked like cat paws.

Rule: every slice ends in a requirement whose proof produces something a
person can look at and operate.

Why: a slice whose requirements are all internal modules cannot produce one,
which is the sign it was cut by layer rather than as a path through the system.

Rule: where a person operates the thing, one requirement is proved by the input
that person sends, written at planning.

Why: planning is the only place cheap enough. Every layer below it is satisfied
by a public method with the right name, and nothing downstream asks whether
anybody can reach it.

Measured: a slice built to let two players play a battle shipped eleven
requirements, not one of them proved by an input a person sends — the ones that
reached the planning screen called its own methods — and the operator's first
act was to open the game and find that no press reached it.

Rule: aim that input at the target as a person sees it, not at a coordinate the
code returns.

Why: where the target's position comes from the same module the assertion
reads, the requirement only shows the code agreeing with itself, and says
nothing about whether anybody can hit it.

Measured: seven requirements drove real presses into a running game, every one
of them at the centre the game's own layout function returned, and every one
passed over a battalion painted 51 pixels wide that answered a press over 3 of
them.

## 5. What this run writes, and where each piece lands

Rule: name a home for every design decision.

Why: a decision with no home named is a decision that will not be written.

Rule: design edits never mention a slice, a card, a source file, or this run.

Why: a reader a year from now cannot tell which conversation produced the
sentence, and does not need to.

Rule: no user-story list on disk.

Why: the stories are how Section 6 reports the work to the operator, and the
cards are how it is recorded.

Rule: a `stubbed` requirement names the slice that will replace it.

Why: then a deliberate fake in a walking skeleton cannot be mistaken for
finished work.

## 6. Task breakdown and sizing

Rule: Section 9's loop re-runs the coverage check on every round.

Why: a requirement that loop adds has never been through the check.

Rule: a sketched later task has no proof command.

Why: that is what makes it cheap.

Rule: when a task fits no story, say so.

Why: a task that fits no story is a module rather than a step toward something
a person can do.

Rule: print the stories in Section 6.

Why: `backlog-task` presents this same list when it asks for approval.

## 8. Write the design document edits

Rule: write the edits without asking, and do not stop.

Why: the conversation was the approval, and Section 9's loop revises the
documents in place.

Rule: write only what Section 5 printed.

Why: a sentence composed while editing is where the worst design changes come
from.

Rule: no status tag and no card id in a design document.

Why: neither belongs to the product, and both rot.

Rule: commit without asking.

Why: the standing permission in `git-commit` covers it.

Rule: if the directory is not tracked by git, stop.

Why: that is a precondition, not something to fix silently.

## 9. Review for gaps, and re-review until a round changes nothing

Rule: the review is a loop.

Why: one pass finds the gaps in the slice as first cut and none of the gaps its
own fixes introduce.

Rule: run `design-gap-task`, and then check the slice yourself.

Why: `design-gap-task` hunts for holes in a described product — a rule that
sorts things into categories without covering every case, an entity created and
never removed — and never reads the slice.

Rule: check each factual requirement against its cited source.

Why: the gap sweep looks for what is missing, and a requirement that is present
and wrong passes it untouched.

Rule: check each requirement against the design documents.

Why: a slice specifying behaviour the product was never designed to have will
be built and then argued about.

Rule: only an unsettled product question waits for the operator.

Why: it waits because nobody has decided yet, not because a template needs
permission.

Rule: re-enter at Section 4 rather than patching in place.

Why: the approval `backlog-task` asks for is on a list built from the
requirements as they now stand.

Rule: stop after a fourth round that still changes a requirement.

Why: step 3's routing of out-of-slice findings is what bounds the loop in the
ordinary case.

Rule: a round that only edits design documents does not start another.

Why: those edits change the product's description rather than the slice, and
the next round's `design-gap-task` reads them as they now stand.

Rule: the loop closes before any card exists.

Why: reviewing after the backlog is created means fixing the slice and the
cards both.

## 10. Hand the backlog on

Rule: load `backlog-task` with three things and nothing else.

Why: the slice is cut and the list is generated, and rebuilding either there
would specify something this run did not say.
