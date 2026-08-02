# 🥔 Potato Chips

> **Crunch skills, not context.**

The lean Agent Skill stack for engineers who use **Codex** and **Claude Code**.

Potato Chips curates a small set of complementary development Skills, installs
them from their canonical open-source sources, and keeps every managed
capability updateable, verifiable, and removable.

> [!NOTE]
> Potato Chips is in pre-release. The first tagged version will include the
> reversible installer and versioned profiles described below.

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

```text
First Principles
       ↓
Task sizing ── small ─────────────→ direct execution
       └────── medium / large ────→ stateful workflow
                                      ↓
Native Agent Skills ─────────────→ implementation + verification
Optional code intelligence ──────→ symbol and reference retrieval
Lifecycle governance ────────────→ update, deduplicate, remove
```

Potato Chips stays at the **Skill layer**. It does not replace an Agent runtime,
ADK, model router, permission system, project rules, or memory provider. Native
Codex and Claude Code discovery remains authoritative.

## The stack

### Core controls

From [`hanzw/agent-skill-evolution`](https://github.com/hanzw/agent-skill-evolution):

| Skill | Responsibility |
| --- | --- |
| `first-principles-checkpoint` | Select the lightest trustworthy workflow and prevent scope drift |
| `evolve-skills` | Update canonical sources, detect overlap, and remove stale Skills |
| `skill-governance` | Evaluate uncertain keep, update, or remove decisions |

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

Code intelligence is native-first. Serena is enabled only when repository-scale
symbol relationships justify it, and its tool surface is limited to retrieval
and diagnostics. File editing, shell execution, onboarding, and memory remain
with their existing owners.

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

The release installer will provide:

- reversible, marked updates to Codex and Claude Code global rules;
- canonical upstream installation rather than copied Skill bodies;
- explicit receipts for managed files and dependencies;
- `dry-run`, `verify`, `update`, and `uninstall` commands;
- post-update duplicate and compatibility checks;
- no telemetry, transcript collection, or hidden capability registry.

## Credits

Potato Chips composes open-source work from its original repositories. Each
dependency retains its own license, authorship, and trademarks. See the linked
upstream projects for installation details and current documentation.

Potato Chips is not endorsed by OpenAI, Anthropic, or the maintainers of the
projects listed above.

## License

[MIT](LICENSE)
