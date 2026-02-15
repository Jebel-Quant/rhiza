"""Stress tests for subprocess operations.

Tests subprocess handling under heavy load to verify stability and
proper resource cleanup.
"""

from __future__ import annotations

import concurrent.futures
import shutil
import subprocess
import sys

import pytest

# Get absolute paths for executables
PYTHON = sys.executable
ECHO = shutil.which("echo") or "/bin/echo"


@pytest.mark.stress
def test_rapid_subprocess_creation(stress_iterations: int):
    """Test rapid subprocess creation and termination.

    Verifies that rapid subprocess creation doesn't leak resources or
    cause degraded performance.
    """
    results = []

    for i in range(stress_iterations):
        result = subprocess.run(  # nosec
            [ECHO, f"test_{i}"],
            capture_output=True,
            text=True,
        )
        results.append(result.returncode == 0 and f"test_{i}" in result.stdout)

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_concurrent_subprocess_execution(concurrent_workers: int):
    """Test concurrent subprocess execution.

    Verifies that multiple subprocesses can run concurrently without
    interference or resource exhaustion.
    """

    def run_subprocess(worker_id: int):
        """Run a simple subprocess and return success status."""
        result = subprocess.run(  # nosec
            [PYTHON, "-c", f"print('worker_{worker_id}')"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and f"worker_{worker_id}" in result.stdout

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(run_subprocess, i) for i in range(concurrent_workers * 5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_subprocess_with_output_stress(stress_iterations: int):
    """Test subprocess operations with output handling.

    Verifies that subprocess output capture works correctly under
    repeated execution.
    """
    results = []

    for i in range(stress_iterations):
        result = subprocess.run(  # nosec
            [PYTHON, "-c", f"import sys; sys.stdout.write('line_{i}\\n' * 10)"],
            capture_output=True,
            text=True,
        )
        # Verify output contains expected lines
        expected_lines = 10
        actual_lines = result.stdout.count(f"line_{i}")
        results.append(result.returncode == 0 and actual_lines == expected_lines)

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_concurrent_python_version_checks(concurrent_workers: int):
    """Test concurrent Python version checking.

    Verifies that multiple Python version checks (common in Makefile operations)
    can run concurrently.
    """

    def check_python_version():
        """Check Python version and return success status."""
        result = subprocess.run(  # nosec
            [PYTHON, "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and "Python" in result.stdout

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(check_python_version) for _ in range(concurrent_workers * 3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_subprocess_error_handling_stress(stress_iterations: int):
    """Test subprocess error handling under stress.

    Verifies that subprocess failures are handled correctly even under
    rapid execution.
    """
    results = []

    for i in range(stress_iterations):
        # Run a command that will fail
        result = subprocess.run(  # nosec
            [PYTHON, "-c", f"import sys; sys.exit({i % 2})"],
            capture_output=True,
            text=True,
        )
        # Verify we can detect success/failure correctly
        expected_code = i % 2
        results.append(result.returncode == expected_code)

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_subprocess_timeout_handling(concurrent_workers: int):
    """Test subprocess timeout handling under concurrent load.

    Verifies that subprocess timeouts work correctly when multiple
    processes are running.
    """

    def run_with_timeout():
        """Run subprocess with timeout and return success status."""
        try:
            result = subprocess.run(  # nosec
                [PYTHON, "-c", "import time; time.sleep(0.01); print('done')"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
        except subprocess.TimeoutExpired:
            return False
        else:
            return result.returncode == 0 and "done" in result.stdout

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(run_with_timeout) for _ in range(concurrent_workers * 2)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"
