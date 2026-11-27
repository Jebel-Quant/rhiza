"""The typos hook: wired with --force-exclude, and an allowlist that stays honest.

typos runs as a hook in the root ``.pre-commit-config.yaml``, which rhiza_ci.yml's
pre-commit job runs, so a misspelling fails the required ``CI gate``. Its configuration
lives in ``[tool.typos]`` in pyproject.toml. Each test closes one way it goes wrong:

* without ``--force-exclude``, typos checks every file prek names explicitly, so the
  CHANGELOG.md exclusion holds for ``--all-files`` scans but not for a commit touching it;
* an allowed word that no longer occurs anywhere is a hole kept open for nothing.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import tomllib
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_HOOK_REPO = "https://github.com/crate-ci/typos"


def _typos_hook() -> dict:
    """Return the typos hook entry from the root pre-commit config."""
    config = yaml.safe_load((_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    for repo in config["repos"]:
        if repo["repo"] == _HOOK_REPO:
            hooks = [hook for hook in repo["hooks"] if hook["id"] == "typos"]
            assert len(hooks) == 1, f"expected one typos hook in {_HOOK_REPO}, got {hooks}"
            return hooks[0]
    raise AssertionError(f"the root .pre-commit-config.yaml has no {_HOOK_REPO} hook")


def _typos_config() -> dict:
    """Return the ``[tool.typos]`` table from pyproject.toml."""
    with (_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["tool"]["typos"]


def _allowed() -> list[str]:
    """Return every allowed word and identifier."""
    default = _typos_config()["default"]
    return sorted({*default.get("extend-words", {}), *default.get("extend-identifiers", {})})


class TestTyposGate:
    """The hook honours the exclusions, and every allowed entry is still needed."""

    def test_hook_forces_exclusions(self) -> None:
        """--force-exclude makes [tool.typos.files] apply to the file names prek passes."""
        assert "--force-exclude" in _typos_hook().get("args", [])

    def test_hook_reports_rather_than_rewrites(self) -> None:
        """--write-changes would silently 'correct' identifiers like `froms` in place."""
        assert "--write-changes" not in _typos_hook().get("args", [])

    def test_changelog_is_excluded(self) -> None:
        """Released sections are history generated from commit messages."""
        assert "CHANGELOG.md" in _typos_config()["files"]["extend-exclude"]

    @pytest.mark.parametrize("word", _allowed())
    def test_allowed_entry_still_occurs(self, word: str) -> None:
        """An allowlist entry nothing uses any more should be removed, not kept open."""
        git = shutil.which("git")
        if git is None:
            pytest.skip("git is not installed")
        result = subprocess.run(  # nosec B603
            [git, "grep", "-l", "-w", "-i", word, "--", ".", ":!pyproject.toml"],
            cwd=_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip(), f"`{word}` is allowed in [tool.typos] but occurs nowhere; remove it"
