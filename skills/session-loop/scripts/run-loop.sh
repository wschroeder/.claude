#!/usr/bin/env bash
#
# Run a long build as a series of fresh Claude Code sessions.
#
# Each iteration starts a new `claude -p` process whose entire input is a
# handoff file, waits for it to exit, and then decides what to do next by
# looking at the repository — never at the transcript. That is what keeps the
# driver itself free of context: it holds nothing between iterations, so it
# never becomes the session it was meant to replace.
#
# A session works until its own context reaches the handoff threshold, not
# until it has done one thing. Re-orientation is the fixed cost of every fresh
# session, so a session that stops early pays it again for nothing.
#
# The loop stops when the session changed nothing, when the handoff says it is
# blocked, when a session does not finish, or when a session fails — never on a
# count. It runs until the work is done or a session needs a person.
#
# Usage:
#   run-loop.sh [REPO] [options]
#
#   --handoff FILE        handoff file, relative to REPO (default: HANDOFF.md)
#   --handoff-at N        context at which a session hands off (default: 225000)
#   --model NAME          model for each session (default: claude-opus-5)
#   --eval-model NAME     model for the reviewer that reads each session's diff
#                         (default: sonnet)
#   --no-eval             do not run the reviewer between sessions
#   --permission-mode M   bypassPermissions (default), acceptEdits, dontAsk, ...
#   --logs DIR            where to keep each run's JSON summary
#                         (default: ~/.claude/session-loop/REPO_NAME)
#   --dry-run             print the command each iteration would run, and stop
#
# The handoff file is not data. Every iteration feeds it to a session as that
# session's instructions, with no person in between, so anyone who can write to
# it decides what the loop does next. Run this only where write access to the
# repository already means trust, and read the warning under "Permissions" in
# references/driver-loop.md before choosing a permissive mode.

set -euo pipefail

REPO="."
HANDOFF="HANDOFF.md"
# Where a session hands off, in context tokens. Measured over 29 sessions, this
# number barely predicts what a turn of work costs (r = -0.07). What does predict
# it is how much a session reads before it first changes a file, which ranged
# from 60,016 to 187,085 across those same sessions. So treat this as a safety
# rail and not a cost knob, and note that lower is the dangerous direction — 4 of
# the 29 had not touched a file at all by 150,000. 225,000 sits just above the
# 195,813 median cost of getting one turn of work out of a fresh session instead,
# which is the point where handing off stops paying, and just below the 250,000
# where the operator measured answers starting to degrade as context fills.
# session_budget.py holds the same number and the measurements behind it.
HANDOFF_AT=225000
# The loop exists to commit unattended, and a headless session cannot answer a
# permission prompt — the prompt becomes a silent denial, HEAD never moves, and
# the run halts on "changed nothing." bypassPermissions is the one mode under
# which the session's own commit is not prompted. This is why the file is a
# program the loop runs, not a note it reads: see "Permissions" in the reference.
PERMISSION_MODE="bypassPermissions"
# Opus 5. The `opus` alias resolves to whatever the latest Opus is when it runs,
# which would change the driver under a long run, so the full id is pinned.
# Measured across 35 loop runs: Opus 5 and Opus 4.8 price within 2% per token, so
# there is nothing to save by running the older one. Override with --model.
MODEL="claude-opus-5"
# After each iteration a second session reads the diff the first one just made,
# with no memory of writing it and no tools to change it. The builder is the
# worst-placed reader of its own work, and it was reading it at the fullest and
# so most expensive part of its context.
#
# `sonnet` rather than the builder's model, because reviewing a stated diff
# against a stated intent is the repeated, well-scoped shape a cheaper model
# handles. Probed before this was written: an evaluator on sonnet found a
# planted off-by-one and a planted shell injection in a two-function diff, in 3
# turns for $0.28, against a builder session measured at $6 to $8. The alias is
# deliberate here where MODEL pins a full id — the evaluator is cheap enough to
# re-probe whenever it drifts, and its job is the one that benefits from newer.
EVAL_MODEL="sonnet"
EVAL=1
LOGS=""
DRY_RUN=0

BUDGET_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/session_budget.py"

die() { printf 'run-loop: %s\n' "$1" >&2; exit 1; }
say() { printf '\n=== %s\n' "$1"; }

# The header comment IS the help text. Reading it to the first line of code
# means the two cannot drift apart as the header grows.
usage() {
  awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "${BASH_SOURCE[0]}"
}

# An option whose value is missing takes the next option as its value and the
# loop goes quietly wrong, so every value-taking option checks first.
need_value() { [ "$#" -ge 2 ] && [ -n "$2" ] || die "$1 needs a value"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --handoff)          need_value "$@"; HANDOFF="$2"; shift 2 ;;
    --handoff-at)       need_value "$@"; HANDOFF_AT="$2"; shift 2 ;;
    --model)            need_value "$@"; MODEL="$2"; shift 2 ;;
    --eval-model)       need_value "$@"; EVAL_MODEL="$2"; shift 2 ;;
    --no-eval)          EVAL=0; shift ;;
    --permission-mode)  need_value "$@"; PERMISSION_MODE="$2"; shift 2 ;;
    --logs)             need_value "$@"; LOGS="$2"; shift 2 ;;
    --dry-run)          DRY_RUN=1; shift ;;
    -h|--help)          usage; exit 0 ;;
    -*)                 die "unknown option: $1" ;;
    *)                  REPO="$1"; shift ;;
  esac
done

# The threshold reaches a session as part of its instructions, so it is checked
# here rather than trusted there.
case "$HANDOFF_AT" in "" | *[!0-9]*) die "--handoff-at must be a whole number, got: $HANDOFF_AT" ;; esac
[ "$HANDOFF_AT" -ge 1 ] || die "--handoff-at must be at least 1"

# Both model names end up as arguments to `claude`, so they are checked at the
# door rather than trusted downstream. Without this, a name carrying a space
# smuggles a second flag onto that command line — "sonnet --dangerously-skip-
# permissions" is one word to the operator and two arguments to the shell.
# A model id is letters, digits, dots, dashes and underscores and nothing else.
for pair in "--model|$MODEL" "--eval-model|$EVAL_MODEL"; do
  case "${pair#*|}" in
    "" | *[!A-Za-z0-9._-]*)
      die "${pair%%|*} must be a model name, got: ${pair#*|}" ;;
  esac
done

command -v claude >/dev/null 2>&1 || die "claude is not on PATH"
[ -d "$REPO" ] || die "no such directory: $REPO"
REPO="$(cd "$REPO" && pwd)"
git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || die "not a git repository: $REPO"

HANDOFF_PATH="$REPO/$HANDOFF"
[ -s "$HANDOFF_PATH" ] || die "handoff file is missing or empty: $HANDOFF_PATH"

# Logs live outside the repository by default. The loop reads `git status` to
# decide whether the previous session finished cleanly, so anything it writes
# inside the working tree would read as unfinished work.
if [ -z "$LOGS" ]; then
  # A run summary carries the session's final message, and the directory names
  # say which repositories are being worked on. Both belong to their owner, the
  # way Claude Code already keeps ~/.claude/projects. A directory the caller
  # named is theirs, and its permissions stay as they set them.
  mkdir -p "$HOME/.claude/session-loop"
  chmod 700 "$HOME/.claude/session-loop"
  LOGS="$HOME/.claude/session-loop/$(basename "$REPO")"
  mkdir -p "$LOGS"
  chmod 700 "$LOGS"
else
  mkdir -p "$LOGS"
fi
LOGS="$(cd "$LOGS" && pwd)"
case "$LOGS" in
  "$REPO" | "$REPO"/*)
    git -C "$REPO" check-ignore -q "$LOGS" \
      || die "--logs is inside the repository and not gitignored: $LOGS
       The loop reads git status to tell finished work from half-applied work,
       and its own files would look like the latter. Move it out, or ignore it."
    ;;
esac

# The ceiling, enforced from outside the session rather than by the session
# remembering to ask about it.
#
# The contract below names three moments to check at: after each commit, before
# the reviews a piece of work owes, and after the probing that opens one. All
# three are milestones in the work cycle, so a session that spends its whole life
# on one piece of work reaches them once, at the end. Measured across the last
# run of two repositories: every worker committed exactly once, between turn 27
# and turn 86, and the single check it ran landed a turn or two later at 145,000
# to 204,000 context — after which 29% of one run's tokens went on turns already
# past the line.
#
# A PostToolUse hook fires on every tool call and is handed the path to the
# session's own transcript, so the number gets read whether or not the session
# thought to read it. PostToolUse and not PreToolUse: a PreToolUse hook exiting 2
# denies the call, which would refuse a session over the line the very Bash calls
# it needs to commit and write its handoff.
#
# Written here rather than into the repository, because a settings file in the
# working tree is dirt, and the loop refuses to start a session on a dirty tree.
#
# Built by python3 rather than a heredoc because two layers of quoting have to be
# right and a heredoc gets neither. The script path is embedded in JSON, so it
# needs JSON escaping; Claude Code then runs the resulting "command" string
# through a shell, so it needs shell quoting as well. Probed: `--settings` at a
# malformed file prints no warning and runs the session anyway, so getting this
# wrong would not stop the loop or announce itself — it would quietly stop
# enforcing the ceiling, which looks exactly like enforcing it.
HOOK_SETTINGS="$LOGS/hook-settings.json"
BUDGET_SCRIPT="$BUDGET_SCRIPT" HANDOFF_AT="$HANDOFF_AT" python3 - > "$HOOK_SETTINGS" <<'SETTINGS' \
  || die "could not write the handoff hook settings: $HOOK_SETTINGS"
import json, os, shlex
command = "python3 %s --hook --handoff-at %s" % (
    shlex.quote(os.environ["BUDGET_SCRIPT"]), os.environ["HANDOFF_AT"])
print(json.dumps({"hooks": {"PostToolUse": [
    {"matcher": "*", "hooks": [{"type": "command", "command": command}]}]}}, indent=2))
SETTINGS
chmod 600 "$HOOK_SETTINGS"

# The contract every session runs under. Appended to the handoff so the
# handoff itself stays a plain continuation prompt a human can also paste.
protocol() {
  cat <<PROTOCOL

---

You are one iteration of an unattended loop. Seven rules govern how you work.

Load the skill the work matches before you start the work, not after. Code or a
comment in any language loads writing-code; the test that opens a piece of work
loads tdd-cycle; the reviews load quick-review and security-review; the commit
message loads git-commit. The handoff you were handed may name skills of its
own, and that list is not the whole of it: it was written by a session that
named the skills it happened to load, so a skill missing from it is not a skill
the work does not need. Measured on the run that prompted this line: a session
loaded three skills, every one of them named by its handoff and none of them
writing-code, which the handoff did not name; of the thirteen lines it added to
the code, ten were comment.

Commit as you go and leave the tree clean. Committing here is already
authorized: the operator started this loop knowing that it commits. That
authority covers amending too — a commit you made in this session, and the
unfinished commit an earlier session left for you to carry on from, because that
commit is a note about where the work got to and you are the one continuing it.
A commit that finished its piece of work is settled: build on top of it rather
than rewriting it. There is nobody present to ask, so finish the commit rather
than stopping to ask.

Pushing is not part of this. Do not push, do not ask whether to push, and do not
look for a remote to work out whether pushing would matter. That is settled
outside the loop, so there is nothing to decide and nothing to report about it
either way — commit, and carry on as though the subject had not come up.

Ask how full you are at three points: after each commit, before you start the
reviews a piece of work owes, and after the probing that opens one.

    python3 $BUDGET_SCRIPT --self --handoff-at $HANDOFF_AT

Skip the check below about a hundred thousand context. Asking is itself a whole
turn at whatever your context already is, and down there the answer cannot be
anything but keep going.

It prints your context so far and one of two verdicts. On "keep going", carry on
here: you have already paid to load this context, and a fresh session would
spend about a hundred thousand tokens re-reading its way back to where you
already are.

On "hand off", stop where you are. You do not have to finish the piece of work
first — inside this loop a commit records where you got to, and does not have to
mean the work is finished and reviewed. Commit what you have with a subject that
says it is unfinished, then rewrite $HANDOFF as the continuation prompt for the
next fresh session: the same thing you would write for a person picking this up
cold, and on top of that, exactly where in the cycle you stopped and what the
piece of work still owes — the test that is written and failing, the reviews not
yet run, what the probe showed. The next session amends that commit or builds on
it.

Stopping just before the reviews is a good place to stop rather than a lapse.
Review turns cost the most where the context is fullest, and the session that
wrote the code is the worst-placed one to read it back: a fresh session reads the
diff for what it says instead of for what it was meant to say.

This rule holds inside the loop and nowhere else. Outside it, a piece of work is
finished and reviewed before it is committed, and nothing here changes that.

Run the reviews a piece of work owes yourself rather than handing them to a
subagent. You will read every finding one returns and act on it, so the diff
arrives in this context anyway and the subagent's reading of it is paid for
twice. In the run that prompted this line, eight review subagents read more than
the session that spawned them, and the session hit the usage limit before it
could commit.

The same test settles anything else you might delegate: if you will open what the
subagent opened, keep the work here. Below about a hundred thousand context, keep
it here whatever the job, unless the subagent would be reading something you were
never going to read yourself — a subagent opens near 21,700 and climbs for
fourteen turns before it can say anything useful, so short of that your own turns
are the cheaper ones and no job is big enough to change it. Above it a long job
can earn the climb back, but only once you are close to the handoff line, and
even there the answer is not a subagent: carry on here until the check tells you
to hand off, and let the next session take the job. It pays the same climb and
keeps what it builds, where a subagent pays it and throws it away the moment it
answers you.

When something has to finish before you can go on — a build, a test run, a
command you sent to the background — wait for it in one call that blocks until it
is done. Do not sleep and look again, and do not ask repeatedly whether it has
finished. Every look costs a whole turn, and a turn re-reads everything you have
read so far: one session spent forty turns and four million tokens doing nothing
but checking, which was a third of everything it read that session.

That one call has to run in the foreground of this turn. Do not put the job in
the background and end your turn to wait for a notification. This session is a
single prompt with no turn after this one, so ending your turn ends the
session, and the commit or the review that job was gating never happens.
Measured on 2026-08-19: a session extracted a function, armed its mutation run
in the background, ended the turn to wait, and stopped there with the work
uncommitted and its handoff unwritten, which halted the run on a dirty tree at
the next iteration.

You are on the driver model. When you hand a piece of work to a subagent, match
the model to the task: Haiku for wide or mechanical passes where only the answer
matters, Sonnet for work that needs judgment you will not re-read yourself, and
the driver model for the reasoning you keep in this session. If the choice
between two models is close, pick the more capable one — a wrong result is
re-done at full price, so saving tokens on a close call buys nothing.

If you cannot proceed without a decision only the operator can make, commit what
you have the same way — unfinished, and saying so — then make the first line of
$HANDOFF read "BLOCKED: " followed by one sentence naming the decision, leave the
rest of the file as it is, and stop. The loop will halt and wait for a person.
Commit first or your question is never read: the driver only looks at the first
line of $HANDOFF at the start of an iteration, so a session that raises one
without committing is caught by the did-anything-change test first, and the run
stops saying the session changed nothing rather than saying what you asked.

Which piece of work comes next is not a decision like that. Take the one that
unblocks the most of what is left, and where nothing waits on anything else,
take any of them and say in $HANDOFF which you took. Nobody is holding a
preference between them, and a run stopped on that question sits idle until
someone happens to look.

If instead you have finished everything the handoff asks for and there is no
next piece of work left, make the first line of $HANDOFF read "DONE" — on its
own or followed by one sentence — and stop. The loop will halt and report the
work complete, rather than reading a finished project as a session that failed
to commit.

You are already inside the loop, so do not start another one: do not invoke the
session-loop skill and do not run run-loop.sh.
PROTOCOL
}

# What the evaluator is asked. It gets no handoff and no protocol: it is not
# continuing the work, it is reading one diff cold. Naming the shapes worth
# reporting keeps it off style and off work the commit already says is
# unfinished on purpose, which is most of what an unaimed reviewer returns.
eval_prompt() {
  cat <<EVALPROMPT
You are reading the commits in the range $1 of the repository you are standing
in. You did not write them, and you have no tools to change anything: report
what you find, do not fix it.

Start with \`git diff $1\` and read whatever surrounding code you need to judge
what you see there.

Report only what you can point at a file and line for:
- the code does not do what its own name, docstring or comment says it does
- a caller of something that changed would now get back something it does not
  expect
- a value that nothing checked reaches a shell, a query, or a file path
- a test whose assertion is weaker than the behaviour its name claims

For each finding, name what executes that code and when it last ran — the
caller, the recipe, the test, the request path. If you cannot find anything
that reaches it, say so on that finding's line. You are not judging whether the
finding is worth fixing; you are handing over the fact that decides it.

Do not report style, naming preferences, formatting, or work that the commit
message itself says is unfinished on purpose.

Answer with PASS alone on the first line if you found nothing worth fixing.
Otherwise put FAIL alone on the first line, then one line per finding, each
beginning with the file and line it is about.
EVALPROMPT
}

say "repo $REPO"
printf 'handoff   %s\n' "$HANDOFF_PATH"
printf 'logs      %s\n' "$LOGS"
printf 'sessions  until the work is done or one needs you, each handing off at %s context\n' "$HANDOFF_AT"

# No iteration cap: the loop runs until a session hands off blocked, commits
# nothing, does not finish, or fails — the real conditions, not a count. Every
# way out is an explicit exit inside the loop, so there is nothing after it.
# What the last iteration's evaluator found, waiting to go in front of the next
# session's handoff. It rides in the prompt rather than in a file in the repo:
# writing it into the tree would leave it dirty, and the dirty-tree gate below
# would then halt the run on the evidence the loop had just produced.
PENDING_FINDINGS=""
# The path behind that text, so an iteration records which review it worked
# from rather than leaving it to be inferred from filenames afterwards.
FINDINGS_IN=""
# How many times a session may declare the work finished over a reviewer that
# disagrees before the run stops and asks for a person. Two, because one
# re-send covers the ordinary case — the reviewer caught something real on the
# last commit and the next session fixes it — and a second disagreement after
# that is the two of them not converging, which spending more will not settle.
MAX_DONE_OVERRIDES=2
DONE_OVERRIDES=0
# MAX_DONE_OVERRIDES for the case where nobody claims to be finished. Three,
# because two findings running on one file is a fix that needed a second pass
# and a third is the two of them circling it. Measured on the run that prompted
# it: three iterations and about ten million weighted tokens went into the
# failure semantics of a one-shot script whose job had finished two iterations
# earlier, and every finding along the way was correct.
MAX_SAME_FILE_FINDINGS=3
LATCHED_PATHS=""
LATCH_COUNT=0
i=0
while :; do
  i=$((i + 1))
  say "iteration $i"

  # Checked every iteration, not once before the first. Each session rewrites
  # this file, and the handoff is gitignored, so a session that empties or
  # deletes it leaves no trace in `git status` — the next session would be
  # handed the protocol and no work at all, and the run would look healthy.
  # The first iteration is already covered before any directory is created,
  # which is why this message can assume a session has run.
  [ -s "$HANDOFF_PATH" ] || die "handoff file is missing or empty: $HANDOFF_PATH
       The last session was supposed to rewrite it and left nothing behind."

  if head -n 1 "$HANDOFF_PATH" | grep -q '^BLOCKED:'; then
    printf 'stopping: the handoff is blocked.\n  %s\n' "$(head -n 1 "$HANDOFF_PATH")"
    exit 0
  fi

  # A finished project is a clean stop, not a failure. Without this a session
  # that has done everything changes nothing, and the tree-moved check below
  # would halt the run as if it had stalled. DONE says the work is complete;
  # the token must stand alone so a handoff that merely mentions the word in
  # prose does not end the run.
  # DONE is the one claim in this loop that a session makes about its own work
  # and nothing checks. It is also the claim that lands at the exact moment the
  # reviewer's findings are about a commit nobody will read again: the session
  # declares the work complete, the reviewer reads that last commit, finds
  # something, and the run exits reporting success with the findings sitting
  # unread in the logs directory. So DONE ends the run only when nothing is
  # outstanding; otherwise it goes back for another session, which is the whole
  # point of having a reader that is not the writer.
  if head -n 1 "$HANDOFF_PATH" | grep -qE '^DONE([[:space:]:]|$)'; then
    if [ -z "$PENDING_FINDINGS" ]; then
      printf 'stopping: the handoff says the work is complete.\n  %s\n' "$(head -n 1 "$HANDOFF_PATH")"
      exit 0
    fi
    # A session that keeps declaring victory against a reviewer that keeps
    # disagreeing is a standoff, and an unbounded loop settles it by spending
    # until the account runs out.
    if [ "$DONE_OVERRIDES" -ge "$MAX_DONE_OVERRIDES" ]; then
      printf 'stopping: the work has said it is finished %s times running and the reviewer\n' \
        "$((DONE_OVERRIDES + 1))"
      printf 'still disagrees. This needs a person: read the findings in %s and\n' "$LOGS"
      printf 'decide which of them is right.\n'
      exit 1
    fi
    DONE_OVERRIDES=$((DONE_OVERRIDES + 1))
    printf '  the handoff says the work is complete, but the reviewer found something in\n'
    printf '  the last commit. Sending it back rather than stopping (%s of %s).\n' \
      "$DONE_OVERRIDES" "$MAX_DONE_OVERRIDES"
  fi

  # After BLOCKED and DONE on purpose: those are statements a session made
  # about its own work, and they outrank a count read off the reviewer.
  if [ "$LATCH_COUNT" -ge "$MAX_SAME_FILE_FINDINGS" ]; then
    printf 'stopping: the last %s reviews all found something in %s.\n' \
      "$LATCH_COUNT" "$LATCHED_PATHS"
    printf 'the reviewer and the sessions are circling one file rather than settling it,\n'
    printf 'and each finding it returns becomes the next session\047s first job. This needs a\n'
    printf 'person: read the findings in %s and decide whether that file still matters.\n' "$LOGS"
    exit 1
  fi

  DIRTY="$(git -C "$REPO" status --porcelain)"
  if [ -n "$DIRTY" ]; then
    printf 'stopping: the working tree is dirty, so the last session did not finish cleanly.\n'
    printf '%s\n' "$DIRTY"
    exit 1
  fi

  HEAD_BEFORE="$(git -C "$REPO" rev-parse HEAD)"
  # What proves a session did something is the code, not the commit id. A session
  # may amend the unfinished commit its predecessor left, and an amend that
  # touches no file still yields a new commit id as soon as it lands a second
  # later than the commit it replaces — measured. Comparing ids would read that
  # rewrite as progress and start another session on the same code, forever.
  TREE_BEFORE="$(git -C "$REPO" rev-parse 'HEAD^{tree}')"

  set -- -p "$PENDING_FINDINGS$(cat "$HANDOFF_PATH")$(protocol)"
  set -- "$@" --output-format json
  set -- "$@" --permission-mode "$PERMISSION_MODE"
  # Additional settings, not a replacement: whatever the operator already has in
  # ~/.claude/settings.json still applies, and this adds the handoff hook on top.
  set -- "$@" --settings "$HOOK_SETTINGS"
  [ -n "$MODEL" ] && set -- "$@" --model "$MODEL"

  if [ "$DRY_RUN" -eq 1 ]; then
    printf 'would run: claude -p <%s bytes of handoff> %s\n' \
      "$(wc -c < "$HANDOFF_PATH" | tr -d ' ')" \
      "--output-format json --permission-mode $PERMISSION_MODE --settings $HOOK_SETTINGS${MODEL:+ --model $MODEL}"
    exit 0
  fi

  RUN_STAMP="$(date -u +%Y%m%dT%H%M%S)"
  RUN_LOG="$LOGS/run-$RUN_STAMP-$i.json"
  STATUS=0
  ( cd "$REPO" && claude "$@" ) > "$RUN_LOG" || STATUS=$?

  if [ "$STATUS" -ne 0 ]; then
    printf 'stopping: claude exited %s. See %s\n' "$STATUS" "$RUN_LOG"
    exit "$STATUS"
  fi

  # claude exits 0 even when it stopped early, so the shell's exit code alone
  # cannot tell a finished session from a cut one. The summary says which.
  SUMMARY_STATUS=0
  python3 - "$RUN_LOG" <<'SUMMARY' || SUMMARY_STATUS=$?
import json, sys

DID_NOT_FINISH = 3
REPORTED_ERROR = 4

try:
    with open(sys.argv[1]) as fh:
        result = json.load(fh)
except Exception as exc:
    print("  (could not read the run summary: %s)" % exc)
    sys.exit(0)

reason = result.get("terminal_reason", "?")
print("  turns %s, %s" % (result.get("num_turns", "?"), reason))

# A denied tool does not stop a headless session, it just does not happen. A
# session that could not run the build still finishes, and says it is done.
denials = result.get("permission_denials") or []
if denials:
    print("  %d tool call(s) were denied, so this session worked without them:"
          % len(denials))
    for name in sorted({d.get("tool_name", "?") for d in denials}):
        print("    %s x%d" % (name, sum(1 for d in denials if d.get("tool_name") == name)))

# Anything other than a clean finish means the session stopped where it did not
# choose to. Naming the reason rather than listing the ones known today means a
# reason this script has never seen still halts the loop.
if reason not in ("?", "completed"):
    sys.exit(DID_NOT_FINISH)
if result.get("is_error"):
    sys.exit(REPORTED_ERROR)
SUMMARY

  case "$SUMMARY_STATUS" in
    0) ;;
    3) printf 'stopping: the session did not finish — see the reason above.\n'
       printf 'look at what it left behind before running another.\n'
       exit 1 ;;
    4) printf 'stopping: the session reported an error. See %s\n' "$RUN_LOG"
       exit 1 ;;
    *) printf 'stopping: could not tell how the session ended. See %s\n' "$RUN_LOG"
       exit 1 ;;
  esac

  TREE_AFTER="$(git -C "$REPO" rev-parse 'HEAD^{tree}')"
  if [ "$TREE_BEFORE" = "$TREE_AFTER" ]; then
    printf 'stopping: the session changed nothing, so the next one would start from the same place.\n'
    LEFTOVER="$(git -C "$REPO" status --porcelain)"
    if [ -n "$LEFTOVER" ]; then
      printf 'it also left work uncommitted, which needs a person before anything else runs:\n%s\n' "$LEFTOVER"
    fi
    exit 1
  fi
  # "now at" rather than "committed": a session that amended the unfinished
  # commit it was handed did not add one, and the count is of commits that are
  # not in what it started from, which is right either way.
  HEAD_AFTER="$(git -C "$REPO" rev-parse HEAD)"
  COMMITS="$(git -C "$REPO" rev-list --count "$HEAD_BEFORE".."$HEAD_AFTER")"
  printf '  now at %s (%s new since the session started)\n' \
    "$(git -C "$REPO" log --oneline -1)" "$COMMITS commit(s)"

  # The ids rather than the clock: an amend leaves the commit it replaced
  # unreachable, so reading `git log` by time credits the work to whichever
  # session amended it. Measured on a repo-b run whose pre-amend commit
  # is reachable from no branch.
  ITER_HEAD_BEFORE="$HEAD_BEFORE" ITER_HEAD_AFTER="$HEAD_AFTER" \
  ITER_COMMITS="$COMMITS" ITER_FINDINGS_IN="$FINDINGS_IN" \
    python3 - > "$LOGS/iter-$RUN_STAMP-$i.json" <<'RECORD' \
      || die "could not write the iteration record for iteration $i"
import json, os, sys

json.dump({
    "head_before": os.environ["ITER_HEAD_BEFORE"],
    "head_after": os.environ["ITER_HEAD_AFTER"],
    "commits": int(os.environ["ITER_COMMITS"]),
    "findings_in": os.path.basename(os.environ["ITER_FINDINGS_IN"]) or None,
}, sys.stdout, indent=2)
sys.stdout.write("\n")
RECORD

  # A second reader, on the diff that session just made. It runs here rather
  # than inside the session for two reasons that point the same way: a session
  # reads its own diff for what it meant to write, and it would be reading at
  # the fullest and most expensive part of its context.
  #
  # It does NOT inherit $PERMISSION_MODE. The builder needs bypassPermissions to
  # commit unattended, and denying Edit and Write under that mode still leaves
  # Bash, which is a whole shell. dontAsk with an explicit read-only allowlist is
  # the mode that matches what a reader needs — probed both ways: under it the
  # evaluator still reached its verdict in 2 turns with no denials, and an
  # instruction to `rm` a file in the repository was denied, file left in place.
  PENDING_FINDINGS=""
  FINDINGS_IN=""
  if [ "$EVAL" -eq 1 ]; then
    # stdin is closed explicitly. Measured without it: "no stdin data received
    # in 3s, proceeding without it" on every iteration — three seconds of stall
    # each time, and a hang rather than a stall if the driver's own stdin is a
    # pipe that nobody closes.
    EVAL_LOG="$LOGS/eval-$(date -u +%Y%m%dT%H%M%S)-$i.json"
    EVAL_STATUS=0
    (
      cd "$REPO" && claude \
        -p "$(eval_prompt "$HEAD_BEFORE..HEAD")" \
        --output-format json \
        --permission-mode dontAsk \
        --allowed-tools "Bash(git :*)" Read Grep Glob \
        --disallowed-tools Edit Write NotebookEdit \
        --model "$EVAL_MODEL" \
        < /dev/null
    ) > "$EVAL_LOG" || EVAL_STATUS=$?

    # A reviewer that fell over is not a reason to stop building. Say so and
    # carry on: the alternative is that one flaky read halts a run that is
    # otherwise healthy, and the commits it would have read are still in git
    # for the next one to reach.
    if [ "$EVAL_STATUS" -ne 0 ]; then
      printf '  the reviewer exited %s, so this iteration went unread. See %s\n' \
        "$EVAL_STATUS" "$EVAL_LOG"
    else
      FINDINGS_FILE="$LOGS/findings-$(date -u +%Y%m%dT%H%M%S)-$i.md"
      # The verdict comes back on stdout and the findings go to a file python
      # opens itself. Splitting them across stdout and stderr instead would put
      # a redirect after a heredoc terminator, which is a shape that parses but
      # does not do what it reads like — measured: the file was written and the
      # findings never reached the next prompt.
      VERDICT="$(python3 - "$EVAL_LOG" "$FINDINGS_FILE" <<'VERDICT'
import json, sys

try:
    with open(sys.argv[1]) as fh:
        text = (json.load(fh).get("result") or "").strip()
except Exception:
    print("UNREADABLE")
    sys.exit(0)

# The contract asks for PASS or FAIL alone on the first line, and a model that
# writes one sentence of preamble first still answered — measured: a real run
# returned "No callers exist yet. I can reason about the slice arithmetic
# directly without needing to execute it." and then FAIL and its findings.
# Requiring line one would have thrown that away, so the verdict is the first
# line that is exactly PASS or FAIL and the findings are what follows it.
# Matching a bare line rather than a substring keeps a finding that discusses a
# failing test from being read as the verdict.
verdict, body = "UNCLEAR", text
lines = text.split("\n")
for n, line in enumerate(lines):
    if line.strip() in ("PASS", "FAIL"):
        verdict = line.strip()
        body = "\n".join(lines[n + 1:]).strip()
        break

if verdict == "PASS":
    print("PASS")
    sys.exit(0)
with open(sys.argv[2], "w") as fh:
    fh.write(body + "\n")
print(verdict)
VERDICT
)"

      case "$VERDICT" in
        PASS)
          LATCHED_PATHS=""
          LATCH_COUNT=0
          printf '  the reviewer read it and found nothing\n' ;;
        FAIL|UNCLEAR)
          if [ "$VERDICT" = UNCLEAR ]; then
            printf '  the reviewer did not answer PASS or FAIL; passing on what it said. See %s\n' \
              "$FINDINGS_FILE"
          else
            printf '  the reviewer found something. See %s\n' "$FINDINGS_FILE"
          fi
          # The contract asks each finding to begin with the file and line it
          # is about; one that does not is not counted rather than guessed at.
          # Python holds the comparison as well as the parsing, so what a model
          # wrote before a colon never reaches the shell as a word: split
          # unquoted, a finding path carrying a `*` would be expanded against
          # whatever directory the loop is standing in. Measured before this
          # was written: the count reset every round and the run never stopped.
          LATCH_STATE="$(python3 - "$FINDINGS_FILE" "$LATCHED_PATHS" "$LATCH_COUNT" <<'LATCH'
import re, sys

named = []
for line in open(sys.argv[1]):
    found = re.match(r"\s*(?:[-*]\s*)?(\S+?):", line)
    if found and found.group(1) not in named:
        named.append(found.group(1))

held, count = sys.argv[2].split(), int(sys.argv[3])
still = [path for path in held if path in named] if count else []
if still:
    count += 1
elif named:
    still, count = named, 1
else:
    still, count = [], 0
print(count, " ".join(still))
LATCH
)"
          LATCH_COUNT="${LATCH_STATE%% *}"
          LATCHED_PATHS="${LATCH_STATE#* }"

          FINDINGS_IN="$FINDINGS_FILE"
          # In front of the handoff, not after it: this is about the commit that
          # is already in, and it is the first thing the next session should do.
          PENDING_FINDINGS="A second session read the diff you were handed and
found the following in it. These are about the commit that is already in, not
about new work. Deal with them first, then carry on with the handoff below.

Each one is a proposal, not an order. It was written by a reader that got the
diff and nothing else, so it cannot tell whether the code it names still
matters. Check what executes that code. If nothing reaches it any more — a
one-shot tool whose job is finished, a branch no caller takes, a guarantee the
repository already makes — write the finding into the handoff with one line
saying why you are leaving it, and carry on with the work. That is not DONE and
it is not a blocked handoff.

$(cat "$FINDINGS_FILE")

--- end of what the reviewer found; your handoff follows ---

" ;;
        *)
          printf '  could not read the reviewer verdict. See %s\n' "$EVAL_LOG" ;;
      esac
    fi
  fi
done
