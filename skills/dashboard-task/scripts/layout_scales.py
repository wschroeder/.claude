#!/usr/bin/env python3
"""Counts how many distinct sizes a built dashboard uses, and checks that each
figure a block declared shows up in that block only.

Reads the built HTML and the layout.tsv that Section 5 wrote. A page that keeps
its sizes in custom properties and reaches them through var() scores near zero
literals, which is the point: the ceilings punish placing a value by hand.

The report opens by naming each file it read and the SHA-256 of the bytes it
read, so a reader can tell which build the findings below describe. Run with
--digest alone to reprint that line for a file and compare.
"""

import argparse
import hashlib
import io
import re
import sys
from collections import defaultdict

LENGTH = re.compile(r"-?\d*\.?\d+(?:px|rem|em|%|pt|vh|vw)\b", re.I)
ROOT_BLOCK = re.compile(r":root\s*\{.*?\}", re.S)
AT_RULE_PRELUDE = re.compile(
    r"@(?:media|container|supports)\b[^{;\"']*(?=\{)", re.I)
SCALE_PROPS = {
    "font-size": ("TYPE-SCALE", 6),
    "border-radius": ("RADIUS-SCALE", 2),
    "padding": ("SPACE-SCALE", None),
    "margin": ("SPACE-SCALE", None),
    "width": ("SIZE-SCALE", None),
    "height": ("SIZE-SCALE", None),
}
# One ceiling rather than a property each, because a swatch's width and a rule's
# height are the same decision made twice. The word boundary in declared_values
# puts the min- and max- forms under these two keys as well, so a measure set by
# hand is counted wherever it was written. A measure in `ch` costs nothing: it is
# a count of characters rather than a distance, and LENGTH does not read it.
POOL_CEILINGS = {"SPACE-SCALE": 8, "SIZE-SCALE": 4}
POOL_LABELS = {"SPACE-SCALE": "padding/margin", "SIZE-SCALE": "width/height"}
BLOCK_TAG = re.compile(r'data-block\s*=\s*"([^"]+)"')


DIGEST_CHARS = 12


def read_file(path):
    with open(path, "rb") as handle:
        return handle.read()


def digest_line(path, body):
    """Name a file by a truncated SHA-256 of the bytes on disk.

    Truncated rather than hashed differently so that `shasum -a 256 <file>`
    starts with the same characters, which lets a reader check a report
    without running this script.
    """
    short = hashlib.sha256(body).hexdigest()[:DIGEST_CHARS]
    return f"read  {path}  sha256:{short}  {len(body)} bytes"


def strip_custom_property_definitions(html):
    """Values defined once in :root are the scale itself, not a use of it."""
    return ROOT_BLOCK.sub("", html)


def strip_query_preludes(html):
    """`(min-width: 46rem)` in a query names where a layout changes, and sets
    nothing on any box. Left in, every threshold reads as a size placed by hand
    and a page that answers its own column rather than the window is punished
    for it.

    Only a prelude that reaches an opening brace is stripped, and a quote or a
    semicolon ends the attempt. The word `@media` sits in content strings and
    script bodies too, and a strip that ran to the next brace from one of those
    took the declarations between with it."""
    return AT_RULE_PRELUDE.sub("", html)


def declared_values(html, prop):
    """Every literal length assigned to prop, ignoring values reached by var()."""
    pattern = re.compile(rf"\b{prop}\s*:\s*([^;{{}}\"']+)", re.I)
    found = set()
    for raw in pattern.findall(html):
        if "var(" in raw:
            continue
        for length in LENGTH.findall(raw):
            found.add(length.lower())
    return found


PAGE_CHROME = "__page__"


def split_blocks(html):
    """Map each data-block slug to the markup between it and the next one.

    Everything before the first marker — the masthead, the filter row, any
    running header — becomes PAGE_CHROME. A figure restated up there is the
    duplication a reader actually sees, and without this region the checks
    below cannot see it at all. The last block still runs to the end of the
    document, so a footer is attributed to whichever block precedes it.
    """
    marks = []
    for m in BLOCK_TAG.finditer(html):
        # Back up to the "<" that opens the element carrying the attribute, so a
        # block's markup starts at its own tag rather than mid-attribute.
        opening = html.rfind("<", 0, m.start())
        marks.append((m.group(1), opening if opening != -1 else m.start()))
    blocks = {}
    if marks and html[: marks[0][1]].strip():
        blocks[PAGE_CHROME] = html[: marks[0][1]]
    for i, (slug, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(html)
        blocks[slug] = html[start:end]
    return blocks


SCRIPT_OR_STYLE = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.S | re.I)


def visible_text(markup):
    """Text a reader can see. Script and style bodies are not that.

    An embedded dataset or a stylesheet sits in the markup and never reaches
    the screen. Counting its numbers as rendered figures makes every check
    below fire on data the reader will never read.
    """
    return re.sub(r"<[^>]+>", " ", SCRIPT_OR_STYLE.sub(" ", markup))


# A comma before exactly three digits groups thousands; the rest separate figures.
FIGURE_LIST_COMMA = re.compile(r",(?!\d{3}(?!\d))")


def parse_layout(text, path):
    rows = []
    # newline=None translates line endings the way text mode does, so a
    # layout.tsv saved with CRLF loses its \r before the columns are split.
    for lineno, line in enumerate(io.StringIO(text, newline=None), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if lineno == 1 and parts[0].strip() == "block":
            continue
        if len(parts) < 7:
            raise SystemExit(
                f"{path}:{lineno}: expected 7 tab-separated columns, saw {len(parts)}"
            )
        block, group, rank, slot, form, figures, why = parts[:7]
        rows.append(
            {
                "line": lineno,
                "block": block.strip(),
                "group": group.strip(),
                "rank": rank.strip(),
                "slot": slot.strip(),
                "form": form.strip(),
                "figures": [f.strip() for f in FIGURE_LIST_COMMA.split(figures) if f.strip()],
                "why": why.strip(),
            }
        )
    if not rows:
        raise SystemExit(f"{path}: no rows")
    return rows


def check_scales(html, findings):
    stripped = strip_query_preludes(strip_custom_property_definitions(html))
    pools = defaultdict(set)
    for prop, (code, ceiling) in SCALE_PROPS.items():
        values = declared_values(stripped, prop)
        if ceiling is None:
            pools[code] |= values
            continue
        if len(values) > ceiling:
            findings.append(
                (code, f"{len(values)} distinct {prop} values, ceiling {ceiling}: "
                       + ", ".join(sorted(values)))
            )
    for code in sorted(pools):
        values, ceiling = pools[code], POOL_CEILINGS[code]
        if len(values) > ceiling:
            findings.append(
                (code, f"{len(values)} distinct {POOL_LABELS[code]} values, "
                       f"ceiling {ceiling}: " + ", ".join(sorted(values)))
            )


def check_ranks(rows, findings):
    seen = defaultdict(list)
    for row in rows:
        if not row["rank"].isdigit() or int(row["rank"]) < 1:
            findings.append(
                ("RANK", f"block {row['block']!r} has rank {row['rank']!r}, "
                         "which is not a positive integer")
            )
            continue
        seen[int(row["rank"])].append(row["block"])
    for rank, blocks in sorted(seen.items()):
        if len(blocks) > 1:
            findings.append(
                ("RANK", f"rank {rank} claimed by {len(blocks)} blocks: "
                         + ", ".join(blocks))
            )
    if seen:
        expected = set(range(1, len(seen) + 1))
        for missing in sorted(expected - set(seen)):
            findings.append(("RANK", f"no block holds rank {missing}"))


def check_blocks_present(rows, blocks, findings):
    declared = {row["block"] for row in rows}
    for slug in sorted(declared - set(blocks)):
        findings.append(("BLOCK-MISSING", f"layout.tsv declares {slug!r}, "
                                          "no data-block in the HTML carries it"))
    for slug in sorted(set(blocks) - declared - {PAGE_CHROME}):
        findings.append(("BLOCK-UNDECLARED", f"the HTML carries data-block={slug!r}, "
                                             "layout.tsv does not declare it"))


def check_figures(rows, blocks, findings):
    text = {slug: visible_text(markup) for slug, markup in blocks.items()}
    for row in rows:
        for figure in row["figures"]:
            pattern = re.compile(rf"(?<![\d.]){re.escape(figure)}(?!\d)(?![.,]\d)")
            elsewhere = sorted(
                slug for slug, body in text.items()
                if slug != row["block"] and pattern.search(body)
            )
            if row["block"] in text and not pattern.search(text[row["block"]]):
                findings.append(
                    ("FIGURE-ABSENT", f"{row['block']} declares figure {figure!r}, "
                                      "which does not appear in that block")
                )
            if elsewhere:
                findings.append(
                    ("REPEATED-FIGURE", f"figure {figure!r} belongs to {row['block']}, "
                                        f"also rendered in: " + ", ".join(elsewhere))
                )


FIGURE = re.compile(r"(?<![\d.\-])\d[\d,]{1,9}(?:\.\d+)?(?![\d.])")
SWEEP_IGNORE = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}


def sweep_undeclared_figures(rows, blocks, warnings):
    """Report any number rendered in two or more regions, declared or not.

    check_figures proves the build honoured layout.tsv. It cannot see a number
    nobody listed, which is the common case: the same count stated once in the
    masthead and again in a block. This sweep is noisy by design — axis ticks
    collide — so it warns and a person answers each line.
    """
    declared = {f for row in rows for f in row["figures"]}
    text = {slug: visible_text(markup) for slug, markup in blocks.items()}
    seen = defaultdict(set)
    for slug, body in text.items():
        for figure in FIGURE.findall(body):
            if figure in SWEEP_IGNORE or figure in declared:
                continue
            seen[figure].add(slug)
    for figure, slugs in sorted(seen.items()):
        if len(slugs) > 1:
            warnings.append(
                ("REPEATED-NUMBER", f"{figure!r} is rendered in {len(slugs)} regions "
                                    f"({', '.join(sorted(slugs))}) and no row declares "
                                    "it. Say which region owns it, or why each needs it.")
            )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--html")
    parser.add_argument("--layout")
    parser.add_argument(
        "--digest", nargs="+", metavar="FILE",
        help="print the read line for each file and exit, to check that a file "
             "still matches the one an earlier report named",
    )
    args = parser.parse_args(argv)

    if args.digest:
        if args.html or args.layout:
            parser.error("--digest names its own files; drop --html and --layout")
        for path in args.digest:
            print(digest_line(path, read_file(path)))
        return 0
    if not args.html or not args.layout:
        parser.error("--html and --layout are both required")

    html_bytes = read_file(args.html)
    layout_bytes = read_file(args.layout)
    html = html_bytes.decode("utf-8")
    rows = parse_layout(layout_bytes.decode("utf-8"), args.layout)
    blocks = split_blocks(html)

    findings = []
    warnings = []
    check_scales(html, findings)
    check_ranks(rows, findings)
    check_blocks_present(rows, blocks, findings)
    check_figures(rows, blocks, findings)
    sweep_undeclared_figures(rows, blocks, warnings)

    print(digest_line(args.html, html_bytes))
    print(digest_line(args.layout, layout_bytes))
    named = len(blocks) - (1 if PAGE_CHROME in blocks else 0)
    print(f"blocks declared: {len(rows)}   blocks found in HTML: {named}"
          f"   page chrome: {'yes' if PAGE_CHROME in blocks else 'no'}")
    for code, message in findings:
        print(f"FAIL  {code}: {message}")
    for code, message in warnings:
        print(f"WARN  {code}: {message}")
    if warnings and not findings:
        print(f"\n{len(warnings)} warning(s), no failures. Answer each warning in one line.")
        return 0
    if not findings:
        print("PASS  every check")
        return 0
    print(f"\n{len(findings)} finding(s), {len(warnings)} warning(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
