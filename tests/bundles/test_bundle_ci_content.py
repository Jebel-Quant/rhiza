"""CI content shipped in bundles: GitHub workflow stubs and GitLab image pinning.

Split out of ``test_bundle_content_validity.py`` (#1514). Both classes assert properties
of the *pipeline definitions* a consumer receives — that each GitHub stub delegates to
the canonical reusable workflow in ``jebel-quant/rhiza`` rather than inlining a copy that
would then drift, and that every GitLab image reference is pinned rather than floating on
a moving tag.

They are grouped because they answer the same question on the two platforms rhiza
supports, and because both read workflow YAML in a way none of the remaining
content-validity suites do.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tests.bundles._content import _all_files_in_bundle

# ---------------------------------------------------------------------------
# GitHub workflow stubs
# ---------------------------------------------------------------------------

# Prefix every reusable-workflow stub must call to delegate to this repository.
_REUSABLE_WORKFLOW_PREFIX = "jebel-quant/rhiza/.github/workflows/"

# rhiza_*.yml workflows that are intentionally NOT thin stubs.  rhiza_release.yml
# is a full release-automation workflow that runs many first-party steps itself
# rather than delegating to a reusable workflow.
_NON_STUB_RHIZA_WORKFLOWS = {"rhiza_release.yml"}

# ---------------------------------------------------------------------------
# GitLab CI uv-image single-source pinning
# ---------------------------------------------------------------------------

_UV_IMAGE_LITERAL = re.compile(r"ghcr\.io/astral-sh/uv:")
_IMAGE_LINE = re.compile(r"^\s*image:\s*(\S+)")


def _load_workflow_doc(path: Path) -> object:
    """Parse a workflow YAML file and return the loaded document."""
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class TestGithubWorkflowStubs:
    """Bundle-shipped GitHub workflows must delegate to jebel-quant/rhiza reusables.

    Covers every bundle that ships a .github/workflows/ directory — not just the
    github-* overlays, but also the `github` bundle.  Documented full workflows
    (rhiza_release.yml) are excepted from the thin-stub requirement.
    """

    def _bundles_with_github_workflows(self, root: Path, bundle_names: list[str]) -> list[tuple[str, Path]]:
        """Return (bundle_name, workflows_dir) for every bundle shipping GitHub workflows."""
        result: list[tuple[str, Path]] = []
        for bundle_name in bundle_names:
            workflows_dir = root / "bundles" / bundle_name / ".github" / "workflows"
            if workflows_dir.is_dir():
                result.append((bundle_name, workflows_dir))
        return result

    def test_workflow_stubs_have_name_field(self, root: Path, bundle_names: list[str]) -> None:
        """Every GitHub workflow YAML file has a top-level 'name' field."""
        errors: list[str] = []
        for bundle_name, workflows_dir in self._bundles_with_github_workflows(root, bundle_names):
            for wf in workflows_dir.glob("*.yml"):
                doc = _load_workflow_doc(wf)
                if not isinstance(doc, dict) or "name" not in doc:
                    errors.append(f"  [{bundle_name}] {wf.name}: missing 'name' field")
        if errors:
            pytest.fail("Workflow stubs without 'name':\n" + "\n".join(errors))

    def test_workflow_stubs_have_on_trigger(self, root: Path, bundle_names: list[str]) -> None:
        """Every GitHub workflow YAML file has an 'on' trigger section.

        Note: pyyaml parses the bare YAML key 'on' as Python boolean True (since 'on'
        is a YAML boolean literal).  We check for both True and the string 'on' to
        handle both parsed and raw representations.
        """
        errors: list[str] = []
        for bundle_name, workflows_dir in self._bundles_with_github_workflows(root, bundle_names):
            for wf in workflows_dir.glob("*.yml"):
                doc = _load_workflow_doc(wf)
                if not isinstance(doc, dict):
                    errors.append(f"  [{bundle_name}] {wf.name}: not a YAML mapping")
                    continue
                # pyyaml parses 'on:' as True (YAML boolean); check both forms
                has_on = "on" in doc or True in doc
                if not has_on:
                    errors.append(f"  [{bundle_name}] {wf.name}: missing 'on' trigger")
        if errors:
            pytest.fail("Workflow stubs without 'on' trigger:\n" + "\n".join(errors))

    def test_workflow_stubs_have_jobs(self, root: Path, bundle_names: list[str]) -> None:
        """Every GitHub workflow YAML file has a non-empty 'jobs' section."""
        errors: list[str] = []
        for bundle_name, workflows_dir in self._bundles_with_github_workflows(root, bundle_names):
            for wf in workflows_dir.glob("*.yml"):
                doc = _load_workflow_doc(wf)
                if not isinstance(doc, dict):
                    continue
                jobs = doc.get("jobs")
                if not jobs:
                    errors.append(f"  [{bundle_name}] {wf.name}: missing or empty 'jobs' section")
        if errors:
            pytest.fail("Workflow stubs without 'jobs':\n" + "\n".join(errors))

    def test_reusable_calls_target_rhiza_workflows(self, root: Path, bundle_names: list[str]) -> None:
        """Every job that calls a reusable workflow must target a jebel-quant/rhiza one.

        This inspects the parsed job-level ``uses:`` reference rather than doing a
        substring search of the file, so it is not satisfied by the jebel-quant/rhiza
        URL in the boilerplate header comment.  Step-level ``uses:`` (third-party
        actions) are intentionally ignored.
        """
        errors: list[str] = []
        for bundle_name, workflows_dir in self._bundles_with_github_workflows(root, bundle_names):
            for wf in workflows_dir.glob("*.yml"):
                doc = _load_workflow_doc(wf)
                if not isinstance(doc, dict):
                    continue
                for job_name, job in (doc.get("jobs") or {}).items():
                    if not isinstance(job, dict):
                        continue
                    uses = job.get("uses")
                    if uses is None:
                        continue  # not a reusable-workflow call
                    if not (isinstance(uses, str) and uses.startswith(_REUSABLE_WORKFLOW_PREFIX)):
                        errors.append(
                            f"  [{bundle_name}] {wf.name}: job '{job_name}' calls '{uses}', "
                            f"not a {_REUSABLE_WORKFLOW_PREFIX}* reusable workflow"
                        )
        if errors:
            pytest.fail("Reusable-workflow calls not targeting jebel-quant/rhiza:\n" + "\n".join(errors))

    def test_rhiza_workflows_are_thin_stubs(self, root: Path, bundle_names: list[str]) -> None:
        """Every rhiza_*.yml bundle workflow is a thin stub (except documented exceptions).

        A thin stub delegates entirely to a jebel-quant/rhiza reusable workflow: each
        of its jobs has a ``uses:`` pointing at that repo and defines no inline
        ``steps:``.  rhiza_release.yml is exempt (it is a full release workflow).
        """
        errors: list[str] = []
        for bundle_name, workflows_dir in self._bundles_with_github_workflows(root, bundle_names):
            for wf in workflows_dir.glob("*.yml"):
                if not wf.name.startswith("rhiza_") or wf.name in _NON_STUB_RHIZA_WORKFLOWS:
                    continue
                doc = _load_workflow_doc(wf)
                jobs = doc.get("jobs") if isinstance(doc, dict) else None
                if not jobs:
                    errors.append(f"  [{bundle_name}] {wf.name}: no jobs to delegate")
                    continue
                for job_name, job in jobs.items():
                    if not isinstance(job, dict):
                        errors.append(f"  [{bundle_name}] {wf.name}: job '{job_name}' is malformed")
                        continue
                    uses = job.get("uses")
                    if not (isinstance(uses, str) and uses.startswith(_REUSABLE_WORKFLOW_PREFIX)):
                        errors.append(
                            f"  [{bundle_name}] {wf.name}: job '{job_name}' does not delegate to a "
                            f"{_REUSABLE_WORKFLOW_PREFIX}* reusable workflow"
                        )
                    if "steps" in job:
                        errors.append(
                            f"  [{bundle_name}] {wf.name}: job '{job_name}' defines inline steps; "
                            f"rhiza_* workflows must be thin stubs (add it to the reusable workflow instead)"
                        )
        if errors:
            pytest.fail("rhiza_* bundle workflows that are not thin stubs:\n" + "\n".join(errors))


class TestGitlabImagePinning:
    """Every GitLab job image must resolve from the single `$UV_IMAGE` variable.

    The uv/Python CI image used to be hardcoded (`ghcr.io/astral-sh/uv:<version>`)
    in ~20 places across the gitlab* bundles, drifting from the version GitHub
    Actions pins. `.gitlab-ci.yml` now defines `UV_IMAGE` once and every job
    references `image: $UV_IMAGE`. These guards stop the literal pin from
    creeping back in and keep the caching plumbing in place.
    """

    def _gitlab_ci_yml(self, root: Path) -> Path:
        """Return the gitlab bundle's `.gitlab-ci.yml`, skipping if the bundle is absent."""
        ci = root / "bundles" / "gitlab" / ".gitlab-ci.yml"
        if not ci.exists():
            pytest.skip("gitlab bundle not present")
        return ci

    def test_no_hardcoded_uv_image_pin_outside_single_source(self, root: Path) -> None:
        """The literal `ghcr.io/astral-sh/uv:` tag may appear only in the UV_IMAGE definition."""
        self._gitlab_ci_yml(root)  # skip if gitlab bundle absent
        offenders: list[str] = []
        for bundle in sorted(root.glob("bundles/gitlab*")):
            for path in _all_files_in_bundle(bundle):
                if path.suffix not in {".yml", ".yaml", ".jinja"}:
                    continue
                for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if not _UV_IMAGE_LITERAL.search(line):
                        continue
                    # The sole allowed literal: the `UV_IMAGE:` variable value.
                    if re.match(r"\s*UV_IMAGE:\s*", line):
                        continue
                    offenders.append(f"{path.relative_to(root)}:{lineno}: {line.strip()}")
        assert not offenders, "Hardcoded uv image pin(s) found; reference `$UV_IMAGE` instead:\n" + "\n".join(offenders)

    def test_image_lines_reference_the_variable(self, root: Path) -> None:
        """Any `image:` value that is a uv image must be exactly `$UV_IMAGE`."""
        self._gitlab_ci_yml(root)
        bad: list[str] = []
        for bundle in sorted(root.glob("bundles/gitlab*")):
            for path in _all_files_in_bundle(bundle):
                if path.suffix not in {".yml", ".yaml", ".jinja"}:
                    continue
                for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    m = _IMAGE_LINE.match(line)
                    if not m:
                        continue
                    value = m.group(1)
                    # Only constrain the uv image; alpine/renovate/etc. are unrelated.
                    if "uv" in value or _UV_IMAGE_LITERAL.search(line):
                        assert_msg = f"{path.relative_to(root)}:{lineno}: {line.strip()}"
                        if value != "$UV_IMAGE":
                            bad.append(assert_msg)
        assert not bad, "uv `image:` lines must be `$UV_IMAGE`:\n" + "\n".join(bad)

    def test_single_source_variables_defined_once(self, root: Path) -> None:
        """`.gitlab-ci.yml` must define UV_IMAGE / UV_CACHE_DIR / UV_PYTHON_INSTALL_DIR exactly once."""
        ci = self._gitlab_ci_yml(root)
        parsed = yaml.safe_load(ci.read_text(encoding="utf-8"))
        variables = parsed.get("variables", {})
        assert variables.get("UV_IMAGE", "").startswith("ghcr.io/astral-sh/uv:"), (
            "variables.UV_IMAGE must pin a concrete ghcr.io/astral-sh/uv image"
        )
        for key in ("UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR"):
            assert key in variables, f"variables.{key} must redirect uv's cache under $CI_PROJECT_DIR"
            assert "CI_PROJECT_DIR" in variables[key], (
                f"variables.{key} must live under $CI_PROJECT_DIR so GitLab can cache it"
            )

    def test_default_cache_covers_uv_dirs(self, root: Path) -> None:
        """`default.cache` must persist the uv wheel + managed-Python directories."""
        ci = self._gitlab_ci_yml(root)
        parsed = yaml.safe_load(ci.read_text(encoding="utf-8"))
        cache = parsed.get("default", {}).get("cache")
        assert cache, "default.cache must be defined so uv downloads persist across jobs"
        paths = cache.get("paths", [])
        assert ".cache/uv" in paths, f"default.cache.paths must include '.cache/uv', got: {paths}"
        assert ".cache/uv-python" in paths, f"default.cache.paths must include '.cache/uv-python', got: {paths}"

    def test_orphaned_python_base_template_removed(self, root: Path) -> None:
        """The unused `.python_base` job template must not reappear."""
        ci = self._gitlab_ci_yml(root)
        parsed = yaml.safe_load(ci.read_text(encoding="utf-8"))
        assert ".python_base" not in parsed, (
            ".python_base was an orphaned template (nothing extends it); it should stay removed"
        )
