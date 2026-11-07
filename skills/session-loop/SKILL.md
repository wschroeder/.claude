---
name: session-loop
description: Runs a long build as a series of fresh Claude Code sessions instead of one that fills up, each session working until its context reaches the 170,000 handoff ceiling or the same check fails three times running. Invoking it checks the repository, writes the handoff through clear-task when none exists, reports what is blocking, and starts the loop — the operator never types a shell command. Also carries the working agreement behind it: how big a session should be, the context bands where delegating starts to pay at this ceiling, and session_budget.py for measuring where sessions actually handed off. Use when starting or resuming unattended work, or when sessions keep running out of context. Whether to delegate at all, and what a subagent prompt must carry, is in the subagents skill.
---

# session-loop — run the work as a series of fresh sessions

1. Run the work as a series of fresh sessions that carry a written handoff instead of a transcript.
2. Let each session run until its context reaches 170,000, checking itself at the four points under "Shaping a session", and hand off then, not after one piece of work.
3. Hand off also after three consecutive failures of the same check, whatever the context number says.
4. Treat 170,000 as a safety rail the operator sets, never as a cost knob to tune; `scripts/test_run_loop.sh` keeps `scripts/run-loop.sh` and `scripts/session_budget.py` in step on it.

## When you are invoked, act. Do not just read.

1. Work through the steps below in order and stop at the first one that applies; the sections after them are reference for these decisions.
2. Do not ask before launching: invoking the skill is the go-ahead.
3. Pass no count of sessions: the loop runs until a session marks the work `DONE`, hands off blocked, or fails.

### 1. Look at the repository

```bash
cd <repo> && git rev-parse --show-toplevel && git log --oneline -3
git status --porcelain
ls -l HANDOFF.md 2>/dev/null && git check-ignore -v HANDOFF.md
git check-ignore -v .tmp/demos/x
```

1. If git ignores `/HANDOFF.md` but not `.tmp/demos/x`, append `/.tmp/demos/` to the file the first `-v` line names, because `demo-task` keeps the walk's folder there.
2. If that file is `.gitignore`, commit the line on its own.

### 2. No HANDOFF.md, or it is not gitignored

1. Produce the handoff here through `clear-task`, and make git ignore `/HANDOFF.md` so the loop's own rewrites do not read as unfinished work.
2. If `git status --porcelain` returned anything, take step 3 first and come back here once the tree is clean, because this step writes and commits.
3. Leave where git ignores the file to the operator: `.gitignore` changes the repository for everyone, and `.git/info/exclude` changes this clone only.

In order:

1. If `/HANDOFF.md` is not already ignored, find the operator's answer. If a handoff carries it or a line in the session's opening prompt gives it, follow it and do not ask again. Otherwise ask once, yes or no, through AskUserQuestion: "Add /HANDOFF.md to .gitignore? No puts it in .git/info/exclude, for this clone only."
2. Run `clear-task`, telling it this is `session-loop` step 2, the repository has no handoff yet, and the operator's answer from sub-step 1 word for word. Do not name the artifact for it, because its §0 check treats a form supplied in the arguments as an input to check.
3. On yes, add `/HANDOFF.md` and `/.tmp/demos/` to `.gitignore` and commit those lines on their own, under the standing permission in `git-commit`. On no, append both to `.git/info/exclude`, which commits nothing.
4. Read the file back and confirm `git status --porcelain` comes back clean.

Then:

1. Write the launch prompt to `pending-handoff.md` in the scratchpad directory your system prompt names, and end the turn. The auto-clear mod clears this session and submits the prompt, and the fresh session finds step 2 passing and launches. Write it as one line with the real repository path:

```
Load the session-loop skill for <repository path> and launch the loop.
```

2. Name the skill in words, never as `/session-loop`, because a submitted prompt that names a skill gets it loaded and nothing has shown a slash command running from one. Why: [references/driver-loop.md](references/driver-loop.md), "Why step 2 writes the launch prompt before the clear".
3. If no auto-clear mod is loaded, stop instead: say the handoff is written, name its first next step, and ask the operator to `/clear` and invoke this skill again.

### 3. The working tree is dirty

1. Do not launch on top of unfinished work or on a handoff written before it.
2. Say what is outstanding in one or two sentences and ask whether to finish and commit it here first.

### 4. The handoff is blocked

1. Read `HANDOFF.md`. Treat it as blocked if the first line starts `BLOCKED:`, or if the first item under "Next steps" depends on something under "Open questions for you".
2. Do not start the loop. Put each decision in its own paragraph, in the operator's terms, with your recommendation and what cuts against it.
3. If the session stopped only to ask which remaining step to do next, settle it yourself: write in the one that unblocks the most of what is left, or any of them where nothing waits on anything else, and launch.
4. Answer the operator's feedback before you file it: say where the design documents already stand on what they asked, and look up any answer that turns on the product's own domain. If what you find disagrees with what they asked for, put that to them in one line and wait.
5. Before you return to step 5, edit `HANDOFF.md` yourself: delete the `BLOCKED:` line and write the decision into the next steps, because the driver halts again on an unchanged first line.
6. If the feedback closes a slice rather than unblocking a step inside one, rewrite the handoff through `clear-task` instead of editing it.

### 5. Check there is unblocked work to start on

1. Say how many of the handoff's next steps can proceed without the operator.
2. Pick no number of sessions: the loop halts at the first session that changes nothing, or at the second in a row that only rewrites the handoff.

### 6. State the run, then launch it

1. State in a few lines the repository, HEAD, what the first session will work on, and that the run ends by itself when a session marks the work `DONE`, hands off blocked, or fails.
2. State that each session runs under `bypassPermissions`, editing and running whatever it decides to with no prompt. The reasoning is under "Permissions" in [references/driver-loop.md](references/driver-loop.md).
3. Launch it with the Bash tool's `run_in_background` set, and do not poll it: you are re-invoked when it exits.

```bash
bash ~/.claude/skills/session-loop/scripts/run-loop.sh <repo>
```

4. Pass `--handoff-at` only to move the 170,000 line.
5. Move the between-iteration reviewer with `--eval-model`, or turn it off with `--no-eval`. It runs on `claude-opus-5-5` at medium effort over the diff each session committed, answers PASS or findings, puts its findings in front of the next session's handoff, and stops the run after three rounds running on the same file.

### 7. When it stops, report what happened

1. Read the driver's output, never the child sessions' transcripts.

```bash
git -C <repo> log --oneline -20
python3 ~/.claude/skills/session-loop/scripts/session_budget.py <repo> --since <start>
```

2. If the stopped session produced a demo to look at, such as a page, a render, or a PDF, send it with SendUserFile. Paste the steps of a demo-steps file into your message and do not send the file.
3. If the driver's last line says the reviewer found something, read the file and fix each finding through `tdd-cycle` before you write any demo ask, because nothing in the loop reads the final iteration's findings. Put a finding you judge not worth fixing in the report with the reason. See [references/measurements.md](references/measurements.md).
4. Say what landed, where each session handed off (the `ctx_end` column), and why the loop stopped.
5. If it stopped on `DONE`, say the work is complete.
6. If it stopped on `BLOCKED:`, read the first line of `HANDOFF.md` against step 4 before you pass it on, and answer a question about what to do next yourself. If it really is the operator's, put it to them and offer to resume.
7. Read the handoff's "Open questions for you". Settle each question that is yours, and carry each one that is the operator's into the ask, the demo ask included. See [references/measurements.md](references/measurements.md).
8. If that question asks for a demo, load `demo-task` and enter it at Section 3, not Section 4. Start the demo server first with the command the demo file's steps name.
9. If the worker's walk record names the commit at HEAD, open its captures with Read and check each after-capture against its step; walk every step yourself, capturing as you go, only when HEAD has moved since that walk. Do either before Section 4 composes the ask.
10. After a walk, reset the demo's data, start the server again, and leave it running for the operator, as demo-task Section 3 says. See [references/measurements.md](references/measurements.md).
11. Open the ask with the phase line, directly above the question, or close the report with it where nothing needs deciding: the three phases in order, with the one the loop stopped in capitalized.

```
spec -> BUILD -> demo
```

### 8. Then measure yourself, before starting anything else

1. Check your own context before starting anything else, because the supervising session fills up like any other:

```bash
python3 ~/.claude/skills/session-loop/scripts/session_budget.py . --self
```

2. On `keep going`, report, and start the next run if there is one.
3. On `finish the step you are on`, finish what is in hand, then hand off as below, and start no other run.
4. On `hand off`, stop, and launch no iteration and no piece of work. Run `clear-task` for the block to paste, not for `HANDOFF.md`, because the driver rewrites that file every iteration for the workers. Tell the operator it is ready to clear and paste.

### Never

1. Never invoke this skill from inside a session the driver started.
2. In such a session, work until your own context says to hand off, write the handoff, and stop.

## What the driver does, and what stops it

1. Know that each iteration starts a fresh `claude -p` whose entire prompt is the handoff file, then decides from `git status`, `git log`, the handoff, and the run's JSON summary, never from a transcript.
2. Know that a PostToolUse hook in the operator's `~/.claude/settings.json` runs `session_budget.py --hook` on every tool call and exits 2 once a session passes the ceiling; the driver registers no hook of its own.
3. Expect the driver to stop when the handoff says `DONE` and the reviewer holds nothing against the last commit. A `DONE` with findings outstanding goes back for another session, twice at most before the run stops for a person.
4. Expect a `BLOCKED:` handoff with findings outstanding to go back with the session told to fix them and keep the question, twice at most, and not once the reviewer has found something in one file three reviews running; then the run stops on the question.
5. Expect it to stop also on `BLOCKED:` with nothing outstanding, a dirty tree, a non-zero `claude` exit, a session that ended other than by finishing, a reported error, or unchanged code with no bd card changing status, and never on a count.
6. Expect a usage limit to make it sleep until the reset the run summary names and retry the same iteration once, for the session and the reviewer alike. It stops on a limit only when it cannot read the reset time or the limit persists after the wait.
7. Know that it reads the summary rather than the exit code, because `claude -p` exits 0 even when cut off, and compares tree hashes rather than commit ids, because an amend that changes no file still makes a new id.
8. Run the loop only where write access to the repository already means trust, because the handoff file is executed as the next session's instructions with nobody reading it first.

Details, flags, and the permissions warning:
[references/driver-loop.md](references/driver-loop.md).

## When to delegate, and when it costs double

1. Before every subagent or workflow, ask:

> After this agent returns, will I open the same material it opened?

2. If yes, do not delegate.
3. Delegate when the agent's context replaces one you would otherwise have paid: research against sources you will never open, wide searches where only the answer matters, and independent checking of a list of claims.
4. Match the model to the task: Haiku for wide or mechanical passes where only the answer matters, Sonnet for judgment you will not re-read yourself, and the driver model for the reasoning you hold in this session. If the choice is close, take the more capable model.
5. Do not delegate work you will review, such as a change you then read line by line.
6. Run `quick-review` and `security-review` yourself, never in subagents; the loop contract names them outright because a worker never sees this file.
7. Below about 100,000 context, delegate nothing; the band where delegating wins opens around 130,000, and that is never a reason to hand off early. The arithmetic and a turn-count table: [references/driver-loop.md](references/driver-loop.md) under "Which model runs what".
8. Take the standing exception for investigation, and what a delegation prompt must carry, from `subagents`; the context bands here hold only at the loop's 170,000 ceiling.

## Shaping a session

1. Ask how full you are at four points: after each commit, before starting the reviews a piece of work owes, after the probing that opens one, and when a review hands back a finding, before you load any skill to fix it:

```bash
python3 ~/.claude/skills/session-loop/scripts/session_budget.py . --self
```

2. Skip the check below about 100,000 context.
3. Read the line it prints, `<session>: turn N, context X of 170,000 — hand off` or `— keep going; R of room, and a handoff through clear-task measured about C`, where C is `HANDOFF_ALLOWANCE` in `session_budget.py`. The exit code stays 0 until the ceiling.
4. On `keep going`, carry on here, because the next session pays about 104,000 tokens to read its way back.
5. On `finish the step you are on`, finish it, write the handoff through `clear-task` yourself, and stop without starting another.
6. On `hand off`, stop where you are: commit what you have with a subject saying it is unfinished, and write the handoff naming where in the cycle you stopped and what the work still owes. The next session amends that commit or builds on it.

### The other trigger: three failures of the same check

1. Hand off after a single command, such as the same test, build, or query, fails a third time after two attempts to fix it, whatever the context number says.
2. Start the count over when a different command fails, but not when the same command fails with a new error.
3. Commit what you have with a subject saying it is unfinished, and write the handoff naming the command, its latest output, and each fix already tried. Why: [references/driver-loop.md](references/driver-loop.md), "Why three failures hand off".
4. Ask most of all just before the reviews, because review turns cost the most where the context is fullest and a fresh session reads the diff better.
5. Apply this loop rule only inside the loop; outside it, finish and review a piece of work before you commit it.
6. Front-load the expensive reading, such as design documents, the code you are matching, and the measurements the work must hit, while the context is small, and read each once.
7. Put a measurement into the record once, not into the conversation three times.
8. Wait in one blocking call with a timeout, never by looking repeatedly.

What each of these numbers was measured on:
[references/driver-loop.md](references/driver-loop.md).

## Measuring

```bash
BUDGET=~/.claude/skills/session-loop/scripts/session_budget.py
python3 "$BUDGET" ~/projects/your-repo --since 2026-08-09
python3 "$BUDGET" . --verbose      # list each subagent
python3 "$BUDGET" . --json         # for a script to read
python3 "$BUDGET" . --self         # the running session, about itself
python3 "$BUDGET" . --waste        # by round, and what each round read
```

Reading the columns, and what `--waste` groups by:
[references/driver-loop.md](references/driver-loop.md).

## Autonomous behavior

1. Without asking, run steps 1 through 6 and launch, and report a blocked handoff as decisions rather than as a failure to launch.
2. Never read a child session's transcript to decide what to do next, start a loop from inside one, or launch another run once your own `--self` check says to hand off.
