#!/usr/bin/env python3
"""Measures the contrast of every piece of text a dashboard draws, in both
colour schemes, and reports the pairs that fall below WCAG 1.4.3.

A page can define a dark scheme and still leave one element behind, because
the element takes a colour that is right against the page and wrong against
the card it actually sits on. That is invisible to a static read of the CSS
and to a render of the default scheme, so this drives a real browser twice.

The report opens by naming the file it read and the SHA-256 of the bytes it
read, the same way layout_scales.py does, so a reader can tell which build
the findings describe.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER = os.path.normpath(
    os.path.join(HERE, "..", "..", "responsive-design", "scripts", "render.sh"))
DIGEST_CHARS = 12
OUT_BLOCK = re.compile(r'<pre id="bc-out">(.*?)</pre>', re.S)
ENTITIES = (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
            ("&#39;", "'"), ("&amp;", "&"))


def contrast_ratio(fg, bg):
    """WCAG 2.x relative-luminance ratio, 1.0 to 21.0, order-independent."""
    light, dark = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def composite(fg, bg, alpha):
    """The colour actually painted when fg is drawn over bg at this alpha."""
    if alpha >= 1.0:
        return tuple(fg)
    return tuple(alpha * f + (1.0 - alpha) * b for f, b in zip(fg, bg))


def _luminance(rgb):
    channels = []
    for value in rgb:
        v = value / 255.0
        channels.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


# WCAG 1.4.3 says 18pt, or 14pt bold. A CSS pixel is 0.75pt, so the two
# thresholds land on 24px and 18.66px.
LARGE_PX = 24.0
LARGE_BOLD_PX = 18.66
BOLD = 700


def threshold(px, weight):
    """The ratio this text has to reach: 3.0 if WCAG calls it large, else 4.5."""
    large = px >= LARGE_PX or (px >= LARGE_BOLD_PX and weight >= BOLD)
    return 3.0 if large else 4.5


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(int(round(c)) for c in rgb)


def check(samples):
    """Findings for every text sample that falls below the ratio its size asks.

    Keyed by block, scheme and the colour pair rather than by node: one rule
    paints every row of a table, so reporting per node would bury every other
    block under one mistake.
    """
    findings, seen = [], set()
    for s in samples:
        drawn = composite(s["fg"], s["bg"], s.get("opacity", 1.0))
        ratio = contrast_ratio(drawn, s["bg"])
        need = threshold(s["px"], s["weight"])
        if ratio >= need:
            continue
        key = (s["block"], s["scheme"], tuple(drawn), tuple(s["bg"]))
        if key in seen:
            continue
        seen.add(key)
        name = s["tag"] + ("." + s["cls"] if s["cls"] else "")
        findings.append(
            ("CONTRAST",
             f"{s['block']}  {name}  {ratio:.2f} (needs {need:.1f})  "
             f"{_hex(drawn)} on {_hex(s['bg'])}  {s['px']:.0f}px  "
             f"[{s['scheme']}]  {s['text']!r}")
        )
    return findings


# Only elements holding text of their own are sampled: an ancestor whose text
# all comes from its children would otherwise be measured again for each one,
# with whatever colour it happens to carry rather than the drawn colour.
HARVEST_JS = """
(function () {
  function rgb(s) {
    var m = s && s.match(/rgba?\\(([^)]+)\\)/);
    if (!m) return null;
    var p = m[1].split(",").map(parseFloat);
    if (p.length > 3 && p[3] === 0) return null;
    return [p[0], p[1], p[2]];
  }
  function painted(el) {
    /* Opacity on the text, or on anything between it and whatever paints the
       background, fades the text against that background. Opacity on the
       background painter fades the text and its background together, and the
       walk stops before counting it: the pair is then composited over
       whatever lies further back, which compresses the ratio a little, and
       this reports the ratio inside the group rather than modelling that. */
    var alpha = 1, e = el;
    while (e && e.nodeType === 1) {
      var cs = getComputedStyle(e);
      var c = rgb(cs.backgroundColor);
      if (c) return { bg: c, alpha: e === el ? 1 : alpha };
      var o = parseFloat(cs.opacity);
      alpha *= isNaN(o) ? 1 : o;
      e = e.parentElement;
    }
    return { bg: [255, 255, 255], alpha: alpha };
  }
  function ownText(el) {
    var out = "";
    for (var i = 0; i < el.childNodes.length; i++) {
      if (el.childNodes[i].nodeType === 3) out += el.childNodes[i].nodeValue;
    }
    return out.trim();
  }
  var out = [];
  document.querySelectorAll("body *").forEach(function (el) {
    var text = ownText(el);
    if (!text) return;
    var cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none") return;
    if (parseFloat(cs.opacity) === 0) return;
    var svg = el.ownerSVGElement || (el.tagName.toLowerCase() === "svg" ? el : null);
    var fg = rgb(svg ? cs.fill : cs.color);
    if (!fg) return;
    var under = painted(svg ? (el.closest("svg") || el) : el);
    var block = el.closest("[data-block]");
    var cls = el.getAttribute("class") || "";
    out.push({ block: block ? block.getAttribute("data-block") : "__page__",
               tag: el.tagName.toLowerCase(), cls: cls.split(" ")[0],
               text: text.slice(0, 40), fg: fg, bg: under.bg,
               px: parseFloat(cs.fontSize), opacity: under.alpha,
               weight: parseInt(cs.fontWeight, 10) || 400 });
  });
  var pre = document.createElement("pre");
  pre.id = "bc-out";
  pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);
})();
"""


def read_file(path):
    with open(path, "rb") as handle:
        return handle.read()


def digest_line(path, body):
    short = hashlib.sha256(body).hexdigest()[:DIGEST_CHARS]
    return f"read  {path}  sha256:{short}  {len(body)} bytes"


def harvest(path, scheme, body):
    """Render the page once in one colour scheme and return what it drew.

    The copy sits beside the original so its relative URLs still resolve, the
    way render.sh does it for the font probe.
    """
    page = body.decode("utf-8", errors="replace")
    probe = "<script>" + HARVEST_JS + "</script>"
    marker = "</body>"
    probed = (page.replace(marker, probe + marker, 1)
              if marker in page else page + probe)
    beside = os.path.join(os.path.dirname(os.path.abspath(path)),
                          ".bc-probe-%d-%s.html" % (os.getpid(), scheme))
    dom = beside + ".dom"
    try:
        with open(beside, "w", encoding="utf-8") as handle:
            handle.write(probed)
        run = subprocess.run(
            [RENDER, "--url", beside, "--out", dom, "--mode", "dom",
             "--width", "1440", "--height", "900", "--color-scheme", scheme],
            capture_output=True, text=True)
        if run.returncode != 0:
            raise SystemExit(f"render failed for {scheme}: {run.stderr.strip()}")
        with open(dom, encoding="utf-8") as handle:
            found = OUT_BLOCK.search(handle.read())
        if not found:
            raise SystemExit(f"the page reported nothing in {scheme}; a script threw")
        raw = found.group(1)
        for entity, char in ENTITIES:
            raw = raw.replace(entity, char)
        samples = json.loads(raw)
    finally:
        for leftover in (beside, dom):
            if os.path.exists(leftover):
                os.remove(leftover)
    for s in samples:
        s["scheme"] = scheme
    return samples


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--html")
    parser.add_argument("--digest", nargs="+",
                        help="print the read line for each file and exit")
    args = parser.parse_args(argv)

    if args.digest and args.html:
        raise SystemExit("--digest reprints a read line; it does not run the check")
    if args.digest:
        for path in args.digest:
            print(digest_line(path, read_file(path)))
        return 0
    if not args.html:
        raise SystemExit("--html is required")

    body = read_file(args.html)
    print(digest_line(args.html, body))
    samples = []
    for scheme in ("light", "dark"):
        got = harvest(args.html, scheme, body)
        samples.extend(got)
        print(f"{scheme}: {len(got)} text nodes across "
              f"{len(set(s['block'] for s in got))} regions")
    findings = check(samples)
    for code, message in findings:
        print(f"FAIL  {code}: {message}")
    if not findings:
        print("no contrast failures in either scheme.")
        return 0
    print(f"\n{len(findings)} finding(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
