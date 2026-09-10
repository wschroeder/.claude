---
name: dashboard-task
description: Builds a dashboard or a data report that argues a point the operator chose — opens the data, declares what it can and cannot support, then proposes three to five candidate stories with the numbers behind each and stops for the operator to pick one or write their own. Never chooses the story itself. From that sentence it drives `writing-prose` to derive the block order, ranks every block so no two carry the same weight, fixes one type scale, one spacing scale, and one corner radius before anything is placed, gives each figure exactly one owner, gates the built file for repeated numbers and for how many distinct sizes it contains, renders it, and reviews it against a seven-check grid before stopping for approval. Hands every chart to `dataviz` and everything about behaving at any width to `responsive-design`, and restates neither. Use when the ask names a dashboard, a data report, an analysis write-up, or a page of charts for a client or a team.
---

# dashboard-task — build a surface that makes a point

Respond with the following sections in order. The order is enforced: each section's
output is the input the next one consumes, and a later section exhibits an earlier
one's fakery. This template builds in the session scratchpad and stops before
anything is written into the user's project.

## The claim this template is built around

A dashboard is not a neutral window onto data. Which numbers you chose, which you
left out, what you put at the top, and what you made big are all arguments, and a
reader absorbs them whether or not you meant to make them. "Here is everything,
you decide" is not neutrality — it is an argument the author declined to defend,
and the reader still has to live with it.

So this template asks you to make the argument on purpose, and to let the operator
make it. Section 2 asks what a reader could wrongly conclude, because that is the
part you are responsible for either way. Section 3 puts the candidate stories to the
operator and stops there. A run never picks the story, and wanting to explore the
data is not an exemption — a browsing surface is a candidate like any other, and it
still needs the sentence that says what it is for.

## Where the content comes from

`writing-prose` owns composition — dumping every idea before any order exists,
deriving the grouping and the sequence from an idea graph, and writing the headings
last from the finished body. **This template drives it, at Section 4**, once the
operator has chosen what the surface argues. It cannot run earlier: its step 0 wants
the one sentence the whole thing argues, and until Section 2 has opened the data
nobody can name that sentence honestly.

`dataviz` owns every individual chart — whether the data even wants a chart, which
form, which colour job, mark specs, the hover layer, and the accessibility pass. Load
it at Section 7 and run its procedure per chart. **This template never restates a
chart rule.** Where the two could seem to overlap, `dataviz` wins: it decides what a
chart looks like, and this template decides only where that chart sits and how much
room it gets.

`responsive-design` owns how the page behaves at a width nobody designed for — the
units, the fluid type scale, where a layout wraps, which query answers which
question, pointer targets, and the accessibility criteria that settle every number.
Load it at Section 6 and follow it. **This template never restates a unit or a
breakpoint rule.**

A brand — fonts, colour identity, tokens — belongs to whichever skill your private
routing names for it. Section 6 reaches that slot. If your routing names none, choose
the scales yourself and say why.

Every section's output follows `~/.claude/CLAUDE.md` "Evidence Format (HARD
CONSTRAINTS)", and every sentence follows its "Communication Style (HARD
CONSTRAINT)". This file restates neither.

Machinery is at `scripts/` beside this file. Run its tests once before trusting the
gate: `python3 scripts/test_layout_scales.py`

---

## Section 1 — Inputs

Ask the operator for anything not supplied. Do not infer a value.

```
Surface:        <dashboard | data report | analysis write-up>
Audience:       <who reads it, and what decision they face when they do>
Data:           - <path to each dataset>
Existing file:  <path, or NONE>
```

What this surface argues is not an input. Nobody can name it before the data has
been opened, which is why asking for it here only ever produced a sentence somebody
guessed. Section 2 opens the data and Section 3 settles the story.

For an existing surface, this runs as a retro-fit against the built file and the
outcome is a diff.

## Section 2 — Declare the data, and the reading you are imposing

This is first contact with the data. Everything Section 3 proposes has to come from
what you find here, so look wider than the question you arrived with.

Valid output: for each dataset, the real output of

    wc -l <path> && head -1 <path>

Then, per dataset, three written answers. Not "looks fine".

- **What it can answer.** Name the questions these columns settle.
- **What it cannot answer.** Name the question a reader will most likely bring that
  these columns do not settle. A count of matches per venue does not measure how good
  a venue is.
- **What a reader could wrongly conclude.** Name at least one, and say where in the
  build you guard against it — an annotation, a denominator shown beside a count, an
  axis that starts at zero, a caption naming the confound.

Anything you know about the data that is not in the data goes here too: how it was
collected, what it excludes, and who chose the categories. That knowledge disappears
the moment somebody else opens the file, and this is the only section that captures it.

## Section 3 — Propose the stories, and stop

**The operator chooses what the surface argues. You never choose it for them.**

A run that picks its own story ships a dashboard arguing something nobody asked for,
and the operator finds out at the end. That has happened, on a prompt that said only
"make me a dashboard to explore the data".

Offer **three to five** candidates. Two is not a choice. Each one gets four lines:

```
sentence:   the one sentence this surface would argue
evidence:   the numbers from Section 2 that support it, quoted
asks:       what it asks the reader to accept
leaves out: what the data holds that this story drops
```

Every candidate's `evidence` carries real figures you computed in Section 2. A
candidate you cannot back with a number is a hunch, and it does not go on the list.

Spread the candidates. Three readings of the same column are one candidate wearing
three hats; go looking for a story in a column you have not touched yet.

**"Explore the data" is not a story, and it is not a reason to skip this section.**
A browsing surface is a candidate like any other and still needs its sentence —
something on the order of "these are the columns worth filtering, and here is what
each one tells you" — so that Section 5 can rank against it and Section 9 can test it.

Put the candidates up with `AskUserQuestion`, per `~/.claude/CLAUDE.md` "Choices and
options get visual separation". The last option is always the operator's own story
rather than one of yours.

Then stop. Do not open Section 4 on a story you chose.

## Section 4 — Derive the order from the chosen story

Load `writing-prose` and run its third tier, giving the operator's chosen sentence as
its step 0. Stop where that skill says to stop, at its step 4, and show the operator
the derived order before a body gets drafted against it.

Valid output: the real output of

    python3 ../writing-prose/scripts/graph_order.py --ideas ideas.tsv --graph graph.tsv

What comes back — `ideas.tsv`, `graph.tsv`, and the printed derivation naming the
groups, the levels, and the free choices somebody made — is what Section 5 consumes.
A block order invented in Section 5 is the defect `writing-prose` exists to prevent.

## Section 5 — Rank the blocks onto the screen

One block per derived group, in the order the levels give. Write `layout.tsv`:

```
block<TAB>group<TAB>rank<TAB>slot<TAB>form<TAB>figures<TAB>why
```

- `block` — a word slug, matching a `data-block="<slug>"` the build will carry.
- `group` — the group's name from the derivation. Not renamed here.
- `rank` — a positive integer, distinct across every row, contiguous from 1. Rank 1
  is what a reader must see first. **Distinctness is the whole point of the column:**
  you cannot give six elements the same weight if you were made to order them.
- `slot` — `hero`, `primary`, `secondary`, or `supporting`. Rank 1 takes `hero`, and
  nothing else does. The largest area on the screen goes to the highest-ranked block,
  whatever form it turns out to want.
- `form` — the answer `dataviz` gives for this block, recorded and not decided here.
  When its "Is it even a chart?" table says a stat tile or a hero number, write that;
  a hero slot holding a single number is a correct outcome, not a thin one.
- `figures` — the specific numbers this block owns, comma-separated. **A figure
  appears in exactly one row's list.** Section 8 proves the build honoured it.
- `why` — one clause. Wherever two blocks could have taken either rank, the winner's
  `why` says which two and why this one went first. A free choice you do not write
  down is one you will not remember making.

A table is a form like any other and takes a `why` naming the question it answers.
"Every value, sortable" is not a question.

## Section 6 — Fix the scales before anything is placed

Load `responsive-design` now and take its unit rules from it: type and space in
`rem`, fluid steps through `clamp()` so one scale replaces a second scale
hand-written at a breakpoint, measure in `ch`. This section decides *which* scales
this surface gets; that skill decides what they are made of, and this one does not
restate it.

Write them as CSS custom properties at the top of the file, before the first block
exists. Four decisions, each with one line saying why:

- **Type scale** — the set of font sizes the whole surface may use, as `clamp()`
  steps rather than a list of fixed sizes.
- **Spacing scale** — the set of padding and margin values it may use, in `rem`.
- **Corner radius** — one value, or two at the most.
- **Colour identity** — what makes this surface look like one thing rather than six.
  This is the identity question, not the encoding question; `dataviz` owns encoding
  and validates the palette against colour-vision deficiency at Section 7.

If your private routing names a skill that owns a brand and its tokens, load it now
and take whatever it settles. Expect it not to settle all four: a brand built for
print has no screen type scale, and many define no corner radius at all. Name each
decision it left open, choose that one yourself, and say why. If your routing names
no brand skill, all four are yours on the same terms.

Shipping whatever the framework defaulted to is itself a decision, and the reader
reads it as one: a surface that did not change its design defaults invites the
question of whether it changed its analysis defaults either.

Section 8 counts how many distinct literal sizes the built file actually contains.
Values reached through `var()` do not count, so defining the scale here is what
makes that gate passable.

## Section 7 — Build, loading dataviz for every chart

Load `dataviz` and run its procedure for each block whose form is a chart. Follow it
exactly and do not restate it here.

Build into the session scratchpad. Writing into the user's project happens at Section
10 and not before.

What this template adds, because the gate and the review read them:

- Every block's container carries `data-block="<slug>"` matching `layout.tsv`. A block
  built without it is invisible to Section 8, which then gates against nothing.
- Every size, space, and radius is written as `var(--token)`, never as a literal.
- The layout, the queries, and the disclosure controls follow `responsive-design`,
  loaded at Section 6. Its filter rule matters most here: `dataviz` puts filters in
  one row above the charts and assumes a wide viewport, and that skill owns what
  happens to that row when the viewport is narrow.

## Section 8 — Gate the built file

Valid output: the real output of

    python3 scripts/layout_scales.py --html <built.html> --layout layout.tsv

Six findings, and each gets a written disposition:

- `TYPE-SCALE`, `RADIUS-SCALE`, `SPACE-SCALE` — more distinct literal values than the
  ceiling allows. Fix by moving the value into a token, or raise the ceiling in one
  line saying why this surface needs more sizes than the ceiling assumes.
- `RANK` — two blocks claiming one rank, a gap in the sequence, or a rank that is not
  a positive integer. This is the flat hierarchy showing up as data.
- `REPEATED-FIGURE` — a number one block declared, rendered in another block too.
  Either the second one drops it, or `layout.tsv` is wrong about who owns it.
- `FIGURE-ABSENT`, `BLOCK-MISSING`, `BLOCK-UNDECLARED` — the build and the plan
  disagree about what exists. Fix whichever is wrong, and say which.

One warning class, which does not fail the gate:

- `REPEATED-NUMBER` — a number rendered in two or more regions that no row declared.
  The script cannot tell a restated headline figure from a coincidence, so each
  warning takes a one-line answer at Section 9 check 4 rather than a fix.

The script reads the page chrome — everything above the first block — as a region of
its own, because a figure restated in a masthead or a filter row is the duplication a
reader actually sees. It ignores `<script>` and `<style>` bodies, so an embedded
dataset does not register as rendered text. What it still cannot tell apart is an
axis tick or a year that happens to match a real figure, so read the locations a
finding names before changing anything.

Do not advance while the script exits non-zero and any finding is unanswered.

## Section 9 — Render it, then review it check by check

Two artifacts, and they answer different questions.

**A full-page desktop render**, for checks 1 to 6, which are about blocks:

    ~/.claude/skills/responsive-design/scripts/render.sh \
      --url <built.html> --out <out.png> --width 1440 --height 2400

That script owns every render both skills make, and `responsive-design` explains
why: Chrome does not exit after writing the file, so a command that waits for it
pays its whole timeout. The image comes out at exactly the window size you asked
for. Add `--fonts` on a dom pass before trusting any measurement taken from a page
that pulls its fonts over the network.

**The width strip from `responsive-design`**, for check 7, which is about widths.
That skill owns the command, the widths, and what to look for. Do not build your own
set of device sizes here — the widths that matter come from an accessibility
criterion, not from a list of phones.

Then open both and read them.

### The grid

**Checks 1, 2, 5, and 6 run against every block. Checks 3, 4, and 7 run once for
the whole surface.** Eight blocks is thirty-five dispositions. Keep the grid in
your working notes; what reaches the response is the findings, the artifacts
checks 1 to 4 and 7 owe, and the coverage line.

Counting the whole grid is the point of it. A review that reports three defects
without saying how many things it examined has reported whatever it happened to
notice, which is how this section failed on the run that produced its first real
dashboard: it looked at seven renders, wrote one sentence naming three cosmetic
defects, and shipped a chart whose vertical axis had no unit.

Every block-and-check pair resolves to exactly one of three states, the same three
`quick-review` uses. There is no fourth.

- **DEMONSTRATED** — backed by something produced in this session: a crop you read,
  a string you quoted off the page, a measurement you ran. Cite it.
- **N/A** — the check is not live for this block. One line of why (`no chart here`,
  `nothing scrolls`).
- **`hypothesis:`** — you suspect a problem and could not produce the artifact.
  Report it labelled rather than dropping it.

"It reads fine" is not a disposition. It is the slot this section exists to close.

### The checks

**Checks 1 to 4 and check 7 owe an artifact even when they come back clean.** For those,
prose is an invalid disposition — they are the ones a builder passes by knowing
what the page means rather than by reading what it says.

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
```

Checks 5 and 6 may be answered in prose, but prose that cites a measurement or
quotes a line, never a story about what the reader will probably understand.

### The coverage line

Close the section with it, and make it real:

```
4 per-block checks x <n> blocks + 3 once = <n> pairs
DEMONSTRATED <n>   N/A <n>   hypothesis <n>   findings: <n>
```

A pair you did not attempt is not `N/A`. Attempt it, or say the grid is incomplete
and which pairs are missing.

### What still needs a person, after the grid

Two questions the grid cannot ask, both answered from the render alone and before
you reopen `layout.tsv`:

- **The point this surface makes**, in one sentence. Compare it to the sentence
  the operator chose in Section 3. A gap between them is the finding, and the
  operator's sentence is not the one to change.
- **What a reader could wrongly conclude** that no check above covers.

## Section 10 — Stop, awaiting approval

Do not copy anything into the user's project. Present the built path, the gate
output, the render, and the exact destination path. Then wait.

Prior approval in this session does not carry forward. Each write, each overwrite,
and any later commit needs its own authorization, per `git-commit` "Safety".

Publishing is a separate question again, and the answer is no unless the operator
asks for it in their own words, per `~/.claude/CLAUDE.md` "Local Files by Default,
No Publishing Without Asking (MANDATORY)".

---

## Convergence

Every item above is a gate, not a suggestion, and every item gets a written
disposition. Then:

- A fix inside a section re-runs **that section's whole gate**, not just the item
  that failed.
- **A fix that changes which blocks exist, or what order they go in, is not fixed
  here.** It goes back to `writing-prose` step 3, and this template restarts at
  Section 5 against the new derivation. Restyling stays here; anything structural
  leaves.
- Changing a rank is structural. It changes what the surface argues.
- Say a gate is complete only when the most recent full run happened against the
  current files with nothing edited after. Otherwise, say which edits landed after
  the last run.
- A gate that cannot be closed is reported to the operator with its number and what
  it would take. It is not reclassified as a preference.

## Notes on what this template does NOT do

- Does not choose what the surface argues. Section 3 puts candidates to the
  operator and stops.
- Does not decide what order the blocks go in. `writing-prose` owns that, and Section 4
  runs it rather than inventing an order here.
- Does not decide anything about an individual chart — not the form, the colours, the
  marks, the tooltips, or the accessibility pass. `dataviz` owns all of it.
- Does not name a brand. Section 6 reaches a slot your private routing fills.
- Does not decide a unit, a breakpoint, a query, or a pointer-target size.
  `responsive-design` owns all of it, and the numbers there come from WCAG
  rather than from a list of devices.
- Does not write into the user's project. That is a separate authorization.
- Does not commit, push, or publish.
- Does not judge whether the data supports the point. Section 2 asks you to write
  down what the data cannot answer; nothing here checks that you were honest.
- Does not decide whether an undeclared repeated number matters. The sweep finds
  them and warns; telling a restated headline figure from a coincidence is check 4's
  job, and yours.
- Does not see a footer. The last block's markup runs to the end of the document, so
  anything after it is attributed to that block rather than to the page chrome.
