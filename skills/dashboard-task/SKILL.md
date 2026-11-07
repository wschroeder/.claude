---
name: dashboard-task
description: Builds a dashboard or a data report that argues a point the operator chose — opens the data, declares what it can and cannot support, then proposes three to five candidate stories with the numbers behind each and stops for the operator to pick one or write their own. Never chooses the story itself. From that sentence it drives `writing-prose` to derive the block order, writes every word the reader will read before any visual exists, ranks every block so no two carry the same weight, fixes one type scale, one spacing scale, and one corner radius before anything is placed, gives each figure exactly one owner, gates the built file for repeated numbers and for how many distinct sizes it contains, renders it, and reviews it against an eight-check grid before stopping for approval. Hands every chart to `dataviz` and behaviour at any width to `responsive-design`, restating neither. Use when the ask names a dashboard, a data report, an analysis write-up, or a page of charts for a client or a team.
---

# dashboard-task — build a surface that makes a point

1. Respond with the following sections in order, because each section's output is the next one's input.
2. Build in the session scratchpad, and stop before anything is written into the user's project.

## The claim this template is built around

1. Treat every choice of which numbers to show, which to leave out, what goes on top, and what is big as an argument the reader absorbs.
2. Make the argument on purpose, and let the operator choose it at Section 3.
3. Never pick the story yourself, including when the ask is only to explore the data: a browsing surface is a candidate like any other and still needs its sentence.

## Where the content comes from

1. Drive `writing-prose` at Section 4, once the operator has chosen what the surface argues, and never earlier.
2. Load `dataviz` at Section 7 and run its procedure per chart; never restate a chart rule, and where the two overlap, `dataviz` wins on what a chart looks like while this template decides only where it sits and how much room it gets.
3. Load `responsive-design` at Section 6 and follow it; never restate a unit or breakpoint rule.
4. Take a brand from whichever skill your private routing names, at Section 6; if your routing names none, choose the scales yourself and say why.
5. Follow `~/.claude/CLAUDE.md` "Evidence Format (HARD CONSTRAINTS)" and "Communication Style (HARD CONSTRAINT)" in every section's output, without restating them.
6. Find the machinery at `scripts/` and the chart library at `assets/`, beside this file.
7. Run all three test suites once before trusting any of them; the last two drive real Chrome, and `test_chartkit.py` takes about a minute:

    python3 scripts/test_layout_scales.py
    python3 scripts/test_block_contrast.py
    python3 scripts/test_chartkit.py

---

## Section 1 — Inputs

1. If the surface is a status or health page, then load `status-page`, build to its layout, and skip Section 3's stop.
2. Ask the operator for anything not supplied, and do not infer a value:

```
Surface:        <dashboard | data report | analysis write-up>
Audience:       <who reads it, and what decision they face when they do>
Data:           - <path to each dataset>
Existing file:  <path, or NONE>
```

3. Do not ask for what the surface argues here; Section 2 opens the data and Section 3 settles the story.
4. For an existing surface, run this as a retro-fit against the built file, and deliver a diff.

## Section 2 — Declare the data, and the reading you are imposing

1. Look wider than the question you arrived with, because everything Section 3 proposes has to come from here.
2. For each dataset, paste the real output of

    wc -l <path> && head -1 <path>

3. Per dataset, write three answers, never "looks fine":
   - **What it can answer:** the questions these columns settle.
   - **What it cannot answer:** the question a reader will most likely bring that these columns do not settle.
   - **What a reader could wrongly conclude:** at least one, with where in the build you guard against it, such as an annotation, a denominator beside a count, a zero-based axis, or a caption naming the confound.
4. Write down here what you know about the data that is not in the data: how it was collected, what it excludes, and who chose the categories.

## Section 3 — Propose the stories, and stop

1. Let the operator choose what the surface argues; never choose it for them.
2. Offer three to five candidates, each in four lines:

```
sentence:   the one sentence this surface would argue
evidence:   the numbers from Section 2 that support it, quoted
asks:       what it asks the reader to accept
leaves out: what the data holds that this story drops
```

3. Back every candidate's `evidence` with real figures computed in Section 2, and drop any candidate you cannot back with a number.
4. Spread the candidates across columns, and look for a story in a column you have not touched yet.
5. If the ask is to explore the data, then offer a browsing surface as a candidate with its own sentence, so Section 5 can rank against it and Section 9 can test it.
6. Put the candidates up with `AskUserQuestion`, one option each, and make the last option the operator's own story.
7. Stop, and do not open Section 4 on a story you chose.

## Section 4 — Derive the order, then write every word the reader will read

1. Load `writing-prose` and run its third tier, giving the operator's chosen sentence as its step 0.
2. Do not stop at its step 4, because a dashboard's body comes from a generator and reordering it costs only a rebuild.
3. Paste the real output of

    python3 ../writing-prose/scripts/graph_order.py --ideas ideas.tsv --graph graph.tsv

4. Hand `ideas.tsv`, `graph.tsv`, and the printed derivation to Section 5, and never invent a block order there.

### Then write `copy.md`, and stop on that

1. Write every string a reader will read before any scale, colour, or mark exists, one entry per derived group plus one for the page chrome:

```
# <the page headline>
<the standfirst, one or two sentences>

## <block heading>            [group: <name from the derivation>]
<the sentence this block asserts, in the reader's words not the data's>
axis / category labels: <every string that will be drawn as a label>

...

# Limits
<one bullet per thing the data cannot support>

# Colophon
<source, date, and what the figures are>
```

2. Write the headline and the block headings last, from the sentences under them, per `writing-prose`.
3. Leave a label unused when its block turns out not to need one.
4. Stop and show `copy.md` in full, and end with one question asking whether the words hold; this is the only stop before the build.
5. Build Section 7 from this file only, and never invent a string during the build.

## Section 5 — Rank the blocks onto the screen

1. Give one block per derived group, in the order the levels give, and write `layout.tsv`:

```
block<TAB>group<TAB>rank<TAB>slot<TAB>form<TAB>figures<TAB>why
```

2. `block`: write a word slug matching the `data-block="<slug>"` the build will carry.
3. `group`: copy the group's name from the derivation, unrenamed.
4. `rank`: give a positive integer, distinct across every row and contiguous from 1, with rank 1 what a reader must see first.
5. `slot`: write `hero`, `primary`, `secondary`, or `supporting`; give `hero` to rank 1 only, and give the largest area to the highest-ranked block whatever its form.
6. `form`: record the answer `dataviz` gives, and if its "Is it even a chart?" table says a stat tile or a hero number, write that.
7. `figures`: list the numbers this block owns, comma-separated, written as the page will print them, and put each figure in exactly one row.
8. If Section 8 reports a figure absent, then find out which side is wrong before editing either.
9. `why`: write one clause, and wherever two blocks could have taken either rank, name both and why the winner went first.
10. Give a table a `why` naming the question it answers; "Every value, sortable" is not a question.

## Section 6 — Fix the scales before anything is placed

1. Load `responsive-design` now and take its unit rules from it.
2. Write the scales as CSS custom properties at the top of the file, before the first block exists, each with one line saying why:
   - **Type scale:** the font sizes the surface may use, as `clamp()` steps.
   - **Spacing scale:** the padding and margin values it may use, in `rem`.
   - **Corner radius:** one value, or two at most.
   - **Colour identity:** what makes the surface look like one thing; `dataviz` owns encoding and validates the palette at Section 7.
3. If your private routing names a skill that owns a brand and its tokens, then load it now, take what it settles, name each decision it left open, choose that one yourself, and say why.
4. If your routing names no brand skill, then choose all four yourself on the same terms.
5. Never ship a framework's design defaults unexamined.
6. Reach every size through `var()`, because Section 8 counts only literal sizes.

## Section 7 — Build, loading dataviz for every chart

1. Load `dataviz` and run its procedure exactly for each block whose form is a chart.
2. Build into the session scratchpad, and write into the user's project only at Section 10.

### Draw on chartkit rather than deriving the geometry again

1. Concatenate `assets/chartkit.js` into the page's `<script>` ahead of the chart bodies, and write each body to draw only its own marks.
2. Never compute a padding, a label-column width, or a stacking threshold in a chart body.
3. Read [references/chartkit.md](references/chartkit.md) now, before the first chart body.
4. Give every block's container `data-block="<slug>"` matching `layout.tsv`.
5. Write every size, space, and radius as `var(--token)`, never as a literal.
6. Where the page recomputes a figure the build also wrote into the prose, make one formatter govern both, matching the browser's rounding, because Python rounds a half to even and JavaScript rounds it up.
7. Follow `responsive-design` for the layout, the queries, and the disclosure controls, including what happens to the filter row at a narrow width.

## Section 8 — Gate the built file

1. Paste the real output of

    python3 scripts/layout_scales.py --html <built.html> --layout layout.tsv

2. Paste its first two lines, which name each file opened and its SHA-256, with the findings.
3. Give each of the six findings a written disposition:
   - `TYPE-SCALE`, `RADIUS-SCALE`, `SPACE-SCALE`: move the value into a token, or raise the ceiling in one line saying why.
   - `RANK`: fix the duplicate, the gap, or the non-integer rank.
   - `REPEATED-FIGURE`: drop the figure from the second block, or correct `layout.tsv` about who owns it.
   - `FIGURE-ABSENT`, `BLOCK-MISSING`, `BLOCK-UNDECLARED`: fix whichever of build or plan is wrong, and say which.
4. Answer each `REPEATED-NUMBER` warning in one line at Section 9 check 4 rather than fixing it.
5. Read the locations a finding names before changing anything, because the script cannot tell an axis tick or a year from a real figure.
6. Do not advance while the script exits non-zero and any finding is unanswered.

## Section 9 — Render it, then review it check by check

1. Render the file whose digest the Section 8 report names; if you rebuilt after that report, then re-run Section 8 first.
2. Take a full-page desktop render for checks 1 to 6:

    ~/.claude/skills/responsive-design/scripts/render.sh \
      --url <built.html> --out <out.png> --width 1440 --height 2400

3. Add `--fonts` on a dom pass before trusting any measurement from a page that loads fonts over the network.
4. Take the width strip from `responsive-design` for check 7, and never build your own set of device sizes.
5. Open both renders and read them.

### The grid

1. Run checks 1, 2, 5, 6, and 8 against every block, and checks 3, 4, and 7 once for the surface.
2. Keep the grid in your working notes, and put in the response the findings, the artifacts checks 1 to 4 and 7 owe, and the coverage line.
3. Resolve every block-and-check pair to exactly one of three states:
   - **DEMONSTRATED:** backed by a crop you read, a string you quoted, or a measurement you ran in this session; cite it.
   - **N/A:** the check is not live for this block, with one line of why.
   - **`hypothesis:`:** a suspected problem you could not produce the artifact for, reported labelled.
4. Never write "It reads fine" as a disposition.

### The checks

1. Give checks 1 to 4, 7, and 8 an artifact even when they come back clean; prose is invalid for them.

```
1  AXIS UNITS       Name every axis on this block's chart and quote the text on
                    the page where a reader learns its unit.
   artifact:        the quoted string and the element holding it.
                    A unit carried only by the block title above the chart, or
                    only by the caption below it, is a FINDING.

2  EDGE CLIPPING    For every container here that scrolls or has a fixed size,
                    crop the render at its right and bottom edge.
   artifact:        the crop, read. A bare "no clipping" is invalid.

3  RANK LEGIBLE     Once per surface, not per block. Write the order your eye
                    lands in, first to last, BEFORE opening layout.tsv.
   artifact:        that list, then the diff against the ranks.

4  FIGURE SWEEP     Answer every WARN the gate raised, and read the page chrome
                    yourself for a figure a block also carries.
   artifact:        the gate's warning lines, each with a one-line answer.

5  EMPTY PLOT       What share of this chart's plotting area holds no marks?
   prose citing     Over a third, say which extreme forces the range and whether
   a measurement    it is annotated.

6  GUARD VISIBLE    For each risk Section 2 named that touches this block, quote
   prose citing     the text in the render that carries the guard.
   the quoted line  A guard that exists only in Section 2 is a FINDING.

7  ANY WIDTH        Once per surface. Run `responsive-design`'s review checklist
   artifact         against the built file and report its coverage line here,
   required         with every finding it raised. Its check 6 is the one this
                    template most often fails: at the narrowest width, does any
                    content reach the first screenful, or does the reader meet
                    a screen of controls?

8  CONTRAST         Every string this block draws, in both colour schemes,
   artifact         against the ratio WCAG 1.4.3 asks of its size.
   required         Run, for the whole surface at once:
                      python3 scripts/block_contrast.py --html <built.html>
                    Report its digest line and its findings. A page that
                    defines a dark scheme is not thereby tested in one: the
                    defect this catches is a colour that is right against the
                    page and wrong against the card the text sits on, and it
                    shows up in one scheme only.
```

2. Answer checks 5 and 6 in prose that cites a measurement or quotes a line.

### The coverage line

1. Close the section with a real coverage line:

```
5 per-block checks x <n> blocks + 3 once = <n> pairs
DEMONSTRATED <n>   N/A <n>   hypothesis <n>   findings: <n>
```

2. Attempt every pair, or say the grid is incomplete and name the missing pairs; an unattempted pair is not `N/A`.

### What still needs a person, after the grid

1. From the render alone, before reopening `layout.tsv`, write the point this surface makes in one sentence and compare it to the operator's Section 3 sentence; report a gap as a finding, and never change the operator's sentence.
2. Name what a reader could wrongly conclude that no check covers.

## Section 10 — Stop, awaiting approval

1. Do not copy anything into the user's project; present the built path, the gate output, the render, and the exact destination path, then wait.
2. Run

    python3 scripts/layout_scales.py --digest <built.html>

3. Compare its `sha256:` value, not the whole line, against the first line of the Section 8 report.
4. If the digests disagree, then rebuild if needed, re-run Sections 8 and 9, and present the new report.
5. Tell the operator that `shasum -a 256 <built.html>` starts with the same characters.
6. Report any wording change since Section 4 as prose in this message with the old and new strings, never as a file in the project.
7. Send the built file with `SendUserFile` and also give its path.
8. Get a fresh authorization for each write, overwrite, and commit, per `git-commit` "Safety".
9. Do not publish unless the operator asks in their own words, per `~/.claude/CLAUDE.md` "Local Files by Default, No Publishing Without Asking (MANDATORY)".

---

## Convergence

1. Give every item above a written disposition.
2. Re-run a section's whole gate after a fix inside it.
3. If a fix changes which blocks exist or their order, then send it back to `writing-prose` step 3 and restart at Section 5 against the new derivation; restyling stays here.
4. Treat a rank change as structural.
5. If wording changes after Section 4 was approved, then make the change, re-run Section 9 against the rebuilt file, and report the old and new strings at Section 10.
6. Call a gate complete only when its latest full run used the current files, checked by the Section 8 digest; otherwise name the edits made after the last run.
7. Report a gate you cannot close with its number and what it would take, and never reclassify it as a preference.

## Notes on what this template does NOT do

1. Does not choose what the surface argues.
2. Does not decide the block order; `writing-prose` owns it.
3. Does not decide anything about an individual chart; `dataviz` owns it, and every answer in a spec handed to `CK.cartesian` or `CK.rows` comes from `dataviz`.
4. Does not name a brand; Section 6 reaches a slot your private routing fills.
5. Does not decide a unit, a breakpoint, a query, or a pointer-target size; `responsive-design` owns them.
6. Does not write into the user's project without a separate authorization.
7. Does not commit, push, or publish; sending the built file with `SendUserFile` is none of these.
8. Does not check that Section 2 was honest about what the data cannot answer.
9. Does not decide whether an undeclared repeated number matters; check 4 does.
10. Does not see a footer: anything after the last block's markup is attributed to that block.
