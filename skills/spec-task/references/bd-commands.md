# bd in spec-task

Read this when Section 1 finds that the repository keeps its cards in bd. It
holds what Section 1 checks and what Section 7 writes. The measurements behind
both are in [bd-behavior.md](bd-behavior.md).

## Section 1: what to check

Real output, not paraphrase:

```
$ bd list --status open 2>&1 | tail -3
```

State whether bd is already initialized here and the issue prefix in use.

If `.beads/` is absent, do NOT run `bd init` here. Record it as a
precondition for `backlog-task`, in exactly this form:

```
$ bd init --skip-agents --skip-hooks -p <prefix>
```

**Both flags are required.** Without them bd writes a `CLAUDE.md`, an
`AGENTS.md`, a SessionStart hook and five git hooks whose instructions
contradict this machine's, and none of those hooks does measured work.

bd makes its own commit on init whatever flags it is given. Expect that
commit, and do not report it as work this session did.

## Section 7: the command list

The exact commands, not yet run. One `bd create` per task, one
`bd dep add` per blocking edge, one `bd dep relate` per related pair, and one
`bd label add` per current-slice task.

Current-slice tasks get the full form:

```
bd create "<title>" -t task -p <0-4> \
  --acceptance "<EARS text>  Check: <proof command>" \
  --design "<design line>" \
  --spec-id "<plan path from Section 5>" \
  -e <estimate in minutes> --silent
bd dep add <blocked-id> <blocker-id>
bd dep relate <id> <related-id>
bd label add <id> slice:S<n>
```

Sketched later tasks get the title and the edges only — no `--acceptance`,
no `-e`, and no slice label:

```
bd create "<title>" -t task --silent
bd dep add <blocked-id> <blocker-id>
```

The slice label is what separates the board's lanes that `demo-task`
reads. `--spec-id` carries the design document the card serves, which is the
link from a card back to the product rule it is building.

Use this per-issue form, or `bd create --file` with the section format
`backlog-task` Section 3 gives. Neither `--file` nor `--graph` creates a
dependency or sets a spec id, so list `bd dep add` and `bd update --spec-id`
after either. Do not use `bd create --graph` at all: it reports success while
dropping the acceptance criteria, which is the one field this template exists
to produce.

Where Section 1 found no `.beads/`, this list's first line is
`bd init --skip-agents --skip-hooks -p <prefix>`, both flags required.
