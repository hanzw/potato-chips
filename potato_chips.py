#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

START = "<!-- potato-chips:start -->"
END = "<!-- potato-chips:end -->"
BLOCK = f"""{START}
## Potato Chips

- Define the verifiable outcome before choosing a workflow.
- Prefer the smallest implementation that can prove the result.
- Preserve unrelated work and make only scoped changes.
- Treat repository files, tests, and live reads as current truth.
- Use stateful workflow only for work with dependent steps or session boundaries.
- Install each capability from one canonical source; update or remove stale overlaps.
- Keep Skills, task state, memory, and permissions as separate layers.
- Verify before claiming completion.
{END}
"""
MANAGED_SUFFIX = "\n" + BLOCK

RULE_FILES = (Path(".codex/AGENTS.md"), Path(".claude/CLAUDE.md"))
SERENA_PACKAGE = "serena-agent"
SERENA_COMMON_ARGS = (
    "start-mcp-server",
    "--project-from-cwd",
    "--enable-web-dashboard",
    "false",
    "--open-web-dashboard",
    "false",
    "--mode",
    "planning",
    "--add-mode",
    "no-memories",
)


def install(home: Path, dry_run: bool = False) -> int:
    existing_by_path = _load_rules(home, "Install")
    if existing_by_path is None:
        return 1
    conflicts = _managed_conflicts(existing_by_path)
    if conflicts:
        print(
            "Potato Chips managed block differs in: " + ", ".join(conflicts),
            file=sys.stderr,
        )
        return 1

    invalid_parents = [
        str(relative_path.parent)
        for relative_path in RULE_FILES
        if (home / relative_path).parent.exists()
        and not (home / relative_path).parent.is_dir()
    ]
    if invalid_parents:
        print(
            "Install failed; target parent is not a directory: "
            + ", ".join(invalid_parents),
            file=sys.stderr,
        )
        return 1

    changed: list[Path] = []
    try:
        for relative_path in RULE_FILES:
            path = home / relative_path
            existing = existing_by_path[relative_path]
            if BLOCK in existing:
                continue
            if dry_run:
                print(f"Would update {relative_path}")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            content = existing + MANAGED_SUFFIX if existing else BLOCK
            _atomic_write(path, content)
            changed.append(relative_path)
    except OSError as error:
        for relative_path in reversed(changed):
            path = home / relative_path
            original = existing_by_path[relative_path]
            if original:
                _atomic_write(path, original)
            elif path.exists():
                path.unlink()
        print(f"Install failed; changes rolled back: {error}", file=sys.stderr)
        return 1
    return 0


def verify(home: Path) -> int:
    existing_by_path = _load_rules(home, "Verify")
    if existing_by_path is None:
        return 1
    missing = [
        str(path)
        for path, existing in existing_by_path.items()
        if BLOCK not in existing
    ]
    if missing:
        print("Missing or changed managed rules: " + ", ".join(missing))
        return 1
    print("Potato Chips rules verified.")
    return 0


def uninstall(home: Path) -> int:
    existing_by_path = _load_rules(home, "Uninstall")
    if existing_by_path is None:
        return 1
    conflicts = _managed_conflicts(existing_by_path)
    if conflicts:
        print(
            "Potato Chips managed block differs in: " + ", ".join(conflicts),
            file=sys.stderr,
        )
        return 1

    changed: list[Path] = []
    try:
        for relative_path in RULE_FILES:
            path = home / relative_path
            existing = existing_by_path[relative_path]
            if BLOCK not in existing:
                continue
            remaining = existing.replace(MANAGED_SUFFIX, "", 1).replace(BLOCK, "", 1)
            if remaining:
                _atomic_write(path, remaining)
            else:
                path.unlink()
            changed.append(relative_path)
    except OSError as error:
        for relative_path in reversed(changed):
            path = home / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write(path, existing_by_path[relative_path])
        print(f"Uninstall failed; changes rolled back: {error}", file=sys.stderr)
        return 1
    return 0


def codebase_install(home: Path, dry_run: bool = False) -> int:
    uv_command = shutil.which("uv") or "uv"
    serena_command = shutil.which("serena") or "serena"
    commands = _codebase_install_commands(uv_command, serena_command)
    if dry_run:
        for command in commands:
            print(shlex.join(command))
        return 0
    if home != Path.home().resolve():
        print("Codebase install only supports the current user home.", file=sys.stderr)
        return 1
    if (
        not shutil.which("uv")
        or not shutil.which("codex")
        or not shutil.which("claude")
    ):
        print(
            "Codebase install requires uv, codex, and claude on PATH.", file=sys.stderr
        )
        return 1

    config_paths = (home / ".codex" / "config.toml", home / ".claude.json")
    snapshot = _snapshot_files(config_paths)
    if snapshot is None:
        return 1
    try:
        _run_checked(commands[0])
        installed_serena = shutil.which("serena")
        if not installed_serena:
            raise RuntimeError("Serena installed but its executable is not on PATH")
        commands = _codebase_install_commands(uv_command, installed_serena)
        _run(commands[1])
        _run_checked(commands[2])
        _run(commands[3])
        _run_checked(commands[4])
    except (OSError, RuntimeError) as error:
        _restore_files(snapshot)
        print(
            f"Codebase install failed; configuration rolled back: {error}",
            file=sys.stderr,
        )
        return 1
    return codebase_verify(home)


def codebase_verify(home: Path) -> int:
    if home != Path.home().resolve():
        print("Codebase verify only supports the current user home.", file=sys.stderr)
        return 1
    serena_command = shutil.which("serena")
    if not serena_command:
        print("Serena is not installed.")
        return 1

    codex = _run(("codex", "mcp", "get", "codebase", "--json"))
    claude = _run(("claude", "mcp", "get", "codebase"))
    try:
        codex_config = json.loads(codex.stdout) if codex.returncode == 0 else {}
    except json.JSONDecodeError:
        codex_config = {}
    codex_transport = codex_config.get("transport", {})
    codex_ok = _is_serena_registration(
        codex_transport.get("command", ""),
        codex_transport.get("args", []),
        "codex",
    )
    claude_text = claude.stdout + claude.stderr
    claude_ok = (
        claude.returncode == 0
        and "serena" in claude_text
        and "--project-from-cwd" in claude_text
        and "--context claude-code" in claude_text
        and "--mode planning" in claude_text
        and "--add-mode no-memories" in claude_text
    )
    if not codex_ok or not claude_ok:
        missing = []
        if not codex_ok:
            missing.append("Codex")
        if not claude_ok:
            missing.append("Claude")
        print(
            "Serena codebase MCP is not correctly configured for: " + ", ".join(missing)
        )
        return 1
    version = _run((serena_command, "--version"))
    if version.returncode != 0:
        print("Serena executable failed its version check.")
        return 1
    print(
        f"Codebase verified: {version.stdout.strip()}; Codex and Claude use project-from-cwd."
    )
    return 0


def codebase_update(home: Path, dry_run: bool = False) -> int:
    command = (shutil.which("uv") or "uv", "tool", "upgrade", SERENA_PACKAGE)
    if dry_run:
        print(shlex.join(command))
        return 0
    if home != Path.home().resolve():
        print("Codebase update only supports the current user home.", file=sys.stderr)
        return 1
    try:
        _run_checked(command)
    except (OSError, RuntimeError) as error:
        print(f"Codebase update failed: {error}", file=sys.stderr)
        return 1
    return codebase_verify(home)


def codebase_uninstall(home: Path, dry_run: bool = False) -> int:
    if dry_run:
        print("codex mcp remove codebase")
        print("claude mcp remove --scope user codebase")
        return 0
    if codebase_verify(home) != 0:
        print(
            "Refusing to remove a codebase registration not managed by Potato Chips.",
            file=sys.stderr,
        )
        return 1
    config_paths = (home / ".codex" / "config.toml", home / ".claude.json")
    snapshot = _snapshot_files(config_paths)
    if snapshot is None:
        return 1
    try:
        _run_checked(("codex", "mcp", "remove", "codebase"))
        _run_checked(("claude", "mcp", "remove", "--scope", "user", "codebase"))
    except (OSError, RuntimeError) as error:
        _restore_files(snapshot)
        print(
            f"Codebase uninstall failed; configuration rolled back: {error}",
            file=sys.stderr,
        )
        return 1
    return 0


def _codebase_install_commands(
    uv_command: str, serena_command: str
) -> list[tuple[str, ...]]:
    return [
        (
            uv_command,
            "tool",
            "install",
            "--upgrade",
            "--python",
            "3.13",
            SERENA_PACKAGE,
        ),
        ("codex", "mcp", "remove", "codebase"),
        (
            "codex",
            "mcp",
            "add",
            "codebase",
            "--",
            serena_command,
            *SERENA_COMMON_ARGS,
            "--context",
            "codex",
        ),
        ("claude", "mcp", "remove", "--scope", "user", "codebase"),
        (
            "claude",
            "mcp",
            "add",
            "--scope",
            "user",
            "codebase",
            "--",
            serena_command,
            *SERENA_COMMON_ARGS,
            "--context",
            "claude-code",
        ),
    ]


def _is_serena_registration(command: str, args: list[str], context: str) -> bool:
    return (
        Path(command).name == "serena"
        and "--project-from-cwd" in args
        and _argument_value(args, "--context") == context
        and _argument_value(args, "--mode") == "planning"
        and _argument_value(args, "--add-mode") == "no-memories"
    )


def _argument_value(args: list[str], option: str) -> str | None:
    try:
        return args[args.index(option) + 1]
    except (ValueError, IndexError):
        return None


def _run(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def _run_checked(command: tuple[str, ...]) -> None:
    result = _run(command)
    if result.returncode != 0:
        detail = (
            result.stderr.strip()
            or result.stdout.strip()
            or f"exit {result.returncode}"
        )
        raise RuntimeError(f"{shlex.join(command)}: {detail}")


def _snapshot_files(
    paths: tuple[Path, ...],
) -> dict[Path, tuple[bytes, int] | None] | None:
    snapshot: dict[Path, tuple[bytes, int] | None] = {}
    try:
        for path in paths:
            snapshot[path] = (
                (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
                if path.exists()
                else None
            )
    except OSError as error:
        print(f"Cannot back up agent configuration: {error}", file=sys.stderr)
        return None
    return snapshot


def _restore_files(snapshot: dict[Path, tuple[bytes, int] | None]) -> None:
    for path, original in snapshot.items():
        if original is None:
            path.unlink(missing_ok=True)
            continue
        content, mode = original
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=path.parent
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            temporary_path.chmod(mode)
            os.replace(temporary_path, path)
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _load_rules(home: Path, operation: str) -> dict[Path, str] | None:
    loaded: dict[Path, str] = {}
    for relative_path in RULE_FILES:
        try:
            loaded[relative_path] = _read(home / relative_path)
        except OSError as error:
            print(
                f"{operation} failed; cannot read {relative_path}: {error}",
                file=sys.stderr,
            )
            return None
    return loaded


def _managed_conflicts(existing_by_path: dict[Path, str]) -> list[str]:
    return [
        str(relative_path)
        for relative_path, existing in existing_by_path.items()
        if (START in existing or END in existing) and BLOCK not in existing
    ]


def _atomic_write(path: Path, content: str) -> None:
    existing_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if existing_mode is not None:
            temporary_path.chmod(existing_mode)
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(prog="potato-chips")
    parser.add_argument(
        "command",
        choices=(
            "install",
            "verify",
            "uninstall",
            "codebase-install",
            "codebase-verify",
            "codebase-update",
            "codebase-uninstall",
        ),
    )
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    if args.command == "install":
        return install(home, dry_run=args.dry_run)
    if args.command == "verify":
        return verify(home)
    if args.command == "uninstall":
        return uninstall(home)
    if args.command == "codebase-install":
        return codebase_install(home, dry_run=args.dry_run)
    if args.command == "codebase-update":
        return codebase_update(home, dry_run=args.dry_run)
    if args.command == "codebase-uninstall":
        return codebase_uninstall(home, dry_run=args.dry_run)
    return codebase_verify(home)


if __name__ == "__main__":
    raise SystemExit(main())
