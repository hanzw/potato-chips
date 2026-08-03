---
name: codex-memory-health
description: Diagnose and safely remediate Codex or ChatGPT desktop memory pressure, unusually high RAM or swap, runaway codebase/Serena daemons, orphan MCP servers, or claims that Codex uses tens or hundreds of gigabytes. Use when Activity Monitor shows extreme Codex memory, the machine swaps heavily, MCP tools become slow, or long agent sessions leave helper processes behind.
---

# Codex Memory Health

Measure before cleaning. Distinguish four different quantities:

- RSS is physical memory currently resident for a process.
- VSZ is reserved virtual address space and is not RAM usage.
- Swap records system pressure and may remain allocated briefly after RAM is freed.
- Cache/session directory size is disk usage, not memory.

## Fast path

Run the bundled audit from this skill directory:

```bash
bash scripts/codex_memory_health.sh --audit
```

The audit prints executable names, not full command arguments, so CLI credentials are not copied into the transcript. A normal run should finish in well under one second.

If the report lists `SAFE_CLEAN_CANDIDATES`, run:

```bash
bash scripts/codex_memory_health.sh --clean-safe
```

The cleanup must re-resolve every PID and fail closed if its command or parent changed. It may terminate only:

1. orphan `codebase-mcp --daemon` processes whose installed script has disappeared or whose RSS is at least 2 GiB;
2. orphan Cloudflare MCP child/launcher pairs where the launcher is already adopted by `launchd` (`PPID=1`).

Before changing this skill, run `bash tests/test_codex_memory_health.sh`. The fixture detector covers Node runtime flags, Python/argument decoys, unsafe Cloudflare parent chains, caller-supplied snapshot rejection, and command-argument redaction. On macOS, also run `bash tests/test_live_cleanup.sh`; it creates one owned orphan, asserts it is the only safe target, and exercises exact-target TERM/KILL revalidation.

These helpers restart on demand. Never auto-terminate ChatGPT, Codex app-server, Codex Renderer, Chrome, an attached test server, or an arbitrary Node process.

## First-principles decision order

1. Confirm system pressure with physical memory, `memory_pressure`, and swap.
2. Rank by RSS; use VSZ only as diagnostic context.
3. Prove ownership and orphan status from PID, PPID, exact command, and installed-script existence.
4. Clean the smallest recoverable target and immediately remeasure.
5. Use `--disk` only when the complaint is storage, not RAM.

If a renderer alone grows large, preserve task state first, then recommend closing unused Codex tasks or restarting the desktop app. Do not kill the current renderer from an agent turn.

## Recurrence prevention

- Prefer one stable semantic-index project per repository. Do not activate every disposable worktree as a separate codebase project.
- Keep generated trees, `node_modules`, nested worktrees, build outputs, browser artifacts, and caches excluded from semantic indexing.
- Treat repeated orphan helpers as a lifecycle bug: capture the exact command, age, RSS, and parent chain before updating or disabling the integration.
- Re-run the audit after MCP-heavy work or when swap exceeds one quarter of physical memory.

## Hard safety boundaries

- Never delete `~/.codex/sessions`, `~/.codex/memories`, ReMe data, repository files, credentials, or handoff state.
- Never clear all caches to fix RAM; cache deletion addresses disk usage and can disrupt a running app.
- Never use broad `pkill node`, `killall`, unresolved globs, or unverified PID lists.
- Report any target that is large but not provably safe instead of killing it.

For optional disk attribution, run:

```bash
bash scripts/codex_memory_health.sh --disk
```
