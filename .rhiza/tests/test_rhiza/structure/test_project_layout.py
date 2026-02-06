"""Tests for the root pytest fixture that yields the repository root Path.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

This module ensures the fixture resolves to the true project root and that
expected files/directories exist, enabling other tests to locate resources
reliably.
"""

from pathlib import Path

import pytest


class TestRootFixture:
    """Tests for the root fixture that provides repository root path."""

    def test_root_returns_pathlib_path(self, root):
        """Root fixture should return a pathlib.Path object."""
        assert isinstance(root, Path)

    def test_root_is_absolute_path(self, root):
        """Root fixture should return an absolute path."""
        assert root.is_absolute()

    def test_root_resolves_correctly_from_nested_location(self, root):
        """Root should correctly resolve to repository root from .rhiza/tests/test_rhiza/."""
        conftest_path = root / ".rhiza" / "tests" / "test_rhiza" / "conftest.py"
        assert conftest_path.exists()

    def test_root_contains_expected_directories(self, root):
        """Root should contain all expected project directories."""
        required_dirs = [".rhiza", "tests", "book"]
        optional_dirs = ["src"]  # src/ is optional (rhiza itself doesn't have one)

        for dirname in required_dirs:
            assert (root / dirname).exists(), f"Required directory {dirname} not found"

        for dirname in optional_dirs:
            if not (root / dirname).exists():
                pytest.skip(f"Optional directory {dirname} not present in this project")

    def test_root_contains_expected_files(self, root):
        """Root should contain all expected configuration files."""
        required_files = [
            "pyproject.toml",
            "README.md",
            "Makefile",
        ]
        optional_files = [
            "ruff.toml",
            ".gitignore",
            ".editorconfig",
        ]

        for filename in required_files:
            assert (root / filename).exists(), f"Required file {filename} not found"

        for filename in optional_files:
            if not (root / filename).exists():
                pytest.skip(f"Optional file {filename} not present in this project")

    def test_root_can_locate_github_scripts(self, root):
        """Root should allow locating GitHub scripts."""
        scripts_dir = root / ".rhiza" / "scripts"
        assert scripts_dir.exists(), ".rhiza/scripts directory should exist"
        assert (scripts_dir / "release.sh").exists(), "release.sh script should exist"
