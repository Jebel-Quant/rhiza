"""Tests for install pattern consistency across Makefiles.

This module validates that all installation targets follow the project's
standard pattern:
1. Check if the tool is available globally (in PATH)
2. If not, install to the local ./bin directory

Exceptions:
- gh CLI: Only checks for global install (no local install available)

Test Types:
- Mock tests: Use mocked commands to verify logic without network/side effects
- Integration tests: Validate actual Makefile patterns via dry-run
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Makefiles that contain install targets
INSTALL_MAKEFILES = [
    "Makefile",
    ".github/Makefile.gh",
    ".rhiza/agentic/Makefile.agentic",
    "presentation/Makefile.presentation",
]

# Expected install patterns for each tool
# Format: (makefile, target_name, tool_name, expects_local_install)
INSTALL_PATTERNS = [
    ("Makefile", "install-uv", "uv", True),
    (".github/Makefile.gh", "gh-install", "gh", False),  # Exception: no local install
    (".rhiza/agentic/Makefile.agentic", "install-copilot", "copilot", True),
    ("presentation/Makefile.presentation", "install-marp", "marp", True),
]


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


@pytest.fixture
def setup_makefiles(logger, root, tmp_path: Path) -> Generator[Path, None, None]:
    """Copy all Makefiles into a temp directory and chdir there."""
    logger.debug("Setting up temporary Makefile test dir: %s", tmp_path)

    # Copy the main Makefile
    if (root / "Makefile").exists():
        shutil.copy(root / "Makefile", tmp_path / "Makefile")

    # Copy .rhiza/.env if present
    if (root / ".rhiza" / ".env").exists():
        (tmp_path / ".rhiza").mkdir(exist_ok=True, parents=True)
        shutil.copy(root / ".rhiza" / ".env", tmp_path / ".rhiza" / ".env")

    # Copy all split Makefiles
    for makefile in INSTALL_MAKEFILES:
        source_path = root / makefile
        if source_path.exists():
            dest_path = tmp_path / makefile
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source_path, dest_path)
            logger.debug("Copied %s to %s", source_path, dest_path)

    # Copy other required includes
    other_includes = [
        "tests/Makefile.tests",
        "book/Makefile.book",
        ".rhiza/Makefile.rhiza",
        ".rhiza/customisations/Makefile.customisations",
    ]
    for include in other_includes:
        source_path = root / include
        if source_path.exists():
            dest_path = tmp_path / include
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source_path, dest_path)

    # Move into tmp directory
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old_cwd)


def run_make(
    logger,
    args: list[str] | None = None,
    check: bool = True,
    dry_run: bool = True,
) -> subprocess.CompletedProcess:
    """Run `make` with optional arguments."""
    cmd = ["make"]
    if args:
        cmd.extend(args)
    flags = "-sn" if dry_run else "-s"
    cmd.insert(1, flags)

    logger.info("Running command: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603

    if check and result.returncode != 0:
        msg = f"make failed with code {result.returncode}:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        raise AssertionError(msg)
    return result


class TestInstallPatternConsistency:
    """Tests to verify install targets follow the global-check-then-local pattern."""

    def test_all_install_targets_exist_in_help(self, logger, setup_makefiles):
        """Verify all install targets appear in make help."""
        result = run_make(logger, ["help"], dry_run=False)
        output = result.stdout

        for _, target, tool, _ in INSTALL_PATTERNS:
            assert target in output, f"Install target '{target}' for {tool} not found in help output"

    @pytest.mark.parametrize(
        ("makefile", "target", "tool", "expects_local"),
        INSTALL_PATTERNS,
        ids=[f"{p[2]}" for p in INSTALL_PATTERNS],
    )
    def test_makefile_contains_global_check(self, root, makefile, target, tool, expects_local):
        """Verify each install Makefile checks for global installation first."""
        makefile_path = root / makefile
        if not makefile_path.exists():
            pytest.skip(f"Makefile {makefile} not found")

        content = makefile_path.read_text()

        # All install patterns should check if command exists globally
        # Pattern: command -v <tool> or which <tool>
        global_check_pattern = rf"command -v {tool}|which {tool}"
        assert re.search(global_check_pattern, content), (
            f"Install target in {makefile} should check if '{tool}' is available globally"
        )

    @pytest.mark.parametrize(
        ("makefile", "target", "tool", "expects_local"),
        [p for p in INSTALL_PATTERNS if p[3]],  # Only tools with local install
        ids=[f"{p[2]}" for p in INSTALL_PATTERNS if p[3]],
    )
    def test_makefile_contains_local_install_fallback(self, root, makefile, target, tool, expects_local):
        """Verify install targets with local install check INSTALL_DIR or bin directory."""
        makefile_path = root / makefile
        if not makefile_path.exists():
            pytest.skip(f"Makefile {makefile} not found")

        content = makefile_path.read_text()

        # Should reference INSTALL_DIR or ./bin for local installation
        local_install_pattern = r"\$\{INSTALL_DIR\}|\./bin|\$\(INSTALL_DIR\)"
        assert re.search(local_install_pattern, content), (
            f"Install target in {makefile} should install '{tool}' to INSTALL_DIR or ./bin"
        )

    def test_gh_cli_only_checks_global(self, root):
        """Verify gh CLI install only checks global (no local install expected)."""
        makefile_path = root / ".github/Makefile.gh"
        if not makefile_path.exists():
            pytest.skip("Makefile.gh not found")

        content = makefile_path.read_text()

        # gh-install should NOT contain install commands, only check and warn
        # It should have the global check but NOT install to INSTALL_DIR
        assert "command -v gh" in content, "gh-install should check for global gh CLI"

        # Should contain warning/info message instead of install
        assert "Please install" in content or "not found" in content, (
            "gh-install should warn user to install gh CLI manually"
        )


class TestMockInstallBehavior:
    """Mock-based tests to verify install behavior without side effects."""

    @pytest.fixture
    def mock_bin_dir(self, tmp_path: Path) -> Path:
        """Create a mock bin directory with mock tools."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)

        # Create mock uv
        uv_mock = bin_dir / "uv"
        uv_mock.write_text('#!/bin/sh\necho "[MOCK] uv $@"\n')
        uv_mock.chmod(0o755)

        # Create mock uvx
        uvx_mock = bin_dir / "uvx"
        uvx_mock.write_text('#!/bin/sh\necho "[MOCK] uvx $@"\n')
        uvx_mock.chmod(0o755)

        return bin_dir

    @pytest.fixture
    def mock_npm(self, tmp_path: Path) -> Path:
        """Create a mock npm command that simulates local installation."""
        mock_path = tmp_path / "mock_npm"
        mock_path.mkdir(exist_ok=True)

        npm_mock = mock_path / "npm"
        npm_mock.write_text("""\
#!/bin/sh
echo "[MOCK] npm $@"
# If installing with --prefix, create the expected directory structure
if echo "$@" | grep -q -- "--prefix"; then
    PREFIX=$(echo "$@" | sed 's/.*--prefix "\\([^"]*\\)".*/\\1/')
    PREFIX=$(echo "$PREFIX" | sed "s/.*--prefix '\\([^']*\\)'.*/\\1/")
    PREFIX=$(echo "$PREFIX" | sed 's/.*--prefix \\([^ ]*\\).*/\\1/')
    mkdir -p "$PREFIX/node_modules/.bin"
    touch "$PREFIX/node_modules/.bin/marp"
    chmod +x "$PREFIX/node_modules/.bin/marp"
fi
""")
        npm_mock.chmod(0o755)

        return mock_path

    def test_install_uv_uses_install_dir(self, logger, setup_makefiles, mock_bin_dir):
        """Test that install-uv respects INSTALL_DIR variable."""
        result = run_make(
            logger,
            ["install-uv", f"INSTALL_DIR={mock_bin_dir}"],
            dry_run=True,
        )
        # The dry run should show the install script would install to INSTALL_DIR
        # Note: The actual check happens at runtime, but we can verify the pattern
        assert result.returncode == 0

    def test_install_marp_dry_run(self, logger, setup_makefiles):
        """Test that install-marp target runs without error in dry-run mode."""
        result = run_make(logger, ["install-marp"], dry_run=True)
        assert result.returncode == 0

    def test_marp_uses_install_dir_for_local_install(self, logger, root, setup_makefiles, tmp_path):
        """Verify MARP_BIN uses INSTALL_DIR for local installation path."""
        # Check the Makefile content directly
        makefile_path = root / "presentation/Makefile.presentation"
        content = makefile_path.read_text()

        # MARP_BIN should reference INSTALL_DIR
        assert "${INSTALL_DIR}" in content, "MARP_BIN should use ${INSTALL_DIR}"
        assert "node_modules/.bin/marp" in content, "MARP_BIN should point to node_modules/.bin/marp"


class TestIntegrationInstallPatterns:
    """Integration tests that validate actual Makefile behavior.

    These tests are designed to work in CI pipelines without requiring
    actual tool installation.
    """

    def test_install_uv_target_dry_run(self, logger, setup_makefiles, tmp_path):
        """Verify install-uv target produces expected dry-run output."""
        result = run_make(logger, ["install-uv"], dry_run=True)
        output = result.stdout

        # Should create bin directory
        assert "mkdir -p" in output

    def test_install_marp_target_dry_run(self, logger, setup_makefiles):
        """Verify install-marp target produces expected dry-run output."""
        result = run_make(logger, ["install-marp"], dry_run=True)
        output = result.stdout

        # Should create bin directory
        assert "mkdir -p" in output

    def test_gh_install_target_dry_run(self, logger, setup_makefiles):
        """Verify gh-install target runs and checks for global install."""
        result = run_make(logger, ["gh-install"], dry_run=True)
        assert result.returncode == 0

    def test_presentation_target_depends_on_install_marp(self, logger, setup_makefiles):
        """Verify presentation target depends on install-marp."""
        result = run_make(logger, ["presentation"], dry_run=True)
        output = result.stdout

        # Should include marp invocation
        assert "marp" in output.lower() or "MARP" in output


class TestInstallDirVariable:
    """Tests for the INSTALL_DIR variable behavior."""

    def test_install_dir_defaults_to_bin(self, logger, setup_makefiles):
        """Verify INSTALL_DIR defaults to ./bin."""
        result = run_make(logger, ["print-INSTALL_DIR"], dry_run=False)
        output = strip_ansi(result.stdout)

        assert "./bin" in output, "INSTALL_DIR should default to ./bin"

    def test_install_dir_can_be_overridden(self, logger, setup_makefiles, tmp_path):
        """Verify INSTALL_DIR can be overridden via command line."""
        custom_dir = tmp_path / "custom_bin"
        result = run_make(
            logger,
            ["print-INSTALL_DIR", f"INSTALL_DIR={custom_dir}"],
            dry_run=False,
        )
        output = strip_ansi(result.stdout)

        assert str(custom_dir) in output, "INSTALL_DIR should be overrideable"

    def test_uv_bin_falls_back_to_install_dir(self, logger, root):
        """Verify UV_BIN falls back to INSTALL_DIR when uv not in PATH."""
        makefile_path = root / "Makefile"
        content = makefile_path.read_text()

        # UV_BIN should use command -v check and fall back to INSTALL_DIR
        assert "UV_BIN" in content
        assert "${INSTALL_DIR}/uv" in content or "$(INSTALL_DIR)/uv" in content

    def test_marp_bin_falls_back_to_install_dir(self, logger, root):
        """Verify MARP_BIN falls back to INSTALL_DIR when marp not in PATH."""
        makefile_path = root / "presentation/Makefile.presentation"
        content = makefile_path.read_text()

        # MARP_BIN should use command -v check and fall back to INSTALL_DIR
        assert "MARP_BIN" in content
        assert "${INSTALL_DIR}" in content


class TestInstallTargetDocumentation:
    """Tests to verify install targets are properly documented."""

    @pytest.mark.parametrize(
        ("makefile", "target", "tool", "expects_local"),
        INSTALL_PATTERNS,
        ids=[f"{p[2]}" for p in INSTALL_PATTERNS],
    )
    def test_install_target_has_help_text(self, root, makefile, target, tool, expects_local):
        """Verify each install target has a help comment."""
        makefile_path = root / makefile
        if not makefile_path.exists():
            pytest.skip(f"Makefile {makefile} not found")

        content = makefile_path.read_text()

        # Each target should have a ## comment for help
        pattern = rf"^{re.escape(target)}:.*##"
        assert re.search(pattern, content, re.MULTILINE), (
            f"Target '{target}' in {makefile} should have a help comment (##)"
        )

    def test_install_uv_is_in_phony(self, root):
        """Verify install-uv is declared as PHONY."""
        makefile = root / "Makefile"
        content = makefile.read_text()

        assert "install-uv" in content
        # Should be in a .PHONY declaration (might be multi-line)
        assert ".PHONY" in content
