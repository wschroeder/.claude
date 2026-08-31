#!/usr/bin/env bash
#
# Exercises run-loop.sh against a stub `claude`, so the loop's decisions are
# tested without spending anything. The stub imitates the two things the
# driver actually reads back: the JSON summary on stdout, and what the
# session did to the repository.
#
# There is no iteration cap, so every scenario has to reach a real stop
# condition on its own — a session that blocks, empties the handoff, commits
# nothing, or fails. A stub that just kept committing would loop forever, which
# is the whole point: nothing arbitrary bounds the run.
#
# Run: bash test_run_loop.sh

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOOP="$HERE/run-loop.sh"
PASS=0
FAIL=0

check() {
  local name="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf 'ok   %s\n' "$name"; PASS=$((PASS + 1))
  else
    printf 'FAIL %s (expected %s, got %s)\n' "$name" "$expected" "$actual"; FAIL=$((FAIL + 1))
  fi
}

# A repo with one commit, a handoff, and a stub claude on PATH whose behavior
# for the run is set by STUB_MODE.
new_fixture() {
  ROOT="$(mktemp -d)"
  REPO="$ROOT/repo"
  mkdir -p "$REPO" "$ROOT/bin"
  git -C "$REPO" init -q
  git -C "$REPO" config user.email test@example.com
  git -C "$REPO" config user.name Test
  echo "start" > "$REPO/file.txt"
  echo "Continue the work." > "$REPO/HANDOFF.md"
  # Gitignored, the way the skill requires: the loop rewrites this file every
  # iteration, and a tracked one would make every finished session look like
  # unfinished work. Tracking it here would also let the dirty-tree check stand
  # in for guards that have to hold on their own in real use.
  echo "/HANDOFF.md" > "$REPO/.gitignore"
  git -C "$REPO" add -A
  git -C "$REPO" commit -qm "initial"

  cat > "$ROOT/bin/claude" <<'STUB'
#!/usr/bin/env bash
# Stub Claude. Reads STUB_MODE; imitates a session's effect on the repo and
# prints the JSON summary the real `claude -p --output-format json` prints.
# Keeps the prompt it was handed, so the contract with the child session can
# be asserted rather than assumed.
# The evaluator is a second call against the same binary, and the flag that
# makes it a reader is what tells the two apart. It has to be handled before
# the builder branches below, because those commit, and an evaluator that
# committed would make every gate the loop has meaningless.
case " $* " in
  *" --disallowed-tools "*)
    printf '%s\n' "$2" > "$STUB_EVAL_PROMPT_FILE"
    printf '%s\n' "$*" > "$STUB_EVAL_ARGV_FILE"
    n=$(( $(cat "$STUB_EVAL_COUNT_FILE" 2>/dev/null || echo 0) + 1 ))
    echo "$n" > "$STUB_EVAL_COUNT_FILE"
    # STUB_VERDICT_FIRST lets a run go FAIL then PASS, which is the only way to
    # see whether findings are cleared once they stop being found.
    if [ -n "${STUB_VERDICT_FIRST:-}" ] && [ "$n" -eq 1 ]; then
      V="$STUB_VERDICT_FIRST"
    else
      V="${STUB_VERDICT:-PASS}"
    fi
    python3 -c 'import json,sys;print(json.dumps({"is_error":False,"num_turns":3,"terminal_reason":"completed","total_cost_usd":0.28,"result":sys.argv[1]}))' "$V"
    exit 0 ;;
esac

printf '%s\n' "$2" > "$STUB_PROMPT_FILE"
printf '%s\n' "$*" > "$STUB_ARGV_FILE"
case "${STUB_MODE:-commit}" in
  commit)
    echo "$RANDOM" >> file.txt
    echo "Continue the work, again." > HANDOFF.md
    git add -A && git commit -qm "stub: did a unit of work"
    ;;
  runs)
    # Several real units of work, then a question. Used to show the loop runs
    # session after session with nothing capping it, stopping only when a
    # session writes BLOCKED. STUB_RUNS says which unit finally raises it, so a
    # value past the old five-iteration default proves no count bounds the run.
    n=$(( $(cat "$STUB_COUNT_FILE" 2>/dev/null || echo 0) + 1 ))
    echo "$n" > "$STUB_COUNT_FILE"
    echo "$RANDOM" >> file.txt
    if [ "$n" -ge "${STUB_RUNS:-3}" ]; then
      printf 'BLOCKED: the operator has to pick a colour.\nrest of handoff\n' > HANDOFF.md
    else
      echo "Continue the work, again." > HANDOFF.md
    fi
    git add -A && git commit -qm "stub: unit $n"
    ;;
  blocked)
    # Commits real work, then blocks — a session that got somewhere before it
    # hit the question. The handoff is gitignored, so it commits a file too.
    echo "$RANDOM" >> file.txt
    printf 'BLOCKED: the operator has to pick a colour.\nrest of handoff\n' > HANDOFF.md
    git add -A && git commit -qm "stub: blocked"
    ;;
  amendwork)
    # Finishes the unfinished commit it was handed rather than adding one: the
    # shape that makes HEAD_BEFORE unreachable, and the reason the record names
    # a range instead of leaving the commits to be found by their timestamps.
    echo "$RANDOM" >> file.txt
    printf 'BLOCKED: the amend landed.\nrest of handoff\n' > HANDOFF.md
    git add -A
    GIT_COMMITTER_DATE="2026-08-16T12:05:00" git commit -q --amend --no-edit
    ;;
  done)
    # Finishes the work: commits, then writes DONE on the first line. On a later
    # call — reached only by code that does not yet recognise DONE — it commits
    # nothing, so such a run halts on "changed nothing" rather than spinning,
    # and the test fails cleanly instead of hanging.
    if head -n1 HANDOFF.md | grep -q '^DONE'; then
      :
    else
      echo "$RANDOM" >> file.txt
      printf 'DONE\nnothing left to do\n' > HANDOFF.md
      git add -A && git commit -qm "stub: finished the work"
    fi
    ;;
  donethenfix)
    # Declares the work finished, then — if it is asked again — commits a fix and
    # declares it finished a second time. This is the shape a run takes when the
    # reviewer catches something on the very last commit.
    n=$(( $(cat "$STUB_COUNT_FILE" 2>/dev/null || echo 0) + 1 ))
    echo "$n" > "$STUB_COUNT_FILE"
    echo "$RANDOM" >> file.txt
    printf 'DONE\nnothing left to do\n' > HANDOFF.md
    git add -A && git commit -qm "stub: call $n, says it is finished"
    ;;
  alwaysdone)
    # Says it is finished every single time, however often it is sent back. The
    # bound on re-sends is the only thing that ends a run like this.
    echo "$RANDOM" >> file.txt
    printf 'DONE\nnothing left to do\n' > HANDOFF.md
    git add -A && git commit -qm "stub: insists it is finished"
    ;;
  nothing) : ;;
  amendonly)
    # Rewrites the last commit without changing one byte of the code, every time
    # it is called. Sessions may now amend the unfinished commit an earlier one
    # left, so this is a shape the loop can really produce: a session that picked
    # the work up, got nowhere, and re-committed it. Each call moves the committer
    # date on, because git reuses the identical commit object when an amend lands
    # inside the same second — measured — and this has to be the case where HEAD
    # really does move, or it proves nothing about watching the tree instead.
    # The BLOCKED escape is only so a driver that never notices terminates the
    # test rather than hanging; reaching it at all is the failure.
    n=$(( $(cat "$STUB_COUNT_FILE" 2>/dev/null || echo 0) + 1 ))
    echo "$n" > "$STUB_COUNT_FILE"
    if [ "$n" -ge 4 ]; then
      printf 'BLOCKED: the driver never noticed.\nrest of handoff\n' > HANDOFF.md
    else
      GIT_COMMITTER_DATE="2026-08-16T12:0$n:00" git commit -q --amend --no-edit
    fi
    ;;
  blockeddirty)
    # Raises a question without committing the work it was in the middle of —
    # what a session does if it takes "stop where you are" to mean stopping
    # without a commit. The question goes in the handoff, the work stays in the
    # tree.
    echo "half-written" >> file.txt
    printf 'BLOCKED: the operator has to pick a colour.\nrest of handoff\n' > HANDOFF.md
    ;;
  dirty)   echo "half-applied" >> file.txt ;;
  crash)   exit 3 ;;
  denied)
    echo "$RANDOM" >> file.txt
    git add -A && git commit -qm "stub: worked with tools denied"
    # Then block, so the uncapped loop stops once the denials have been surfaced
    # rather than committing forever.
    printf 'BLOCKED: nothing more to decide.\nrest of handoff\n' > HANDOFF.md
    printf '{"is_error":false,"num_turns":7,"terminal_reason":"completed","total_cost_usd":1.25,"permission_denials":[{"tool_name":"Bash"},{"tool_name":"Bash"},{"tool_name":"Write"}]}\n'
    exit 0
    ;;
  cutoff)
    # What a run that stopped part way looks like: work committed, the session
    # cut off, and the process still exits 0.
    echo "$RANDOM" >> file.txt
    git add -A && git commit -qm "stub: cut off part way"
    printf '{"is_error":false,"num_turns":3,"terminal_reason":"max_turns","total_cost_usd":9.0,"result":null}\n'
    exit 0
    ;;
  errored)
    echo "$RANDOM" >> file.txt
    git add -A && git commit -qm "stub: errored"
    printf '{"is_error":true,"num_turns":4,"terminal_reason":"completed","total_cost_usd":2.0}\n'
    exit 0
    ;;
  garbage)
    echo "$RANDOM" >> file.txt
    # Then block, so an unreadable summary does not stop the loop on its own but
    # the uncapped run still comes to rest.
    printf 'BLOCKED: nothing more to decide.\nrest of handoff\n' > HANDOFF.md
    git add -A && git commit -qm "stub: unreadable summary"
    printf 'this is not json\n'
    exit 0
    ;;
  emptyhandoff)
    # Commits, then leaves the next session nothing to work from.
    echo "$RANDOM" >> file.txt
    git add -A && git commit -qm "stub: committed then emptied the handoff"
    : > HANDOFF.md
    printf '{"is_error":false,"num_turns":5,"terminal_reason":"completed"}\n'
    exit 0
    ;;
esac
printf '{"is_error":false,"num_turns":7,"terminal_reason":"completed","total_cost_usd":1.25}\n'
STUB
  chmod +x "$ROOT/bin/claude"
  export PATH="$ROOT/bin:$PATH"
  export STUB_PROMPT_FILE="$ROOT/last-prompt.txt"
  export STUB_ARGV_FILE="$ROOT/last-argv.txt"
  export STUB_COUNT_FILE="$ROOT/stub-count.txt"
  export STUB_EVAL_PROMPT_FILE="$ROOT/last-eval-prompt.txt"
  export STUB_EVAL_ARGV_FILE="$ROOT/last-eval-argv.txt"
  export STUB_EVAL_COUNT_FILE="$ROOT/eval-count.txt"
}

drop_fixture() { rm -rf "$ROOT"; }

run_loop() { ( cd "$REPO" && "$LOOP" "$REPO" "$@" ) > "$ROOT/out.txt" 2>&1; echo $?; }

# --- with no cap, the loop runs session after session and stops only on a real
#     exit condition, not on a count. Six units is past the old five-iteration
#     default, so a run that reaches the sixth proves nothing arbitrary bounded
#     it — the only thing that ends it is a session finally needing a person. ---
new_fixture
export STUB_MODE=runs
export STUB_RUNS=6
status="$(run_loop)"
check "an uncapped run exits 0 when a session finally blocks" 0 "$status"
check "every unit ran — six, past the old five-iteration default" 7 "$(git -C "$REPO" rev-list --count HEAD)"
grep -q "the handoff is blocked" "$ROOT/out.txt"
check "it stopped because a session needed the operator, not a counter" 0 $?
unset STUB_RUNS
drop_fixture

# --- a blocked handoff halts the NEXT iteration, not the current one ---
new_fixture
export STUB_MODE=blocked
status="$(run_loop)"
check "blocked handoff exits 0" 0 "$status"
check "blocked handoff stops after one session" 2 "$(git -C "$REPO" rev-list --count HEAD)"
grep -q "the handoff is blocked" "$ROOT/out.txt"
check "blocked reason is reported" 0 $?
drop_fixture

# --- a session that finishes everything writes DONE on the first line, and the
#     loop stops with success — not by treating a finished project as a session
#     that failed to commit ---
new_fixture
export STUB_MODE=done
status="$(run_loop)"
check "a DONE handoff stops the loop with success" 0 "$status"
grep -q "the work is complete" "$ROOT/out.txt"
check "the completion is reported" 0 $?
case "$(cat "$ROOT/out.txt")" in *"changed nothing"*) ok=1 ;; *) ok=0 ;; esac
check "a finished project is not reported as a failure to commit" 0 "$ok"
check "the finished work is kept" 2 "$(git -C "$REPO" rev-list --count HEAD)"
drop_fixture

# --- a session that commits nothing must not be run again ---
new_fixture
export STUB_MODE=nothing
status="$(run_loop)"
check "no-progress session exits 1" 1 "$status"
grep -q "changed nothing" "$ROOT/out.txt"
check "no-progress reason is reported" 0 $?
drop_fixture

# --- a session that rewrites the last commit without changing the code must not
#     be run again either. A session may now amend the unfinished commit its
#     predecessor left, so HEAD moving no longer proves that anything happened:
#     measured, an amend that touches no file still produces a new commit id as
#     soon as it lands in a later second than the commit it replaces. The tree
#     hash is what distinguishes work from a rewrite, so that is what the driver
#     compares.
new_fixture
export STUB_MODE=amendonly
status="$(run_loop)"
check "a session that amended without changing the code exits 1" 1 "$status"
grep -q "changed nothing" "$ROOT/out.txt"
check "the no-progress reason is reported for an amend that changed no code" 0 $?
# The one that bites. Watching HEAD, the driver reads each rewrite as progress
# and launches another session, so it takes a second iteration to notice — and
# only because this stub happens to repeat itself. Watching the tree, it stops
# on the first.
case "$(cat "$ROOT/out.txt")" in *"iteration 2"*) ok=1 ;; *) ok=0 ;; esac
check "the rewrite is caught on the first iteration, not the second" 0 "$ok"
drop_fixture

# --- a question raised without committing the work is never read, which is why
#     the contract tells a blocked session to commit first. The driver reads the
#     first line of the handoff at the start of an iteration, so a BLOCKED line
#     written during one is not seen until the next — and the did-anything-change
#     test gets there first. Pinned because the contract now makes this promise
#     to every session, and it holds only while the checks stay in this order. ---
new_fixture
export STUB_MODE=blockeddirty
status="$(run_loop)"
check "blocking without committing exits 1, not 0" 1 "$status"
grep -q "pick a colour" "$ROOT/out.txt"
check "the operator's question is never printed" 1 $?
grep -q "changed nothing" "$ROOT/out.txt"
check "what is reported instead is a session that changed nothing" 0 $?
drop_fixture

# --- work left half-applied stops the loop before it starts another session ---
new_fixture
export STUB_MODE=dirty
status="$(run_loop)"
check "dirty tree exits 1" 1 "$status"
grep -q "left work uncommitted" "$ROOT/out.txt"
check "dirty tree reason is reported" 0 $?
drop_fixture

# --- denied tools are surfaced; a session that could not run its build still
#     reports success, so the count is the only way anyone finds out ---
new_fixture
export STUB_MODE=denied
status="$(run_loop)"
check "a session with denied tools still counts as progress" 0 "$status"
grep -q "3 tool call(s) were denied" "$ROOT/out.txt"
check "the denial count is reported" 0 $?
grep -q "Bash x2" "$ROOT/out.txt"
check "denials are broken down by tool" 0 $?
drop_fixture

# --- a session that did not finish stops the loop even though it committed
#     and even though claude exited 0 ---
new_fixture
export STUB_MODE=cutoff
status="$(run_loop)"
check "a session that did not finish stops the loop" 1 "$status"
check "it does not start another session" 2 "$(git -C "$REPO" rev-list --count HEAD)"
grep -q "did not finish" "$ROOT/out.txt"
check "the cutoff is reported" 0 $?
grep -q "max_turns" "$ROOT/out.txt"
check "the reason it stopped is named" 0 $?
drop_fixture

# --- a session that empties or mangles the handoff stops the loop, rather than
#     handing the next one no task at all ---
new_fixture
export STUB_MODE=emptyhandoff
status="$(run_loop)"
check "an emptied handoff stops the loop" 1 "$status"
check "the next session never started" 2 "$(git -C "$REPO" rev-list --count HEAD)"
grep -q "handoff file is missing or empty" "$ROOT/out.txt"
check "the emptied handoff is reported" 0 $?
drop_fixture

# --- a session that reports an error stops the loop ---
new_fixture
export STUB_MODE=errored
status="$(run_loop)"
check "an errored session stops the loop" 1 "$status"
grep -q "reported an error" "$ROOT/out.txt"
check "the error is reported" 0 $?
drop_fixture

# --- an unreadable summary is not treated as success ---
new_fixture
export STUB_MODE=garbage
status="$(run_loop)"
check "an unreadable summary does not stop the loop on its own" 0 "$status"
grep -q "could not read the run summary" "$ROOT/out.txt"
check "the unreadable summary is reported" 0 $?
drop_fixture

# --- a crashed session propagates its exit code ---
new_fixture
export STUB_MODE=crash
status="$(run_loop)"
check "crashed session propagates exit code" 3 "$status"
drop_fixture

# --- a dirty tree at the very start is refused before any session runs ---
new_fixture
echo "uncommitted" >> "$REPO/file.txt"
export STUB_MODE=commit
status="$(run_loop)"
check "pre-existing dirt is refused" 1 "$status"
check "nothing was committed" 1 "$(git -C "$REPO" rev-list --count HEAD)"
drop_fixture

# --- the help text carries every option, however long the header grows ---
HELP="$("$LOOP" --help)"
for opt in --handoff --handoff-at --model --eval-model --no-eval --permission-mode --logs --dry-run; do
  case "$HELP" in *"$opt"*) ok=0 ;; *) ok=1 ;; esac
  check "help documents $opt" 0 "$ok"
done
# The count is gone, so the help must not still offer it.
case "$HELP" in *--iterations*) ok=1 ;; *) ok=0 ;; esac
check "help no longer documents the removed --iterations flag" 0 "$ok"

# --- what the child session is actually handed: the handoff, then the contract ---
new_fixture
export STUB_MODE=blocked
printf 'DO THE NEXT THING.\n' > "$REPO/HANDOFF.md"
git -C "$REPO" add -A && git -C "$REPO" commit -qm "handoff"
status="$(run_loop)"
check "one session ran and then blocked" 0 "$status"
# Flattened, so an assertion is about what the contract says rather than about
# where the paragraph happened to wrap.
PROMPT="$(tr '\n' ' ' < "$ROOT/last-prompt.txt" | tr -s ' ')"
for phrase in "DO THE NEXT THING." "rewrite HANDOFF.md" "BLOCKED: " "DONE" "do not invoke the" \
              "session_budget.py" "--self" "hand off" "keep going"; do
  case "$PROMPT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the child session is told: $phrase" 0 "$ok"
done
# The skill body says not to delegate work whose result you will read yourself,
# but the worker never sees the skill body — it is handed the handoff and this
# contract, nothing else. So the rule has to be in here, and it has to name the
# reviews, because that is the work sessions actually delegated. Measured on
# 2026-08-16: the three repo-a sessions that handed their reviews to subagents
# spent $51.30 and left one commit unfinished, and in the last of them eight
# review subagents read 13,383,442 tokens against the session's own 11,782,397 —
# more reading in the subagents than in the session that then read every finding
# they returned. Over the same day repo-b spawned no subagent at all, cost
# $56.25 across eight iterations, and finished.
# The capital R is load-bearing: it pins the sentence as an instruction, so
# softening it to "prefer to run the reviews yourself" breaks this rather than
# sliding through on the tail of the sentence still matching.
for phrase in "Run the reviews a piece of work owes yourself rather than handing them to a subagent" \
              "read every finding" "keep the work here"; do
  case "$PROMPT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the contract tells the session: $phrase" 0 "$ok"
done
# "will I open what it opened" tells a session what NOT to delegate but leaves it
# guessing about the rest. Fitting the eight measured review subagents gives the
# missing half: they open at 21,735 on average and grow 3,981 a turn, taking a
# median fourteen turns to reach four fifths of their peak. Running that curve
# against a session's own — 2,108 a turn while working — delegating loses at
# every job size until the session is past about 100,000 context, and only wins
# between there and the handoff line, which is where handing off wins instead.
# The two numbers are the whole heuristic, so they are asserted inside their
# sentences rather than alongside them. Asserting "keep it here whatever the job"
# on its own let the floor be edited from a hundred thousand to ten thousand with
# the suite still green, which is how this comment came to exist.
#
# The floor carries an exception and must keep carrying it. It was fitted from
# subagents re-reading a diff the parent already held, where the climb is pure
# duplication. Material neither of them has read yet is the opposite case: read
# inline it lands in the session's context and is re-sent every turn afterwards,
# which is the one thing a subagent genuinely saves. A floor stated without the
# exception forbids the only delegation that was ever worth making.
# And it must not pre-empt the how-full check. Telling a session at 130,000 that
# handing off beats delegating reads as "hand off now", which is the early stop
# the whole threshold exists to prevent — a fresh session pays about 104,000 to
# get back to where this one already is. The rule defers to the check instead.
for phrase in "Below about a hundred thousand context, keep it here whatever the job" \
              "never going to read yourself" \
              "until the check tells you to hand off" \
              "opens near 21,700 and climbs for fourteen turns" \
              "keeps what it builds"; do
  case "$PROMPT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the contract tells the session: $phrase" 0 "$ok"
done
# A turn re-sends the whole context, so a turn spent asking "is it done yet?"
# costs exactly what a turn spent working costs. Measured on 2026-08-16 in
# one repo-a session: forty turns and 4,149,263 tokens went on sleeping, polling,
# and writing the word "Waiting" — 35% of everything that session read. repo-b
# waited too, but blocked once per wait instead of looking repeatedly, and spent
# seven turns on it across a whole session.
# The wait also has to be in the foreground. A session that backgrounds the job
# and ends its turn to await a notification is waiting in a way that only works
# where something will send one: under claude -p the turn boundary is the end of
# the session. Measured on 2026-08-19 in repo-b: a session extracted a
# function, armed its mutation run in the background, ended the turn to wait,
# and died there with the work uncommitted and its handoff unwritten, which
# halted the run on a dirty tree at the next iteration.
for phrase in "wait for it in one call that blocks" "Do not sleep and look again" \
              "Every look costs a whole turn" "in the foreground of this turn" \
              "ending your turn ends the session"; do
  case "$PROMPT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the contract tells the session: $phrase" 0 "$ok"
done
# Asking how full you are is itself a full-context turn. Six checks per session
# was the repo-a habit, one of them at 43,254 context where the answer cannot
# be anything but "keep going". No check below 102,349 in any measured session
# returned "hand off", so below roughly a hundred thousand the turn is wasted.
case "$PROMPT" in *"Skip the check below about a hundred thousand"*) ok=0 ;; *) ok=1 ;; esac
check "the contract puts a floor under the how-full check" 0 "$ok"
# The opening line promises a count, so a rule added below has to be counted
# here too or the session is told to expect fewer than it gets.
case "$PROMPT" in *"Seven rules govern how you work"*) ok=0 ;; *) ok=1 ;; esac
check "the contract counts its own rules correctly" 0 "$ok"
# A handoff names the skills the session that wrote it happened to load, so the
# list propagates by imitation and a skill that did not exist when the phrasing
# was written never joins it. writing-code never reached a repo-a session that
# way; the contract names the skills here, where no session can drop one. Each
# phrase carries the verb, because the paragraph also names writing-code while
# recounting the run that went without it — matching the bare name passes on the
# anecdote alone, with the instruction deleted.
for phrase in "loads writing-code" "loads tdd-cycle" \
              "load quick-review and security-review" "loads git-commit"; do
  case "$PROMPT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the contract tells the session what loads: $phrase" 0 "$ok"
done
# The session runs on the driver model, but it chooses the model for anything it
# delegates, and that choice is the one lever that changes what a fixed usage
# allowance buys: a Haiku token and a driver-model token are not billed alike.
# The contract therefore names which work goes where, and closes the tie in
# favour of the better model — a wrong answer is re-done at full price, so
# saving tokens on a close call is a false economy.
for phrase in "match the model to the task" "Haiku" "Sonnet" "pick the more capable one"; do
  case "$PROMPT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the contract tells the session: $phrase" 0 "$ok"
done
# The worker decides when to stop from its own context, so the contract must
# not also tell it to stop after one unit — that is what cut sessions off at
# 80,000 having done a single thing.
case "$PROMPT" in *"Do not start another unit of work"*) ok=1 ;; *) ok=0 ;; esac
check "the contract no longer caps a session at one unit of work" 0 "$ok"

# Nobody is present to approve anything, so a session that treats committing as
# needing a person's say-so does the entire unit of work and then stops one
# command short. Measured across two repositories: 19 of 48 loop sessions
# committed nothing, and three of those had finished the work, the tests and
# both reviews first. The contract therefore grants that authority up front,
# and bounds it — commits and amends here, nothing that leaves the machine.
# The amend is bounded by what the commit means, not by which session made it.
# A session may rewrite an unfinished commit, including one an earlier session
# left for it, because that commit is a note about where the work got to and the
# session picking it up is the one continuing it. A commit that finished its
# piece of work is settled and gets built on instead. The driver no longer needs
# the amend bounded for its own sake: it compares tree hashes, so a rewrite that
# changes no code cannot pass for progress.
#
# The push clauses are about turns, not permissions. A bare "do not push" leaves
# the subject open, and a session that has just committed then asks whether to
# push, or checks for a remote, finds none, and writes a paragraph explaining why
# no push was needed. Both cost the operator something: the first stops an
# unattended run dead, the second burns turns on a non-question. So the contract
# has to close the topic, which means naming the asking and the checking too.
for phrase in "already authorized" "amend" "Do not push" \
              "the unfinished commit an earlier session left" \
              "finished its piece of work is settled" \
              "do not ask whether to push" "do not look for a remote"; do
  case "$PROMPT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the contract tells the session: $phrase" 0 "$ok"
done

# Where the session is allowed to stop is the whole reason a repo-a session ran
# to 280,910 context while the ceiling said 170,000. Measured over four sessions
# there: the first commit landed at 182,032, 268,636 and 271,695, so the only
# checkpoint the contract offered — after a commit — could not fire until the
# session was already up to 100,000 tokens past the line, and the verdict it then
# printed was correct and useless. The contract therefore asks at three points
# rather than one, and lets the session stop at any of them by committing what it
# has unfinished. The three points are where the measurements put them: after a
# commit, before the reviews (which cost 34,514 to 77,358 of context growth, and
# in repo-a began at 191,278 to 212,848), and after the probing that opens a
# piece of work.
for phrase in "before you start the reviews" "after the probing" \
              "stop where you are" "do not have to finish the piece of work" \
              "says it is unfinished" "where in the cycle you stopped" \
              "holds inside the loop and nowhere else"; do
  case "$PROMPT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the contract tells the session: $phrase" 0 "$ok"
done
# Stopping part way through a piece of work is now the normal thing to do, which
# makes it the normal state to be in when a question comes up as well. A session
# that writes BLOCKED over uncommitted work halts the run on the dirty tree
# instead — a worse message, and the operator's question never gets printed. So
# the blocked path has to say to commit first, exactly like the handoff path.
case "$PROMPT" in *"commit what you have the same way"*) ok=0 ;; *) ok=1 ;; esac
check "the contract tells a blocked session to commit what it has first" 0 "$ok"
# BLOCKED halts the whole run until a person happens to look, so what counts as
# a question for the operator has to be drawn narrowly or the escape becomes the
# expensive default. A session that had room to keep working stopped the run to
# ask which of the remaining steps to do next — a choice the operator had no
# preference about, bought at the price of every hour until they read it. The
# ordering rule has to be in the contract rather than the skill body, because a
# worker is handed the handoff and this contract and never sees that file.
#
# Both halves are asserted. "Take the one that unblocks the most" on its own
# leaves a session with independent steps still able to read the silence as
# grounds to ask, which is the exact case the operator said they do not care
# about; and the instruction to say which one it took is what stops the next
# session repeating the same piece of work.
for phrase in "Which piece of work comes next is not a decision like that" \
              "unblocks the most of what is left" \
              "take any of them and say"; do
  case "$PROMPT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the contract tells the session: $phrase" 0 "$ok"
done

ARGV="$(cat "$ROOT/last-argv.txt")"
for flag in "--output-format json" "--permission-mode"; do
  case "$ARGV" in *"$flag"*) ok=0 ;; *) ok=1 ;; esac
  check "the child session is launched with $flag" 0 "$ok"
done
# The loop's whole job is to commit unattended, and a headless session cannot
# answer a permission prompt: the prompt becomes a silent denial, HEAD never
# moves, and the run halts on "changed nothing." Probed on this operator's
# setup — the permissions hook allows `git status` and `mix test` but passes
# `git commit` through to a prompt — so the driver runs bypassPermissions, the
# one mode under which the session's own commit is not prompted.
case "$ARGV" in *"--permission-mode bypassPermissions"*) ok=0 ;; *) ok=1 ;; esac
check "the child session runs under bypassPermissions, so its commit is not prompted" 0 "$ok"
# Opus 5 specifically. The `opus` alias resolves to whatever the latest Opus is
# at the time it runs, which silently changes the driver under a long run, so the
# full model id is pinned rather than the alias. Measured across 35 loop runs:
# Opus 5 and Opus 4.8 price within 2% of each other per token, so the driver
# takes the more capable of the two rather than the older one.
case "$ARGV" in *"--model claude-opus-5"*) ok=0 ;; *) ok=1 ;; esac
check "the child session runs on Opus 5" 0 "$ok"
case "$ARGV" in *--max-budget-usd*) ok=1 ;; *) ok=0 ;; esac
check "the child session is launched with no dollar cap" 0 "$ok"
case "$(cat "$ROOT/out.txt")" in *'$'*) ok=1 ;; *) ok=0 ;; esac
check "the driver reports no dollar figure" 0 "$ok"
drop_fixture

# --- the ceiling is enforced from outside the session, by a hook ---
#
# Measured across the last run of repo-a and of repo-b: every worker committed
# exactly once, between turn 27 and turn 86, and the single budget check it ran
# landed a turn or two later at 145,000 to 204,000 context. 29% of repo-a's run
# went on turns already past the line. The three moments the contract names to
# check at are all milestones in the work cycle, so a session that spends its
# life on one piece of work reaches them once, at the end.
#
# A PostToolUse hook fires on every tool call instead, and is handed the path to
# the session's own transcript, so the number gets read whether or not the
# session thought to read it. Probed on this machine: hooks do fire in headless
# `claude -p` runs, plain hook stdout never reaches the model, and exit 2 with a
# line on stderr arrives as a blocking error the session cannot skim past.
new_fixture
export STUB_MODE=blocked
status="$(run_loop --logs "$ROOT/logs")"
check "a run with the hook wired up still completes" 0 "$status"
ARGV="$(cat "$ROOT/last-argv.txt")"
case "$ARGV" in *"--settings "*) ok=0 ;; *) ok=1 ;; esac
check "the child session is launched with --settings" 0 "$ok"

SETTINGS="$(printf '%s\n' "$ARGV" | sed -n 's/.*--settings \([^ ][^ ]*\).*/\1/p')"
check "a settings path was parsed out of the invocation" 0 \
  "$([ -n "$SETTINGS" ] && echo 0 || echo 1)"
check "the settings file the driver named exists" 0 \
  "$([ -f "$SETTINGS" ] && echo 0 || echo 1)"
# Outside the repository. A settings file written into the working tree is dirt,
# and the driver refuses to start a session on a dirty tree — wiring the hook up
# that way would stop the loop on its own first iteration. Mutation-checked: this
# has to fail on an EMPTY path too, or a run that never launched a session at all
# satisfies it by having nothing to place, and the assertion reads green on the
# exact breakage it exists to catch.
case "${SETTINGS:-$REPO/unset}" in "$REPO"/*) ok=1 ;; *) ok=0 ;; esac
check "the settings file lives outside the repository" 0 "$ok"
python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SETTINGS" 2>/dev/null
check "the settings file is valid JSON" 0 "$?"

SETTINGS_TEXT="$(tr '\n' ' ' < "$SETTINGS" | tr -s ' ')"
LOOP_HANDOFF_AT="$(awk -F= '/^HANDOFF_AT=/ { print $2; exit }' "$LOOP")"
# The absolute path, because the hook runs with the repository as its working
# directory and would never find a relative one.
for phrase in "PostToolUse" "$HERE/session_budget.py" "--hook" \
              "--handoff-at $LOOP_HANDOFF_AT"; do
  case "$SETTINGS_TEXT" in *"$phrase"*) ok=0 ;; *) ok=1 ;; esac
  check "the hook settings carry $phrase" 0 "$ok"
done
# PostToolUse and not PreToolUse. A PreToolUse hook exiting 2 denies the tool
# call, so a session over the line would be refused the very Bash calls it needs
# to commit and write the handoff — it would be trapped rather than retired.
# PostToolUse lets the call through and tells the session afterwards.
case "$SETTINGS_TEXT" in *PreToolUse*) ok=1 ;; *) ok=0 ;; esac
check "the driver registers no PreToolUse hook, which would deny the commit" 0 "$ok"
# The threshold the hook enforces is the one the contract quotes. Two numbers
# that drift apart would tell a worker one ceiling and hold it to another.
PROMPT="$(tr '\n' ' ' < "$ROOT/last-prompt.txt" | tr -s ' ')"
case "$PROMPT" in *"--handoff-at $LOOP_HANDOFF_AT"*) ok=0 ;; *) ok=1 ;; esac
check "the contract quotes the same threshold the hook enforces" 0 "$ok"
drop_fixture

# --- the hook survives an awkward path, because a broken one fails silently ---
#
# Probed: `claude -p --settings <malformed json>` prints no warning and runs the
# session anyway. So a settings file the driver mangles does not stop the loop or
# announce itself — it just quietly stops enforcing the ceiling, which is
# indistinguishable from working. Two layers have to be right for that not to
# happen. The path is embedded in JSON, so it needs JSON escaping; and Claude Code
# runs the resulting "command" string through a shell, so it needs shell quoting
# too. A directory name with a space and a quote in it exercises both at once.
new_fixture
ODD="$ROOT/od d\"ir"
mkdir -p "$ODD"
cp "$HERE/run-loop.sh" "$HERE/session_budget.py" "$ODD/"
export STUB_MODE=blocked
( cd "$REPO" && bash "$ODD/run-loop.sh" "$REPO" --logs "$ROOT/logs2" ) > "$ROOT/odd.txt" 2>&1
check "the driver runs from a path with a space and a quote in it" 0 "$?"
ODD_SETTINGS="$ROOT/logs2/hook-settings.json"
python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$ODD_SETTINGS" 2>/dev/null
check "the settings file is still valid JSON from an awkward path" 0 "$?"
# Round-trip rather than a substring match: the point is that what a shell will
# actually execute names the real script, not that the raw bytes look plausible.
python3 - "$ODD_SETTINGS" "$ODD/session_budget.py" <<'ODDCHECK'
import json, shlex, sys
cmd = json.load(open(sys.argv[1]))["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
sys.exit(0 if shlex.split(cmd)[1] == sys.argv[2] else 1)
ODDCHECK
check "the command in it resolves to the real script path once a shell splits it" 0 "$?"
drop_fixture

# --- the threshold the worker is told to use is the one the script defaults to ---
DEFAULT_HANDOFF_AT="$(awk -F= '/^HANDOFF_AT=/ { print $2; exit }' "$LOOP")"
check "the default threshold is readable from the script" 0 \
  "$([ -n "$DEFAULT_HANDOFF_AT" ] && echo 0 || echo 1)"
# The number itself is the operator's call, so it is pinned here rather than
# derived from a curve. It is worth knowing how little it decides: measured over
# 29 sessions, cost per turn of actual work barely moves with where the session
# stopped (r = -0.07), while it does track how much the session read before its
# first file change (r = +0.62, and that ranged from 60,016 to 187,085). This is
# a safety rail. Lower is the dangerous direction — 4 of those 29 had changed
# nothing at all by 150,000 context, so a ceiling there would have retired them
# before they did any work.
#
# 225,000 is where the operator put it. The break-even is measurable: a turn taken
# in the session you already have costs exactly its own context, and a turn of
# work from a fresh one costs a median 195,813 with its whole re-orientation
# charged to it. So a ceiling a little above that median buys margin against the
# quarter of sessions whose re-orientation runs to 251,450, and the accuracy
# ceiling is at 250,000, so it fits underneath.
check "the default threshold is the operator's 225,000" 225000 "$DEFAULT_HANDOFF_AT"
check "the help text quotes the real default" "$DEFAULT_HANDOFF_AT" \
  "$(grep -- '--handoff-at' "$LOOP" | grep -oE 'default: [0-9]+' | head -1 | awk '{ print $2 }')"
check "the script agrees with session_budget.py" "$DEFAULT_HANDOFF_AT" \
  "$(awk -F'= *' '/^DEFAULT_HANDOFF_AT/ { gsub(/_/, "", $2); print $2; exit }' "$HERE/session_budget.py")"

# The model default gets the same treatment as the threshold. Without this the
# help text is prose nobody checks, and an operator reading `--model NAME
# (default: ...)` would be told the wrong model the first time the pinned id
# moves — the same drift the threshold check above exists to catch.
DEFAULT_MODEL="$(awk -F'"' '/^MODEL="/ { print $2; exit }' "$LOOP")"
check "the default model is readable from the script" 0 \
  "$([ -n "$DEFAULT_MODEL" ] && echo 0 || echo 1)"
check "the help text quotes the real default model" "$DEFAULT_MODEL" \
  "$(grep -- '--model NAME' "$LOOP" | grep -oE 'default: [^)]+' | head -1 | sed 's/default: //')"

# --- money is gone from the skill, not merely unused ---
# A flag with a value after it is a flag being passed. A bare mention is prose,
# and the reference deliberately names --max-budget-usd to say why it is not
# used — deleting that explanation is how the flag comes back. Test files are
# excluded for the same reason: naming a flag is how they guard against it.
MONEY="$(grep -rlE -- '--(max-)?budget-usd[ =]*[0-9$"]|--ceiling-usd[ =]*[0-9$"]|--rates[ =]|BUDGET_USD|CEILING_USD' \
         "$HERE/.." 2>/dev/null | grep -v '/test_' | tr '\n' ' ' | sed 's/ $//')"
check "no file still carries a money flag" "" "$MONEY"

# --- guards that stop the loop before it can spend anything ---
new_fixture
status="$( ( "$LOOP" "$ROOT" ) >/dev/null 2>&1; echo $? )"
check "a non-repo directory is refused" 1 "$status"
rm "$REPO/HANDOFF.md"
status="$(run_loop)"
check "a missing handoff is refused" 1 "$status"
drop_fixture

# --- values that are not values are refused before any session runs ---
new_fixture
export STUB_MODE=commit
status="$(run_loop --handoff-at "0') or __import__('os').system('touch $ROOT/PWNED') or float('0")"
check "a threshold that is not a number is refused" 1 "$status"
check "nothing was executed through the threshold" 1 "$([ -e "$ROOT/PWNED" ] && echo 0 || echo 1)"
check "no session ran" 1 "$(git -C "$REPO" rev-list --count HEAD)"
status="$(run_loop --handoff-at "; rm -rf /")"
check "a threshold that is a shell fragment is refused" 1 "$status"
status="$(run_loop --handoff-at)"
check "an option with no value is refused" 1 "$status"
# The count is gone and the money flags never existed: none may be quietly
# accepted and ignored. Each must be refused as an unknown option.
for gone in --budget-usd --ceiling-usd --iterations; do
  status="$(run_loop "$gone" 100)"
  check "$gone is refused rather than ignored" 1 "$status"
done
drop_fixture

# --- a logs directory inside the repo would read as unfinished work ---
new_fixture
export STUB_MODE=blocked
status="$(run_loop --logs "$REPO")"
check "logs in the repo root are refused" 1 "$status"
status="$(run_loop --logs "$REPO/logs")"
check "logs in a repo subdirectory are refused" 1 "$status"
printf 'logs/\n' > "$REPO/.gitignore"
git -C "$REPO" add -A && git -C "$REPO" commit -qm "ignore logs"
status="$(run_loop --logs "$REPO/logs")"
check "logs in an ignored subdirectory are allowed" 0 "$status"
drop_fixture

# --- the default logs directory is private; a named one is left alone ---
new_fixture
export STUB_MODE=blocked
export HOME="$ROOT/home"
status="$(run_loop)"
check "the default logs directory works" 0 "$status"
check "the default logs directory is owner-only" 700 \
  "$(stat -c '%a' "$ROOT/home/.claude/session-loop/repo" 2>/dev/null || stat -f '%Lp' "$ROOT/home/.claude/session-loop/repo")"
check "its parent is owner-only too" 700 \
  "$(stat -c '%a' "$ROOT/home/.claude/session-loop" 2>/dev/null || stat -f '%Lp' "$ROOT/home/.claude/session-loop")"
drop_fixture

new_fixture
export STUB_MODE=blocked
mkdir -p "$ROOT/mylogs"; chmod 755 "$ROOT/mylogs"
status="$(run_loop --logs "$ROOT/mylogs")"
check "a named logs directory still works" 0 "$status"
check "a named logs directory keeps its permissions" 755 "$(stat -c '%a' "$ROOT/mylogs" 2>/dev/null || stat -f '%Lp' "$ROOT/mylogs")"
check "a run summary was written there" 1 "$(ls "$ROOT/mylogs"/run-*.json 2>/dev/null | wc -l | tr -d ' ')"
drop_fixture

# --- dry run shows the command and spends nothing ---
new_fixture
export STUB_MODE=commit
status="$(run_loop --dry-run)"
check "dry run exits 0" 0 "$status"
check "dry run commits nothing" 1 "$(git -C "$REPO" rev-list --count HEAD)"
drop_fixture

# --- a second session reads the diff, with no memory of writing it and no tools
#     to change it ---
#
# The builder grading its own work is the failure this closes, and it was
# costing twice over: the review ran in the session that wrote the code, at the
# fullest and therefore most expensive part of its context. Probed before this
# was built — an evaluator on sonnet found a planted off-by-one and a planted
# shell injection in a two-function diff, in 3 turns for $0.28, against a
# builder session measured at $6 to $8. The same probe confirmed the lockout is
# real: asked directly to edit the file, it reported "Edit is disabled for this
# session, in subagents as well as here" and the file was untouched.
new_fixture
export STUB_MODE=blocked
status="$(run_loop)"
check "the loop still exits cleanly with an evaluator in it" 0 "$status"
check "the evaluator ran once for the one iteration" 1 "$(cat "$STUB_EVAL_COUNT_FILE" 2>/dev/null || echo 0)"
EVAL_ARGV="$(cat "$STUB_EVAL_ARGV_FILE" 2>/dev/null || echo "")"
case "$EVAL_ARGV" in *"--disallowed-tools Edit Write NotebookEdit"*) ok=0 ;; *) ok=1 ;; esac
check "the evaluator is denied every tool that could change the tree" 0 "$ok"
case "$EVAL_ARGV" in *"--model sonnet"*) ok=0 ;; *) ok=1 ;; esac
check "the evaluator runs on the cheap model by default" 0 "$ok"
case "$EVAL_ARGV" in *"--output-format json"*) ok=0 ;; *) ok=1 ;; esac
check "the evaluator's verdict is read as json, not scraped from prose" 0 "$ok"
# The handoff hook belongs to a builder. An evaluator that hit a context ceiling
# would be told to commit and rewrite the handoff, which is exactly what it has
# no tools to do, so it would spend turns failing instead of answering.
case "$EVAL_ARGV" in *"--settings"*) ok=1 ;; *) ok=0 ;; esac
check "the evaluator does not get the builder's handoff hook" 0 "$ok"
# Denying Edit and Write under bypassPermissions still leaves Bash, which is a
# whole shell. Probed: under dontAsk with the read-only allowlist the evaluator
# reached its verdict in 2 turns with no denials, and an instruction to remove a
# file in the repository was denied with the file left in place.
case "$EVAL_ARGV" in *"--permission-mode dontAsk"*) ok=0 ;; *) ok=1 ;; esac
check "the evaluator does not inherit the builder's permission mode" 0 "$ok"
case "$EVAL_ARGV" in *"--allowed-tools Bash(git :*) Read Grep Glob"*) ok=0 ;; *) ok=1 ;; esac
check "the evaluator's shell is scoped to reading git" 0 "$ok"
EVAL_PROMPT="$(tr '\n' ' ' < "$STUB_EVAL_PROMPT_FILE" | tr -s ' ')"
case "$EVAL_PROMPT" in *"PASS"*) ok=0 ;; *) ok=1 ;; esac
check "the evaluator is told what a clean verdict looks like" 0 "$ok"
case "$EVAL_PROMPT" in *"git diff"*) ok=0 ;; *) ok=1 ;; esac
check "the evaluator is told how to reach the diff" 0 "$ok"
drop_fixture

# --- what the evaluator found reaches the session that can act on it ---
#
# A verdict nobody reads is worth nothing. On FAIL the findings go in front of
# the next builder's handoff, rather than into a file in the repository: writing
# them into the tree would leave it dirty, and the driver's own dirty-tree gate
# would then halt the run on the evidence it just produced.
new_fixture
export STUB_MODE=runs
export STUB_RUNS=3
export STUB_VERDICT="FAIL
- file.txt:1 — the widget count is off by one"
# A logs directory inside the fixture, not the shared default: the default is
# not cleaned between fixtures, so a findings file left by an earlier scenario
# would make this pass whether or not this run wrote one.
mkdir -p "$ROOT/logs"
status="$(run_loop --logs "$ROOT/logs")"
check "a failing verdict does not by itself stop the run" 0 "$status"
NEXT_PROMPT="$(tr '\n' ' ' < "$STUB_PROMPT_FILE" | tr -s ' ')"
case "$NEXT_PROMPT" in *"the widget count is off by one"*) ok=0 ;; *) ok=1 ;; esac
check "the next session is handed what the evaluator found" 0 "$ok"
case "$NEXT_PROMPT" in *"Continue the work"*) ok=0 ;; *) ok=1 ;; esac
check "the handoff still reaches it too" 0 "$ok"
check "the findings are kept where the operator can read them" 1 \
  "$([ -n "$(ls "$ROOT/logs"/findings-*.md 2>/dev/null)" ] && echo 1 || echo 0)"
drop_fixture

# --- a clean verdict adds nothing to the next prompt ---
new_fixture
export STUB_MODE=runs
export STUB_RUNS=3
export STUB_VERDICT="PASS"
status="$(run_loop)"
check "a clean run still finishes" 0 "$status"
NEXT_PROMPT="$(cat "$STUB_PROMPT_FILE")"
case "$NEXT_PROMPT" in *"found the following"*) ok=1 ;; *) ok=0 ;; esac
check "a passing verdict puts no findings block in the next prompt" 0 "$ok"
drop_fixture

# --- a reviewer that clears its throat first has still answered ---
#
# Measured in a real run: the evaluator wrote "No callers exist yet. I can reason
# about the slice arithmetic directly without needing to execute it." and then
# FAIL and its finding. Reading only the first line called that unclear and
# handed the next session the preamble as though it were a finding.
new_fixture
export STUB_MODE=blocked
# The preamble names a verdict word on purpose. Scanning for PASS or FAIL as a
# substring rather than as the whole line reads this first sentence as the
# answer, and the run then has a verdict it cannot act on at all.
export STUB_VERDICT="I checked whether the existing tests PASS, and they do.

FAIL
- util.py:3 — take() returns size + 1 items, not size"
mkdir -p "$ROOT/logs"
status="$(run_loop --logs "$ROOT/logs")"
check "a verdict behind a preamble still runs cleanly" 0 "$status"
FOUND="$(cat "$ROOT/logs"/findings-*.md 2>/dev/null)"
case "$FOUND" in *"take() returns size + 1 items"*) ok=0 ;; *) ok=1 ;; esac
check "the finding behind a preamble is kept" 0 "$ok"
case "$FOUND" in *"I checked whether"*) ok=1 ;; *) ok=0 ;; esac
check "the preamble is not passed on as a finding" 0 "$ok"
# What the driver says it did is the discriminating check. Read the verdict as a
# substring and the preamble sentence becomes the verdict — a value no branch
# below matches, so the run reports it could not read the reviewer at all and
# the findings reach nobody, while the findings file still looks correct.
case "$(cat "$ROOT/out.txt")" in
  *"the reviewer found something"*) ok=0 ;;
  *) ok=1 ;;
esac
check "the run reports a finding rather than an unreadable verdict" 0 "$ok"
drop_fixture

# --- a line about a failing test is not mistaken for the verdict ---
new_fixture
export STUB_MODE=blocked
export STUB_VERDICT="FAIL
- t.py:9 — the test named for a FAIL case asserts PASS instead"
mkdir -p "$ROOT/logs"
status="$(run_loop --logs "$ROOT/logs")"
check "a finding mentioning the verdict words still runs" 0 "$status"
case "$(cat "$ROOT/logs"/findings-*.md 2>/dev/null)" in
  *"the test named for a FAIL case asserts PASS instead"*) ok=0 ;; *) ok=1 ;; esac
check "a finding that mentions PASS and FAIL survives intact" 0 "$ok"
drop_fixture

# --- findings stop being sent once they stop being found ---
#
# Without this the block is set on a failing iteration and never cleared, so
# every later session is handed findings about a commit somebody already fixed
# and told to deal with them first. It re-reads the diff, finds them gone, and
# the loop pays for that on every remaining iteration. A run that fails once and
# then passes is the only shape that shows it, which is why the stub can vary
# its verdict at all.
new_fixture
export STUB_MODE=runs
export STUB_RUNS=3
export STUB_VERDICT_FIRST="FAIL
- file.txt:1 — a stale finding that gets fixed straight away"
export STUB_VERDICT="PASS"
status="$(run_loop)"
check "a run that fails once then passes still finishes" 0 "$status"
case "$(cat "$STUB_PROMPT_FILE")" in
  *"a stale finding that gets fixed straight away"*) ok=1 ;;
  *) ok=0 ;;
esac
check "findings are not repeated to sessions after they stop being found" 0 "$ok"
unset STUB_VERDICT_FIRST
drop_fixture

# --- "finished" is not the last word while the reviewer is still holding
#     something ---
#
# The loop used to take DONE off the handoff's first line and stop there and
# then, which is the one moment the reviewer's findings can be about the commit
# nobody will ever look at again. A session declares the work complete, the
# reviewer reads that final commit, finds something, and the run exits reporting
# success with the findings still in the logs directory unread. This is the gap
# the research is loudest about: the thing that ends the loop should be a check
# the agent does not get to make about its own work.
new_fixture
export STUB_MODE=donethenfix
export STUB_VERDICT_FIRST="FAIL
- file.txt:1 — the last commit left the counter off by one"
export STUB_VERDICT="PASS"
status="$(run_loop)"
check "a run sent back and then cleared still ends cleanly" 0 "$status"
check "the session that said DONE was asked again" 2 "$(cat "$STUB_COUNT_FILE")"
case "$(cat "$STUB_PROMPT_FILE")" in
  *"the last commit left the counter off by one"*) ok=0 ;; *) ok=1 ;; esac
check "the session sent back is told what was found" 0 "$ok"
case "$(cat "$ROOT/out.txt")" in *"Sending it back rather than stopping"*) ok=0 ;; *) ok=1 ;; esac
check "the run says why it did not stop at DONE" 0 "$ok"
unset STUB_VERDICT_FIRST
drop_fixture

# --- but sending it back cannot go on forever ---
#
# A reviewer that keeps failing a session that keeps declaring victory is a
# standoff, and an unbounded loop resolves it by spending until the account runs
# out. It stops and says a person is needed instead.
new_fixture
export STUB_MODE=alwaysdone
export STUB_VERDICT="FAIL
- file.txt:1 — still wrong"
# Under a wall clock, because the failure this guards against is a loop that
# never ends. Without the timeout a counter that stops advancing does not fail
# this test, it hangs the whole suite — measured, by mutating the increment to
# a no-op and watching the run never come back.
status="$( ( cd "$REPO" && timeout 120 "$LOOP" "$REPO" ) > "$ROOT/out.txt" 2>&1; echo $? )"
check "an endless standoff stops rather than spinning" 1 "$status"
# The bound itself is pinned, the way the context threshold is: one re-send
# covers the reviewer catching something real on the last commit, and a second
# disagreement after that is the two of them not converging.
check "the bound on re-sends is 2" 2 \
  "$(awk -F= '/^MAX_DONE_OVERRIDES=/ { print $2; exit }' "$LOOP")"
case "$(cat "$ROOT/out.txt")" in *"needs a person"*) ok=0 ;; *) ok=1 ;; esac
check "it says a person has to settle it" 0 "$ok"
drop_fixture

# --- the operator can move it or switch it off ---
new_fixture
export STUB_MODE=blocked
export STUB_VERDICT="PASS"
status="$(run_loop --eval-model opus)"
check "--eval-model is accepted" 0 "$status"
case "$(cat "$STUB_EVAL_ARGV_FILE")" in *"--model opus"*) ok=0 ;; *) ok=1 ;; esac
check "--eval-model picks the model the evaluator runs on" 0 "$ok"
drop_fixture

new_fixture
export STUB_MODE=blocked
status="$(run_loop --no-eval)"
check "--no-eval is accepted" 0 "$status"
check "--no-eval means no evaluator ran at all" 0 "$(cat "$STUB_EVAL_COUNT_FILE" 2>/dev/null || echo 0)"
drop_fixture

# --- the model name reaches a command line, so it is checked here ---
#
# Same discipline as --handoff-at: a value that ends up as an argument is
# validated at the door rather than trusted downstream. --model gets the same
# check because it is the same class of value and had none.
new_fixture
export STUB_MODE=blocked
status="$(run_loop --eval-model "sonnet --dangerously-skip-permissions")"
check "an --eval-model carrying another flag is refused" 1 "$status"
status="$(run_loop --eval-model "; rm -rf /")"
check "an --eval-model carrying a shell command is refused" 1 "$status"
status="$(run_loop --model "opus --dangerously-skip-permissions")"
check "a --model carrying another flag is refused" 1 "$status"
drop_fixture

# --- a reviewer and a session stuck on the same file stop rather than spin ---
#
# The reviewer reads one diff cold and reports what it can point at a file and
# line for, so it cannot tell that the file it keeps failing has stopped
# mattering. Each finding it returns becomes the next session's first job, and a
# correct finding is the kind that gets fixed — which puts the same file back in
# front of it. Measured on a real run: three iterations and about ten million
# weighted tokens went into the failure semantics of a one-shot script whose
# only job had finished two iterations earlier. This is MAX_DONE_OVERRIDES for
# the case where nobody claims to be finished.
new_fixture
export STUB_MODE=commit
export STUB_VERDICT="FAIL
- file.txt:1 — the docstring promises what the code does not do"
# Under a wall clock, for the same reason the standoff bound is: a counter that
# never advances hangs the suite instead of failing it.
status="$( ( cd "$REPO" && timeout 120 "$LOOP" "$REPO" ) > "$ROOT/out.txt" 2>&1; echo $? )"
check "findings on one file, iteration after iteration, stop the run" 1 "$status"
# The count is in the assertion, not just the file: measured with the bound
# mutated to 99, a run that stopped on the ninety-ninth round still satisfied
# "it stopped and said file.txt", so that assertion pinned nothing.
case "$(cat "$ROOT/out.txt")" in
  *"the last 3 reviews all found something in file.txt"*) ok=0 ;; *) ok=1 ;;
esac
check "it stops on the third round and names the file" 0 "$ok"
# Pinned the way the other bounds are. Three, because two consecutive findings
# on one file is the ordinary case of a fix that needed a second pass, and a
# third is the two of them circling it.
check "the bound on same-file findings is 3" 3 \
  "$(awk -F= '/^MAX_SAME_FILE_FINDINGS=/ { print $2; exit }' "$LOOP")"
drop_fixture

# --- what the session says about its own work is heard first ---
#
# BLOCKED and DONE are statements a session makes on purpose; the same-file
# bound is a heuristic read off the reviewer. A run that reaches a real stop
# condition takes it, and never reports a latch instead.
new_fixture
export STUB_MODE=runs
export STUB_RUNS=3
export STUB_VERDICT="FAIL
- file.txt:1 — the same thing again"
status="$(run_loop)"
check "a blocked handoff stops cleanly even with three findings on one file" 0 "$status"
case "$(cat "$ROOT/out.txt")" in *"the handoff is blocked"*) ok=0 ;; *) ok=1 ;; esac
check "it stops on the block rather than on the bound" 0 "$ok"
drop_fixture

# --- a finding carries what runs the code, and may be put down ---
#
# The reviewer cannot judge whether a finding is worth fixing, so it is asked
# for the fact that decides it instead: what reaches this code. The session that
# holds the handoff is the one that can weigh that, and it needs saying that it
# is allowed to.
new_fixture
export STUB_MODE=blocked
export STUB_VERDICT="PASS"
status="$(run_loop)"
check "a run carrying the new wording still finishes" 0 "$status"
EVAL_PROMPT="$(tr '\n' ' ' < "$STUB_EVAL_PROMPT_FILE" | tr -s ' ')"
case "$EVAL_PROMPT" in *"what executes that code"*) ok=0 ;; *) ok=1 ;; esac
check "the reviewer is asked what executes the code it found" 0 "$ok"
drop_fixture

# The permission to put a finding down rides with the findings rather than in
# the protocol, which every session pays for whether or not it was handed one.
new_fixture
export STUB_MODE=runs
export STUB_RUNS=2
export STUB_VERDICT="FAIL
- file.txt:1 — the docstring promises what the code does not do"
status="$(run_loop)"
check "a run that hands findings on still finishes" 0 "$status"
PROMPT="$(tr '\n' ' ' < "$STUB_PROMPT_FILE" | tr -s ' ')"
case "$PROMPT" in *"proposal, not an order"*) ok=0 ;; *) ok=1 ;; esac
check "the session handed a finding is told it may put it down" 0 "$ok"
drop_fixture

# --- a path in a finding is a name, not a pattern ---
#
# The findings file is written by a model reading the repository, so what it
# puts before the colon is text rather than a checked path. Left unquoted it
# would be split and then glob-expanded against whatever directory the loop is
# standing in, and one entry carrying a `*` would silently become several.
new_fixture
export STUB_MODE=commit
export STUB_VERDICT="FAIL
- *.txt:1 — a finding whose path reads as a pattern"
status="$( ( cd "$REPO" && timeout 120 "$LOOP" "$REPO" ) > "$ROOT/out.txt" 2>&1; echo $? )"
check "a finding path carrying a glob still stops the run at the bound" 1 "$status"
case "$(cat "$ROOT/out.txt")" in
  *"the last 3 reviews"*) ok=0 ;; *) ok=1 ;;
esac
check "it counted three rounds rather than expanding the pattern" 0 "$ok"
drop_fixture

# --- each iteration records the range of commits its session produced ---
#
# Joining a session to its commits by timestamp is wrong the moment a session
# amends: the commit it replaced becomes unreachable from HEAD, so a reading
# that walks `git log` attributes the work to whichever later session amended
# it, and the session that did the work looks like it produced nothing. The
# range is exact and the driver already holds both ends of it.
new_fixture
export STUB_MODE=blocked
BEFORE="$(git -C "$REPO" rev-parse HEAD)"
status="$(run_loop --logs "$ROOT/logs")"
check "recording the range leaves the run's exit code alone" 0 "$status"
check "the iteration wrote one record" 1 \
  "$(find "$ROOT/logs" -name 'iter-*-1.json' | wc -l | tr -d ' ')"
RECORD="$(find "$ROOT/logs" -name 'iter-*-1.json' | head -1)"
read -r GOT_BEFORE GOT_AFTER GOT_COMMITS <<EOF
$(python3 -c "
import json, sys
r = json.load(open(sys.argv[1]))
print(r['head_before'], r['head_after'], r['commits'])
" "$RECORD")
EOF
check "the record names the commit the session started from" "$BEFORE" "$GOT_BEFORE"
check "the record names where the session left HEAD" \
  "$(git -C "$REPO" rev-parse HEAD)" "$GOT_AFTER"
check "the record counts what the session added" 1 "$GOT_COMMITS"
drop_fixture

# --- the record says which findings file its session was handed ---
#
# Which sessions were working from a review rather than from the handoff is the
# split that separates a loop feeding on its own scaffolding from one building
# the project. Recovering it from the filename stamps works only while findings
# and run files happen to share one, so the driver writes down what it handed.
new_fixture
export STUB_MODE=runs
export STUB_RUNS=3
export STUB_VERDICT_FIRST="FAIL
- file.txt:1 — a finding the next session is handed"
export STUB_VERDICT="PASS"
mkdir -p "$ROOT/logs"
status="$(run_loop --logs "$ROOT/logs")"
check "a run that hands findings on still exits 0" 0 "$status"
HANDED="$(basename "$(find "$ROOT/logs" -name 'findings-*-1.md' | head -1)")"
check "the first session was handed nothing" null \
  "$(python3 -c "
import json, sys
print(json.dumps(json.load(open(sys.argv[1]))['findings_in']))
" "$(find "$ROOT/logs" -name 'iter-*-1.json' | head -1)")"
check "the second session records the findings it was handed" "\"$HANDED\"" \
  "$(python3 -c "
import json, sys
print(json.dumps(json.load(open(sys.argv[1]))['findings_in']))
" "$(find "$ROOT/logs" -name 'iter-*-2.json' | head -1)")"
unset STUB_RUNS STUB_VERDICT_FIRST STUB_VERDICT
drop_fixture

# --- a session that amends still gets its work counted ---
#
# This is the case the record exists for. The commit the session started from is
# unreachable once it amends, so anything reading `git log` afterwards sees one
# commit dated at the amend and credits it to whoever was running then.
new_fixture
export STUB_MODE=amendwork
BEFORE="$(git -C "$REPO" rev-parse HEAD)"
status="$(run_loop --logs "$ROOT/logs")"
check "an amending session runs to a clean stop" 0 "$status"
check "the amend left the commit it replaced unreachable" 1 \
  "$(git -C "$REPO" merge-base --is-ancestor "$BEFORE" HEAD; echo $?)"
check "the session that amended is credited with the work" 1 \
  "$(python3 -c "
import json, sys
print(json.load(open(sys.argv[1]))['commits'])
" "$(find "$ROOT/logs" -name 'iter-*-1.json' | head -1)")"
check "and the range starts where the session did" "$BEFORE" \
  "$(python3 -c "
import json, sys
print(json.load(open(sys.argv[1]))['head_before'])
" "$(find "$ROOT/logs" -name 'iter-*-1.json' | head -1)")"
drop_fixture

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
