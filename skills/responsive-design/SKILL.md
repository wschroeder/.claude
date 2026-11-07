---
name: responsive-design
description: Makes a page work on a phone and a desktop without naming device widths — type and space in rem with clamp() so one fluid scale replaces a second scale hand-written at a breakpoint, layout that wraps on content with auto-fit and flex-wrap, a container query where a component should answer to its own column rather than the window, dvh instead of vh, and a disclosure control where fluid layout would otherwise fill the screen with widgets. Carries the numbers the published standards already set rather than invented ones: reflow at 320 CSS pixels, text resize to 200%, the four text-spacing overrides, and 24-pixel pointer targets. Ends in a review checklist naming what to test, at what width, and what a headless render cannot show you at all. Use when a page has to work on mobile and desktop, when CSS breakpoints, fluid type, viewport units, media or container queries are in question, and when reviewing a built page for how it behaves at widths nobody designed for.
---

# responsive-design

1. Set constraints and let the browser do layout; never name a device width.
2. If the page does not fit, fix it with fluid units and content-driven wrapping.
3. If the page fits but holds too much, such as eight controls on a phone, fix it with disclosure, never with smaller units.

## The numbers you do not have to invent

1. Take every width and size from this table, never from argument; each is testable.

| What | Number | Source |
|------|--------|--------|
| Reflow, vertical scrolling content | **320 CSS px** wide, no horizontal scrolling | WCAG 1.4.10 AA |
| Reflow, horizontal scrolling content | **256 CSS px** tall | WCAG 1.4.10 AA |
| Text resize | **200%**, no loss of content or function | WCAG 1.4.4 AA |
| Text spacing the layout must survive | line-height **1.5**, paragraph **2em**, letter **0.12em**, word **0.16em** | WCAG 1.4.12 AA |
| Pointer target | **24×24 CSS px** | WCAG 2.5.8 AA |
| Pointer target, preferred | **44×44 CSS px** | WCAG 2.5.5 AAA |

2. Treat 320 as a 1280px desktop viewport at 400% zoom, not as a phone.
3. Let content that genuinely needs two dimensions, such as data tables, maps, diagrams, video, games, and code blocks where indentation carries meaning, scroll inside its own container under the 1.4.10 exemption; the page around it still reflows.

## Units

| Never | Instead | Because |
|-------|---------|---------|
| `font-size: 14px` | `font-size: var(--t-body)` in `rem` | a px type scale ignores a reader who has raised their browser's default font size |
| a second type scale inside a breakpoint | one `clamp()` scale | the scale then moves continuously and the breakpoint disappears |
| `padding: 16px` | `padding: var(--s-4)` in `rem` | space that does not grow with text crushes enlarged type |
| `max-width: 640px` on prose | `max-width: 62ch` | measure is a count of characters, not a distance |
| `height: 100vh` | `height: 100dvh` | `100vh` is the *largest* viewport, so mobile browser chrome clips it on load |

1. Never cite WCAG 1.4.4 against a px font-size: page zoom scales px. Rest the rule on the reader's default font size, which px ignores.

### The fluid step

1. To scale a value from `S1` at viewport `V1` to `S2` at viewport `V2`, all in px, use:

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

2. Write the minimum and maximum in `rem`, never `px`, so the reader's default font size still reaches them.
3. Generate a whole scale at utopia.fyi rather than doing this by hand per step.

## Layout

1. Let the content pick where it breaks.

```css
/* A row that becomes a column when its items stop fitting. No breakpoint. */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(28ch, 100%), 1fr));
  gap: var(--s-4);
}
```

2. Write the minimum as `min(28ch, 100%)`, never a bare `28ch`, because a bare minimum wider than the container overflows it.
3. Give any flex or grid child that holds text or a scroller `min-width: 0`, because the default `min-width: auto` refuses to shrink and pushes the page sideways.

### A value that wraps keeps its label in line

1. Never hold a value on one line with `white-space: nowrap`; it gives way only at the narrow end, where the body starts scrolling sideways.
2. Let the value wrap, and reserve its height so a cell that takes two lines does not drop its label below the labels beside it:

```css
.readout .n {
  white-space: normal;
  overflow-wrap: break-word;
  line-height: 1.5;
  min-height: 3em;   /* engines with no lh unit */
  min-height: 2lh;
}
```

3. Write the reservation in `lh` so it tracks the reader's text-spacing override, and declare `line-height: 1.5` so the `em` fallback lands on two lines exactly.
4. Before you add the reservation, measure the grid's column minimum against the longest string; if the minimum is wider, the value cannot wrap before the grid collapses to one column, so skip it.

### Check the narrow end with the text doubled, not only at the default size

1. Test 320 CSS pixels with the reader's default font size doubled, because every `rem` doubles while the viewport stays put.
2. Cap `rem` padding against the viewport, so it stops growing where the viewport cannot spare it:

```css
.hero { padding-inline: min(var(--s-10), 6vw); }
```

3. Lower a `clamp()` floor in `rem` until the longest string fits at 320, because the floor does not fall with the `vw` term; the desktop size does not move.
4. Give every heading and any unbroken value `overflow-wrap: break-word`.
5. Run check 2 of the review checklist before trusting a page at 320; all three surface there.

### Which query

| The behaviour belongs to | Use | Note |
|---|---|---|
| one component, wherever it sits | `@container` | set `container-type: inline-size` on its wrapper |
| the page's own skeleton | `@media` | the shell, not the pieces inside it |

1. Prefer container queries, because a viewport query cannot tell a wide slot from a narrow one; they are baseline across Chrome, Firefox, Safari, and Edge.

```css
.card-wrap { container-type: inline-size; container-name: card; }
@container card (min-width: 34rem) { .card { grid-template-columns: 1fr 2fr; } }
```

2. Name your containers, because an unnamed `@container` binds to the nearest container ancestor.
3. If a media query is genuinely right, write the breakpoint in `em` and put it where the content stops fitting, not at a device width.

### The body never scrolls sideways

1. Scroll wide content inside its own container, and make that container reachable by keyboard:

```css
.tablewrap { overflow-x: auto; }
.tablewrap:focus-visible { outline: 2px solid var(--accent); }
```

2. Set `tabindex="0"` on a scrolling container so a keyboard reader can reach it.

## Disclosure — the decision fluid layout cannot make

1. Collapse a filter set, a toolbar, or a nav with more than about four controls on a narrow screen.

```css
/* Collapsed by default; the container decides when it may open flat. */
details.filters > summary { display: block; }
@container shell (min-width: 48rem) {
  details.filters > summary { display: none; }
  details.filters > .body   { display: flex; flex-wrap: wrap; }
}
```

Rules:

- Default to collapsed, and expand only where space allows.
- Use `<details>`/`<summary>`, which gives you keyboard operation and the
  expanded state; never a `<div>` with a click handler.
- Make the summary say what is inside and what is active, such as "Filters · 2 applied".
- Make the trigger at least 24×24, and 44×44 if it is a primary action.

## The review checklist

1. Run the checklist against the built page.
2. Resolve every item to **DEMONSTRATED** with the artifact named, **N/A** with one line of why, or **`hypothesis:`** when you suspect a problem and could not produce the artifact; "it looks fine" is not a state.

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

3. Close with the count: `8 checks. DEMONSTRATED n  N/A n  hypothesis n. findings: n`.

### Getting the artifacts

1. Produce each artifact once and read it against the checks named beside it.

```
width strip            checks 1, 5, 8    many widths in one render
real-viewport render   check 6           one width, the REAL device height
root-font-size render  check 2           the built file with 200% root size
text-spacing render    check 3           the built file with the four overrides
computed boxes         checks 4, 7       measured, not looked at
```

2. Build the width strip as one render of many iframes, each with its own viewport:

```bash
# strip.html holds one <iframe src="page.html" width="320|390|600|900"> per width
~/.claude/skills/responsive-design/scripts/render.sh \
  --url strip.html --out strip.png --width 2280 --height 800
```

3. Send every render through `render.sh`, and run its tests once before trusting it: `python3 ~/.claude/skills/responsive-design/scripts/test_render.py`.
4. Reach widths under 500 only through the iframe strip, because Chrome clamps `--window-size` to 500 and `render.sh` refuses a `--width` below it.
5. Add `--fonts` to a dom pass for a page that declares webfaces, and read the receipt, which reports faces downloaded over faces declared:

```
render: ok out=dom.html bytes=191568 width=1440 elapsed=1s fonts=8/57
```

6. Compare two captures only when their receipts match. Treat `fonts=0/0` on a page that declares webfaces as a render that never reached the font host.
7. Never use `document.fonts.status` or `document.fonts.check()` instead, because both report success with the font hosts blocked.
8. Give check 6 its own render at one width and the real device height, because the strip's fixed-height iframes have no fold.
9. For the two injected renders, copy the built file, insert a `<style>` before `</head>`, and render the copy; never edit the original.

```html
<!-- check 2, the root font size a reader may have raised -->
<style>html{font-size:200%!important}</style>

<!-- check 3, the four WCAG 1.4.12 overrides -->
<style>
*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}
p{margin-bottom:2em!important}
</style>
```

10. Run check 3 a second time with every webface swapped for its fallback, because the wider fallback and the spacing overrides compound.
11. Read the numbers for checks 1, 4, 7, and 8 rather than judging by eye. If a devtools MCP is available, read `documentElement.scrollWidth` against `innerWidth` and the computed boxes directly; otherwise count units in the source for check 4.

## What a headless render cannot show you

1. Report these as untested rather than passing them.

- **`dvh` behaviour.** Desktop emulation has no address bar to collapse, so
  `svh`, `lvh`, and `dvh` all report the same value.
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
