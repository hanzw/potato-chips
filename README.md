# 🥔 Potato Chips

> **Crunch skills, not context — better scripts, fewer wasted cycles.**

A small, maintainable daily-development Skill stack for engineers who use
**Codex and Claude Code**. Potato Chips installs portable Agent Skills from
their canonical open-source repositories, applies one shared set of global
engineering rules, and gives every managed item an update, verification, and
removal path.

> [!IMPORTANT]
> This repository is currently a **design preview**. The installer has not been
> published yet. Review the scope below before treating it as a distribution.

## Start here: First Principles before workflow

`first-principles-checkpoint` is the first control in the stack, not another
optional methodology. At session start, the agent answers four questions from
current repository evidence:

1. What concrete outcome must exist when this task is done?
2. What facts must be true for that outcome to be trustworthy?
3. What is the smallest next action that can prove or disprove one fact?
4. What process, artifact, or scope can be removed or deferred?

That checkpoint selects the lightest workflow that can still produce reliable
evidence. It runs again only at decisions where complexity can compound: after
a blocker or failed test, before adding a dependency or abstraction, at the end
of an implementation wave, and before claiming completion.

## Automatic task sizing

Potato Chips classifies the task before choosing a workflow. A task is **small**
only when all small-task conditions hold; any medium or large signal moves it
upward.

| Size | Recognition signals | Default action |
| --- | --- | --- |
| Small | One outcome, one local seam, one focused session, one direct verification path, no migration or coordinated release | Work directly; do not create planning state |
| Medium | Multiple dependent steps, more than one module/service, schema or configuration changes, integration/E2E evidence, or a likely PR-sized change | Auto-start Buildomator routing; prefer a validated quick task when scope is already clear |
| Large | Cross-session or multi-repository work, architectural change, data migration, staged release/rollback, parallel workstreams, or external coordination | Auto-start or resume a Buildomator milestone before implementation |

If sizing is ambiguous, take one read-only discovery step. If the task still has
dependent unknowns, classify it as medium. Risk alone does not justify a giant
plan; it just requires the relevant evidence and recovery path.

### Startup routing

```text
read repository truth
        ↓
first-principles checkpoint
        ↓
classify small / medium / large
        ├─ small  -> direct execution + direct verification
        └─ M/L    -> resume existing state, else invoke /bm:do <task>
```

When `/bm:` is available, the agent starts the medium/large workflow without
waiting for the user to remember a command. It emits one short notice, then lets
Buildomator route to the appropriate quick task, discussion, project, milestone,
plan, execution, or verification flow. An existing `.planning/STATE.md` or
unfinished handoff is resumed before creating new state.

Buildomator is currently
[Claude Code-native](https://github.com/buildomator/buildomator). On a Codex
installation where `/bm:` is not available, Potato Chips uses the same sizing
rules and maintains a bounded `HANDOFF.md`; it must never claim that
Buildomator started when it did not.

## Why “Potato Chips”?

A Skill should be a small, composable capability chip—not another framework.
Give the agent the right chips and it produces cleaner scripts while wasting
fewer compute cycles. The stack should stay crisp: if a Skill is stale,
duplicated, or no longer useful, remove it.

## The common pain

| Pain | Potato Chips answer |
| --- | --- |
| Every new tool installs more instructions | A deliberately small core with optional profiles |
| Similar Skills compete for attention | One canonical source per capability |
| Codex and Claude drift into different behavior | Shared rules plus native installation to both agents |
| Global instruction files become personal and unshareable | A generalized, marked section with no names or project paths |
| Updates restore old duplicates | Re-run discovery and lifecycle checks after every update |
| Uninstall means manually hunting symlinks and config | Every managed item gets a verified removal path |
| Long sessions lose the actual objective | First-principles checkpoints and bounded task handoffs |

## What this is—and is not

```text
Potato Chips              -> selects and maintains the daily Skill stack
Native Agent Skills       -> reusable development capabilities
Repository AGENTS.md      -> project-specific truth and rules
HANDOFF / task tool       -> current long-task continuation
Memory provider           -> optional durable history
Agent runtime / ADK       -> executes or hosts agents; not replaced here
```

Potato Chips is not an Agent Development Kit, model router, orchestration
framework, memory database, or shadow Skill registry. Native Codex and Claude
Skill discovery remains authoritative.

## Proposed stack

The default is intentionally smaller than a “top 100 Skills” list.

### Essential control loop

Installed from
[`hanzw/agent-skill-evolution`](https://github.com/hanzw/agent-skill-evolution)
(MIT):

| Skill | Reason it earns a default slot |
| --- | --- |
| `first-principles-checkpoint` | Selects the smallest trustworthy workflow at startup and prevents drift during execution |
| `evolve-skills` | Finds canonical sources, updates, deduplicates, and removes stale Skills |
| `skill-governance` | Tests an uncertain keep/update/remove decision instead of guessing |

### Medium/large task engine

[`buildomator/buildomator`](https://github.com/buildomator/buildomator) (MIT) is
included as the preferred stateful workflow whenever its `/bm:` command surface
is available. Fresh Claude Code installation follows the upstream commands:

```text
/plugin marketplace add buildomator/marketplace
/plugin install bm@buildomator
/reload-plugins
```

Potato Chips uses `/bm:do <task>` as the automatic routing entry rather than
hard-coding one large workflow for every task. The legacy `/gsd:` prefix remains
a compatibility alias during the 4.x line; new documentation uses `/bm:`.

### Engineering core under review

Candidates come from
[`mattpocock/skills`](https://github.com/mattpocock/skills) (MIT) and will be
installed from that repository rather than copied:

| Skill | Daily job | Current decision |
| --- | --- | --- |
| `codebase-design` | Design deep, testable modules and clean seams | Include |
| `diagnosing-bugs` | Build a tight failing signal before changing code | Include |
| `tdd` | Run behavior-first red/green slices | Include |
| `resolving-merge-conflicts` | Preserve both intents and verify the result | Include |
| `research` | Use primary sources and capture cited findings | Review portability |
| `code-review` | Review standards and spec separately | Review portability; currently expects Matt-specific project setup |

### Optional profiles

Optional means opt-in, not secretly installed by the default command.

| Profile | Canonical source | Purpose |
| --- | --- | --- |
| Large-codebase intelligence | [`oraios/serena`](https://github.com/oraios/serena) (MIT) | Add LSP-backed symbol lookup and reference tracing for medium/large repositories when native search is insufficient |
| Skill evaluation | [`promptfoo/promptfoo`](https://github.com/promptfoo/promptfoo) (MIT) | Install `promptfoo-evals` and `promptfoo-provider-setup` for controlled Skill ablations |
| Security audit | [`trailofbits/skills`](https://github.com/trailofbits/skills) (CC BY-SA 4.0) | Add narrowly selected security Skills for audit work, not normal coding turns |

#### Codebase intelligence: native first

Potato Chips does not install a semantic indexer for every user. Start with the
host agent's native file search, Git, and language tooling. Enable the Serena
profile only when the task needs symbol relationships, cross-file references,
or repeated discovery across a large repository that native search cannot
answer efficiently.

The profile exposes Serena's LSP-backed retrieval tools to both Codex and Claude
Code. Its overlapping file, shell, and editing utilities stay disabled, and its
memory feature stays disabled because durable history belongs to the selected
memory provider. This keeps Serena a code-intelligence layer rather than a
second agent workflow or memory system.

The profile deliberately does not default to an embedding database or graph
service. Those systems can improve natural-language or architectural discovery,
but add indexing, storage, daemon, credential, or database lifecycle costs that
do not earn an always-on place in the core.

### Deliberate non-defaults

- [`obra/superpowers`](https://github.com/obra/superpowers) and
  [`github/spec-kit`](https://github.com/github/spec-kit) are strong projects,
  but their default development workflows overlap with the task-state and
  implementation loop above.
- Large catalogs from
  [`anthropics/skills`](https://github.com/anthropics/skills),
  [`openai/skills`](https://github.com/openai/skills), and
  [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills)
  should be installed by need or profile, not as an always-on bundle.
- Local compatibility wrappers, personal finance Skills, organization-specific
  deploy rules, and generated `source-command-*` bridges never belong in the
  public default.
- Existing private code-index launchers remain local migration inputs; Potato
  Chips does not publish or depend on them.

These exclusions are about overlap and context quality—not a ranking of the
upstream projects.

## Planned Codex + Claude contract

The installer will use the native [`skills`](https://www.npmjs.com/package/skills)
manager with both targets explicitly selected:

```bash
npx skills@latest add <canonical-source> \
  --skill <selected-skills> \
  --global --agent codex claude-code --yes
```

Compatibility is not considered proven merely because installation succeeds.
Before release, every selected Skill must pass:

1. native discovery in Codex and Claude Code;
2. frontmatter validation;
3. a scan for unavailable tool names and runtime-specific assumptions;
4. a realistic trigger test;
5. install, update, verify, and uninstall checks in an isolated home;
6. a clean removal check showing no retired alias remains.

Skills that need unavailable tools, private project conventions, or copied
upstream bodies will be removed from the default instead of patched locally.

## Planned global rules

Potato Chips will ship one generalized rules template and merge a clearly marked
section into both global instruction files without replacing unrelated content:

```text
Codex        -> ~/.codex/AGENTS.md
Claude Code  -> ~/.claude/CLAUDE.md
```

The shared rules cover only durable engineering behavior:

- run First Principles before selecting the workflow and at complexity-bearing
  decision points;
- automatically start or resume Buildomator for recognized medium/large tasks
  when `/bm:` is available, otherwise maintain a bounded handoff;
- think before coding and surface assumptions;
- prefer the smallest implementation that solves the request;
- make surgical changes and preserve dirty worktrees;
- define verifiable outcomes and run the relevant checks;
- treat repository files and live reads as current truth;
- keep Skills, task state, memory, and permissions as separate layers;
- never store secrets, raw transcripts, or personal project paths;
- install from upstream, credit upstream, and delete real duplicates.

Personal names, employers, repository paths, credentials, brokerage behavior,
deployment accounts, and company-specific policy are explicitly excluded.

## Planned lifecycle

```text
install -> discover -> verify -> use -> update -> re-audit -> remove or keep
```

The first release must provide:

- `install`: back up global rule files, merge the managed section, install each
  selected Skill from its canonical source, and write a local receipt;
- `update`: update upstream Skills, then rerun portability and duplicate checks;
- `verify`: compare expected and native discovery and detect broken symlinks or
  retired aliases;
- `uninstall`: remove only Potato Chips-managed Skills and restore or remove the
  marked rules section;
- `dry-run`: print every planned change without writing anything.

There will be no telemetry, prompt collection, copied Skill bodies, or hidden
capability database.

## Core advantage

Most Skill packs optimize for **how much they install**. Potato Chips optimizes
for **how confidently the stack can evolve**:

1. one source per capability;
2. First Principles chooses the lightest adequate workflow;
3. medium/large tasks automatically gain durable state instead of relying on
   the user to remember a command;
4. the same task-sizing behavior in Codex and Claude, with an honest fallback
   where Buildomator is unavailable;
5. optional profiles instead of permanent context growth;
6. evidence before keep/update/remove decisions;
7. reversible global changes and explicit upstream credit.

## Review before implementation

Please review these decisions first:

- Is the four-Skill engineering core small enough?
- Should `research` become default or remain optional?
- Should Matt's current `code-review` be excluded until its project-setup
  dependency is removed upstream?
- Are the medium/large recognition signals conservative enough to avoid
  starting Buildomator for genuinely small work?
- Is security better as an opt-in profile rather than an always-loaded default?
- Is the Serena profile narrow enough, with native search remaining the default?

The implementation will begin only after this public scope is accepted.

## Credits and trademarks

Potato Chips installs open-source work from its original repositories and does
not claim authorship over upstream Skills. Each dependency retains its own
license and attribution. “Codex,” “Claude,” and all upstream project names are
the property of their respective owners. This project is not endorsed by
OpenAI, Anthropic, Matt Pocock, Promptfoo, Buildomator, Trail of Bits, GitHub,
Vercel, or the maintainers of Superpowers.
