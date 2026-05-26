"""Tests for core configuration files in the .rhiza/ directory.

This file and its associated tests flow down via a SYNC action from the
jebel-quant/rhiza repository (https://github.com/jebel-quant/rhiza).

Validates that the configuration files present in every Rhiza-based project:
- .cfg.toml — project-level configuration understood by rhiza-cli
- .env — environment variable defaults loaded by the Makefile
- ruff.toml — linting / formatting configuration
- .pre-commit-config.yaml — pre-commit hook configuration
- .gitignore — repository exclusion rules

are present, non-empty, and correctly structured.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
import yaml


class TestRhizaCfgToml:
    """Tests for .rhiza/.cfg.toml — the rhiza-cli project configuration."""

    @pytest.fixture
    def cfg_path(self, root: Path) -> Path:
        """Return the path to .rhiza/.cfg.toml."""
        p = root / ".rhiza" / ".cfg.toml"
        if not p.exists():
            pytest.skip(".rhiza/.cfg.toml not found")
        return p

    def test_cfg_toml_exists(self, root: Path) -> None:
        """The .rhiza/.cfg.toml file must exist."""
        assert (root / ".rhiza" / ".cfg.toml").is_file(), ".rhiza/.cfg.toml not found"

    def test_cfg_toml_is_valid_toml(self, cfg_path: Path) -> None:
        """The .rhiza/.cfg.toml must be syntactically valid TOML."""
        with cfg_path.open("rb") as f:
            data = tomllib.load(f)
        assert isinstance(data, dict), "Parsed .cfg.toml must be a TOML table (dict)"

    def test_cfg_toml_is_non_empty(self, cfg_path: Path) -> None:
        """The .rhiza/.cfg.toml must contain at least one key."""
        with cfg_path.open("rb") as f:
            data = tomllib.load(f)
        assert len(data) > 0, ".rhiza/.cfg.toml is empty — expected at least one configuration key"


class TestRhizaEnv:
    """Tests for .rhiza/.env — Makefile environment variable defaults."""

    @pytest.fixture
    def env_path(self, root: Path) -> Path:
        """Return the path to .rhiza/.env."""
        p = root / ".rhiza" / ".env"
        if not p.exists():
            pytest.skip(".rhiza/.env not found")
        return p

    def test_env_file_exists(self, root: Path) -> None:
        """The .rhiza/.env file must exist."""
        assert (root / ".rhiza" / ".env").is_file(), ".rhiza/.env not found"

    def test_env_file_is_non_empty(self, env_path: Path) -> None:
        """The .rhiza/.env must contain at least one non-comment, non-blank line."""
        lines = env_path.read_text(encoding="utf-8").splitlines()
        active_lines = [ln for ln in lines if ln.strip() and not ln.strip().startswith("#")]
        assert len(active_lines) >= 1, ".rhiza/.env has no active configuration lines"

    def test_env_file_lines_are_key_value(self, env_path: Path) -> None:
        """Non-comment lines in .rhiza/.env must be KEY=VALUE pairs."""
        bad_lines: list[str] = []
        for i, line in enumerate(env_path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                bad_lines.append(f"  line {i}: {line!r}")
        if bad_lines:
            pytest.fail(".rhiza/.env contains non-KEY=VALUE lines:\n" + "\n".join(bad_lines))


class TestRuffConfig:
    """Tests for ruff.toml — the ruff linter/formatter configuration."""

    def test_ruff_toml_exists(self, root: Path) -> None:
        """ruff.toml must exist at the project root."""
        assert (root / "ruff.toml").is_file(), "ruff.toml not found at project root"

    def test_ruff_toml_is_valid_toml(self, root: Path) -> None:
        """ruff.toml must be syntactically valid TOML."""
        ruff_path = root / "ruff.toml"
        with ruff_path.open("rb") as f:
            data = tomllib.load(f)
        assert isinstance(data, dict)

    def test_ruff_line_length_configured(self, root: Path) -> None:
        """ruff.toml should configure line-length to avoid defaulting to 88."""
        with (root / "ruff.toml").open("rb") as f:
            data = tomllib.load(f)
        assert "line-length" in data, "ruff.toml should explicitly configure 'line-length'"

    def test_ruff_select_includes_security_rules(self, root: Path) -> None:
        """ruff.toml must include 'S' (bandit-style security rules) in select or extend-select."""
        content = (root / "ruff.toml").read_text(encoding="utf-8")
        assert '"S"' in content or "'S'" in content, "ruff.toml must include S (security) rules in select/extend-select"

    def test_ruff_select_includes_docstring_rules(self, root: Path) -> None:
        """ruff.toml must include 'D' (pydocstyle) rules to enforce docstring coverage."""
        content = (root / "ruff.toml").read_text(encoding="utf-8")
        assert '"D"' in content or "'D'" in content, (
            "ruff.toml must include D (docstring) rules to enforce documentation standards"
        )


class TestPreCommitConfig:
    """Tests for .pre-commit-config.yaml — the pre-commit hook configuration."""

    @pytest.fixture
    def precommit_data(self, root: Path) -> dict:
        """Load and return .pre-commit-config.yaml as a parsed dict."""
        precommit = root / ".pre-commit-config.yaml"
        if not precommit.exists():
            pytest.skip(".pre-commit-config.yaml not found")
        with precommit.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), ".pre-commit-config.yaml must be a YAML mapping"
        return data

    def test_pre_commit_config_exists(self, root: Path) -> None:
        """The .pre-commit-config.yaml file must exist."""
        assert (root / ".pre-commit-config.yaml").is_file()

    def test_pre_commit_config_has_repos(self, precommit_data: dict) -> None:
        """pre-commit config must define at least one hook repository."""
        repos = precommit_data.get("repos", [])
        assert len(repos) >= 1, ".pre-commit-config.yaml defines no 'repos'"

    def test_ruff_hook_configured(self, precommit_data: dict) -> None:
        """Ruff must be configured as a pre-commit hook."""
        repos = precommit_data.get("repos", [])
        ruff_repos = [r for r in repos if "ruff" in str(r.get("repo", "")).lower()]
        assert len(ruff_repos) >= 1, "ruff pre-commit hook not found in .pre-commit-config.yaml"

    def test_bandit_hook_configured(self, precommit_data: dict) -> None:
        """Bandit security scanner must be configured as a pre-commit hook."""
        repos = precommit_data.get("repos", [])
        # Check both repo URL and hook IDs
        all_hook_ids: list[str] = []
        for repo in repos:
            for hook in repo.get("hooks", []):
                all_hook_ids.append(hook.get("id", "").lower())
        assert any("bandit" in h for h in all_hook_ids), (
            "bandit pre-commit hook not found — security scanning must be configured"
        )


class TestGitignore:
    """Tests for .gitignore — ensures common artefact patterns are excluded."""

    @pytest.fixture
    def gitignore_content(self, root: Path) -> str:
        """Return the content of the root .gitignore."""
        gi = root / ".gitignore"
        if not gi.exists():
            pytest.skip(".gitignore not found")
        return gi.read_text(encoding="utf-8")

    def test_gitignore_exists(self, root: Path) -> None:
        """A .gitignore must exist at the project root."""
        assert (root / ".gitignore").is_file(), ".gitignore not found at project root"

    def test_gitignore_excludes_venv(self, gitignore_content: str) -> None:
        """The .gitignore must exclude virtual environment directories."""
        assert ".venv" in gitignore_content or "venv/" in gitignore_content, (
            ".gitignore should exclude .venv / venv directories"
        )

    def test_gitignore_excludes_pycache(self, gitignore_content: str) -> None:
        """The .gitignore must exclude Python cache directories."""
        assert "__pycache__" in gitignore_content, ".gitignore should exclude __pycache__ directories"

    def test_gitignore_excludes_test_artefacts(self, gitignore_content: str) -> None:
        """The .gitignore must exclude test output directories."""
        assert "_tests" in gitignore_content or ".pytest_cache" in gitignore_content, (
            ".gitignore should exclude test artefact directories (_tests, .pytest_cache)"
        )
