# bd in spec-task

1. Read this when Section 1 finds that the repository keeps its cards in bd.

## Section 1: what to check

1. Print the real output, not a paraphrase:

```
$ bd list --status open 2>&1 | tail -3
```

2. State whether bd is already initialized here and the issue prefix in use.
3. If `.beads/` is absent and `bd where` prints no database path, do NOT run `bd init` here; record it as a precondition for `backlog-task`, in exactly this form:

```
$ bd init --skip-agents --skip-hooks -p <prefix>
```

4. Require both flags, because without them bd writes a `CLAUDE.md`, an `AGENTS.md`, a SessionStart hook, and five git hooks that contradict this machine's instructions.
5. Expect the commit bd makes on init, and do not report it as work this session did.

## Section 7: the command list

1. Write the exact commands, not yet run: one `bd create` per task, one `bd dep add` per blocking edge, one `bd dep relate` per related pair, and one `bd label add` per current-slice task.
2. Give current-slice tasks the full form:

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

3. Give sketched later tasks the title and the edges only, with no `--acceptance`, no `-e`, and no slice label:

```
bd create "<title>" -t task --silent
bd dep add <blocked-id> <blocker-id>
```

4. Give every current-slice task its slice label, because `demo-task` reads the board's lanes from it, and its `--spec-id`, the design document the card serves.
5. Use this per-issue form, or `bd create --file` with the section format `backlog-task` Section 3 gives, and list `bd dep add` and `bd update --spec-id` after `--file`, because it sets neither.
6. Never use `bd create --graph`: it reports success while dropping the acceptance criteria.
7. Where Section 1 found no `.beads/` and `bd where` found no database, make this list's first line `bd init --skip-agents --skip-hooks -p <prefix>`, both flags required.
