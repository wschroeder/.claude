---
name: responsive-design
description: Makes a page work on a phone and a desktop without naming device widths — type and space in rem with clamp() so one fluid scale replaces a second scale hand-written at a breakpoint, layout that wraps on content with auto-fit and flex-wrap, a container query where a component should answer to its own column rather than the window, dvh instead of vh, and a disclosure control where fluid layout would otherwise fill the screen with widgets. Carries the numbers the standards already settled rather than invented ones: reflow at 320 CSS pixels, text resize to 200%, the four text-spacing overrides, and 24-pixel pointer targets. Ends in a review checklist naming what to test, at what width, and what a headless render cannot show you at all. Use when a page has to work on mobile and desktop, when CSS breakpoints, fluid type, viewport units, media or container queries are in question, and when reviewing a built page for how it behaves at widths nobody designed for.
---

# responsive-design

Be the browser's mentor, not its micromanager. You set constraints; the browser
does layout. Every device width you name is a width you will be wrong about.

Two failures follow from micromanaging, and they need different fixes:

- **It does not fit.** Fixed units and hand-picked breakpoints. Fluid units and
  content-driven wrapping fix this.
- **It fits and should not be there.** Eight controls need the room eight
  controls need, at any unit. Only disclosure fixes this.

Do not reach for the first fix when the problem is the second one.

## The numbers you do not have to invent

Never argue about a width. These are settled, and each is testable.

| What | Number | Source |
|------|--------|--------|
| Reflow, vertical scrolling content | **320 CSS px** wide, no horizontal scrolling | WCAG 1.4.10 AA |
| Reflow, horizontal scrolling content | **256 CSS px** tall | WCAG 1.4.10 AA |
| Text resize | **200%**, no loss of content or function | WCAG 1.4.4 AA |
| Text spacing the layout must survive | line-height **1.5**, paragraph **2em**, letter **0.12em**, word **0.16em** | WCAG 1.4.12 AA |
| Pointer target | **24×24 CSS px** | WCAG 2.5.8 AA |
| Pointer target, preferred | **44×44 CSS px** | WCAG 2.5.5 AAA |

**320 is not a phone.** It is a 1280px desktop viewport at 400% zoom, which is
what a low-vision reader actually does. That is why it is the floor and why no
device name belongs in this table.

1.4.10 exempts content that genuinely needs two dimensions: data tables, maps,
diagrams, video, games, and code blocks where indentation carries meaning. Those
scroll inside their own container. The page around them still reflows.

Why each number is what it is: [references/sources.md](references/sources.md).

## Units

| Never | Instead | Because |
|-------|---------|---------|
| `font-size: 14px` | `font-size: var(--t-body)` in `rem` | a px type scale ignores a reader who has raised their browser's default font size |
| a second type scale inside a breakpoint | one `clamp()` scale | the scale then moves continuously and the breakpoint disappears |
| `padding: 16px` | `padding: var(--s-4)` in `rem` | space that does not grow with text crushes enlarged type |
| `max-width: 640px` on prose | `max-width: 62ch` | measure is a count of characters, not a distance |
| `height: 100vh` | `height: 100dvh` | `100vh` is the *largest* viewport, so mobile browser chrome clips it on load |

**A px font-size does not fail WCAG 1.4.4.** Page zoom scales px, and the criterion
accepts any method that reaches 200%. The rule above stands on the reader's default
font size, which px ignores and zoom does not fix. Do not cite 1.4.4 against a px
size — see [references/sources.md](references/sources.md#the-144-correction).

### The fluid step

To scale a value from `S1` at viewport `V1` to `S2` at viewport `V2`, all in px:

```
slope     = (S2 - S1) / (V2 - V1)
intercept = S1 - slope * V1
css       = clamp( S1rem, <intercept/16>rem + <slope*100>vw, S2rem )
```

Worked, for body text 16px at a 320px viewport rising to 18px at 1240px:

```css
/* slope 2/920 = 0.0021739 -> 0.217vw;  intercept 16 - 0.696 = 15.304px = 0.957rem */
--t-body: clamp(1rem, 0.957rem + 0.217vw, 1.125rem);
```

The minimum and maximum are in `rem` so the reader's default font size still
reaches them. A `clamp()` bounded in `px` ignores that setting exactly as a plain
`px` size does.

Generate a whole scale at utopia.fyi rather than doing this by hand per step.

## Layout

Let the content pick where it breaks.

```css
/* A row that becomes a column when its items stop fitting. No breakpoint. */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(28ch, 100%), 1fr));
  gap: var(--s-4);
}
```

`min(28ch, 100%)` rather than a bare `28ch`: a bare minimum wider than the
container overflows it, which is the single most common way an `auto-fit` grid
breaks at 320px.

Flex and grid children default to `min-width: auto`, so a long word or a wide
table refuses to shrink and pushes the page sideways. Give any child that holds
text or a scroller `min-width: 0`.

### A value that wraps keeps its label in line

`white-space: nowrap` is not how you hold a value on one line. In a grid of
repeated cells you will not catch it at any width you are likely to try: it
gives way only at the narrow end, where the column finally measures thinner
than the string and the body starts scrolling sideways.

Let the value wrap, and reserve its height so a cell that takes two lines does
not drop its label below the labels beside it:

```css
.readout .n {
  white-space: normal;
  overflow-wrap: break-word;
  line-height: 1.5;
  min-height: 3em;   /* engines with no lh unit */
  min-height: 2lh;
}
```

Write the reservation in `lh`, which is the element's own computed line height
and so tracks the reader's text-spacing override. A height you sized against a
line height of your own choosing comes up short the moment that override sets
`line-height: 1.5`. Declare that same 1.5 here and the `em` fallback lands on
two lines exactly, which is what makes it safe to ship beside the `lh`.

Check whether you need the reservation at all before you add it. Where the
grid's own column minimum is already wider than the longest string, the value
cannot wrap until the grid has collapsed to one column, and a single cell per
row has no neighbour to fall out of line with. Measure the two against each
other rather than assuming either:
[references/sources.md](references/sources.md), "The cost of holding a line".

### Check the narrow end with the text doubled, not only at the default size

A reader who raises their browser's default font size doubles every `rem` on the
page. The viewport does not move with them, so at 320 CSS pixels the space and
the type go on growing into a column that can spare neither, and the body starts
scrolling sideways. That is a 1.4.10 failure reached through 1.4.4, at a width
nobody designed and a size nobody tested.

Three things break this way, and each is a rule from further up this page.

**Padding in `rem` eats the column it sits in.** Cap it against the viewport, so
it stops growing where the viewport cannot spare it:

```css
.hero { padding-inline: min(var(--s-10), 6vw); }
```

**A `clamp()` floor in `rem` is a floor the viewport cannot honour.** The `vw`
term falls as the viewport narrows and the floor does not, so the browser takes
the floor and the longest string overruns its line. Lower the floor until that
string fits. The desktop size does not move, because the preferred term already
sits above the floor there.

**A heading at a doubled size holds words wider than its column.** Give every
heading and any unbroken value `overflow-wrap: break-word`.

Check 2 of the review checklist is where all three surface, and it is the one to
run before trusting a page at 320. The measurements:
[references/sources.md](references/sources.md), "Space that grows while the
viewport does not".

### Which query

| The behaviour belongs to | Use | Note |
|---|---|---|
| one component, wherever it sits | `@container` | set `container-type: inline-size` on its wrapper |
| the page's own skeleton | `@media` | the shell, not the pieces inside it |

Container queries are baseline across Chrome, Firefox, Safari, and Edge. Prefer
them: the same block appears in a wide slot and a narrow one, and a viewport
query cannot tell those apart.

```css
.card-wrap { container-type: inline-size; container-name: card; }
@container card (min-width: 34rem) { .card { grid-template-columns: 1fr 2fr; } }
```

Name your containers. An unnamed `@container` binds to the nearest container
ancestor, which is not always the one you meant.

Where a media query is genuinely right, write the breakpoint in `em` and put it
where the content stops fitting, not at a device width. An `em` breakpoint scales
with the reader's text size; a `px` one does not.

### The body never scrolls sideways

Wide content scrolls inside its own container, and that container is reachable by
keyboard:

```css
.tablewrap { overflow-x: auto; }
.tablewrap:focus-visible { outline: 2px solid var(--accent); }
```

Set `tabindex="0"` on a scrolling container so a keyboard reader can reach it.

## Disclosure — the decision fluid layout cannot make

Fluid layout decides how things fit. It never decides what belongs on screen.

A filter set, a toolbar, or a nav with more than about four controls fills a
narrow screen before the reader has seen anything you built. Measured on one
build: a filter bar 429px tall on an 844px screen, with the first content block
starting at 809px. Every value in it was already a token.

```css
/* Collapsed by default; the container decides when it may open flat. */
details.filters > summary { display: block; }
@container shell (min-width: 48rem) {
  details.filters > summary { display: none; }
  details.filters > .body   { display: flex; flex-wrap: wrap; }
}
```

Rules:

- Default to collapsed. Expanded is what you earn with space, not what you start
  from.
- Use `<details>`/`<summary>`, which gives you keyboard operation and the
  expanded state for free. A `<div>` with a click handler gives you neither.
- The summary says what is inside and what is active — "Filters · 2 applied" —
  so a reader knows whether opening it matters.
- The trigger is at least 24×24, and 44×44 if it is a primary action.

## The review checklist

Run against the built page. Every item resolves to **DEMONSTRATED** with the
artifact named, **N/A** with one line of why, or **`hypothesis:`** when you
suspect a problem and could not produce the artifact. There is no fourth state,
and "it looks fine" is not one of them.

```
1  REFLOW 320     At 320 CSS px wide, does the body scroll sideways?
   artifact       scrollWidth vs innerWidth at 320, or a 320-wide render.
                  Any two-dimensional scrolling outside an exempt element
                  is a FINDING.  (WCAG 1.4.10)

2  FONT PREF      Force the root font size to 200% and render. Does the text
   artifact       actually grow, and does anything clip when it does?
                  the injected render. Text that does not grow means the
                  scale is not in rem — the dynamic half of check 4, and the
                  proof that a static px count actually matters. Cite no
                  criterion here: this is not WCAG 1.4.4.

3  TEXT SPACING   Inject the four overrides and render. Does anything clip,
   artifact       overlap, disappear, or fall out of line with the cells
                  beside it?
                  the injected render.  (WCAG 1.4.12)

4  UNIT AUDIT     Count px against rem for font-size, padding, and margin.
   artifact       the two counts. Any px font-size is a FINDING.

5  BREAKPOINTS    List every @media width and its unit. A px breakpoint at
   artifact       a device width is a FINDING; name the content that
                  stops fitting there instead.

6  FIRST SCREEN   At the narrowest width, does any content reach the first
   artifact       screenful? A render at that width and the real viewport
                  HEIGHT — never a tall strip, which has no fold.
                  No content above the fold is a FINDING.

7  TARGETS        Smallest interactive element, measured.
   artifact       its computed box. Under 24x24 is a FINDING.  (WCAG 2.5.8)

8  SIDEWAYS       List every element wider than the viewport. One that is
   artifact       not inside its own scrolling container is a FINDING; it is
                  what makes the body scroll and what check 1 reports.
                  the list, with each element's right edge.
```

Close with the count: `8 checks. DEMONSTRATED n  N/A n  hypothesis n. findings: n`.

### Getting the artifacts

Four artifacts cover the eight checks. Produce each once and read it against the
checks named beside it.

```
width strip            checks 1, 5, 8    many widths in one render
real-viewport render   check 6           one width, the REAL device height
root-font-size render  check 2           the built file with 200% root size
text-spacing render    check 3           the built file with the four overrides
computed boxes         checks 4, 7       measured, not looked at
```

**The width strip.** One render holds many widths at once — iframes each get their
own viewport, so media and container queries evaluate correctly inside them:

```bash
# strip.html holds one <iframe src="page.html" width="320|390|600|900"> per width
~/.claude/skills/responsive-design/scripts/render.sh \
  --url strip.html --out strip.png --width 2280 --height 800
```

Every render in this skill goes through that script. It kills Chrome once the
output stops growing, because Chrome does not exit after writing the file, and a
command that waits for it pays its whole timeout instead of the two seconds the
render takes. Run its tests once before trusting it:
`python3 ~/.claude/skills/responsive-design/scripts/test_render.py`.

**One Chrome window per width cannot test the narrow end.** Chrome clamps
`--window-size` to a 500-pixel minimum, so a window asked for 320, 390 or 480
renders at 500 and reports a clean pass for a page nobody tested. The iframe strip
is the only way to reach the two narrowest widths this skill requires. `render.sh`
refuses a `--width` below 500 rather than let the clamp through quietly.

**Fonts that arrive over the network change what you measured.** A page declaring
webfaces lays out one way before its glyphs land and another way after, so a
capture taken in between belongs to a page no reader will see. Add `--fonts` to a
dom pass and read the receipt, which reports faces downloaded over faces declared:

```
render: ok out=dom.html bytes=191568 width=1440 elapsed=1s fonts=8/57
```

Two captures are comparable only when their receipts match. A page that declares
webfaces and reports `fonts=0/0` never reached the font host at all. Do not reach
for `document.fonts.status` or `document.fonts.check()` instead — both report
success with the font hosts blocked. See
[references/sources.md](references/sources.md), "Renders are not reproducible".

**The strip cannot serve check 6.** Its iframes have a fixed height, so it has no
fold — the same defect as a tall phone-width strip. Check 6 needs its own render at
one width and the real device height.

**The two injected renders.** Copy the built file, insert a `<style>` before
`</head>`, and render the copy. Never edit the original.

```html
<!-- check 2, the root font size a reader may have raised -->
<style>html{font-size:200%!important}</style>

<!-- check 3, the four WCAG 1.4.12 overrides -->
<style>
*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}
p{margin-bottom:2em!important}
</style>
```

Run check 3 a second time with every webface swapped for its fallback. The two
conditions compound: each one on its own widens a string by a little, and a
fallback face is wider per character than the one you chose, so the pair
overruns a column that either alone still fits.

**Measured, not looked at.** For checks 1, 4, 7 and 8, read the numbers. Where a
devtools MCP is available, read `documentElement.scrollWidth` against `innerWidth`
and the computed boxes directly; otherwise count units in the source for check 4.

## What a headless render cannot show you

Say these are untested rather than passing them.

- **`dvh` behaviour.** Desktop emulation has no address bar to collapse, so
  `svh`, `lvh`, and `dvh` all report the same value. A `dvh` bug does not
  reproduce anywhere but a real device.
- **Touch.** Hit targets, hover states that have no touch equivalent, and
  scroll-versus-drag conflicts.
- **The reader's own settings.** OS-level text size, reduced motion, and forced
  colors, unless you emulate each one deliberately.

## What this skill does not cover

- Anything inside a chart — form, colour, marks, tooltips, the accessibility
  pass. `dataviz` owns all of it, including the chart container's own sizing.
- A brand's fonts, colours, or tokens. That is whichever skill your private
  routing names.
- What goes on the page and in what order. `writing-prose` owns composition.
