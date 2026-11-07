---
name: writing-code
description: Everything that holds around a code change in any language — probing an unfamiliar boundary before building on it, tracing every caller, comment, test and outside reference it reaches, comment discipline, naming over narration, error returns that match what callers destructure, keeping raw secrets out of logs, guarding at the function boundary, and the reviews the finished diff owes: quick-review always, security-review when the diff touches outside input, auth, the network, a shell, a query, a secret, or a dependency. Routes to the language skill when one exists, and carries references for PostgreSQL schema work and for user interfaces: controls that match how the app already does the same action, and help text that states facts only. Loaded by tdd-cycle before the test, and on its own whenever code, comments, or docstrings change, whenever anything a person reads on an app's screens changes, such as a label, help text, or a tooltip, even in a design document, or when a language has no skill of its own.
---

## Purpose

1. Follow these conventions in every language; `tdd-cycle` drives the loop, and this skill governs what the code and its comments look like once the loop reaches Green.

## Load the language skill first, if there is one

| Language | Skill | Where it lives |
|----------|-------|----------------|
| Elixir, Ecto, Phoenix | `elixir-development` | global |
| CSS, HTML, any user interface that has to work at more than one width | `responsive-design` | global |
| Any edit to a status or health page's markup or styles | `status-page`, before the edit | global |
| PostgreSQL schema: migrations, DDL, `COMMENT ON` | [references/sql-schema-postgres.md](references/sql-schema-postgres.md) | this skill's references |
| A control a person uses: button, form, dialog, inline edit, row action; a label, help text, a definition, or a tooltip on a screen; a link, redirect, or form action built from request parameters; a page's own contents list on a phone | [references/ux-design.md](references/ux-design.md) | this skill's references |
| A how-to or help guide a person reads in the app: its steps, screenshots, problem sections, and links | `writing-prose` [references/how-to.md](../writing-prose/references/how-to.md) | global |
| A Godot game played in a phone's browser: web export, serving it to an iPhone, touch input | [references/godot-web-phone.md](references/godot-web-phone.md) | this skill's references |
| TypeScript: data entering from a request, a file, a model reply, or a query | [references/typescript-parse-at-the-edge.md](references/typescript-parse-at-the-edge.md) | this skill's references |
| Ecto migrations | `elixir-migrations`, `safe-migration` | one project only |
| TypeScript, React | `quality-checks`, `eslint`, `security-review-fe` | one project only |

1. If a project carries its own copy of one of these, use the project copy inside that project and the global one everywhere else.
2. If the language has no skill, such as GDScript, treat this file as its entire convention set and say so in one line.

## Before you change a screen, read the interface reference

1. Before your first edit to a file that renders a control a person uses, such as a view, a template, a component, or a form, read [references/ux-design.md](references/ux-design.md) now.
2. Read it too before you write or change any text a person reads on a screen, such as a label, help text, a definition, or a tooltip, even where that text sits in a design document or a card.
3. In your report on a view edit, name the existing view whose pattern you copied and one thing you matched against it, such as the dialog structure, the button order, or the label pattern.
4. Quote the line from that view and the matching line from your edit, with each file and line number.
5. Do this whatever skill or handoff brought you to the file, and in rapid mode too.

## Probe before you build

1. Before writing more than ~20 lines of code that touches a boundary you don't own, such as an external API, a database schema, a library you haven't used in this session, or a framework convention you're uncertain about, write a throwaway probe and paste its actual output into the conversation.
2. Do the same for code that relies on an algorithm or logic whose behavior you haven't measured in this session, your own expertise included.
3. Run the probe first and write the production code after; cite the probe's output as the REF for that code.

**What is NOT a probe.**

- "The docs say it returns X" — that is intent, not observation, under the
  global Evidence Format's rule that design docs describe intent.
- "I've used this API before" — your memory is a hypothesis, not a measurement.
- "Based on the schema file" — the schema file is a design artifact; the running
  system may differ.
- A `case` clause in your code that "should handle" the API's response —
  speculation, not observation.
- Reading the file at HEAD, a `git diff`, or a grep result — those confirm what
  the code SAYS, not what the running system DOES.

4. Before you write `UNPROBED` for an outside service you may not call, run the client on your side of it: read what the installed CLI or SDK sends for that command, run its serializer or parser on a sample input, and name that check and what it showed in the `UNPROBED` line.
5. If a probe is impractical, write `UNPROBED — <reason>`; if no boundary is crossed, write `EXEMPT — <reason>`.
6. Never stage file reads, greps, or diffs under a "Probe" heading.
7. Apply this rule to code no test drives too; `tdd-cycle` runs it as step 0 against the boundaries the test will touch. Detail and exemptions: `~/.claude/skills/tdd-cycle/references/probing.md`.

## Read a stored value instead of working it out again

1. Before code works out a value by fetching or parsing something, such as a page count, a total, or a status, check whether the database already stores it.
2. If it does, read the stored value, and work it out again only where the data it came from can have changed since it was stored.

## Before the edit: trace its reach

Before writing or dispatching any change, one-line or large, grep for each of these:

1. **Callers** — every call site of the function / GraphQL field / env var /
   module being modified. Check that their expectations still hold after the
   change.
2. **Comments and docstrings** — inline `#` comments, moduledocs, `@doc` blocks
   that mention the function name, the arg name, the return value, or the old
   behavior in prose. If the comment becomes false, fix it in the same diff.
3. **Tests** — assertions, test names, and describe blocks that encode the old
   behavior. Rename tests alongside assertion flips.
4. **External references** — PR bodies, Trello cards, design docs, frontend
   queries, skill frontmatter that describe the old semantic. If the backend
   contract shifted, edit these too.

**Find out why the code is the way it is before you change it.**

1. Read `git log -L` or `git blame` for the lines, the commit messages, the issue they name, and wherever else the team records its decisions.
2. If `~/.claude/CLAUDE-private.md` fills the decision-records slot for this skill, look in the places it names too.
3. If the change is going to a subagent, put all four findings in its prompt up front; `subagents` holds the rest of what that prompt owes, and whether to send one at all.

## Comments

1. **Default: no comment.** If code needs a sentence to explain what it does, rename it or extract a smaller function first, then check whether the sentence is still needed.
2. Keep only a comment that explains a non-obvious why: a constraint you did not choose, an ordering that looks arbitrary and is not, a workaround for a named bug with the bug named, or a tradeoff someone will otherwise "fix" back.
3. **The deletion test.** Before keeping any comment, delete it and read the code; if the code tells you the same thing, leave it deleted. Run this on every comment in the diff, including ones you are touching but did not write.
4. Write one comment per paragraph of code, never per line; if every line needs one, extract a named function.
5. Hold a comment added to a file you did not create to a higher bar: it must be a why, and it must be about the change you are making.
6. Treat doc-comments (`##`, `@doc`, `@moduledoc`, `///`, docstrings) the same: where the language's tooling consumes them, write one line saying what the thing returns, and put design rationale in `docs/`.
7. Describe the code as it stands, never how it got there. Forbidden:

- *History and contrast* — "the prior structure ran…", "now serializes only", "used
  to provide". Git holds the history.
- *Definition by absence* — describing the code by what it is not or no longer does,
  such as "without holding the lock". State what it does, not what it avoids.
- *Rationale for the change* — why the edit was made belongs in the commit message.
  The comment carries only the lasting why a reader needs in order to understand the
  code as written: an invariant it relies on, a safety property that is not obvious.

8. In a test comment, state the invariant the test pins, not the structural mechanism it exercises.
9. **Never leave commented-out code.** Delete it.
10. Make a reference in a comment name a thing the reader can grep for, such as a heading, a symbol, or a quoted phrase, never a line number.
11. **No dead code.** Delete branches the change made unreachable, helpers nothing calls, and temporary variables nothing reads, rather than commenting why they are kept.

## Naming

1. Before writing an explanatory comment, try the rename.
2. Name what the thing IS or DOES, not how it is implemented.
3. Call a function `validate_*`, `verify_*`, or `ensure_*` only if it performs that action; if it only returns a boolean, call it `is_*` or `has_*`.

## Error returns, logs, and untrusted callers

1. **Error returns match what callers destructure.** Route a new error tuple through the existing `else` / `case` branches, and never introduce a shape callers pattern-match but do not handle.
2. **Never log raw sensitive content**: tokens, codes, verifiers, secrets, emails, IPs, request bodies, full changesets, or an `inspect` of a struct that may hold any of those.
3. Delete a log that fires on expected behavior; log what needs human attention at error level, with presence flags or field keys, never raw content.
4. **Parse at the edge, don't validate inside.** Parse outside input once, where it enters, such as a request, a file, a model reply, or a query result, into a declared internal type, pass that type around, and convert it back only on the way out.
5. Do not re-check a parsed type inside the code. If a value inside still has its raw outside shape, trace it back to where it entered and parse it there.
6. Answer a failed parse with that interface's refusal (a 400 over HTTP), never a crash; the language skill or reference in the table above carries how.
7. **Guard at the function boundary, not at the caller.** If a function relies on its caller validating X, and X's type does not already carry the guarantee, guard X here too.

## Product rules that reach the code

- Keep a business fact that users know in data they can edit, never in a
  constant.
- Never guess at ambiguous input, and never normalize away text that may carry
  meaning.
- Store an unknown value as null and derive its default when reading.
  [references/sql-schema-postgres.md](references/sql-schema-postgres.md) has
  the schema side.

## Anyone can rebuild what the code reads

1. Ship the script itself, never instructions for writing one.
2. Fix a temporary tool of your own, such as a probe, a driver, or a harness, without asking.
3. If code or a test reads a file, such as a fixture, an answers file, a seeded database, or a harness directory, make that file with a committed script beside the code, and have the test or the setup step run it.
4. Make a README tell the reader which commands to run, each running a committed script, and never carry a block of code to paste into a shell or an editor.

## Measure before declaring done

1. Before every commit, run this from the repository root:

```bash
python3 ~/.claude/skills/writing-code/scripts/comment_share.py
```

2. Pass `--base <ref>` to measure from a ref other than the merge base with origin's default branch; the script counts committed, uncommitted, and untracked lines, and skips prose files and `COMMENT ON` text.
3. Give every listed block "keep" with the non-obvious why it explains, or "delete", whatever the share; delete what fails, then run the script again.
4. **Above 10% in any one file, read that file's blocks a second time.** A file that is genuinely one tricky function with one paragraph of justification can sit above it and say so.
5. Report the per-file numbers and each block's disposition when you report the change.

## After the edit: the review sequence is owed

Any code change, however small, owes this review sequence before the commit decision arises:

0. If the change reaches something a person sees, clicks, or plays, run it
   the way the project runs locally — a dev server, a scene in the game
   engine's editor, a desktop build, a terminal app — and use it the way a
   person would: open it, click, type, play, and watch what comes back. Do
   this after every change you can see, not only once, and again before the
   reviews; fix what it finds first. If `project-drive`
   appears in the available skills, load it for how to send this product
   real input. If nothing is listed, work it out and say in one line what
   you did.
1. `quick-review` against the change.
2. `security-review` against the change, when the diff touches any of these:
   input from outside the program (a request, a file, the clipboard, a message,
   a command-line argument), authentication or authorization (a session, a token,
   or an OAuth, OIDC, SAML, or other sign-in route included), a network call or
   a listening server, a shell or subprocess command, a SQL or other query
   string, a secret, token or credential, a file path built from input,
   deserialization, or an added or changed dependency. When it touches none of
   them, say so in one line and skip it.

Then:

1. Run the reviews inline in this session, never in subagents; `subagents` carries the measurement.
2. Present the findings to the user and wait for explicit per-action authorization before any commit, amend, or push, under `git-commit`'s rules.
3. Handle the findings by `quick-review`'s "Re-review and the fix loop".
4. **Prose-only diffs are exempt.** If no hunk anywhere in the diff is an executable change, only prose files (`*.md`, `*.txt`, `*.rst`) or comment-only hunks, skip the sequence; otherwise the whole diff is in scope.
5. Before the diff is written, back every boundary claim it will encode with a probe REF from this session, under "Probe before you build" above.

## What this skill does not cover

- Test structure and the red-green-refactor loop: `tdd-cycle`.
- What the review passes look for: `quick-review` and `security-review`; this skill says when they run.
- Commit and push authorization, and commit messages: `git-commit`.
- Prose written to the user: Communication Style in the global `CLAUDE.md`.
