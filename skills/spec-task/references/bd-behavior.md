# What bd actually stores

Measured against `bd version 1.2.2 (dev)` on 2026-09-01, in a throwaway
repository created with `git init && bd init --non-interactive --prefix sp`.
Re-run these probes if bd's version changes; every rule in SKILL.md
Sections 1 and 7, and every rule in `backlog-task`, rests on them.

## `bd init` is not a quiet command

After `bd init` in an empty repository, `git status --short`:

```
?? .agents/
?? .beads/
?? .claude/
?? .codex/
?? .gitignore
?? AGENTS.md
?? CLAUDE.md
```

Seven paths, including a `CLAUDE.md` and an `AGENTS.md`. The
`.claude/settings.json` it writes registers a hook:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "command": "bd prime --hook-json", "type": "command" } ],
        "matcher": "" } ]
  }
}
```

In a client repository this is a change the operator approves, not one the
template makes on its own. That is why Section 1 forbids running it at
probe time and `backlog-task` names it in its stop.

## Why Section 1 requires `--skip-agents --skip-hooks`

Measured 2026-09-02 against the same version, in two throwaway repositories.

`bd init --skip-agents --skip-hooks -p cln` writes no `CLAUDE.md`, no
`AGENTS.md`, no `.claude/`, no `.agents/`, and sets no `core.hooksPath`.
The tracker still works completely: `bd create --acceptance` stored
criteria that `bd show` printed under `ACCEPTANCE CRITERIA`, and
`bd update --claim` and `bd close --reason` both succeeded.

**What the instruction files say that this machine does not.** Four
conflicts, all of them arriving before any skill loads:

- `CLAUDE.md` withholds commits — "Do not run git commits, git pushes, or
  Dolt remote sync unless explicitly asked" — and the SessionStart hook
  goes further, "Git authority: no git operations in this context".
  `git-commit` grants standing permission for commit and amend. This one
  fired: one run stopped mid-slice on card one of eight to renegotiate it.
- `AGENTS.md` instructs "ALWAYS use non-interactive flags" and gives
  `rm -rf directory  # NOT: rm -r directory`, against a standing rule to
  look at the target before deleting and never to run a destructive
  command unconfirmed.
- The hook advises "When creating multiple issues/tasks/epics, use
  parallel subagents for efficiency", which is what `subagents` exists to
  prevent.
- The hook prohibits "markdown files for task tracking" and memory files,
  while `session-loop` runs on a `HANDOFF.md`.

None of it is editable in place: both managed blocks carry
`<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->`, and
`config.yaml` has no profile key, so the three profiles the file describes
are prose the model reads rather than a setting anyone can change.

The per-session cost is 3,139 bytes of project `CLAUDE.md` plus 5,375
bytes of `bd prime --hook-json` output, about 2,100 tokens before a skill
loads. `AGENTS.md` is Codex's file and costs nothing under Claude Code,
but is where the `rm -rf` advice lives.

**The hooks do no measured work.** Each of the five, run as
`BD_GIT_HOOK=1 bd hooks run <name> -v`, prints exactly two lines —
`backup: skipping — running as git hook` and `auto-export: skipping —
running as git hook` — exits 0, and leaves the tree clean. They cost about
0.09s per commit: 0.10s real with `core.hooksPath` set, 0.00–0.01s with it
unset, three runs each. Untested with `backup.enabled` or `export.auto`
turned on; both ship off.

Two things the help text implies that did not happen. `prepare-commit-msg`
is documented as adding "agent identity trailers for forensics" and added
nothing — a commit made with `-m "Plain subject with no trailer"` came
back from `git log --format=%B` as exactly that. And `bd doctor`, which
checks for missing hooks, does not run at all in embedded mode: it returns
"Note: 'bd doctor' is not yet supported in embedded mode."

**What no flag prevents.** bd commits on init regardless. And `bd close`
writes the tracked file `.beads/interactions.jsonl` — `bd create`,
`bd ready` and `bd update --claim` all leave the tree clean, `bd close`
does not. Since `tdd-cycle` 4c commits and then closes, a following
`git add -u` sweeps that record into the next card's commit; nine
consecutive card commits in one run carried the previous card's close.
That is why 4c stages by path.

bd also ships a metrics endpoint, `https://gastownhall-eventsapi.com/mp/collect`,
disabled in `~/.config/bd/config.yaml` with `notice_shown: true`.

## The per-issue form stores what a spec needs

```
$ bd create "Parse EARS ubiquitous requirement" -t task -p 1 \
    --acceptance "When the parser receives 'The system shall X', the parser
    shall return kind=ubiquitous. Check: go test ./ears -run TestUbiquitous" \
    --design "Single regexp table keyed by EARS pattern." --silent
sp-2px

$ bd show sp-2px
○ sp-2px · Parse EARS ubiquitous requirement   [● P1 · OPEN]
Owner: William Schroeder · Type: task
...
DESIGN
  Single regexp table keyed by EARS pattern.
ACCEPTANCE CRITERIA
  When the parser receives 'The system shall X', the parser shall return
  kind=ubiquitous. Check: go test ./ears -run TestUbiquitous
BLOCKS
  ← ○ sp-41y: Reject malformed EARS line ● P2
```

`--design` and `--acceptance` each render as their own section.
`--spec-id` renders as a `Spec:` line near the top:

```
$ bd create "Spec-id probe" --spec-id "docs/specs/2026-09-01-ears-parser.md" ...
$ bd show sp-0w1
○ sp-0w1 · Spec-id probe   [● P2 · OPEN]
Owner: William Schroeder · Type: task
Created: 2026-09-01 · Updated: 2026-09-01
Spec: docs/specs/2026-09-01-ears-parser.md
```

Dependencies and the ready list:

```
$ bd dep add sp-41y sp-2px
✓ Added dependency: sp-41y (Reject malformed EARS line) depends on
  sp-2px (Parse EARS ubiquitous requirement) (blocks)

$ bd ready
○ sp-2px ● P1 Parse EARS ubiquitous requirement
Ready: 1 issues with no active blockers
```

## `bd create --file` silently demotes everything to prose

Input file:

```markdown
## First batch issue
Type: task
Priority: 1
Acceptance: When input is empty, the parser shall return ErrEmpty. Check: go test ./ears -run TestEmpty

Description text here.

## Second batch issue
Type: task
Priority: 2
Blocked-by: First batch issue
```

It reports success — `✓ Created 2 issues` — and then:

```
$ bd show sp-eg4
○ sp-eg4 · First batch issue   [● P2 · OPEN]
DESCRIPTION
  Type: task
  Priority: 1
  Acceptance: When input is empty, the parser shall return ErrEmpty. Check: go
  test ./ears -run TestEmpty
  Description text here.

$ bd dep list sp-3ey
sp-3ey has no dependencies
```

The priority stayed at the P2 default, the acceptance criteria became
description prose, and the dependency was never created. Note also that
`--dry-run` is rejected with `--file`, so there is no way to preview it.

## `bd create --graph` drops unknown fields and creates the issues anyway

```
$ bd create --graph plan.json
warning: graph plan node["a"] has unknown field(s): [acceptance_criteria]
  (silently dropped — see 'bd create --graph' schema)
warning: graph plan node["b"] has unknown field(s): [acceptance_criteria blocked_by]
  (silently dropped — see 'bd create --graph' schema)
Created 2 issues
  a -> sp-jpp
  b -> sp-9dx

$ bd show sp-jpp
○ sp-jpp · Graph issue A   [● P1 · OPEN]
DESCRIPTION
  (none)

$ bd dep list sp-9dx
sp-9dx has no dependencies
```

The node key is `key`, not `id`, and the plan's top-level key is `nodes`.
The field names for acceptance criteria and dependencies were not
discovered; `acceptance`, `acceptance_criteria`, `deps` and `blocked_by`
are all rejected as unknown. Because unknown fields are a warning rather
than an error, a plan file with the wrong field name creates a full set of
issues carrying none of the spec — which is the failure `backlog-task`
Section 4 exists to catch.
