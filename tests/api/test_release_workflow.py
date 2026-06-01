"""Tests for the rhiza_release.yml workflow configuration.

Validates that the release workflow is correctly defined, including the
update-changelog job that generates and commits CHANGELOG.md on every release.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_release.yml"
EXPECTED_JOBS = {
    "tag",
    "build",
    "draft-release",
    "update-changelog",
    "pypi",
    "conda",
    "devcontainer",
    "finalise-release",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_workflow(root: Path) -> dict:
    """Load and parse the release workflow YAML file."""
    workflow_file = root / WORKFLOW_PATH
    if not workflow_file.exists():
        pytest.fail(f"Workflow file not found: {workflow_file}")
    with open(workflow_file, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _step_commands(job: dict) -> list[str]:
    """Return all ``run`` strings from a job's steps."""
    return [step["run"] for step in job.get("steps", []) if "run" in step]


def _step_uses(job: dict) -> list[str]:
    """Return all ``uses`` strings from a job's steps."""
    return [step["uses"] for step in job.get("steps", []) if "uses" in step]


# ---------------------------------------------------------------------------
# Structure tests — validate the YAML content of rhiza_release.yml
# ---------------------------------------------------------------------------


class TestReleaseWorkflowStructure:
    """Validate the static content of rhiza_release.yml."""

    @pytest.fixture(scope="class")
    def workflow(self, root):
        """Load and return the parsed release workflow YAML."""
        return _load_workflow(root)

    def test_workflow_file_exists(self, root):
        """Workflow file must exist at the expected path."""
        assert (root / WORKFLOW_PATH).exists()

    def test_workflow_triggers_on_version_tags(self, workflow):
        """Workflow must trigger on version tags (v*)."""
        triggers = workflow.get("on") or workflow.get(True) or {}
        push = triggers.get("push", {})
        tags = push.get("tags", [])
        assert any("v*" in tag for tag in tags), "Workflow must trigger on v* tags"

    def test_workflow_has_contents_write_permission(self, workflow):
        """Workflow must have contents: write permission to push CHANGELOG.md."""
        permissions = workflow.get("permissions", {})
        assert permissions.get("contents") == "write", "Workflow must have contents: write permission"

    def test_workflow_contains_expected_jobs(self, workflow):
        """Workflow should keep the expected release job structure."""
        jobs = workflow.get("jobs", {})
        assert EXPECTED_JOBS.issubset(set(jobs)), "Release workflow is missing expected jobs"

    def test_conda_job_depends_on_pypi(self, workflow):
        """Conda recipe generation should only run after PyPI publish decision."""
        conda_job = workflow["jobs"]["conda"]
        assert "pypi" in conda_job.get("needs", []), "Conda job must depend on pypi job output"
        commands = "\n".join(_step_commands(conda_job))
        assert "PUBLISH_CONDA" in commands
        assert "needs.pypi.outputs.should_publish" in commands
        assert "grayskull pypi" in commands

    def test_finalise_release_includes_conda_signal(self, workflow):
        """Final release gating should account for conda recipe generation."""
        finalise_job = workflow["jobs"]["finalise-release"]
        assert "conda" in finalise_job.get("needs", [])
        assert "needs.conda.result == 'success'" in str(finalise_job.get("if", ""))
