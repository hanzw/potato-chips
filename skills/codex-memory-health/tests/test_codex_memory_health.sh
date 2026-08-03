#!/usr/bin/env bash
set -euo pipefail

skill_dir=$(cd "$(dirname "$0")/.." && pwd)
script="$skill_dir/scripts/codex_memory_health.sh"
test_dir=$(mktemp -d "${TMPDIR:-/tmp}/codex-memory-health-test.XXXXXX")
trap 'find "$test_dir" -type f -delete 2>/dev/null || true; find "$test_dir" -type d -empty -delete 2>/dev/null || true' EXIT

installed_script="$test_dir/@tr4n2uil/codebase-mcp/dist/main.js"
mkdir -p "$(dirname "$installed_script")"
: > "$installed_script"
snapshot="$test_dir/processes.txt"
printf '%s\n' \
  "901 1 4194304 8388608 99.0 00:20 Mon Aug 2 12:00:00 2026 /opt/homebrew/bin/node --trace-warnings $installed_script --daemon --api-key TOPSECRET" \
  "902 1 131072 8388608 1.0 01:20 Mon Aug 2 11:00:00 2026 /opt/homebrew/bin/node --trace-warnings $installed_script --daemon" \
  '903 904 1048576 8388608 80.0 02:20 Mon Aug 2 10:00:00 2026 node /tmp/mcp-server-cloudflare --token CLOUDFLARESECRET' \
  '904 1 1024 8192 0.0 02:20 Mon Aug 2 10:00:00 2026 npm exec @cloudflare/mcp-server-cloudflare@0.2.0' \
  '905 906 524288 8388608 20.0 02:20 Mon Aug 2 10:00:00 2026 node /tmp/mcp-server-cloudflare' \
  '906 1 1024 8192 0.0 02:20 Mon Aug 2 10:00:00 2026 npm exec unrelated-package@1.0.0' \
  '907 1 3145728 8388608 30.0 02:20 Mon Aug 2 10:00:00 2026 /usr/bin/python /missing/@tr4n2uil/codebase-mcp/dist/main.js --daemon' \
  '908 909 3145728 8388608 30.0 02:20 Mon Aug 2 10:00:00 2026 /usr/bin/python /tmp/mcp-server-cloudflare' \
  '909 1 1024 8192 0.0 02:20 Mon Aug 2 10:00:00 2026 npm exec @cloudflare/mcp-server-cloudflare@0.2.0' \
  '910 1 3145728 8388608 30.0 02:20 Mon Aug 2 10:00:00 2026 node --eval /missing/@tr4n2uil/codebase-mcp/dist/main.js --daemon' \
  > "$snapshot"

output=$(CODEX_MEMORY_HEALTH_PS_SNAPSHOT="$snapshot" bash "$script" --audit)
grep -q 'HELPER_COUNTS codebase=2 cloudflare=2 safe=3' <<< "$output"
grep -q 'SAFE_CLEAN_CANDIDATES' <<< "$output"
grep -q 'REPORT_ONLY pid=902 .*codebase daemon not proven safe' <<< "$output"
grep -q 'REPORT_ONLY pid=905 .*Cloudflare MCP parent chain not proven safe' <<< "$output"
grep -q 'REPORT_ONLY pid=907 .*Node entrypoint not proven' <<< "$output"
grep -q 'REPORT_ONLY pid=908 .*Node entrypoint not proven' <<< "$output"
grep -q 'REPORT_ONLY pid=910 .*Node entrypoint not proven' <<< "$output"
grep -q 'STATUS=WARN' <<< "$output"
if grep -qE 'TOPSECRET|CLOUDFLARESECRET|--api-key|--token' <<< "$output"; then
  printf 'FAIL: audit leaked command arguments\n' >&2
  exit 1
fi

if CODEX_MEMORY_HEALTH_PS_SNAPSHOT="$snapshot" bash "$script" --clean-safe >/dev/null 2>&1; then
  printf 'FAIL: cleanup accepted a caller-supplied process snapshot\n' >&2
  exit 1
fi

printf 'PASS codex-memory-health fixture classification and redaction\n'
