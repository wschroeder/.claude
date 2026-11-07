# chartkit — what each function takes, and the two ways to call it wrong

1. Concatenate `assets/chartkit.js` into the page's `<script>` ahead of the chart bodies, and write each body to draw only its own marks; the function that sizes a band is the one that draws into it.
2. Take every look-and-feel decision from `dataviz`; chartkit only measures and places what that skill decided.

## Contents

- [The two chart forms](#the-two-chart-forms)
- [Ticks](#ticks)
- [The hover layer, and the field name that broke a build](#the-hover-layer-and-the-field-name-that-broke-a-build)
- [Pointer targets](#pointer-targets)
- [What the page owes the library](#what-the-page-owes-the-library)

## The two chart forms

1. Use `CK.cartesian(host, spec)` for a value axis down the left and a value or category axis along the bottom: pass the tick values, a formatter per axis, the axis titles, and the radius of the largest mark you will draw; it returns the plot box and a scale for each direction.
2. Use `CK.rows(host, spec)` for horizontal rows sharing one axis along the bottom, such as ranked bars, dots on a stem, or a mean against a range: pass one entry per row with a label and a value string, the tick values, and the axis title; it returns the plot box, a scale, the chart's own width, and where each row sits.
3. Leave to both forms whether a label sits beside or above its mark, whether the value column is drawn, which tick labels are drawn, and how tall the axis band is for a wrapped title.

## Ticks

1. Use `CK.niceTicks(max, count)` for an axis from zero to a maximum.
2. Use `CK.rangeTicks(lo, hi, count)` for a range whose low end is not zero, as a scatter's horizontal axis usually needs.
3. Pass inputs unguarded; a zero maximum, a reversed range, or a range too small for a step returns a single tick.
4. Ask for the ticks the data deserves, and let the chart label every nth tick where the plot is narrow; every tick keeps its gridline, and the first keeps its label.

## The hover layer, and the field name that broke a build

1. Write each tooltip line as `{ key, val, tail }`, and put the figure in `val`, never in a field named `value`.
2. Use `CK.hoverable(node, lines)` to wire pointer and keyboard focus onto one node, and `CK.showTip(ev, lines)` to fill the tooltip: `key` is the quiet label before the figure, `tail` the unit after it, and a line with only `val` is the heading.
3. Check the tooltips by driving a real pointer at the page, because no static render shows a missing figure.

## Pointer targets

1. Use `CK.rowHit(box, i, lines, label)` for each row of a `CK.rows` chart; it covers the row, never falls below the 24 CSS pixels WCAG 2.2 asks of a pointer target, sets `role` and `aria-label`, and wires the hover layer.
2. Call it after drawing that row's marks, because it goes on the end of the SVG.
3. Never make the marks themselves the hover targets.

## What the page owes the library

1. Define the four classes it reads type sizes from — `.ax` for tick labels, `.cat` for category labels, `.val` for value labels, and `.axtitle` for axis titles — with sizes from the tokens Section 6 fixed.
2. Provide one element with `id="tip"` for the hover layer.
3. Set letter-spacing and word-spacing for those classes only on the class, on `body`, or on `*`, never on a container around the chart, because chartkit measures them from a probe node it draws in the document body.
4. Read `scripts/test_chartkit.py`, which draws both forms at 320, 768, and 1440 in real Chrome, for what each spec accepts.
