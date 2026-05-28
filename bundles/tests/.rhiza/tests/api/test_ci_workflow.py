"""Tests for the rhiza_ci.yml workflow configuration."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from api.conftest import run_make

MULTI_OS_MATRIX = 'RHIZA_CI_OS_MATRIX=["ubuntu-latest","windows-latest"]'
WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_ci.yml"


def test_ci_os_matrix_make_target_defaults_to_ubuntu_when_env_missing(logger):
    """ci-os-matrix target must default to ubuntu-latest when env value is absent."""
    result = run_make(logger, ["-f", ".rhiza/rhiza.mk", "RHIZA_CI_OS_MATRIX=", "ci-os-matrix"], dry_run=False)
    assert result.returncode == 0
    assert json.loads(result.stdout.strip()) == ["ubuntu-latest"]


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
    pre_commit_cache_step = next(step for step in pre_commit_steps if step.get("name") == "Cache pre-commit environments")
    assert pre_commit_cache_step["with"]["key"] == "${{ runner.os }}-pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}"
