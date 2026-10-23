#!/usr/bin/env bash
input=$(cat)

have() { command -v "$1" >/dev/null 2>&1; }

# bash runs command substitution inside an array subscript in $(( )), so an
# unchecked field reaching arithmetic is code execution.
is_integer() { [[ $1 =~ ^[0-9]+$ ]]; }
is_number()  { [[ $1 =~ ^[0-9]+(\.[0-9]+)?$ ]]; }

parts="$(whoami)@$(hostname -s)"

# Nothing in the payload is readable without jq, so there is nothing to fall
# through to.
if ! have jq; then
  printf '%s [jq missing]' "$parts"
  exit 0
fi

# A subscription meters usage as a fraction of two rolling windows, and Claude
# Code persists that fraction nowhere — it arrives in this payload and is gone.
# Every failure here is swallowed: a lost sample must not cost the status line.
sample_usage() {
  local dir="${CLAUDE_USAGE_LOG_DIR:-$HOME/.claude/usage-log}"
  mkdir -p "$dir" 2>/dev/null || return 0
  # The samples are the operator's spend and how much of their subscription
  # window is gone. A directory this cannot make private gets no sample.
  chmod 700 "$dir" 2>/dev/null || return 0
  printf '%s\n' "$input" \
    | jq -c --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '{
        ts: $ts,
        session: .session_id,
        model: .model.id,
        effort: (.effort | if type == "object" then .level else . end),
        usd: .cost.total_cost_usd,
        ctx_pct: .context_window.used_percentage,
        five_hour_pct: .rate_limits.five_hour.used_percentage,
        seven_day_pct: .rate_limits.seven_day.used_percentage
      }' >> "$dir/$(date -u +%Y-%m-%d).jsonl" 2>/dev/null || return 0
  prune_usage_log "$dir"
}

# Log names are ISO dates, one file per UTC day, so a glob lists them oldest
# first. Ordering by name rather than age keeps this portable: macOS date takes
# only -v-30d, GNU date only -d "30 days ago", and each rejects the other.
prune_usage_log() {
  local dir=$1 files keep=30 excess
  # Without this an empty argument globs the root instead of a log directory,
  # and what stops the rm is then only which files the root happens to hold.
  [ -n "$dir" ] || return 0
  files=("$dir"/*.jsonl)
  [ -e "${files[0]}" ] || return 0
  excess=$(( ${#files[@]} - keep ))
  [ "$excess" -gt 0 ] || return 0
  rm -f "${files[@]:0:excess}" 2>/dev/null || return 0
}
sample_usage

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
model=$(echo "$input" | jq -r '.model.display_name // empty')
used=$(echo "$input" | jq -r '.context_window.used_percentage | numbers')
context_size=$(echo "$input" | jq -r '.context_window.context_window_size | numbers')

if [ -n "$cwd" ]; then
  parts="${parts} ${cwd}"
fi

if [ -n "$cwd" ] && git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
  if [ -n "$branch" ]; then
    parts="${parts} (${branch})"
  fi
fi

if [ -n "$model" ]; then
  parts="${parts} | ${model}"
fi

if is_number "$used" && is_integer "$context_size"; then
  parts="${parts} ctx:${used}%"
  # bc carries the multiply because bash integer arithmetic rejects a
  # fractional percentage.
  if have bc; then
    used_tokens=$(printf '%.0f' "$(echo "scale=0; $context_size * $used / 100" | bc)")
    parts="${parts} ($((used_tokens / 1000))K/$((context_size / 1000))K)"
  else
    parts="${parts} [bc missing]"
  fi
fi

printf '%s' "$parts"
