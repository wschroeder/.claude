# ~/.claude

My Claude Code setup: one instruction file that loads into every session,
sixteen skills, and a statusline script. Clone it into `~/.claude` and it works.
Nothing to install, no configuration first.

If you came looking for parts, the skills are usually what people take. Help
yourself. They stand alone except where an entry says otherwise.

```
CLAUDE.md                   instructions loaded into every session
skills/                     sixteen skills, described below
statusline-command.sh       the statusline, with its tests beside it
statusline-command.test.sh
```

## CLAUDE.md

Standing instructions. Most of them exist because something went wrong once.

The longest section asks for evidence. Any response that makes a claim about the
project has to open with what was actually checked, tagged so every claim points
at the thing that proves it. Anything unverified says so out loud.

Three shorter sections follow. How to write for a reader — the one section that
governs every response, not just the ones about code. A rule that nothing gets
published off this machine without being asked for. And a note on following a
chain to its end rather than stopping at the first plausible file.

What used to sit between them has moved out. Everything that only applies while
code is being changed now lives in the skill that is already loaded at that
moment: `writing-code` holds probing an unfamiliar boundary, tracing what a
change reaches, and the review sequence a diff owes; `quick-review` holds the
bar a fix has to clear and the loop that runs until both reviews come back
clean; `git-commit` holds the authorization each destructive action needs on its
own; `subagents` holds whether to hand work to an agent and what its prompt must
carry; `systematize` holds the three-times rule. CLAUDE.md keeps only what has
to be true before any of them load.

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

- **`writing-code`** Everything that holds around a code change in any language:
  probing an unfamiliar boundary first, tracing what the change reaches, comment
  discipline and naming while writing it, and the review sequence the diff owes
  afterwards. Hands off to a language skill where one exists.

- **`elixir-development`** Elixir, Ecto and Phoenix conventions no compiler
  enforces: query timeouts, changesets over a raw `change/2`, migration safety,
  test hygiene, timezone handling.

### Reviewing it

- **`quick-review`** Reviews a change in nine named passes, each one having to
  say where it landed: proved, ruled out, or written down as a hunch it could
  not prove. Also holds the one definition of the bar a fix has to clear, and
  the loop that runs until both reviews come back clean.

- **`security-review`** Looks for vulnerabilities in a change, scoped to the
  working tree, staged, a branch, the last commit, or a named ref.

### Git and pull requests

- **`git-commit`** Authors the commit message, and asks separately about commit,
  amend and push — each destructive action needs its own approval, and an
  approval from earlier in the session is not one.

- **`pr-create-task`** Opens a pull request with a body saying what the diff
  cannot show, and stops before the push.

- **`pr-feedback-task`** Waits for the review bots, inventories every thread, and
  weighs each one before code moves. Hands the accepted ones to
  `pr-respond-task`.

- **`pr-respond-task`** Gives every accepted finding a probe, a failing test and
  a fix, then runs `quick-review` and `security-review` over the combined diff.

### Long jobs

- **`session-loop`** Runs a long build as a series of fresh sessions, each
  handing off in writing when its own context reaches the 170,000 ceiling.

- **`subagents`** Decides whether to hand work to an agent at all — one question
  settles it — and fixes what the prompt has to carry when the answer is yes.

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

### Why the routing table is back

An earlier version of this file said the routing table was dead weight, on the
evidence that generic placeholder rows — "a design-system skill", to be filled
in by the private file — decided nothing, while the descriptions picked the
right skill every time. That was true of placeholder rows and is wrong about the
table as it stands.

The rows are concrete now, and one of them is load-bearing: the rule that
editing code loads `writing-code` is what makes the review sequence fire at all,
because a skill cannot instruct you to load it. Once the standing instructions
stopped restating what the skills say, the routing row became the thing that
reaches them. Deleting the table would silently switch the review off.

Descriptions still do most of the work, and a row is only worth adding where
something has to happen before the first tool call.

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
