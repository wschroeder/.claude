"""Tests for block_contrast.py, which measures text contrast in both colour
schemes. The arithmetic is tested without a browser; only the end-to-end path
needs Chrome."""
import os
import shutil
import tempfile
import unittest

import block_contrast


class ContrastArithmetic(unittest.TestCase):
    def test_the_ratio_matches_the_pairs_wcag_names_and_the_one_that_shipped(self):
        """21:1 is the maximum the formula can produce. 1.07 is what a built
        page actually drew: a heading left at the browser's default black,
        sitting on a hero card painted #100720."""
        self.assertAlmostEqual(
            block_contrast.contrast_ratio((0, 0, 0), (255, 255, 255)), 21.0, places=2)
        self.assertAlmostEqual(
            block_contrast.contrast_ratio((0, 0, 0), (16, 7, 32)), 1.07, places=2)
        self.assertAlmostEqual(
            block_contrast.contrast_ratio((16, 7, 32), (0, 0, 0)), 1.07, places=2)


class LargeTextThreshold(unittest.TestCase):
    """WCAG 1.4.3 asks 4.5:1 of body text and 3:1 of large text, and defines
    large as 18pt, or 14pt when bold. In CSS pixels that is 24, or 18.66 bold.
    A check that applies one number to everything fails headings that are fine
    and passes captions that are not."""

    def test_the_boundary_sits_where_the_criterion_puts_it(self):
        self.assertEqual(block_contrast.threshold(24.0, 400), 3.0)
        self.assertEqual(block_contrast.threshold(23.9, 400), 4.5)
        self.assertEqual(block_contrast.threshold(18.66, 700), 3.0)
        self.assertEqual(block_contrast.threshold(18.66, 400), 4.5)
        self.assertEqual(block_contrast.threshold(18.5, 700), 4.5)


def sample(**kw):
    base = {"block": "verdict", "scheme": "light", "tag": "h2", "cls": "kicker",
            "text": "The answer up front", "fg": [0, 0, 0], "bg": [16, 7, 32],
            "px": 24.0, "weight": 400, "opacity": 1.0}
    base.update(kw)
    return base


class Findings(unittest.TestCase):
    def test_the_pair_below_its_threshold_is_reported_with_block_scheme_and_ratio(self):
        """Taken from the build this came from: one heading failed, in light
        only, and the same element in dark was among the best on the page."""
        findings = block_contrast.check([
            sample(),
            sample(scheme="dark", fg=[241, 241, 248]),
            sample(block="board", cls="", text="Every condition", fg=[26, 16, 48],
                   bg=[241, 241, 248], px=27.0),
        ])
        self.assertEqual(len(findings), 1)
        code, message = findings[0]
        self.assertEqual(code, "CONTRAST")
        self.assertIn("verdict", message)
        self.assertIn("light", message)
        self.assertIn("1.07", message)
        self.assertIn("needs 3.0", message)
        self.assertIn("The answer up front", message)

    def test_one_token_used_on_two_hundred_nodes_is_reported_once(self):
        """A colour is set in one rule and drawn in every row of a table. The
        finding is the rule, so repeating it per node buries the other blocks."""
        findings = block_contrast.check([sample(text="row %d" % i) for i in range(200)])
        self.assertEqual(len(findings), 1)


class PartialOpacity(unittest.TestCase):
    """Text drawn at less than full opacity is painted as a blend of its own
    colour and what lies behind it, so its declared colour overstates what the
    reader sees. Measured on a built page: an eyebrow set to `opacity: 0.72`
    reads 7.88 from its declared colour and 4.53 as drawn, against the 4.5 its
    size asks. Reading the declaration would have cleared it by three points."""

    def test_the_drawn_colour_is_the_blend_and_not_the_declaration(self):
        fg, bg = (183, 150, 224), (16, 7, 32)
        self.assertAlmostEqual(block_contrast.contrast_ratio(fg, bg), 7.88, places=2)
        drawn = block_contrast.composite(fg, bg, 0.72)
        self.assertAlmostEqual(block_contrast.contrast_ratio(drawn, bg), 4.53, places=2)

    def test_full_opacity_leaves_the_colour_alone(self):
        self.assertEqual(block_contrast.composite((10, 20, 30), (0, 0, 0), 1.0),
                         (10, 20, 30))

    def test_check_measures_what_is_drawn(self):
        faded = sample(fg=[183, 150, 224], px=12.0, opacity=0.35,
                       text="The strongest predictor we found")
        self.assertEqual(len(block_contrast.check([faded])), 1)
        self.assertEqual(block_contrast.check([dict(faded, opacity=1.0)]), [])


CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Passes in light and fails in dark, so a run that measures only the default
# scheme reports nothing and the test catches that rather than the arithmetic.
# The dark pair is the one a built page actually shipped on its selected filter
# pill: paper-white on the series colour, 3.09 against the 4.5 that 14px asks.
TWO_SCHEME_FIXTURE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>
:root { --card:#FFFFFF; --ink:#111111; }
@media (prefers-color-scheme: dark) { :root { --card:#9B7BC6; --ink:#F1F1F8; } }
body { margin:0; background:var(--card); }
section { background:var(--card); padding:10px; }
h2 { color:var(--ink); font-size:14px; font-weight:400; margin:0; }
</style></head><body>
<section data-block="tile"><h2>Selected filter</h2></section>
</body></html>"""


@unittest.skipUnless(os.path.exists(CHROME), "Chrome not installed here")
class BothSchemes(unittest.TestCase):
    """The point of the check is the scheme nobody renders. A page can define a
    dark palette and leave one pairing behind in it, and a review that renders
    the default scheme calls that page clean."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="block-contrast-test.")
        self.page = os.path.join(self.dir, "page.html")
        with open(self.page, "w", encoding="utf-8") as f:
            f.write(TWO_SCHEME_FIXTURE)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_a_pairing_that_only_fails_in_dark_is_still_found(self):
        body = block_contrast.read_file(self.page)
        light = block_contrast.harvest(self.page, "light", body)
        dark = block_contrast.harvest(self.page, "dark", body)
        self.assertEqual([s["fg"] for s in light if s["tag"] == "h2"], [[17, 17, 17]])
        self.assertEqual([s["fg"] for s in dark if s["tag"] == "h2"], [[241, 241, 248]])
        self.assertEqual(block_contrast.check(light), [])
        findings = block_contrast.check(dark)
        self.assertEqual(len(findings), 1)
        self.assertIn("tile", findings[0][1])
        self.assertIn("[dark]", findings[0][1])
        self.assertIn("3.09", findings[0][1])

    def test_page_text_that_looks_like_the_probe_output_survives_the_round_trip(self):
        """The harvest hands its samples back inside a <pre> and reads them out
        of the dumped DOM, so page text containing a closing pre tag, an
        ampersand or an escaped entity is the case that would corrupt them."""
        tricky = os.path.join(self.dir, "tricky.html")
        with open(tricky, "w", encoding="utf-8") as f:
            f.write('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                    "<style>body{background:#fff}h2{color:#111;font-size:14px;"
                    "font-weight:400}</style></head><body>"
                    '<section data-block="tricky"><h2>'
                    "a &lt;/pre&gt; and an &amp; and an &amp;lt; here"
                    "</h2></section></body></html>")
        got = block_contrast.harvest(tricky, "light",
                                     block_contrast.read_file(tricky))
        texts = [s["text"] for s in got if s["tag"] == "h2"]
        self.assertEqual(texts, ["a </pre> and an & and an &lt; here"])

    def test_the_harvest_reports_the_opacity_that_fades_the_text(self):
        """The compositing is only reached if the browser walk actually carries
        the opacity back. Here the wrapper fades the heading and paints no
        background of its own, which is the arrangement that hides the fade
        from a reader of the CSS."""
        faded = os.path.join(self.dir, "faded.html")
        with open(faded, "w", encoding="utf-8") as f:
            f.write('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                    "<style>body{background:#000}section{background:#000}"
                    ".veil{opacity:0.3}h2{color:#FFF;font-size:14px;font-weight:400}"
                    "</style></head><body>"
                    '<section data-block="t"><div class="veil"><h2>faded</h2></div>'
                    "</section></body></html>")
        got = block_contrast.harvest(faded, "light",
                                     block_contrast.read_file(faded))
        heading = [s for s in got if s["tag"] == "h2"]
        self.assertEqual(len(heading), 1)
        self.assertAlmostEqual(heading[0]["opacity"], 0.3, places=3)
        self.assertEqual(len(block_contrast.check(heading)), 1)

    def test_a_faded_card_does_not_fade_its_text_against_its_own_background(self):
        """Opacity on the element painting the background takes the text with
        it, so the ratio inside that group is what it was. Compositing the
        whole group over what lies further back compresses it a little, and
        this pins the simpler reading rather than modelling that."""
        group = os.path.join(self.dir, "group.html")
        with open(group, "w", encoding="utf-8") as f:
            f.write('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                    "<style>body{background:#FFF}"
                    "section{background:#000;opacity:0.5}"
                    "h2{color:#FFF;font-size:14px;font-weight:400}"
                    "</style></head><body>"
                    '<section data-block="t"><h2>on a faded card</h2></section>'
                    "</body></html>")
        heading = [s for s in block_contrast.harvest(
            group, "light", block_contrast.read_file(group)) if s["tag"] == "h2"]
        self.assertEqual(len(heading), 1)
        self.assertEqual(heading[0]["opacity"], 1)
        self.assertEqual(block_contrast.check(heading), [])

    def test_the_probe_copy_is_not_left_beside_the_page(self):
        block_contrast.harvest(self.page, "dark", block_contrast.read_file(self.page))
        self.assertEqual(sorted(os.listdir(self.dir)), ["page.html"])


if __name__ == "__main__":
    unittest.main()
