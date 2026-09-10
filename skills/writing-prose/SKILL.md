---
name: writing-prose
description: Composes prose a person reads for its argument — dumping every point before any order, heading, or count exists, then deriving the grouping and the sequence from what those points require of each other, then writing the headings and titles last, from the finished body. Scales to the output: one point needs no machinery, several parts need a traced list, and a document a reader navigates needs an idea graph with a derived order. Use when writing or restructuring an email, a design document, a README, a findings report, a memo, or a proposal; when organizing a brain dump; when settling section order, headings, or titles; or when prose reads as AI-written. Cites `~/.claude/CLAUDE.md` "Communication Style" for every sentence-level rule and never restates it.
---

## Purpose

This skill owns **composition**: what gets said, in what order, under what
headings. Three other places own the rest, and this file never restates them.

- `~/.claude/CLAUDE.md` "Communication Style (HARD CONSTRAINT)" owns every rule
  about a sentence — the actor and the verb, commas, invented labels, the colon
  for a follow-on sentence, where the ask goes. Those rules apply to everything
  you emit, this reply included, whether or not this skill is loaded.
- `writing-code` owns code and the comments inside it. It decides whether a
  comment should exist at all and what it may say; the first tier below governs
  only how the sentence reads.
- A branded print build — a brand, a page format, and a PDF — belongs to
  whichever skill your private routing names for it. This skill reaches that
  skill only when the ask names that kind of deliverable, and it never decides
  the brand itself.

## Pick the tier first

**The test: does the output have parts whose order could be wrong?**

Count the parts you are planning. Not words — parts. A doc-comment has one. A
design document has many.

| Parts | Tier | Machinery |
|-------|------|-----------|
| One point, no sections | Tier one | none |
| Several parts, one sitting | Tier two | a list in your working notes |
| Sections a reader navigates | Tier three | an idea file and a graph |

**Erring upward is the failure mode this test exists to prevent.** Building a
graph for a two-sentence comment is worse than loading nothing, because it spends
the reader's patience and yours on a structure with one node. When the tier is
genuinely unclear, take the lower one and say in one line which you took.

---

## Tier one — one point, no sections

A code comment, a commit message, a Slack reply, a short email, a one-paragraph
answer.

The CLAUDE.md sentence rules apply, and no composition machinery does. Write it,
then read it once against those rules. Do not dump, do not outline, and do not
announce a count.

One addition, because it is the only ordering decision a single point has: say
the point in the first sentence. Everything after it is support.

Register — how formal to be, how warm, and how much of the reader's own world
to explain back to them — is neither a sentence rule nor a composition
decision, so neither CLAUDE.md nor this body covers it. Read
[references/register.md](references/register.md) before writing as the operator
to someone they have written to before.

---

## Tier two — several parts, one sitting

An email carrying three asks, a PR body, a findings report, an in-repo README,
one section of a design document, a handoff.

### 1. Dump the parts before deciding anything about them

Write every point you might make, one per line, in your working notes. No
numbers, no headings, no ordering, and no count of how many there will be. The
dump is allowed to be longer than the output.

A point that came from your own knowledge rather than from a source gets a line
saying so. That list is allowed to be long. It is not allowed to be invisible.

### 2. Order the parts by what each needs the reader to already have

For each part, name what the reader must already hold to understand it. A part
whose prerequisite comes later moves after it. Parts with no prerequisite can go
anywhere, and that freedom is a choice you make rather than a constraint you
discovered.

### 3. Check three things before you write the headings

- **Every part in the output traces to a line in the dump.** A part with no line
  behind it was invented during layout, which is where the worst ordering
  defects come from. Either add its line to the dump, or cut the part.
- **Every line in the dump either lands in a part or gets a one-line reason for
  being dropped.** A line that silently vanishes is a decision nobody recorded.
- **Nothing announces a count.** "Three things", "the four questions", "two
  reasons" — a count written before the items exist is a promise the rest of the
  output then has to keep, and it keeps it with filler.

### 4. Write the headings, the opening summary, and the title last

A heading is a claim about what a section contains, so it cannot be written
honestly before the section exists. Write the body, then read each part and name
what it actually says. If a heading names something the part's own prose never
mentions, the heading is wrong, not the prose.

An opening summary is the same case, one level up: it summarizes a body, so it
comes after the body.

---

## Tier three — sections a reader navigates

A design document, a whitepaper, a deck, a specification, a long report.

The steps are ordered, and each one's output is what the next one reads. Do not
run them out of order and do not skip the printing — a structure nobody printed
is a structure nobody reviewed.

### 0. Write the one sentence, and the word budget

Before dumping anything, write the single sentence the whole document argues, and
the number of words it gets. Both go at the top of `ideas.tsv` as comments.

**The sentence is the filter.** Every idea earns its place by serving that
sentence, and an idea that is merely true, merely interesting, or merely nearby
is a rabbit hole that costs the reader the main point. A dump is allowed to be
long; the document is not.

**The budget is a constraint, not an outcome.** Pick it from what the reader will
actually read, not from what the material could fill. Measure against it at step
7. A draft over budget gets ideas cut, never sentences compressed — compressing
sentences is how a document keeps every rabbit hole and becomes unreadable
instead of merely long.

### 1. Dump every idea, keyed by a word slug

`ideas.tsv`, one row per idea:

```
idea<TAB>source<TAB>locator<TAB>the one sentence it supports
```

`idea` is a **word slug**, never a number — `evidence-first`, not `1`. A numeric
key is an order, and there is no order yet.

`source` and `locator` cite where the idea came from. **Print the cited lines.**
For every row with a real source, paste the actual `sed -n '<range>p'` output
underneath — real output, never a paraphrase. Writing a sentence that the cited
line does not say is the cheapest error to make and the most expensive to find,
because every step after this one treats the row as true. Measured: one run
turned a rule about dead code a change had orphaned into a general principle
about which review pass owns a check, and nothing downstream noticed.

An idea from your own knowledge, the audience's context, or a framing device
carries `-` in both and a sentence saying where it came from. **This list is
where a document loses its best material.** Nothing can check it, so it is the
one part of the dump that depends entirely on you sweeping wide before you start:
the research behind the argument, what the audience already believes, the
comparison that makes the point land. Measured: one run drew only on the declared
source files and silently dropped an entire section of research grounding that
the earlier version of the same document had.

### 2. Declare the graph

`graph.tsv`, one row per edge, three relations and no others:

```
from<TAB>rel<TAB>to
```

- `needs` — a reader must hold `to` before `from` makes sense. These produce the
  order, both between sections and between the items inside one section. A numbered
  list whose items constrain each other gets a `needs` edge per pair that does, and
  the script sequences them rather than leaving the numbering to whoever typed it.
- `example-of` — `from` is evidence for the claim `to`. These produce the
  sections: a claim plus its examples is one section.
- `same` — `from` and `to` make the same point. These catch two sections doing
  one section's work.

Every idea gets at least one edge. An idea with none is reported as an orphan,
and an orphan is either an idea that belongs in a section or an idea to drop with
a reason.

### 3. Derive the grouping and the order

    python3 scripts/graph_order.py --ideas ideas.tsv --graph graph.tsv

Valid output is the real output of that command. It prints the groups, the
levels, the item order inside any section whose members constrain each other, the
orphans, and any edge it refused. Do not advance while it exits non-zero — it
refuses an empty idea file, a duplicated slug, a self-edge, a truncated edge line,
an orphan, and a cycle, rather than reporting a clean bill on any of them.

The groups are the sections. The levels are the order. Neither was typed.

### 4. Answer the free choices the sort leaves, in writing

The script names every level holding more than one group, because those are
positions the prerequisites do not settle. For each, write one line saying which
group you put first and why. A free choice you do not write down is a choice you
will not remember making, and it is the one a reader will question.

### 5. Draft the body against the derived order

One unit per group, in the order the levels give. Draft prose only — no
headings, no titles, no numbering, and no count of anything.

### 6. Write the headings and titles from the finished body

Read each unit's finished prose and name what it says. Then the document title,
from the whole. The opening summary, if the document has one, comes last of all.

### 7. Run the checks a script can settle

Re-run the derivation against the graph as it now stands, because step 6 usually
changes it:

    python3 scripts/graph_order.py --ideas ideas.tsv --graph graph.tsv

Then measure the prose itself, which the graph says nothing about:

    python3 scripts/voice_stats.py draft.txt

Three numbers decide whether it reads like a person wrote it. **Inversions** count
saying what a thing is not before saying what it is — "rather than", "instead of",
"not X but Y". The ceiling is low and it is easy to blow: one measured draft hit
16.5 against a ceiling of 2.0, and fourteen of its eighteen hits were the single
phrase "rather than". **Median sentence length** and **long-sentence share** say
whether the reader is being asked to hold too much at once. A maxim candidate is a
sentence that closes a block by generalising into a saying; cut it by default.

Then measure length against the budget from step 0. **Over budget means cutting
ideas**, which readmits you to step 3, because dropping an idea changes the graph.

The script settles grouping, order, orphans, and cycles. The rest cannot be
scripted. **Each item takes a written answer naming something concrete. An item
with no written answer is an open item, and an open item stops the step** —
"looks fine" is not an answer.

What the graph now settles, and what to check against it:

- **A group spans adjacent units or none.** A group too large for one unit splits,
  and the `within:` sequence tells you where: cut it where the unconstrained members
  end and the constrained tail begins, and give each unit its own members. What is
  wrong is a group appearing in two units that are **not adjacent**, or two units
  drawing on the **same members**. Name which of those two you found, and which unit
  gets cut or merged. A sixteen-idea group split across two neighbouring pages is
  correct and gets no finding.
- **Every unit traces to at least one idea, and every idea lands or is logged
  dropped.** Both directions. A unit no idea produced is the defect this tier
  exists to prevent, and it is the direction nobody checks.
- **Each heading's key noun appears in its own unit's prose.** A word that lives
  in seven headings and no paragraph is a label nobody defined.
- **Every announced count equals the number of items behind it.** Count them.

What a person still has to read for:

- **Cold reader.** Name the first unit where someone meeting this cold would be
  lost without an earlier unit, or state that there is none.
- **The reader's actual ask.** Quote what you were asked for. Name the units that
  answer it and give their positions. If the answer sits in the last third behind
  material nobody asked about, say so and move it.
- **One idea per unit.** Name any unit whose point cannot be stated without "and"
  or "or". Two ideas in one unit is two units, which means the graph is missing an
  edge.
- **Nameable transitions.** Write the transition between each pair of consecutive
  units as a short sentence. A transition you cannot write is a seam; name it.
- **What the derivation revealed.** One line on what printing the groups and levels
  showed that your plan did not, or "nothing".

**Any structural change readmits you to step 3.** Adding a unit, dropping one, or
moving one changes the graph, which changes the grouping and the order, which
makes every written answer above describe a document that no longer exists.
Re-run the script and re-answer the checks. A handoff telling the next session to
re-run this is not a substitute for re-running it.

### 8. Choose the form

The content is organized. Now, and not before, decide what it gets built as.

---

## Choosing the form

**The default is a local file at a path that fits the repository**, per
`~/.claude/CLAUDE.md` "Local Files by Default, No Publishing Without Asking". A
design document goes in `docs/` or `design/`; a report goes wherever similar
documents already live; when nothing fits, the session scratchpad, and say so.
Markdown, unless the ask names another format.

**A branded print build happens only when the ask names one.** Check your private
routing for a skill that owns branded print deliverables. If the ask names that
kind of deliverable and your routing lists such a skill, then load it, hand it
the derived order from step 3, and follow it from its first section onward. If
the ask names none, finish in the default form and do not raise the subject.

**Publishing is a separate ask again**, and the answer is no unless the operator
asks for it in their own words. This holds however the document was built.

---

## What this skill does not cover

Sentence, comma, word, and label rules — `~/.claude/CLAUDE.md` "Communication
Style (HARD CONSTRAINT)". Code, comments, and docstrings — `writing-code`.
Commit messages — `git-commit`. A pull request body's required content —
`pr-create-task`, which this skill's tier two serves. Requirements, acceptance
criteria, and task sizing — `spec-task`. A brand, page architecture, print gates,
and PDF export — the print skill your private routing names. Whether to write the
document at all.

## Autonomous behaviour

Pick the tier without asking, and say in one line which you picked. Run tier one
and tier two inline without stopping.

For tier three, what happens after step 4 depends on what the body will cost to
rebuild, so say in one line which of these two you are in. If a person drafts the
body — an email, a design document, a report someone types out — then stop after
step 4 and show the operator the derived order and the free choices, because
reordering after that body is written means rewriting its paragraphs. If a
generator writes the body from a declared list of parts, then reordering costs a
rebuild and nothing else: carry on without stopping, and let the skill driving
you choose what it puts in front of the operator instead. Showing someone a list
of section slugs is not worth a stop when they could be reading the words.

Report the script output verbatim rather than summarizing it. When a check
cannot be closed, report it with what it would take, rather than reclassifying it
as a preference.
