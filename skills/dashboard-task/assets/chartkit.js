/* chartkit — chart geometry and drawing for a dashboard built as one HTML file.
 *
 * Concatenate this into the page's <script> ahead of the chart bodies, the way
 * assemble.sh cats its parts together. It expects the page to define four
 * classes and reads its type sizes off them rather than carrying sizes of its
 * own: .ax for tick labels, .cat for category labels, .val for value labels,
 * and .axtitle for axis titles.
 *
 * Every band of a chart is sized from the width the browser gives the strings
 * that will sit in that band, and the same function that sizes a band is the
 * one that draws into it. A caller never picks a padding multiplier.
 */
(function (global) {
  "use strict";

  /* ------------------------------------------------------------- reading */

  /* A field holding a comma inside quotes shifts every column after it when
     the reader splits on commas, and the row still parses, so the wrong
     column ends up drawn against the right axis. Returns a grid of rows; the
     caller names the columns, since which ones matter is its business. */
  function parseCSV(text) {
    var s = String(text).replace(/^\uFEFF/, "");
    var rows = [];
    var row = [];
    var field = "";
    var quoted = false;
    for (var i = 0; i < s.length; i++) {
      var c = s[i];
      if (quoted) {
        if (c === '"') {
          if (s[i + 1] === '"') { field += '"'; i++; } else quoted = false;
        } else field += c;
      } else if (c === '"') quoted = true;
      else if (c === ",") { row.push(field); field = ""; }
      else if (c === "\n") { row.push(field); field = ""; rows.push(row); row = []; }
      else if (c !== "\r") field += c;
    }
    if (field !== "" || row.length) { row.push(field); rows.push(row); }
    return rows.filter(function (r) { return r.length > 1 || r[0] !== ""; });
  }

  /* -------------------------------------------------------- page chrome */

  /* Each of these replaces what it finds. They all redraw on a resize and on
     a filter change, and one that appended would stack a second legend under
     the first and grow a table to twice its rows. */

  /* items: [{ label, color, line }] — line draws a rule rather than a swatch,
     so a fitted line does not read as another observed series. */
  function legend(host, items) {
    host.textContent = "";
    items.forEach(function (item) {
      var span = document.createElement("span");
      var mark = document.createElement("i");
      if (item.line) mark.className = "line";
      mark.style.background = item.color;
      span.appendChild(mark);
      span.appendChild(document.createTextNode(item.label));
      host.appendChild(span);
    });
  }

  /* cols: [{ label, num }] — num right-aligns the column through the page's
     own .n class. rows are arrays of already-formatted strings, in column
     order: a value the chart shortened to fit, or moved into the hover layer,
     stays readable here. */
  function tableInto(host, cols, rows, caption) {
    host.textContent = "";
    var table = document.createElement("table");
    if (caption) {
      var cap = document.createElement("caption");
      cap.textContent = caption;
      table.appendChild(cap);
    }
    var head = document.createElement("thead");
    var headRow = document.createElement("tr");
    cols.forEach(function (col) {
      var th = document.createElement("th");
      if (col.num) th.className = "n";
      th.textContent = col.label;
      headRow.appendChild(th);
    });
    head.appendChild(headRow);
    table.appendChild(head);
    var body = document.createElement("tbody");
    rows.forEach(function (cells) {
      var tr = document.createElement("tr");
      cols.forEach(function (col, i) {
        var td = document.createElement("td");
        if (col.num) td.className = "n";
        td.textContent = cells[i];
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    table.appendChild(body);
    host.appendChild(table);
  }

  /* A correlation over two rows is not defined, and a plot drawn from an empty
     list produces NaN geometry that renders as nothing with no explanation.
     This says so in the space the chart would have taken. */
  function tooFew(host, message) {
    host.textContent = "";
    var p = document.createElement("p");
    p.className = "caption";
    p.textContent = message;
    host.appendChild(p);
  }

  /* --------------------------------------------------------- the hover layer */

  var TIP_GAP = 12;

  /* One tooltip serves every chart on the page. The page supplies the element;
     it is looked up per call so the library can be concatenated in ahead of
     the markup. */
  function tipNode() { return document.getElementById("tip"); }

  /* lines: [{ key, val, tail }] — key is the quiet label, val the figure, tail
     the unit. A line with only val is the heading. */
  function showTip(ev, lines) {
    var tip = tipNode();
    if (!tip) return;
    tip.textContent = "";
    lines.forEach(function (line) {
      var row = document.createElement("div");
      if (line.key) {
        var key = document.createElement("span");
        key.className = "k";
        key.textContent = line.key + " ";
        row.appendChild(key);
      }
      var strong = document.createElement("strong");
      strong.textContent = line.val;
      row.appendChild(strong);
      if (line.tail) row.appendChild(document.createTextNode(" " + line.tail));
      tip.appendChild(row);
    });
    tip.style.opacity = "1";
    var x = ev.clientX + TIP_GAP;
    var y = ev.clientY + TIP_GAP;
    var box = tip.getBoundingClientRect();
    /* Flipped to the other side of the pointer rather than nudged along the
       edge: the heading carrying the match name is the first thing a clamped
       tooltip loses. */
    if (x + box.width > window.innerWidth - 4) x = ev.clientX - box.width - TIP_GAP;
    if (y + box.height > window.innerHeight - 4) y = ev.clientY - box.height - TIP_GAP;
    tip.style.left = Math.max(4, x) + "px";
    tip.style.top = Math.max(4, y) + "px";
  }

  function hideTip() {
    var tip = tipNode();
    if (tip) tip.style.opacity = "0";
  }

  /* Some values appear nowhere but the hover layer, so a reader who cannot use
     a pointer reaches them through focus. */
  function hoverable(node, lines) {
    node.addEventListener("pointerenter", function (ev) { showTip(ev, lines); });
    node.addEventListener("pointermove", function (ev) { showTip(ev, lines); });
    node.addEventListener("pointerleave", hideTip);
    node.setAttribute("tabindex", "0");
    node.addEventListener("focus", function () {
      var box = node.getBoundingClientRect();
      showTip({ clientX: box.left + box.width / 2,
                clientY: box.top + box.height / 2 }, lines);
    });
    node.addEventListener("blur", hideTip);
  }

  /* ---------------------------------------------------------- statistics */

  function pearson(xs, ys) {
    var n = xs.length;
    if (n < 3) return NaN;
    var mx = 0, my = 0, i;
    for (i = 0; i < n; i++) { mx += xs[i]; my += ys[i]; }
    mx /= n; my /= n;
    var sxy = 0, sxx = 0, syy = 0;
    for (i = 0; i < n; i++) {
      var dx = xs[i] - mx, dy = ys[i] - my;
      sxy += dx * dy; sxx += dx * dx; syy += dy * dy;
    }
    /* A column that never varies has no correlation to report. Returning zero
       would draw a bar claiming the condition was measured and found not to
       matter, which is a different statement from not being measurable. */
    if (sxx === 0 || syy === 0) return NaN;
    return sxy / Math.sqrt(sxx * syy);
  }

  function fitLine(xs, ys) {
    var n = xs.length;
    var mx = 0, my = 0, i;
    for (i = 0; i < n; i++) { mx += xs[i]; my += ys[i]; }
    mx /= n; my /= n;
    var sxy = 0, sxx = 0;
    for (i = 0; i < n; i++) {
      sxy += (xs[i] - mx) * (ys[i] - my);
      sxx += Math.pow(xs[i] - mx, 2);
    }
    if (sxx === 0) return null;
    var b = sxy / sxx;
    return { b: b, a: my - b * mx };
  }

  /* The smallest correlation this many observations could detect at 80% power,
     two-sided alpha 0.05. A bar below this is noise drawn to scale, and no
     chart shows that line unless someone asks it to. */
  function floorR(n) {
    return n < 6 ? NaN : Math.tanh((1.959964 + 0.841621) / Math.sqrt(n - 3));
  }

  /* Seeded, so a band computed from a shuffle comes back identical on every
     redraw. A reader watching the page reflow would otherwise see the range
     move and read that as the data changing. */
  function rng(seed) {
    var s = seed >>> 0;
    return function () {
      s ^= s << 13; s >>>= 0;
      s ^= s >> 17;
      s ^= s << 5;  s >>>= 0;
      return s / 4294967296;
    };
  }

  /* ------------------------------------------------------------ measuring */

  var NS = "http://www.w3.org/2000/svg";
  var measurer = document.createElement("canvas").getContext("2d");

  function baseFont() {
    return parseFloat(getComputedStyle(document.body).fontSize) || 16;
  }

  /* Reads the size a page gave a class. Not cached: a fluid scale built on
     clamp() returns a different size at a different viewport width, and the
     charts redraw on resize. */
  function classFontPx(cls) {
    var svg = S("svg", { width: 1, height: 1 });
    var probe = T(0, 0, "0", cls);
    svg.appendChild(probe);
    document.body.appendChild(svg);
    var px = parseFloat(getComputedStyle(probe).fontSize) || 12;
    svg.remove();
    return px;
  }

  /* The WCAG 1.4.12 text-spacing override sets both of these, and the browser
     adds both to the width it draws, so reading one without the other sizes a
     band too narrow for the string that goes in it. The two report an unset
     value differently: `letter-spacing` computes to the word `normal`, which
     parses to NaN, where `word-spacing` computes to `0px`. */
  function classSpacing(cls) {
    var svg = S("svg", { width: 1, height: 1 });
    var probe = T(0, 0, "0", cls);
    svg.appendChild(probe);
    document.body.appendChild(svg);
    var style = getComputedStyle(probe);
    var track = parseFloat(style.letterSpacing);
    var word = parseFloat(style.wordSpacing);
    svg.remove();
    return { track: isFinite(track) ? track : 0,
             word: isFinite(word) ? word : 0 };
  }

  /* Both properties are set on every measurement, including back to zero, so
     a class the page leaves alone cannot inherit the spacing of whichever
     class was measured before it. */
  function spaceOut(spacing) {
    measurer.letterSpacing = ((spacing && spacing.track) || 0) + "px";
    measurer.wordSpacing = ((spacing && spacing.word) || 0) + "px";
  }

  function textW(str, px, weight, spacing) {
    measurer.font = (weight || 400) + " " + px + "px Inter, sans-serif";
    spaceOut(spacing);
    return measurer.measureText(String(str)).width;
  }

  function monoW(str, px, weight, spacing) {
    measurer.font = (weight || 400) + " " + px + "px 'DM Mono', 'Courier New', monospace";
    spaceOut(spacing);
    return measurer.measureText(String(str)).width;
  }

  /* An axis title's class uppercases it, and text-transform does not reach
     measureText, so the string is uppercased here before it is measured. */
  function titleW(str, px, weight, spacing) {
    var up = String(str).toUpperCase();
    measurer.font = "500 " + px + "px 'DM Mono', 'Courier New', monospace";
    spaceOut(spacing);
    return measurer.measureText(up).width;
  }

  function widest(strings, px, weight, measure, spacing) {
    var m = measure || textW;
    var most = 0;
    (strings || []).forEach(function (s) {
      var w = m(s, px, weight, spacing);
      if (w > most) most = w;
    });
    return most;
  }

  function S(tag, attrs, cls) {
    var e = document.createElementNS(NS, tag);
    if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (cls) e.setAttribute("class", cls);
    return e;
  }

  function T(x, y, str, cls, anchor) {
    var t = S("text", { x: x, y: y }, cls);
    if (anchor) t.setAttribute("text-anchor", anchor);
    t.textContent = str;
    return t;
  }

  /* A category label wider than the room it has gets an ellipsis. Callers keep
     the full string in the tooltip and the block's data table, so nothing the
     chart shortens is only available shortened. */
  function fitText(str, maxW, px, measure, spacing) {
    var m = measure || textW;
    var t = String(str);
    if (m(t, px, undefined, spacing) <= maxW) return t;
    while (t.length > 1 && m(t + "…", px, undefined, spacing) > maxW) {
      t = t.slice(0, -1);
    }
    return t + "…";
  }

  /* An axis title states the unit, so it is never shortened to fit. It wraps
     onto as many lines as the plot is wide enough for and the band grows. */
  function wrapLines(str, maxW, px, spacing) {
    var words = String(str).split(" ");
    var lines = [];
    var cur = "";
    words.forEach(function (word) {
      var join = cur ? cur + " " + word : word;
      if (cur && titleW(join, px, 500, spacing) > maxW) {
        lines.push(cur);
        cur = word;
      } else cur = join;
    });
    if (cur) lines.push(cur);
    return lines.map(function (line) {
      return titleW(line, px, 500, spacing) > maxW
        ? fitText(line, maxW, px, titleW, spacing) : line;
    });
  }

  var TITLE_LEADING = 1.35;

  function axisTitle(svg, x, baseline, str, maxW, px, anchor, spacing) {
    var lines = wrapLines(str, maxW, px, spacing);
    var t = S("text", { x: x, y: baseline }, "axtitle");
    if (anchor) t.setAttribute("text-anchor", anchor);
    lines.forEach(function (line, i) {
      var span = S("tspan", { x: x, dy: i === 0 ? 0 : px * TITLE_LEADING });
      span.textContent = line;
      t.appendChild(span);
    });
    svg.appendChild(t);
    return lines.length;
  }

  /* A label centred on the very edge of the plot spills half of itself outside
     the SVG. It anchors inward only where that would happen, so nothing is
     nudged off its own gridline at a width where centring fits. */
  function edgeAnchor(cx, halfW, w) {
    if (cx - halfW < 0) return "start";
    if (cx + halfW > w) return "end";
    return "middle";
  }

  /* Round tick values from zero up to max. A maximum of zero derives a step of
     zero and the walk below never advances; a negative or non-finite one
     derives NaN and the walk never runs, handing back an empty list that
     leaves an axis with no gridlines and no labels. Callers are told not to
     guard before calling, so the answer comes from here: one tick at zero,
     which is what an axis with nothing above zero on it means. */
  function niceTicks(max, count) {
    if (!(max > 0) || !isFinite(max) || !(count > 0)) return [0];
    var raw = max / count;
    var mag = Math.pow(10, Math.floor(Math.log10(raw)));
    var step = [1, 2, 2.5, 5, 10].map(function (m) { return m * mag; })
      .find(function (s) { return s >= raw; }) || 10 * mag;
    var out = [];
    for (var t = 0; t <= max + step / 2; t += step) out.push(+t.toFixed(10));
    return out;
  }

  /* Round tick values inside a range whose low end is not zero. niceTicks
     walks from zero and takes no lower bound, so an axis running 30 to 92 has
     no answer there. */
  function rangeTicks(lo, hi, count) {
    if (!(hi > lo) || !isFinite(lo) || !isFinite(hi) || !(count > 0)) {
      return [isFinite(lo) ? lo : 0];
    }
    var span = hi - lo;
    var raw = span / count;
    var mag = Math.pow(10, Math.floor(Math.log10(raw)));
    var step = [1, 2, 2.5, 5, 10].map(function (m) { return m * mag; })
      .find(function (s) { return s >= raw; }) || 10 * mag;
    if (!(step > 0)) return [lo];
    var out = [];
    for (var t = Math.ceil(lo / step) * step; t <= hi + step / 1000; t += step) {
      out.push(+t.toFixed(10));
    }
    return out;
  }

  /* A bar with one rounded end and one square end, so the end sitting on the
     baseline stays flat against it. The radius is clamped to the bar rather
     than trusted: an arc wider than the bar it turns inside out, and the shape
     that reaches the screen is then larger than the rectangle asked for. */
  function barRight(x, y, w, h, r) {
    var rr = Math.max(0, Math.min(r, w, h / 2));
    return "M" + x + "," + y + "H" + (x + w - rr) +
           "a" + rr + "," + rr + " 0 0 1 " + rr + "," + rr +
           "V" + (y + h - rr) + "a" + rr + "," + rr + " 0 0 1 " + (-rr) + "," + rr +
           "H" + x + "Z";
  }

  function barUp(x, y, w, h, r) {
    var rr = Math.max(0, Math.min(r, w / 2, h));
    return "M" + x + "," + (y + h) + "V" + (y + rr) +
           "a" + rr + "," + rr + " 0 0 1 " + rr + "," + (-rr) +
           "H" + (x + w - rr) + "a" + rr + "," + rr + " 0 0 1 " + rr + "," + rr +
           "V" + (y + h) + "Z";
  }

  function frame(host, w, h, label) {
    host.textContent = "";
    var svg = S("svg", {
      width: w, height: h, viewBox: "0 0 " + w + " " + h, role: "img"
    }, "chart");
    svg.setAttribute("aria-label", label || "");
    host.appendChild(svg);
    return svg;
  }

  function formatted(values, format) {
    var f = format || String;
    return (values || []).map(function (v) { return String(f(v)); });
  }

  /* How tall a block of axis-title lines is, from its first baseline to the
     bottom of its descenders. */
  function titleBlockHeight(lines, px) {
    if (lines < 1) return 0;
    return px * 1.1 + (lines - 1) * px * TITLE_LEADING + px * 0.35;
  }

  var TICK_BASELINE = 1.45;

  /* Clear space between two tick labels, in the label's own em. Below about a
     half the axis reads as one run of digits rather than as separate numbers. */
  var TICK_LABEL_GAP = 0.6;

  /* A label `edgeAnchor` pushed inward reaches a full width to one side of its
     tick rather than a half width to each, so the anchor decision has to be
     the same one the drawing makes. Without a width there is no edge to
     measure against and every label is taken as centred. */
  function labelSpan(label, cx, px, spacing, w) {
    var half = monoW(label, px, 400, spacing) / 2;
    var anchor = isFinite(w) ? edgeAnchor(cx, half, w) : "middle";
    if (anchor === "start") return { lo: cx, hi: cx + half * 2 };
    if (anchor === "end") return { lo: cx - half * 2, hi: cx };
    return { lo: cx - half, hi: cx + half };
  }

  /* Tick values arrive from the caller, which cannot know the width the plot
     ends up with, so the labels handed over may not all fit. Labelling every
     nth tick keeps what is drawn evenly spaced and keeps the first, which is
     where the axis states its low end. The gridlines stay at every tick. */
  function tickStride(labels, xs, px, spacing, w) {
    var n = labels.length;
    if (n < 2) return 1;
    var clear = px * TICK_LABEL_GAP;
    for (var step = 1; step < n; step++) {
      var fits = true;
      for (var i = step; i < n; i += step) {
        var lower = labelSpan(labels[i - step], xs[i - step], px, spacing, w);
        var upper = labelSpan(labels[i], xs[i], px, spacing, w);
        if (upper.lo - lower.hi < clear) { fits = false; break; }
      }
      if (fits) return step;
    }
    return n;
  }

  /* The band under a plot: the tick labels' baseline and their descenders,
     then the axis title's block. Both chart forms derive it here, and both
     place the title with the function below, so the room reserved and the
     room used cannot drift apart — which is the failure this library exists
     to stop, one level up from a chart body. */
  function axisBand(axPx, titlePx, titleLines, hasTicks) {
    var band = hasTicks ? axPx * (TICK_BASELINE + 0.3) : 0;
    if (titleLines) {
      band += (hasTicks ? axPx * 0.5 : 0) + titleBlockHeight(titleLines, titlePx);
    }
    return band;
  }

  function axisTitleBaseline(axPx, titlePx, hasTicks) {
    return (hasTicks ? axPx * (TICK_BASELINE + 0.5) : 0) + titlePx * 1.1;
  }

  /* A plot with a value axis down the left and a value or category axis along
     the bottom. Sizes all four bands, draws the grid, both tick bands, the
     axis line and both titles, and hands back the plot box with a scale for
     each direction. The caller draws only its marks.
     Callers pass tick values, not a count: whichever of niceTicks or a fixed
     set they used, the strings this measures are the strings it draws. */
  function cartesian(host, spec) {
    var w = Math.max(1, Math.round(spec.width));
    var h = Math.max(1, Math.round(spec.height));
    var base = baseFont();
    var axPx = classFontPx("ax");
    var titlePx = classFontPx("axtitle");
    var axSp = classSpacing("ax");
    var titleSp = classSpacing("axtitle");
    var y = spec.y || {};
    var x = spec.x || {};

    var yLabels = formatted(y.ticks, y.format);
    var xLabels = formatted(x.ticks, x.format);
    var gap = base * 0.4;
    /* A dot on the axis line or at the largest value in the data has half of
       itself past the plot box, which is what a scatter plot looks like. Past
       the edge of the SVG it is clipped instead, and the clipped one is the
       extreme a reader most needs to see, so every band keeps its radius. */
    var mark = Math.max(0, spec.markRadius || 0);

    var padL = Math.ceil(Math.max(
      widest(yLabels, axPx, 400, monoW, axSp) + gap, mark));
    var padR = Math.ceil(Math.max(base * 0.5, mark));

    var yTitleLines = y.title
      ? wrapLines(y.title, w, titlePx, titleSp).length : 0;
    var padT = Math.ceil(Math.max(titleBlockHeight(yTitleLines, titlePx) + base * 0.4,
                                  axPx * 0.45, mark));

    var plotW = Math.max(1, w - padL - padR);
    var xTitleLines = x.title
      ? wrapLines(x.title, plotW, titlePx, titleSp).length : 0;

    var tickBaseline = axPx * TICK_BASELINE;
    var padB = Math.ceil(Math.max(
      axisBand(axPx, titlePx, xTitleLines, xLabels.length > 0), mark));

    var x0 = padL;
    var x1 = w - padR;
    var y0 = h - padB;
    var y1 = padT;

    var yLo = y.ticks && y.ticks.length ? y.ticks[0] : 0;
    var yHi = y.ticks && y.ticks.length ? y.ticks[y.ticks.length - 1] : 1;
    if (yHi === yLo) yHi = yLo + 1;
    var xLo = x.min, xHi = x.max;
    if (xHi === xLo) { xHi = xLo + 1; xLo = xLo - 1; }

    var sx = function (v) { return x0 + (v - xLo) / (xHi - xLo) * (x1 - x0); };
    var sy = function (v) { return y0 - (v - yLo) / (yHi - yLo) * (y0 - y1); };

    var svg = frame(host, w, h, spec.label);

    (y.ticks || []).forEach(function (t, i) {
      svg.appendChild(S("line", { x1: x0, x2: x1, y1: sy(t), y2: sy(t) }, "gridline"));
      svg.appendChild(T(x0 - gap, sy(t) + axPx * 0.35, yLabels[i], "ax", "end"));
    });

    var xTickStep = tickStride(xLabels, (x.ticks || []).map(sx), axPx, axSp, w);
    (x.ticks || []).forEach(function (t, i) {
      if (i % xTickStep) return;
      var cx = sx(t);
      svg.appendChild(T(cx, y0 + tickBaseline, xLabels[i], "ax",
                        edgeAnchor(cx, monoW(xLabels[i], axPx, 400, axSp) / 2, w)));
    });

    svg.appendChild(S("line", { x1: x0, x2: x1, y1: y0, y2: y0 }, "axisline"));

    if (xTitleLines) {
      axisTitle(svg, (x0 + x1) / 2,
                y0 + axisTitleBaseline(axPx, titlePx, xLabels.length > 0),
                x.title, plotW, titlePx, "middle", titleSp);
    }
    /* The y title sits horizontally above the plot in every chart. Rotated
       text is harder to read, and a title longer than its plot is tall would
       need a second treatment that the page would then carry two of. */
    if (yTitleLines) {
      axisTitle(svg, 0, titlePx * 1.1, y.title, w, titlePx, null, titleSp);
    }

    return { svg: svg, x0: x0, x1: x1, y0: y0, y1: y1, sx: sx, sy: sy,
             padL: padL, padR: padR, padT: padT, padB: padB,
             base: base, axPx: axPx, titlePx: titlePx };
  }

  /* The share of the width a label gutter may take before the labels move
     above their marks instead. The four row charts this came from had capped
     it at 0.46, 0.44, 0.42 and 0.46 and separately stacked below a width in
     base units, two mechanisms for one concern; this is the tightest of the
     four caps, applied once. */
  var LABEL_SHARE_MAX = 0.42;
  /* Below this share of the width the plot has no room left to read, so the
     value column is dropped and the caller puts those numbers in the
     tooltip and the block's data table instead. */
  var PLOT_SHARE_MIN = 0.3;

  /* Horizontal rows sharing one value axis along the bottom: ranked bars,
     dots on a stem, a mean against a range. Sizes the label gutter, the value
     column and the axis band, draws the grid, the tick band, the axis title
     and every row's label and value, and hands back the plot box, a scale,
     and where each row sits. The caller draws only its marks. */
  function rows(host, spec) {
    var w = Math.max(1, Math.round(spec.width));
    var base = baseFont();
    var axPx = classFontPx("ax");
    var catPx = classFontPx("cat");
    var valPx = classFontPx("val");
    var titlePx = classFontPx("axtitle");
    var axSp = classSpacing("ax");
    var catSp = classSpacing("cat");
    var valSp = classSpacing("val");
    var titleSp = classSpacing("axtitle");
    var items = spec.rows || [];
    var labels = items.map(function (r) { return String(r.label); });
    var values = items.map(function (r) {
      return r.value === null || r.value === undefined ? "" : String(r.value);
    });
    var markH = spec.markHeight === undefined
      ? Math.min(24, Math.round(base * 0.9)) : spec.markHeight;
    var gap = base * 0.4;

    var labelWanted = widest(labels, catPx, 400, textW, catSp) + base * 0.6;
    var stacked = labelWanted > w * LABEL_SHARE_MAX;
    var labelW = stacked ? 0 : Math.ceil(labelWanted);

    /* A row drawn as a dot at its value rather than a bar to it puts half the
       dot past the plot's right edge when that value sits at the top of the
       axis, so the right band never falls below the radius. */
    var mark = Math.max(0, spec.markRadius || 0);
    var anyValue = values.some(function (v) { return v !== ""; });
    /* A dot at the top of the axis is centred on the plot's right edge and so
       reaches its own radius past it, where the value column starts. Clear the
       radius as well as the gap, or the mark lands on the digits. */
    var valueGap = gap + mark;
    var valueWanted = anyValue
      ? widest(values, valPx, 500, monoW, valSp) + valueGap + base * 0.6 : 0;
    var padR = Math.ceil(Math.max(valueWanted || base * 0.5, mark));
    var showValues = anyValue && (w - labelW - padR) >= w * PLOT_SHARE_MIN;
    if (!showValues) padR = Math.ceil(Math.max(base * 0.5, mark));

    var rowH = Math.round(stacked
      ? catPx * 1.45 + markH + base * 0.5
      : Math.max(markH + base * 0.6, catPx * 1.85));

    var tickLabels = formatted(spec.ticks, spec.tickFormat);
    var x0 = labelW;
    var x1 = w - padR;
    var plotW = Math.max(1, x1 - x0);
    var titleLines = spec.title
      ? wrapLines(spec.title, w - x0, titlePx, titleSp).length : 0;

    var tickBaseline = axPx * TICK_BASELINE;
    var axisH = Math.ceil(axisBand(axPx, titlePx, titleLines, tickLabels.length > 0));
    var h = items.length * rowH + axisH;
    var axisY = h - axisH;

    var tickLo = spec.ticks && spec.ticks.length ? spec.ticks[0] : 0;
    var tickHi = spec.ticks && spec.ticks.length
      ? spec.ticks[spec.ticks.length - 1] : 1;
    if (tickHi === tickLo) tickHi = tickLo + 1;
    var sx = function (v) { return x0 + (v - tickLo) / (tickHi - tickLo) * plotW; };

    var svg = frame(host, w, h, spec.label);

    var rowTop = function (i) { return i * rowH; };
    var markTop = function (i) {
      return stacked ? rowTop(i) + catPx * 1.45 : rowTop(i) + (rowH - markH) / 2;
    };
    var rowMid = function (i) { return markTop(i) + markH / 2; };

    /* A stacked label sits above its own mark, inside the band a gridline runs
       down, so one line from the top of the plot to the axis strikes through
       the words. Draw a segment per row from that row's mark instead, which
       leaves the label's line clear and still rules every mark. */
    var gridSegments = stacked
      ? items.map(function (unused, i) {
          return { y1: markTop(i), y2: rowTop(i) + rowH };
        })
      : [{ y1: 0, y2: axisY }];

    var tickStep = tickStride(tickLabels, (spec.ticks || []).map(sx), axPx, axSp, w);
    (spec.ticks || []).forEach(function (t, i) {
      var cx = sx(t);
      gridSegments.forEach(function (seg) {
        svg.appendChild(S("line", { x1: cx, x2: cx, y1: seg.y1, y2: seg.y2 },
                          "gridline"));
      });
      if (i % tickStep) return;
      svg.appendChild(T(cx, axisY + tickBaseline, tickLabels[i], "ax",
                        edgeAnchor(cx, monoW(tickLabels[i], axPx, 400, axSp) / 2, w)));
    });
    if (titleLines) {
      axisTitle(svg, x0,
                axisY + axisTitleBaseline(axPx, titlePx, tickLabels.length > 0),
                spec.title, w - x0, titlePx, null, titleSp);
    }

    items.forEach(function (r, i) {
      var room = stacked ? w : x0 - base * 0.5;
      var label = fitText(r.label, room, catPx, textW, catSp);
      if (stacked) {
        svg.appendChild(T(0, rowTop(i) + catPx * 1.05, label, "cat"));
      } else {
        svg.appendChild(T(x0 - base * 0.5, rowMid(i) + catPx * 0.34, label, "cat", "end"));
      }
      /* The value goes in a fixed column at the plot's right edge rather than
         following the end of its own mark. padR is sized for that column, so a
         long value on a near-full-width mark cannot push past the edge. */
      if (showValues && values[i] !== "") {
        svg.appendChild(T(x1 + valueGap, rowMid(i) + valPx * 0.34, values[i], "val"));
      }
    });

    return { svg: svg, width: w, x0: x0, x1: x1, sx: sx, height: h,
             rowTop: rowTop, markTop: markTop, rowMid: rowMid,
             rowH: rowH, markH: markH, axisY: axisY, axisH: axisH,
             stacked: stacked, showValues: showValues,
             labelW: labelW, padR: padR,
             base: base, axPx: axPx, catPx: catPx, valPx: valPx, titlePx: titlePx };
  }

  /* WCAG 2.2 asks this many CSS pixels of a pointer target. */
  var MIN_POINTER_TARGET = 24;

  /* A row's mark is thinner than the row it sits in, and the reader is aiming
     at the row rather than at the mark, so the target covers the row and never
     falls below the pointer minimum. It paints nothing and takes the pointer
     anyway, which a rect with no fill does not do on its own. Call it after
     drawing the row's marks: it goes on the end of the SVG, so marks drawn
     afterwards would sit on top of it and take the pointer back. */
  function rowHit(box, i, lines, label) {
    var h = Math.max(box.rowH, MIN_POINTER_TARGET);
    var hit = S("rect", { x: 0, y: box.rowMid(i) - h / 2,
                          width: box.width, height: h, fill: "none" });
    hit.style.pointerEvents = "all";
    hit.setAttribute("role", "img");
    if (label) hit.setAttribute("aria-label", label);
    box.svg.appendChild(hit);
    hoverable(hit, lines);
    return hit;
  }

  global.CK = {
    parseCSV: parseCSV,
    showTip: showTip, hideTip: hideTip, hoverable: hoverable,
    pearson: pearson, fitLine: fitLine, floorR: floorR, rng: rng,
    baseFont: baseFont, classFontPx: classFontPx, classSpacing: classSpacing,
    textW: textW, monoW: monoW, titleW: titleW, widest: widest,
    S: S, T: T, frame: frame, barRight: barRight, barUp: barUp,
    legend: legend, tableInto: tableInto, tooFew: tooFew,
    fitText: fitText, wrapLines: wrapLines, axisTitle: axisTitle,
    edgeAnchor: edgeAnchor, niceTicks: niceTicks, rangeTicks: rangeTicks,
    tickStride: tickStride,
    cartesian: cartesian, rows: rows, rowHit: rowHit
  };
})(window);
