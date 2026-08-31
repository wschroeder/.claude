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

failures=0

# A PATH holding the base toolset plus only the optional binaries named, so a
# case can remove jq or bc without also hiding the shell's own utilities.
# touch is present so the injection cases can actually fire; without it they
# would pass because the payload could not run, not because it was blocked.
SANDBOX_BASE_TOOLS=(cat whoami hostname git touch)
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

printf '\n'
if [ "$failures" -eq 0 ]; then
  printf 'all tests passed\n'
else
  printf '%d test(s) failed\n' "$failures"
fi
exit $((failures > 0))
