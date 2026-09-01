---
name: writing-code
description: Everything that holds around a code change in any language — probing an unfamiliar boundary before building on it, tracing every caller, comment, test and outside reference the change reaches, comment discipline and naming over narration, error returns that match what callers destructure, keeping raw secrets out of logs, guarding at the function boundary, and the quick-review then security-review sequence the finished diff owes. Routes to the language-specific skill when one exists. Loaded by tdd-cycle before the test is written, and on its own whenever code, comments, docstrings or doc-comments are added or changed, or when a language has no skill of its own.
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

## Probe before you build

Before writing more than ~20 lines of code that touches a boundary you don't own
— external API, database schema, library you haven't used in this session,
framework convention you're uncertain about — OR that relies on an algorithm or
logic whose behavior you haven't measured in this session (your own expertise
included) — write a throwaway probe and paste its actual output into the
conversation. The probe runs first; the production code follows. The probe's
output becomes a REF that anchors the code you're about to write.

**What is NOT a probe.**

- "The docs say it returns X" — that is intent, not observation. Rule 11 of the
  global Evidence Format applies.
- "I've used this API before" — your memory is a hypothesis, not a measurement.
- "Based on the schema file" — the schema file is a design artifact; the running
  system may differ.
- A `case` clause in your code that "should handle" the API's response —
  speculation, not observation.
- Reading the file at HEAD, a `git diff`, or a grep result — those confirm what
  the code SAYS, not what the running system DOES.

When a probe is impractical write `UNPROBED — <reason>`; when no boundary is
crossed write `EXEMPT — <reason>`. Never stage file reads, greps or diffs under
a "Probe" heading. `tdd-cycle` runs this as step 0 of its loop, against the
boundaries the test will touch; this section is the wider rule, and it holds for
code that no test drives. Detail, exemptions and rationale:
`~/.claude/skills/tdd-cycle/references/probing.md`.

## Before the edit: trace its reach

Before making any code change — one-line or large — pause and trace its reach.
Stale references elsewhere don't raise compile errors but they lie to the next
reader and surface as review findings two rounds later. Most regressions come
from changes that landed in the right place but missed the other places that
described it.

Before writing or dispatching the change, grep for each of these:

1. **Callers** — every call site of the function / GraphQL field / env var /
   module being modified. Do their expectations still hold after the change? A
   renamed queue, a flipped return value, an added required arg — each one
   rewrites caller assumptions.
2. **Comments and docstrings** — inline `#` comments, moduledocs, `@doc` blocks
   that mention the function name, the arg name, the return value, or the old
   behavior in prose. If the comment becomes false, fix it in the same diff.
   Doc/code drift is the most common regression this checklist catches.
3. **Tests** — assertions, test names, and describe blocks that encode the old
   behavior. Rename tests alongside assertion flips so git history records the
   product decision, not just the code change.
4. **External references** — PR bodies, Trello cards, design docs, frontend
   queries, skill frontmatter that describe the old semantic. If the backend
   contract shifted, these get edited too — otherwise the follow-on reader
   trusts a stale spec.

This scan is the work. The code edit is the easy part. If the change is going to
a subagent, put all four findings in its prompt up front — "here are the 3
callers, 2 comments, 4 tests, and 1 PR body that reference this" — so nothing is
re-discovered mid-change. `subagents` holds the rest of what that prompt owes,
and the question of whether to send one at all.

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

Evidence for this: [references/why-comment-discipline.md](references/why-comment-discipline.md).

## Naming

A name that needs a comment is the wrong name. Before writing an explanatory
comment, try the rename — it is almost always shorter than the comment and it
travels with every call site.

Names say what the thing IS or DOES, not how it is implemented. A function called
`validate_*`, `verify_*` or `ensure_*` must actually perform that action; if it only
returns a boolean, it is `is_*` or `has_*`.

## Error returns, logs, and untrusted callers

**Error returns match what callers destructure.** A new error tuple flows through the
existing `else` / `case` branches rather than falling through silently. Do not
introduce a shape callers pattern-match but do not handle.

**Never log raw sensitive content.** No log line carries tokens, codes, verifiers,
secrets, emails, IPs, request bodies, full changesets, or an `inspect` of a struct
that may hold any of those. A log that fires on expected behavior is noise — delete
it. A log that needs human attention is an error-level log carrying presence flags or
field keys, never raw content.

**Guard at the function boundary, not at the caller.** Write each function assuming an
untrusted caller rather than the one you designed around. Where it relies on "my
caller validates X before calling me", guard X here too — a later refactor can break
the caller's validation without touching this function.

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

## After the edit: the review sequence is owed

Any code change — regardless of how small, how confident, or how many prior
changes in the session were approved — owes a review sequence before the commit
decision arises:

1. `quick-review` against the change.
2. `security-review` against the change.

Run both inline in this session rather than handing them to subagents — see
`subagents`, which carries the measurement. Present the findings to the user
and wait for explicit per-action authorization before any commit, amend or push
— `git-commit` owns those rules. What happens to the findings themselves is
`quick-review`'s "Re-review and the fix loop".

**Prose-only diffs are exempt.** A diff that introduces no executable change —
pure prose files (`*.md`, `*.txt`, `*.rst`) and/or comment-only hunks in code
files — does not trigger the review sequence. The test is "any executable change
anywhere in the diff": if yes, the whole diff is in scope; if no, skip.

Before the diff is written, every boundary claim it will encode needs a probe
REF from this session — see "Probe before you build" above. A diff carrying an
unobserved boundary claim is a process violation, not a neutral starting point.

## What this skill does not cover

Test structure and the red-green-refactor loop (`tdd-cycle`). What the review
passes actually look for (`quick-review`, `security-review`) — this skill says
when they run, not what they check. Commit and push authorization, and commit
messages (`git-commit`). Prose written to the user (Communication Style in the
global `CLAUDE.md`).
