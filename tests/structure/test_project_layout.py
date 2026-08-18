"""Tests for the root pytest fixture that yields the repository root Path.

This module ensures the fixture resolves to the true project root and that expected
files/directories exist, enabling other tests to locate resources reliably.

It used to carry a header saying it flowed downstream via a SYNC action, which had not been
true since the module moved into the mother repo's own ``tests/``. The distinction is real
now that the rhiza checks are a package (#1540): this asserts *rhiza's* layout, while the
equivalent assertion for a consumer's repository lives in pytest-rhiza.
"""

import pytest


class TestRootFixture:
    """Tests for the root fixture that provides repository root path."""

    def test_root_resolves_correctly_from_nested_location(self, root):
        """Root must resolve to the repository root, not to the nested test package.

        Anchored on ``.rhiza/template-bundles.yml``, and the choice of anchor has a history
        worth heeding. It was ``.rhiza/tests/conftest.py`` until the rhiza checks became the
        pytest-rhiza dependency (#1540), then ``.rhiza/rhiza.mk`` until the make layer became
        the rhiza-task dependency. Both anchors were *synced template content*, so each
        extraction invalidated one — the same shape of breakage twice.

        The bundle inventory cannot go the same way: it is what makes this the mother repo
        rather than a consumer of it, so no extraction can move it out.
        """
        assert (root / ".rhiza" / "template-bundles.yml").is_file(), f"{root} does not look like the rhiza mother repo"

    def test_root_contains_expected_directories(self, root):
        """Root should contain all expected project directories."""
        required_dirs = [".rhiza"]
        # optional_dirs = ["src", "tests", "book"]  # src/ is optional (rhiza itself doesn't have one)

        for dirname in required_dirs:
            assert (root / dirname).exists(), f"Required directory {dirname} not found"

        # Check that at least one CI directory exists (.github or .gitlab)
        ci_dirs = [".github", ".gitlab"]
        if not any((root / ci_dir).exists() for ci_dir in ci_dirs):
            pytest.fail(f"At least one CI directory from {ci_dirs} must exist")

        # Optional directories are not enforced in this shared layout test.

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

        missing_optional_files = [filename for filename in optional_files if not (root / filename).exists()]
        if missing_optional_files:
            pytest.skip("Optional files not present in this project: " + ", ".join(missing_optional_files))
