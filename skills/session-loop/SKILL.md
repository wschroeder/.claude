---
name: session-loop
description: Runs a long build as a series of fresh Claude Code sessions instead of one that fills up, each session working until its own context reaches a handoff threshold. Invoking it checks the repository and the handoff file, reports what is blocking, and starts the loop — the operator never types a shell command. Also carries the working agreement behind it: how big a session should be, when handing work to a subagent pays and when it doubles the reading, and session_budget.py for measuring where sessions actually handed off. Invoke when starting or resuming unattended work, when deciding whether to use subagents, or when sessions keep running out of context. Do not auto-activate.
---

# session-loop — run the work as a series of fresh sessions

Every turn re-reads the whole context, so a session that has been going a while
pays many times over for the same work. The fix is to end sessions and start
new ones, carrying a written handoff instead of a transcript. This skill does
that on a loop.

Ending too early is its own waste, though: a fresh session spends about 104,000
tokens re-reading its way back to where the last one already was. So a session
runs until its context reaches 225,000, checking itself at three points along
the way, and hands off then — not after one piece of work. A hook the driver
installs checks the same number on every tool call, so the ceiling holds even
when a session never reaches one of those three points.

225,000 is the operator's number, and it decides less than it looks like it
should. Measured over 29 sessions, what a turn of actual work costs barely moves
with where the session stopped — the correlation is -0.07. What it does track is
how much the session read before it first changed a file, which ranged from
60,016 to 187,085 across those same sessions. So treat this ceiling as a safety
rail and not a cost knob. Lower is the dangerous direction: 4 of the 29 had
changed nothing at all by 150,000 context, and a ceiling there would have retired
them before they did any work.

The two numbers it sits between are both measured. A turn taken here costs
exactly its own context, and a turn of work from a fresh session costs a median
195,813 once that session's own re-reading is charged to it — so below roughly
195,813 carrying on is cheaper, and above it handing off is. That figure's
quartiles are 153,681 and 251,450, so a ceiling a little above the median buys
margin against drawing a slow-starting successor. The upper bound is accuracy:
answers were measured starting to degrade past 250,000. If answers go wrong in
the last stretch of a session, lower this before blaming the work.

## When you are invoked, act. Do not just read.

Work through these in order and stop at the first one that applies. The
sections below this one are reference for the decisions here, not a preamble
to read first.

If the operator passed `go`, skip the confirmation in step 6 and launch.
Otherwise confirm first. There is no count to pass: the loop runs until a
session marks the work `DONE`, hands off blocked, or fails.

### 1. Look at the repository

```bash
cd <repo> && git rev-parse --show-toplevel && git log --oneline -3
git status --porcelain
ls -l HANDOFF.md 2>/dev/null && git check-ignore -v HANDOFF.md
```

### 2. No HANDOFF.md, or it is not gitignored

Stop and say what is missing. The handoff is produced by ending a normal
session with `clear-task` and asking it to write the block to `HANDOFF.md`;
`/HANDOFF.md` belongs in `.gitignore` so the loop's own rewrites do not read
as unfinished work. Offer to add the ignore rule now if that is the only gap.

### 3. The working tree is dirty

The loop refuses to start on top of unfinished work, and it is right to. Say
what is outstanding in one or two sentences and ask whether to finish and
commit it here first. A handoff written before those changes describes a repo
that no longer exists, so do not launch on a stale one.

### 4. The handoff is blocked

Read `HANDOFF.md`. It is blocked if the first line starts `BLOCKED:`, or if
the first item under "Next steps" depends on something under "Open questions
for you".

This is the common case and it deserves a fast, clean answer rather than a
launch. Do not start the loop. Instead put each decision in its own paragraph,
in the operator's terms, with your recommendation and what cuts against it.

First check the question is really theirs, though. A session that stops to ask
which of the remaining steps to do next is asking something you can settle:
write in the one that unblocks the most of what is left, or where nothing waits
on anything else, write in any of them and launch. Do not pass that one on. The
operator has no preference between two independent steps, and the run has been
sitting idle since the moment it asked.

Their answer does not reach the next session on its own. The blocked session
left `BLOCKED:` on the first line of `HANDOFF.md` with its question below, and
the driver halts on that line — it will halt again the instant you relaunch,
because nothing has changed. So before you return to step 5, edit `HANDOFF.md`
yourself: delete the `BLOCKED:` line and write the decision into the next steps,
where the work that was waiting on it can now proceed. That edited file is what
carries their answer forward — the next fresh session reads it as its
instructions and picks up where the blocked one stopped. One word back from them
usually unblocks the whole queue.

### 5. Check there is unblocked work to start on

Say how many of the handoff's next steps can proceed without the operator. You
are not picking a number of sessions — the loop stops itself when the work runs
out, because a session with nothing left to do commits nothing and halts it.
This is only the check that there is something to start on, and a sense of how
much the run will chew through before it gets there.

### 6. Propose the run, then launch it

State the repository, HEAD, what the first session will work on, that the run
ends by itself — when a session marks the work `DONE`, hands off blocked, or
fails, not after any set number of sessions — and, because it runs
unattended, that each session runs under `bypassPermissions`, editing and
running whatever it decides to with no prompt. A few lines, not a page. That
last line is the operator's cue to confirm this is a repository where write
access already means trust; the reasoning is under "Permissions" in
[references/driver-loop.md](references/driver-loop.md). Then wait for one word
unless the operator already said `go`.

```bash
bash ~/.claude/skills/session-loop/scripts/run-loop.sh <repo>
```

Run it with the Bash tool's `run_in_background` set. It is minutes to hours
per iteration and the operator may be on a phone, so a foreground call would
just block. Do not poll it either — the driver prints as it goes and you are
re-invoked when it exits.

Each session runs until its own context reaches 225,000 and then hands off, so
one iteration is however much work fits under that — usually several commits,
not one. Pass `--handoff-at` only to move that line; the reasoning is in
[references/driver-loop.md](references/driver-loop.md).

Between iterations the driver runs a second, much smaller session over the diff
the first one just committed. It has no memory of writing that code and no tools
to change it, and it answers PASS or a list of findings, each naming what
executes the code it is about. Anything it finds goes in front of the next
session's handoff as a proposal that session may put down. Three rounds running
on the same file stop the run instead, because a reader with no mission cannot
tell when the file it keeps failing has stopped mattering. It runs on `sonnet`
and cost $0.28 in the run that was measured, against $6 to $8 for the session it
read. Move it with `--eval-model`, or turn it off with `--no-eval`.

### 7. When it stops, report what happened

Read the driver's output, not the child sessions' transcripts — reading those
is how a watcher turns back into the thing this skill exists to avoid.

```bash
git -C <repo> log --oneline -20
python3 ~/.claude/skills/session-loop/scripts/session_budget.py <repo> --since <start>
```

Say what landed, where each session handed off (the `ctx_end` column), and why
the loop stopped. If it stopped on `DONE`, the work is complete — say so. If it
stopped on `BLOCKED:`, the first line of `HANDOFF.md` is the question — read it
against step 4 before you pass it on, because a question about what to do next
is one you answer yourself. If it really is the operator's, put it to them and
offer to resume.

### 8. Then measure yourself, before starting anything else

Watching a loop is not free, and the session doing the watching fills up like
any other. One supervising session reached 277,862 context while its workers
were being held to 170,000, the ceiling at the time. So ask yourself the same
question you ask them:

```bash
python3 ~/.claude/skills/session-loop/scripts/session_budget.py . --self
```

On `keep going`, carry on — report, and start the next run if there is one.

On `hand off`, stop. Do not launch another iteration, and do not start the next
piece of work. Run the `clear-task` skill, write the handoff block, and tell the
operator it is ready. They clear and paste it into a fresh session, which picks
the loop back up from there.

### Never

Do not invoke this skill from inside a session the driver started. You would
be launching a loop from within a loop. A session that finds itself under the
loop protocol works until its own context says to hand off, writes the handoff,
and stops.

## What the driver does, and what stops it

Each iteration it starts a fresh `claude -p` whose entire prompt is the
handoff file, waits, then decides what to do next from `git status`,
`git log`, the handoff, and the run's JSON summary. It never reads a
transcript. That is what keeps it free of context: it accumulates nothing, so
it cannot fill up and become an orchestrator.

It also hands each session a `--settings` file it writes into the logs
directory, registering `session_budget.py --hook` as a PostToolUse hook. That is
what enforces the ceiling on a session that works for eighty turns without
reaching any of the three points the contract names — the hook reads the
session's own transcript on every tool call, says nothing while there is room,
and exits 2 with the number when there is not. It adds to the operator's own
settings rather than replacing them.

It stops when the handoff says `DONE` and the reviewer is holding nothing
against the last commit — a `DONE` with findings outstanding goes back for
another session instead, twice at most before the run stops and asks for a
person. It also stops when the handoff says `BLOCKED:`, when the tree is dirty, when
`claude` exits non-zero, when a session ended for any reason other than
finishing, when the session reported an error, or when the code came out
unchanged — never on a count. `claude -p` exits 0 even when it was cut off part
way, so the driver reads the summary rather than trusting the exit code. It
compares tree hashes rather than commit ids, because a session may amend the
unfinished commit it was handed, and an amend that changes no file still
produces a new commit id.

Details, flags, and the permissions warning:
[references/driver-loop.md](references/driver-loop.md).

One property to understand before starting one: the handoff file is the next
session's instructions, executed with nobody reading them first. Anyone who
can write to it decides what the loop does. Run it only where write access to
the repository already means trust.

## When to delegate, and when it costs double

This is the decision the loop cannot make for you, and getting it wrong makes
the same material get read twice. Ask one question before every subagent or
workflow:

> After this agent returns, will I open the same material it opened?

If yes, do not delegate. You pay its climb from a fresh context up to a full
one, and then your own reading on top.

**Delegate** when the agent's context genuinely replaces one you would
otherwise have paid: research against sources you will never open, wide
searches where only the answer matters, independent checking of a list of
claims.

**Match the model to the task** when you do delegate. Haiku handles wide or
mechanical passes where only the answer matters; Sonnet handles work that needs
judgment you will not re-read yourself; keep the driver model for the reasoning
you hold in this session. Where the choice is close, take the more capable
model — a wrong result is re-done at full price, so saving tokens on a close
call buys nothing.

**Do not delegate** when you will review the result. Building a change you
then read line by line means the diff arrives in your context regardless, so
the delegation saved nothing. If your working agreement says you review every
change, handing that change to an agent cannot pay — the standard is right,
and the delegation is what has to go.

**The reviews are the case this keeps catching.** A session that hands
`quick-review` and `security-review` to subagents still reads every finding and
applies it, so the diff lands in its context either way. Handing them off has
measured as costing more and finishing less. The loop contract names the reviews
outright, because a worker session is handed the handoff and the contract and
never sees this file.

Below about 100,000 of context no job is large enough for a subagent to win —
its turns cost more than yours. The band where delegating does win opens around
130,000. That is a reason not to delegate, never a reason to hand off early.

The measurements behind those two numbers, the climb-versus-growth arithmetic,
and a turn-count table for the borderline cases are in
[references/driver-loop.md](references/driver-loop.md) under "Which model runs
what". Read them when a delegation looks borderline; the rule above is enough
the rest of the time.

## Shaping a session

Ask how full you are at three points — after each commit, before starting the
reviews a piece of work owes, and after the probing that opens one:

```bash
python3 ~/.claude/skills/session-loop/scripts/session_budget.py . --self
```

Not below about 100,000 context, though. Asking is itself a full-context turn,
and down there the answer cannot be anything but keep going. Measured on
2026-08-16, repo-a sessions ran the check six times each — one at 43,254
context — where repo-b ran it three or four times starting at 110,714. No check
below 102,349 in any of those sessions returned `hand off`, and the six checks
cost between 550,055 and 756,225 tokens a session, up to 11% of what the session
read.

It prints `<session>: turn N, context X of 225,000 — hand off` or `— keep going`. On
`keep going`, carry on here; stopping earlier is not thrift, because the next
session pays about 104,000 tokens to read its way back to where you already are.

On `hand off`, stop where you are. A piece of work does not have to be finished
first: commit what you have with a subject saying it is unfinished, and write
the handoff so it names where in the cycle you stopped and what the work still
owes. The next session amends that commit or builds on it.

Asking only after a commit is what let sessions sail past the line. Measured
across four repo-a sessions, the first commit landed at 182,032, 268,636 and
271,695 context, so the only checkpoint on offer could not fire until the
session was up to 100,000 tokens past 170,000 — and what it printed then was
correct and useless. The point just before the reviews is the one that pays:
review turns cost the most where the context is fullest, and they read the diff
better from a session that did not write it.

This is the loop's rule and holds only inside it. Outside the loop a piece of
work is finished and reviewed before it is committed.

Front-load the expensive reading — design documents, the code you are
matching, the measurements the work must hit — while the context is small.
Read a thing once. Put a measurement into the record once, not into the
conversation three times.

**Wait in one call that blocks, never by looking repeatedly.** A turn spent
asking "is it finished yet?" costs exactly what a turn spent working costs,
because both re-send the whole context. On 2026-08-16 repo-a's last session
spent 40 turns and 4,149,263 tokens on `sleep 300`, repeated agent polling, and
15 turns whose entire output was the word `Waiting.` — 35% of everything that
session read, at up to 156,555 tokens for one of them. repo-b waited on long
runs too, but blocked once per wait with a single call and a ten-minute timeout,
and spent 7 turns on it across a whole session.

## Measuring

```bash
BUDGET=~/.claude/skills/session-loop/scripts/session_budget.py
python3 "$BUDGET" ~/projects/your-repo --since 2026-08-09
python3 "$BUDGET" . --verbose      # list each subagent
python3 "$BUDGET" . --json         # for a script to read
python3 "$BUDGET" . --self         # the running session, about itself
python3 "$BUDGET" . --waste        # by round, and what each round read
```

`--waste` groups the run into rounds — the stretch between one usage-limit
cutoff and the next, which is the unit a run is actually lived in — and says
what each round's tokens were spent reading. The floor is the system prompt,
tool schemas and skill listing every turn re-reads before it reaches anything
about the work; it is measured from the round's own sessions rather than held
as a constant, by fitting opening context against handoff length. The reviewer
is counted here and in `--value`, which is a fifth to a quarter of a round.

The last line of a round is the one to read first: a session the limit cut off
before it could commit read everything on that line for nothing.

Everything is in tokens; nothing is priced. Three columns carry it. `ctx_end`
is where each session stopped and should land near the threshold — well under
it means sessions are handing off early and re-orienting more often than they
need to. `ctx_start` rising across sessions means the handoff is inflating.
`fanout` is what the subagents read as a multiple of what the session read:
`0.00x` never delegated, `1.00x` delegating doubled the reading. A row marked
`<- cut off by the usage limit` did not choose to stop, so its `ctx_end` says
nothing about where the threshold put it.

## Autonomous behavior

Without asking: run steps 1 through 5, and report a blocked handoff as
decisions rather than as a failure to launch.

Ask first: before launching, unless the operator said `go`. It runs with nobody
watching.

Never: read a child session's transcript to decide what to do next, start a loop
from inside one, or launch another run once your own `--self` check says to hand
off.
