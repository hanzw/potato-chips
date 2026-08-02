# Potato Chips Design Handoff

## Current state

- Public repository created as `hanzw/potato-chips`.
- README is the only product artifact intended for review at this stage.
- No installer, global rules, upstream Skills, Banner, or release package has
  been added yet.
- No existing global Skill was removed as part of creating this repository.

## Goal

Publish a generalized, updateable daily-development Skill stack for Codex and
Claude Code that can be shared with colleagues or used publicly without leaking
personal project details.

## Accepted decisions

- Brand: **Potato Chips**.
- One-liner: **“Crunch skills, not context — better scripts, fewer wasted
  cycles.”**
- Install upstream Skills from their canonical repositories; never copy their
  bodies into this repository.
- Keep the default stack small and move security, evaluation, frontend, and
  long-task workflows into optional profiles when appropriate.
- Ship generalized global engineering rules for Codex and Claude, merged with
  markers and exact rollback rather than overwriting user files.
- Use Agent Skill Evolution for the stack's own update/dedup/remove lifecycle.

## Evidence already collected

- Native `skills` can target `codex` and `claude-code` together.
- The current private global inventory still contains unsourced legacy wrappers
  and personal/project-specific Skills; cleanup is incomplete.
- `mattpocock/skills` exposes portable engineering candidates, but its current
  `code-review` expects Matt-specific setup files and tool semantics.
- Buildomator is useful task-state infrastructure but should not silently become
  a cross-agent core dependency until both-agent behavior is verified.

## Next step after review

Apply requested README changes first. Only after approval:

1. finalize the core and optional profiles;
2. implement reversible install/update/verify/uninstall with dry-run;
3. add generalized `AGENTS.md` and Claude adapter content;
4. generate the original anime-style Banner;
5. validate in isolated Codex and Claude homes;
6. publish the first versioned release;
7. separately audit and clean the user's existing global Skill inventory.

## Public-data boundary

Do not add user names, employers, local paths, repository names, credentials,
brokerage behavior, private deployment rules, raw prompts, or private Skill
inventories to this repository.
