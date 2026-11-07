---
name: writing-prose
description: Composes prose a person reads for its argument — dumping every point before any order, heading, or count exists, then deriving the grouping and the sequence from what those points require of each other, then writing the headings and titles last, from the finished body. Scales to the output: one point needs no machinery, several parts need a traced list, and a document a reader navigates needs an idea graph with a derived order. Use when writing or restructuring an email, a design document, a README, a findings report, a memo, a proposal, or a how-to or help guide; when organizing a brain dump; when choosing section order, headings, or titles; or when prose reads as AI-written. Cites `~/.claude/CLAUDE.md` "Communication Style" for every sentence-level rule and never restates it.
---

## Purpose

This skill owns composition: what gets said, in what order, under what headings.

1. Take every sentence rule from `~/.claude/CLAUDE.md` "Communication Style (HARD CONSTRAINT)", and never restate one here.
2. Leave code and the comments inside it to `writing-code`; this skill governs only how a comment's sentences read.
3. Leave a brand, a page format, and a PDF to the print skill your private routing names, and reach that skill only when the ask names that kind of deliverable.

## Pick the tier first

1. Count the parts you plan, not the words, and pick the tier from this table.

| Parts | Tier | Machinery |
|-------|------|-----------|
| One point, no sections | Tier one | none |
| Several parts, one sitting | Tier two | a list in your working notes |
| Sections a reader navigates | Tier three | an idea file and a graph |

2. If the tier is unclear, take the lower one and say in one line which you took.

## Rules for every tier

1. Name anything a reader follows by something they can grep for or act on, such as a heading, a function, a quoted phrase, a file name, or a row's key.
2. Never point a reader at a line number, a line range, a row number, or "the third item"; a line range is fine only in your own working notes.

## Text that leaves the team

When the reader is outside the team, such as a customer or a client stakeholder, switch from the internal register before you draft, and check the draft against these rules.

1. Cut the history, and name a thing as it stands now ("our current rule").
2. Cut evidence the reader will not act on, and keep one number only when it is the finding.
3. Turn every `hypothesis:` into a question to the reader, never a flat claim.
4. Write findings in the first person: "I found", "I haven't found", "I believe".
5. Give each number its so-what in the same sentence, and close any arithmetic the reader would otherwise do.
6. Use the reader's own names for things, such as the label on their screen.
7. Leave out whatever is not a gap, a problem, or a finding for this reader, even when it cost you work to rule out.

## Run the voice check

Every tier runs this on its finished text.

1. Save the text to a file in the scratchpad and run `python3 scripts/voice_stats.py <file>`.
2. Mark each maxim candidate, silent tail, closing verb, punchline, and comma candidate keep or cut, and fix every one you cut.
3. Cut a maxim candidate, a sentence that closes a block by generalising into a saying, by default.
4. Rewrite a silent tail, a sentence that ends on what nobody did, to name the actor that stayed silent.
5. Replace a closing verb such as "settled" or "resolved" with the act, such as "nobody has checked".
6. Cut a punchline, a clause tacked on with ", and" that ends on a negative count or an absence, from a title, a headline, or an opening sentence.
7. Mark a comma candidate keep only by naming the CLAUDE.md comma rule that allows it.
8. Mark each missing comma candidate add when the words after the conjunction carry a subject of their own, and leave otherwise.
9. Report a band the script says you missed in one line with the reason you kept the text, or rewrite until it lands; on short text, ignore the bands.

## Answer each sentence rule in writing

Tier two and tier three run this after the voice check.

1. Read the finished text against every rule in `~/.claude/CLAUDE.md` "Communication Style" except the five that govern the reply: the options rule, the ask rule, the rule to answer only what was asked, the chat-length rule, and the tables rule. A rule added to CLAUDE.md later joins the check unless you add it to that list.
2. Put the answers in the reply that hands the text over, under a heading "Sentence rules", one entry per rule, named by its topic.
3. Answer each entry by quoting every sentence you fixed under that rule, before and after; or by giving the number of sentences you read for it; or by saying in a few words why the rule cannot apply, such as "no dates".
4. Under the colon rule, list every sentence that has no main verb, including headings' captions and bullets, and mark each fixed or kept with the reason.
5. Treat an entry that says only "checked", "no issues", or "passes", and an entry with no answer, as an open item, and do not hand the text over while one is open.

---

## Tier one — one point, no sections

A code comment, a commit message, a Slack reply, a short email, or a one-paragraph answer.

1. Say the point in the first sentence, and let everything after it support that point.
2. Do not dump, outline, or announce a count.
3. Check the text against the CLAUDE.md rules in three separate passes: one for commas, one for where each subject ends and its main verb begins, and one for sentences a reader could take two ways.
4. Run the voice check.
5. If you are writing as the operator to someone they have written to before, read [references/register.md](references/register.md) now.
6. If you are planning a how-to or help guide, read [references/how-to.md](references/how-to.md) now, before planning, because it changes the order of work when a set holds more than one guide.

---

## Tier two — several parts, one sitting

An email carrying three asks, a PR body, a findings report, an in-repo README, one section of a design document, or a handoff.

1. Dump every point you might make in your working notes, one per line, with no numbers, headings, order, or count.
2. Give a line of its own to every point that came from your own knowledge rather than from a source.
3. For each part, name what the reader must already hold to understand it, and move a part after any part it needs.
4. Check that every part in the output traces to a line in the dump; add the line or cut the part.
5. Check that every line in the dump lands in a part or gets a one-line reason for being dropped.
6. Check that nothing announces a count.
7. Write the body, then the headings, then any opening summary, then the title, each from what the finished text actually says.
8. Rename any heading that names something its own part's prose never mentions.
9. Run the voice check, then answer each sentence rule in writing.

---

## Tier three — sections a reader navigates

A design document, a whitepaper, a deck, a specification, or a long report. Run the steps in order, and print every output a step names.

### 0. Write the one sentence and the word budget

1. Before dumping anything, write the single sentence the whole document argues and the number of words it gets, as comments at the top of `ideas.tsv`.
2. Admit an idea only when it serves that sentence.
3. For a document that shows status, such as a coverage map or an inventory, make the sentence and the title name what it covers, and do not invent a claim for it.
4. Pick the budget from what the reader will actually read.

### 1. Dump every idea, keyed by a word slug

`ideas.tsv`, one row per idea:

```
idea<TAB>source<TAB>locator<TAB>the one sentence it supports
```

1. Key each idea with a word slug such as `evidence-first`, never a number.
2. For every row with a real source, paste the real `sed -n '<range>p'` output of the cited lines underneath it.
3. Give an idea from your own knowledge, the audience's context, or a framing device `-` in both source columns and a sentence saying where it came from.
4. Sweep wide for those unsourced ideas before you start: the research behind the argument, what the audience already believes, and the comparison that makes the point land.

### 2. Declare the graph

`graph.tsv`, one row per edge, three relations and no others:

```
from<TAB>rel<TAB>to
```

1. Use `needs` when a reader must hold `to` before `from` makes sense; give a `needs` edge to each pair of items inside a numbered list that constrain each other.
2. Use `example-of` when `from` is evidence for the claim `to`.
3. Use `same` when `from` and `to` make the same point.
4. Give every idea at least one edge.

### 3. Derive the grouping and the order

    python3 scripts/graph_order.py --ideas ideas.tsv --graph graph.tsv

1. Take the groups as the sections and the levels as the order.
2. Do not advance while the script exits non-zero.

### 4. Answer the free choices in writing

1. For each level the script names as holding more than one group, write one line saying which group goes first and why.

### 5. Draft the body

1. Write one unit per group, in the order the levels give, as prose only, with no headings, titles, numbering, or counts.

### 6. Write the headings and titles

1. Name each unit from its finished prose, then title the document from the whole, then write any opening summary last.

### 7. Run the checks

1. Re-run `python3 scripts/graph_order.py --ideas ideas.tsv --graph graph.tsv` against the graph as it now stands.
2. Run the voice check on `draft.txt`, and keep inversions ("rather than", "instead of", "not X but Y"), median sentence length, and long-sentence share inside the script's bands.
3. Answer each sentence rule in writing.
4. If the draft is over budget, cut ideas, never sentences, and go back to step 3.
5. Give each item below a written answer naming something concrete; an item without one is open and stops the step.
   - A group spans adjacent units or none: name any group that appears in two units that are not adjacent, or any two units that draw on the same members, and which unit you cut or merged.
   - Every unit traces to at least one idea, and every idea lands or is logged dropped.
   - Each heading's key noun appears in its own unit's prose.
   - Every announced count equals the number of items behind it.
   - Cold reader: name the first unit where someone meeting this cold would be lost, or state that there is none.
   - The reader's actual ask: quote it, name the units that answer it and their positions, and move them forward if they sit in the last third.
   - One idea per unit: name any unit whose point needs "and" or "or" to state.
   - Transitions: write the transition between each pair of consecutive units as a short sentence, and name any you cannot write.
   - What the derivation revealed: one line, or "nothing".
6. After any structural change, re-run step 3 and answer these checks again.

### 8. Choose the form

1. Decide what the content gets built as only after the content is organized.

---

## Choosing the form

1. Write a local file at a path that fits the repository, in Markdown unless the ask names another format, as `~/.claude/CLAUDE.md` "Local Files by Default, No Publishing Without Asking" says.
2. If the ask names a branded print deliverable and your private routing lists a skill for it, load that skill, hand it the derived order from step 3, and follow it from its first section; otherwise do not raise the subject.
3. Publish only when the operator asks in their own words.

## What this skill does not cover

Sentence rules belong to CLAUDE.md "Communication Style", code and comments to `writing-code`, commit messages to `git-commit`, a pull request body's content to `pr-create-task`, requirements to `spec-task`, and branded print to the print skill your private routing names.

## Autonomous behaviour

1. Pick the tier without asking, and say in one line which you picked.
2. Run tier one and tier two inline without stopping.
3. At tier three, if a person drafts the body, stop after step 4 and show the operator the derived order and the free choices.
4. At tier three, if a generator writes the body from a declared list of parts, carry on without stopping.
5. Report script output verbatim.
6. Report a check you cannot close with what it would take to close it.
