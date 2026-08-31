# ~/.claude

My Claude Code setup: one instruction file that loads into every session,
fifteen skills, and a statusline script. Clone it into `~/.claude` and it works.
Nothing to install, no configuration first.

If you came looking for parts, the skills are usually what people take. Help
yourself. They stand alone except where an entry says otherwise.

```
CLAUDE.md                   instructions loaded into every session
skills/                     fifteen skills, described below
statusline-command.sh       the statusline, with its tests beside it
statusline-command.test.sh
```

## CLAUDE.md

Standing instructions. Most of them exist because something went wrong once.

The longest section asks for evidence. Any response that makes a claim about the
project has to open with what was actually checked, tagged so every claim points
at the thing that proves it. Anything unverified says so out loud.

Three shorter sections follow. How a change gets reviewed before it is
committed. When to probe an unfamiliar API before writing code against a guess
about its shape. A rule that work done by hand three times becomes a script.

It ends with two imports:

```
@~/.claude/CLAUDE-environment.md
@~/.claude/CLAUDE-private.md
```

Neither file is here. The first holds what is true of one machine: which tools
are installed, how its shell behaves. The second holds anything that names an
employer, a client, or an engagement. A missing import loads nothing and raises
no error, so a fresh clone runs fine without either of them.

## The skills

### Writing code

- **`tdd-cycle`** Probes an unfamiliar boundary for real output, then red, green,
  refactor against what it measured. Loads `writing-code` before the test.

- **`writing-code`** Comment discipline and naming for any language, handing off
  to a language skill where one exists.

- **`elixir-development`** Elixir, Ecto and Phoenix conventions no compiler
  enforces: query timeouts, changesets over a raw `change/2`, migration safety,
  test hygiene, timezone handling.

### Reviewing it

- **`quick-review`** Reviews a change in nine named passes, each one having to
  say where it landed: proved, ruled out, or written down as a hunch it could
  not prove.

- **`security-review`** Looks for vulnerabilities in a change, scoped to the
  working tree, staged, a branch, the last commit, or a named ref.

### Git and pull requests

- **`git-commit`** Authors the commit message, and asks separately about commit,
  amend and push.

- **`pr-create-task`** Opens a pull request with a body saying what the diff
  cannot show, and stops before the push.

- **`pr-feedback-task`** Waits for the review bots, inventories every thread, and
  weighs each one before code moves. Hands the accepted ones to
  `pr-respond-task`.

- **`pr-respond-task`** Gives every accepted finding a probe, a failing test and
  a fix, then runs `quick-review` and `security-review` over the combined diff.

### Long jobs

- **`session-loop`** Runs a long build as a series of fresh sessions, each
  handing off in writing when its own context reaches a measured threshold.

- **`clear-task`** Writes the handoff before a context is cleared: the decisions,
  the dead ends, and what is actually verified.

### Thinking first

- **`grill-me`** Interviews you about a plan one question at a time, down each
  branch, until the design is settled.

- **`design-gap-task`** Walks every entity in a set of design docs through its
  lifecycle, then sweeps for what cuts across all of them.

### Keeping this collection usable

- **`systematize`** Decides between a script and a skill and where it goes, then
  creates, extends, merges or retires it.

- **`create-task-skill`** Builds a new task skill through the discipline it
  teaches, and stops for approval before writing the file.

### One thing that did not work

There used to be a table of generic routing rows here, along the lines of "a
design-system skill", to be filled in by the private file. It decided nothing.
Present, absent, or half-filled, the right skill came back every time from the
descriptions alone. In practice it just cost context on every session. Write the
descriptions well and let them do the routing.

## Statusline

Renders a line like:

```
user@host ~/src/project (main) | Opus 5 ctx:14% (140K/1000K)
```

Point `settings.json` at it:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash $HOME/.claude/statusline-command.sh"
  }
}
```

It needs `jq`. Nothing in the payload is readable without it, so the line falls
back to `user@host [jq missing]`. The token breakdown needs `bc` and becomes
`[bc missing]` when it is absent. Everything else still renders.
