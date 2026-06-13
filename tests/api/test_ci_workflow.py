"""Tests for the rhiza_ci.yml workflow configuration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

from tests.util import run_make

MULTI_OS_MATRIX = 'RHIZA_CI_OS_MATRIX=["ubuntu-latest","windows-latest"]'
WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_ci.yml"

# ci-os-matrix relies on `printf` from a POSIX shell; MinGW make on Windows
# doesn't reproduce the same stdout, and JSON quoting in make variable
# assignments is incompatible with cmd.exe expansion.
_skip_on_windows = pytest.mark.skipif(
    sys.platform == "win32", reason="ci-os-matrix requires a POSIX shell (not available on Windows)"
)


@_skip_on_windows
def test_ci_os_matrix_make_target_defaults_to_ubuntu_when_env_missing(logger):
    """ci-os-matrix target must default to ubuntu-latest when env value is absent."""
    result = run_make(logger, ["-f", ".rhiza/rhiza.mk", "RHIZA_CI_OS_MATRIX=", "ci-os-matrix"], dry_run=False)
    assert result.returncode == 0
    assert json.loads(result.stdout.strip()) == ["ubuntu-latest"]


@_skip_on_windows
def test_ci_os_matrix_make_target_can_be_configured(logger):
    """ci-os-matrix target must use the configured RHIZA_CI_OS_MATRIX value."""
    result = run_make(
        logger,
        ["-f", ".rhiza/rhiza.mk", MULTI_OS_MATRIX, "ci-os-matrix"],
        dry_run=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout.strip()) == ["ubuntu-latest", "windows-latest"]


def test_ci_security_job_runs_stale_suppression_gate(root):
    """CI security job must fail on stale # nosec CVE suppressions."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    security_job = workflow["jobs"]["security"]
    run_steps = [step.get("run", "") for step in security_job.get("steps", [])]

    assert any("make security" in run for run in run_steps)
    assert any("--fail-stale-nosec-cve" in run for run in run_steps)


def test_ci_jobs_define_timeout_budgets(root):
    """CI jobs must define explicit timeout budgets."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    jobs = workflow["jobs"]
    expected = {
        "generate-matrix": 5,
        "test": 20,
        "lowest-deps": 20,
        "typecheck": 5,
        "deptry": 5,
        "pre-commit": 5,
        "docs-coverage": 10,
        "validation": 5,
        "security": 10,
        "license": 10,
    }

    for job_name, timeout in expected.items():
        assert jobs[job_name]["timeout-minutes"] == timeout


def test_ci_cache_keys_match_audit_policy(root):
    """CI cache keys must follow the documented shared key format."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    test_steps = workflow["jobs"]["test"]["steps"]
    uv_cache_step = next(step for step in test_steps if step.get("name") == "Cache uv artifacts")
    assert uv_cache_step["with"]["key"] == "${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}"

    pre_commit_steps = workflow["jobs"]["pre-commit"]["steps"]
    pre_commit_cache_step = next(
        step for step in pre_commit_steps if step.get("name") == "Cache pre-commit environments"
    )
    assert (
        pre_commit_cache_step["with"]["key"]
        == "${{ runner.os }}-pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}"
    )


def test_ci_test_job_runs_make_under_bash(root):
    """CI test job must run make under bash for Windows compatibility."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    run_tests_step = next(step for step in workflow["jobs"]["test"]["steps"] if step.get("name") == "Run tests")
    assert run_tests_step["shell"] == "bash"
    assert "make test" in run_tests_step["run"]


def test_ci_workflow_header_documents_classifier_driven_matrix(root):
    """CI workflow header must document that Python classifiers drive the matrix."""
    content = (root / WORKFLOW_PATH).read_text(encoding="utf-8")
    assert "Programming Language :: Python :: 3.x" in content
    assert "Adding/removing classifiers updates CI Python coverage automatically" in content
