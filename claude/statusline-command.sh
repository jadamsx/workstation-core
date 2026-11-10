#!/usr/bin/env bash
input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // .model.id // ""')
effort=$(echo "$input" | jq -r '.effort.level // empty')
branch=$(echo "$input" | jq -r '.worktree.branch // empty')
[ -z "$branch" ] && branch=$(git --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null || true)

lines_added=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
lines_removed=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')
cost=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')

used_tokens=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
window_size=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0')

five_hour_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_hour_resets=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
seven_day_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
seven_day_resets=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

c() { printf '\033[38;2;%sm' "$1"; }
R=$'\033[0m'
G="$(c 184\;184\;184)"
SEP="$(c 74\;74\;74) · $R"
pct_col() { [ "$1" -ge 80 ] && echo "247;118;142" || { [ "$1" -ge 50 ] && echo "224;175;104" || echo "158;206;106"; }; }

fmt_tokens() {
  local n=$1
  [ "$n" -ge 1000 ] && printf '%dk' $(( n / 1000 )) || printf '%d' "$n"
}

make_bar() {
  local pct=$1
  local pct_int=$(printf '%.0f' "$pct")
  local filled=$(( pct_int * 8 / 100 ))
  local bar=""
  for i in $(seq 1 "$filled"); do bar="${bar}▓"; done
  for i in $(seq 1 $(( 8 - filled ))); do bar="${bar}░"; done
  printf '%s%s %d%%%s' "$(c "$(pct_col "$pct_int")")" "$bar" "$pct_int" "$R"
}

fmt_reset() {
  local ts=$1
  [ -z "$ts" ] && return
  local epoch
  # If it's already a number, use it directly
  if [[ "$ts" =~ ^[0-9]+$ ]]; then
    epoch=$ts
  else
    epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" "+%s" 2>/dev/null) \
      || epoch=$(date -d "$ts" "+%s" 2>/dev/null) \
      || return
  fi
  local now diff
  now=$(date +%s)
  diff=$(( epoch - now ))
  if [ "$diff" -le 0 ]; then
    printf 'now'
  elif [ "$diff" -lt 3600 ]; then
    printf '%dm' $(( diff / 60 ))
  else
    printf '%dh%dm' $(( diff / 3600 )) $(( (diff % 3600) / 60 ))
  fi
}

parts=""
add() { [ -n "$parts" ] && parts="$parts$SEP$1" || parts="$1"; }

# Model + effort
if [ -n "$effort" ] && [ "$effort" != "null" ]; then
  add "$(c 122\;162\;247)$model (${effort})$R"
else
  add "$(c 122\;162\;247)$model$R"
fi

# Branch
[ -n "$branch" ] && [ "$branch" != "HEAD" ] && add "$(c 125\;207\;255)$branch$R"

# Lines changed this session
if [ "$lines_added" -gt 0 ] || [ "$lines_removed" -gt 0 ]; then
  add "$(c 158\;206\;106)+${lines_added}$R $(c 247\;118\;142)-${lines_removed}$R"
fi

# Estimated cost
cost_nonzero=$(echo "$cost > 0.00001" | bc -l 2>/dev/null || echo 0)
[ "$cost_nonzero" = "1" ] && add "$(c 224\;175\;104)\$$(printf '%.2f' "$cost")$R"

# Context window
used_fmt=$(fmt_tokens "$used_tokens")
window_fmt=$(fmt_tokens "$window_size")
used_int=$(printf '%.0f' "$used_pct")
add "$(c "$(pct_col "$used_int")")ctx (${used_fmt}/${window_fmt}) ${used_int}%$R"

# 5h rate limit + reset time
if [ -n "$five_hour_pct" ]; then
  reset_str=$(fmt_reset "$five_hour_resets")
  bar_str=$(make_bar "$five_hour_pct")
  five_str="${G}5h$R $bar_str"
  [ -n "$reset_str" ] && five_str="$five_str ${G}resets ${reset_str}$R"
  add "$five_str"
fi

# 7d rate limit
if [ -n "$seven_day_pct" ]; then
  seven_str="${G}7d$R $(make_bar "$seven_day_pct")"
  add "$seven_str"
fi

printf '%s' "$parts"
grp() { printf '%s%s%s ' "$(c "$1")" "$2" "$R"; shift 2; local x; for x in "$@"; do printf '%s%s%s ' "$(c 128\;128\;128)" "$x" "$R"; done; }
dot() { printf '%s·%s ' "$(c 74\;74\;74)" "$R"; }
printf '\n'
grp "187;154;247" plan /plan-epic /plan-story /plan-task /plan-bug /plan-spike; dot
grp "158;206;106" act /build; dot
grp "122;162;247" ship /babysit /change-write /ticket-write; printf '\n'
grp "255;158;100" verify /verify-self /verify-change /verify-epic /verify-comments /verify-plan; printf '\n'
grp "125;207;255" docs /handoff-write /handoff-read-in /diagrams /reflect
