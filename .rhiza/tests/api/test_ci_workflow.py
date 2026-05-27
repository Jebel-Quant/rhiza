"""Tests for the rhiza_ci.yml workflow configuration."""

from __future__ import annotations

import json
from pathlib import Path

from api.conftest import run_make
import yaml

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
