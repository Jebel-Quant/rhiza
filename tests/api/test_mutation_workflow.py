"""Tests for the rhiza_mutation.yml workflow badge publishing configuration."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_mutation.yml"


def _load_workflow(root: Path) -> dict:
    """Load and parse the mutation workflow YAML file."""
    workflow_file = root / WORKFLOW_PATH
    if not workflow_file.exists():
        pytest.fail(f"Workflow file not found: {workflow_file}")
    with open(workflow_file, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _step_names(job: dict) -> list[str]:
    """Return all step names from a job."""
    return [step.get("name", "") for step in job.get("steps", [])]


class TestMutationWorkflowStructure:
    """Validate badge generation and publishing in rhiza_mutation.yml."""

    @pytest.fixture(scope="class")
    def workflow(self, root: Path) -> dict:
        """Return parsed workflow data."""
        return _load_workflow(root)

    def test_workflow_file_exists(self, root: Path) -> None:
        """Workflow file must exist at the expected path."""
        assert (root / WORKFLOW_PATH).exists()

    def test_workflow_has_expected_jobs(self, workflow: dict) -> None:
        """Workflow must keep mutation and badge publishing jobs."""
        jobs = workflow.get("jobs", {})
        assert {"mutation", "publish-mutation-badge"}.issubset(set(jobs))

    def test_mutation_job_is_opt_in(self, workflow: dict) -> None:
        """Mutation testing is very optional: the job is gated on MUTATION_ENABLED.

        The whole mutation job only runs when the downstream repo sets the
        `MUTATION_ENABLED` repository variable to 'true'; otherwise it skips
        cleanly so repos are never forced into a mutation gate.
        """
        mutation_job = workflow["jobs"]["mutation"]
        assert "MUTATION_ENABLED" in str(mutation_job.get("if", "")), (
            "mutation job must be gated on the MUTATION_ENABLED repository variable (opt-in)"
        )

    def test_mutation_job_uploads_badge_artifact(self, workflow: dict) -> None:
        """Mutation job must publish the computed badge as an artifact."""
        mutation_job = workflow["jobs"]["mutation"]
        names = _step_names(mutation_job)
        assert "Generate mutation badge" in names
        assert "Upload mutation badge" in names
        assert "Enforce mutation gate" in names

    def test_publish_job_uses_pages_permissions(self, workflow: dict) -> None:
        """Publish job must have explicit GitHub Pages deployment permissions."""
        publish_job = workflow["jobs"]["publish-mutation-badge"]
        permissions = publish_job.get("permissions", {})
        assert permissions.get("pages") == "write"
        assert permissions.get("id-token") == "write"
        assert permissions.get("contents") == "read"

    def test_publish_job_deploys_pages_artifact(self, workflow: dict) -> None:
        """Publish job must upload and deploy the companion book artifact."""
        publish_job = workflow["jobs"]["publish-mutation-badge"]
        uses_values = [step["uses"] for step in publish_job.get("steps", []) if "uses" in step]
        assert any("actions/upload-pages-artifact@" in item for item in uses_values)
        assert any("actions/deploy-pages@" in item for item in uses_values)

    def test_workflow_documents_badge_url(self, root: Path) -> None:
        """Workflow comments should document the stable mutation badge path."""
        content = (root / WORKFLOW_PATH).read_text(encoding="utf-8")
        assert "mutation-badge.svg" in content
