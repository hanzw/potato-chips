---
name: codebase-intelligence
description: "Use the global codebase MCP for repository-scale code navigation: locating symbol declarations or implementations, tracing callers and references, impact analysis, and understanding relationships across files or modules. Trigger before broad grep or full-file reads when the task is primarily about code symbols and their relationships."
---

# Codebase Intelligence

Use the MCP server named `codebase` as a semantic index. Keep repository files,
tests, and live reads as current truth.

1. Start with `get_symbols_overview` or `find_symbol`.
2. Use `find_referencing_symbols`, `find_implementations`, or declaration tools
   for relationships and impact.
3. Batch independent lookups in one turn; request symbol bodies only when needed.
4. Use host-agent tools for edits, shell commands, and exact text searches.
5. Verify conclusions against affected code and tests before making a claim.

Do not use Serena onboarding or memory tools. Do not create project memories.
The global integration is intentionally read-only and ReMe remains the durable
memory owner. If `codebase` is unavailable, fall back to native search and state
that semantic lookup was unavailable.

Skip this Skill for a single known file, a literal text search, or non-code
documentation where native read/search is simpler.
