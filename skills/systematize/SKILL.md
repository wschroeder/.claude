---
name: systematize
description: Turns work you have repeated into machinery, and keeps the skill library from growing past the point where the model stops finding things. Covers the whole lifecycle — deciding between a script and a skill, where a script lives and when to extend an existing one rather than write another, creating a skill, extending one, merging two, and retiring one — plus the slot pattern that lets a global skill reach project-specific mechanics without naming them. Use when a workflow keeps recurring, when something done by hand three times should become a script, when asked to capture or save something as a skill, when a skill is outdated or wrong, when two skills overlap, or when the library needs pruning.
activation:
  - "extract this as a skill"
  - "create a skill from this"
  - "make this a skill"
  - "make this a script"
  - "should this be a script or a skill"
  - "we keep doing this by hand"
  - "save this workflow"
  - "capture this pattern"
  - "update this skill"
  - "improve this skill"
  - "merge these skills"
  - "consolidate skills"
  - "retire this skill"
---

# systematize — machinery for what you repeat, without a library nobody can search

## When this fires

Having done the same thing by hand in three separate sessions. Not twice, and
not "this could recur" — three times, observed.

The test is the same **operation**, not the same command names. Three unrelated
things that each begin with `git status` are not a pattern. A probe written,
run, and cleaned up by hand in thirty sessions is.

## First decide: script or skill

Getting this wrong is worse than doing nothing.

**A sequence of commands that is the same every time is a script.** It never
becomes a skill. A skill makes the next session read a paragraph where it could
have run one command, and it pays that cost on every load.

**A judgment that keeps coming out wrong the same way is a skill.** The thing
being captured is a decision, an order of investigation, a trap worth naming —
something a command cannot encode.

**Most repetition is neither**, and gets nothing.

### Where a script lives

- If anything other than a skill would still call it — a task-runner recipe, a
  design doc, CI, a person — it goes in the project's existing `scripts/`
  directory, exposed through the task runner.
- If deleting the skill would leave it with no caller, it goes with the skill at
  `<skill>/scripts/`, and is deleted when the skill is.

Never a new top-level directory. Every script gets a test beside it, and the
skill-owned tests are wired into the project's gate with a glob so a new skill
joins without the gate being edited.

### A new script is the last resort too

The same rule that governs skills below. Before writing one, find out whether an
existing script already does the reading yours would have to do — the same files
parsed, the same filtering, the same output. Extend that one. A second script
beside it parses the same files again, drifts from the first, and only one of the
two has tests.

Finding it is the hard part, because a skill's own machinery sits at
`<skill>/scripts/` and nothing lists it. Look in two places before you start: the
skill descriptions already in front of you, since a skill that owns a script
usually names it there, and then the `scripts/` directory of whichever skill the
work touches. Measured on the session that prompted this line — it worked out
where a run's tokens had gone using throwaway python, while
`session-loop/scripts/session_budget.py` already read those same transcripts and
was named in that skill's own description, which had been in context since the
first turn.

## The three-level hierarchy

Skills load in layers. Every edit respects these budgets:

| Layer | What | When loaded | Budget |
|-------|------|-------------|--------|
| Metadata | Frontmatter: name, description, activation | Every session | ~100 tokens |
| Core instructions | SKILL.md body | On activation | under 500 lines |
| References | `references/*.md` | Read on demand | Unbounded |

A skill body is declarative. It says what to do, in what order, and what not to
do. It does not argue the case. Rationale, measurements, research citations,
worked derivations and the history of why a rule was tightened all belong in
`references/`, where a reader who disputes a rule pays for the argument and
nobody else does. The test: delete a sentence and ask whether the instruction
still tells you what to do. If it does, the sentence was the treatise, and it
moves.

Heavy content — templates, scripts over 20 lines, full API examples, large
lookup tables — belongs in `references/`, linked with a plain markdown link:
`See [references/foo.md](references/foo.md)`.

Reference files over 100 lines open with a table of contents. SKILL.md is the
index; references are the detail. A reference may point at another reference —
that is lazy loading working, and a cross-reference made in context is worth
keeping. Two shapes are not. A chain, where opening one file obliges you to open
a third, makes the cost of following a link unbounded; keep every target a leaf.
And the instruction to open a given file belongs in exactly one place: a
reference that restates the body's own pointer gets that file read twice.

## Creating a skill

Creating a new skill is the **last** resort. Try adding a section to an existing
skill first, and create a new one only when you can say which existing skills
you considered and why each is a poor home.

For a task-shaped skill — one whose whole point is forcing a specific ordered
response as proof the rules were followed — use `create-task-skill` instead.
This skill covers the ordinary kind.

### 1. Name what recurred

What operation, what problem it solves, what should pull the skill in, and what
the steps actually are. Pull them from the sessions where it happened rather
than from how you would describe it now.

### 2. Write the description

The description is the only part loaded every session, so it is the whole of
what the model has when deciding whether to open the skill.

- Third person: "Guides Claude through…", "Turns…", "Covers…".
- Name the trigger terms — the specific words, errors, or file types that mean
  this skill applies.
- Under 1024 characters, specific rather than generic.
- Say what makes it *different* from its neighbours. A description that could
  equally describe two skills is how the wrong one gets picked.

### 3. Choose activation keywords

Natural phrasings, not just technical ones. Include the casual form and the
precise form, and the errors a person would paste.

### 4. Write the body

```markdown
---
name: [kebab-case-name]
description: [third person, trigger terms, under 1024 chars]
activation:
  - "[keyword]"
---

## Purpose
[What this helps with, and when]

## Process
### 1. [Step]
### 2. [Step]

## Key guidelines

## Examples
### What good looks like
### What to avoid

## Autonomous behaviour
[When to act without asking, when to stop and ask, what to report]
```

Every example in the body must have been run. An example nobody executed is the
most expensive kind of wrong, because it is the part a reader copies.

### 5. Propose before writing

Show the frontmatter and the section outline, say which existing skills you
considered, and wait. Write the file only after approval.

### 6. Add the routing row in the same edit

A skill nothing routes to is a skill nothing loads.

## Slots: reaching project mechanics from a global skill

A global skill must never name a project's commands. Instead it names a slot:

> If `project-<step>` appears in the available skills, load it. If nothing is
> listed, do the step by hand and say so in one line.

The project fills the slot with a project skill of that name under
`<repo>/.claude/skills/`. Adding one modifies no existing skill, and the skill
listing every session already carries is what makes it discoverable — no lookup
call needed.

`tdd-cycle` step 0 and `project-probe` are the worked example.

## Updating a skill

Read the whole skill first. Keep what works; change what is wrong.

**Just do it** for typos, a missing example, clearer wording, an obvious extra
activation keyword.

**Ask first** for restructuring, removing sections, changing what the skill is
for, or anything that would conflict with another skill.

When the body passes 500 lines, move heavy content into `references/` rather
than trimming the substance.

## Merging skills

Merge when skills overlap in purpose, are always used together, duplicate each
other's content, or are so granular they should have been sections.

Do not merge skills with different purposes that merely touch, skills with
conflicting approaches, or skills that are already focused.

1. Read every skill being merged, in full.
2. For each, name its core purpose, its unique value, and what it duplicates.
3. Design the merged skill — a name covering all of them, one description, the
   union of activation keywords with duplicates dropped, and content organised
   logically rather than concatenated.
4. Show the outline and what is being dropped. Wait for approval.
5. Write the merged skill.
6. Delete the old files, update every routing row, and grep for anything else
   that named them. A merge that leaves the old names referenced is half done.

Watch for content that has gone stale in one of the sources — a tool that is no
longer used, an example naming something retired. A merge is the moment to drop
it, not carry it forward.

## Retiring a skill

The half that keeps a library usable.

Retire when nothing has loaded it in months, when its content moved into another
skill, or when the thing it describes no longer exists. Delete the directory,
delete the routing row, and grep for the name across skills and CLAUDE.md files.

Prefer retiring to keeping something "in case" — a skill kept for a case that
never comes still costs every load, and still competes with the right skill for
selection.

## The cap, and why it is a hard rule

Adding a skill makes every other skill harder to find. What degrades first is
**selection**, not the context budget — the model picks the wrong skill because
a similar description shadowed the right one.

Measured, in *More Skills, Worse Agents? Skill Shadowing Degrades Performance
When Expanding Skill Libraries* (Databricks, 2026): pass rate dropped 21% going
from a small useful set to 202 skills, shadowing accounted for up to 68% of the
loss and was the only statistically significant effect, and the share of runs
choosing the right skill fell from 88.0% to 52.6%. Degradation was already
measurable at 52 skills and rose monotonically with size.

So the global set is capped at about two dozen. A new global skill that would
push it past that means merging or retiring one first, in the same change.
Project skills sit in their own repo and are counted against that repo, not the
global set.

## What makes a good skill

Repeated multi-step workflows. Decision frameworks used often. Safety-critical
processes. Traps that are easy to forget and expensive to rediscover.

Not: one-off tasks, processes too variable to write down, things already
documented where a reader would look anyway, a single command, or anything
needing human judgment at every step.

## What not to do

- Do not create a skill for something a script should do.
- Do not rewrite an existing skill wholesale without asking.
- Do not remove content before understanding why it is there.
- Do not let SKILL.md pass 500 lines without splitting into `references/`.
- Do not build a mega-skill that covers everything; it will shadow the rest.
- Do not leave old names referenced after a merge or a retirement.
