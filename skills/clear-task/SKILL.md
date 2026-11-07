---
name: clear-task
description: Produces a copy-paste continuation prompt for resuming work in a fresh chat after /clear. Works every handoff consideration through ordered sections without printing them, then writes the finished prompt to one file and ends the turn. Writes the sections from what the session already holds rather than re-probing for it. Works out whether a session-loop worker or the operator reads the prompt next, and writes it to HANDOFF.md only for a worker. For the operator it writes pending-handoff.md in the session's scratchpad and prints one short line, because the auto-clear mod runs /clear and submits the file. Carries the words typed after /clear-task into the prompt word for word, as the next session's first step. Use when wrapping up a session before clearing, writing a handoff or continuation prompt, or carrying in-flight work into a fresh chat — "hand this off", "I'm about to /clear", "write me a continuation prompt".
---

# clear-task — frontload the handoff, then emit the prompt

1. Produce a continuation prompt that a fresh chat after /clear can act on without re-reading this conversation, as one file write to the file §0 settles on: `pending-handoff.md` in the scratchpad for the operator, or `HANDOFF.md` for a worker.
2. Work through the sections below in order before writing it, and print none of them.
3. For the operator, make the Write call the last thing in the turn, with no text before or after it and no printed block.
4. Write every consideration into the sections first, and assemble the prompt from them last.
5. If you find a missing consideration while writing the prompt, return to §12, add it to its section, and regenerate the prompt; never append to the prompt.
6. Use no pronoun for a person, and never "you" or "I" for either party, in the sections or the block: name "the agent" or "the operator" every time, except inside a direct quotation.

## 0. Who reads this next (settle it before writing anything)

1. Decide whether a `session-loop` worker or the operator reads this prompt next: a worker gets `HANDOFF.md`, and the operator gets the block, written to `pending-handoff.md` (see "Stop").
2. Read the prompt this session opened with, and take the first case that applies:
   - If it carries the unattended-loop protocol, the words "You are one iteration of an unattended loop" and an instruction to write `HANDOFF.md` through this skill, a worker reads next.
   - If `session-loop` step 2 is seeding a repository with no handoff yet, or the operator asked for the file in their own words, a worker reads next.
   - If the next steps need no answer from the operator, ask with AskUserQuestion whether to hand to `session-loop`, recommending it; on yes, a worker reads next.
   - Otherwise, the operator reads next.
3. Write one line naming the reader and what settled it:

    reader: the operator — this session opened on a request they typed, and
    nothing in it carried the loop protocol

4. Ask anything the operator must answer before the handoff, such as the reader or whether to hand off now, with AskUserQuestion, not in the response text.
5. Never run `pgrep` to decide this.

## 1. Objective

1. State the overall task and what done looks like, in one or two sentences in the operator's terms, with no recap of how the session got here.
2. If the session had several goals, list each and mark it complete or in-flight.
3. Name the one task this prompt continues, with its issue id if it has one, in the first line.
4. List every other issue, card, or topic the session touched under "Mentioned, not ours", one line each.
5. If the session held something back as a later slice of this work, file it as a bd card or a line in the look-ahead sketch before writing, name the card in §4, and never list it under "Mentioned, not ours". See [references/measurements.md](references/measurements.md).
6. Write the fix for a fault this slice made as the next session's first step, and file no card for it.
7. Check, or file a bd card for, every warning, error, or suspected defect the session saw and did not fix, even outside this slice or with only a hypothesized cause; name the card in §4, never under "Mentioned, not ours".

## 2. Verified state (the tool output this session already produced)

1. Quote the ground truth from what commands printed when this session ran them: the branch, commit subjects and hashes, the last `git status`, the suite's test counts, query results, and files written. Say when each ran.
2. Run `date` before writing any time, and take "Where things stand" and every timestamp from it; never estimate one.
3. Write a time for an earlier event, such as the operator's turn, only where a tool's output showed it; otherwise write "before" and the `date` reading. See [references/measurements.md](references/measurements.md).
4. Where this session never ran a command, say so instead of filling the gap.
5. Re-run nothing to fill this section in.
6. Reconcile every §3 "done" claim against this section, and label one with no command output behind it unverified rather than probing it into shape.

## 3. Completed work (each item reconciled against §2)

1. Tag every accomplished item:
   - `verified`: backed by a specific §2 line, cited as a commit hash, status line, or file.
   - `unverified`: done in narrative but missing from §2, such as an unsaved edit; say so plainly.

## 4. Decisions, constraints, and dead-ends

1. Record the decisions made this session with their reasons, the constraints discovered, and the dead-ends tried with why they failed.
2. Tag each item `verified`, naming the probe, command, or query and quoting enough output that the claim stands alone, or `hypothesis:` for everything else, however obvious it feels.
3. Split an observation from the explanation drawn from it before tagging, and give each its own line and tag.
4. Write a known failure in the current Jira issue's own work as needing a card cut by `spec-task`, placed in §8 ahead of new work, never as an inherited `hypothesis:`. See [references/measurements.md](references/measurements.md).
5. Record a dead-end against the tool, call, or path that failed, never as a ban on the class of evidence it served, and name any other route to the same evidence.
6. Put anything the operator approved, such as a design, a layout, or a scope, here in their terms with the time of approval, stated in full, never as a clause inside a §8 step.
7. When the operator says a card's work is applied, merged, or working, write `Decision (operator, <timestamp>, "<their words>")` naming each card it covers as accepted, and put nothing in §10 asking them to accept those cards.
8. Label a decision "operator" only beside their own words, as `Decision (operator, <timestamp>, "<their words>")`. Label a choice the agent reached, even one they let stand, `Decision (Claude, <session>)` with its reason.
9. For a carried-forward operator decision with no quote, search their turns for one, and relabel it as Claude's where none turns up. See [references/measurements.md](references/measurements.md).
10. For every decision in the opening prompt, do one of three things and say which in one line: carry it forward word for word (after the search above for an unquoted `operator` label); record it in the project's design documents and point to the file; or strike it, naming what replaced it or who withdrew it. A shorter restatement is none of the three.

## 5. Principles the operator highlighted

1. Carry verbatim the operating rules the operator stated this session about how the work is done, each naming its concrete behavior; if there were none, write `None`.
2. Never derive a rule from a principle: quote the operator's words and stop. A limit on running a kind of test never forbids writing one.
3. Carry the operator's definition of released here word for word whenever no project document holds it.
4. Carry the operator's answer on where git ignores `/HANDOFF.md` here word for word once `session-loop` step 2 has it: yes means `.gitignore`, no means `.git/info/exclude`.
5. For every directive inherited in the opening prompt, do one of three things and say which in one line: carry it forward where it still binds; record it as a card or design document line where it became plan or product; or strike it where the session carried it out or the operator withdrew it. Never drop one silently, or decide that a directive you did not hear spoken was never yours.

## 6. Learned this session

1. Record durable discoveries that would matter to someone not doing this task, such as a non-obvious behavior, a confirmed mechanism, a measured result, or a corrected misconception, each specific enough to act on and naming where it was verified.
2. Split what was measured from what was concluded, tagged separately, as in §4.
3. If nothing rose to significant, write `None`.
4. Never record a code defect here; fix it, or file it as a card named in §4.

## 7. Credentials and test access

1. Capture the literal values of test credentials the operator handed over this session, with the environment each is for and what it unlocks.
2. If none were handed over, write `None` and leave the credentials heading out of the prompt in §13.
3. Keep every identifier from a real environment, such as a principal id, client id, tenant or subscription id, key, token, or connection string, out of every section, `verified` lines included, and name the resource instead, per `~/.claude/CLAUDE.md` "Keep an Identifier Where You Found It".

## 8. Next steps (ordered, next action first)

1. Order the remaining plan by execution sequence, with the single concrete next action first, and name any dependency on a §10 question.
2. Give every step the command and the output it prints when the step is done.
3. Where a review stopped part-way, name its notes file, per `quick-review` "Record each pass as it finishes", and say to resume from it.
4. Make step 1 the operator's instruction for the next session, in their words, where §11 gives one; run nothing before it, no owed work, review, or re-measurement.
5. If that instruction asks for a conversation, such as "let's discuss" or "wait for my feedback", make step 1 say where things stand and what is left, then stop and wait. List the work this session would have scheduled as what is left, file no cards for it first, and write under the list of open decisions: "Do not ask the operator about these until they reply to step 1."
6. If §11 is a question that the response writing this handoff answers, make step 1 put that answer in front of the operator and wait, make their question the next session's subject ahead of any earlier objective, never write that it is answered, and quote any "not yet" or "hold off" inside it.
7. Never declare a stage of the work finished.
8. Point a step that builds something the operator approved to that decision in §4, or the file holding it, without restating it.
9. Where a skill handed off to this one, put the step it was on and what that step still owes right after the operator's instruction, in its words; if nothing said, write that nothing did.
10. Where the session committed or holds uncommitted code, walk what `writing-code` owes: `comment_share.py` with a disposition for every block it lists, `quick-review`, and `security-review` where `writing-code`'s list calls for one. Record each as run with its output, or "not run", and make every "not run" a numbered step right after the operator's instruction.
11. Where the steps finish the slice's last task, make the last step "load `demo-task` and run it for the slice".
12. Where a demo hands off before `demo-task` Section 4's ask, make the first step after the operator's instruction "go back to `demo-task` Section 3 and walk every step again", never "resume at Section 4"; if the walk used up data the demo needs, say to walk with another record or put new data in place.
13. Where the phase that owed work has ended, create its card before generating the prompt and name the card here instead of writing the work as a step; a question the operator has not been asked belongs in §10.
14. Write no sentence about what the product can do without the command that showed it and what it printed; write closed cards, a passing suite, or a green gate instead.

## 9. Pointers (paths, links, skills, commands, environment)

1. List each path with the greppable identifier inside it that the work turns on, never a line number, taken from what this session opened; mark a recalled path nothing touched `hypothesis:`.
2. List the links: PR, ticket, design doc, and relevant chat.
3. List no skills to load first; name each skill in the step it owns. See [references/measurements.md](references/measurements.md).
4. List the setup to reach a working state: workspace directory, `eval "$(direnv export bash)"`, test command, and dev-server port.
5. Name the environment or workspace, and any secret or environment switch in effect.

## 10. Open questions / blockers

1. List everything unresolved that needs an operator decision, or write `None`; invent no decisions, and bury no blocker in §8.
2. For every question inherited in the opening prompt and about to go on unanswered, do one of three things: file it as a card; write its answer into the design document that should have held it; or strike it. Carrying it a third time is none of the three.
3. List every operator approval in §4 that no project design document holds yet: what was approved, when, and that the design documents, by the project's own name for them, do not hold it. The three outcomes above then apply.
4. List in one line every `Decision (Claude)` in §4 that defers a fix, a gap, or a behavior change to the operator, or sets behavior the card's acceptance criteria do not cover, naming what they must decide. §10 is never `None` while §4 holds one. See [references/measurements.md](references/measurements.md).
5. Keep here every question this session raised or announced for the operator that they have not seen, never as a card or under "Mentioned, not ours"; filing a card becomes an outcome only once the operator has seen it.
6. If the operator says they do not care about an item, that it does not matter now, or that it waits for a later phase with nowhere named to track it, strike it: quote their words once with the time and drop it from every section. Never treat a "no" to one way of keeping it as a request to offer the next way.

## 11. The operator's last words, verbatim

1. Quote the operator's final turn before the clear exactly and in full, in a block quote with its timestamp.
2. Treat words typed after `/clear-task` as that final turn: quote them, and make them §8's first step.
3. Write arguments a session passed when calling this skill itself into §8 as an instruction, and quote none of them here.
4. With no typed text, take the turn before the invocation as the final turn.
5. Quote it even where §5 and §8 already carry it.
6. Where nobody typed anything this session beyond the pasted handoff, carry the last handoff's quote forward word for word with its original timestamp, and say it is inherited.
7. Once a session has done what an inherited quote asked, strike it in one line naming what it did.
8. Write `None` only where this session has no final turn and the opening prompt carried no quote, and then leave the heading out of the prompt in §13.

## 12. Completeness gate (the frontloading forcing function)

1. Before writing the prompt, answer each question in your reasoning, not the response:
   - If the fresh chat read only §1–§11, what would it still get wrong or have to ask?
   - What did this session try that failed, that §4 does not yet name?
   - What rule or preference did the operator state that §5 does not yet capture?
   - What durable thing did this session learn that §6 does not yet record?
   - Which defect, or unexplained warning or error, is neither fixed nor named on a card in §4?
   - What credential or test access that §8's next action needs does §7 not list?
   - What path, link, command, or skill that §8's next action needs does §9 not list?
   - What fact obvious right now would be invisible after /clear?
   - Which claim in §4 or §6 is an unmeasured explanation, untagged or riding on a neighbouring `verified`? Read every "because", "so", "due to", "caused by", and "which is why" in those sections, split each out, and mark it `hypothesis:`.
   - Which reference in §1–§11 names a line rather than a greppable identifier?
   - Is §11 the operator's final turn word for word, or a shortened or tidied version?
   - Did the invoking line carry words after `/clear-task`, does §11 quote them, and does the block carry them under its own heading?
   - Is §8's first step what §11 asks for? Move anything ahead of it behind it or into the list of what is left.
   - If §11 is a question this response answers, does §8's first step put that answer in front of the operator and wait?
   - Does §10 list each `Decision (Claude)` in §4 that leaves something for the operator or sets behavior the acceptance criteria do not cover?
   - Is each question the operator never saw in §10, and none in a card or under "Mentioned, not ours"?
   - Is each item the operator said they do not care about struck in their words, rather than turned into a new open question?
   - Does §1 name exactly one task with its issue id, and does every other issue id in §1–§11 appear under "Mentioned, not ours"?
   - Does the artifact match what §0 settled?
   - Going through the opening prompt item by item, which decisions, directives, and questions have been carried, recorded, or struck, and which dropped or shortened? Write the list out, comparing against the inherited text, not memory.
   - Which term did a session coin that the operator never used? Define it plainly at its first appearance in the response and again in the block, or replace it with plain words.
   - Outside a direct quotation, which sentence, inherited lines included, uses a pronoun for a person, "you", or "I" instead of "the agent" or "the operator"?
2. Integrate every gap into its section, never into the prompt, and proceed to §13 only when the questions surface nothing new.
3. Work §0 through §12 one at a time, in order, every time, never merging neighbours or skipping §12.
4. Where a section is empty, write `None` in its part of the prompt, or for §7 and §11 leave its heading out.

## 13. The continuation prompt (the file's whole content)

1. Assemble the file's text from §1–§11 in plain English for a fresh AI and the operator, per `~/.claude/CLAUDE.md` "Communication Style", without the code fence.
2. Trace every line to a consideration above; if you reach for something not in §1–§11, stop, add it to its section, and regenerate the whole block.
3. Use this shape:

```
We are continuing work on <the one task, and its issue id> — <definition of done>.

Mentioned, not ours (do not work on these):
<every other issue or topic from §1, one per line, or "None">

The operator's last words are below, word for word. Do what they ask before
anything else in this prompt. Treat every line marked verified as settled, and
do not re-measure it:
<from §11 — omit this heading entirely if §11 is None>

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

Credentials / test access (literal test values only; name real resources):
<from §7 — omit this heading entirely if §7 is None>

Next steps, in order:
1. <next concrete action, naming the skill that owns it>
2. ...

Pointers:
- Paths: <path, and the identifier to grep for inside it>
- Links: <PR / ticket / doc>
- Setup: <cd ...; direnv; test/dev command; port; env>

Open questions for you:
<from §10, or "None">
```

4. Use real values, not placeholders, and make the block self-contained; nothing follows it.

## Stop — the prompt is the terminal artifact

1. Produce the one file §0 settled on, and never run /clear or begin the next steps yourself.
2. Where §0 settled on the operator, write the prompt to `pending-handoff.md` in the scratchpad directory your system prompt names, then end the turn with one line that repeats nothing, such as "Handoff written." Print no sections, block, path, or summary.
3. Print the block only when the operator says the auto-clear mod is not running.
4. Where §0 settled on a worker, never write `pending-handoff.md`; the handoff is `HANDOFF.md` alone. `session-loop` step 2 alone writes its own launch prompt to `pending-handoff.md` after this skill writes `HANDOFF.md`.
5. If the operator asks a session that has written its handoff and is under the ceiling to keep working, keep working, and rewrite the prompt when it stops.
6. Where §0 settled on a worker, write §1–§11 as always, write the assembled prompt to `HANDOFF.md`, print no block, and report the path and its line count.
7. Where §0 settled on a worker, write only what the next card needs: name each open card by id and leave its criteria and notes in bd, and leave out every path, link, environment, and identifier no open card uses. The rules carrying decisions, directives, and the operator's last words forward still hold. See [references/measurements.md](references/measurements.md).
8. Replace the whole `HANDOFF.md` when writing it, never append. Once the operator has accepted a slice, carry its working rules and their standing decisions, and leave out that slice's status lines, tasks, and requirements.
9. Make the one turn that writing the file costs the whole report: the path and line count, nothing else. Take no further turn of your own; anything the operator types after it is a new instruction.
10. Delete a stale `HANDOFF.md` left in the repository rather than writing over it; §0 says whether anyone is coming for it.
11. Read [references/measurements.md](references/measurements.md) only for the reasons and measured cases behind these rules.

## Notes on what this template does NOT do

1. It runs no /clear and starts no session; the auto-clear mod does that from `pending-handoff.md`, or the operator does it by hand.
2. It begins none of the next steps.
3. It writes, commits, pushes, and posts nothing except the one file §0 calls for and the backlog card §8 requires for a finished phase's owed work, and takes no destructive action.
4. It prints neither the sections nor the block for the operator; a late consideration is fixed by rewriting the file, never by a postscript.
5. It takes no second turn after writing `HANDOFF.md`.
6. It labels a claim with no backing §2 line `unverified`.
7. It hands an unmeasured explanation across as `hypothesis:`, separate from the reading it explains, in §4 and §6 alike.
8. It never merges or skips sections, §0 and §12 included.
9. It prints no empty section; a `None` in §7 drops the credentials heading.
10. It chains to no other skill, `session-loop` included.
