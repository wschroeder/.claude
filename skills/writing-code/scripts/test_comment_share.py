"""Tests for comment_share.

Run: python3 -m unittest discover -s ~/.claude/skills/writing-code/scripts
"""

import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comment_share.py")


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def write(repo, path, text, mode="w"):
    with open(os.path.join(repo, path), mode) as f:
        f.write(text)


class CommentShareTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        write(self.repo, "old.sql", "-- on main already\nselect 0;\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(self.repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        result = subprocess.run([sys.executable, SCRIPT, *args], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_counts_each_file_over_committed_uncommitted_and_untracked_branch_lines(self):
        write(self.repo, "a.sql", "select 1;\n-- why one\nselect 2;\n")
        git(self.repo, "add", "a.sql")
        git(self.repo, "commit", "-qm", "c1")
        write(self.repo, "a.sql", "-- why two\nselect 3;\n", mode="a")
        write(self.repo, "old.sql", "select 9;\n", mode="a")
        write(self.repo, "new.py", "x = 1  # trailing is code\n# lead\ny = 2\nz = 3\n")

        out = self.run_script()

        self.assertIn("a.sql  added 5  comment 2  40%  over 10%\n", out)
        self.assertIn("new.py  added 4  comment 1  25%  over 10%\n", out)
        self.assertIn("old.sql  added 1  comment 0  0%\n", out)

    def test_lists_every_added_comment_block_with_its_first_line(self):
        write(self.repo, "a.ts", "// first\n// still first\nconst a = 1;\n/* second */\nconst b = --a;\n")

        out = self.run_script()

        blocks = out.split("comment blocks:\n", 1)[1]
        self.assertEqual(blocks, "  a.ts:1  (2 lines)  // first\n  a.ts:4  (1 line)  /* second */\n")

    def test_reads_comments_by_language_and_skips_prose_files(self):
        write(self.repo, "notes.md", "# Heading\n\ntext\n")
        write(self.repo, "a.ts", "--a;\n# not a ts comment\n")
        write(self.repo, "b.sql", "comment on table t is\n  'catalog text, not a comment';\n")

        out = self.run_script()

        self.assertNotIn("notes.md", out)
        self.assertIn("a.ts  added 2  comment 0  0%\n", out)
        self.assertIn("b.sql  added 2  comment 0  0%\n", out)

    def test_base_option_measures_from_the_named_ref(self):
        write(self.repo, "a.sql", "-- one\n")
        git(self.repo, "add", "a.sql")
        git(self.repo, "commit", "-qm", "c1")
        write(self.repo, "a.sql", "select 1;\n", mode="a")

        out = self.run_script("--base", "HEAD")

        self.assertIn("a.sql  added 1  comment 0  0%\n", out)


if __name__ == "__main__":
    unittest.main()
