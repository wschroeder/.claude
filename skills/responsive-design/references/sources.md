# Sources — where each number and rule comes from

- [The standards, and why 320 is the floor](#the-standards)
- [Why fluid beats a second scale at a breakpoint](#fluid-type)
- [Container queries over media queries](#container-queries)
- [Viewport units](#viewport-units)
- [The 1.4.4 correction — an error this file shipped](#the-144-correction)
- [The layout philosophy](#the-layout-philosophy)
- [The failure that produced the disclosure rule](#the-disclosure-rule)

## The standards

Every number in the skill's table is a WCAG success criterion. None was chosen
by anyone on this side of the screen, which is the point: a device width is an
opinion and a criterion is not.

**SC 1.4.10 Reflow (AA).** Normative text: "Content can be presented without
loss of information or functionality, and without requiring scrolling in two
dimensions for: Vertical scrolling content at a width equivalent to 320 CSS
pixels; Horizontal scrolling content at a height equivalent to 256 CSS pixels.
Except for parts of the content which require two-dimensional layout for usage
or meaning."

The W3C Understanding page states that 320 CSS pixels "is equivalent to a
starting viewport width of 1280 CSS pixels wide at 400% zoom". This is the
sentence that settles the argument about picking device widths. The criterion
is not about phones at all — it is about a low-vision reader zooming a desktop
browser to 400%, which collapses a 1280px viewport to a 320px one. A page that
reflows at 320 serves that reader and every phone as a side effect.

Named exceptions: images, maps, diagrams, video, games, presentations, data
tables, code blocks where indentation carries meaning, and interfaces that must
keep a toolbar in view. The page around such an element still reflows; the
element scrolls inside its own container.

Named failure: F102, content disappearing when reflowed. Hiding something at a
narrow width is not passing the criterion.

- https://www.w3.org/WAI/WCAG21/Understanding/reflow.html

**SC 1.4.4 Resize Text (AA).** Text resizes to 200% without loss of content or
functionality. The implementation guidance names the cause directly: avoid
absolute sizing, because pixel font sizes prevent text from resizing in some
browsers. This is why the skill forbids a `px` font-size outright rather than
discouraging it.

**SC 1.4.12 Text Spacing (AA).** Line height at least 1.5, paragraph spacing at
least 2em, letter spacing at least 0.12em, word spacing at least 0.16em. The
criterion does not require a page to use these values. It requires the page to
survive a reader who imposes them. It is a resilience test, and it is the one
nobody runs, which is why it is check 3 rather than a footnote.

**SC 2.5.8 Target Size (Minimum), AA, new in WCAG 2.2.** Pointer targets at
least 24×24 CSS pixels, measured on the hit area rather than the painted
graphic. Five exceptions: adequate spacing between small targets, an equivalent
control elsewhere, inline targets in a run of text, a size the user agent sets,
and an essential presentation. **SC 2.5.5 Target Size (Enhanced), AAA** asks 44×44.

## Fluid type

A breakpoint that swaps one type scale for another produces a jump: the reader
drags a window one pixel and the heading changes size. `clamp()` removes the
jump by making the scale a continuous function of viewport width.

The rule that matters is that the minimum and maximum are in `rem`, so the
reader's own default font size reaches them. A `clamp()` bounded in `px` ignores
that setting exactly as a bare `px` size does. This is not a 1.4.4 question —
see the correction below.

utopia.fyi generates a whole scale, taking a type ratio and two viewport
anchors and emitting the `clamp()` custom properties. Prefer it to computing
each step by hand; the skill gives the formula so a single value can be derived
or checked without the tool.

- https://utopia.fyi/blog/clamp/
- https://css-tricks.com/consistent-fluidly-scaling-type-and-spacing/

## Container queries

Baseline across Chrome 105+, Firefox 110+, Safari 16+, and Edge 105+, roughly
93% of global usage as of 2026. Safe for production.

The division of labour that the current guidance settles on: behaviour that
belongs to a component goes to a container query, behaviour that belongs to the
page skeleton goes to a media query, and most real projects need both. The
argument for preferring the container query is that a component does not know
where it has been placed — the same card sits in a wide slot on one page and a
narrow column on another, and a viewport query cannot tell those two apart.

Two cautions from the same sources. Name your containers, or a nested component
binds to the wrong ancestor. And container *style* queries, as opposed to size
queries, are still only partially supported.

- https://blog.logrocket.com/container-queries-2026/

## Viewport units

`svh`, `lvh`, and `dvh` reached Baseline Widely Available in June 2025, about
95% of users by early 2026.

`100vh` resolves against the *largest* viewport — the one with browser chrome
hidden. On load, mobile chrome is visible, so a `100vh` section is taller than
the screen and its bottom is clipped. `svh` is the small viewport with chrome
shown, `lvh` the large one with it hidden, and `dvh` tracks the change live.

The testing caution is the important part, and it is why the skill has a
section listing what a render cannot show: dvh bugs do not reproduce in a
desktop browser, DevTools device emulation included, because there is no
address bar to collapse. All three units report the same value there. Animating
a height to `100dvh` also jitters, since the unit changes during scroll — use a
fixed unit or `svh` inside an animation.

- https://web.dev/blog/viewport-units

## The 1.4.4 correction

The first version of this skill said a px font-size fails SC 1.4.4 Resize Text.
That is wrong, and the error shipped in three places before anyone caught it.

1.4.4 is permissive about *how* text reaches 200%. Resizing text alone and zooming
the whole page both satisfy it, and page zoom scales px perfectly well. Eric
Eggert states the consequence directly: "if it is possible to resize the text to
200% using any method, it cannot be a failure of 1.4.4." A px-sized page that
zooms to 200% passes.

What px actually costs you is the reader who has raised their browser's default
font size. Zoom does not help them, because they did not zoom — they set a
preference, and a px page ignores it. That is a real usability failure and a good
reason to ban px font sizes. It is not a WCAG AA failure, and citing 1.4.4 for it
is the kind of borrowed authority that gets a whole checklist distrusted once
someone checks one line of it.

Reflow at 320 is where zoom does bite, because 320 CSS px is a 1280px viewport at
400%. That criterion is the one a px-heavy page is likely to actually fail.

- https://yatil.net/blog/resize-text-reflow

## The layout philosophy

Andy Bell's framing, from his 2022 talk and from Every Layout with Heydon
Pickering: be the browser's mentor, not its micromanager. Set base rules and
hints, then get out of the way and let the browser resolve the layout against
conditions you cannot enumerate. Every Layout describes its components as
existing in a quantum state, offering narrow and wide configurations at once,
resolved by the space actually available and the intrinsic width of the content.

This is the same idea as intrinsic web design, which Jen Simmons named: shift
work from the author to the browser by declaring what should happen rather than
how, and let algorithms, the cascade, and the components do the rest.

- https://every-layout.dev/
- https://buildexcellentwebsit.es/

## The disclosure rule

This rule exists because of a specific build, not from the literature.

A dashboard was built entirely from design tokens, passing its own scale gate
with zero literal values. On an 844px-tall screen its filter bar measured 429px,
51% of the first screenful, and the first content block began at 809px — so a
reader met a screen of filters and nothing else. Every value involved was
already a token, and no unit change would have altered the outcome, because
eight filter groups occupy the room eight filter groups occupy.

That is the boundary the skill draws: fluid layout decides how things fit, and
only disclosure decides what belongs on screen. Reaching for units when the
problem is disclosure is the mistake this section exists to prevent.


## Renders are not reproducible

Three renders of one unchanged dashboard produced three different results. Six
captures taken with the output-polling wrapper were byte-identical to each other;
two taken with the font hosts mapped to 127.0.0.1 were byte-identical to each
other and different from the first six; one taken by waiting for Chrome to exit
matched neither, differing from the webfont group by 88,330 pixels and from the
blocked group by 124,134.

The page had no randomness and disabled transitions. It linked three families
from Google Fonts with `display=swap`. With the font hosts mapped to 127.0.0.1,
`document.fonts` held 0 faces against 57, and the page came out 71 pixels shorter.

Which number to read matters. `document.fonts.size` counts faces the stylesheet
*declares*, so it reaches 57 the moment that stylesheet parses and says nothing
about glyphs. Counting the faces whose own `status` is `loaded` gives the
downloaded total, which on that page was 8 of the 57. Two other candidates are
worth naming only to rule them out: `document.fonts.status` reads `loaded` and
`document.fonts.check("1em 'Host Grotesk'")` returns `true` even with the hosts
blocked, because a fallback can render the text.

That is why the receipt carries a downloaded-over-declared count rather than only
a byte count. The harness cannot make the network fast, but it can record what
had arrived, so two captures that disagree can be told apart from two that agree.

## Chrome's minimum window width

`--window-size=320`, `390` and `480` each rendered at `innerWidth: 500`;
`--window-size=600` rendered at 600. A single Chrome window therefore cannot
produce the 320-pixel viewport that WCAG 1.4.10 requires, and a run that asks
for one gets a silent pass at 500 instead of a failure. The iframe strip exists
for this reason as much as for media and container query evaluation.
