---
name: clear-task
description: Manual-invoke template — produces a copy-paste continuation prompt for resuming work in a fresh chat after /clear. Frontloads every handoff consideration into ordered sections, then emits the finished prompt as the terminal code block. Do not auto-activate; invoke explicitly only.
---

# clear-task — frontload the handoff, then emit the prompt

For the current session's work, produce a continuation prompt that a
fresh chat (after /clear) can act on without re-reading this
conversation. Respond with the sections below in order. The
continuation prompt is the LAST thing in your response — a single
fenced code block with nothing after it.

This template exists to defeat one specific failure mode. Because
tokens are generated left to right, once you start writing the prompt
you cannot revise its earlier lines; a consideration that surfaces
mid-prompt gets tacked on as a postscript after the code block — where
the operator, who copies only the block, never sees it. The fix is
structural: every consideration is dumped into the ordered sections
below FIRST, and the prompt is assembled from them LAST. If you
discover a missing consideration while writing the prompt, that is a
defect in the Completeness gate (§11) — return there, add it, and
regenerate the prompt. You never append to the prompt.

The output discipline is recursive: this skill follows the rule it
teaches — all considerations come before the artifact, and the
artifact is terminal.

## 1. Objective

The north star. One or two sentences in the operator's terms: what is
the overall task, and what does "done" look like? If the session had
several goals, list them and mark each complete / in-flight. No process
recap — state the goal, not the history of how you got here.

## 2. Verified state (real tool output, not memory)

The ground truth the fresh chat inherits. Paste actual output — not a
paraphrase — for each repo touched this session:

```bash
git -C <repo> branch --show-current
git -C <repo> status --porcelain
git -C <repo> log --oneline -5
git -C <repo> diff --stat HEAD
```

Run the block once per repo if the work spans several. If no repo is
involved (an infra change, an investigation), substitute the equivalent
state probe — the file written, the query result, the resource queried —
and paste its output. This section is the measurement that every
"completed work" claim in §3 must reconcile against. A "done" claim with
no matching line here is unverified (~/.claude/CLAUDE.md rule 1, "Verify
before claiming").

## 3. Completed work (each item reconciled against §2)

What was actually accomplished. Tag every item:

- `verified` — backed by a specific line in §2. Cite it (a commit hash,
  a status line, a file).
- `unverified` — done in narrative but not reflected in §2 (an unsaved
  edit, a claim you cannot back with tool output). Say so plainly; do
  not let it read as done.

The §2/§3 split is the load-bearing separation: your memory of "what we
did" is narrative; §2 is the measurement. Conflating them is the same
error as citing a design doc for a runtime claim (~/.claude/CLAUDE.md
rule 11).

## 4. Decisions, constraints, and dead-ends

The context most often lost across a /clear:

- Decisions made this session and the reason — so the fresh chat does
  not relitigate them.
- Constraints discovered — an API shape, a schema quirk, an env gotcha,
  a rule that bit.
- Dead-ends — approaches tried that FAILED, and why they failed. This is
  the highest-value, most-forgotten content: without it the fresh chat
  repeats the same failed attempt.

Tag every item here the way §3 tags completed work. A constraint, a
diagnosis, or a reason a thing failed is a claim about the system, and the
fresh chat will act on it without re-deriving it:

- `verified` — name the probe, command, or query that showed it, and quote
  enough of the output that the claim stands on its own.
- `hypothesis:` — everything else. An explanation you find convincing but
  did not measure is a hypothesis, however obvious it feels right now.

Split the observation from the explanation BEFORE tagging either one. A
reading and the diagnosis you drew from it are two claims; one `verified`
covering both launders the diagnosis into a measurement, and the fresh
chat builds on it and finds out the hard way. Write:

    verified: forward vs reversed field order diverges, 4 of 4 blocks, at
      cdfbe35 — sweep output above.
    hypothesis: the rout/flee path is what makes it order-dependent.

NOT "MEASURED: order diverges because the rout path is order-dependent."
That is ~/.claude/CLAUDE.md rules 4 and 10 applied to the handoff itself:
one tag covers one fact, and a causal connector starts a new claim.

## 5. Principles the operator highlighted

The operating rules the operator stated this session — how they want the
work done, not what the work is. These are the "always do it this way" /
"never touch that" / "remember to X" instructions the operator emphasized
in their own words: a preferred strategy, a guardrail, a sequencing rule.
They are meant to outrank the fresh chat's own instincts, so they must
survive the /clear verbatim. Distinguish from §4: §4 holds decisions you
reached and why; §5 holds directives the operator handed you. Each
principle should name the concrete behavior, not a label for it
(~/.claude/CLAUDE.md "Communication Style"). If the operator highlighted
no principle this session, write `None` — do not invent one.

## 6. Learned this session

The significant, durable discoveries — facts about the system that hold
beyond this task and are worth carrying forward: a non-obvious behavior, a
confirmed mechanism, a measured result, a corrected misconception. The
test is durability: if the insight would matter to someone who is NOT
doing this exact task, it belongs here. Contrast with §4 — §4's
constraints and dead-ends exist to stop the fresh chat repeating this
session's mistakes; §6 is knowledge that stands on its own. State each
learning specifically enough to act on, and say where it was verified — a
probe, a query, a measurement (~/.claude/CLAUDE.md rule 1). The splitting
rule from §4 applies here too: what you measured and what you concluded
from it are two entries, tagged separately. If nothing rose to
"significant," write `None`.

## 7. Credentials and test access

The test credentials and access details the operator handed over this
session, so the fresh chat can reach the same systems without asking
again: test logins, sandbox API keys, a sample account id, the
environment they belong to. Capture the literal values — these are
throwaway test credentials, and the continuation prompt's whole purpose is
to be self-contained (§12). Note which environment each credential is for
and what it unlocks. If the operator handed over no credentials, write
`None` here — and then leave the whole credentials heading OUT of the
prompt in §12. An empty section in the prompt costs the reader a heading
and tells them nothing.

## 8. Next steps (ordered, next action first)

The remaining plan, ordered by execution sequence, not importance. The
first item is the single concrete next action the fresh chat should
take. If a step depends on an open question in §10, name the dependency.

The first step also says what to re-check before acting on it. Time passes
between writing this prompt and reading it, and a background agent, a
running server, a branch, or a teammate's push can move underneath it.
Name the specific thing that could have changed and the command that
settles it — not "confirm state," but "run `<command>`; the handoff
assumed `<X>`, act only if that still holds."

## 9. Pointers (paths, links, skills, commands, environment)

The lookup table that saves the fresh chat from rediscovering what you
already found. These are exactly the "oh, also remember to..." items —
enumerate them HERE, not after the prompt:

- file:line references central to the work. Confirm each one this session
  before listing it — open the file, or run the grep. A path you remember
  is a guess, and a wrong directory sends the fresh chat hunting.
- Links — PR, ticket / Trello, design doc, the relevant chat.
- Skills the fresh chat should load first, by name, and why.
- Setup to reach a working state — workspace dir, `eval "$(direnv export bash)"`,
  test command, dev-server port.
- Which environment / workspace, and any secret/env switch in effect.

## 10. Open questions / blockers

Anything unresolved that needs an operator decision before or during the
next steps. If there are none, write `None`. Do not invent decisions; do
not bury a real blocker inside §8.

## 11. Completeness gate (the frontloading forcing function)

Before writing the prompt, interrogate §1–§10 out loud. Answer each:

- If the fresh chat read only §1–§10, what would it still get wrong or
  have to ask?
- What did this session try that failed, that §4 does not yet name?
- What rule or preference did the operator state that §5 does not yet
  capture?
- What significant, durable thing did this session learn that §6 does not
  yet record?
- What credential or test access did the operator hand over that §7 does
  not yet list, that the next action in §8 needs?
- What path, link, command, or skill does §9 not yet list that the next
  action in §8 needs?
- What "obvious to me right now" fact is implicit and would be invisible
  after /clear?
- Which claim in §4 or §6 is an explanation I never measured, still
  sitting there untagged or riding on a neighbouring `verified`? Read every
  "because", "so", "due to", "caused by", "which is why" in those two
  sections: each one starts a claim of its own. Split it out and mark it
  `hypothesis:`.
- Which file:line in §9 did I write from memory rather than confirm this
  session?
- What could change between now and when this prompt is read, that §8's
  first step does not tell the reader to re-check?

Every gap found here is integrated into the relevant section above —
§1–§10 — NOT appended to the prompt. Proceed to §12 only when this
interrogation surfaces nothing new. This section is the entire point of
the template: it is where "remembering" is supposed to happen, before
the prompt is committed.

Write §1 through §11 as eleven separate headings, in order, every time.
Do not merge neighbours into a combined heading such as "8–10" or "9–11",
and never skip §11 — the tail sections are the ones the momentum of a long
session eats first, and §11 is the one that catches the rest.

## 12. The continuation prompt (terminal output)

A single fenced code block, assembled from §1–§10, written in plain
English for the reader — a fresh AI plus the operator (~/.claude/CLAUDE.md
"Communication Style"). It is the LAST thing in your response: no prose,
no postscript, no "let me know if..." after it. Every line in the prompt
must trace to a consideration already written above; if while assembling
it you reach for something not in §1–§10, STOP — that is a §11 miss.
Return to the relevant section, add it, regenerate the whole block.

Shape:

```
We are continuing work on <objective + definition of done>.

Where things stand:
<verified state + completed work; verified vs unverified marked>

Watch out for (decisions already made — do not relitigate; dead-ends
already tried — do not repeat). Each line keeps the tag it carries in §4;
anything marked `hypothesis:` is unmeasured — reproduce it before you
build on it:
<from §4, tags intact>

Operating principles the operator set (follow these over your own
instincts):
<from §5>

Learned this session (tags intact — `verified` names the probe,
`hypothesis:` does not):
<from §6>

Credentials / test access (paste literal values):
<from §7 — omit this heading entirely if §7 is None>

Next steps, in order:
1. <next concrete action, and what to re-check first in case it moved>
2. ...

Pointers:
- Paths: <file:line ...>
- Links: <PR / ticket / doc>
- Load these skills first: <names>
- Setup: <cd ...; direnv; test/dev command; port; env>

Open questions for you:
<from §10, or "None">
```

Use real values, not placeholders. The block must be self-contained —
the fresh chat must not need this conversation. Nothing follows it.

## Stop — the prompt is the terminal artifact

This template produces text and nothing else. It does NOT run /clear, does
NOT begin executing the next steps, and does NOT write the prompt to a file
unless the operator explicitly asks. The operator copies the block and
starts the new chat.

## Notes on what this template does NOT do

- Does not run /clear or start a new session — that is the operator's
  manual step.
- Does not begin the next steps; it only describes them.
- Does not write, commit, push, or post anything. There is no destructive
  action.
- Does not append anything after the prompt code block. A late
  consideration is a §11 miss, fixed by regenerating the block — never by a
  postscript.
- Does not fabricate completed work: a claim with no backing line in §2 is
  labelled `unverified` (~/.claude/CLAUDE.md rule 1).
- Does not hand a diagnosis to the fresh chat as a measurement. An
  explanation you did not measure goes across as `hypothesis:`, separate
  from the reading it explains, in §4 and §6 alike.
- Does not merge or drop sections. Eleven headings before the block, in
  order, §11 included.
- Does not print an empty section. A `None` in §7 means the credentials
  heading does not appear in the prompt at all.
- Does not chain to any other skill. Invoke it explicitly, like its
  siblings (pr-feedback-task, pr-respond-task).
