"""Performance benchmarks for Makefile operations.

This file contains benchmarks that measure the performance of key Makefile
operations to detect regressions and ensure acceptable performance.

Uses pytest-benchmark to measure and compare execution times.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess  # nosec B404
import sys

import pytest

# Add test utils to path
tests_root = pathlib.Path(__file__).resolve().parent.parent.parent / ".rhiza" / "tests"
if str(tests_root) not in sys.path:
    sys.path.insert(0, str(tests_root))

from test_utils import MAKE  # noqa: E402

# Test configuration constants
STRESS_TEST_DEFAULT_ITERATIONS = 100
MAKEFILE_VARIABLES = ["PYTHON_VERSION", "UV_BIN", "VENV", "RHIZA_VERSION", "INSTALL_DIR"]


class TestMakefilePerformance:
    """Benchmark tests for Makefile target execution."""

    def test_help_target_performance(self, benchmark, root):
        """Benchmark the help target execution time."""

        def run_help():
            result = subprocess.run([MAKE, "help"], cwd=root, capture_output=True, text=True, check=True)  # nosec B603
            return result

        result = benchmark(run_help)
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_print_variable_performance(self, benchmark, root):
        """Benchmark the print-% target execution time."""

        def run_print():
            result = subprocess.run(
                [MAKE, "print-PYTHON_VERSION"], cwd=root, capture_output=True, text=True, check=True
            )  # nosec B603
            return result

        result = benchmark(run_print)
        assert result.returncode == 0

    def test_dry_run_install_performance(self, benchmark, root):
        """Benchmark dry-run of install target."""

        def run_install_dry():
            result = subprocess.run([MAKE, "-n", "install"], cwd=root, capture_output=True, text=True, check=True)  # nosec B603
            return result

        result = benchmark(run_install_dry)
        assert result.returncode == 0

    def test_makefile_parsing_overhead(self, benchmark, root):
        """Benchmark Makefile parsing overhead with a minimal dry-run target."""

        def run_noop():
            # Use a dry-run of the help target to force Makefile evaluation without executing commands
            result = subprocess.run([MAKE, "-n", "help"], cwd=root, capture_output=True, text=True, check=True)  # nosec B603
            return result

        result = benchmark(run_noop)
        assert result.returncode == 0


class TestFileSystemOperations:
    """Benchmark tests for file system operations used in templates."""

    def test_directory_traversal_performance(self, benchmark, root):
        """Benchmark directory traversal performance."""
        import os

        def traverse_directory():
            count = 0
            # Exclude common artifact and virtual environment directories to keep
            # the benchmark stable and representative of the source tree.
            excluded_dirs = {
                "venv",
                ".venv",
                "__pycache__",
                "_tests",
                ".pytest_cache",
                ".mypy_cache",
                ".tox",
                "build",
                "dist",
            }
            for _root_dir, dirs, files in os.walk(root):
                # Skip hidden directories and known artifact directories
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in excluded_dirs]
                count += len(files)
            return count

        count = benchmark(traverse_directory)
        assert count > 0

    def test_file_reading_performance(self, benchmark, root):
        """Benchmark reading pyproject.toml file."""
        pyproject = root / "pyproject.toml"

        def read_pyproject():
            with open(pyproject, encoding="utf-8") as f:
                content = f.read()
            return len(content)

        size = benchmark(read_pyproject)
        assert size > 0

    def test_multiple_file_checks_performance(self, benchmark, root):
        """Benchmark checking existence of multiple files."""
        files_to_check = [
            "pyproject.toml",
            "README.md",
            "Makefile",
            ".rhiza/rhiza.mk",
            "pytest.ini",
            "ruff.toml",
            ".gitignore",
        ]

        def check_files():
            results = []
            for filename in files_to_check:
                results.append((root / filename).exists())
            return results

        results = benchmark(check_files)
        assert any(results)  # At least some files should exist


class TestSubprocessOverhead:
    """Benchmark tests for subprocess execution overhead."""

    def test_subprocess_creation_overhead(self, benchmark):
        """Benchmark the overhead of creating subprocesses."""

        def run_echo():
            result = subprocess.run(["echo", "test"], capture_output=True, text=True, check=True)  # nosec B603
            return result

        result = benchmark(run_echo)
        assert result.returncode == 0

    @pytest.mark.skipif(
        not pathlib.Path(".git").exists() or not shutil.which("git"), reason="Git repository and git command required"
    )
    def test_git_command_performance(self, benchmark, root):
        """Benchmark git status command performance."""

        def run_git_status():
            result = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True, check=True)  # nosec B603
            return result

        result = benchmark(run_git_status)
        assert result.returncode == 0


@pytest.fixture(scope="module")
def stress_test_iterations():
    """Number of iterations for stress tests."""
    return STRESS_TEST_DEFAULT_ITERATIONS


class TestStressScenarios:
    """Stress tests to verify stability under repeated operations."""

    @pytest.mark.stress
    def test_repeated_help_invocations(self, root, stress_test_iterations):
        """Stress test: Repeatedly invoke help target."""
        failures = 0
        for _i in range(stress_test_iterations):
            result = subprocess.run([MAKE, "help"], cwd=root, capture_output=True, text=True, check=False)  # nosec B603
            if result.returncode != 0:
                failures += 1

        # Allow up to 1% failure rate
        assert failures < stress_test_iterations * 0.01

    @pytest.mark.stress
    def test_concurrent_print_variable_stress(self, root):
        """Stress test: Multiple concurrent print-% invocations."""
        import concurrent.futures

        def print_variable(var):
            result = subprocess.run([MAKE, f"print-{var}"], cwd=root, capture_output=True, text=True, check=False)  # nosec B603
            return result.returncode == 0

        # Run multiple variables concurrently with reduced iterations for deterministic results
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for _ in range(5):  # Reduced iterations to minimize flakiness
                for var in MAKEFILE_VARIABLES:
                    futures.append(executor.submit(print_variable, var))

            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed; this test should be deterministic
        success_rate = sum(results) / len(results)
        assert success_rate == 1.0, f"Expected 100% success but got {success_rate * 100:.1f}%"

    @pytest.mark.stress
    def test_file_system_stress(self, tmp_path, stress_test_iterations):
        """Stress test: Rapid file creation and deletion."""
        test_dir = tmp_path / "stress_test"
        test_dir.mkdir()

        failures = []
        for i in range(stress_test_iterations):
            try:
                # Create a file
                test_file = test_dir / f"test_{i}.txt"
                test_file.write_text(f"Test content {i}")

                # Read it back
                content = test_file.read_text()
                assert f"Test content {i}" in content

                # Delete it
                test_file.unlink()
            except Exception as e:
                failures.append((i, str(e)))

        # Should have very few failures
        if failures:
            failure_details = "; ".join(f"iteration {i}: {msg}" for i, msg in failures[:5])
            assert len(failures) < stress_test_iterations * 0.01, (
                f"Too many failures ({len(failures)}): {failure_details}"
            )
