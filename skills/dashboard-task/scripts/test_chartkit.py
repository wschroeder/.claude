"""Tests for chartkit.js, the chart geometry and drawing library.

Every case runs in real headless Chrome through render.sh, because the thing
under test is text measurement: the library sizes each band of a chart from the
width the browser actually gives the strings that will sit in it. A stub
measurer would let the library agree with itself and still ship a label hanging
off the edge of its own SVG.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTKIT = os.path.normpath(os.path.join(HERE, "..", "assets", "chartkit.js"))
RENDER = os.path.normpath(
    os.path.join(HERE, "..", "..", "responsive-design", "scripts", "render.sh"))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# The library reads its type sizes off these classes rather than carrying sizes
# of its own, so a page supplies them and this is the reference set.
PAGE_CSS = """
:root { --mark:#3b6ea5; --accent:#c8553d; --grid:#dfdcd4; --annot:#8a8a8a;
        --band:#e6e2f2; --ink:#1c1c1c; }
* { box-sizing: border-box; }
body { margin:0; font-size:16px; font-family: Inter, sans-serif; }
svg.chart { display:block; overflow:visible; }
.ax      { font: 400 11px 'DM Mono','Courier New',monospace; fill:#555; }
.cat     { font: 400 13px Inter, sans-serif; fill:#1c1c1c; }
.val     { font: 500 12px 'DM Mono','Courier New',monospace; fill:#1c1c1c; }
.axtitle { font: 500 10px 'DM Mono','Courier New',monospace;
           text-transform: uppercase; letter-spacing: 0.08em; fill:#666; }
.gridline { stroke: var(--grid); }
.axisline { stroke: #9a9a9a; }
#tip { position: fixed; left: 0; top: 0; max-width: 22rem; padding: 0.5rem 0.65rem;
       background: #fff; border: 1px solid #ccc; font-size: 12px; opacity: 0;
       pointer-events: none; }
#tip .k { color: #777; }
"""

# Reports what the browser laid out, not what the library predicted. `worst`
# is how far past each edge of the SVG the furthest text node reached.
HARNESS_JS = """
function report(o) { document.getElementById("ck-out").textContent = JSON.stringify(o); }
function bounds(svg, selector) {
  var W = +svg.getAttribute("width"), H = +svg.getAttribute("height");
  var worst = { left:0, right:0, top:0, bottom:0 }, escaped = [];
  Array.prototype.forEach.call(svg.querySelectorAll(selector || "text"), function (t) {
    var b = t.getBBox();
    var over = { left: -b.x, right: b.x + b.width - W,
                 top: -b.y, bottom: b.y + b.height - H };
    var out = false;
    ["left","right","top","bottom"].forEach(function (s) {
      if (over[s] > worst[s]) worst[s] = over[s];
      if (over[s] > 0.5) out = true;
    });
    if (out) escaped.push({ tag: t.tagName, text: t.textContent, x: b.x, y: b.y,
                            w: b.width, h: b.height, over: over });
  });
  return { width: W, height: H, worst: worst, escaped: escaped };
}
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>%s</style></head><body>
<div id="host"></div><div id="legend"></div><div id="table"></div>
<div id="tip"></div><pre id="ck-out"></pre>
<script>%s</script>
<script>%s</script>
<script>%s</script>
</body></html>
"""

OUT_BLOCK = re.compile(r'<pre id="ck-out">(.*?)</pre>', re.S)
ENTITIES = (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&amp;", "&"))


class Case(unittest.TestCase):
    """Renders one page per case. Chrome answers in one to two seconds because
    render.sh stops waiting once the DOM dump stops growing."""

    width = 900
    height = 700

    def setUp(self):
        if not os.path.exists(CHARTKIT):
            self.fail("no library at %s" % CHARTKIT)
        with open(CHARTKIT, encoding="utf-8") as f:
            self.library = f.read()
        self.dir = tempfile.mkdtemp(prefix="chartkit-test.")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def draw(self, case_js):
        """Run case_js against the library in Chrome, return what it reported."""
        page = os.path.join(self.dir, "case.html")
        dom = os.path.join(self.dir, "case.dom.html")
        with open(page, "w", encoding="utf-8") as f:
            f.write(PAGE % (PAGE_CSS, self.library, HARNESS_JS, case_js))
        proc = subprocess.run(
            [RENDER, "--url", page, "--out", dom, "--mode", "dom",
             "--width", str(self.width), "--height", str(self.height)],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(dom, encoding="utf-8") as f:
            found = OUT_BLOCK.search(f.read())
        self.assertIsNotNone(found, "the case reported nothing; a script threw")
        raw = found.group(1)
        for entity, char in ENTITIES:
            raw = raw.replace(entity, char)
        self.assertNotEqual(raw.strip(), "", "the case reported nothing; a script threw")
        return json.loads(raw)


class CartesianFits(Case):
    """A plot with a value axis down the left and a category or value axis
    along the bottom. Every band is sized from the strings that will be drawn
    in it, so a wide tick label widens the left band instead of hanging off
    the edge of the SVG."""

    def test_a_tick_label_far_wider_than_two_digits_still_fits_the_left_band(self):
        got = self.draw("""
          var box = CK.cartesian(document.getElementById("host"), {
            width: 520, height: 320,
            y: { ticks: [0, 400000, 800000, 1250000],
                 format: function (v) { return v.toLocaleString("en-US"); },
                 title: "seats sold" },
            x: { min: 0, max: 40, ticks: [0, 10, 20, 30, 40],
                 format: function (v) { return v.toFixed(0); },
                 title: "apparent temperature (\\u00b0C)" }
          });
          report({ bounds: bounds(box.svg), x0: box.x0, x1: box.x1 });
        """)
        self.assertEqual(got["bounds"]["escaped"], [])
        self.assertEqual(got["bounds"]["worst"]["left"], 0)


class RowsFit(Case):
    """Horizontal rows with a label gutter on the left and a value column on
    the right. The four row charts in the build this came from had each picked
    their own label-column cap — 0.46, 0.44, 0.42 and 0.46 of the width — and
    their own width below which labels move above their bars, at 27 base
    widths in three of them and 30 in the fourth. Nobody chose those
    differences, and text escaping the SVG at a narrow width is what they
    produced. One rule lives here instead."""

    def test_the_value_column_stays_inside_the_svg_however_long_the_values_are(self):
        """The escape this replaces: two of the four charts drew each row's
        value just past the end of its own mark, so a row whose mark nearly
        filled the plot pushed its value off the right edge. Here the column
        sits at the plot's right edge and the right padding is measured from
        the widest value that will go in it."""
        got = self.draw("""
          var rows = [["Kickoff hour", "1,250,000 seats"],
                      ["Venue altitude", "982,400 seats"],
                      ["Wind speed", "77,000 seats"]];
          var box = CK.rows(document.getElementById("host"), {
            width: 520,
            rows: rows.map(function (r) { return { label: r[0], value: r[1] }; }),
            ticks: [0, 1, 2, 3], tickFormat: function (v) { return v.toFixed(0); },
            title: "mean goals per match"
          });
          report({ bounds: bounds(box.svg), showValues: box.showValues,
                   stacked: box.stacked, x1: box.x1, padR: box.padR });
        """)
        self.assertTrue(got["showValues"], "the value column was dropped, so nothing was drawn in it")
        self.assertFalse(got["stacked"], "the labels stacked, so the gutter was not exercised")
        self.assertEqual(got["bounds"]["escaped"], [])

    def test_whether_labels_stack_follows_the_labels_not_the_width_alone(self):
        """One rule replaces two. The four charts this came from each capped
        the gutter's share of the width and, separately, stacked below a width
        measured in base units — so at 400px a chart with four-letter labels
        stacked them anyway and spent the vertical room for nothing. Both
        renders here are 400px wide and only the labels differ."""
        case = """
          var box = CK.rows(document.getElementById("host"), {
            width: 400,
            rows: LABELS.map(function (L) { return { label: L, value: null }; }),
            ticks: [0, 5, 10], tickFormat: function (v) { return v + "%"; },
            title: "share of goal variation explained"
          });
          report({ bounds: bounds(box.svg), stacked: box.stacked,
                   labelW: box.labelW, height: box.height });
        """
        short = self.draw(case.replace("LABELS", '["Rain", "Wind", "Heat"]'))
        long = self.draw(case.replace(
            "LABELS", '["Attendance against stadium capacity",'
                      ' "Apparent temperature at kickoff", "Day of the tournament"]'))
        self.assertFalse(short["stacked"], "four-letter labels stacked at 400px")
        self.assertGreater(short["labelW"], 0)
        self.assertTrue(long["stacked"], "labels far wider than the gutter cap kept a gutter")
        self.assertEqual(long["labelW"], 0)
        self.assertLess(short["height"], long["height"])
        self.assertEqual(short["bounds"]["escaped"], [])
        self.assertEqual(long["bounds"]["escaped"], [])


class CsvReading(Case):
    """A field holding a comma inside quotes shifts every column after it when
    the reader splits on commas, and the shift is silent: the row still parses,
    so a chart draws the wrong column against the right axis. CRLF endings hide
    it further by leaving a stray return on the last field of every row."""

    def test_a_quoted_comma_and_a_doubled_quote_survive_crlf_endings(self):
        got = self.draw(r"""
          var text = 'city,roof,seats\r\n'
                   + 'Dallas,"retractable, closed",80000\r\n'
                   + 'Miami,"the ""open"" roof",64000\r\n';
          report({ grid: CK.parseCSV(text) });
        """)
        self.assertEqual(got["grid"], [
            ["city", "roof", "seats"],
            ["Dallas", "retractable, closed", "80000"],
            ["Miami", 'the "open" roof', "64000"],
        ])

    def test_a_row_short_of_the_header_is_handed_back_short_rather_than_padded(self):
        """The caller decides what a ragged row means. Silently padding it to
        the header's width would hand a chart an empty string where it expects
        a number, and NaN geometry is what reaches the screen."""
        got = self.draw(r"""
          report({ grid: CK.parseCSV('a,b,c\nDallas,80000\n') });
        """)
        self.assertEqual(got["grid"], [["a", "b", "c"], ["Dallas", "80000"]])


class BarPaths(Case):
    """A bar with one rounded end, drawn as a path so the flat end stays flat
    against its baseline. A corner radius wider than the bar itself turns the
    arc inside out, and the shape that reaches the screen is larger than the
    rectangle the chart asked for — so a one-match column drawn at two pixels
    wide overlaps its neighbours."""

    def test_a_radius_larger_than_the_bar_does_not_grow_the_bar(self):
        got = self.draw(r"""
          var svg = CK.frame(document.getElementById("host"), 200, 100, "bars");
          var thin = CK.S("path", { d: CK.barUp(20, 40, 2, 3, 4), fill: "#333" });
          var wide = CK.S("path", { d: CK.barRight(20, 70, 3, 2, 4), fill: "#333" });
          svg.appendChild(thin); svg.appendChild(wide);
          var t = thin.getBBox(), w = wide.getBBox();
          report({ up: { x: t.x, y: t.y, w: t.width, h: t.height },
                   right: { x: w.x, y: w.y, w: w.width, h: w.height } });
        """)
        self.assertAlmostEqual(got["up"]["w"], 2, delta=0.01)
        self.assertAlmostEqual(got["up"]["h"], 3, delta=0.01)
        self.assertAlmostEqual(got["up"]["x"], 20, delta=0.01)
        self.assertAlmostEqual(got["right"]["w"], 3, delta=0.01)
        self.assertAlmostEqual(got["right"]["h"], 2, delta=0.01)
        self.assertAlmostEqual(got["right"]["y"], 70, delta=0.01)


class Statistics(Case):
    """Correlation, a straight-line fit, the weakest correlation a sample this
    size could detect, and a seeded generator. The floor is the one a reader
    needs and no chart shows by default: a tournament of 104 matches cannot
    detect a correlation under 0.27 at all, so a bar at 0.19 is noise drawn to
    scale."""

    def test_an_exact_straight_line_reads_as_a_correlation_of_one(self):
        got = self.draw(r"""
          report({ r: CK.pearson([1,2,3,4], [2,4,6,8]),
                   down: CK.pearson([1,2,3,4], [8,6,4,2]),
                   fit: CK.fitLine([1,2,3], [3,5,7]) });
        """)
        self.assertAlmostEqual(got["r"], 1.0, places=12)
        self.assertAlmostEqual(got["down"], -1.0, places=12)
        self.assertAlmostEqual(got["fit"]["b"], 2.0, places=12)
        self.assertAlmostEqual(got["fit"]["a"], 1.0, places=12)

    def test_correlation_is_undefined_below_three_points_or_without_variation(self):
        """Returning zero for these would draw a bar saying the condition was
        measured and found not to matter, which is a different claim from not
        being able to measure it."""
        got = self.draw(r"""
          report({ two: String(CK.pearson([1,2], [2,4])),
                   flat: String(CK.pearson([1,1,1], [2,4,6])),
                   vertical: String(CK.fitLine([1,1,1], [2,4,6])) });
        """)
        self.assertEqual(got["two"], "NaN")
        self.assertEqual(got["flat"], "NaN")
        self.assertEqual(got["vertical"], "null")

    def test_the_detection_floor_falls_as_the_sample_grows(self):
        got = self.draw(r"""
          report({ five: String(CK.floorR(5)), six: CK.floorR(6),
                   thirty: CK.floorR(30), full: CK.floorR(104),
                   thousand: CK.floorR(1000) });
        """)
        self.assertEqual(got["five"], "NaN")
        self.assertAlmostEqual(got["six"], 0.9242601000570452, places=12)
        self.assertAlmostEqual(got["thirty"], 0.492355858173306, places=12)
        self.assertAlmostEqual(got["full"], 0.2717645708284619, places=12)
        self.assertAlmostEqual(got["thousand"], 0.08849498350478814, places=12)

    def test_the_seeded_generator_repeats_its_sequence(self):
        """A shuffle band redrawn on every resize has to come back the same, or
        a reader watching the page reflow sees the range move and reads that as
        the data changing."""
        got = self.draw(r"""
          function take(seed, n) {
            var g = CK.rng(seed), out = [];
            for (var i = 0; i < n; i++) out.push(g());
            return out;
          }
          report({ a: take(20260909, 6), b: take(20260909, 6), other: take(7, 6) });
        """)
        self.assertEqual(got["a"], got["b"])
        self.assertNotEqual(got["a"], got["other"])
        for value in got["a"]:
            self.assertGreaterEqual(value, 0)
            self.assertLess(value, 1)


class Tooltip(Case):
    """One tooltip element serves every chart. A pointer in the last few pixels
    of the window would put it past the edge, where the part of it carrying the
    match name is the part that gets cut off, so it flips to the other side of
    the pointer instead."""

    def test_a_pointer_at_the_far_corner_keeps_the_whole_tooltip_on_screen(self):
        got = self.draw(r"""
          CK.showTip({ clientX: window.innerWidth - 6, clientY: window.innerHeight - 6 },
                     [{ val: "Dallas 3\u20132 Miami" },
                      { key: "goals", val: "5" },
                      { key: "apparent temperature", val: "31.4", tail: "\u00b0C" }]);
          var tip = document.getElementById("tip");
          var r = tip.getBoundingClientRect();
          report({ left: r.left, top: r.top, right: r.right, bottom: r.bottom,
                   vw: window.innerWidth, vh: window.innerHeight,
                   opacity: getComputedStyle(tip).opacity, text: tip.textContent });
        """)
        self.assertGreaterEqual(got["left"], 0)
        self.assertGreaterEqual(got["top"], 0)
        self.assertLessEqual(got["right"], got["vw"])
        self.assertLessEqual(got["bottom"], got["vh"])
        self.assertEqual(got["opacity"], "1")
        self.assertIn("Dallas 3\u20132 Miami", got["text"])
        self.assertIn("31.4", got["text"])
        self.assertIn("\u00b0C", got["text"])

    def test_a_chart_mark_takes_focus_and_answers_it_with_the_same_lines(self):
        """Some values appear nowhere but the hover layer, so a reader who
        cannot use a pointer reaches them through focus.

        Two halves, because headless Chrome only does one of them: calling
        focus() moves document.activeElement to the mark and dispatches no
        focus event at all, the window never being focused. So the first half
        checks the mark is reachable and the second dispatches the event to
        check what the handler does with it. A real keyboard reaching a real
        mark is the join between them, and no headless render shows it."""
        got = self.draw(r"""
          var svg = CK.frame(document.getElementById("host"), 400, 200, "marks");
          var hit = CK.S("rect", { x: 10, y: 10, width: 80, height: 40, fill: "#333" });
          svg.appendChild(hit);
          CK.hoverable(hit, [{ val: "Miami" }, { key: "goals", val: "2" }]);
          hit.focus();
          var reachable = document.activeElement === hit;
          hit.dispatchEvent(new FocusEvent("focus"));
          var tip = document.getElementById("tip");
          var r = tip.getBoundingClientRect();
          var shown = { text: tip.textContent, opacity: getComputedStyle(tip).opacity,
                        left: r.left, top: r.top, right: r.right, bottom: r.bottom };
          hit.dispatchEvent(new FocusEvent("blur"));
          report({ tabindex: hit.getAttribute("tabindex"), reachable: reachable,
                   shown: shown, afterBlur: getComputedStyle(tip).opacity,
                   vw: window.innerWidth, vh: window.innerHeight });
        """)
        self.assertEqual(got["tabindex"], "0")
        self.assertTrue(got["reachable"], "the mark never became the active element")
        self.assertEqual(got["shown"]["opacity"], "1")
        self.assertIn("Miami", got["shown"]["text"])
        self.assertIn("2", got["shown"]["text"])
        self.assertGreaterEqual(got["shown"]["left"], 0)
        self.assertLessEqual(got["shown"]["right"], got["vw"])
        self.assertLessEqual(got["shown"]["bottom"], got["vh"])
        self.assertEqual(got["afterBlur"], "0", "the tooltip stayed up after blur")


class PageChrome(Case):
    """The legend, the data table under a chart, and the message that stands in
    for a chart with too few rows to draw. The table is not a courtesy: it is
    where a value the chart shortened to fit, or moved into the hover layer,
    stays readable."""

    def test_a_data_table_carries_its_caption_and_marks_its_numeric_columns(self):
        got = self.draw(r"""
          CK.tableInto(document.getElementById("table"),
            [{ label: "Condition" }, { label: "Share explained", num: true }],
            [["Apparent temperature", "4.1%"], ["Venue altitude", "0.8%"]],
            "The same values the chart draws.");
          var t = document.querySelector("#table table");
          report({
            caption: t.querySelector("caption").textContent,
            heads: Array.prototype.map.call(t.querySelectorAll("thead th"),
              function (h) { return [h.textContent, h.className]; }),
            firstRow: Array.prototype.map.call(t.querySelectorAll("tbody tr:first-child td"),
              function (d) { return [d.textContent, d.className]; }),
            bodyRows: t.querySelectorAll("tbody tr").length });
        """)
        self.assertEqual(got["caption"], "The same values the chart draws.")
        self.assertEqual(got["heads"], [["Condition", ""], ["Share explained", "n"]])
        self.assertEqual(got["firstRow"], [["Apparent temperature", ""], ["4.1%", "n"]])
        self.assertEqual(got["bodyRows"], 2)

    def test_a_legend_marks_a_line_apart_from_a_filled_swatch(self):
        """A fitted line and a dot series read as the same thing when both get
        a square of colour, and the line is the one a reader is meant to treat
        as a claim rather than an observation."""
        got = self.draw(r"""
          CK.legend(document.getElementById("legend"), [
            { label: "One match", color: "rgb(59, 110, 165)" },
            { label: "Best straight line through every dot",
              color: "rgb(138, 138, 138)", line: true }]);
          report({ items: Array.prototype.map.call(
            document.querySelectorAll("#legend span"), function (s) {
              var mark = s.querySelector("i");
              return { label: s.textContent, cls: mark.className,
                       bg: mark.style.background };
            }) });
        """)
        self.assertEqual(got["items"], [
            {"label": "One match", "cls": "", "bg": "rgb(59, 110, 165)"},
            {"label": "Best straight line through every dot", "cls": "line",
             "bg": "rgb(138, 138, 138)"}])

    def test_redrawing_replaces_what_was_there_rather_than_adding_to_it(self):
        """Every one of these redraws on a resize and on a filter change. One
        that appended would stack a second legend under the first and grow a
        table to twice its rows, and the page would look right until somebody
        dragged a window edge."""
        got = self.draw(r"""
          var legendHost = document.getElementById("legend");
          var tableHost = document.getElementById("table");
          var chartHost = document.getElementById("host");
          for (var pass = 0; pass < 3; pass++) {
            CK.legend(legendHost, [{ label: "One match", color: "#3b6ea5" }]);
            CK.tableInto(tableHost, [{ label: "Round" }], [["Final"]], "cap");
            CK.frame(chartHost, 100, 50, "a chart");
          }
          CK.tooFew(chartHost, "Fewer than three matches are selected.");
          report({ legendSpans: legendHost.querySelectorAll("span").length,
                   tables: tableHost.querySelectorAll("table").length,
                   tableRows: tableHost.querySelectorAll("tbody tr").length,
                   svgsLeft: chartHost.querySelectorAll("svg").length,
                   message: chartHost.textContent,
                   messageClass: chartHost.querySelector("p").className });
        """)
        self.assertEqual(got["legendSpans"], 1)
        self.assertEqual(got["tables"], 1)
        self.assertEqual(got["tableRows"], 1)
        self.assertEqual(got["svgsLeft"], 0, "tooFew left the chart it replaced in place")
        self.assertEqual(got["message"], "Fewer than three matches are selected.")
        self.assertEqual(got["messageClass"], "caption")


class WholeChart(Case):
    """One complete chart of each form, drawn the way a chart body draws one:
    the library sizes the bands and lays the axes, the body adds only its
    marks. Both forms are checked at a width nobody designed for and at a wide
    one, because the build this came from shipped a version with five text
    nodes outside their SVG at the narrow width and three at 1440."""

    def test_ranked_bars_keep_every_mark_and_label_inside_the_svg(self):
        case = """
          var data = [["Attendance against stadium capacity", 0.0412],
                      ["Apparent temperature at kickoff", 0.0233],
                      ["Day of the tournament", 0.0117],
                      ["Venue altitude", 0.0081]];
          var box = CK.rows(document.getElementById("host"), {
            width: WIDTH,
            rows: data.map(function (d) {
              return { label: d[0], value: (d[1] * 100).toFixed(1) + "%" };
            }),
            ticks: CK.niceTicks(0.05, 4),
            tickFormat: function (v) { return (v * 100).toFixed(0) + "%"; },
            title: "share of goal variation explained",
            label: "Each condition ranked by the share of goals it explains"
          });
          var worstMark = 0;
          data.forEach(function (d, i) {
            var wide = Math.max(1, box.sx(d[1]) - box.x0);
            var bar = CK.S("path", {
              d: CK.barRight(box.x0, box.markTop(i), wide, box.markH, 4),
              fill: i === 0 ? "#c8553d" : "#3b6ea5" });
            box.svg.appendChild(bar);
            var b = bar.getBBox();
            worstMark = Math.max(worstMark, b.x + b.width - box.x1,
                                 -b.x + box.x0 === 0 ? 0 : 0);
          });
          report({ bounds: bounds(box.svg), worstMark: worstMark,
                   x0: box.x0, x1: box.x1, height: box.height,
                   stacked: box.stacked, showValues: box.showValues });
        """
        for width in ("320", "768", "1440"):
            with self.subTest(width=width):
                got = self.draw(case.replace("WIDTH", width))
                self.assertEqual(got["bounds"]["escaped"], [], "width %s" % width)
                self.assertLessEqual(got["worstMark"], 0.01,
                                     "a bar reached past the plot at width %s" % width)

    def test_a_scatter_keeps_every_dot_and_label_inside_the_svg(self):
        """A dot sitting on the axis line or at the largest value in the data
        has half of itself past the plot box, which is what a scatter plot
        looks like — but past the edge of the SVG it is clipped, and the
        clipped dot is the extreme a reader most needs to see. So the caller
        says how big its marks are and the library keeps room for them."""
        case = """
          var pts = [[14.2, 2], [31.9, 5], [22.0, 0], [28.4, 3], [40.0, 7], [10.0, 1]];
          var box = CK.cartesian(document.getElementById("host"), {
            width: WIDTH, height: Math.round(WIDTH * 0.62), markRadius: RADIUS,
            y: { ticks: CK.niceTicks(7, 5), format: function (v) { return v.toFixed(0); },
                 title: "goals in the match" },
            x: { min: 10, max: 40, ticks: [10, 20, 30, 40],
                 format: function (v) { return v.toFixed(1); },
                 title: "apparent temperature at kickoff (\u00b0C)" },
            label: "Goals in a match against apparent temperature, one dot per match"
          });
          var fit = CK.fitLine(pts.map(function (p) { return p[0]; }),
                               pts.map(function (p) { return p[1]; }));
          box.svg.appendChild(CK.S("line", {
            x1: box.sx(10), x2: box.sx(40),
            y1: box.sy(fit.a + fit.b * 10), y2: box.sy(fit.a + fit.b * 40),
            stroke: "#8a8a8a" }));
          pts.forEach(function (p) {
            box.svg.appendChild(CK.S("circle", {
              cx: box.sx(p[0]), cy: box.sy(p[1]), r: RADIUS, fill: "#3b6ea5" }));
          });
          report({ text: bounds(box.svg), marks: bounds(box.svg, "circle"),
                   x0: box.x0, x1: box.x1, y0: box.y0, y1: box.y1 });
        """
        for width in ("320", "768", "1440"):
            for radius in ("4", "14"):
                with self.subTest(width=width, radius=radius):
                    got = self.draw(case.replace("WIDTH", width).replace("RADIUS", radius))
                    self.assertEqual(got["text"]["escaped"], [])
                    self.assertEqual(got["marks"]["escaped"], [])
                    self.assertLess(got["x0"], got["x1"])
                    self.assertLess(got["y1"], got["y0"])

    def test_a_dot_at_the_end_of_its_row_keeps_room_for_its_own_radius(self):
        """Two of the four row charts drew a dot at the value rather than a bar
        to it, so a row whose value sits at the top of the axis puts half the
        dot past the plot's right edge. The value column happened to be wide
        enough to absorb a radius of four; a chart that drops the value column,
        or draws a larger mark, has nothing there."""
        case = """
          var data = [["Estadio Azteca", 3.00], ["MetLife Stadium", 2.40],
                      ["SoFi Stadium", 1.75]];
          var box = CK.rows(document.getElementById("host"), {
            width: WIDTH, markRadius: RADIUS, markHeight: RADIUS * 2,
            rows: data.map(function (d) { return { label: d[0], value: null }; }),
            ticks: [0, 1, 2, 3], tickFormat: function (v) { return v.toFixed(0); },
            title: "mean goals per match"
          });
          data.forEach(function (d, i) {
            box.svg.appendChild(CK.S("line", { x1: box.x0, x2: box.sx(d[1]),
              y1: box.rowMid(i), y2: box.rowMid(i), stroke: "#ccc" }));
            box.svg.appendChild(CK.S("circle", { cx: box.sx(d[1]), cy: box.rowMid(i),
              r: RADIUS, fill: "#3b6ea5" }));
          });
          report({ text: bounds(box.svg), marks: bounds(box.svg, "circle"),
                   x0: box.x0, x1: box.x1, showValues: box.showValues });
        """
        for width in ("320", "900"):
            for radius in ("4.5", "13"):
                with self.subTest(width=width, radius=radius):
                    got = self.draw(case.replace("WIDTH", width).replace("RADIUS", radius))
                    self.assertFalse(got["showValues"], "no values were passed")
                    self.assertEqual(got["text"]["escaped"], [])
                    self.assertEqual(got["marks"]["escaped"], [])
                    self.assertLess(got["x0"], got["x1"])

    def test_a_mark_wider_than_the_value_column_still_gets_its_room(self):
        """The value column usually absorbs a dot's radius, so the two only
        come apart when the mark is the wider of them — a bubble sized by a
        third variable, against a value column holding "3.0"."""
        got = self.draw(r"""
          var data = [["Estadio Azteca", 3.00], ["MetLife Stadium", 2.40],
                      ["SoFi Stadium", 1.75]];
          var box = CK.rows(document.getElementById("host"), {
            width: 900, markRadius: 44, markHeight: 88,
            rows: data.map(function (d) {
              return { label: d[0], value: d[1].toFixed(1) };
            }),
            ticks: [0, 1, 2, 3], tickFormat: function (v) { return v.toFixed(0); },
            title: "mean goals per match"
          });
          data.forEach(function (d, i) {
            box.svg.appendChild(CK.S("circle", { cx: box.sx(d[1]), cy: box.rowMid(i),
              r: 44, fill: "#3b6ea5", opacity: 0.5 }));
          });
          report({ text: bounds(box.svg), marks: bounds(box.svg, "circle"),
                   showValues: box.showValues, padR: box.padR, x1: box.x1 });
        """)
        self.assertTrue(got["showValues"], "the value column was dropped, so it was not the narrower of the two")
        self.assertEqual(got["marks"]["escaped"], [])
        self.assertEqual(got["text"]["escaped"], [])
        self.assertGreaterEqual(got["padR"], 44)


class TickGeneration(Case):
    """Round tick values for an axis running from zero to a maximum. A chart
    whose rows are all zero, or whose maximum arrives negative from a subtraction
    that came out backwards, is a state the data reaches — and the caller is told
    not to do defensive arithmetic before calling, so the answer has to come from
    here."""

    def test_round_steps_for_an_ordinary_maximum(self):
        got = self.draw(r"""
          report({ small: CK.niceTicks(0.05, 4), goals: CK.niceTicks(7, 5),
                   thousands: CK.niceTicks(78000, 4) });
        """)
        self.assertEqual(got["small"], [0, 0.02, 0.04, 0.06])
        self.assertEqual(got["goals"], [0, 2, 4, 6, 8])
        self.assertEqual(got["thousands"], [0, 20000, 40000, 60000, 80000])

    def test_a_maximum_of_zero_yields_one_tick_rather_than_spinning(self):
        """The step derived from a maximum of zero is itself zero, and the loop
        that walks from zero to the maximum in steps of zero never advances. The
        page stops responding; it does not draw a wrong chart."""
        got = self.draw(r"""
          report({ zero: CK.niceTicks(0, 4) });
        """)
        self.assertEqual(got["zero"], [0])

    def test_a_maximum_that_is_negative_or_not_a_number_yields_one_tick(self):
        """A negative maximum gives a step of NaN, the loop body never runs, and
        the empty tick list that comes back leaves the axis with no gridlines and
        no labels — a chart that looks built and says nothing."""
        got = self.draw(r"""
          report({ negative: CK.niceTicks(-5, 4), nan: CK.niceTicks(NaN, 4),
                   infinite: CK.niceTicks(Infinity, 4) });
        """)
        self.assertEqual(got["negative"], [0])
        self.assertEqual(got["nan"], [0])
        self.assertEqual(got["infinite"], [0])


class RowHitTargets(Case):
    """A row's mark is a bar 14 pixels tall, and the reader is aiming at the
    row. The build this came from drew its marks, measured them, found every
    one of them under the 24-pixel pointer target WCAG 2.2 asks for, and wrote
    its own invisible rect per row to fix it."""

    def test_a_row_target_clears_24_pixels_though_its_mark_is_thinner(self):
        got = self.draw(r"""
          var items = [["Humidity", "+0.213"], ["Days of rest", "\u22120.177"],
                       ["Roof overhead", "+0.145"]];
          var box = CK.rows(document.getElementById("host"), {
            width: 520,
            rows: items.map(function (r) { return { label: r[0], value: r[1] }; }),
            ticks: [0, 0.1, 0.2, 0.3],
            tickFormat: function (v) { return v.toFixed(1); },
            title: "correlation with total goals"
          });
          var hits = items.map(function (r, i) {
            return CK.rowHit(box, i, [{ val: r[0] }, { key: "r", val: r[1] }], r[0]);
          });
          report({
            markH: box.markH, rowH: box.rowH, width: box.width, axisY: box.axisY,
            boxes: hits.map(function (h) {
              var b = h.getBoundingClientRect();
              return { w: +b.width.toFixed(1), h: +b.height.toFixed(1),
                       y: +h.getAttribute("y"), label: h.getAttribute("aria-label") };
            })
          });
        """)
        self.assertEqual(got["markH"], 14,
                         "the mark is no longer thinner than the target, so this "
                         "case stopped exercising the thing it was written for")
        self.assertEqual(len(got["boxes"]), 3)
        want = max(got["rowH"], 24)
        for i, b in enumerate(got["boxes"]):
            self.assertEqual(b["h"], want, "row %d target is %s tall" % (i, b["h"]))
            self.assertEqual(b["w"], 520, "row %d target does not span the chart" % i)
        self.assertGreaterEqual(got["boxes"][0]["y"], 0)
        self.assertLessEqual(got["boxes"][-1]["y"] + got["boxes"][-1]["h"], got["axisY"])
        self.assertEqual(got["boxes"][0]["label"], "Humidity")

    def test_the_floor_binds_when_the_row_itself_is_shorter_than_24(self):
        """At the page's own type sizes a row already runs past 24 pixels, so
        the first case leaves the floor doing no work. Shrink the type and the
        row drops under it, which is when the target has to stop following the
        row and hold at 24."""
        got = self.draw(r"""
          var s = document.createElement("style");
          s.textContent = "body{font-size:11px} .cat{font-size:9px}";
          document.head.appendChild(s);
          var box = CK.rows(document.getElementById("host"), {
            width: 420,
            rows: [{ label: "Humidity" }, { label: "Wind speed" }],
            ticks: [0, 1, 2], tickFormat: function (v) { return v.toFixed(0); }
          });
          var hit = CK.rowHit(box, 0, [{ val: "Humidity" }], "Humidity");
          report({ rowH: box.rowH, markH: box.markH,
                   hitH: +hit.getBoundingClientRect().height.toFixed(1),
                   mid: box.rowMid(0), y: +hit.getAttribute("y") });
        """)
        self.assertLess(got["rowH"], 24,
                        "the row is not shorter than the floor, so this case is "
                        "not exercising the floor")
        self.assertEqual(got["hitH"], 24)
        self.assertEqual(got["y"], got["mid"] - 12,
                         "the target is not centred on the row it covers")

    def test_the_pointer_lands_on_the_target_and_not_the_mark_beneath_it(self):
        """The target paints nothing, and a rect with no fill takes no pointer
        events by default — measured in this Chrome: fill=none alone does not
        receive the point, and fill=none with pointer-events:all does. So the
        rule is not decoration. It also has to sit above the mark it covers,
        which is why the caller draws its marks before calling."""
        got = self.draw(r"""
          var box = CK.rows(document.getElementById("host"), {
            width: 520,
            rows: [{ label: "Humidity", value: "+0.213" }],
            ticks: [0, 0.1, 0.2], tickFormat: function (v) { return v.toFixed(1); }
          });
          var bar = CK.S("path", {
            d: CK.barRight(box.x0, box.markTop(0), 60, box.markH, 4), fill: "#36a" });
          box.svg.appendChild(bar);
          var hit = CK.rowHit(box, 0,
            [{ val: "Humidity" }, { key: "correlation", val: "+0.213" }], "Humidity");
          var b = hit.getBoundingClientRect();
          var x = b.left + box.x0 + 20, y = b.top + b.height / 2;
          var over = document.elementFromPoint(x, y);
          hit.dispatchEvent(new PointerEvent("pointerenter", { clientX: x, clientY: y }));
          var tip = document.getElementById("tip");
          report({ overIsTarget: over === hit, overTag: over && over.tagName,
                   barIsBeneath: document.elementFromPoint(x, y) !== bar,
                   tipText: tip.textContent,
                   tipOpacity: getComputedStyle(tip).opacity });
        """)
        self.assertTrue(got["overIsTarget"],
                        "the point over the mark reached a %s, not the target"
                        % got["overTag"])
        self.assertTrue(got["barIsBeneath"])
        self.assertEqual(got["tipOpacity"], "1")
        self.assertIn("Humidity", got["tipText"])
        self.assertIn("+0.213", got["tipText"])


class RangeTickGeneration(Case):
    """Round tick values for an axis whose low end is not zero. The explorer
    scatter in the build this came from ran humidity from 30 to 92 per cent and
    altitude from 2 to 2,240 metres, and `niceTicks` walks from zero, so that
    page carried a second tick generator of its own to cover them."""

    def test_ticks_over_a_range_that_does_not_start_at_zero_stay_inside_it(self):
        got = self.draw(r"""
          report({ humidity: CK.rangeTicks(30, 92, 5),
                   fromZero: CK.niceTicks(92, 5) });
        """)
        self.assertEqual(got["humidity"], [40, 60, 80])
        self.assertEqual(
            got["fromZero"][0], 0,
            "niceTicks is supposed to start at zero; if it does not, this case "
            "no longer shows why rangeTicks exists")

    def test_a_range_with_no_span_or_no_tick_count_yields_one_tick(self):
        """None of these spins. Each one derives a step of zero, NaN, or
        Infinity, and the walk then never runs, handing back an empty list that
        leaves an axis with no gridlines and no labels. The single tick is the
        low end of the range, which is the whole axis when there is no span."""
        got = self.draw(r"""
          report({ equal: CK.rangeTicks(5, 5, 4),
                   reversed: CK.rangeTicks(90, 30, 4),
                   noCount: CK.rangeTicks(30, 92, 0),
                   loNaN: CK.rangeTicks(NaN, 92, 4),
                   hiInfinite: CK.rangeTicks(30, Infinity, 4) });
        """)
        self.assertEqual(got["equal"], [5])
        self.assertEqual(got["reversed"], [90])
        self.assertEqual(got["noCount"], [30])
        self.assertEqual(got["loNaN"], [0])
        self.assertEqual(got["hiInfinite"], [30])

    def test_a_span_too_small_to_derive_a_step_from_yields_one_tick(self):
        """A span can clear the guard above and still leave nothing to walk in
        steps of: the magnitude below the smallest span JavaScript can hold
        rounds to zero, and the walk from lo to hi in steps of zero never
        advances. Measured: lo 0, hi 5e-324 gives a step of 0 and, without the
        check on the derived step, an empty tick list."""
        got = self.draw(r"""
          report({ smallest: CK.rangeTicks(0, 5e-324, 4) });
        """)
        self.assertEqual(got["smallest"], [0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
