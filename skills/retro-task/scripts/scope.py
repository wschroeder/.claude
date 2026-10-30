import json, re, sys
seen = set()
in_claude = re.compile(r"(?:git -C|cd)\s+(?:~|\$HOME|/Users/[^/\s]+)/\.claude/?(?:\s|&|;|$)")
message = re.compile(r"""\bcommit\b[^\n|;]*?(?:-m\s+(?:"((?:[^"\\]|\\.)*)"|\x27([^\x27]*)\x27)|-F\s+-\s+<<-?\s*\x27?(\w+)\x27?\n(.*))""", re.S)
for path in sys.argv[1:]:
    for line in open(path):
        try:
            r = json.loads(line)
        except Exception:
            continue
        for c in (r.get("message") or {}).get("content") or []:
            if not (isinstance(c, dict) and c.get("type") == "tool_use") or c.get("id") in seen:
                continue
            seen.add(c.get("id"))
            if c.get("name") in ("Edit", "Write"):
                p = c["input"].get("file_path", "")
                if "/.claude/skills/" in p or p.endswith("CLAUDE.md"):
                    print(r.get("timestamp"), c["name"], p)
            if c.get("name") == "Bash":
                cmd = c["input"].get("command", "")
                if in_claude.search(cmd) and re.search(r"\bgit\b[^\n]*\bcommit\b", cmd):
                    m = message.search(cmd)
                    text = m and (m.group(1) or m.group(2) or m.group(4))
                    print(r.get("timestamp"), "commit", text.splitlines()[0] if text else "(message from a file)")
