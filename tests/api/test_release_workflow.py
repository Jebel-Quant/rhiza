"""Tests for the rhiza_release.yml workflow configuration.

Validates that the release workflow is correctly defined. CHANGELOG.md is
folded into the version-bump commit by the release process (rhiza-claude
``/release``) before the tag is pushed, so the tagged commit already carries
the changelog and the workflow no longer commits it separately.
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

    @pytest.fixture
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


# ---------------------------------------------------------------------------
# #1537 -- asserted against *both* copies of the release workflow
# ---------------------------------------------------------------------------

# The live workflow is what runs here; the bundle copy is what every `github` consumer
# gets. They are real files rather than symlinks (Actions will not run a symlinked
# workflow), so a fix applied to one and not the other leaves the bug shipped. This is the
# pattern test_release_tag_reachability.py already uses for the same pair.
_RELEASE_WORKFLOWS = [
    Path(".github") / "workflows" / "rhiza_release.yml",
    Path("bundles") / "github" / ".github" / "workflows" / "rhiza_release.yml",
]


def _finalise_condition(root: Path, relative: Path) -> str:
    """Return the ``if`` expression on a release workflow's finalise-release job.

    Args:
        root: Repository root.
        relative: Path to the workflow, relative to the root.

    Returns:
        The condition as written, or the empty string when the job has none.
    """
    workflow = yaml.safe_load((root / relative).read_text(encoding="utf-8"))
    return str(workflow["jobs"]["finalise-release"].get("if", ""))


@pytest.mark.parametrize("relative", _RELEASE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_finalise_release_survives_a_failed_conda_job(root, relative):
    """The condition must name a status function, or the OR inside it is unreachable (#1537).

    GitHub combines a job's own ``if`` with an implicit ``success()`` over every entry in
    ``needs`` **unless** the expression names one of ``always()``, ``cancelled()``,
    ``failure()`` or ``success()``. Without one, the OR is evaluated only in runs where conda
    already succeeded -- so a conda failure skipped ``finalise-release`` however true the OR
    was. Releasing jointview v0.2.0 is the record of it: PyPI published, grayskull 404'd on
    metadata that had not propagated, and the release was stranded as the draft
    ``untagged-547fe31ec1ed6de3ef9b`` holding SBOM and provenance assets nobody could see.

    ``test_finalise_release_includes_conda_signal`` cannot catch this, and that is the point
    worth remembering: an ``if`` naming ``needs.conda.result`` reads as though it handles a
    conda failure, and looks identical whether or not it can ever be reached.
    """
    condition = _finalise_condition(root, relative)
    assert any(fn in condition for fn in ("cancelled()", "always()", "failure()")), (
        f"{relative.as_posix()}: finalise-release's `if` is {condition!r}, which names no "
        f"status function -- so GitHub adds an implicit success() over needs and a failed "
        f"`conda` job skips the release finalisation regardless (#1537)."
    )


@pytest.mark.parametrize("relative", _RELEASE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_finalise_release_is_not_unconditional(root, relative):
    """``always()`` would finalise a release during a run somebody cancelled.

    The counterpart to the test above, and why the fix is ``!cancelled()`` rather than the
    more obvious ``always()``: a cancelled release run is the one case where publishing is
    certainly not wanted, and ``always()`` ignores exactly that.
    """
    condition = _finalise_condition(root, relative)
    assert "always()" not in condition, (
        f"{relative.as_posix()}: finalise-release uses always(), so cancelling a release run "
        f"still publishes the GitHub release. Use `!cancelled()`, which skips on cancellation "
        f"but survives a failed conda job (#1537)."
    )


@pytest.mark.parametrize("relative", _RELEASE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_conda_waits_for_pypi_metadata_to_propagate(root, relative):
    """Grayskull must retry, because PyPI's index lags the upload it just accepted.

    The other half of #1537, and the half that was already fixed before the issue was
    revisited. A first release has no existing PyPI entry to fall back on, so grayskull 404s
    on metadata that appears minutes later. Asserted because a retry loop is exactly the kind
    of thing a later simplification removes as noise -- it reads as defensive clutter until
    the release it protects is the one that fails.
    """
    workflow = yaml.safe_load((root / relative).read_text(encoding="utf-8"))
    commands = "\n".join(_step_commands(workflow["jobs"]["conda"]))
    lost_the_retry = (
        f"{relative.as_posix()}: the conda job no longer retries grayskull. PyPI metadata for "
        f"a just-published version can lag the upload by minutes, and a first release has "
        f"nothing to fall back on (#1537)."
    )
    assert "MAX_ATTEMPTS" in commands, lost_the_retry
    assert "sleep" in commands, lost_the_retry
