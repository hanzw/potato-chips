# Security policy

## Supported versions

Potato Chips is pre-release. Until the first stable tag, security fixes are
applied to the latest commit on `main`; older commits are not maintained as
separate supported versions.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository. Do
not include secrets, private prompts, transcripts, exploit details, or personal
data in a public issue. If private reporting is unavailable, open a public
issue containing only a request for a private contact channel.

Include the affected command or Skill, the expected and observed behavior, a
minimal reproduction, and the impact. Reports will be acknowledged after they
are reviewed; remediation timing depends on severity and whether the issue is
owned here or upstream.

## Security boundary

Potato Chips manages global rules, Skill files, and optional MCP registration.
It does not provide process isolation, a permission boundary, secret storage,
or protection from a malicious upstream dependency. Review `--dry-run` output,
pin or audit upstream revisions when your environment requires it, and keep
credentials outside Skills and repository files.

Issues in an upstream Skill, package, or service should also be reported to
that project's security channel. Potato Chips may remove or pin an affected
dependency, but it cannot provide upstream fixes or support guarantees.
