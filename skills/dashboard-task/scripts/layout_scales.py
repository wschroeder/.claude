#!/usr/bin/env python3
"""Counts how many distinct sizes a built dashboard uses, and checks that each
figure a block declared shows up in that block only.

Reads the built HTML and the layout.tsv that Section 5 wrote. A page that keeps
its sizes in custom properties and reaches them through var() scores near zero
literals, which is the point: the ceilings punish placing a value by hand.
"""

import argparse
import re
import sys
from collections import defaultdict

LENGTH = re.compile(r"-?\d*\.?\d+(?:px|rem|em|%|pt|vh|vw)\b", re.I)
ROOT_BLOCK = re.compile(r":root\s*\{.*?\}", re.S)
SCALE_PROPS = {
    "font-size": ("TYPE-SCALE", 6),
    "border-radius": ("RADIUS-SCALE", 2),
    "padding": ("SPACE-SCALE", None),
    "margin": ("SPACE-SCALE", None),
}
SPACE_CEILING = 8
BLOCK_TAG = re.compile(r'data-block\s*=\s*"([^"]+)"')


def strip_custom_property_definitions(html):
    """Values defined once in :root are the scale itself, not a use of it."""
    return ROOT_BLOCK.sub("", html)


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


def read_layout(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
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
                    "figures": [f.strip() for f in figures.split(",") if f.strip()],
                    "why": why.strip(),
                }
            )
    if not rows:
        raise SystemExit(f"{path}: no rows")
    return rows


def check_scales(html, findings):
    stripped = strip_custom_property_definitions(html)
    space = set()
    for prop, (code, ceiling) in SCALE_PROPS.items():
        values = declared_values(stripped, prop)
        if ceiling is None:
            space |= values
            continue
        if len(values) > ceiling:
            findings.append(
                (code, f"{len(values)} distinct {prop} values, ceiling {ceiling}: "
                       + ", ".join(sorted(values)))
            )
    if len(space) > SPACE_CEILING:
        findings.append(
            ("SPACE-SCALE", f"{len(space)} distinct padding/margin values, "
                            f"ceiling {SPACE_CEILING}: " + ", ".join(sorted(space)))
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
            pattern = re.compile(rf"(?<![\d.]){re.escape(figure)}(?![\d.])")
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
    parser.add_argument("--html", required=True)
    parser.add_argument("--layout", required=True)
    args = parser.parse_args(argv)

    html = open(args.html, encoding="utf-8").read()
    rows = read_layout(args.layout)
    blocks = split_blocks(html)

    findings = []
    warnings = []
    check_scales(html, findings)
    check_ranks(rows, findings)
    check_blocks_present(rows, blocks, findings)
    check_figures(rows, blocks, findings)
    sweep_undeclared_figures(rows, blocks, warnings)

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
