---
name: create-task-skill
description: Produces a verified plan for a new task-shaped skill — one whose point is forcing a specific ordered response as proof the rules were followed — by probing boundaries, confirming every cited skill is globally invokable, drafting a body whose sections are the forcing chain, and reviewing it against the meta-rules; stops for approval before any file is written. Use when building a skill of that shape; `systematize` covers the ordinary kind and routes here.
---

# create-task-skill — build a new task skill via the same discipline

1. For the proposed task skill in $ARGUMENTS (or interactively gathered), respond with the following sections in order.
2. Do NOT create the skill file; produce a verified plan and stop at the write step for explicit approval.
3. Put actual tool output in each section, not paraphrased summaries, and keep the order, because each section's output anchors the next.

## The core insight (read once, then apply to the sections below)

1. Design the skill body to force a specific, ordered response that can only be produced honestly if the rules were followed.
2. Make each section depend on the real output of the one before it, so a faked upstream section shows in the section downstream.

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

1. If any input is unclear, ASK the operator before proceeding; never pattern-match a plausible value into one of these slots.

## Probe Phase

1. Paste real output, not paraphrase.

### Boundary probes

1. For each command, API call, or shell pattern the new skill will reference, run a one-shot probe and paste its real output:

```
$ <command>
<actual output>
```

### Cited-skill availability probes

1. For each skill the new skill cites by name, verify it is in a globally invokable location:

```
$ find ~/.claude/skills ~/.claude/commands \
       -maxdepth 2 -ipath "*<skill>*" -name "*.md" 2>/dev/null
$ find ~/.claude/plugins -maxdepth 8 -ipath "*<skill>*" \
       -name SKILL.md 2>/dev/null
```

2. Match the path, not the filename, because a global skill is a *directory* named after the skill holding a `SKILL.md`; never use `-iname "<skill>*" -type f`.
3. Run both finds, because a plugin skill at user scope sits seven levels under `~/.claude/plugins`; cite a plugin skill as `plugin-name:skill-name`.
4. Never edit a plugin skill, because the next plugin update overwrites its directory; wrap it instead, citing it for what it owns and adding only what it does not.
5. If NEITHER find locates the skill, treat it as project-scoped, never reference it as `/skill-name` from a global task skill, and take one of three options:

- (a) Inline the relevant mechanics directly into the new skill so it
  is self-contained
- (b) Move or copy the cited skill to a global location
- (c) Replace the citation with a globally-available alternative

### CLAUDE.md probes

1. For each CLAUDE.md rule the new skill relies on, show the line range and the exact rule name, in this shape:

```
~/.claude/CLAUDE.md  "Evidence Format (HARD CONSTRAINTS)"  → ref
skills/writing-code   "Probe before you build"               → ref
skills/writing-code   "After the edit: the review sequence"  → ref
~/.claude/CLAUDE.md  rule 11 (design docs describe intent)  → ref
```

2. Make the new skill reference those rules, never duplicate them.

## Draft Body

Propose the full skill body in a fenced block, exactly as it will appear in the file, including:

1. **frontmatter**: `name` and `description`. The description states
   what the skill produces and ends with a "Use when…" clause naming
   the words, file types and errors that mean this skill applies —
   the trigger terms `systematize` step 2 requires. While a new
   template is still being iterated on, say so in the body; never
   withhold the triggers from the description.
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

1. State Y/N with reasoning for each:

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

2. On any N, return to Draft Body, fix, and re-review; never advance to Write Plan with open gates.

## Write Plan

```
Path:     ~/.claude/skills/<skill-name>/SKILL.md
Action:   mkdir -p <skill-dir> && Write SKILL.md
Bytes:    <approximate count>
Row:      <the routing row, quoted exactly as it will read>
Table:    <~/.claude/CLAUDE.md, or the private table when the row names
           mechanics only one machine carries>
```

1. Ship the routing row with the skill, in the same change.
2. Write the row's topic column in the words the operator would actually use, and check it against every row already in the table so no topic restates its neighbour.

## Stop — awaiting approval before writing

1. Do not call mkdir or Write yet; the operator approves the write, routing row included, as a separate action.
2. Follow this iteration discipline:

- Build ONE new task skill and use it on real tasks for a week or two
  before starting another
- After it earns its keep, add a second; discover overlap and
  ambiguity between them at that point
- Only then build a router with outcome-shaped discriminators
- Only after the router stabilizes, add the echo-back-for-approval gate
- Do NOT pre-build a grid of templates speculatively. Rule of three
  applies in retrospect: lift to a router only when a third template's
  arrival makes the routing question concrete

## Notes on what this template does NOT do

- Does not write the skill file or its routing row. Both go in one
  change, and that change is a separate authorization.
- Does not reference any skill that has not been verified as globally
  invokable in the Probe Phase.
- Does not duplicate content from CLAUDE.md; references it.
- Does not decide whether the new skill hands off to another one.
  Some do — `pr-feedback-task` hands its accepted findings to
  `retro-task` — but a hand-off is designed
  deliberately for that skill, never inherited from this template.
- Does not build the router, echo-back gate, or any harness-level
  forcing function. Those become reasonable only after enough
  templates exist to make routing concrete.
