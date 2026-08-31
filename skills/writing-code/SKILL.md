---
name: writing-code
description: How code gets written in any language — comment discipline, naming over narration, and routing to the language-specific skill when one exists. Loaded by tdd-cycle before the test is written, and on its own whenever code or comments are being added, changed, or reviewed. Use when writing or editing code in any language, when writing or editing comments, docstrings, or doc-comments, or when a language has no skill of its own.
activation:
  - "write code"
  - "add a comment"
  - "docstring"
  - "doc-comment"
  - "code style"
  - "coding conventions"
---

## Purpose

Conventions that hold for every language. `tdd-cycle` drives the loop; this skill
governs what the code and its comments look like once the loop reaches Green.

## Load the language skill first, if there is one

| Language | Skill | Where it lives |
|----------|-------|----------------|
| Elixir, Ecto, Phoenix | `elixir-development` | global |
| Ecto migrations | `elixir-migrations`, `safe-migration` | one project only |
| TypeScript, React | `quality-checks`, `eslint`, `security-review-fe` | one project only |

Where a project carries its own copy of one of these, the project copy wins inside
that project and the global one applies everywhere else.

If the language has no skill — GDScript today — this file is the entire convention
set for it. Say that in one line rather than proceeding as though a convention file
had been consulted.

## Comments

**Default: no comment.** Code that needs a sentence to explain what it does needs a
better name or a smaller function first. Rename it, extract it, then check whether
the sentence is still needed. Usually it is not.

**The only comment that earns its place explains a non-obvious why.** A constraint
you did not choose. An ordering that looks arbitrary and is not. A workaround for a
named bug, with the bug named. A tradeoff that someone will otherwise "fix" back.
Everything else — what the function does, what the next line does, what the
arguments are — is narration, and the code already says it.

**The deletion test.** Before keeping any comment, delete it and read the code. If
the code tells you the same thing, leave it deleted. Run this on every comment in
the diff, including ones you did not write but are touching.

**One comment per paragraph of code, never per line.** If a block needs context, one
comment above the block. A comment above every line means the block should have been
a named function.

**Editing a file you did not create is the case to watch.** Explanation added to
existing code is where comment volume actually accumulates — in this codebase, lines
added to pre-existing files run about half comments, against about 40% for lines
added to brand-new files. If you are adding a comment to a file you are only passing
through, the bar is higher, not lower: it must be a why, and it must be about the
change you are making.

**Doc-comments are not exempt.** `##`, `@doc`, `@moduledoc`, `///`, docstrings —
where the language's tooling consumes them, one line saying what the thing returns
is enough. A doc-comment is not the place for design rationale. That belongs in
`docs/`, where one reader finds it once, instead of every reader paying for it in
every file that repeats it.

**A comment describes the code as it stands, never how it got there.** Three ways a
comment drifts off the code it sits above, all of them forbidden:

- *History and contrast* — "the prior structure ran…", "now serializes only", "used
  to provide". Git holds the history.
- *Definition by absence* — describing the code by what it is not or no longer does:
  "no ClickHouse I/O runs while the lock is held", "without holding the lock". State
  what it does, not what it avoids.
- *Rationale for the change* — why the edit was made belongs in the commit message.
  The comment carries only the lasting why a reader needs in order to understand the
  code as written: an invariant it relies on, a safety property that is not obvious.

Test comments follow the same rules. State the invariant the test pins, not the
structural mechanism it exercises.

**Never leave commented-out code.** Delete it. Git has it.

**No dead code.** Do not leave branches the change made unreachable, helpers nothing
calls, or temporary variables nothing reads. A comment explaining why something is
kept but unused is not a substitute for deleting it.

### Why this is a rule and not a preference

- Comments do not measurably improve correctness. Nielebock, Krolikowski, Krüger,
  Leich and Ortmeier (*Empirical Software Engineering* 24(3), 2019) put 277
  mostly-professional developers on bug-fixing and extension tasks under three
  conditions — no comments, implementation comments, documentation comments — and
  found no meaningful difference in accuracy; documentation comments raised the
  variance in completion time. Participants believed comments helped more than the
  results showed, and rated proper identifiers as more helpful than comments.
- Comments go stale by default. Wen, Nagy, Bavota and Lanza (*ICPC* 2019), across
  1,500 Java projects and 3.3 million commits, found only 13–20% of code changes
  trigger a comment update.
- The cost falls on every read. A comment is written once and read by every later
  session. In this codebase file contents are about 40% of everything a session
  loads, and about half of the source lines are comments.

## Naming

A name that needs a comment is the wrong name. Before writing an explanatory
comment, try the rename — it is almost always shorter than the comment and it
travels with every call site.

Names say what the thing IS or DOES, not how it is implemented. A function called
`validate_*`, `verify_*` or `ensure_*` must actually perform that action; if it only
returns a boolean, it is `is_*` or `has_*`.

## Measure before declaring done

Comment share of the lines you added, working tree:

```bash
git diff -U0 | awk '/^\+/ && !/^\+\+\+/ { s=$0; sub(/^\+/,"",s); gsub(/^[ \t]+/,"",s); if (s=="") next; n++; if (s ~ /^(#|\/\/|--|\*|\/\*)/) c++ } END { printf "added non-blank lines %d, comment lines %d (%.0f%%)\n", n+0, c+0, (n?100*c/n:0) }'
```

For a commit that already landed, swap `git diff -U0` for
`git show --format='' -U0 <ref>`.

**Above 10%, run the deletion test over every comment in the diff and re-measure.**
The 10% comes from the one-comment-per-paragraph rule above, not from research: a
paragraph of eight to twelve lines carrying one comment line lands near it. It is a
trigger for a second look, not a hard cap — a diff that is genuinely one tricky
function with one paragraph of justification can sit above it and say so.

Report the number when you report the change. A measurement nobody prints is a
measurement nobody makes.

## What this skill does not cover

Test structure and the red-green-refactor loop (`tdd-cycle`). Review passes
(`quick-review`, `security-review`). Commit messages (`git-commit`). Prose written
to the user (Communication Style in the global `CLAUDE.md`).
