"""Tests that dogfooded .claude/commands/ files match the bundles that ship them.

Bundles ship Claude Code slash commands under .claude/commands/. The mother repo
dogfoods a subset of those commands into its own root .claude/commands/ directory.
Every dogfooded command must be byte-for-byte identical to its bundle source,
except for the deliberate mother-repo overrides listed in _LOCAL_OVERRIDES — these
are adapted to this repo's specifics (e.g. no src/, a rhiza-test gate) and are
documented inside the command file itself.

The root directory is intentionally a *subset* of all bundle commands (e.g.
rhiza_update is not dogfooded here because the mother repo has no upstream to sync
from), so the check is driven from the root side: each dogfooded command is matched
back to the bundle that ships it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

# Root .claude/commands/ files that intentionally diverge from their bundle source.
# Each is a mother-repo-specific variant documented inside the command file. The
# byte-comparison test asserts these *do* differ, so a stale entry is caught here.
_LOCAL_OVERRIDES = frozenset({"rhiza_quality.md"})


def _bundle_command_sources() -> dict[str, Path]:
    """Map each command filename to the bundle .claude/commands/ file that ships it."""
    sources: dict[str, Path] = {}
    bundles_dir = _ROOT / "bundles"
    if not bundles_dir.is_dir():
        return sources
    for cmd_file in sorted(bundles_dir.glob("*/.claude/commands/*")):
        if not cmd_file.is_file() or "__pycache__" in cmd_file.parts:
            continue
        sources.setdefault(cmd_file.name, cmd_file)
    return sources


def _root_commands() -> list[Path]:
    """Return every dogfooded command file under the root .claude/commands/."""
    commands_dir = _ROOT / ".claude" / "commands"
    if not commands_dir.is_dir():
        return []
    return [p for p in sorted(commands_dir.glob("*")) if p.is_file()]


_SOURCES = _bundle_command_sources()
_ROOT_COMMANDS = _root_commands()


class TestBundleClaudeCommandsSync:
    """Verify dogfooded .claude/commands/ files stay in sync with their bundle sources."""

    def test_root_commands_dir_exists_and_is_nonempty(self) -> None:
        """Root .claude/commands/ must exist and contain at least one command file.

        Without this guard, the parametrized tests below produce zero cases when the
        directory is absent or empty, making CI appear green while the sync check
        never actually ran.
        """
        commands_dir = _ROOT / ".claude" / "commands"
        assert commands_dir.is_dir(), (
            ".claude/commands/ directory is missing — create it or remove this test "
            "if the mother repo no longer dogfoods Claude Code commands"
        )
        assert _ROOT_COMMANDS, (
            ".claude/commands/ exists but contains no command files — add at least one "
            "command or remove this test if the mother repo no longer dogfoods commands"
        )

    @pytest.mark.parametrize("root_file", _ROOT_COMMANDS, ids=[p.name for p in _ROOT_COMMANDS])
    def test_dogfooded_command_has_bundle_source(self, root_file: Path) -> None:
        """Every dogfooded command must be shipped by some bundle .claude/commands/."""
        assert root_file.name in _SOURCES, (
            f"{root_file.name}: not shipped by any bundle .claude/commands/ — "
            f"add it to a bundle or remove the dogfooded copy"
        )

    @pytest.mark.parametrize("root_file", _ROOT_COMMANDS, ids=[p.name for p in _ROOT_COMMANDS])
    def test_dogfooded_command_matches_bundle(self, root_file: Path) -> None:
        """Each dogfooded command matches its bundle source, unless a documented override."""
        source = _SOURCES.get(root_file.name)
        if source is None:
            pytest.skip(f"{root_file.name}: no bundle source (covered by the existence test)")
        if root_file.name in _LOCAL_OVERRIDES:
            assert root_file.read_bytes() != source.read_bytes(), (
                f"{root_file.name}: listed in _LOCAL_OVERRIDES but identical to its bundle "
                f"source — drop it from _LOCAL_OVERRIDES so drift is caught"
            )
            return
        assert root_file.read_bytes() == source.read_bytes(), (
            f"{root_file.name}: dogfooded copy differs from bundle source "
            f"{source.relative_to(_ROOT)} — edit both sides or add a documented override"
        )
