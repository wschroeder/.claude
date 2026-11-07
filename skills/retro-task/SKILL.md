---
name: retro-task
description: Inspects the process after a review of the branch finds something — reads the run's own transcripts to find what each of last round's changes actually did, hears the operator's experience before interpreting it, answers their feedback against transcript evidence, then proposes the next batch of skill and CLAUDE.md changes as named options and stops for signoff. Inspects the process, not the product; the demo and the product's feedback belong to `demo-task`. Investigate-only until signoff, and every accepted change ends as a commit rather than a note. Use only after a review of the branch has found something: an outside pull request review, whose legitimate findings `pr-feedback-task` hands here, or the whole-branch review in `pr-create-task`. A demo in `demo-task` does not start it; `demo-task` hands straight to `spec-task`. Use it to retro that run, review how the process went on it, or read its transcripts to find why a rule did or did not fire — "retro this run", "retro the slice". An informal conversation about what should change in a skill or a CLAUDE.md is `systematize`, not this.
---

# retro-task — a review found something, so the process gets inspected

1. For the run named in $ARGUMENTS, respond with the sections below in order.
2. If $ARGUMENTS is empty, take the run as everything shipped since the last round was recorded, and say which commit you measured from and where you read it.
3. Inspect the process only: what was built and whether it works belong to `demo-task`, what comes next belongs to `spec-task`, and a finding about the product goes to the design document.
4. Start only from a pull request review handed here by `pr-feedback-task` or the whole-branch review in `pr-create-task`, handed here with the tip it read; `demo-task`'s demo does not start this template.
5. Take the run as the work since the last retro, and each legitimate finding as that review's feedback: Section 6 asks why our own reviews let it through, and Section 8 hands the finding itself to `spec-task`.
6. Deliver the change batch in Section 7, and read and write nothing in Sections 1 through 6.
7. Run the sections in order, because each is built from the one above it.
8. Follow CLAUDE.md "Evidence Format (HARD CONSTRAINTS)", especially its rules that a pattern label is a hypothesis, that recognition is a starting point, and that a ref that locates is not a ref that proves.

## 0. Before Section 1, read your own room

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

1. If the reading is past the ceiling it reports, hand off before starting this template: say so, say that no section has run, write the handoff through `clear-task` yourself, and then ask the operator to `/clear`.
2. Treat this check as deciding whether this phase starts here; the check at the end of Section 8 governs the hand to the next phase.

## 1. Scope the round

1. Show real output, not paraphrase.
2. Take last round's changes from the previous retro's transcript: its Edit and Write calls on skill files and CLAUDE.md files, and its Bash calls that committed in `~/.claude`.
3. Expect a session that edited a skill through a shell script to leave only the commit.
4. Do not use `~/.claude`'s git log to tell which changes were this project's, because other sessions commit there too.
5. Keep the trailing `*` in `<slug>*` so the scan also reads the project's worktrees:

    $ python3 -I ~/.claude/skills/retro-task/scripts/scope.py ~/.claude/projects/<slug>*/*.jsonl | sort | tail -25
    $ git -C <product repo> log --oneline | head -5
    $ git -C <product repo> status --porcelain
    $ ls -lat ~/.claude/projects/<slug>/*.jsonl | head -25

6. Report the changes shipped last round, where the product repository stands now, and every transcript whose mtime is later than the newest of those changes.
7. Exclude a transcript older than the newest change, because it is not evidence about the changes.
8. If the product repository has been rebuilt, say so plainly, and treat card ids and commit hashes from earlier rounds as dead.

## 2. The session map

1. Write one line per session in scope: id, local start and end, the model, how many operator turns it carried, and what it did in the run.
2. Count subagent transcripts, under `<session-id>/subagents/`, separately.
3. Read `session-loop/scripts/session_budget.py <project>` for where each session handed off rather than counting tokens by hand.
4. Mark which sessions ran unattended, because a change that fired only there has not been tested with a person present.

## 3. What last round's changes actually did

1. Write one record per change in Section 1's list:

    change:   <what shipped>
    fired:    <the verbatim transcript line and its timestamp, or "did not fire">
    untested: <the case this run never exercised, or "none">

2. Write "did not fire" for a change with no transcript line behind it, whatever the file says.
3. Quote the line; a grep that found the changed file locates the change and proves nothing about its behavior.
4. If every change fired and nothing is untested, re-examine the search before believing it, in case it only looked where the change would have succeeded.

## 4. Stop — the operator's experience of the run

1. Hear the operator before interpreting, offer nothing above this line as a conclusion, and write nothing below it until they have answered.
2. **Open with what they already said.** Quote the operator's own turns from the supervising session's transcript, their typed messages and AskUserQuestion answers each with its timestamp, as their account taken in the moment.
3. Quote each legitimate finding beside them as the reviewers' feedback.
4. Say what Section 3 found in at most a screen.
5. Ask only what is in neither: what they saw that their own turns and the transcripts do not show.
6. Do not propose a change here, and do not ask them to choose between changes they have not heard argued.
7. If they answer "I can't remember", record their account as the quoted turns and nothing more, and carry on to Section 5.
8. **Open the ask with the phase line**, directly above the question — the path a review's findings take, this stop's capitalized:

```
review -> RETRO -> spec
```

9. **Unattended, this stop ends the run.** Inside a `session-loop` run, commit what is already done, then write `HANDOFF.md` through `clear-task` with a first line reading `BLOCKED:` and one sentence saying a retro is waiting on the operator's experience of the run, and stop.
10. Write that handoff through the skill rather than by hand, however close the ceiling is.

## 5. Where the readings diverge

1. Answer each thing the operator raised against transcript evidence, and say plainly where your reading and theirs differ.
2. Report something they remember that the transcripts do not show as your finding, not theirs to defend.
3. Label their account as evidence about how the run felt and never as evidence about a mechanism, and put both in the response.

## 6. The findings

1. Write one record per finding, with the mechanism as the finding rather than the category:

    finding:    <a sentence naming who did what>
    observed:   <the transcript line, with its timestamp>
    mechanism:  <the instruction, line, or absence that produced it>
    competing:  <the instruction it lost to, where there was one>

2. If the mechanism line is empty, mark the record `hypothesis:` in those words.
3. Do not stop at matching this run's trouble to a shape seen before; find the mechanism in this instance.
4. Check for two mechanisms by name: a rule stated far from the output it governs does not reach that output, and where two instructions cover the same moment the nearer one wins unless precedence is stated.
5. For each finding that a review caught and the build's own reviews let through, write one more record:

    review finding: <one line>
    angle:          <the angle in `quick-review` or `security-review` that
                     should have caught it, its line quoted | none covers it>
    our review:     <what our review wrote at that angle, quoted from the
                     transcript with its session id: a dropped problem, an
                     N/A, or a proof too weak to show the bug>

6. Propose in Section 7 the smallest change to that skill that would have caught it: a sharper proof, a closed loophole, or a new angle with the finding as its worked example.

## 7. Stop — the change batch, then signoff

1. Ask for this approval separately from Section 4.
2. Lead with what changes and why, one paragraph each, in the operator's terms.
3. Give every Section 6 finding one of four outcomes: a change proposed, a change deliberately not made with one line saying why, a finding that needs another run before anyone can act on it, or the operator's call about the product, sent to the design document.
4. If the choice between two changes is real, put them up as named options, each on its own bullet, and recommend one.
5. **Open the ask with the phase line**, directly above the question — the path a review's findings take, this stop's capitalized:

```
review -> RETRO -> spec
```

6. Ask one question with your recommendation: make this batch, or strike the parts they do not want.
7. Put the ask last in the message.
8. Write nothing until they answer, and treat signoff as covering this batch and no later one — `git-commit`, "Safety".

## 8. Record and commit

1. Route each accepted change through the skill that owns it: `systematize` for an edit to an existing skill or a new ordinary one, `create-task-skill` for a new task-shaped one.
2. Make a CLAUDE.md change directly, and land a new skill's routing row in the same edit as the skill.
3. Follow `systematize`, "Keep every client and project out of `~/.claude`", for every word this step writes into `~/.claude`, the commit message included.
4. If a CLAUDE.md names a process log, append what was measured, what changed, and what is still unmeasured; otherwise say that the commit message is the record.
5. Commit last, through `git-commit`, staging by path.
6. Before handing off, read your own room:

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

7. If the reading is past the ceiling, or says `finish the step you are on`, hand off instead of continuing: say so, write the handoff through `clear-task` yourself, and then ask the operator to `/clear`.
8. Tell `clear-task` which section you stopped at and what that section still owes, such as a record not yet worked or an answer the operator owes.
9. Otherwise, hand to `spec-task` in the same turn, and let it decide and specify the next slice.
10. Pass every one of the review's findings to `spec-task` with its evidence.

## Notes on what this template does NOT do

- Does not demo the product, take product feedback, or reconcile a design
  document. That is `demo-task`.
- Does not decide or size the next slice. That is `spec-task`.
- Does not edit a skill itself. Section 8 routes every change to the skill that
  owns it.
- Does not run the work again, re-open a slice, or fix what a finding describes
  in the product.
- Does not take over the retroed session's tasks or write as though it were
  that session.
- Does not treat adoption counts, effort estimates, or a change's presence in a
  file as evidence that it fired.
- Does not push, and does not send anything outward. The log and the skill
  repository stay local.
