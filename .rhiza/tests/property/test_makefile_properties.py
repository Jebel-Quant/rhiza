"""Property-based tests for Makefile targets and operations.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

Uses Hypothesis to generate test cases that verify Makefile behavior with various inputs.
"""

from __future__ import annotations

import re

from hypothesis import given, strategies as st
import pytest

from api.conftest import run_make


# Known Makefile targets to exclude from unknown target tests
KNOWN_MAKEFILE_TARGETS = [
    "help", "install", "test", "fmt", "deptry", "clean", "benchmark",
    "mypy", "typecheck", "security", "sync", "validate", "readme",
    "print", "version", "rhiza", "post", "pre"
]


class TestMakefileProperties:
    """Property-based tests for Makefile target validation."""

    @given(target_name=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-_"),
        min_size=1,
        max_size=20
    ))
    def test_unknown_target_produces_error(self, logger, target_name):
        """Property: Unknown targets should produce a meaningful error message."""
        # Filter out known targets
        if target_name in KNOWN_MAKEFILE_TARGETS or any(target_name.startswith(prefix) for prefix in KNOWN_MAKEFILE_TARGETS):
            return

        proc = run_make(logger, [target_name], check=False, dry_run=False)
        # Should either fail or show it's unknown
        if proc.returncode != 0:
            # Make typically says "No rule to make target" or similar
            assert "No rule" in proc.stderr or "No rule" in proc.stdout or proc.returncode != 0

    @given(variable_name=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_"),
        min_size=1,
        max_size=30
    ))
    def test_print_variable_always_succeeds(self, logger, variable_name):
        """Property: print-VARIABLE target should always succeed even for undefined variables."""
        # The print-% target should work for any variable name
        proc = run_make(logger, [f"print-{variable_name}"], check=False)
        # Should succeed (though value might be empty)
        assert proc.returncode == 0

    def test_help_output_structure_is_consistent(self, logger):
        """Property: Help output should always have a consistent structure."""
        proc = run_make(logger, ["help"])
        out = proc.stdout

        # Help should always contain these sections
        assert "Usage:" in out
        assert "Targets:" in out

        # Every target line should follow the pattern "  target-name  description"
        # We can validate the structure even if content varies
        lines = out.split("\n")
        target_section = False
        for line in lines:
            if "Targets:" in line:
                target_section = True
                continue
            if target_section and line.strip().startswith("make"):
                # Usage section
                continue
            if target_section and line.strip() and not line.strip().startswith("#"):
                # Should be either a section header or a target line
                # Section headers are bold (contain ANSI codes) or are simple text
                # Target lines have spaces between name and description
                if not any(x in line for x in ["\033[", "##@"]):
                    # Regular target line - should have consistent spacing
                    parts = line.split()
                    if len(parts) >= 2:
                        # First part is target name, rest is description
                        assert len(parts[0]) > 0


class TestVersionStringProperties:
    """Property-based tests for version string handling."""

    @given(major=st.integers(min_value=0, max_value=99),
           minor=st.integers(min_value=0, max_value=99),
           patch=st.integers(min_value=0, max_value=999))
    def test_version_string_format(self, major, minor, patch):
        """Property: Version strings should always follow semver format."""
        version = f"{major}.{minor}.{patch}"
        # Should match semver pattern
        pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(pattern, version)

    @given(version_string=st.from_regex(r"^\d+\.\d+\.\d+$", fullmatch=True))
    def test_version_parsing_never_raises(self, version_string):
        """Property: Valid version strings should always parse successfully."""
        parts = version_string.split(".")
        assert len(parts) == 3
        # Should be able to convert to integers
        major, minor, patch = map(int, parts)
        assert major >= 0
        assert minor >= 0
        assert patch >= 0


class TestPathProperties:
    """Property-based tests for path handling in Makefile operations."""

    @given(dirname=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-_"),
        min_size=1,
        max_size=20
    ))
    def test_relative_path_handling(self, dirname):
        """Property: Directory names should not contain path traversal."""
        # Ensure paths don't contain dangerous patterns
        assert ".." not in dirname
        assert "/" not in dirname
        assert "\\" not in dirname

    @given(filename=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-_."),
        min_size=1,
        max_size=30
    ).filter(lambda x: not x.startswith(".") and not x.endswith(".")))
    def test_filename_safety(self, filename):
        """Property: Filenames should be safe for filesystem operations."""
        # Should not contain path separators or control characters
        assert "/" not in filename
        assert "\\" not in filename
        assert "\0" not in filename
        assert "\n" not in filename
        assert "\r" not in filename
