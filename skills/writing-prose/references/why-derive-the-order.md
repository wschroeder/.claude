# why-derive-the-order — the failures that produced each rule, and the research behind them

Every measurement here was run. Output is pasted from the session that produced the
rule, not reconstructed.

- [The failure that produced the ordering discipline](#the-failure-that-produced-the-ordering-discipline)
- [The failure that produced the graph](#the-failure-that-produced-the-graph)
- [Why the judgment items need a re-run rule](#why-the-judgment-items-need-a-re-run-rule)
- [What the research says](#what-the-research-says)

## The failure that produced the ordering discipline

A 15-slide deck explaining the `tdd-cycle` skill passed every gate its template had
— balance, voice bands, render inspection — and shipped with three ordering defects
that a reader hits in the first ten seconds:

1. **Slide 2 used Red and Green; slide 3 defined them.** The slide arguing why
   probing matters talked about "red and green both passing" one slide before the
   deck named the five states.
2. **One topic sat in two places with unrelated slides between.** Slide 10 introduced
   the `writing-code` companion skill; slide 14 carried its comment rule. Slides 11
   through 13 covered activation, the autonomous loop, and a recap.
3. **New material arrived after the recap.** Slide 13 was phrased "the short
   version". Slide 14 then introduced a new topic, before slide 15 said goodbye.

Neither of the two gates that existed could see any of it. `content_balance.py`
compares word share; `voice_stats.py` measures sentence habits. Order was never an
input to either, and the one place order got set — the unit numbering in
`outline.tsv` — had a `why` column justifying *word budget*, not sequence.

How defects 2 and 3 got there is worth recording, because it is a process trace
rather than an accident. `content_balance.py` reported one source section as
`DROPPED`. The fix was to add a unit for it. The unit was appended as the last row of
the outline, because that is where a new row goes — and nothing then asked where that
*topic* belonged. A gate answered with the cheapest edit that silenced it produced
two of the three defects.

## The failure that produced the graph

A six-page document ran through the ordering gate above, in three sessions, and
still shipped with a numbered summary whose items were in the wrong order and a
closing block that restated the summary almost word for word. The operator caught
both by reading. Measured afterwards, in that session's own working files:

```
ideas.tsv                           44 rows, keyed by word slug, no numbers, no order
outline.tsv                         12 rows
idea slugs traceable into outline     3   terminal-artifact, enumerate-first, anti-anchoring
idea slugs with no trace             41
```

The brainstorm dump was already the right shape. What went missing was the grouping:
44 ideas became 12 units, and nothing recorded how. The step existed and left no
artifact, which is what the graph now is.

Worse, the mapping ran in only one direction:

```
ideas.tsv rows citing a real source        44 of 44
outline rows with section '-'               4   units 1, 2, 3, and 12
```

Four units had no idea behind them at all, and two of those four were the units the
operator complained about. The template demanded a "no source" list and said outright
that it must not be invisible; no such file existed. Its gate watched for a source
section that no idea drew on, and nothing watched for a document unit that no idea
produced. Both problem units walked through the unwatched direction, which is why
step 7 now checks both.

## Why the judgment items need a re-run rule

In those same three sessions, the scripted checks ran constantly and the written ones
ran once:

```
grep -c "outline_flow.py"                 21 runs in one session, 5 in the next
gate item "Nothing repeats"               answered once, in the first session
                                          skill-injection text only, in the other two
```

The summary page that caused the duplication was requested 800 messages after that
one answer. The handoff at the end of that session said in as many words: "Adding a
unit is structural, so the convergence rule readmits you to Section 7." The next
session's opening message carried the same instruction forward. The written items
were never answered again.

A handoff telling the next session to re-run a check is not a substitute for
re-running it. That is why step 7 says any structural change readmits you to step 3
rather than leaving the re-run to whoever reads the notes.

## What the research says

**Higher-order concerns before lower-order concerns.** Writing centres teach revision
top-down: thesis, development, and organization are settled before grammar, word
choice, and sentence shape, because "surface-level edits are ineffective if the
foundational structure of the document is flawed." This is why the tiers put every
sentence rule after the order is settled.

- [Higher and Lower Order Concerns for Editing](https://pressbooks.pub/composition2024/chapter/reading-1-higher-and-lower-order-concerns-for-editing/)
- [Structured Revision — Writing Commons](https://writingcommons.org/section/writing-process/revision/revision-revision-guide/)
- [Revising: Higher and Lower Order Concerns (Smith College)](https://www.smith.edu/sites/default/files/media/Documents/Jacobson-Center/higher-lower-concerns.pdf)

**Reverse outlining is the named technique.** Reduce a finished draft to one line per
unit, then read the outline rather than the prose. It surfaces "sudden jumps between
ideas, paragraphs that seem out of order," and material on one topic "scattered
throughout the paper" that should be regrouped — defects 1 and 2 above, named in the
pedagogy decades before either template existed. The derivation printout in step 3 is
a reverse outline computed from the graph rather than typed from the draft.

- [Reverse Outlines — University of Wisconsin](https://writing.wisc.edu/handbook/reverseoutlines/)
- [Reverse Outlining — Oregon State](https://writingcenter.oregonstate.edu/reverse-outline)
- [Reverse Outline — University of Waterloo](https://uwaterloo.ca/writing-and-communication-centre/reverse-outline)

**Deck-specific checks.** Reviewers of presentations ask whether the slide order
supports a narrative, whether each slide carries one idea — if its point needs "and"
or "or" to state, it is two slides — and note that a deck gets read out of order, so a
slide leaning on its predecessor is fragile. The "one idea per unit" and "cold reader"
items come from here.

- [10 Specific Things To Check Your Slide Deck Against](https://nurijanian.substack.com/p/10-specific-things-to-check-your)
- [Slides Deck Organization Guidelines](https://www.przntperfect.com/post/slides-deck-organization-guidelines)

**Terms defined before use** is standard technical-document review practice, usually
enforced through a glossary. The `needs` relation is the same rule applied to unit
order, and the topological sort is what enforces it without anyone reading for it.

- [A review checklist for technical writers](https://medium.com/@Archanachowty/a-review-checklist-for-technical-writers-a382dea4059f)

What `tdd-cycle` contributes is the enforcement shape rather than any writing rule:
each item is a gate and not a suggestion, a failing gate is fixed inside the loop
instead of being handed to the operator as a preference, a fix re-runs the whole
checklist rather than the failed item, and a measurement nobody printed is a
measurement nobody made. Printing the derivation is that last rule applied to
structure — the same reason `tdd-cycle` says to run the file count rather than
estimate it.
