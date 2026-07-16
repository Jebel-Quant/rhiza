"""Tests for the benchmark Makefile target and its resilience.

Mirrors test_marimo_targets.py: the tests bundle ships the ``benchmark`` target
in .rhiza/make.d/test.mk (and the benchmarks bundle ships the pytest-benchmark
suite that target runs), so this exercises the target end-to-end against a synced
repo rather than relying solely on static bundle-content checks.
"""

import shutil
import subprocess  # nosec

import pytest

MAKE = shutil.which("make") or "/usr/bin/make"


@pytest.fixture
def test_makefile(git_repo):
    """Return the test.mk path (home of the benchmark target) or skip if missing."""
    makefile = git_repo / ".rhiza" / "make.d" / "test.mk"
    if not makefile.exists():
        pytest.skip("test.mk not found, skipping test")
    return makefile


def test_benchmark_target_defined(git_repo, test_makefile):
    """The benchmark target must be defined and dry-run cleanly.

    The recipe guards internally on ${TESTS_FOLDER}/benchmarks existing, so a
    dry-run (-n) verifies make can resolve the target (and its 'install'
    prerequisite) without installing pytest-benchmark or running benchmarks.
    """
    result = subprocess.run([MAKE, "-n", "benchmark"], cwd=git_repo, capture_output=True, text=True)  # nosec
    assert "no rule to make target" not in result.stderr.lower(), (
        "Target benchmark should be defined in .rhiza/make.d/test.mk"
    )
    assert result.returncode == 0, f"Dry-run of benchmark failed: {result.stderr}"


def test_benchmark_is_phony(test_makefile):
    """test.mk must declare benchmark as a .PHONY target."""
    content = test_makefile.read_text()

    phony_targets = set()
    for line in content.splitlines():
        if line.startswith(".PHONY:"):
            phony_targets.update(line.split(":", 1)[1].strip().split())

    assert "benchmark" in phony_targets, f"benchmark should be declared .PHONY, got {phony_targets}"


def test_benchmark_depends_on_install(test_makefile):
    """The benchmark target must depend on 'install' so the venv is ready before use."""
    content = test_makefile.read_text()
    assert "benchmark:: install" in content, "benchmark should declare 'install' as a prerequisite"


def test_benchmark_recipe_drives_pytest_benchmark(test_makefile):
    """The recipe must guard on the benchmarks folder and drive pytest-benchmark."""
    content = test_makefile.read_text()
    assert "${TESTS_FOLDER}/benchmarks" in content, (
        "benchmark recipe should guard on the configurable benchmarks folder existing"
    )
    assert "--benchmark-only" in content, "benchmark recipe should run pytest in --benchmark-only mode"
    assert "--benchmark-json" in content, "benchmark recipe should emit a JSON results file for reporting"
