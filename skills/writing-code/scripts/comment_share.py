"""Comment share of the lines each file added on this branch, and every added comment block.

Usage: comment_share.py [--base REF]

REF defaults to the merge base with origin's default branch. The range covers
commits since REF, uncommitted changes, and untracked files.
"""

import argparse
import os
import re
import subprocess
import sys

PROSE = {".md", ".markdown", ".txt", ".rst"}
HASH = ("#",)
SLASH = ("//", "/*", "*", "{/*")
MARKERS = {
    **{ext: HASH for ext in (".py", ".sh", ".bash", ".zsh", ".rb", ".ex", ".exs", ".nix", ".yaml", ".yml", ".toml", ".r", ".pl", ".tf", ".gd", ".conf", ".cfg", ".ini")},
    **{ext: SLASH for ext in (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs", ".c", ".h", ".cc", ".cpp", ".hpp", ".java", ".kt", ".swift", ".cs", ".scss", ".css")},
    **{ext: ("--",) for ext in (".sql", ".lua", ".hs")},
    **{ext: ("<!--",) for ext in (".html", ".xml", ".vue", ".svg")},
}
FALLBACK = ("#", "//", "--", "*", "/*")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def default_base():
    head = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip()
    return git("merge-base", "HEAD", head).strip()


def markers_for(path):
    name = os.path.basename(path)
    if name == "Dockerfile" or name == "justfile" or name == "Makefile":
        return HASH
    return MARKERS.get(os.path.splitext(name)[1].lower(), FALLBACK)


def added_lines(base):
    """Yield (path, line number, text) for every line added since base, untracked files included."""
    path = None
    line_no = 0
    for raw in git("diff", "-U0", "--no-color", "--no-renames", base).splitlines():
        if raw.startswith("+++ "):
            path = None if raw == "+++ /dev/null" else raw[6:]
        elif (m := HUNK.match(raw)):
            line_no = int(m.group(1))
        elif raw.startswith("+") and path:
            yield path, line_no, raw[1:]
            line_no += 1
    for untracked in git("ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        if not untracked:
            continue
        try:
            with open(untracked, encoding="utf-8") as f:
                for n, text in enumerate(f.read().splitlines(), start=1):
                    yield untracked, n, text
        except (UnicodeDecodeError, IsADirectoryError):
            continue


def measure(base):
    stats = {}
    blocks = []
    last = None
    for path, n, text in added_lines(base):
        if os.path.splitext(path)[1].lower() in PROSE:
            continue
        s = text.strip()
        if not s:
            continue
        counts = stats.setdefault(path, [0, 0])
        counts[0] += 1
        if not s.startswith(markers_for(path)):
            continue
        counts[1] += 1
        if last == (path, n - 1):
            blocks[-1][2] += 1
        else:
            blocks.append([path, n, 1, s])
        last = (path, n)
    return stats, blocks


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", help="ref to measure from; defaults to the merge base with origin's default branch")
    args = parser.parse_args()
    stats, blocks = measure(args.base or default_base())
    print("per file (lines this branch added):")
    for path, (added, comments) in sorted(stats.items()):
        share = round(100 * comments / added)
        flag = "  over 10%" if share > 10 else ""
        print(f"  {path}  added {added}  comment {comments}  {share}%{flag}")
    print("comment blocks:")
    for path, n, size, first in blocks:
        print(f"  {path}:{n}  ({size} {'line' if size == 1 else 'lines'})  {first}")


if __name__ == "__main__":
    sys.exit(main())
