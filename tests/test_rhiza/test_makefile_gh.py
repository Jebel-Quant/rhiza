"""Tests for the GitHub Makefile targets using safe dry-runs.

These tests validate that the .github/github.mk targets are correctly exposed
and emit the expected commands without actually executing them.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from conftest import run_make

# We need to copy these files to the temp dir for the tests to work
REQUIRED_FILES = [
    ".github/github.mk",
]


@pytest.fixture(autouse=True)
def setup_gh_makefile(logger, root, tmp_path: Path):
    """Copy the Makefile and GitHub Makefile into a temp directory."""
    logger.debug("Setting up temporary GitHub Makefile test dir: %s", tmp_path)

    # Copy the main Makefile
    if (root / "Makefile").exists():
        shutil.copy(root / "Makefile", tmp_path / "Makefile")

    # Copy core Rhiza Makefiles
    if (root / ".rhiza" / "rhiza.mk").exists():
        (tmp_path / ".rhiza").mkdir(exist_ok=True)
        shutil.copy(root / ".rhiza" / "rhiza.mk", tmp_path / ".rhiza" / "rhiza.mk")

    if (root / ".rhiza" / ".env").exists():
        (tmp_path / ".rhiza").mkdir(exist_ok=True)
        shutil.copy(root / ".rhiza" / ".env", tmp_path / ".rhiza" / ".env")

    # Copy required split Makefiles
    for rel_path in REQUIRED_FILES:
        source_path = root / rel_path
        if source_path.exists():
            dest_path = tmp_path / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source_path, dest_path)
            logger.debug("Copied %s to %s", source_path, dest_path)
        else:
            pytest.skip(f"Required file {rel_path} not found")

    # Move into tmp directory
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def test_gh_targets_exist(logger):
    """Verify that GitHub targets are listed in help."""
    result = run_make(logger, ["help"], dry_run=False)
    output = result.stdout

    expected_targets = ["gh-install", "view-prs", "view-issues", "failed-workflows", "whoami"]

    for target in expected_targets:
        assert target in output, f"Target {target} not found in help output"


@pytest.mark.parametrize("target", [
    "gh-install",
    "view-prs",
    "view-issues",
    "failed-workflows",
    "whoami",
])
def test_gh_target_dry_run(logger, target):
    """Verify GitHub Makefile target dry-run succeeds."""
    result = run_make(logger, [target])
    assert result.returncode == 0
