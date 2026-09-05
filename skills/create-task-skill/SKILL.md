---
name: create-task-skill
description: Produces a verified plan for a new task-shaped skill — one whose point is forcing a specific ordered response as proof the rules were followed — by probing boundaries, confirming every cited skill is globally invokable, drafting a body whose sections are the forcing chain, and reviewing it against the meta-rules; stops for approval before any file is written. Use when building a skill of that shape; `systematize` covers the ordinary kind and routes here.
---

# create-task-skill — build a new task skill via the same discipline

For the proposed task skill in $ARGUMENTS (or interactively gathered),
respond with the following sections in order. Do NOT create the skill
file — this template produces a verified plan and stops at the write
step for explicit approval.

The output discipline is recursive: this skill follows the pattern it
teaches. Each section contains actual tool output, not paraphrased
summaries. Order is enforced because each section's output anchors the
next, AND each section's downstream requirement constrains the
fidelity of the section above it.

## The core insight (read once, then apply to the sections below)

Task skills turn rule-following from a *side-promise* into an
*output-shaped proof obligation*. The skill body forces a specific,
ordered response. The response artifact can only be generated
honestly if the rules were followed. Sections must contain real tool
output because the section that comes next depends on it; and the
upstream section must be honest because the downstream section will
exhibit the fakery if it isn't. Both directions of the chain forcing
matter.

## Inputs

```
Skill name:           <kebab-case, e.g. "investigate-task", "migrate-task">
Outcome shape:        <diff | recommendation | report | review-comment>
                      (this is what the response ultimately produces;
                      it is the routing discriminator we'll use later
                      when a router gets built)
Boundaries touched:   - <each external command, API, schema, library,
                          or file path the skill body will reference>
                      - ...
Cited skills:         - <skill name>  (must be verified globally
                          invokable — see Probe Phase)
                      - ...
CLAUDE.md sections
  referenced:         - <section names or rule numbers; do not duplicate
                          their content, reference them>
```

If any input is unclear, ASK the operator before proceeding. Do not
pattern-match a plausible value into one of these slots — wrong inputs
here cascade into a misshapen skill body.

## Probe Phase

Real output, not paraphrased.

### Boundary probes

For each command, API call, or shell pattern the new skill will
reference, run a one-shot probe and paste its real output:

```
$ <command>
<actual output>
```

Cautionary tale this catches: in an earlier session a skill was drafted
citing `gh pr view --json reviewThreads` because the Linear workflow
doc mentioned the GraphQL field `reviewThreads`. The command does not
exist — `reviewThreads` is a GraphQL-only field, accessed via
`gh api graphql`. The pattern-match cost a round-trip. The fix is the
probe.

### Cited-skill availability probes

For each skill the new skill cites by name, verify it is in a globally
invokable location:

```
$ find ~/.claude/skills ~/.claude/commands \
       -maxdepth 2 -ipath "*<skill>*" -name "*.md" 2>/dev/null
$ find ~/.claude/plugins -maxdepth 8 -ipath "*<skill>*" \
       -name SKILL.md 2>/dev/null
```

Match the path, not the filename. A global skill is a *directory* named
after the skill holding a `SKILL.md`, so `-iname "<skill>*" -type f`
matches nothing and reports every installed skill as missing. The
`-maxdepth 2` keeps the output to one line per skill by excluding
`references/*.md`, and still catches a `~/.claude/commands/<skill>.md`.

Both finds are required. A skill installed by a plugin at user scope
resolves globally but sits seven levels under `~/.claude/plugins`, so the
first find alone reports it missing — a false negative that sends the
draft off to inline mechanics it should have cited. Cite a plugin skill
as `plugin-name:skill-name`.

A plugin skill is also effectively immutable: its directory is a
version-pinned cache that the next plugin update overwrites. A global
skill that adds to one wraps it — cites it for what it owns, adds only
what it does not — and never edits it.

If NEITHER find locates the skill, it is project-scoped and CANNOT be
referenced as `/skill-name` from a global task skill. Three options:

- (a) Inline the relevant mechanics directly into the new skill so it
  is self-contained
- (b) Move or copy the cited skill to a global location
- (c) Replace the citation with a globally-available alternative

Cautionary tale: an earlier draft of a task skill referenced
`/respond-all` as a handoff, but `respond-all` lives under
`~/dev/{ai*,legends-*}/.claude/skills/` only. The citation would have
been a broken pointer from anywhere outside those project trees. The
fix was to inline the verified reply syntax.

### CLAUDE.md probes

For each CLAUDE.md rule the new skill relies on, show the line range
and the exact rule name. The new skill REFERENCES — it does not
duplicate. Example:

```
~/.claude/CLAUDE.md  "Evidence Format (HARD CONSTRAINTS)"  → ref
skills/writing-code   "Probe before you build"               → ref
skills/writing-code   "After the edit: the review sequence"  → ref
~/.claude/CLAUDE.md  rule 11 (design docs describe intent)  → ref
```

CLAUDE.md is the dictionary; the task skill is the form. Duplicating
the dictionary into the form creates drift the moment CLAUDE.md changes.

## Draft Body

Propose the full skill body in a fenced block, exactly as it will
appear in the file. The body must include:

1. **frontmatter**: `name` and `description`. The description states
   what the skill produces and ends with a "Use when…" clause naming
   the words, file types and errors that mean this skill applies —
   the trigger terms `systematize` step 2 requires. A description that
   only says what the skill produces gives the model no way to reach
   it, so the skill runs only when the operator types its name. While
   a new template is still being iterated on, say so in the body; do
   not withhold the triggers from the description to achieve it.
2. **Opening paragraph**: what the template produces, when it stops,
   and that section order is enforced.
3. **Ordered sections** with structural headers. Each section
   specifies what counts as valid output (e.g., "real shell output,
   not paraphrased"). The sections form a bidirectional forcing chain.
4. **Stop section** before any destructive action (write, post,
   commit, push). State that prior approval in the session does NOT
   carry forward — each destructive action needs its own
   authorization per `git-commit`, "Safety".
5. **"Notes on what this template does NOT do"** closing section.
   Explicit boundary list — what is out of scope, what does not chain,
   what is not auto-executed.

## Review against the meta-rules

State Y/N with reasoning for each:

```
- Each section forces real tool output (verbatim, not paraphrase)?
  → <Y/N + which sections, and how the output is produced>
- Bidirectional forcing chain present
  (each section's output anchors next; next constrains current)?
  → <Y/N + describe the chain>
- Stop-and-await-approval before every destructive action?
  → <Y/N + where each stop lives>
- All cited skills verified globally invokable?
  → <Y/N + list>
- No auto-activation triggers in description?
  → <Y/N + quote the description>
- CLAUDE.md content referenced, not duplicated?
  → <Y/N + list refs>
- "What this template does NOT do" closer present?
  → <Y/N>
- Outcome shape is unambiguous (one of: diff, recommendation,
  report, review-comment)?
  → <Y/N + which>
- Section count is justified — every section earns its keep on a
  real task; no ceremonial padding?
  → <Y/N + justification per section>
```

Any N → return to Draft Body, fix, re-review. Do not advance to Write
Plan with open gates.

## Write Plan

```
Path:     ~/.claude/skills/<skill-name>/SKILL.md
Action:   mkdir -p <skill-dir> && Write SKILL.md
Bytes:    <approximate count>
Mapping:  NONE — unmapped during the iteration window
```

## Stop — awaiting approval before writing

Do not call mkdir or Write yet. The operator approves the write as a
separate action. Per the iteration discipline established when this
pattern was built:

- Build ONE new task skill, leave it unmapped, use it on real tasks
  for a week or two
- After it earns its keep, add a second; discover overlap and
  ambiguity between them at that point
- Only then build a router with outcome-shaped discriminators
- Only after the router stabilizes, add the echo-back-for-approval gate
- Do NOT pre-build a grid of templates speculatively. Rule of three
  applies in retrospect: lift to a router only when a third template's
  arrival makes the routing question concrete

## Notes on what this template does NOT do

- Does not write the skill file. Writing is a separate authorization.
- Does not add the new skill to any CLAUDE.md routing table.
- Does not reference any skill that has not been verified as globally
  invokable in the Probe Phase.
- Does not duplicate content from CLAUDE.md; references it.
- Does not decide whether the new skill hands off to another one.
  Some do — `pr-feedback-task` hands its accepted findings to
  `pr-respond-task` behind a gate — but a hand-off is designed
  deliberately for that skill, never inherited from this template.
- Does not build the router, echo-back gate, or any harness-level
  forcing function. Those become reasonable only after enough
  templates exist to make routing concrete.
