#!/usr/bin/env bash
set -euo pipefail

mode="${1:---audit}"
case "$mode" in
  --audit|--clean-safe|--disk|--help) ;;
  *) printf 'Usage: %s [--audit|--clean-safe|--disk|--help]\n' "$0" >&2; exit 64 ;;
esac

if [ "$mode" = "--help" ]; then
  printf 'Usage: %s [--audit|--clean-safe|--disk]\n' "$0"
  exit 0
fi

if [ "$mode" = "--clean-safe" ] && [ -n "${CODEX_MEMORY_HEALTH_PS_SNAPSHOT:-}" ]; then
  printf 'Refusing cleanup from a caller-supplied process snapshot.\n' >&2
  exit 65
fi

task_tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/codex-memory-health.XXXXXX")
task_ps_file="$task_tmp_dir/processes.txt"
cleanup_tmp() {
  [ ! -f "$task_ps_file" ] || unlink "$task_ps_file"
  rmdir "$task_tmp_dir" 2>/dev/null || true
}
trap cleanup_tmp EXIT

if [ -n "${CODEX_MEMORY_HEALTH_PS_SNAPSHOT:-}" ]; then
  [ -f "$CODEX_MEMORY_HEALTH_PS_SNAPSHOT" ] || { printf 'Snapshot not found.\n' >&2; exit 66; }
  cp "$CODEX_MEMORY_HEALTH_PS_SNAPSHOT" "$task_ps_file"
else
  ps -axo pid=,ppid=,rss=,vsz=,%cpu=,etime=,lstart=,command= > "$task_ps_file"
fi

physical_bytes=$(sysctl -n hw.memsize)
physical_gib=$(awk -v bytes="$physical_bytes" 'BEGIN {printf "%.1f", bytes/1073741824}')
free_percent=$(memory_pressure -Q | awk -F': ' '/System-wide memory free percentage/ {gsub(/%/,"",$2); print $2}')
swap_line=$(sysctl vm.swapusage)

printf 'CODEX_MEMORY_HEALTH\n'
printf 'physical_gib=%s free_percent=%s\n' "$physical_gib" "${free_percent:-unknown}"
printf '%s\n' "$swap_line"
printf '\nTOP_RSS_MIB\n'
sort -nr -k3 "$task_ps_file" | awk '
  NR <= 15 {
    executable=$12
    sub(/^.*\//, "", executable)
    printf "pid=%s ppid=%s rss_mib=%.1f vsz_gib=%.1f cpu=%s etime=%s executable=%s\n", $1,$2,$3/1024,$4/1048576,$5,$6,executable
  }
'

codebase_script_from_command() {
  awk '
    function basename(path) {sub(/^.*\//, "", path); return path}
    BEGIN {valid=0}
    {
      if (basename($1) != "node") exit
      for (i=2; i<=NF; i++) {
        if ($i ~ /\/@tr4n2uil\/codebase-mcp\/dist\/main\.js$/) {
          if ($(i+1) == "--daemon") {print $i; valid=1}
          exit
        }
        if ($i ~ /^--(trace-warnings|no-warnings|enable-source-maps)$/) continue
        if ($i ~ /^--inspect(-brk)?(=.*)?$/) continue
        exit
      }
    }
  ' <<< "$1"
}

is_codebase_command() {
  local command="$1" script
  script=$(codebase_script_from_command "$command")
  [ -n "$script" ]
}

process_is_node() {
  local pid="$1" command="$2" executable
  if [ -n "${CODEX_MEMORY_HEALTH_PS_SNAPSHOT:-}" ]; then
    executable=${command%% *}
  else
    executable=$(ps -p "$pid" -o comm= 2>/dev/null | sed -n 's/^ *//p' || true)
  fi
  executable=${executable##*/}
  [ "$executable" = node ]
}

is_cloudflare_child_command() {
  awk '
    function basename(path) {sub(/^.*\//, "", path); return path}
    {
      if (basename($1) != "node") exit 1
      for (i=2; i<=NF; i++) {
        if ($i ~ /\/mcp-server-cloudflare$/) exit 0
        if ($i ~ /^--(trace-warnings|no-warnings|enable-source-maps)$/) continue
        if ($i ~ /^--inspect(-brk)?(=.*)?$/) continue
        exit 1
      }
      exit 1
    }
  ' <<< "$1"
}

is_cloudflare_parent_command() {
  awk '
    {
      executable=$1
      sub(/^.*\//, "", executable)
      exit !(executable == "npm" && $2 == "exec" && $3 ~ /^@cloudflare\/mcp-server-cloudflare@/)
    }
  ' <<< "$1"
}

safe_pids=()
safe_kinds=()
safe_reasons=()
safe_ppids=()
safe_starts=()
safe_commands=()
reported_codebase=0
reported_cloudflare=0

add_candidate() {
  local pid="$1" kind="$2" reason="$3" ppid="$4" start="$5" command="$6" existing
  for existing in "${safe_pids[@]:-}"; do
    [ "$existing" != "$pid" ] || return 0
  done
  safe_pids+=("$pid")
  safe_kinds+=("$kind")
  safe_reasons+=("$reason")
  safe_ppids+=("$ppid")
  safe_starts+=("$start")
  safe_commands+=("$command")
}

while read -r pid ppid rss_kb vsz_kb cpu etime start_day start_month start_date start_time start_year command; do
  [ -n "${command:-}" ] || continue
  start="$start_day $start_month $start_date $start_time $start_year"
  case "$command" in
  *"/@tr4n2uil/codebase-mcp/dist/main.js"*)
    if ! is_codebase_command "$command" || ! process_is_node "$pid" "$command"; then
      printf 'REPORT_ONLY pid=%s rss_mib=%.1f reason=codebase signature present but Node entrypoint not proven\n' "$pid" "$(awk -v rss="$rss_kb" 'BEGIN {print rss/1024}')"
      continue
    fi
    reported_codebase=$((reported_codebase + 1))
    script_path=$(codebase_script_from_command "$command")
    reason=""
    if [ "$ppid" = "1" ] && [ ! -f "$script_path" ]; then
      reason="orphan codebase daemon with missing installed script"
    elif [ "$ppid" = "1" ] && [ "$rss_kb" -ge 2097152 ]; then
      reason="orphan codebase daemon at or above 2 GiB RSS"
    fi
    if [ -n "$reason" ]; then
      add_candidate "$pid" codebase "$reason" "$ppid" "$start" "$command"
    else
      printf 'REPORT_ONLY pid=%s rss_mib=%.1f reason=codebase daemon not proven safe\n' "$pid" "$(awk -v rss="$rss_kb" 'BEGIN {print rss/1024}')"
    fi
    ;;
  *"/mcp-server-cloudflare"*)
    if ! is_cloudflare_child_command "$command" || ! process_is_node "$pid" "$command"; then
      printf 'REPORT_ONLY pid=%s rss_mib=%.1f reason=Cloudflare signature present but Node entrypoint not proven\n' "$pid" "$(awk -v rss="$rss_kb" 'BEGIN {print rss/1024}')"
      continue
    fi
    reported_cloudflare=$((reported_cloudflare + 1))
    parent_line=$(awk -v target="$ppid" '$1==target {print; exit}' "$task_ps_file")
    parent_safe=0
    if [ -n "$parent_line" ]; then
      read -r parent_pid parent_ppid parent_rss parent_vsz parent_cpu parent_etime parent_day parent_month parent_date parent_time parent_year parent_command <<< "$parent_line"
      parent_start="$parent_day $parent_month $parent_date $parent_time $parent_year"
      if [ "$parent_ppid" = "1" ] && is_cloudflare_parent_command "$parent_command"; then
        add_candidate "$pid" cloudflare-child "orphan Cloudflare MCP child" "$ppid" "$start" "$command"
        add_candidate "$parent_pid" cloudflare-parent "orphan Cloudflare MCP launcher" "$parent_ppid" "$parent_start" "$parent_command"
        parent_safe=1
      fi
    fi
    if [ "$parent_safe" -ne 1 ]; then
      printf 'REPORT_ONLY pid=%s rss_mib=%.1f reason=Cloudflare MCP parent chain not proven safe\n' "$pid" "$(awk -v rss="$rss_kb" 'BEGIN {print rss/1024}')"
    fi
    ;;
  esac
done < "$task_ps_file"

printf '\nHELPER_COUNTS codebase=%s cloudflare=%s safe=%s\n' "$reported_codebase" "$reported_cloudflare" "${#safe_pids[@]}"
if [ "${#safe_pids[@]}" -eq 0 ]; then
  printf 'STATUS=OK no proven safe orphan helpers\n'
else
  printf 'SAFE_CLEAN_CANDIDATES\n'
  for index in "${!safe_pids[@]}"; do
    pid=${safe_pids[$index]}
    rss_kb=$(awk -v target="$pid" '$1==target {print $3; exit}' "$task_ps_file")
    printf 'pid=%s rss_mib=%.1f kind=%s reason=%s\n' "$pid" "$(awk -v rss="${rss_kb:-0}" 'BEGIN {print rss/1024}')" "${safe_kinds[$index]}" "${safe_reasons[$index]}"
  done
  printf 'STATUS=WARN run --clean-safe for exact recoverable targets\n'
fi

read_current_identity() {
  local pid="$1"
  ps -p "$pid" -o ppid=,rss=,lstart=,command= 2>/dev/null | sed -n 's/^ *//p' || true
}

find_candidate_index() {
  local target="$1" index
  for index in "${!safe_pids[@]}"; do
    [ "${safe_pids[$index]}" != "$target" ] || { printf '%s' "$index"; return 0; }
  done
  return 1
}

validate_candidate() {
  local index="$1" phase="$2" pid kind expected_ppid expected_start expected_command current
  local current_ppid current_rss current_day current_month current_date current_time current_year current_command current_start script parent_index parent_current
  pid=${safe_pids[$index]}
  kind=${safe_kinds[$index]}
  expected_ppid=${safe_ppids[$index]}
  expected_start=${safe_starts[$index]}
  expected_command=${safe_commands[$index]}
  current=$(read_current_identity "$pid")
  [ -n "$current" ] || return 2
  read -r current_ppid current_rss current_day current_month current_date current_time current_year current_command <<< "$current"
  current_start="$current_day $current_month $current_date $current_time $current_year"
  [ "$current_start" = "$expected_start" ] && [ "$current_command" = "$expected_command" ] || return 1

  case "$kind" in
    codebase)
      [ "$current_ppid" = "1" ] && is_codebase_command "$current_command" && process_is_node "$pid" "$current_command" || return 1
      script=$(codebase_script_from_command "$current_command")
      { [ ! -f "$script" ] || [ "$current_rss" -ge 2097152 ]; } || return 1
      ;;
    cloudflare-parent)
      [ "$current_ppid" = "1" ] && is_cloudflare_parent_command "$current_command" || return 1
      ;;
    cloudflare-child)
      is_cloudflare_child_command "$current_command" && process_is_node "$pid" "$current_command" || return 1
      if [ "$current_ppid" = "$expected_ppid" ]; then
        parent_index=$(find_candidate_index "$expected_ppid") || return 1
        parent_current=$(read_current_identity "$expected_ppid")
        [ -n "$parent_current" ] || [ "$phase" = kill ] || return 1
        if [ -n "$parent_current" ]; then
          validate_candidate "$parent_index" "$phase" || return 1
        fi
      elif [ "$phase" = kill ] && [ "$current_ppid" = "1" ] && [ -z "$(read_current_identity "$expected_ppid")" ]; then
        :
      else
        return 1
      fi
      ;;
    *) return 1 ;;
  esac
  return 0
}

if [ "$mode" = "--clean-safe" ] && [ "${#safe_pids[@]}" -gt 0 ]; then
  printf '\nCLEANING_SAFE_ORPHANS\n'
  for index in "${!safe_pids[@]}"; do
    if validate_candidate "$index" term; then
      kill -TERM "${safe_pids[$index]}" 2>/dev/null || true
    else
      status=$?
      [ "$status" -eq 2 ] || { printf 'ABORT target identity or safety predicate changed pid=%s\n' "${safe_pids[$index]}" >&2; exit 70; }
    fi
  done

  sleep 2
  for index in "${!safe_pids[@]}"; do
    if validate_candidate "$index" kill; then
      kill -KILL "${safe_pids[$index]}" 2>/dev/null || true
    else
      status=$?
      [ "$status" -eq 2 ] || { printf 'ABORT surviving target identity or safety predicate changed pid=%s\n' "${safe_pids[$index]}" >&2; exit 70; }
    fi
  done
  sleep 0.5

  remaining=0
  for index in "${!safe_pids[@]}"; do
    if validate_candidate "$index" kill; then
      printf 'FAILED pid=%s original process still running\n' "${safe_pids[$index]}" >&2
      remaining=$((remaining + 1))
    fi
  done
  [ "$remaining" -eq 0 ] || exit 71
  printf 'CLEAN_RESULT=OK targeted=%s\n' "${#safe_pids[@]}"
  memory_pressure -Q
  sysctl vm.swapusage
fi

if [ "$mode" = "--disk" ]; then
  printf '\nDISK_USAGE\n'
  for path in "$HOME/.codex" "$HOME/Library/Application Support/Codex" "$HOME/Library/Caches/com.openai.codex" "$HOME/Library/Caches/Codex"; do
    if [ -e "$path" ]; then du -sh "$path"; else printf 'MISSING %s\n' "$path"; fi
  done
  printf 'Disk totals are attribution only; no files were deleted.\n'
fi
