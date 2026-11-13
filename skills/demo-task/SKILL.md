---
name: demo-task
description: Closes a finished slice — runs every proof command to find where it actually stands, assembles a demo the operator can reproduce and operate themselves, takes their feedback verbatim, carries a rapid mode the operator switches on to pause the proof commands and captures while they try ideas or sculpt a new screen on made-up data, and switches off by approving, shows a slice of only prose or infrastructure as code as its full diff for the operator to review, closes the cards they accepted and leaves the rest demoable, then writes whatever their feedback decided about the product into the design documents before handing to `spec-task`. Use when a slice is finished, when asked to demo what was built, or to review how a slice landed — "demo this slice", "show me S2", "close out this iteration", "let's sculpt this", "quick tweak". Does not decide or size what comes next; that is `spec-task`, which it hands to.
---

# demo-task — the slice is shown, the feedback is recorded

1. For the slice named in $ARGUMENTS, respond with the sections below in order. If $ARGUMENTS is empty, take the slice whose cards are demoable, say which, and quote the query that found it.
2. Produce three deliverables: the demo in Section 3, the cards moved in Section 5, and the design document edits in Section 6. Section 4 is the one stop; everything after it records what the operator said there.
3. Write everything the operator reads in plain English, with no requirement id, bead id, or coined word carrying a sentence.
4. Keep CLAUDE.md's Evidence Format in full: the evidence block stays, and every claim carries its tag. Where plain English and evidence pull apart, write the plain sentence and put its tag on it.
5. Use an id only as a tag after the clause it proves; state what the requirement asks for in the sentence itself.
6. Build each section from the one above it; write no status tag before Section 2's commands have run.
7. If a section fights the work rather than catching something, say so instead of skipping it.

## 0. Before Section 1, read your own room

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

1. If it reports you are past the ceiling, hand off before Section 1: say so, say no section has run, write the handoff through `clear-task` yourself and end the turn, so the auto-clear mod clears the session.
2. Treat this check as separate from Section 7's, which governs the hand to the next phase.

## Rapid mode — when the operator pauses the formality

1. When the operator asks in their own words for speed over rigor, at any point in the demo phase or before any slice exists, say in one line that rapid mode is on, and read [references/rapid-mode.md](references/rapid-mode.md) before your next edit.

## Diff route — when the slice has nothing to run

1. Take this route where every file the slice changed is prose (design documents, READMEs, skill files) or infrastructure as code (Terraform, CI workflows, Dockerfiles). If any changed file is code a person runs, through a screen or a command line, take the usual route.
2. Run Section 1, then skip Sections 2 and 3: no proof commands, walk, captures, or operate-it steps.
3. In Section 4, print the whole diff in the message, file by file, exactly as `git diff` prints it with its context lines, never trimmed to changed lines, and ask the operator to read it as a code review and say what is wrong.
4. In Section 5, close each card they accepted with their words as its reason, and run Sections 6 and 7 as usual.

## 1. Setup and boundaries

1. Print the real output of:

```
$ pwd && git rev-parse --show-toplevel
$ ls docs design specs 2>/dev/null
$ bd list --label slice:<current> --status open
$ bd list --label slice:<current> --status in_progress
$ bd list --label slice:<current> --status demoable
$ bd list --label slice:<current> --status closed
$ bd list --no-labels
```

2. Name the current slice, and state the board's counts:

```
  Backlog      bd list --no-labels                              known, not pulled
  TODO         bd list --label slice:<n> --status open          pulled, not started
  In progress  bd list --label slice:<n> --status in_progress
  Demoable     bd list --label slice:<n> --status demoable      built, nobody has seen it
  Done         bd list --label slice:<n> --status closed        demoed and accepted
```

3. Take Demoable as this template's input: `tdd-cycle` leaves a card there, and only a demo moves it to Done.
4. If `bd list --status demoable` errors or returns nothing on a slice whose cards are closed, say in one line that the project has not registered the status, and read Done as the input instead. The project runs `bd config set status.custom "demoable:wip"` itself.
5. State the definition of released, taking the first that exists: `project-definition-of-done` if listed, loaded here; the design documents or README, quoted with file and line; or the handoff's quote from the operator, saying it came from the handoff. If none exists, stop.
6. If the current slice has no closed bead and none of its proof commands passes, say in one line that it has not started and that building it is `tdd-cycle`, and stop without running Sections 2 through 6.

## 2. Where the slice actually stands

1. **Suspended while rapid mode is on** — see "Rapid mode" above. Run none of these commands and write none of these records until the operator approves.
2. Run every proof command for the current slice's requirements, then write three parts in this order.
3. First write one plain-English paragraph saying what was built and what a person can now do. Put in it no tag, requirement id, bead id, command, count, or coined word, including any phrase built from a name in the code or a card title that uses one; say what the change does for a person, or that nothing changes on screen.
4. If the slice built something a person cannot act on, such as a checker or a test harness, say so in that paragraph in terms of what it does for them. If there is nothing to say, name that as a finding, and let Section 3 report there is no demo.
5. Then write the stories:

```
Story: As a <person who uses the product>, I can <what they can do>.
  beads:  <ids>
  proof:  <the command, or the thing to look at>
  status: <n> of <m> closed
```

6. Fill `beads` and `proof` from each card's acceptance criteria, reading the cards one at a time and keeping only their criteria, and put every proof command under the card whose criteria name it.
7. Make the role someone who uses the product, never the developer; name toolchain work on the `proof` line of the story it serves.
8. Lead with any story whose beads are all closed but whose proof command fails.
9. Last, write the per-requirement records, which are for you:

```
[R<n>] $ <the proof command>
       <the last line of real output>
       result: passes | fails | ran nothing
```

10. Count a command that ran no tests as a failure; read the test count, never the exit code alone.
11. Record a failing proof command without repairing it; Section 6 hands it to the next slice.
12. Run every command even when the bead that owned it is closed.

## 3. The demo

1. **Suspended while rapid mode is on** — see "Rapid mode" above. Produce no artifact and write no reproduction command until the operator approves.
2. Show the definition of released being met by the thing itself, not by tests passing.
3. If a walk step needs a model, dataset, or setting other than the operator's environment names, or spends money, ask about that alone before walking, outside Section 4's ask. If they say no, leave the step out and write "the walk did not check this" against it.
4. Write one record:

```
  shows:      <which requirements, by id>
  artifact:   <path to the screenshot, recording, file or output>
  produced by: $ <the exact command that made it>
  drove it:   <the input you sent it, and the capture either side of that>
  operate it: $ <the exact command the operator runs to drive it themselves>
```

5. Where the operator clicks rather than runs a command, make `operate it` numbered steps, each saying where to click, what to check before, what to do, and what to check after.
6. Write those steps as a story before driving anything: load `writing-prose` and use its tier-two method, dumping every card and changed behavior and ordering them so each step sets up the next.
7. Map every rule on every card to a step, or say in one line why it has nothing on screen, and write the mapping under the steps, one line per rule: card, rule, step number. Map each case of a multi-case rule to its own step, and add a step for any case the mapping says went undriven before walking.
8. Order the steps so the walk can run again from step 1: put a step that changes data after every step that reads it, or follow it with a step that restores it.
9. If the slice changes a step in the middle of a pipeline, add a walk step capturing the screen just before and just after it, even where the end state alone would pass.
10. Follow the written steps literally as the drive: capture before and after each step and compare each after-capture with its "check after" text.
11. Capture the whole page (`fullPage` true, no `uid`) unless the step is about one element, and open every capture with Read before sending it, comparing the image, never the page text.
12. To find what to click, read only the region the step works in, such as with `evaluate_script`, never a whole-page snapshot.
13. Where a capture and its "check after" text disagree, fix the step or send the product back to build as [references/driving-rules.md](references/driving-rules.md) says, and post nothing until they agree.
14. Print the steps in full in the message that posts the demo; keep the file on disk as the walk's record, unsent.
15. Start whatever the demo needs yourself, such as a build and a server, give the operator what they open with the server's PID, and leave it running until they answer. Where a step restarts the app, tell them to type "restart" and restart it yourself.
16. Where a step needs setup a phone cannot do, do it yourself, show the evidence it is in place, and hand the operator only the test on the phone.
17. Before posting, set each answer the operator gave during the spec, as quoted in cards and design documents, beside the captures, and say whether a capture shows the build matching it.
18. Read each capture taken just before the operator acts as a newcomer would. If one shows something they turned down, or something a newcomer could not make sense of, fix it and walk again before posting, whether or not the spec covers it; raise it only when the fix needs a choice they have not made.
19. Read every figure on every capture against the others on the same screen, such as a count against a heading's total, and say whether those that should agree do. If the slice caused a mismatch, fix it before posting; if not, state it in the post as a walk finding.
20. Before driving anything, read [references/driving-rules.md](references/driving-rules.md).

## 4. Stop — show the operator and take the feedback

1. Post Sections 2 and 3 and stop: no status reconciliation, no next slice, no fixes.
2. **While rapid mode is on, this stop is the sentence or two that "Rapid mode" above calls for**, and nothing below returns until the operator approves.
3. If the demo gains a new way to reach the product, such as a new build, platform, or kind of input, go back to Section 3, drive it through that way with a person's input, and read the captures before sending.
4. Record the walk as you go in its folder, `/.tmp/demos/<date>-<slug>/` at the root of the working tree, alongside the demo file, captures, and any driver, and never commit anything in it. Record the commit the walk runs on and one line per finished step naming its captures and whether it matched.
5. Where a walk runs past about ten steps, drive it with a script in that folder that takes the captures and prints those lines.
6. Before the walk's first step, run two checks. If `git check-ignore -q .tmp/demos/x` exits non-zero, append `/.tmp/demos/` to `.gitignore` and commit that line alone. If `git ls-files` lists a demo file or walk record outside that folder, move it in, `git rm --cached` it, and commit that alone.
7. If anything has been committed since the captures were taken, go back to Section 3 and walk every step again; one fresh capture is not a walk. A session may finish an earlier session's walk only when the record names the current HEAD, nothing has touched the walk's data, and it opens every capture it posts with Read.
8. If you hand off before this section's ask, write the next first step as "resume the walk at step N" where the record allows it, and as "go back to Section 3 and walk every step again" otherwise, never "resume at Section 4". If a walk used up data the demo needs, the next walk uses another record or puts new data in place, never skipping the walk.
9. Open the ask with the phase line directly above the question, this stop's phase capitalized:

```
spec -> build -> DEMO
```

10. Ask for one thing: that the operator work the demo themselves and say what is wrong with it. Give them what Section 3's record says they act on, the command or the thing to open, and ask them to close any link of the chain that went unproven.
11. Before handing over a link, run any local tool that would check it, such as `pdftoppm` with a pixel diff; if you still hand it over, write "the walk did not check this" against it and give no reason it ought to pass.
12. Name the two or three things worth looking at, never ask what they would like to do next, and put the ask last.
13. Before asking the operator anything about how the product behaves, search the design documents for the answer, including questions from a handoff, your own, and ones raised while answering feedback; check each oddity they ask about the same way. Where the documents answer it, quote the line and drop the question.
14. Where the demo is something to read, such as a page, report, render, or PDF, send the file with `SendUserFile` and give its path. Never send a file of operate-it steps.
15. Where the demo follows a background run the operator was not watching, such as `session-loop`, send one `PushNotification` per demo naming the slice. Write the demo message first, summary, steps, phase line, and ask, then call SendUserFile and PushNotification, and end with one line pointing back that repeats nothing, such as "The demo is above."
16. Record what comes back verbatim, one record per point, and interpret only in Section 6:

```
[F<n>] "<the operator's own words>"
```

17. Try a fix the feedback asks for before reviewing it: edit the working tree, restart the app, and walk the named step until it matches. Then run `writing-code`'s reviews, commit once on the passing version, and walk every step again.
18. Inside a `session-loop` run, make this stop a line in a file:
    1. Commit what is done, never the walk's folder.
    2. Stop every server you started, and write its start command into the demo file's steps.
    3. Write the start command and the walk command each as a short numbered list of single commands runnable as printed, the app launch as one line setting every variable, never a script or env file.
    4. After your last edit to the demo file, run both exactly as printed, and write `BLOCKED:` only once both work.
    5. Write `HANDOFF.md` through `clear-task` with a first line reading `BLOCKED:` and one sentence naming the slice and the file holding its demo, and stop, however close the ceiling is.
    6. Write `BLOCKED:` only once Section 3's record and captures exist and the drive has reached everything the slice changed; before then, write an ordinary handoff naming the section or step still to drive.
    7. Where the worker stopped partway through the walk, add a line `WALK: <path to the walk record>`, relative to the repository root or absolute.
    8. Move no requirement to `demoed`; they stay `built` until a person has looked.
19. Never carry on into Section 5 after posting the demo.

## 5. Move the cards the operator accepted

1. Make one of three moves per card:

```
  demoable -> closed      the operator accepted it at Section 4
  demoable -> open        its proof command failed or ran nothing at Section 2
  stays demoable          built, and the operator has not seen it
```

2. Close with `bd close --reason`, putting Section 2's measured output in the reason.
3. Before staging the closes, run `bd export -o .beads/issues.jsonl`; in a git worktree, skip it, and you are in one when `bd where` prints a directory outside the current checkout.
4. Close the cards the operator's acceptance names, whether they worked the demo or judged the captures, and never on the absence of a complaint.
5. Name any card still `open` or `in_progress` as not shipped in this slice, and leave it where it is.

## 6. What the feedback changed

1. Work every Section 4 record to one of six outcomes:
   - A request to do something before this phase ends, such as research, a second look, or a design conversation: do it now, and say what came of it.
   - Accepted as it stands: say so in one line.
   - **A decision about how the product behaves: write it into the design document in this run**, in the document's voice with no mention of this demo, per `spec-task` "The design documents hold the product".
   - A new requirement nobody has specified: one line in the look-ahead sketch, or a card where it is concrete enough to title, with no requirement text or proof command unless it lands in the next slice.
   - A dropped requirement: close its card as won't-do with the operator's words in the reason.
   - Rejected: one line saying why.
2. Write a feedback point to Jira, Trello, or any outside tracker only when the operator asks, per `~/.claude/CLAUDE.md` "Change a card only when I ask".
3. Reopen nothing in the demoed slice: send new requirements and revisions to `spec-task` for a later slice, and never file a card with the demoed slice's label to fix what the demo found.
4. Name every design document edited, quoting the sentence each gained or lost, and every card created or closed by id, and commit both through `git-commit`.

## 7. Hand to `spec-task`

1. Before handing off, read your own room:

    $ python3 ~/.claude/skills/session-loop/scripts/session_budget.py --self

2. If it reports you are past the ceiling, or says `finish the step you are on`, write the handoff through `clear-task` yourself, telling it which section you stopped at and what it still owes, and end the turn, so the auto-clear mod clears the session.
3. Otherwise, hand to `spec-task` now, in the same turn, however small the slice, and never ask whether to run it.
4. If the operator said they would do something themselves, such as open the deployed page or complete a sign-in, and has not reported back, stop and say in one line what you are waiting on and that the spec follows it.
5. If the operator's acceptance asks a question or asks for something next, answer in prose and do it, searching the design documents first as Section 4 says, and then hand to the spec; never answer with a question about which to do first.

## What this template does NOT do

1. It decides, sizes, and pulls no next slice, and writes no EARS requirements or proof commands; that is `spec-task`.
2. It runs no build work; that is `tdd-cycle`, or `session-loop` unattended.
3. It inspects no process, reads no transcripts, and changes no skill; that is `systematize`, when the operator asks.
4. It repairs no failing proof command.
5. It decides no definition of released; the operator settles it in `spec-task` Section 1.
6. It writes no status, card id, or slice number into a design document.
7. It pushes nothing outward.
