"""Tests for the rhiza_release.yml workflow configuration.

Validates that the release workflow is correctly defined. CHANGELOG.md is
folded into the version-bump commit by the rhiza-tools ``bump`` command (via a
git-cliff pre-commit hook), so the tagged commit already carries the changelog
and the workflow no longer commits it separately.
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

    def test_workflow_top_level_permissions_are_read_only(self, workflow):
        """Top-level permissions must stay least-privilege (read-only).

        Write scopes are granted per-job (Scorecard Token-Permissions); the
        workflow must not hand every job write access by default.
        """
        permissions = workflow.get("permissions", {})
        assert permissions.get("contents") == "read", "Top-level contents permission must be read"
        assert "write" not in permissions.values(), f"Top-level permissions must be read-only, got {permissions}"

    def test_workflow_has_no_changelog_commit_job(self, workflow):
        """CHANGELOG.md is folded into the bump commit, not committed by the workflow.

        Guards against reintroducing a separate post-tag changelog commit, which
        would duplicate the entry already carried by the tagged bump commit.
        """
        jobs = workflow.get("jobs", {})
        assert "update-changelog" not in jobs, "update-changelog job must not be reintroduced"
        for name, job in jobs.items():
            commands = "\n".join(_step_commands(job))
            assert "git-cliff --output CHANGELOG.md" not in commands, (
                f"job '{name}' must not regenerate and commit CHANGELOG.md"
            )

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

    def test_sbom_attestation_is_staged_as_release_signature(self, workflow):
        """Non-buildable repos must still ship a recognised signature asset.

        Repos without a ``[build-system]`` produce no ``dist/*.intoto.jsonl``
        provenance, so the SBOM's Sigstore attestation bundle is staged as a
        ``*.sigstore.json`` release asset to satisfy OpenSSF Scorecard's
        Signed-Releases check.
        """
        build_job = workflow["jobs"]["build"]
        steps = build_job.get("steps", [])
        attest_step = next((s for s in steps if s.get("name") == "Attest SBOM"), None)
        assert attest_step is not None, "Attest SBOM step must exist"
        assert attest_step.get("id") == "attest-sbom", "Attest SBOM step needs an id to reference its bundle"

        commands = "\n".join(_step_commands(build_job))
        assert "steps.attest-sbom.outputs.bundle-path" in commands
        assert "sbom.cdx.json.sigstore.json" in commands

        upload_step = next((s for s in steps if s.get("name") == "Upload SBOM artifacts"), None)
        assert upload_step is not None, "Upload SBOM artifacts step must exist"
        assert "sbom.cdx.json.sigstore.json" in upload_step["with"]["path"]

    def test_pypi_publish_strips_provenance_bundle(self, workflow):
        """PyPI upload must remove the provenance bundle from ``dist/`` first."""
        pypi_job = workflow["jobs"]["pypi"]
        steps = pypi_job.get("steps", [])

        cleanup_step = next((s for s in steps if s.get("name") == "Remove non-distribution files before publish"), None)
        assert cleanup_step is not None, "PyPI job must remove non-distribution files before publish"
        assert cleanup_step.get("if") == "${{ steps.check_dist.outputs.should_publish == 'true' }}"
        assert cleanup_step.get("run") == "rm -f dist/*.intoto.jsonl"
