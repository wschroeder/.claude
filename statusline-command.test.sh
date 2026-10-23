#!/usr/bin/env bash
# Tests for statusline-command.sh. Run: bash statusline-command.test.sh
#
# A missing-dependency case removes the binary from PATH rather than stubbing an
# exit code, so what it exercises is the real absence.

set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SCRIPT="$SCRIPT_DIR/statusline-command.sh"
# Resolved now so the sandbox PATH below cannot hide the interpreter itself.
BASH_BIN=$(command -v bash)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Every case runs against a throwaway log directory. Without this the suite
# would append to the operator's real usage log on each run, and the deltas
# taken from that log would count test payloads as usage.
export CLAUDE_USAGE_LOG_DIR="$TMP/usage-log"

failures=0

# A PATH holding the base toolset plus only the optional binaries named, so a
# case can remove jq or bc without also hiding the shell's own utilities.
# touch is present so the injection cases can actually fire; without it they
# would pass because the payload could not run, not because it was blocked.
SANDBOX_BASE_TOOLS=(cat whoami hostname git touch mkdir date rm chmod)
sandbox_path() {
  local dir="$TMP/bin.$1"; shift
  rm -rf "$dir"; mkdir -p "$dir"
  local tool resolved
  set -- "${SANDBOX_BASE_TOOLS[@]}" "$@"
  for tool in "$@"; do
    resolved=$(command -v "$tool" 2>/dev/null) || continue
    ln -sf "$resolved" "$dir/$tool"
  done
  printf '%s' "$dir"
}

assert_output() {
  local name=$1 expected=$2 actual=$3
  if [ "$actual" = "$expected" ]; then
    printf 'ok   %s\n' "$name"
  else
    printf 'FAIL %s\n       expected: %s\n       actual:   %s\n' "$name" "$expected" "$actual"
    failures=$((failures + 1))
  fi
}

assert_contains() {
  local name=$1 needle=$2 haystack=$3
  case "$haystack" in
    *"$needle"*) printf 'ok   %s\n' "$name" ;;
    *) printf 'FAIL %s\n       expected to contain: %s\n       actual: %s\n' "$name" "$needle" "$haystack"
       failures=$((failures + 1)) ;;
  esac
}

assert_absent() {
  local name=$1 needle=$2 haystack=$3
  case "$haystack" in
    *"$needle"*) printf 'FAIL %s\n       expected NOT to contain: %s\n       actual: %s\n' "$name" "$needle" "$haystack"
                 failures=$((failures + 1)) ;;
    *) printf 'ok   %s\n' "$name" ;;
  esac
}

# The shape the live harness actually sends, captured from a running session.
FIXTURE="$TMP/input.json"
cat > "$FIXTURE" <<'JSON'
{
  "model": { "id": "claude-opus-5[1m]", "display_name": "Opus 5 (1M context)" },
  "workspace": { "current_dir": "/tmp/not-a-repo", "project_dir": "/tmp/not-a-repo" },
  "context_window": { "used_percentage": 14, "context_window_size": 1000000 },
  "cwd": "/tmp/not-a-repo"
}
JSON

USER_HOST="$(whoami)@$(hostname -s)"

# --- everything available ---------------------------------------------------
full_path=$(sandbox_path full jq bc)
out=$(PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$FIXTURE")
assert_output "full deps: renders cwd, model and context detail" \
  "$USER_HOST /tmp/not-a-repo | Opus 5 (1M context) ctx:14% (140K/1000K)" "$out"

# --- bc absent -------------------------------------------------------------
# The percentage comes straight from jq, so it survives; only the K/K
# breakdown needs arithmetic. Losing it should be announced, not silent.
nobc_path=$(sandbox_path nobc jq)
out=$(PATH="$nobc_path" "$BASH_BIN" "$SCRIPT" < "$FIXTURE")
assert_contains "bc absent: keeps the percentage"        "ctx:14%"     "$out"
assert_contains "bc absent: names the missing tool"      "bc missing"  "$out"
assert_absent   "bc absent: drops the token breakdown"   "140K"        "$out"
assert_contains "bc absent: still renders the model"     "Opus 5"      "$out"

# --- jq absent -------------------------------------------------------------
# Nothing can be parsed without jq, so the line degrades to identity plus
# the reason, rather than emptiness or a shell error.
nojq_path=$(sandbox_path nojq bc)
out=$(PATH="$nojq_path" "$BASH_BIN" "$SCRIPT" < "$FIXTURE")
assert_contains "jq absent: names the missing tool" "jq missing" "$out"
assert_contains "jq absent: still identifies user and host" "$USER_HOST" "$out"
assert_absent   "jq absent: emits no shell error text" "command not found" "$out"

# --- git branch ------------------------------------------------------------
repo="$TMP/repo"
mkdir -p "$repo"
git -C "$repo" init -q -b trunk 2>/dev/null
cat > "$TMP/input-repo.json" <<JSON
{
  "model": { "display_name": "Opus 5" },
  "workspace": { "current_dir": "$repo" },
  "context_window": { "used_percentage": 14, "context_window_size": 1000000 },
  "cwd": "$repo"
}
JSON
out=$(PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$TMP/input-repo.json")
assert_contains "in a repo: shows the branch" "(trunk)" "$out"

# --- no debug artifact -----------------------------------------------------
# The script used to copy every payload to a world-readable /tmp path.
if [ -e /tmp/statusline-input.json ]; then
  printf 'SKIP writes no debug copy of the payload (/tmp/statusline-input.json already exists; not deleting it)\n'
else
  PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$FIXTURE" > /dev/null
  if [ -e /tmp/statusline-input.json ]; then
    printf 'FAIL writes no debug copy of the payload\n       /tmp/statusline-input.json was created\n'
    failures=$((failures + 1))
    rm -f /tmp/statusline-input.json
  else
    printf 'ok   writes no debug copy of the payload\n'
  fi
fi

# --- absent optional fields ------------------------------------------------
cat > "$TMP/input-sparse.json" <<'JSON'
{ "cwd": "/tmp/not-a-repo" }
JSON
out=$(PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$TMP/input-sparse.json")
assert_output "sparse input: renders identity and cwd only" \
  "$USER_HOST /tmp/not-a-repo" "$out"

# --- untrusted numeric fields ----------------------------------------------
# The payload is JSON from another process. bash evaluates an array subscript
# inside $(( )), so a non-numeric value reaching arithmetic is code execution.
CANARY="$TMP/pwned-arith"
cat > "$TMP/input-arith-injection.json" <<JSON
{ "cwd": "/tmp", "model": { "display_name": "M" },
  "context_window": { "used_percentage": 14, "context_window_size": "x[\$(touch $CANARY)]" } }
JSON
rm -f "$CANARY"
out=$(PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$TMP/input-arith-injection.json" 2>/dev/null)
if [ -e "$CANARY" ]; then
  printf 'FAIL non-numeric context size does not execute code\n       canary %s was created\n' "$CANARY"
  failures=$((failures + 1))
  rm -f "$CANARY"
else
  printf 'ok   non-numeric context size does not execute code\n'
fi
assert_absent "non-numeric context size: no bogus breakdown" "0K" "$out"

CANARY2="$TMP/pwned-pct"
cat > "$TMP/input-pct-injection.json" <<JSON
{ "cwd": "/tmp", "model": { "display_name": "M" },
  "context_window": { "used_percentage": "a[\$(touch $CANARY2)]", "context_window_size": 1000000 } }
JSON
rm -f "$CANARY2"
out=$(PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$TMP/input-pct-injection.json" 2>/dev/null)
if [ -e "$CANARY2" ]; then
  printf 'FAIL non-numeric percentage does not execute code\n       canary %s was created\n' "$CANARY2"
  failures=$((failures + 1))
else
  printf 'ok   non-numeric percentage does not execute code\n'
fi
assert_absent "non-numeric percentage: not echoed into the line" "touch" "$out"
assert_contains "non-numeric percentage: rest of line intact" "/tmp | M" "$out"

# A non-numeric field must not leave bc complaining on stderr either.
err=$(PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$TMP/input-arith-injection.json" 2>&1 >/dev/null)
assert_output "non-numeric context size: silent on stderr" "" "$err"

# --- fractional percentage --------------------------------------------------
# This is why bc carries the multiply rather than bash arithmetic.
cat > "$TMP/input-fractional.json" <<'JSON'
{ "cwd": "/tmp", "model": { "display_name": "M" },
  "context_window": { "used_percentage": 14.7, "context_window_size": 1000000 } }
JSON
out=$(PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$TMP/input-fractional.json")
assert_contains "fractional percentage: renders it" "ctx:14.7%" "$out"
assert_contains "fractional percentage: rounds the breakdown" "(147K/1000K)" "$out"

# --- subscription usage sampling -------------------------------------------
# A subscription meters usage as a fraction of two rolling windows, and that
# fraction is in this payload and nowhere on disk. These pin that the sample is
# taken, and that failing to take it never costs the status line.
SAMPLE_FIXTURE="$TMP/input-sample.json"
cat > "$SAMPLE_FIXTURE" <<'JSON'
{
  "session_id": "test-session-1",
  "cwd": "/tmp/not-a-repo",
  "model": { "id": "claude-opus-5[1m]", "display_name": "Opus 5 (1M context)" },
  "effort": { "level": "xhigh" },
  "workspace": { "current_dir": "/tmp/not-a-repo" },
  "context_window": { "used_percentage": 43, "context_window_size": 1000000 },
  "cost": { "total_cost_usd": 38.865748 },
  "rate_limits": {
    "five_hour": { "used_percentage": 26, "resets_at": 1789616400 },
    "seven_day": { "used_percentage": 19, "resets_at": 1790128800 }
  }
}
JSON

sample_dir="$TMP/sample-a"
out=$(CLAUDE_USAGE_LOG_DIR="$sample_dir" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$SAMPLE_FIXTURE")
assert_contains "sampling: the bar still renders" "Opus 5 (1M context)" "$out"

line=$(cat "$sample_dir"/*.jsonl 2>/dev/null | tail -1)
if [ -z "$line" ]; then
  printf 'FAIL sampling: an invocation appends a line\n       nothing under %s\n' "$sample_dir"
  failures=$((failures + 1))
else
  printf 'ok   sampling: an invocation appends a line\n'
  field() { printf '%s' "$line" | jq -r "$1"; }
  assert_output "sampling: records the session"       "test-session-1"      "$(field .session)"
  assert_output "sampling: records the model"         "claude-opus-5[1m]"   "$(field .model)"
  assert_output "sampling: unwraps the effort object" "xhigh"               "$(field .effort)"
  assert_output "sampling: records list-price usd"    "38.865748"           "$(field .usd)"
  assert_output "sampling: records the 5-hour window" "26"                  "$(field .five_hour_pct)"
  assert_output "sampling: records the 7-day window"  "19"                  "$(field .seven_day_pct)"
  assert_output "sampling: timestamps the sample"     "true" \
    "$(field '.ts | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]+Z$")')"
fi

# Two turns must leave two samples, or no delta can be taken across a run.
CLAUDE_USAGE_LOG_DIR="$sample_dir" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$SAMPLE_FIXTURE" > /dev/null
assert_output "sampling: a second turn appends rather than replaces" \
  "2" "$(cat "$sample_dir"/*.jsonl | wc -l | tr -d ' ')"

# Claude Code sends effort as a bare string to hooks and as an object here.
sample_str="$TMP/sample-str"
jq '.effort = "medium"' "$SAMPLE_FIXTURE" > "$TMP/input-effort-string.json"
CLAUDE_USAGE_LOG_DIR="$sample_str" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$TMP/input-effort-string.json" > /dev/null
assert_output "sampling: a bare-string effort is recorded too" \
  "medium" "$(cat "$sample_str"/*.jsonl | tail -1 | jq -r .effort)"

# An API-key account, and a subscription before its first API response, both
# arrive with no rate_limits at all. The sample must still be taken.
sample_nolimit="$TMP/sample-nolimit"
out=$(CLAUDE_USAGE_LOG_DIR="$sample_nolimit" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$FIXTURE")
assert_contains "sampling: no rate_limits still renders the bar" "Opus 5" "$out"
assert_output "sampling: an absent window records null, not a dropped sample" \
  "null" "$(cat "$sample_nolimit"/*.jsonl 2>/dev/null | tail -1 | jq -r .seven_day_pct)"

# The log directory is the one path in this script taken from the environment.
out=$(CLAUDE_USAGE_LOG_DIR="/proc/nonexistent/nope" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$SAMPLE_FIXTURE" 2>/dev/null)
assert_contains "sampling: an unwritable log directory still renders the bar" "Opus 5" "$out"
err=$(CLAUDE_USAGE_LOG_DIR="/proc/nonexistent/nope" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$SAMPLE_FIXTURE" 2>&1 >/dev/null)
assert_output "sampling: an unwritable log directory is silent on stderr" "" "$err"

# Payload fields reach a file path and a jq program, so the same canary the
# arithmetic cases use applies here.
CANARY3="$TMP/pwned-sample"
cat > "$TMP/input-sample-injection.json" <<JSON
{ "cwd": "/tmp", "model": { "display_name": "M", "id": "x[\$(touch $CANARY3)]" },
  "session_id": "\$(touch $CANARY3)",
  "context_window": { "used_percentage": 14, "context_window_size": 1000000 } }
JSON
rm -f "$CANARY3"
CLAUDE_USAGE_LOG_DIR="$TMP/sample-inj" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$TMP/input-sample-injection.json" > /dev/null 2>&1
if [ -e "$CANARY3" ]; then
  printf 'FAIL sampling: a payload field does not execute code\n       canary %s was created\n' "$CANARY3"
  failures=$((failures + 1))
  rm -f "$CANARY3"
else
  printf 'ok   sampling: a payload field does not execute code\n'
fi

# The log holds the operator's spend and how much of their subscription window
# is gone. The driver writes its own logs directory under $HOME owner-only for
# that same reason, and this one is created beside it.
perm_dir="$TMP/sample-perm"
CLAUDE_USAGE_LOG_DIR="$perm_dir" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$SAMPLE_FIXTURE" > /dev/null
assert_output "sampling: the log directory is owner-only" "700" \
  "$(stat -c '%a' "$perm_dir" 2>/dev/null || stat -f '%Lp' "$perm_dir")"

# --- no debug artifact from sampling ----------------------------------------
if [ -e /tmp/statusline-probe.json ]; then
  printf 'FAIL sampling: leaves no probe copy of the payload\n       /tmp/statusline-probe.json exists\n'
  failures=$((failures + 1))
else
  printf 'ok   sampling: leaves no probe copy of the payload\n'
fi

# --- the sampler's log does not grow without bound --------------------------
# The sampler writes one file a day and nothing else removes them, so it drops
# the oldest itself once a month of days is on disk.
retain_dir="$TMP/sample-retain"
mkdir -p "$retain_dir"
for month in 07 08; do
  i=1
  while [ "$i" -le 20 ]; do
    printf -v day '%02d' "$i"
    : > "$retain_dir/2026-$month-$day.jsonl"
    i=$((i + 1))
  done
done
CLAUDE_USAGE_LOG_DIR="$retain_dir" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$SAMPLE_FIXTURE" > /dev/null
kept=("$retain_dir"/*.jsonl)
assert_output "retention: a run leaves thirty days of samples" "30" "${#kept[@]}"
assert_output "retention: drops the oldest day" "absent" \
  "$([ -e "$retain_dir/2026-07-01.jsonl" ] && echo present || echo absent)"
assert_output "retention: keeps the newest day it was given" "present" \
  "$([ -e "$retain_dir/2026-08-20.jsonl" ] && echo present || echo absent)"
assert_output "retention: keeps the sample this run just took" "1" \
  "$(cat "$retain_dir/$(date -u +%Y-%m-%d).jsonl" 2>/dev/null | wc -l | tr -d ' ')"

# Under the limit nothing is dropped, so a quiet month keeps every day it has.
under_dir="$TMP/sample-under"
mkdir -p "$under_dir"
for day in 01 02 03 04 05; do : > "$under_dir/2026-08-$day.jsonl"; done
CLAUDE_USAGE_LOG_DIR="$under_dir" PATH="$full_path" "$BASH_BIN" "$SCRIPT" < "$SAMPLE_FIXTURE" > /dev/null
under=("$under_dir"/*.jsonl)
assert_output "retention: under the limit nothing is dropped" "6" "${#under[@]}"

printf '\n'
if [ "$failures" -eq 0 ]; then
  printf 'all tests passed\n'
else
  printf '%d test(s) failed\n' "$failures"
fi
exit $((failures > 0))
