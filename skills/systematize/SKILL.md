---
name: systematize
description: Turns work you have repeated into machinery, and keeps the skill library from growing past the point where the model stops finding things. Covers the whole lifecycle — deciding between a script and a skill, where a script lives and when to extend an existing one rather than write another, creating a skill, extending one, merging two, and retiring one — plus the slot pattern that lets a global skill reach project-specific mechanics without naming them. Use when a workflow keeps recurring, when something done by hand three times should become a script, when asked to capture or save something as a skill, when a skill is outdated or wrong, when two skills overlap, or when the library needs pruning.
---

## When this fires

1. Build machinery once you have done the same operation by hand in three separate sessions, observed, not predicted.
2. Judge sameness by the operation, not by the command names it starts with.
3. Fix the third repetition before you continue the work that surfaced it.

## First decide: script or skill

1. Make a sequence of commands that is the same every time into a script, never a skill.
2. Make a judgment that keeps coming out wrong the same way into a skill: a decision, an order of investigation, or a trap worth naming.
3. Give most repetition neither.

### Where a script lives

1. Put a script that anything besides a skill would call, such as a task-runner recipe, CI, or a person, in the project's existing `scripts/` directory, exposed through the task runner.
2. Put a script only one skill calls at `<skill>/scripts/`, and delete it with the skill.
3. Never create a new top-level directory for scripts.
4. Give every script a test beside it, and wire skill-owned tests into the project's gate with a glob.

### A new script is the last resort

1. Before writing a script, look for one that already reads the same files, filters the same way, or prints the same output, and extend it.
2. Look in the skill descriptions in front of you and in the `scripts/` directory of each skill the work touches.

## The three-level hierarchy

| Layer | What | When loaded | Budget |
|-------|------|-------------|--------|
| Metadata | Frontmatter: name and description | Every session | ~100 tokens |
| Core instructions | SKILL.md body | On activation | under 500 lines |
| References | `references/*.md` | Read on demand | Unbounded |

1. Keep each layer inside its budget.
2. Write the body as instructions only: what to do, in what order, and what not to do.
3. Put rationale, measurements, research citations, and history in `references/`; if deleting a sentence leaves the instruction intact, move it.
4. Put templates, scripts over 20 lines, full API examples, and large lookup tables in `references/`.
5. Open a reference over 100 lines with a table of contents.
6. Keep every reference a leaf: a reference may point at another, but never at one that obliges a third.
7. Give the order to open a given reference in exactly one place.
8. Point at a required reference at the step that needs it, with a condition the model can check ("if the diff adds a migration") and an order to read it now, because a model skips a bare "see" link.
9. Put a required step in the body or behind a pointer of that shape; only rationale may sit behind a bare link.

## Write rules as a short list

This holds for `~/.claude/CLAUDE.md` and for every skill body and reference.

1. State each rule as a numbered imperative of one or two sentences.
2. Keep a short "such as" phrase only when it names what triggers the rule.
3. Cut every BAD and GOOD pair, worked example, and "Measured on" story.
4. Delete a cut example; never move it into `references/`.
5. Keep ordered steps, commands, templates, lookup tables, and scripts, because they are not examples.
6. Name a rule by its topic, such as "the comma rule", and never by its number.

## Creating a skill

1. Try adding a section to an existing skill first, and create a new one only when you can name the skills you considered and why each is a poor home.
2. For a task-shaped skill, one that forces a specific ordered response as proof the rules were followed, use `create-task-skill` instead.

### 1. Name what recurred

1. Name the operation, the problem it solves, what should pull the skill in, and the steps, taken from the sessions where it happened.

### 2. Write the description

1. Write it in the third person: "Guides Claude through…", "Turns…", "Covers…".
2. Name the trigger terms: the words, errors, and file types that mean this skill applies.
3. Keep it under 1024 characters.
4. Say what makes the skill different from its neighbours.
5. Put the trigger phrasings in the description's sentences, the casual and the precise form, because `activation:` is not a real field and nothing reads it.

### 3. Write the body

```markdown
---
name: [kebab-case-name]
description: [third person, trigger terms, under 1024 chars]
---

## Purpose
[What this helps with, and when]

## Process
### 1. [Step]
### 2. [Step]

## Rules
1. [One- or two-sentence imperative]

## Autonomous behaviour
[When to act without asking, when to stop and ask, what to report]
```

1. Run every command in the body before you write it down.

### 4. Propose before writing

1. Show the frontmatter, the section outline, and the skills you considered, and wait for approval before writing the file.

### 5. Add the routing row in the same edit

1. Add the skill's routing row in the edit that creates it.

## Slots: reaching project mechanics from a global skill

1. Never name a project's commands in a global skill; name a slot instead:

> If `project-<step>` appears in the available skills, load it. If nothing is
> listed, do the step by hand and say so in one line.

2. Fill the slot with a project skill of that name under `<repo>/.claude/skills/`.
3. Use `tdd-cycle` step 0 and `project-probe` as the model.

## Updating a skill

1. Read the whole skill first.
2. Make typo fixes, clearer wording, and an obvious missing trigger phrasing without asking.
3. Ask first before restructuring, removing a section, changing what the skill is for, or anything that conflicts with another skill.
4. When the body passes 500 lines, move heavy content into `references/` rather than trimming the substance.
5. Commit every edit to a skill or to `~/.claude/CLAUDE.md` in the turn that makes it, through `git-commit`, staging by path.

## Keep every client and project out of `~/.claude`

`~/.claude` is a public repository. This covers skill bodies, references, scripts and their comments, CLAUDE.md, and commit messages.

1. Leave out client, vendor, product, and project names, and the names of systems a client uses.
2. Leave out ticket keys, bead ids, pull request numbers, and repository or worktree names.
3. Leave out the client's domain nouns, such as what the app's records are and what its users do with them.
4. Leave out table, column, function, route, file, and log-event names from a client's code, and data values quoted from it.
5. Leave out the names of people other than the operator.
6. Keep the failure itself, written with neutral stand-ins such as a record, a customer, an outside system, a nightly sync, and `ABC-123`.
7. Date a measurement in a reference, and give it no ticket.
8. Keep the names of public tools, libraries, and published research.
9. Name no issue in a `~/.claude` commit, overriding `git-commit`'s rule to name the tracking issue.
10. Before every commit in `~/.claude`, read each added line of `git diff --cached`, the message included, against this list.

## Merging skills

1. Merge skills that overlap in purpose, are always used together, duplicate each other, or are so small they should be sections.
2. Do not merge skills with different purposes that merely touch, skills with conflicting approaches, or skills that are already focused.
3. Read every skill being merged in full.
4. For each, name its core purpose, its unique value, and what it duplicates.
5. Design the merged skill: one name covering all of them, one description carrying every trigger phrasing the originals had, and content organised by topic.
6. Show the outline and what you are dropping, and wait for approval.
7. Write the merged skill.
8. Delete the old files, update every routing row, and grep for anything else that names them.
9. Drop stale content, such as a retired tool, rather than carrying it forward.

## Retiring a skill

1. Retire a skill nothing has loaded in months, one whose content moved elsewhere, one whose subject no longer exists, or one that cannot show it improved quality.
2. Delete the directory and the routing row, and grep for the name across skills and CLAUDE.md files.
3. Prefer retiring to keeping a skill "in case".

## The cap

1. Keep the global set at about two dozen skills, because each new skill makes the model pick the wrong one more often.
2. Merge or retire a global skill in the same change as any addition that would pass the cap.
3. Count project skills against their own repository, not the global set.

## What makes a good skill

1. Capture repeated multi-step workflows, decision frameworks used often, safety-critical processes, and traps that are expensive to rediscover.
2. Do not capture one-off tasks, processes too variable to write down, things already documented where a reader would look, a single command, or anything needing human judgment at every step.

## What not to do

1. Do not create a skill for something a script should do.
2. Do not rewrite an existing skill wholesale without asking.
3. Do not remove content before understanding why it is there.
4. Do not build a mega-skill that covers everything.
5. Do not leave old names referenced after a merge or a retirement.
