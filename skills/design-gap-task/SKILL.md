---
name: design-gap-task
description: Manual-invoke template — produces a filtered report of product-level gaps in a design document set, using an entity-lifecycle inventory plus cross-cutting coverage sweeps, with a review/filter checkpoint applied before candidates reach the final report. Do not auto-activate; invoke explicitly only.
---

# design-gap-task — find gaps by entity lifecycle and by coverage sweep, then filter as you go

For the design-doc directory in $ARGUMENTS, respond with the sections
below in order. If $ARGUMENTS is empty, look for it — a single
unambiguous design-doc directory found this way (state what you found
and how) counts as stating the directory, not guessing a path. If more
than one plausible directory exists, or none do, stop and ask the
operator instead of picking one yourself. The deliverable is the report
in Section 5. This template never writes to any file; see Section 6.

The output discipline is structural, not stylistic: Section 2's entity
list has to be real because Section 3 runs its lifecycle check against
each entry in it; Section 3's slot content has to be real because the
consumer-without-producer flag only means something if both the effect
side and the producer side were actually searched for; Section 4's
sweeps have to enumerate real rules and real boundaries because a
half-filled coverage matrix reads as "covered" exactly where it isn't;
the filter checkpoint in Section 3(d) can only keep or drop candidates
that Sections 3 and 4 actually produced; and Section 5's Evidence-block
format forces every surviving finding back to a real file:line, which
is what exposes a faked upstream section. Each direction constrains the
other.

Two complementary methods run here, because they catch different gaps.
The per-entity lifecycle loop (Sections 2–3) catches a gap that lives
inside one entity — created but never removed, removed with a downstream
effect but no trigger. The cross-cutting sweeps (Section 4) catch a gap
that lives in the *cross-product* of two or more systems and belongs to
no single entity's lifecycle: a rule that sorts units into who-qualifies
without covering every case, or a boundary of the play space that some
mechanic can reach with no stated result. A run that does only the
per-entity loop asymptotes at "a couple left" and never reaches a
defensible stop, because its frame structurally under-samples
interactions — the sweeps are what let the count actually close.

## 1. Setup

State the design-doc directory and enumerate it for real:

```
$ find <dir> -maxdepth 1 -name '*.md' | sort
<actual output>
```

## 2. Entity Inventory

Real output, not paraphrased. Read every file from Section 1. List
every noun the docs treat as a first-class *thing* — something that
exists, gets created, changes state, or is removed — not a *system* or
*mechanic*. A system is a rule (how combat resolves, how a queue
drains); an entity is what the rule acts on (a battalion, a commander,
a user session, a subscription — whatever this design's own nouns are).

For each entity:

```
<entity name> — first introduced <file>:<line>, "<exact quoted phrase>"
```

An entity mentioned only as flavor text, never independently created,
put at risk, or removed anywhere in the set — verified with a real grep
across every file, not a guess — doesn't belong on the list. Note it
and the grep that ruled it out anyway; a wrong exclusion here is the
same near-miss that hid a real gap in this project before.

## 3. Per-Entity Micro-Loop (repeat for every entity in Section 2)

Take each entity through all four steps below before moving to the next
entity. Do not run step (a) for every entity first and the filter in
step (d) afterward as one big batch at the end — the filter runs on
each entity's own candidates while they're still fresh.

**(a) Lifecycle check.** Fill six slots with real grep/Read output,
quoted with its location, or mark the slot UNSPECIFIED together with
the search that came up empty (a slot is only UNSPECIFIED if something
was actually searched for):
  - Representation — its own first-class thing, or embedded inside a
    different entity from Section 2?
  - Cardinality — how many exist, and what decides that count?
  - Acquisition — built, purchased, free, or bundled? Mark N/A only
    after confirming the concept doesn't apply here, not by skipping it.
  - Risk exposure — what can degrade or endanger it in normal operation?
  - Removal trigger — the SPECIFIC event that ends it or changes its
    state. "It dies" is not an answer to this slot; "condition X,
    defined at file:line, causes it to die" is.
  - Downstream effect — what changes elsewhere when the trigger fires?

**(b) Consumer-without-producer flag.** If downstream effect has real
content but removal trigger is UNSPECIFIED, that's a raw candidate.
Grep every place the entity's past-tense/result form is used as a
precondition elsewhere in the set, and quote the hit count. A high
count on the effect side with zero on the trigger side is not evidence
the trigger is defined somewhere unindexed — it's the gap.

**(c) Second look.** Before advancing, re-read the passage(s) cited in
(a) and (b) once more, hunting specifically for a second, different gap
in the same text. State either the second finding or "re-scanned,
nothing further" — a passage that already produced one finding is not
used up.

**(d) Filter checkpoint — on this entity's candidates only, now, before
the next entity.** For each candidate from (b) and (c), check all four
and log the result even when it's a drop:
  - Re-verified absence with a second, differently-worded grep — a
    single miss doesn't prove nothing exists (CLAUDE.md rule 1).
  - Product/mechanism-level, not a numeric or tunable parameter this
    doc set already defers on purpose — check for that set's own
    deferral convention before flagging.
  - Not a restatement of a candidate already logged for a different
    entity this run.
  - The effect side actually presupposes this specific missing cause,
    not just sits near it — a suspected gap is a hypothesis to verify,
    not a conclusion to report (CLAUDE.md rules 7–8).
  Any No → "considered and dropped," with the one-line reason, logged
  rather than deleted. All Yes → survives to Section 5.

## 4. Cross-Cutting Coverage Sweeps (run once, across the whole set, after Section 3)

These two sweeps run once over the entire doc set, not per entity —
their subject is the interaction *between* systems, which is why the
per-entity loop can come back clean while the gap is still there. Each
sweep is a coverage matrix: enumerate the cells, then fill every one
with either a specifying file:line or an explicit-deferral file:line. A
cell you can fill neither way is a raw candidate. Run each raw candidate
through the same four-check filter as Section 3(d) — re-verify the
absence with a second grep, confirm it's mechanism-level and not a
deferred tunable, confirm it isn't a restatement, confirm the effect
side really presupposes the missing rule — and send survivors to
Section 5 alongside the per-entity findings.

This section exists because the two gaps that outlived this design's
later reviews were both here, not in any entity's lifecycle: a partition
that sorted who screens a charged artillery battery into "a Ready
infantry/cavalry battalion" versus "nobody at all," silent on a friendly
battery or a stopped-but-shaken battalion standing in the same lane; and
a boundary — the map's own edge — that ordered movement, a routing
block's flee vector, and the cornered check could all reach with no
stated result. Neither is a "created but never removed" gap. Both are
cells in the matrices below.

**(A) Partition-totality sweep.** Grep the set for every rule that gates
a role, effect, or eligibility on what a thing *is* or *what state it's
in* — the giveaway verbs are `counts as | doesn't count | qualifies |
eligible | can only | may only | only <X> can | requires being | must be
| isn't counted`. For each hit, name the attribute it partitions on (the
arm? the morale state? the formation? the unit type?), list every value
that attribute can take from the docs' own vocabulary, and confirm the
rule states an outcome for *each* value — not just the values that
qualify plus a single "otherwise nothing." The failure mode to hunt is a
rule that enumerates who's in and pairs it with only the empty negative
("if none is present…"), while a thing that *is* present but doesn't
qualify — a not-A standing exactly where the rule looks — falls through
with no defined outcome. A total partition names all three: qualifies,
present-but-doesn't-qualify, absent.

**(B) State-combination and boundary sweep.** Two cross-products the
per-entity loop never lays out:
  - *State combinations.* For each entity that can hold more than one
    state or condition at once, enumerate its states from the docs (for
    the design that seeded this skill, a block could be some mix of
    Ready / Forming / Disordered / Shaken-Rallying / Routed / Eliminated
    / Cornered / garrisoning / skirmishing / hosting-a-commander /
    over-capacity). For each pair that can legally co-occur, confirm the
    docs either specify the combined behavior or rule the pairing out.
    The gap is a legal combination whose behavior nobody stated — e.g.
    does a Cornered host still project its commander's bonus? does a gate
    keyed on "Shaken/Rallying or Routed" mean to include or exclude
    Forming and Disordered? Trace it to an existing mechanism before
    flagging: a combination often resolves through a factor already in a
    formula (a disordered charge lands weakened because cohesion already
    scales the clash), and that's a close, not a gap.
  - *Boundaries.* Enumerate every boundary of the play space — the map's
    spatial edge, the turn's time limit, a vision or sight budget, a
    storage / point / count cap, a range cutoff — and cross each against
    every mechanic that can reach it (move, rout, charge run-up, flee
    vector, fire arc, order scheduling, purchase). The gap is a boundary
    a mechanic can hit with no stated result: a unit routed past the map
    edge, an order scheduled with no time left to finish, a purchase with
    no slot to land in.

When both sweeps' matrices are full — every cell a specifying or a
deferring file:line — that is what licenses a scoped, defensible stop:
no lifecycle gaps, no partition-totality gaps, no state/boundary gaps,
with the residual risk named as "a matrix missing a whole axis," which
is a small reviewable claim rather than an open-ended search. That
scoped closure is a real "no structural gaps found"; it does not speak
to tuning values the set defers on purpose or to whether the design is
fun, which belong to sweeps and playtesting, not a document review.

## 5. Findings Report

Present only candidates that survived the step-(d) filter — from a
per-entity micro-loop (Section 3) or a coverage sweep (Section 4) — in
the Evidence-block format `~/.claude/CLAUDE.md`'s Evidence Format section
requires for any project-specific claim: REFs first, one ref per claim,
`hypothesis:` prefix on anything asserting a specific reason a gap
exists rather than just that it exists. Write the prose per
`~/.claude/CLAUDE.md`'s Communication Style section — name the entity
or the interacting systems and the missing rule directly; don't invent a
compound-noun label for the gap itself. Include the full "considered and
dropped" log from every step (d) underneath — a reader should see what
got ruled out and why, not just what survived.

Every entity from Section 2, and every matrix cell from Section 4, lands
in exactly one of three places by the time this section is written: a
surviving finding above, a line in "considered and dropped," or — for an
entity or cell that never produced a candidate to filter — a one-line
"checked, no gap" note naming what closed it. An entity or a matrix axis
that appears upstream but nowhere here is an incomplete run, not a clean
pass: this skill exists because a design's commander-succession gap
survived three prior ad hoc reviews by hiding in exactly that silence,
and it survived this skill's own first real runs the same way — first a
lifecycle gap, then two interaction gaps the per-entity loop couldn't
see — before the added sweeps caught them.

## 6. Stop — this template writes nothing

The report in Section 5 is the entire deliverable. This skill never
writes an Open Questions heading, a note, or anything else into any
design doc. If the target doc set has its own convention for tracking
open items, applying it is an operator decision made afterward — this
template doesn't assume one and doesn't invoke one automatically.
Folding a confirmed gap into the docs is a separate, later,
explicitly-authorized action through ordinary discussion, per
`~/.claude/CLAUDE.md`'s Change → Review Workflow for anything beyond a
prose-only edit.

Once the report is delivered, this template's job is done, but that's
not a reason to stop and ask whether to keep going. Move straight into
resolving the findings in a sensible order — report order is fine —
without asking permission first; the operator has answered yes to that
every time it's come up. That doesn't touch the actual per-finding
decision: still lay out the tradeoffs, research them per the Probe
Before Build note above, and wait for the operator's answer before any
edit lands. It only skips the redundant question of whether to start.

## Notes on what this template does NOT do

- Does not write to any file — Section 5 is the entire deliverable.
- Does not research or resolve a flagged gap (no WebSearch, no
  precedent-gathering) — that happens afterward, in conversation, the
  same way this project's own commander-representation gap got
  resolved only after being flagged. When that afterward conversation
  does research a gap, `~/.claude/CLAUDE.md`'s Probe Before Build
  section still applies to it — a historical or precedent claim
  backing a recommended option needs a real search or citation behind
  it that session, not assumed general knowledge, whether it lands in
  prose or inside a tool call like AskUserQuestion.
- Does not delegate the inventory, lifecycle check, or coverage sweeps
  to a subagent — investigation is done directly, per
  `~/.claude/CLAUDE.md`'s Subagents section.
- Does not flag a numeric or tunable parameter the doc set already
  defers on purpose.
- Does not batch the per-entity filter to the end — Section 3(d) runs
  per entity. The Section 4 sweeps are the one deliberate exception:
  they run once across the whole set by nature, since their subject is
  cross-entity, and they filter their own candidates with the same four
  checks before the report.
- Does not chain to another task template automatically.
- Does not add auto-activation triggers to its own description.
