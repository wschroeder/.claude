#!/usr/bin/env python3
"""Tests for layout_scales.py. Run: python3 test_layout_scales.py"""

import os
import tempfile
import unittest

import layout_scales


def write(tmp, name, body):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


CLEAN_HTML = """
<style>
:root { --step-1: 12px; --step-2: 16px; --step-3: 24px; --r: 6px; --s: 8px; }
.card { font-size: var(--step-2); border-radius: var(--r); padding: var(--s); }
h1 { font-size: var(--step-3); }
</style>
<section data-block="headline"><p>104 matches played</p></section>
<section data-block="venues"><p>Twelve venues hosted the group stage.</p></section>
"""

CLEAN_LAYOUT = (
    "block\tgroup\trank\tslot\tform\tfigures\twhy\n"
    "headline\tscale\t1\thero\tstat\t104\tthe count is the lead\n"
    "venues\tgeography\t2\tprimary\tbar\t\t-\n"
)


class ScaleCounting(unittest.TestCase):
    def test_var_references_do_not_count_as_literals(self):
        findings = []
        layout_scales.check_scales(CLEAN_HTML, findings)
        self.assertEqual(findings, [])

    def test_root_definitions_are_the_scale_not_a_use_of_it(self):
        html = "<style>:root{--a:1px;--b:2px;--c:3px;--d:4px;--e:5px;--f:6px;--g:7px;}</style>"
        findings = []
        layout_scales.check_scales(html, findings)
        self.assertEqual(findings, [])

    def test_eleven_hand_placed_font_sizes_fail(self):
        rules = "".join(f".s{i}{{font-size:{10 + i}px;}}" for i in range(11))
        findings = []
        layout_scales.check_scales(f"<style>{rules}</style>", findings)
        codes = [c for c, _ in findings]
        self.assertIn("TYPE-SCALE", codes)
        self.assertIn("11 distinct font-size values", findings[0][1])

    def test_eight_corner_radii_fail(self):
        rules = "".join(f".r{i}{{border-radius:{i + 1}px;}}" for i in range(8))
        findings = []
        layout_scales.check_scales(f"<style>{rules}</style>", findings)
        self.assertIn("RADIUS-SCALE", [c for c, _ in findings])

    def test_padding_and_margin_share_one_ceiling(self):
        pads = "".join(f".p{i}{{padding:{i + 1}px;}}" for i in range(5))
        margins = "".join(f".m{i}{{margin:{i + 20}px;}}" for i in range(5))
        findings = []
        layout_scales.check_scales(f"<style>{pads}{margins}</style>", findings)
        self.assertIn("SPACE-SCALE", [c for c, _ in findings])


class Ranks(unittest.TestCase):
    def rows(self, ranks):
        return [
            {"line": i, "block": f"b{i}", "group": "g", "rank": r, "slot": "-",
             "form": "-", "figures": [], "why": "-"}
            for i, r in enumerate(ranks, 1)
        ]

    def test_distinct_contiguous_ranks_pass(self):
        findings = []
        layout_scales.check_ranks(self.rows(["1", "2", "3"]), findings)
        self.assertEqual(findings, [])

    def test_two_blocks_cannot_share_a_rank(self):
        findings = []
        layout_scales.check_ranks(self.rows(["1", "1", "2"]), findings)
        self.assertTrue(any("rank 1 claimed by 2 blocks" in m for _, m in findings))

    def test_a_gap_in_the_ranks_is_reported(self):
        findings = []
        layout_scales.check_ranks(self.rows(["1", "3"]), findings)
        self.assertTrue(any("no block holds rank 2" in m for _, m in findings))

    def test_a_non_numeric_rank_is_reported(self):
        findings = []
        layout_scales.check_ranks(self.rows(["1", "high"]), findings)
        self.assertTrue(any("not a positive integer" in m for _, m in findings))


class Figures(unittest.TestCase):
    def test_a_figure_rendered_in_one_block_only_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = write(tmp, "d.html", CLEAN_HTML)
            layout = write(tmp, "layout.tsv", CLEAN_LAYOUT)
            self.assertEqual(layout_scales.main(["--html", html, "--layout", layout]), 0)

    def test_the_same_number_in_three_blocks_fails(self):
        html_body = CLEAN_HTML.replace(
            '<section data-block="venues"><p>Twelve venues hosted the group stage.</p></section>',
            '<section data-block="venues"><p>104 matches across 12 venues</p></section>'
            '<section data-block="summary"><p>Total: 104</p></section>',
        )
        layout = CLEAN_LAYOUT + "summary\tscale\t3\tsupporting\ttable\t\t-\n"
        with tempfile.TemporaryDirectory() as tmp:
            h = write(tmp, "d.html", html_body)
            l = write(tmp, "layout.tsv", layout)
            self.assertEqual(layout_scales.main(["--html", h, "--layout", l]), 1)

    def test_a_declared_figure_missing_from_its_own_block_is_reported(self):
        findings = []
        rows = [{"line": 1, "block": "headline", "group": "g", "rank": "1", "slot": "hero",
                 "form": "stat", "figures": ["104"], "why": "-"}]
        layout_scales.check_figures(rows, {"headline": "<p>no number here</p>"}, findings)
        self.assertIn("FIGURE-ABSENT", [c for c, _ in findings])

    def test_a_longer_number_does_not_match_a_shorter_declared_one(self):
        findings = []
        rows = [{"line": 1, "block": "a", "group": "g", "rank": "1", "slot": "hero",
                 "form": "stat", "figures": ["104"], "why": "-"}]
        blocks = {"a": "<p>104</p>", "b": "<p>1043 and 2104</p>"}
        layout_scales.check_figures(rows, blocks, findings)
        self.assertEqual([c for c, _ in findings], [])


class BlockTracing(unittest.TestCase):
    def test_a_declared_block_absent_from_the_html_is_reported(self):
        findings = []
        rows = [{"line": 1, "block": "ghost", "group": "g", "rank": "1", "slot": "-",
                 "form": "-", "figures": [], "why": "-"}]
        layout_scales.check_blocks_present(rows, {}, findings)
        self.assertIn("BLOCK-MISSING", [c for c, _ in findings])

    def test_a_block_in_the_html_nobody_declared_is_reported(self):
        findings = []
        layout_scales.check_blocks_present([], {"stray": ""}, findings)
        self.assertIn("BLOCK-UNDECLARED", [c for c, _ in findings])


class LayoutFile(unittest.TestCase):
    def test_a_short_row_is_refused_rather_than_padded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "layout.tsv", "a\tb\tc\n")
            with self.assertRaises(SystemExit):
                layout_scales.read_layout(path)

    def test_an_empty_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "layout.tsv", "# only a comment\n")
            with self.assertRaises(SystemExit):
                layout_scales.read_layout(path)


class PageChrome(unittest.TestCase):
    def test_markup_before_the_first_marker_becomes_its_own_region(self):
        html = '<header><p>104 of 104 matches</p></header>' + CLEAN_HTML
        blocks = layout_scales.split_blocks(html)
        self.assertIn(layout_scales.PAGE_CHROME, blocks)
        self.assertIn("104 of 104", blocks[layout_scales.PAGE_CHROME])

    def test_page_chrome_is_not_reported_as_an_undeclared_block(self):
        findings = []
        layout_scales.check_blocks_present([], {layout_scales.PAGE_CHROME: ""}, findings)
        self.assertEqual(findings, [])

    def test_a_declared_figure_restated_in_the_masthead_now_fails(self):
        html = '<header><p>104 matches</p></header>' + CLEAN_HTML
        with tempfile.TemporaryDirectory() as tmp:
            h = write(tmp, "d.html", html)
            l = write(tmp, "layout.tsv", CLEAN_LAYOUT)
            self.assertEqual(layout_scales.main(["--html", h, "--layout", l]), 1)

    def test_no_page_chrome_when_the_first_marker_opens_the_document(self):
        blocks = layout_scales.split_blocks('<section data-block="a">x</section>')
        self.assertNotIn(layout_scales.PAGE_CHROME, blocks)


class UndeclaredSweep(unittest.TestCase):
    def rows(self, figures=()):
        return [{"line": 1, "block": "a", "group": "g", "rank": "1", "slot": "hero",
                 "form": "stat", "figures": list(figures), "why": "-"}]

    def test_a_number_in_two_regions_that_nobody_declared_warns(self):
        warnings = []
        blocks = {"__page__": "<p>1,033,829 seats</p>", "a": "<p>1,033,829 total</p>"}
        layout_scales.sweep_undeclared_figures(self.rows(), blocks, warnings)
        self.assertEqual([c for c, _ in warnings], ["REPEATED-NUMBER"])

    def test_a_declared_figure_is_left_to_the_failing_check(self):
        warnings = []
        blocks = {"__page__": "<p>104</p>", "a": "<p>104</p>"}
        layout_scales.sweep_undeclared_figures(self.rows(["104"]), blocks, warnings)
        self.assertEqual(warnings, [])

    def test_small_axis_tick_numbers_do_not_warn(self):
        warnings = []
        blocks = {"a": "<p>0 5 10</p>", "b": "<p>0 5 10</p>"}
        layout_scales.sweep_undeclared_figures(self.rows(), blocks, warnings)
        self.assertEqual(warnings, [])

    def test_a_number_in_one_region_only_does_not_warn(self):
        warnings = []
        blocks = {"a": "<p>1,033,829</p>", "b": "<p>nothing</p>"}
        layout_scales.sweep_undeclared_figures(self.rows(), blocks, warnings)
        self.assertEqual(warnings, [])

    def test_warnings_alone_do_not_fail_the_gate(self):
        html = CLEAN_HTML.replace("Twelve venues hosted the group stage.",
                                  "2,847 seats") .replace(
                                  "<p>104 matches played</p>",
                                  "<p>104 matches played, 2,847 seats</p>")
        with tempfile.TemporaryDirectory() as tmp:
            h = write(tmp, "d.html", html)
            l = write(tmp, "layout.tsv", CLEAN_LAYOUT)
            self.assertEqual(layout_scales.main(["--html", h, "--layout", l]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
