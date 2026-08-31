# Running a long build unattended

Contents:

- [Why /loop and cron are not this](#why-loop-and-cron-are-not-this)
- [What the driver does](#what-the-driver-does)
- [The handoff contract](#the-handoff-contract)
- [Where a session hands off](#where-a-session-hands-off)
- [Permissions](#permissions)
- [The flags that matter](#the-flags-that-matter)
- [Starting one](#starting-one)
- [Reading what it did](#reading-what-it-did)

## Why /loop and cron are not this

`/loop 30m <prompt>` re-fires a prompt into the conversation it was started
from, on a schedule. So does a cron job created inside a session. Both are
useful — polling a build, checking a deploy, a standing review — and both
keep every earlier turn.

That makes them the wrong shape here. A loop whose whole purpose is to retire
a context cannot be built out of a mechanism that preserves it: after eight
iterations you have one session at half a million tokens, which is the
problem, not the fix.

The thing that actually resets a context is a new operating system process.
`claude -p "<prompt>"` starts a fresh session, runs to completion, prints a
result, and exits. Its transcript lands under `~/.claude/projects/` like any
other, so the same tools read it.

Use `/loop` for watching something. Use a driver process for building
something.

## What the driver does

`scripts/run-loop.sh`. One iteration:

1. Stop if the handoff file is missing or empty — a session was meant to
   rewrite it and left nothing behind. Because the handoff is gitignored, this
   does not show up as a dirty tree.
2. Stop if the handoff's first line begins `BLOCKED:` (a decision the operator
   has to make) or `DONE` (the work is complete).
3. Stop if the working tree is dirty — that means the previous session did
   not finish, and a fresh one would build on half-applied work.
4. Note the current tree hash.
5. Run `claude -p` with the handoff file as its entire prompt, plus a short
   protocol block appended, and wait. It also passes `--settings` at a small
   file it writes into the logs directory, registering the handoff hook
   described below.
6. Stop if claude exited non-zero, or if the run's summary says it ended for
   any reason other than finishing.
7. Stop if the tree hash did not move. A session that changed nothing would
   hand the next one the same starting position, and the loop would spin. The
   tree rather than the commit id, because a session may amend the unfinished
   commit it was handed, and an amend that touches no file still produces a new
   commit id as soon as it lands a second later than the commit it replaces.
8. Otherwise loop, and the handoff the session just rewrote becomes the next
   iteration's prompt.

The driver never reads a transcript. It reads `git status`, `git log`, the
handoff file, and the JSON summary of the run — all small, all fixed size.
That is the property that makes it a driver rather than an orchestrator: it
accumulates nothing, so it cannot fill up.

## The handoff contract

One file in the repository, `HANDOFF.md` by default, holds everything the
next session needs. It is the same artifact the `clear-task` skill produces
for a human to paste, so a run can be picked up by hand at any point.

The driver appends a short protocol to it before each run, telling the session a
few things: load the skill the work matches before starting the work, which is
here rather than in the handoff because a handoff names only the skills the
session that wrote it happened to load; commit as you go; check your own context
at three points and either carry on or stop; if a decision is needed that only
the operator can make, put `BLOCKED: <one sentence>` on the first line and stop;
and if the work is all done with nothing left to do, put `DONE` on the first
line and stop.

That middle clause has to be drawn narrowly, because `BLOCKED:` halts the whole
run until somebody happens to look at it — the most expensive thing a session
can do, and the one escape it can reach for at any moment. Choosing which piece
of work to do next is the case that has come up: a session with room to keep
working stopped the run to ask which of the remaining steps to take, which the
operator had no view on. So the protocol answers that one in advance. Take the
step that unblocks the most of what is left; where nothing waits on anything
else, take any of them and record which in the handoff, so the next session does
not start the same piece of work over.

The commit rule carries its own permission, because it has to. Starting the loop
is the operator's authorization for every commit it makes in that repository, and
for amending — a commit the running session made, and the unfinished commit an
earlier session left for it. The protocol says so outright, so a session that
would otherwise wait for a person does not. The bound is what the commit means
rather than which session made it: a commit that finished its piece of work is
settled and gets built on, and one that only records where the work got to is a
note the next session is free to rewrite. Nothing here needs the amend bounded
for the driver's sake, because the driver compares tree hashes and a rewrite that
changes no code cannot pass for progress.

## Where a session is allowed to stop

The threshold only binds if the session can act on it, and for a long time it
could not. The check ran after a commit, and a commit meant a piece of work that
was finished and reviewed — so the nearest legal stopping point was however far
away the end of the current piece of work happened to be. Measured across four
repo-a sessions, the first commit landed at 182,032, 268,636 and 271,695
context against a 170,000 ceiling. Every verdict those sessions got was correct
and arrived up to 100,000 tokens too late. Over the same run, 61% to 70% of each
session's tokens were spent above the line.

So the session now asks at three points — after each commit, before starting the
reviews a piece of work owes, and after the probing that opens one — and may stop
at any of them by committing what it has, marked unfinished, with the handoff
naming where in the cycle it stopped and what the work still owes.

Asking at those three points is not enough on its own, because all three are
milestones in the work cycle and a session that spends its whole life on one
piece of work reaches them once. Measured across a later run of both
repositories: every worker committed exactly once, between turn 27 and turn 86,
and the single check it ran landed a turn or two after that commit at 145,000 to
204,000 context. 29% of one run's tokens still went above the line.

So the driver also enforces the ceiling from outside the session. It writes a
settings file registering `session_budget.py --hook` as a PostToolUse hook and
passes it with `--settings`, which adds to whatever the operator already has
rather than replacing it. The hook fires on every tool call and is handed the
path to the session's own transcript, so the number gets read whether or not the
session thought to read it. Under the line it prints nothing — anything it wrote
would enter the context and be re-paid by every later turn. Over the line it
exits 2 with one line on stderr naming the context, the ceiling, and the two
steps that make this a handoff rather than an abort: commit what you have marked
unfinished, then rewrite the handoff.

Three things about that shape were probed rather than assumed. Hooks do fire in
headless `claude -p` runs. A hook writing to plain stdout is invisible to the
model, while exit 2 with stderr arrives as a blocking error it reads back
verbatim. And PostToolUse exit 2 does not undo the call that just ran — a live
run over the line committed successfully with the hook firing on the commit
itself. PreToolUse would be the wrong event for exactly that reason: exiting 2
there denies the call, so a session over the line would be refused the Bash
calls it needs to commit and hand off, and would be trapped rather than retired.

The point before the reviews is the one that pays. In those same sessions the
review sequence began at 191,278 to 212,848 context and added 34,514 to 77,358
of growth, so it ran at the most expensive part of the session; run from a fresh
one it costs a fraction of that. It also reads better there. The session that
wrote the code is the worst-placed one to read it back, because it reads the diff
for what it meant; a session that did not write it reads the diff for what it
says.

Sessions that already fit are unaffected. Over the same run the repo-b sessions
reached their first commit at 141,066 to 158,717 and ended at 154,881 to 172,453,
so every checkpoint they hit said "keep going" until the last one.

This rule holds inside the loop. Outside it, a piece of work is finished and
reviewed before it is committed.

Push is handled differently, and the wording matters more than it looks. A bare
"do not push" forbids the act and leaves the subject open, which produces the two
behaviours it was meant to prevent: a session that has just committed asks
whether to push as well, or checks for a remote, finds none, and writes a
paragraph explaining why no push was necessary. The first stops an unattended run
until a person answers. The second spends turns on a question nobody asked. So
the protocol closes the topic rather than prohibiting the act — do not push, do
not ask, do not go looking for a remote, and report nothing about it either way.
Whether anything is pushed is settled outside the loop.

That paragraph is not decoration. Across two repositories, 19 of 48 loop
sessions committed nothing at all, and three of them — 92 million context tokens
between them — had finished the work, the tests and both reviews before stopping
one command short. One says why in its own handoff: "destructive git actions need
per-action authorization." The driver then halts the whole run on "the session
changed nothing," so the finished work sits in a dirty tree and every remaining
iteration is thrown away.

That last rule is what makes an unattended run safe to leave. A session that
hits a real question halts the loop instead of guessing, and the first line of
the handoff tells you what it wanted.

Keep the handoff honest about what is measured and what is believed, keep the
decisions already made in it so they are not relitigated, and keep the dead
ends in it so they are not walked twice. A handoff drifting past six or seven
thousand tokens has started becoming a transcript; prune it.

## Where a session hands off

A fresh session is not free. Measured across 29 sessions in two repositories: one
opens at about 39,000 tokens of context before it has read anything of yours, and
the median one does not land its first change until about 105,000. That gap is
what every handoff costs, and it is paid again every time.

The median hides the part that matters. Across those 29 sessions the first file
change landed anywhere between 60,016 and 187,085 context — a threefold spread —
and it is that spread, not the ceiling, that decides what a run costs.

Take cost per turn of actual work: total context spent, divided by the turns
after that session's own first Edit or Write. Correlated against the obvious
candidates, only one of them explains anything.

```
  how much it read before first changing a file    r = +0.62
  how many turns it ran                            r = -0.33
  where the session stopped                        r = -0.07
```

Split the same sessions on that first number and the size of it is plain. The ten
that first touched a file below 90,000 context cost a median 144,049 per working
turn and got 51 working turns out of their life. The nine that first touched one
above 130,000 cost 264,826 and got 20.

So the handoff threshold is close to irrelevant as a cost control. An earlier
version of this section said otherwise: it carried a fitted curve putting the
cheapest stop near 162,000 and charging 200,000 a 4% premium. That fit assumed a
single re-orientation cost shared by every session. The measurement says the cost
varies threefold between them, which swamps the curve.

What the threshold is genuinely for is not retiring a session before it has done
anything. Lower is the dangerous direction: 4 of the 29 had not changed a single
file by 150,000 context, and 1 had not by 170,000. A ceiling beneath those
numbers does not save money — it throws away reading the session already paid
for.

The default is 225,000, set between two measured numbers. Below it: a turn taken
in the session you already have costs exactly its own context, while a turn of
work from a fresh session costs a median 195,813 with that session's whole
re-orientation charged to it — so carrying on is the cheaper move up to roughly
195,813 and handing off is cheaper after. That median has quartiles of 153,681
and 251,450, the same threefold spread as everything else here, so a ceiling
somewhat above it buys margin against drawing a slow-starting successor. Above
it: this operator measured answers starting to degrade past 250,000, which is
the hard bound. If answers start going wrong in the last stretch of a session,
this is the first number to lower.

What it is not is where the money is. The money is in why a session reads 60,000
tokens before its first change on a good day and 187,000 on a bad one.

Both errors cost real tokens, and it is worth knowing which one you actually
make. Measured over the 22 driver sessions in these two repositories that
finished normally under the earlier rule — commit one unit of work, then stop —
the common error was overshooting, not stopping short. The median session ended
at 327,000 context and 15 of the 22 ran past 200,000. Only four ended under
165,000.

So "stop after one unit" did not keep sessions small. A unit of work in a real
repository is a slice plus its tests plus a mutation survey plus two reviews,
and that runs to a third of a million tokens on its own. The self-check is the
ceiling those sessions never had. It also catches the opposite case, which does
happen: a session that finishes early is told to keep going rather than hand off
before it has earned back its own 104,000 tokens of orientation.

The worker measures itself:

```bash
python3 ~/.claude/skills/session-loop/scripts/session_budget.py . --self
```

It prints `<session>: turn N, context X of Y — hand off` or `— keep going`,
and exits 3 when it is over. The session name is there because the lookup can
land on a neighbouring transcript, and a verdict with no name on it gives the
reader no way to notice that it did. Claude Code puts the running session's id in
`CLAUDE_CODE_SESSION_ID` and names the transcript after it, so a session can
find its own record; that holds in headless `claude -p` runs too, and the
transcript is flushed as the session goes, so the number is current rather than
whatever it was when the process started.

## Permissions

Start with what the handoff file actually is. Every iteration hands it to a
session as that session's whole instruction set, with no person reading it in
between. It is a program the loop runs, not a note it reads. Whoever can write
to that file decides what the next session does, at whatever permission mode
the loop was started with — so on a permissive mode, write access to the repo
is write access to your shell.

That matters in three concrete situations, and none of them is exotic. A
repository that takes contributions from anyone else. A session that reads a
web page, an issue, or a dependency's README and then writes what it read into
the handoff. A build step that can touch files in the tree. Run the loop where
write access to the repository already means trust, and nowhere else.

Then the mechanics, and they are why the default is bypassPermissions rather
than something narrower. An unattended session cannot answer a permission
prompt, and nothing waits for one: the prompt is taken as a denial, the call
does not happen, and the session finishes and reports success. Measured with a
headless run under `acceptEdits`: a shell command outside the settings allowlist
came back denied, the session said `DENIED` and finished, and the run JSON
reported `terminal_reason: completed` with the refused call under
`permission_denials`. Nothing failed. The session simply did less.

For most tools that is a quiet loss of quality. For the commit it is fatal to
the whole loop. Every iteration has to commit — the driver decides whether to
continue by whether HEAD moved — and a commit is a `git` call, not a file edit,
so no edit-accepting mode covers it. Probed on this machine: the permissions
hook auto-approves `git status` and `mix test` but passes `git add` and
`git commit` through to a prompt, and a prompt headless is a denial. Under
`acceptEdits` the session would do the work, have its commit refused without a
sound, leave a dirty tree, and the driver would halt the run on "committed
nothing" — on the first iteration. bypassPermissions is the only mode under
which the session's own commit goes through with nobody there, so it is the
default.

That reach is the price of it, and it is the danger the top of this section
already named. bypassPermissions lets the session edit and run whatever it
decides to, and the handoff it is handed is instructions rather than a note.
Together they mean write access to the repository is write access to your shell,
for the length of the run, unattended. Run the loop only where that is already
true: where `git` is a real undo, the repository takes no untrusted
contributions, and you will read the history afterwards. Where it is not, do not
loosen the loop to fit — do that work attended instead.

The driver still prints the denial count after each run. Under bypassPermissions
it should be zero; a non-zero count means something refused the session a tool
even so, and that session worked without something it reached for.

## The flags that matter

Measured against `claude --help` and one live `claude -p` run:

```
  -p, --print              run headless: take the prompt, work, print, exit
  --output-format json     the summary the driver reads: num_turns,
                           terminal_reason, is_error, session_id
  --permission-mode M      bypassPermissions (default) | acceptEdits | auto |
                           dontAsk | manual | plan
  --model NAME             claude-opus-5 (default); an alias like opus or
                           sonnet is the latest of that family, not a fixed one
  --effort LEVEL           low | medium | high | xhigh | max
  --autocompact auto|N     when to compact rather than stop
  --add-dir DIR            extra directories the session may touch
```

There is a `--max-budget-usd` and the driver does not use it. A fixed dollar
cap cut an expensive session at half the work of a cheap one — measured across
those same 18 sessions, cost per output token ranged more than two to one — so
the same number meant different amounts of work on different days. Context does
not drift like that, and the session can read its own.

What matters instead is that a session can stop without saying so. Measured:
a run cut off part way still exits 0. The shell's exit code cannot tell a
finished session from a cut one, which is why the driver reads
`terminal_reason` from the summary and stops on anything other than
`completed` rather than starting a fresh session on top of interrupted work.

## The second reader

The session that wrote a diff is the worst-placed one to read it back: it reads
for what it meant to write. It is also the most expensive reader available,
because by the time a piece of work is finished its context is at its fullest
and every review turn is billed at that.

So after each iteration commits, the driver runs a second session over just that
diff. It gets `HEAD_BEFORE..HEAD` and nothing else — no handoff, no protocol, no
memory of the work — and it is launched with `--disallowed-tools Edit Write
NotebookEdit`, which is what makes it a reader rather than a second builder.
Probed: told directly to fix a bug it had just found, it came back with "Edit is
disabled for this session, in subagents as well as here" and the file was
untouched.

It runs on `sonnet` rather than the builder's model. Reviewing a stated diff
against a stated intent is the repeated, well-scoped shape a cheaper model
handles, and the measurement supports it: against a two-function diff carrying a
planted off-by-one and a planted shell injection, it found both, in 3 turns, for
$0.28 — against $6 to $8 for the session that wrote the code. `--eval-model`
moves it and `--no-eval` turns it off.

It answers `PASS` alone, or `FAIL` and one line per finding, each line naming
what executes the code it is about and when that last ran. It is not asked
whether a finding is worth fixing — it has the diff and nothing else, so it
cannot know — only for the fact that decides it, which the session holding the
handoff can then weigh. On `FAIL` the
findings are written to the logs directory and put in front of the next
session's handoff — in the prompt rather than in a file in the repository,
because writing them into the tree would leave it dirty and the driver's own
dirty-tree gate would then halt the run on the evidence it had just produced.
They are cleared the moment an iteration comes back clean; without that the same
findings are re-sent to every later session, which re-reads the diff, finds them
already fixed, and pays for that on every remaining iteration.

There is one thing it does decide, and it is the only claim in this loop that a
session used to make about its own work with nothing checking it. `DONE` on the
first line of the handoff ends the run — and the moment it is written is exactly
the moment the reviewer's findings are about a commit nobody will open again. So
`DONE` now ends the run only when the reviewer is holding nothing; otherwise the
work goes back for another session with the findings in front of it. Twice, at
most: a session that keeps declaring victory against a reviewer that keeps
disagreeing is a standoff, and an unbounded loop settles it by spending until the
account runs out, so the third time the run stops and asks for a person.

The same bound covers the case where nobody claims to be finished. Every finding
becomes the next session's first job, and a correct finding is the kind that
gets fixed — which puts the same file back in front of the reviewer, which finds
the next corner of it. Three consecutive rounds of findings about one file stop
the run and ask a person whether that file still matters. Measured on the run
that prompted it: three iterations and about ten million weighted tokens went
into the failure semantics of a one-shot script whose only job had finished two
iterations earlier, and every finding along the way was correct.

Two things it deliberately does not do. A finding on its own does not stop the
run — a reviewer that fell over or answered in prose is reported and the building
carries on, because the commits it failed to read are still in git for the next
session to reach. And it does not replace the reviews the contract asks a session to run —
those are deeper than this, and until there is a measurement of what this catches
that they do not, taking them out would be trading known depth for an unmeasured
substitute.

Two things to know before trusting it further than that. Its findings become
part of the next session's prompt, and that session runs under
bypassPermissions — so text in your repository reaches a session that can act on
it. That is not a new boundary, because the builder already reads the same diff
directly, but it is a second path along the same one. And the findings file
inherits whatever mode the logs directory has, exactly as the run summaries do,
so a `--logs` directory you made world-readable makes the findings and the run
summaries world-readable with it.

What it cannot do is run anything. The read-only allowlist is `Bash(git :*)`
plus Read, Grep and Glob, so an evaluator that wants to execute the function it
is suspicious of gets denied — measured, in the first end-to-end run: it tried
`python3 -c` on the buggy function to confirm an off-by-one and was refused. It
reached the right answer by reading instead, but its findings are reasoning
rather than measurement, and that is the cost of not giving a reviewer a shell.
Giving it one safely means running it in a throwaway worktree, which is not
built.

## Which model runs what

The driver runs Opus 5, pinned by full id rather than the `opus` alias, because
an alias resolves to whatever is newest when it runs and would change the driver
underneath a long build.

Picking between Opus versions is not a cost decision. Measured across 35 loop
runs in these two repositories, Opus 5 and Opus 4.8 priced within 2% of each
other per token, so running the older one saves nothing and gives up capability.

Where the model choice does matter is in what a session delegates, and there the
spread is real: in those same runs the Haiku subagents cost $0.22 against $507 of
driver time. That is the lever worth using deliberately. The protocol tells each
session to match the model to the task — Haiku for wide or mechanical passes
where only the answer matters, Sonnet for work needing judgment the session will
not re-read itself, the driver model for reasoning it keeps — and to take the
more capable model whenever the call is close, because a wrong result is re-done
at full price and the tokens saved on a close call buy nothing.

Note what that does *not* license. A cheaper subagent is only cheaper if the
session does not then read the same material itself. That question used to live
only in the skill body, which no worker ever sees — a session is handed the
handoff and the contract and nothing else — so the contract now carries it too,
naming the reviews outright.

The reviews are the case this keeps catching. On 2026-08-16 the three repo-a
sessions that handed `quick-review` and `security-review` to subagents cost
$51.30 and finished with one commit still marked unfinished. The last of them
spawned eight review subagents that read 13,383,442 tokens against the session's
own 11,782,397, and it hit the usage limit before it could commit. Over the same
day repo-b ran both of those reviews inline in every session, spawned no
subagent at all, cost $56.25 across eight iterations, and ended `DONE`. The
subagents were not what bought repo-a its reviews — repo-b got the same ones
without them. Model choice decides what a delegation costs, not whether it was
worth making.

The arithmetic underneath that is worth keeping, because the per-turn intuition
points the wrong way. A subagent turn really is cheaper: 73,535 tokens against
the parent's 100,704 in that session, since it opens near 21,400 rather than
carrying everything the parent has read. What overturns it is the climb. Those
eight subagents opened between 21,084 and 22,430 and had to reach between 52,231
and 176,573 before they could say anything, taking 7 to 27 turns each to get
within a fifth of their peak. Of the 13,383,442 they read, 7,103,053 went on the
climb and 6,280,389 on the review, and the parent spent 4,149,263 more waiting.
Delegation therefore pays only where the subagent's climb stands in for one the
parent would otherwise have made and then does not make anyway — which a review
of the parent's own diff never is, because the parent's climb there is zero.

Fitting those eight gives a subagent start of 21,735 and growth of 3,981 a turn,
against 2,108 a turn for a session working on its own, measured over three
sessions. Both were fitted from subagents re-reading a diff the parent already
held, so what follows bounds duplicated reading and not first reading: material
neither has opened, and the parent never will, is read once either way, and
reading it inline leaves it in the parent's context to be re-sent every turn
afterwards. Running the two curves against each other puts the crossover above
about 100,000 of parent context — below that no job is large enough for a
subagent to win, because its turns cost more than the parent's outright. The band
where it does win opens around 130,000. Under the old 170,000 handoff line that
left only 40,000 tokens of a session's life above the crossover, so the contract
told a session there to leave the job for the next one rather than give it to a
subagent. At the current 225,000 the band is 95,000 wide — but the curves were
fitted under the old ceiling, so read 170,000 as the end of the measurement and
not the end of the range. For a job needing the stated number of turns once the reading is done:

```
                        the session's context when it decides
  work turns        60k     100k     130k     150k     170k
       5          here     here     here     here     here
      10          here     here     here     here     agent
      15          here     here     here     agent    agent
      20          here     here     agent    agent    agent
      30          here     here     agent    agent    agent
      40          here     here     here     agent    agent
      60          here     here     here     agent    agent
```


Read the last column as the end of what was measured rather than the end of
the range. The reason for leaving a job to the next session is
unchanged: both pay a climb of roughly fourteen
turns, but the fresh session keeps what it builds and spends the rest of its life
in it, where the subagent discards its context the moment it answers. That is a
reason not to delegate and not a licence to hand off early — the contract still
sends the session on until the how-full check says otherwise, because stopping at
130,000 costs the next one about 104,000 tokens of re-reading. Delegation is left
with one dependable case: material the session will never open itself.

## Waiting costs turns, and a turn costs the whole context

A session that waits by looking repeatedly pays a full turn per look. Measured in
one repo-a session: 8 calls of `sleep 300`, 9 agent-list polls, and 15 turns
whose entire output was a variant of `Waiting.` — 40 turns and 4,149,263 tokens,
35% of everything the session read, with single waiting turns costing as much as
156,555. repo-b waited on long runs in the same period but blocked once per
wait with a ten-minute timeout, spending 7 turns across a whole session and 0 in
two others. The contract now tells sessions to block rather than look again.

## Starting one

Do the first iteration by hand, always. It is the cheapest possible check
that the handoff is good enough to work from cold.

```bash
cd ~/projects/your-repo
# Write HANDOFF.md — use the clear-task skill at the end of a normal session.
claude -p "$(cat HANDOFF.md)" --output-format json | tee /tmp/first.json
```

Read the result. Did it commit? Did it rewrite the handoff? If yes to both,
the loop has something to stand on:

```bash
LOOP=~/.claude/skills/session-loop/scripts/run-loop.sh

"$LOOP" ~/projects/your-repo --dry-run                 # show the command, run nothing
"$LOOP" ~/projects/your-repo
```

There is no count to set — the run bounds itself. It ends when a session marks
the work `DONE`, hands off blocked, commits nothing because the work has run out,
does not finish, or fails. The hand-run above is the cheap check before you leave it alone; once a
few have landed cleanly, you can trust it to stop itself.

## Reading what it did

```bash
BUDGET=~/.claude/skills/session-loop/scripts/session_budget.py

git -C ~/projects/your-repo log --oneline -10
python3 "$BUDGET" ~/projects/your-repo --since 2026-08-09
ls ~/.claude/session-loop/your-repo/                   # one JSON summary per run
```

Three columns are worth checking after every run.

`ctx_end` is where each session actually stopped, and it is the one that says
whether the mechanism is working. It should land near the threshold. Well
under it means sessions are stopping early and paying the re-orientation cost
more often than they need to. Well over it means they are not checking.

`ctx_start` across iterations. Flat is healthy. Climbing means the handoff is
inflating, and each session is starting further up the curve than the last.

A row marked `<- cut off by the usage limit` ended because the limit hit, not
because the session decided it was full. Its `ctx_end` is where it happened to
be standing, not a handoff point, and the work it was mid-way through is
unfinished.

`fanout` is what the subagents read as a multiple of what the session read.
Should be `0.00x` for build work. Anything above zero means a session
delegated, and the question from the skill body applies: did the parent then
read the same material anyway?
