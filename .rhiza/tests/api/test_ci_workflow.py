"""Tests for the rhiza_ci.yml workflow configuration."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_ci.yml"


def _load_workflow(root: Path) -> dict:
    """Load and parse the CI workflow YAML file."""
    workflow_file = root / WORKFLOW_PATH
    if not workflow_file.exists():
        pytest.fail(f"Workflow file not found: {workflow_file}")
    with open(workflow_file) as fh:
        return yaml.safe_load(fh)


def test_ci_workflow_uses_generated_os_matrix(root):
    """CI test job must read its OS matrix from generate-matrix job output."""
    workflow = _load_workflow(root)
    test_job = workflow["jobs"]["test"]
    matrix = test_job["strategy"]["matrix"]
    assert matrix["os"] == "${{ fromJson(needs.generate-matrix.outputs.os_matrix) }}"


def test_ci_workflow_defines_os_matrix_output(root):
    """generate-matrix job must expose an os_matrix output from the os step."""
    workflow = _load_workflow(root)
    outputs = workflow["jobs"]["generate-matrix"]["outputs"]
    assert outputs["os_matrix"] == "${{ steps.os.outputs.list }}"


def test_ci_workflow_os_matrix_defaults_to_ubuntu(root):
    """OS matrix generation must default to Ubuntu when env config is unset."""
    workflow = _load_workflow(root)
    steps = workflow["jobs"]["generate-matrix"]["steps"]
    os_step = next(step for step in steps if step.get("id") == "os")
    run = os_step["run"]
    assert "RHIZA_CI_OS_MATRIX" in run
    assert "ubuntu-latest" in run
