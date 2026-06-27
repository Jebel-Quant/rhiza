"""Hygiene tests for platform-overlay bundle stubs.

Platform-overlay bundles pair a *feature* (tests, book, marimo, docker,
devcontainer, paper) with a *platform* (GitHub or GitLab).  Each overlay ships
the CI workflow file(s) that wire that feature into that platform's CI system,
while the feature bundle itself stays local-first (no hosted workflow files).

Feature bundles and GitHub helper targets are exercised elsewhere
(``tests/api/test_workflow_stubs.py``, ``.rhiza/tests/api/test_github_targets.py``),
but the overlay stubs themselves are only thinly verified.  These tests assert,
per overlay, that it composes its feature + platform correctly:

- the bundle is declared in template-bundles.yml and ``requires`` exactly its
  feature bundle and its platform bundle,
- it ships the expected workflow file(s) under the platform-specific workflows
  directory and ships nothing under the *other* platform's directory, and
- the workflow wires the feature to the platform the right way: GitHub overlays
  delegate to the matching ``jebel-quant/rhiza`` reusable workflow via a
  job-level ``uses:``; GitLab overlays inline the pipeline as runnable jobs.

These tests describe rhiza's own ``bundles/<overlay>/`` layout, which downstream
projects never receive, so they live in ``tests/`` rather than ``.rhiza/tests/``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

# Prefix every GitHub reusable-workflow stub must call to delegate to this repo.
_REUSABLE_WORKFLOW_PREFIX = "jebel-quant/rhiza/.github/workflows/"


@dataclass(frozen=True)
class OverlaySpec:
    """Expected composition of a single platform-overlay bundle.

    Attributes:
        bundle: The overlay bundle name (e.g. ``github-tests``).
        platform: The platform bundle it overlays (``github`` or ``gitlab``).
        feature: The feature bundle it overlays (e.g. ``tests``).
        workflows: Workflow file basenames the overlay must ship.
        feature_workflows: For GitHub overlays, the reusable feature workflows
            each shipped workflow must delegate to (basename, without path).
            Empty for GitLab overlays, which inline their pipeline.
    """

    bundle: str
    platform: str
    feature: str
    workflows: tuple[str, ...]
    feature_workflows: tuple[str, ...] = ()


# The platform-specific directory each platform's overlays write workflows into.
_WORKFLOW_DIR = {
    "github": Path(".github") / "workflows",
    "gitlab": Path(".gitlab") / "workflows",
}

# Authoritative expectation for every overlay bundle.  Grounded in the actual
# contents of bundles/<overlay>/ as of this commit; update alongside the bundles.
_OVERLAYS: tuple[OverlaySpec, ...] = (
    OverlaySpec(
        bundle="github-tests",
        platform="github",
        feature="tests",
        workflows=("rhiza_ci.yml", "rhiza_codeql.yml", "rhiza_mutation.yml", "rhiza_benchmark.yml"),
        feature_workflows=("rhiza_ci.yml", "rhiza_codeql.yml", "rhiza_mutation.yml", "rhiza_benchmark.yml"),
    ),
    OverlaySpec(
        bundle="github-book",
        platform="github",
        feature="book",
        workflows=("rhiza_book.yml",),
        feature_workflows=("rhiza_book.yml",),
    ),
    OverlaySpec(
        bundle="github-marimo",
        platform="github",
        feature="marimo",
        workflows=("rhiza_marimo.yml",),
        feature_workflows=("rhiza_marimo.yml",),
    ),
    OverlaySpec(
        bundle="github-docker",
        platform="github",
        feature="docker",
        workflows=("rhiza_docker.yml",),
        feature_workflows=("rhiza_docker.yml",),
    ),
    OverlaySpec(
        bundle="github-devcontainer",
        platform="github",
        feature="devcontainer",
        workflows=("rhiza_devcontainer.yml",),
        feature_workflows=("rhiza_devcontainer.yml",),
    ),
    OverlaySpec(
        bundle="github-paper",
        platform="github",
        feature="paper",
        workflows=("rhiza_paper.yml",),
        feature_workflows=("rhiza_paper.yml",),
    ),
    OverlaySpec(
        bundle="gitlab-tests",
        platform="gitlab",
        feature="tests",
        workflows=("rhiza_ci.yml",),
    ),
    OverlaySpec(
        bundle="gitlab-book",
        platform="gitlab",
        feature="book",
        workflows=("rhiza_book.yml",),
    ),
    OverlaySpec(
        bundle="gitlab-marimo",
        platform="gitlab",
        feature="marimo",
        workflows=("rhiza_marimo.yml",),
    ),
)

_OVERLAY_IDS = tuple(spec.bundle for spec in _OVERLAYS)


@pytest.fixture(scope="module")
def template_bundles(root: Path) -> dict:
    """Load and return the parsed ``.rhiza/template-bundles.yml`` document."""
    with (root / ".rhiza" / "template-bundles.yml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _load_workflow_doc(path: Path) -> object:
    """Parse a workflow YAML file and return the loaded document."""
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class TestOverlayBundleComposition:
    """Each overlay must compose exactly its feature bundle and its platform bundle."""

    def test_every_overlay_is_covered(self, template_bundles: dict) -> None:
        """The spec table must list every overlay bundle defined in template-bundles.yml.

        Guards against a new ``github-*`` / ``gitlab-*`` overlay being added to the
        bundle definitions without a matching hygiene spec here.  ``github`` and
        ``gitlab`` are the platform bundles themselves, not overlays, so are excluded.
        """
        defined = set(template_bundles.get("bundles", {}))
        overlays = {
            name for name in defined if (name.startswith(("github-", "gitlab-"))) and name not in {"github", "gitlab"}
        }
        covered = {spec.bundle for spec in _OVERLAYS}
        assert overlays == covered, (
            f"overlay spec table out of sync with template-bundles.yml; "
            f"uncovered={sorted(overlays - covered)}, stale={sorted(covered - overlays)}"
        )

    @pytest.mark.parametrize("spec", _OVERLAYS, ids=_OVERLAY_IDS)
    def test_overlay_is_defined(self, spec: OverlaySpec, template_bundles: dict) -> None:
        """The overlay bundle must be declared in template-bundles.yml."""
        assert spec.bundle in template_bundles.get("bundles", {}), (
            f"overlay '{spec.bundle}' is not defined in template-bundles.yml"
        )

    @pytest.mark.parametrize("spec", _OVERLAYS, ids=_OVERLAY_IDS)
    def test_overlay_requires_feature_and_platform(self, spec: OverlaySpec, template_bundles: dict) -> None:
        """The overlay's ``requires`` must be exactly its feature bundle and platform bundle."""
        definition = template_bundles["bundles"][spec.bundle]
        requires = set(definition.get("requires", []))
        assert requires == {spec.feature, spec.platform}, (
            f"overlay '{spec.bundle}' should require exactly "
            f"{{{spec.feature!r}, {spec.platform!r}}}, got {sorted(requires)}"
        )


class TestOverlayBundleFiles:
    """Each overlay must ship its feature's workflow file(s) on its platform only."""

    @pytest.mark.parametrize("spec", _OVERLAYS, ids=_OVERLAY_IDS)
    def test_ships_expected_workflows(self, spec: OverlaySpec, root: Path) -> None:
        """Every expected workflow file exists under the platform-specific workflows dir."""
        workflows_dir = root / "bundles" / spec.bundle / _WORKFLOW_DIR[spec.platform]
        assert workflows_dir.is_dir(), f"overlay '{spec.bundle}' is missing {_WORKFLOW_DIR[spec.platform]}/"
        for wf in spec.workflows:
            assert (workflows_dir / wf).is_file(), (
                f"overlay '{spec.bundle}' should ship {_WORKFLOW_DIR[spec.platform] / wf}"
            )

    @pytest.mark.parametrize("spec", _OVERLAYS, ids=_OVERLAY_IDS)
    def test_no_extra_workflow_files(self, spec: OverlaySpec, root: Path) -> None:
        """The overlay must ship only its declared workflows — no surprises in the dir."""
        workflows_dir = root / "bundles" / spec.bundle / _WORKFLOW_DIR[spec.platform]
        shipped = {p.name for p in workflows_dir.glob("*.yml")}
        assert shipped == set(spec.workflows), (
            f"overlay '{spec.bundle}' workflows dir mismatch: "
            f"unexpected={sorted(shipped - set(spec.workflows))}, "
            f"missing={sorted(set(spec.workflows) - shipped)}"
        )

    @pytest.mark.parametrize("spec", _OVERLAYS, ids=_OVERLAY_IDS)
    def test_does_not_ship_other_platform_workflows(self, spec: OverlaySpec, root: Path) -> None:
        """A GitHub overlay must not ship .gitlab/ files and vice versa."""
        other = "gitlab" if spec.platform == "github" else "github"
        other_dir = root / "bundles" / spec.bundle / _WORKFLOW_DIR[other]
        assert not other_dir.exists(), (
            f"overlay '{spec.bundle}' targets {spec.platform} but also ships a {other} workflows dir"
        )


_GITHUB_OVERLAYS = tuple(spec for spec in _OVERLAYS if spec.platform == "github")
_GITHUB_OVERLAY_IDS = tuple(spec.bundle for spec in _GITHUB_OVERLAYS)

_GITLAB_OVERLAYS = tuple(spec for spec in _OVERLAYS if spec.platform == "gitlab")
_GITLAB_OVERLAY_IDS = tuple(spec.bundle for spec in _GITLAB_OVERLAYS)


class TestGithubOverlayWiring:
    """GitHub overlays must delegate to the matching jebel-quant/rhiza reusable workflow."""

    @pytest.mark.parametrize("spec", _GITHUB_OVERLAYS, ids=_GITHUB_OVERLAY_IDS)
    def test_each_workflow_delegates_to_its_feature_reusable(self, spec: OverlaySpec, root: Path) -> None:
        """Every shipped workflow has a job that ``uses:`` the matching reusable feature workflow.

        This is the core feature + platform wiring assertion: a github-<feature>
        overlay's rhiza_<feature>.yml must delegate to
        jebel-quant/rhiza/.github/workflows/rhiza_<feature>.yml so the feature runs
        on GitHub via the canonical reusable workflow.
        """
        workflows_dir = root / "bundles" / spec.bundle / _WORKFLOW_DIR["github"]
        for wf_name in spec.feature_workflows:
            expected_target = f"{_REUSABLE_WORKFLOW_PREFIX}{wf_name}"
            doc = _load_workflow_doc(workflows_dir / wf_name)
            assert isinstance(doc, dict), f"[{spec.bundle}] {wf_name}: not a YAML mapping"
            job_uses = [
                job.get("uses")
                for job in (doc.get("jobs") or {}).values()
                if isinstance(job, dict) and isinstance(job.get("uses"), str)
            ]
            assert any(u.startswith(expected_target) for u in job_uses), (
                f"[{spec.bundle}] {wf_name}: no job delegates to '{expected_target}@<ref>'; job uses found: {job_uses}"
            )

    @pytest.mark.parametrize("spec", _GITHUB_OVERLAYS, ids=_GITHUB_OVERLAY_IDS)
    def test_workflows_are_thin_stubs(self, spec: OverlaySpec, root: Path) -> None:
        """GitHub overlay workflows are thin stubs: jobs delegate via ``uses:`` and define no inline steps."""
        workflows_dir = root / "bundles" / spec.bundle / _WORKFLOW_DIR["github"]
        for wf_name in spec.workflows:
            doc = _load_workflow_doc(workflows_dir / wf_name)
            jobs = doc.get("jobs") if isinstance(doc, dict) else None
            assert jobs, f"[{spec.bundle}] {wf_name}: no jobs defined"
            for job_name, job in jobs.items():
                assert isinstance(job, dict), f"[{spec.bundle}] {wf_name}: job '{job_name}' is malformed"
                uses = job.get("uses")
                assert isinstance(uses, str), (
                    f"[{spec.bundle}] {wf_name}: job '{job_name}' has no string 'uses:' delegating to a "
                    f"{_REUSABLE_WORKFLOW_PREFIX}* reusable workflow"
                )
                assert uses.startswith(_REUSABLE_WORKFLOW_PREFIX), (
                    f"[{spec.bundle}] {wf_name}: job '{job_name}' does not delegate to a "
                    f"{_REUSABLE_WORKFLOW_PREFIX}* reusable workflow"
                )
                assert "steps" not in job, (
                    f"[{spec.bundle}] {wf_name}: job '{job_name}' defines inline steps; "
                    f"github overlay workflows must be thin stubs"
                )


class TestGitlabOverlayWiring:
    """GitLab overlays inline the pipeline (no reusable-workflow ``uses:``)."""

    @pytest.mark.parametrize("spec", _GITLAB_OVERLAYS, ids=_GITLAB_OVERLAY_IDS)
    def test_workflow_defines_runnable_jobs(self, spec: OverlaySpec, root: Path) -> None:
        """Each GitLab overlay workflow defines at least one job with a ``script`` block.

        GitLab CI has no reusable-workflow ``uses:`` mechanism, so overlays inline
        their job definitions (driven by ``make`` targets) rather than delegating.
        """
        workflows_dir = root / "bundles" / spec.bundle / _WORKFLOW_DIR["gitlab"]
        for wf_name in spec.workflows:
            doc = _load_workflow_doc(workflows_dir / wf_name)
            assert isinstance(doc, dict), f"[{spec.bundle}] {wf_name}: not a YAML mapping"
            assert doc, f"[{spec.bundle}] {wf_name}: empty document"
            jobs_with_script = [key for key, value in doc.items() if isinstance(value, dict) and "script" in value]
            assert jobs_with_script, f"[{spec.bundle}] {wf_name}: defines no GitLab CI job with a 'script' block"

    @pytest.mark.parametrize("spec", _GITLAB_OVERLAYS, ids=_GITLAB_OVERLAY_IDS)
    def test_workflow_does_not_use_github_reusables(self, spec: OverlaySpec, root: Path) -> None:
        """GitLab overlays must not reference GitHub reusable workflows."""
        wf_dir = root / "bundles" / spec.bundle / _WORKFLOW_DIR["gitlab"]
        for wf_name in spec.workflows:
            content = (wf_dir / wf_name).read_text(encoding="utf-8")
            assert _REUSABLE_WORKFLOW_PREFIX not in content, (
                f"[{spec.bundle}] {wf_name}: GitLab overlay should not reference GitHub reusable workflows"
            )
