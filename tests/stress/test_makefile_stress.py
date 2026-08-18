"""Stress tests for Makefile operations.

Tests Makefile operations under concurrent load and repeated execution
to verify stability and detect resource leaks.
"""

from __future__ import annotations

import concurrent.futures
import shutil
import subprocess  # nosec B404
from pathlib import Path

import pytest

# Get absolute paths for executables
MAKE = shutil.which("make") or "/usr/bin/make"

# `make help` under the rhiza-task shim prints the CLI's task table and then the
# repo-owned targets the CLI cannot know about. This marker sits between the two, so
# matching it proves the delegation *and* the local half ran. The old assertion looked
# for "Usage:", the make layer's own banner, which no longer exists.
_HELP_MARKER = "Repo-owned targets"


@pytest.mark.stress
def test_concurrent_help_invocations(root: Path, concurrent_workers: int):
    """Test concurrent invocations of make help.

    Verifies that multiple simultaneous help invocations don't cause
    race conditions or resource conflicts.
    """

    def run_help():
        """Run make help and return success status."""
        result = subprocess.run(  # nosec
            [MAKE, "help"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and _HELP_MARKER in result.stdout

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(run_help) for _ in range(concurrent_workers * 2)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_repeated_help_executions(root: Path, stress_iterations: int):
    """Test repeated executions of make help.

    Verifies that repeated help invocations don't leak resources or
    cause degraded performance over time.
    """
    results = []

    for _ in range(stress_iterations):
        result = subprocess.run(  # nosec
            [MAKE, "help"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        results.append(result.returncode == 0 and _HELP_MARKER in result.stdout)

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_concurrent_dry_run_operations(root: Path, concurrent_workers: int):
    """Test concurrent dry-run operations.

    Verifies that multiple dry-run operations can execute concurrently
    without conflicts.
    """

    def run_dry_run(target: str):
        """Run make target in dry-run mode and return success status."""
        result = subprocess.run(  # nosec
            [MAKE, "-n", target],
            cwd=root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    # Test multiple targets concurrently
    targets = ["install", "test", "fmt", "clean"] * (concurrent_workers // 4 + 1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(run_dry_run, target) for target in targets[: concurrent_workers * 2]]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_rapid_makefile_parsing(root: Path, stress_iterations: int):
    """Test rapid Makefile parsing operations.

    Verifies that Makefile parsing doesn't degrade with repeated invocations.
    """
    results = []

    for _ in range(stress_iterations):
        result = subprocess.run(  # nosec
            [MAKE, "-n", "-p"],  # Print database (parsed Makefile)
            cwd=root,
            capture_output=True,
            text=True,
        )
        results.append(result.returncode == 0)

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_concurrent_variable_printing(root: Path, concurrent_workers: int):
    """Test concurrent Makefile variable printing.

    Verifies that multiple variable print operations can run concurrently
    without corruption or conflicts. Uses only guaranteed-to-exist variables.
    """

    def print_variable(setting: str):
        """Print one resolved setting and return success status."""
        result = subprocess.run(  # nosec
            [MAKE, "--no-print-directory", setting],
            cwd=root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    # `make print-VAR` was a pattern rule in the retired make layer; the CLI exposes a
    # `print` subcommand instead, and the shim has no pattern rule that would reach it with
    # an argument. `todos` stands in: a real target, cheap, read-only, and routed through the
    # `%:` catch-all, so it exercises the same concurrent delegation path.
    variables = ["todos"] * concurrent_workers

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(print_variable, var) for var in variables]
        results = [f.result(timeout=30) for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"
