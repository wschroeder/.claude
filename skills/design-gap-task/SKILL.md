---
name: design-gap-task
description: Produces a filtered report of product-level gaps in a design document set, working from an inventory of each entity's lifecycle plus cross-cutting coverage sweeps, with a review checkpoint every candidate clears before it reaches the final report. Use when asked what is missing from a design, to find holes or gaps in a spec or design doc set, or to check a set of design documents for coverage.
---


# design-gap-task — find gaps by entity lifecycle and by coverage sweep, then filter as you go

1. For the design-doc directory in $ARGUMENTS, respond with the sections below in order.
2. If $ARGUMENTS is empty, look for it; a single unambiguous design-doc directory found this way, stated with how you found it, counts as stating the directory.
3. If more than one plausible directory exists, or none do, stop and ask the operator instead of picking one yourself.
4. Deliver the report in Section 5, and write to no file during the sweep; see Section 6.
5. Make each section real, because the next one runs against it: Section 3 checks each entity Section 2 lists, Section 3(d) filters only what Sections 3 and 4 produced, and Section 5's Evidence block forces every surviving finding back to a real file:line.
6. Run both methods: the per-entity lifecycle loop (Sections 2–3) catches a gap inside one entity, and the cross-cutting sweeps (Section 4) catch a gap in the cross-product of two or more systems that belongs to no single entity.

## 1. Setup

1. State the design-doc directory and enumerate it for real:

```
$ find <dir> -maxdepth 1 -name '*.md' | sort
<actual output>
```

## 2. Entity Inventory

1. Show real output, not paraphrase, and read every file from Section 1.
2. List every noun the docs treat as a first-class *thing*, something that exists, gets created, changes state, or is removed, and not a *system* or *mechanic*: a system is a rule, and an entity is what the rule acts on.
3. For each entity:

```
<entity name> — first introduced <file>:<line>, "<exact quoted phrase>"
```

4. Leave off an entity mentioned only as flavor text, never independently created, put at risk, or removed anywhere in the set, verified with a real grep across every file.
5. Note each excluded entity with the grep that ruled it out.

## 3. Per-Entity Micro-Loop (repeat for every entity in Section 2)

1. Take each entity through all four steps below before moving to the next entity, never running (a) for all of them and the (d) filter as one batch at the end.

**(a) Lifecycle check.**

1. Fill six slots with real grep or Read output, quoted with its location, or mark the slot UNSPECIFIED together with the search that came up empty:
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

**(b) Consumer-without-producer flag.**

1. If downstream effect has real content but removal trigger is UNSPECIFIED, log a raw candidate.
2. Grep every place the entity's past-tense or result form is used as a precondition elsewhere in the set, and quote the hit count.
3. Treat a high count on the effect side with zero on the trigger side as the gap, not as a trigger defined somewhere unindexed.

**(c) Second look.**

1. Before advancing, re-read the passages cited in (a) and (b), hunting for a second, different gap in the same text.
2. State either the second finding or "re-scanned, nothing further".

**(d) Filter checkpoint — on this entity's candidates only, now, before the next entity.**

1. For each candidate from (b) and (c), check all four and log the result even when it's a drop:
  - Re-verified absence with a second, differently-worded grep.
  - Product/mechanism-level, not a numeric or tunable parameter this
    doc set already defers on purpose — check for that set's own
    deferral convention before flagging.
  - Not a restatement of a candidate already logged for a different
    entity this run.
  - The effect side actually presupposes this specific missing cause,
    not just sits near it.
2. On any No, log "considered and dropped" with a one-line reason rather than deleting it; on all Yes, send it to Section 5.

## 4. Cross-Cutting Coverage Sweeps (run once, across the whole set, after Section 3)

1. Run these two sweeps once over the entire doc set, not per entity.
2. Build each sweep as a coverage matrix: enumerate the cells, then fill every one with either a specifying file:line or an explicit-deferral file:line.
3. Log a cell you can fill neither way as a raw candidate, run it through Section 3(d)'s four checks, and send survivors to Section 5 alongside the per-entity findings.

**(A) Partition-totality sweep.**

1. Grep the set for every rule that gates a role, effect, or eligibility on what a thing *is* or *what state it's in*, using the giveaway verbs `counts as | doesn't count | qualifies | eligible | can only | may only | only <X> can | requires being | must be | isn't counted`.
2. For each hit, name the attribute it partitions on and list every value that attribute can take from the docs' own vocabulary.
3. Confirm the rule states an outcome for *each* value, not just the values that qualify plus a single "otherwise nothing".
4. Hunt for a rule that enumerates who's in and pairs it with only the empty negative ("if none is present…"), so a thing present but not qualifying falls through.
5. Require a total partition to name all three: qualifies, present-but-doesn't-qualify, and absent.

**(B) State-combination and boundary sweep.**

1. *State combinations.* For each entity that can hold more than one state or condition at once, enumerate its states from the docs, and for each pair that can legally co-occur, confirm the docs either specify the combined behavior or rule the pairing out.
2. Before flagging a combination, trace it to an existing mechanism, such as a factor already in a formula; a combination that resolves through one is a close, not a gap.
3. *Boundaries.* Enumerate every boundary of the play space, such as a spatial edge, a time limit, a vision budget, a count cap, or a range cutoff, and cross each against every mechanic that can reach it.
4. Flag a boundary a mechanic can hit with no stated result.
5. When both sweeps' matrices are full, every cell a specifying or a deferring file:line, stop, and name the residual risk as "a matrix missing a whole axis".
6. Report that scoped closure as "no structural gaps found", and say it does not cover tuning values the set defers on purpose or whether the design is fun.

## 5. Findings Report

1. Present only candidates that survived the step-(d) filter, from Section 3 or Section 4, in the Evidence-block format `~/.claude/CLAUDE.md`'s Evidence Format section requires.
2. Put REFs first, one ref per claim, and prefix with `hypothesis:` anything asserting a specific reason a gap exists rather than just that it exists.
3. Write the prose per `~/.claude/CLAUDE.md`'s Communication Style section, naming the entity or the interacting systems and the missing rule directly.
4. Include the full "considered and dropped" log from every step (d) underneath.
5. Place every entity from Section 2, and every matrix cell from Section 4, in exactly one of three places: a surviving finding, a line in "considered and dropped", or a one-line "checked, no gap" note naming what closed it.
6. Treat an entity or a matrix axis that appears upstream but nowhere here as an incomplete run.
7. **Running a second time over the same directory.** If a caller revises the documents and runs this template again, as `spec-task` Section 9 does, treat the previous report and log as context, not precedent.
8. On that re-run, redo Section 2's inventory and Section 3's lifecycle check over every entity the revision touched, re-fill any Section 4 matrix cell whose axis gained a value, and let the step-(d) filter drop duplicates on their own merits.

## 6. Stop — the report, then the caller's rules

1. Deliver the Section 5 report as this template's entire deliverable; Sections 1 through 5 only read.
2. Resolve the findings next, which writes.
3. **A caller that invoked this template inside its own loop owns what happens to the findings, and this section does not override it.** `spec-task` Section 9 is that caller: its step 3 routes every finding into the document and its step 4 revises it, so follow the caller.
4. **Never ask whether a decision belongs in the design document.** Put a confirmed finding into the document and commit it, per `spec-task` Section 8.
5. Ask the operator only a real choice between competing product answers, as the choice itself with the options named, through AskUserQuestion.
6. Research the options first, per `writing-code`'s "Probe before you build" section.
7. Once the report is delivered, move straight into resolving the findings in a sensible order, such as report order, without asking permission to start.

## Notes on what this template does NOT do

- Does not write to any file during the sweep — Sections 1 through 5 only
  read, so the report describes the documents as they stood. Resolving the
  findings afterward does write, under Section 6's rules.
- Does not research or resolve a flagged gap (no WebSearch, no
  precedent-gathering) during the sweep. When the conversation afterward
  researches a gap, `writing-code`'s "Probe before you build" section
  applies: a historical or precedent claim backing a recommended option
  needs a real search or citation that session, whether it lands in prose
  or inside a tool call like AskUserQuestion.
- Does not delegate the inventory, lifecycle check, or coverage sweeps
  to a subagent — investigation is done directly, per the `subagents`
  skill.
- Does not flag a numeric or tunable parameter the doc set already
  defers on purpose.
- Does not batch the per-entity filter to the end — Section 3(d) runs
  per entity. The Section 4 sweeps are the one deliberate exception:
  they run once across the whole set by nature, since their subject is
  cross-entity, and they filter their own candidates with the same four
  checks before the report.
- Does not chain to another task template automatically. A caller that
  loops it, as `spec-task` Section 9 does, owns that loop.
- Does not add auto-activation triggers to its own description.