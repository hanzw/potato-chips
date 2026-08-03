#!/usr/bin/env bash
set -euo pipefail

skill_dir=$(cd "$(dirname "$0")/.." && pwd)
script="$skill_dir/scripts/codex_memory_health.sh"
task_dir=$(mktemp -d "${TMPDIR:-/tmp}/codex-memory-health-live.XXXXXX")
target="$task_dir/@tr4n2uil/codebase-mcp/dist/main.js"
test_pid=""

cleanup_owned() {
  [ -z "$test_pid" ] || kill -KILL "$test_pid" 2>/dev/null || true
  [ ! -f "$target" ] || unlink "$target"
  rmdir "$task_dir/@tr4n2uil/codebase-mcp/dist" 2>/dev/null || true
  rmdir "$task_dir/@tr4n2uil/codebase-mcp" 2>/dev/null || true
  rmdir "$task_dir/@tr4n2uil" 2>/dev/null || true
  rmdir "$task_dir" 2>/dev/null || true
}
trap cleanup_owned EXIT

mkdir -p "$(dirname "$target")"
cp "$skill_dir/tests/fixtures/@tr4n2uil/codebase-mcp/dist/main.js" "$target"
test_pid=$(sh -c 'nohup node "$1" --daemon >/dev/null 2>&1 & printf "%s" "$!"' _ "$target")
sleep 0.2
test_ppid=$(ps -p "$test_pid" -o ppid= | tr -d ' ')
[ "$test_ppid" = 1 ]
unlink "$target"

audit_output=$(bash "$script" --audit)
grep -q 'HELPER_COUNTS .* safe=1' <<< "$audit_output"
[ "$(grep -c '^pid=.* kind=' <<< "$audit_output")" -eq 1 ]
grep -q "^pid=$test_pid .* kind=codebase " <<< "$audit_output"

clean_output=$(bash "$script" --clean-safe)
grep -q 'CLEAN_RESULT=OK targeted=1' <<< "$clean_output"
if kill -0 "$test_pid" 2>/dev/null; then
  printf 'FAIL: owned orphan survived cleanup\n' >&2
  exit 1
fi

printf 'PASS live exact-target cleanup and identity revalidation\n'
