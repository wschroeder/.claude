# chartkit — what each function takes, and the two ways to call it wrong

`assets/chartkit.js` beside this skill sizes each band of a chart from the width
the browser gives the strings that will sit in that band, and the function that
sizes a band is the one that draws into it. Concatenate it into the page's
`<script>` ahead of the chart bodies, and write each body to draw only its own
marks.

`dataviz` decides what a chart looks like. Everything here measures and places
what that skill already decided, so every answer in a spec below came from there.

## Contents

- [The two chart forms](#the-two-chart-forms)
- [Ticks](#ticks)
- [The hover layer, and the field name that broke a build](#the-hover-layer-and-the-field-name-that-broke-a-build)
- [Pointer targets](#pointer-targets)
- [What the page owes the library](#what-the-page-owes-the-library)

## The two chart forms

`CK.cartesian(host, spec)` draws a value axis down the left and a value or
category axis along the bottom. It takes the tick values, a formatter per axis,
the axis titles, and the radius of the largest mark you will draw; it returns the
plot box and a scale for each direction.

`CK.rows(host, spec)` draws horizontal rows sharing one axis along the bottom:
ranked bars, dots on a stem, a mean against a range. It takes one entry per row
carrying a label and a value string, the tick values, and the axis title; it
returns the plot box, a scale, the chart's own width, and where each row sits.

Both settle whether a label fits beside its mark or goes above it, whether the
value column has room to be drawn at all, which tick labels there is room to
draw, and how tall the axis band must be for a title that wrapped onto a second
line.

## Ticks

`CK.niceTicks(max, count)` walks from zero to a maximum.

`CK.rangeTicks(lo, hi, count)` covers a range whose low end is not zero, which is
what a scatter's horizontal axis usually needs — humidity from 30 to 92, altitude
from 2 to 2,240.

Neither asks the caller to guard its inputs. A maximum of zero, a reversed range,
a range too small to derive a step from: each comes back as a single tick rather
than as an empty list that leaves an axis with no gridlines and no labels.

You pass tick values, and neither function knows the width the plot ends up with,
so a narrow plot can receive more labels than it has room for. Both chart forms
label every nth tick rather than drawing them on top of each other, choosing the
smallest n whose labels clear each other. Every tick keeps its gridline, and the
first tick keeps its label, so the axis still states where it starts. Ask for the
ticks the data deserves and let the chart drop what will not fit.

## The hover layer, and the field name that broke a build

**A tooltip line is `{ key, val, tail }`, and the figure goes in `val`.**

`CK.hoverable(node, lines)` wires pointer and keyboard focus onto one node.
`CK.showTip(ev, lines)` fills the tooltip from those lines: `val` is the figure,
`key` the quiet label before it, `tail` the unit after it, and a line carrying
only `val` is the heading.

Name the field `value` instead and every tooltip on the page draws its labels
with no numbers beside them. No static render shows that. One build shipped it
all the way to its Section 9 review and found it only by driving a real pointer
at the finished page.

## Pointer targets

`CK.rowHit(box, i, lines, label)` builds the invisible pointer target for one row
of a `CK.rows` chart. It covers the row and never falls below the 24 CSS pixels
WCAG 2.2 asks of a pointer target, sets `role` and `aria-label`, and wires the
hover layer onto itself.

Call it after drawing that row's marks: it goes on the end of the SVG, so marks
drawn afterwards would sit on top of it and take the pointer back.

A bar is thinner than the row it sits in and the reader is aiming at the row, so
making the marks themselves hoverable is what leaves a chart full of 14-pixel
targets.

## What the page owes the library

Four classes it reads its type sizes off — `.ax` for tick labels, `.cat` for
category labels, `.val` for value labels, and `.axtitle` for axis titles — and
one element with `id="tip"` for the hover layer. Give those classes their sizes
from the tokens Section 6 fixed.

It reads letter-spacing and word-spacing off those same four classes and adds
both to every width it measures, so a reader who turns on the WCAG 1.4.12
text-spacing override gets bands sized for the strings they actually see. It
learns all six numbers by drawing one probe node per class into the document
body and asking the browser what it computed, which is the one thing to know
when you write the CSS: a rule on the class, on `body`, or on `*` reaches that
probe, and a rule on some container the chart happens to sit inside does not.
Measured on a chart inside a `letter-spacing: 0.12em` wrapper: a four-character
tick label drew 34.09 wide and measured 26.4.

`scripts/test_chartkit.py` draws both forms at 320, 768, and 1440 in real Chrome.
Read it for what each spec accepts.
