"""Shared fixtures and helpers for sync tests.

Provides environment setup for template sync, workflow versioning,
and content validation tests.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess  # nosec
from pathlib import Path

import pytest

# Get absolute paths for executables to avoid S607 warnings
GIT = shutil.which("git") or "/usr/bin/git"
MAKE = shutil.which("make") or "/usr/bin/make"


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def run_make(
    logger, args: list[str] | None = None, check: bool = True, dry_run: bool = True, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    """Run `make` with optional arguments and return the completed process.

    Args:
        logger: Logger used to emit diagnostic messages during the run
        args: Additional arguments for make
        check: If True, raise on non-zero return code
        dry_run: If True, use -n to avoid executing commands
        env: Optional environment variables to pass to the subprocess
    """
    cmd = [MAKE]
    if args:
        cmd.extend(args)
    # Use -s to reduce noise, -n to avoid executing commands
    flags = "-sn" if dry_run else "-s"
    cmd.insert(1, flags)
    logger.info("Running command: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)  # nosec B603
    logger.debug("make exited with code %d", result.returncode)
    if result.stdout:
        logger.debug("make stdout (truncated to 500 chars):\n%s", result.stdout[:500])
    if result.stderr:
        logger.debug("make stderr (truncated to 500 chars):\n%s", result.stderr[:500])
    if check and result.returncode != 0:
        msg = f"make failed with code {result.returncode}:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        raise AssertionError(msg)
    return result


def setup_rhiza_git_repo():
    """Initialize a git repository and set remote to rhiza."""
    subprocess.run([GIT, "init"], check=True, capture_output=True)  # nosec B603
    subprocess.run(  # nosec B603
        [GIT, "remote", "add", "origin", "https://github.com/jebel-quant/rhiza"],
        check=True,
        capture_output=True,
    )


@pytest.fixture(autouse=True)
def setup_sync_env(logger, root, tmp_path: Path):
    """Set up a temporary environment for sync tests with Makefile, templates, and git.

    This fixture creates a complete test environment with:
    - Makefile and rhiza.mk configuration
    - .rhiza-version file and .env configuration
    - template.yml and pyproject.toml
    - Initialized git repository (configured as rhiza origin)
    - src/ and tests/ directories to satisfy validate target
    """
    logger.debug("Setting up sync test environment: %s", tmp_path)

    # Copy the main Makefile into the temporary working directory
    shutil.copy(root / "Makefile", tmp_path / "Makefile")

    # Copy core Rhiza Makefiles and version file
    (tmp_path / ".rhiza").mkdir(exist_ok=True)
    shutil.copy(root / ".rhiza" / "rhiza.mk", tmp_path / ".rhiza" / "rhiza.mk")

    # Copy .rhiza-version if it exists
    if (root / ".rhiza" / ".rhiza-version").exists():
        shutil.copy(root / ".rhiza" / ".rhiza-version", tmp_path / ".rhiza" / ".rhiza-version")

    # Create a minimal, deterministic .rhiza/.env for tests
    env_content = "SCRIPTS_FOLDER=.rhiza/scripts\nCUSTOM_SCRIPTS_FOLDER=.rhiza/customisations/scripts\n"
    (tmp_path / ".rhiza" / ".env").write_text(env_content)

    logger.debug("Copied Makefile from %s to %s", root / "Makefile", tmp_path / "Makefile")

    # Create a minimal .rhiza/template.yml
    (tmp_path / ".rhiza" / "template.yml").write_text("repository: Jebel-Quant/rhiza\nref: main\n")

    # Sort out pyproject.toml
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')

    # Move into tmp directory for isolation
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    logger.debug("Changed working directory to %s", tmp_path)

    # Initialize a git repo so that commands checking for it (like materialize) don't fail validation
    setup_rhiza_git_repo()

    # Create src and tests directories to satisfy validate
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "tests").mkdir(exist_ok=True)

    try:
        yield
    finally:
        os.chdir(old_cwd)
        logger.debug("Restored working directory to %s", old_cwd)
