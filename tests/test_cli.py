from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from stat import S_IMODE

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "potato_chips.py"


class LifecycleTests(unittest.TestCase):
    def run_cli(self, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args, "--home", str(home)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_install_verify_and_uninstall_preserve_existing_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            codex_rules = home / ".codex" / "AGENTS.md"
            codex_rules.parent.mkdir(parents=True)
            original = "# Existing Codex rules\n\n\n"
            codex_rules.write_text(original, encoding="utf-8")

            installed = self.run_cli(home, "install")
            self.assertEqual(installed.returncode, 0, installed.stderr)

            codex_content = codex_rules.read_text(encoding="utf-8")
            claude_content = (home / ".claude" / "CLAUDE.md").read_text(
                encoding="utf-8"
            )
            self.assertTrue(codex_content.startswith(original))
            self.assertIn("<!-- potato-chips:start -->", codex_content)
            self.assertIn("<!-- potato-chips:end -->", codex_content)
            self.assertIn("<!-- potato-chips:start -->", claude_content)

            verified = self.run_cli(home, "verify")
            self.assertEqual(verified.returncode, 0, verified.stderr)

            removed = self.run_cli(home, "uninstall")
            self.assertEqual(removed.returncode, 0, removed.stderr)
            self.assertEqual(codex_rules.read_text(encoding="utf-8"), original)
            self.assertFalse((home / ".claude" / "CLAUDE.md").exists())

    def test_install_dry_run_reports_targets_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)

            result = self.run_cli(home, "install", "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(".codex/AGENTS.md", result.stdout)
            self.assertIn(".claude/CLAUDE.md", result.stdout)
            self.assertEqual(list(home.iterdir()), [])

    def test_install_fails_without_partial_writes_on_changed_managed_block(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            codex_rules = home / ".codex" / "AGENTS.md"
            codex_rules.parent.mkdir(parents=True)
            original = (
                "# Existing\n\n"
                "<!-- potato-chips:start -->\nchanged by user\n"
                "<!-- potato-chips:end -->\n"
            )
            codex_rules.write_text(original, encoding="utf-8")

            result = self.run_cli(home, "install")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("managed block differs", result.stderr)
            self.assertEqual(codex_rules.read_text(encoding="utf-8"), original)
            self.assertFalse((home / ".claude" / "CLAUDE.md").exists())

    def test_install_rolls_back_when_a_target_cannot_be_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            codex_rules = home / ".codex" / "AGENTS.md"
            codex_rules.parent.mkdir(parents=True)
            codex_rules.write_text("# Existing\n", encoding="utf-8")
            (home / ".claude").write_text("not a directory", encoding="utf-8")

            result = self.run_cli(home, "install")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Install failed", result.stderr)
            self.assertEqual(codex_rules.read_text(encoding="utf-8"), "# Existing\n")

    def test_uninstall_refuses_to_remove_changed_managed_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(self.run_cli(home, "install").returncode, 0)
            codex_rules = home / ".codex" / "AGENTS.md"
            changed = codex_rules.read_text(encoding="utf-8").replace(
                "Verify before claiming completion.", "Keep this local change."
            )
            codex_rules.write_text(changed, encoding="utf-8")
            claude_before = (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")

            result = self.run_cli(home, "uninstall")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("managed block differs", result.stderr)
            self.assertEqual(codex_rules.read_text(encoding="utf-8"), changed)
            self.assertEqual(
                (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8"),
                claude_before,
            )

    def test_install_and_uninstall_preserve_existing_file_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            codex_rules = home / ".codex" / "AGENTS.md"
            codex_rules.parent.mkdir(parents=True)
            codex_rules.write_text("# Existing\n", encoding="utf-8")
            codex_rules.chmod(0o640)

            self.assertEqual(self.run_cli(home, "install").returncode, 0)
            self.assertEqual(S_IMODE(codex_rules.stat().st_mode), 0o640)

            self.assertEqual(self.run_cli(home, "uninstall").returncode, 0)
            self.assertEqual(S_IMODE(codex_rules.stat().st_mode), 0o640)

    def test_uninstall_fails_cleanly_when_a_target_is_not_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual(self.run_cli(home, "install").returncode, 0)
            codex_rules = home / ".codex" / "AGENTS.md"
            codex_before = codex_rules.read_text(encoding="utf-8")
            claude_rules = home / ".claude" / "CLAUDE.md"
            claude_rules.unlink()
            claude_rules.mkdir()

            result = self.run_cli(home, "uninstall")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Uninstall failed", result.stderr)
            self.assertEqual(codex_rules.read_text(encoding="utf-8"), codex_before)


if __name__ == "__main__":
    unittest.main()
