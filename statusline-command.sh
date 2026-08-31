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
