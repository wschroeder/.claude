"""Tests for scope.

Run: python3 -m unittest discover -s ~/.claude/skills/retro-task/scripts
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCOPE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scope.py")


def tool_use(id_, name, input_):
    return {"timestamp": "2026-01-01T00:00:00Z", "message": {"content": [
        {"type": "tool_use", "id": id_, "name": name, "input": input_}]}}


class ScopeTest(unittest.TestCase):
    def run_scope(self, records):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
            f.write("not json\n")
        try:
            out = subprocess.run([sys.executable, "-I", SCOPE, f.name], capture_output=True, text=True, check=True)
        finally:
            os.unlink(f.name)
        return out.stdout.splitlines()

    def test_lists_skill_edits_and_commits_in_claude_once_each(self):
        lines = self.run_scope([
            tool_use("a", "Edit", {"file_path": "/Users/x/.claude/skills/demo/SKILL.md"}),
            tool_use("a", "Edit", {"file_path": "/Users/x/.claude/skills/demo/SKILL.md"}),
            tool_use("b", "Edit", {"file_path": "/Users/x/repo/app.ts"}),
            tool_use("c", "Bash", {"command": "git -C ~/.claude commit -m 'Tighten the demo rule'"}),
            tool_use("d", "Bash", {"command": "git commit -m 'product change'"}),
        ])
        self.assertEqual(lines, [
            "2026-01-01T00:00:00Z Edit /Users/x/.claude/skills/demo/SKILL.md",
            "2026-01-01T00:00:00Z commit Tighten the demo rule",
        ])


if __name__ == "__main__":
    unittest.main()
