# 🥔 Potato Chips

> **Crunch skills, not context.**

The lean Agent Skill stack for engineers who use **Codex** and **Claude Code**.

Potato Chips curates a small set of complementary development Skills, installs
them from their canonical open-source sources, and keeps every managed
capability updateable, verifiable, and removable.

> [!NOTE]
> Potato Chips is in pre-release. The installer is usable now; the first tag
> will freeze the public profile and compatibility contract.

## Why

Agent setups usually grow by addition. Similar Skills overlap, global rules
drift, and old integrations remain active long after they stop helping. The
result is not just more context—it is less reliable tool selection.

Potato Chips applies four constraints:

1. **One capability, one canonical source.**
2. **The smallest workflow that can prove the result.**
3. **Optional capabilities stay optional.**
4. **Everything installed must have an update and removal path.**

## Architecture

Potato Chips is a thin control profile above the native Agent host. It keeps
workflow instructions, task state, active context, durable memory, retrieval,
and repository truth separate instead of turning them into one opaque system.

See the [upper-layer architecture and design rationale](docs/ARCHITECTURE.md).
Potato Chips stays at the **Skill layer**: it does not replace an Agent runtime,
ADK, model router, permission system, project rules, or memory provider. Native
Codex and Claude Code discovery remains authoritative.

## Quick start

Preview and install the shared rules:

```bash
python3 potato_chips.py install --dry-run
python3 potato_chips.py install
python3 potato_chips.py verify
```

Install global code intelligence for both agents:

```bash
npx skills add hanzw/potato-chips --global \
  --agent codex claude-code --skill codebase-intelligence --yes
python3 potato_chips.py codebase-install --dry-run
python3 potato_chips.py codebase-install
python3 potato_chips.py codebase-verify
```

This installs the official `serena-agent` package and registers one user-level
MCP named `codebase` in Codex and Claude Code. On each new agent session,
`--project-from-cwd` selects the current Git repository automatically; there is
no per-project MCP registration. Existing sessions must be restarted to load
changed MCP configuration.

Update or remove it explicitly:

```bash
npx skills update codebase-intelligence --global --yes
python3 potato_chips.py codebase-update
python3 potato_chips.py codebase-uninstall
npx skills remove codebase-intelligence --global \
  --agent codex claude-code --yes
```

## The stack

### Core controls

From [`hanzw/agent-skill-evolution`](https://github.com/hanzw/agent-skill-evolution):

| Skill | Responsibility |
| --- | --- |
| `first-principles-checkpoint` | Select the lightest trustworthy workflow and prevent scope drift |
| `evolve-skills` | Update canonical sources, detect overlap, and remove stale Skills |
| `skill-governance` | Evaluate uncertain keep, update, or remove decisions |

From this repository, `codebase-intelligence` is the thin routing Skill that
selects Serena for symbol relationships and broad impact analysis. It contains
no copied Serena documentation and no project-specific rules.

### Engineering core

Selected from [`mattpocock/skills`](https://github.com/mattpocock/skills):

- `codebase-design`
- `diagnosing-bugs`
- `tdd`
- `resolving-merge-conflicts`

These cover the daily implementation loop without installing a broad catalog.

### Stateful work

[`buildomator/buildomator`](https://github.com/buildomator/buildomator) provides
durable task state for medium and large work when its `/bm:` command surface is
available. Small tasks stay direct; Codex uses a bounded handoff when the
Buildomator integration is unavailable.

### Optional profiles

| Profile | Source | Purpose |
| --- | --- | --- |
| Code intelligence | [`oraios/serena`](https://github.com/oraios/serena) | LSP-backed symbol and reference retrieval for large repositories |
| Skill evaluation | [`promptfoo/promptfoo`](https://github.com/promptfoo/promptfoo) | Controlled Skill and prompt evaluations |
| Security review | [`trailofbits/skills`](https://github.com/trailofbits/skills) | Focused security workflows |

Code intelligence is native-first. Serena is registered globally, then used
when repository-scale symbol relationships justify it. Its official `planning`
and `no-memories` modes keep this integration read-only and prevent a second
memory layer; repository files remain current truth, and ReMe or another
selected provider remains the memory layer.

## Scope boundary

- Global Skills contain only reusable, cross-project behavior.
- Project Skills contain domain rules, deployment procedures, and private data
  workflows for that repository.
- A project-specific Skill may expose a thin Claude/Codex adapter, but its body
  has one canonical source.
- Serena is global infrastructure, not a project Skill and not a memory store.

## Automatic workflow selection

| Task | Default route |
| --- | --- |
| Small, local, directly verifiable | Execute and verify directly |
| Multiple dependent steps or modules | Start or resume a bounded stateful workflow |
| Cross-session, architectural, migration, or release work | Use a milestone with explicit verification and recovery |

The classification is evidence-based. Risk adds the relevant verification and
rollback path; it does not automatically justify a larger process.

## Lifecycle

```text
install → discover → verify → use → update → re-audit → keep or remove
```

The installer provides:

- reversible, marked updates to Codex and Claude Code global rules;
- official upstream installation rather than copied dependency code;
- `dry-run`, `verify`, `update`, and `uninstall` commands;
- verification after install and update;
- no telemetry, transcript collection, or hidden capability registry.

## Credits

Potato Chips composes open-source work from its original repositories. Each
dependency retains its own license, authorship, and trademarks. See the linked
upstream projects for installation details and current documentation.

Potato Chips is not endorsed by OpenAI, Anthropic, or the maintainers of the
projects listed above.

## License

[MIT](LICENSE)
