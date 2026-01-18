"""Tests for .github/workflows/rhiza_sync.yml workflow validation.

This file validates that the rhiza_sync.yml workflow uses the correct patterns
for reading and using the RHIZA_VERSION from .rhiza/.rhiza-version.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


class TestRhizaSyncWorkflow:
    """Tests for the rhiza_sync.yml workflow file."""

    @pytest.fixture
    def workflow_file(self, root):
        """Load the rhiza_sync.yml workflow file."""
        workflow_path = root / ".github" / "workflows" / "rhiza_sync.yml"
        if not workflow_path.exists():
            pytest.skip("rhiza_sync.yml workflow not found")
        return workflow_path

    def test_workflow_exists(self, workflow_file):
        """The rhiza_sync.yml workflow should exist."""
        assert workflow_file.exists()
        assert workflow_file.is_file()

    def test_workflow_has_get_rhiza_version_step(self, workflow_file):
        """The workflow should have a step to get the Rhiza version."""
        content = workflow_file.read_text()
        workflow = yaml.safe_load(content)

        # Find the sync job
        sync_job = workflow.get("jobs", {}).get("sync", {})
        steps = sync_job.get("steps", [])

        # Look for the "Get Rhiza version" step
        version_step = None
        for step in steps:
            if step.get("name") == "Get Rhiza version":
                version_step = step
                break

        assert version_step is not None, "Get Rhiza version step not found"
        assert "rhiza-version" in version_step.get("id", "")

    def test_workflow_reads_version_from_file(self, workflow_file):
        """The workflow should read the version from .rhiza/.rhiza-version."""
        content = workflow_file.read_text()

        # Check that the workflow reads from .rhiza/.rhiza-version
        assert ".rhiza/.rhiza-version" in content
        # Check for the fallback pattern
        assert "cat .rhiza/.rhiza-version 2>/dev/null || echo" in content

    def test_workflow_uses_version_variable(self, workflow_file):
        """The workflow should use the version from the rhiza-version step."""
        content = workflow_file.read_text()
        workflow = yaml.safe_load(content)

        sync_job = workflow.get("jobs", {}).get("sync", {})
        steps = sync_job.get("steps", [])

        # Find the sync template step
        sync_step = None
        for step in steps:
            if step.get("name") == "Sync template":
                sync_step = step
                break

        assert sync_step is not None, "Sync template step not found"

        # Check that the step uses the rhiza-version output
        run_script = sync_step.get("run", "")
        assert "steps.rhiza-version.outputs.version" in run_script
        assert "RHIZA_VERSION=" in run_script

    def test_workflow_uses_version_in_uvx_command(self, workflow_file):
        """The workflow should use the version variable in uvx commands."""
        content = workflow_file.read_text()

        # Check that uvx uses the version variable
        assert 'uvx "rhiza>=' in content or "uvx \"rhiza>=" in content
        assert "${RHIZA_VERSION}" in content or "${{ steps.rhiza-version.outputs.version }}" in content

    def test_workflow_generates_pr_description(self, workflow_file):
        """The workflow should generate a PR description using rhiza summarise."""
        content = workflow_file.read_text()
        workflow = yaml.safe_load(content)

        sync_job = workflow.get("jobs", {}).get("sync", {})
        steps = sync_job.get("steps", [])

        # Find the sync template step
        sync_step = None
        for step in steps:
            if step.get("name") == "Sync template":
                sync_step = step
                break

        assert sync_step is not None

        run_script = sync_step.get("run", "")
        # Check that summarise is called with --output pr-description.md
        assert "summarise" in run_script
        assert "pr-description.md" in run_script

    def test_workflow_uses_pr_description_file(self, workflow_file):
        """The workflow should use the pr-description.md file as PR body."""
        content = workflow_file.read_text()
        workflow = yaml.safe_load(content)

        # Find the create pull request step
        steps = workflow.get("jobs", {}).get("sync", {}).get("steps", [])
        pr_step = None
        for step in steps:
            if step.get("name") == "Create pull request":
                pr_step = step
                break

        assert pr_step is not None, "Create pull request step not found"

        # Check that it uses body-path instead of body
        with_params = pr_step.get("with", {})
        assert "body-path" in with_params
        assert with_params.get("body-path") == "pr-description.md"
        # Ensure old static body is not used
        assert "body" not in with_params or with_params.get("body") == ""

    def test_workflow_version_fallback_to_0_9_0(self, workflow_file):
        """The workflow should fallback to version 0.9.0 if file doesn't exist."""
        content = workflow_file.read_text()

        # Check for the fallback pattern with 0.9.0
        assert 'echo "0.9.0"' in content or "echo '0.9.0'" in content

    def test_workflow_sync_uses_materialize_force(self, workflow_file):
        """The workflow should use 'materialize --force' command."""
        content = workflow_file.read_text()

        # Check that materialize --force is used
        assert "materialize --force" in content

    def test_workflow_runs_on_schedule_and_dispatch(self, workflow_file):
        """The workflow should run on schedule and workflow_dispatch."""
        content = workflow_file.read_text()
        workflow = yaml.safe_load(content)

        triggers = workflow.get("on", {})
        assert "workflow_dispatch" in triggers
        assert "schedule" in triggers


class TestRhizaSyncWorkflowConsistency:
    """Tests for consistency between workflow and Makefile."""

    def test_workflow_and_makefile_use_same_version_file(self, root):
        """Both workflow and Makefile should read from .rhiza/.rhiza-version."""
        workflow_path = root / ".github" / "workflows" / "rhiza_sync.yml"
        makefile_path = root / ".rhiza" / "rhiza.mk"

        if not workflow_path.exists():
            pytest.skip("rhiza_sync.yml workflow not found")

        workflow_content = workflow_path.read_text()
        makefile_content = makefile_path.read_text()

        # Both should reference .rhiza/.rhiza-version
        assert ".rhiza/.rhiza-version" in workflow_content
        assert ".rhiza/.rhiza-version" in makefile_content

    def test_workflow_and_makefile_use_same_fallback_version(self, root):
        """Both workflow and Makefile should fallback to 0.9.0."""
        workflow_path = root / ".github" / "workflows" / "rhiza_sync.yml"
        makefile_path = root / ".rhiza" / "rhiza.mk"

        if not workflow_path.exists():
            pytest.skip("rhiza_sync.yml workflow not found")

        workflow_content = workflow_path.read_text()
        makefile_content = makefile_path.read_text()

        # Both should have 0.9.0 as fallback
        assert "0.9.0" in workflow_content
        assert "0.9.0" in makefile_content

    def test_workflow_and_makefile_use_same_rhiza_command_pattern(self, root):
        """Both should use 'rhiza>={VERSION}' pattern."""
        workflow_path = root / ".github" / "workflows" / "rhiza_sync.yml"
        makefile_path = root / ".rhiza" / "rhiza.mk"

        if not workflow_path.exists():
            pytest.skip("rhiza_sync.yml workflow not found")

        workflow_content = workflow_path.read_text()
        makefile_content = makefile_path.read_text()

        # Both should use rhiza>=VERSION pattern
        assert "rhiza>=" in workflow_content
        assert "rhiza>=" in makefile_content
