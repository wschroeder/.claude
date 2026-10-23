#!/usr/bin/env python3
"""Tests for layout_scales.py. Run: python3 test_layout_scales.py"""

import contextlib
import hashlib
import io
import os
import tempfile
import unittest

import layout_scales


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = layout_scales.main(argv)
    return code, out.getvalue()


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


    def test_hand_placed_box_sizes_fail(self):
        """The four properties this started with cover type, corners and space,
        so a size placed straight onto a box went uncounted. Measured on a
        built page that passed the gate: seven distinct literal lengths across
        min-height, height and width, one of them the 32rem that left a hero
        card half empty."""
        rules = (".a{min-height:32rem;}.b{height:0.68rem;}.c{height:0.75rem;}"
                 ".d{height:2px;}.e{width:1.25rem;}")
        findings = []
        layout_scales.check_scales(f"<style>{rules}</style>", findings)
        self.assertIn("SIZE-SCALE", [c for c, _ in findings])
        self.assertIn("5 distinct width/height values", dict(findings)["SIZE-SCALE"])

    def test_a_prose_measure_in_ch_is_not_counted_as_a_hand_placed_size(self):
        """responsive-design asks for prose measure as a count of characters,
        and a page following it carries one max-width per column width it
        supports — the built page that prompted this carried twelve. A count of
        characters is not a distance, so none of them is a size placed by hand."""
        rules = "".join(f".m{i}{{max-width:{50 + i}ch;}}" for i in range(12))
        findings = []
        layout_scales.check_scales(f"<style>{rules}</style>", findings)
        self.assertEqual(findings, [])

    def test_a_query_threshold_is_not_a_size_placed_on_a_box(self):
        """`@container shell (min-width: 46rem)` names the width at which a
        component changes shape. It sets nothing on any box, and a page doing
        what responsive-design asks carries one per layout change."""
        rules = ("@container shell (min-width:46rem){.a{color:red}}"
                 "@container shell (min-width:52rem){.b{color:blue}}"
                 "@media (min-width:60rem){.c{color:green}}"
                 "@media (max-height:30rem){.d{color:gray}}"
                 "@media (min-width:70rem){.e{color:teal}}")
        findings = []
        layout_scales.check_scales(f"<style>{rules}</style>", findings)
        self.assertEqual(findings, [])

    def test_an_at_rule_name_inside_a_string_does_not_eat_the_rule_after_it(self):
        """Stripping a prelude runs to the next brace, so the word `@media` in
        a content string carried the strip past the closing quote and took a
        real declaration with it. A gate that counts sizes placed by hand must
        not lose one to a coincidence of spelling."""
        rules = '.a{content:"@media handheld";width:5rem;}.b{width:6rem;}'
        stripped = layout_scales.strip_query_preludes(f"<style>{rules}</style>")
        self.assertIn("5rem", stripped)
        self.assertEqual(
            sorted(layout_scales.declared_values(stripped, "width")), ["5rem", "6rem"])

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

    def test_a_declared_figure_ending_a_sentence_is_found_in_its_block(self):
        findings = []
        rows = [{"line": 1, "block": "a", "group": "g", "rank": "1", "slot": "hero",
                 "form": "stat", "figures": ["2.36"], "why": "-"}]
        layout_scales.check_figures(rows, {"a": "<p>a gap of 2.36.</p>"}, findings)
        self.assertEqual([c for c, _ in findings], [])

    def test_a_dotted_number_does_not_match_a_shorter_declared_one(self):
        findings = []
        rows = [{"line": 1, "block": "a", "group": "g", "rank": "1", "slot": "hero",
                 "form": "stat", "figures": ["2.36"], "why": "-"}]
        blocks = {"a": "<p>2.36</p>", "b": "<p>version 2.36.5</p>"}
        layout_scales.check_figures(rows, blocks, findings)
        self.assertEqual([c for c, _ in findings], [])

    def test_a_thousands_group_does_not_match_a_shorter_declared_one(self):
        findings = []
        rows = [{"line": 1, "block": "a", "group": "g", "rank": "1", "slot": "hero",
                 "form": "stat", "figures": ["104"], "why": "-"}]
        blocks = {"a": "<p>104</p>", "b": "<p>104,829 attended</p>"}
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
                layout_scales.parse_layout(open(path).read(), path)

    def test_an_empty_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "layout.tsv", "# only a comment\n")
            with self.assertRaises(SystemExit):
                layout_scales.parse_layout(open(path).read(), path)

    def test_a_thousands_separator_does_not_split_one_figure_into_two(self):
        text = ("block\tgroup\trank\tslot\tform\tfigures\twhy\n"
                "a\tg\t1\thero\tstat\t2,200, 14.2, 20,000\t-\n")
        rows = layout_scales.parse_layout(text, "layout.tsv")
        self.assertEqual(rows[0]["figures"], ["2,200", "14.2", "20,000"])


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


class TheReportNamesWhatItRead(unittest.TestCase):
    def test_the_report_carries_a_sha256_of_the_bytes_of_each_file_it_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = write(tmp, "d.html", CLEAN_HTML)
            layout = write(tmp, "layout.tsv", CLEAN_LAYOUT)
            code, out = run_main(["--html", html, "--layout", layout])
            self.assertEqual(code, 0)
            for path in (html, layout):
                body = open(path, "rb").read()
                short = hashlib.sha256(body).hexdigest()[:12]
                self.assertIn(f"read  {path}  sha256:{short}  {len(body)} bytes",
                              out.splitlines())

    def test_digest_mode_reprints_the_line_the_gate_printed_for_each_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = write(tmp, "d.html", CLEAN_HTML)
            layout = write(tmp, "layout.tsv", CLEAN_LAYOUT)
            _, gate = run_main(["--html", html, "--layout", layout])
            code, alone = run_main(["--digest", html, layout])
        self.assertEqual(code, 0)
        self.assertEqual(len(alone.splitlines()), 2)
        for line in alone.splitlines():
            self.assertIn(line, gate.splitlines())

    def test_the_digest_lines_open_the_report_in_the_order_they_were_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = write(tmp, "d.html", CLEAN_HTML)
            layout = write(tmp, "layout.tsv", CLEAN_LAYOUT)
            _, out = run_main(["--html", html, "--layout", layout])
        first, second = out.splitlines()[:2]
        self.assertTrue(first.startswith(f"read  {html}  sha256:"), first)
        self.assertTrue(second.startswith(f"read  {layout}  sha256:"), second)

    def test_a_layout_whose_lines_end_in_bare_carriage_returns_still_parses(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "layout.tsv", CLEAN_LAYOUT.replace("\n", "\r"))
            text = open(path, "rb").read().decode("utf-8")
            rows = layout_scales.parse_layout(text, path)
        self.assertEqual([r["block"] for r in rows], ["headline", "venues"])

    def test_the_gate_is_refused_when_only_one_of_the_two_files_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = write(tmp, "d.html", CLEAN_HTML)
            with self.assertRaises(SystemExit):
                run_main(["--html", html])

    def test_digest_mode_is_refused_alongside_the_gate_rather_than_skipping_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = write(tmp, "d.html", CLEAN_HTML)
            layout = write(tmp, "layout.tsv", CLEAN_LAYOUT)
            with self.assertRaises(SystemExit):
                run_main(["--digest", html, "--html", html, "--layout", layout])


if __name__ == "__main__":
    unittest.main(verbosity=1)
