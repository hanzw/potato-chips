#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import stat
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
    parser.add_argument("command", choices=("install", "verify", "uninstall"))
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    if args.command == "install":
        return install(home, dry_run=args.dry_run)
    return {"verify": verify, "uninstall": uninstall}[args.command](home)


if __name__ == "__main__":
    raise SystemExit(main())
