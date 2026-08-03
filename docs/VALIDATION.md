# Core Skill validation

Validated on 2026-08-03 using fresh Codex executions, native Skill discovery,
Promptfoo `0.121.20`, the live Serena MCP, and the public CLI lifecycle.

## Published core

| Capability | Canonical source | Evidence |
| --- | --- | --- |
| First-principles reset | [`hanzw/agent-skill-evolution`](https://github.com/hanzw/agent-skill-evolution) | Controlled two-case ablation and a fresh implicit-routing trace |
| Skill lifecycle | [`hanzw/agent-skill-evolution`](https://github.com/hanzw/agent-skill-evolution) | Native inventory, update, source, overlap, and removal audit used for this release |
| Skill governance | [`hanzw/agent-skill-evolution`](https://github.com/hanzw/agent-skill-evolution) | Promptfoo baseline-versus-treatment workflow completed without eval errors |
| Code intelligence | This repository | Fresh Codex execution loaded the Skill, audited resources, and called Serena symbol tools |
| Memory health | This repository | Synthetic classifier tests, live exact-target cleanup, and read-only machine audit passed |

The governance workflow also installs `promptfoo-evals` and
`promptfoo-provider-setup` from
[`promptfoo/promptfoo`](https://github.com/promptfoo/promptfoo). They are support
dependencies, so the public installer verifies seven installed Skills while the
product surface remains five capabilities.

## Observed results

### First-principles ablation

Two representative overengineering regressions were executed once against the
same model and schema with and without `first-principles-checkpoint`:

| Arm | Passed | Failed |
| --- | ---: | ---: |
| Baseline | 0 | 2 |
| With Skill | 2 | 0 |

The four calls completed in 28 seconds and used 98,733 total tokens. Promptfoo's
Codex provider did not expose `response.metadata.skillCalls` in this run, so a
separate fresh execution was used to prove activation: its event trace read the
project fixture's `SKILL.md` and emitted the required outcome, known facts,
smallest proof, and deferred work.

This is a single controlled observation, not a universal model benchmark. It is
enough to retain the Skill because it prevented both regressions without adding
a runtime or persistent service.

### Code intelligence chain

A fresh read-only Codex task asked for the definition, references, and test
impact of `codebase_install`. The trace showed this sequence:

```text
load codebase-intelligence
  → run codex-memory-health --audit
  → activate the current Serena project
  → find_symbol + find_referencing_symbols + get_symbols_overview
  → cross-check with rg and the focused unit test
  → run codex-memory-health --audit again
```

The task found the production dispatch, the only CLI test seam, and an uncovered
verification gap without modifying the repository. The focused test passed.

### Memory health

- Fixture classification and command-argument redaction: passed.
- macOS live cleanup of one owned orphan with PID identity revalidation: passed.
- Read-only machine audit: completed with no safe orphan cleanup candidates.
- The tool never terminated Codex, ChatGPT, a renderer, or an attached process.

### Installer lifecycle

The public CLI test suite verifies:

- exact canonical GitHub sources;
- Codex and Claude Code installation targets;
- dry-run output for install, update, and removal;
- native JSON inventory verification;
- reversible shared-rule changes;
- Serena registration for both hosts.

## Deliberate exclusions

- Buildomator remains an optional Claude task-state plugin for medium and large
  work. Its broad command catalog is not copied into Codex global Skills.
- Language-, framework-, research-, UI-, and security-specific Skills remain
  optional profiles rather than global defaults.
- ReMe remains the durable-memory provider. It is not represented as a Skill.
- Project Skills remain in their repositories and are never promoted globally.

The exclusion rule is simple: when a capability is not needed across most
projects or duplicates a host/plugin capability, do not spend global Skill
metadata on it.
