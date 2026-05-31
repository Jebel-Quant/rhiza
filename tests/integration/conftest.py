"""Fixtures for rhiza-specific integration tests.

These tests live in tests/ (not .rhiza/tests/) and do not sync downstream.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from pathlib import Path

import pytest

GIT = shutil.which("git") or "/usr/bin/git"


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a temporary directory with a minimal git repo and pyproject.toml."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')
    subprocess.run([GIT, "init"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    subprocess.run([GIT, "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    subprocess.run([GIT, "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    return tmp_path
