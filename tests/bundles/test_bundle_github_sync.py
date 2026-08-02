"""Tests that dogfooded .github/ platform-config files match their bundle source.

Most root dogfood files are symlinks into ``bundles/`` (single source of truth). A
handful cannot be: GitHub reads ``.github/`` platform config (Dependabot, release
notes, secret-scanning, the PR template, rulesets) directly from the tree and does
**not** resolve symlinks, so those files must be real copies at the repo root. Their
counterparts in ``bundles/github/.github/`` therefore stay real too, and this test is
the guard that the two never drift.

Workflow files under ``.github/workflows/`` are intentionally excluded: the mother
repo ships its own live reusable workflows there, which differ by design from the
stub workflows the github bundle injects into downstream projects.

``rulesets/main-branch-protection.json`` is excluded for the same reason one level
down — see :class:`TestRequiredStatusCheckContexts`, which owns that divergence.

The check is driven from the bundle side, restricted to files the mother repo
actually dogfoods (i.e. a same-path root counterpart exists). Bundle-only files such
as ISSUE_TEMPLATE/ and DISCUSSION_TEMPLATE/ have no root twin and are skipped.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]

# The one dogfooded .github/ file whose two copies must differ (issue #1448): the
# same check runs under a bare name here and a `ci / `-prefixed name downstream.
_RULESET = Path("rulesets") / "main-branch-protection.json"

# The stub that produces the prefix downstream. Its job id is the prefix.
_CI_STUB = _ROOT / "bundles" / "github-tests" / ".github" / "workflows" / "rhiza_ci.yml"


def _github_dogfood_pairs() -> list[tuple[str, Path, Path]]:
    """Return (label, bundle_file, root_file) for each dogfooded .github/ copy.

    A pair is included when a non-workflow file in ``bundles/github/.github/`` has a
    same-path counterpart at the repository root — the set the mother repo dogfoods.
    """
    pairs: list[tuple[str, Path, Path]] = []
    bundle_github = _ROOT / "bundles" / "github" / ".github"
    if not bundle_github.is_dir():
        return pairs

    for bundle_file in sorted(bundle_github.rglob("*")):
        if not bundle_file.is_file() or "__pycache__" in bundle_file.parts:
            continue
        relative = bundle_file.relative_to(bundle_github)
        if relative.parts and relative.parts[0] == "workflows":
            continue  # live mother-repo workflows differ from bundle stubs by design
        if relative == _RULESET:
            continue  # required-check names differ by design — see TestRequiredStatusCheckContexts
        root_file = _ROOT / ".github" / relative
        if not root_file.exists():
            continue  # bundle-only file (e.g. ISSUE_TEMPLATE/) — not dogfooded here
        pairs.append((f".github/{relative}", bundle_file, root_file))

    return pairs


_PAIRS = _github_dogfood_pairs()


class TestBundleGithubSync:
    """Verify dogfooded .github/ copies stay byte-identical to their bundle source."""

    def test_dogfood_set_is_nonempty(self) -> None:
        """At least one .github/ file must be dogfooded.

        Without this guard the parametrized test below would silently produce zero
        cases (e.g. after a refactor that moved the files), making CI appear green
        while the sync check never ran.
        """
        assert _PAIRS, (
            "No dogfooded .github/ files found — the github bundle moved its platform "
            "config, or the mother repo stopped dogfooding it; update this test."
        )

    @pytest.mark.parametrize(
        ("label", "bundle_file", "root_file"),
        _PAIRS,
        ids=[p[0] for p in _PAIRS],
    )
    def test_dogfooded_github_file_matches_bundle(self, label: str, bundle_file: Path, root_file: Path) -> None:
        """Each dogfooded .github/ copy must byte-match its bundle source.

        These files cannot be symlinks (GitHub does not follow symlinks for platform
        config), so unlike the symlinked dogfood files they can drift — edit both
        sides together, or the copies fall out of sync.
        """
        assert not root_file.is_symlink(), (
            f"{label}: must be a real file — GitHub does not resolve symlinks for .github/ "
            f"platform config (Dependabot, Actions, etc.)"
        )
        assert root_file.read_bytes() == bundle_file.read_bytes(), (
            f"{label}: dogfooded copy differs from bundle source "
            f"{bundle_file.relative_to(_ROOT)} — edit both sides to keep them in sync"
        )


def _required_contexts(ruleset: Path) -> list[str]:
    """Return the required status-check contexts declared by a ruleset file."""
    rules = json.loads(ruleset.read_text(encoding="utf-8"))["rules"]
    checks = next(rule for rule in rules if rule["type"] == "required_status_checks")
    return [check["context"] for check in checks["parameters"]["required_status_checks"]]


def _ci_job_names() -> set[str]:
    """Return the check-run names the mother repo's reusable CI workflow reports.

    GitHub names a check run after the job's ``name:``, falling back to its job id.
    """
    workflow = yaml.safe_load((_ROOT / ".github" / "workflows" / "rhiza_ci.yml").read_text(encoding="utf-8"))
    return {job.get("name", job_id) for job_id, job in workflow["jobs"].items()}


class TestRequiredStatusCheckContexts:
    """The two ruleset copies must differ by exactly the caller's job-id prefix (#1448).

    One file, two invocation shapes. In the mother repo ``rhiza_ci.yml`` carries
    ``push:``/``pull_request:`` alongside ``workflow_call:``, so its jobs run at the top
    level and report bare check-run names. Downstream the github-tests bundle ships a
    thin caller whose ``jobs.ci`` delegates to that same reusable workflow, and GitHub
    names the resulting runs ``<calling job id> / <inner job name>``.

    A bundle ruleset listing bare contexts therefore names six checks that can never
    report, leaving every downstream PR blocked on "Expected — waiting for status".
    """

    def test_caller_stub_has_a_single_job_that_supplies_the_prefix(self) -> None:
        """The prefix is the caller's job id, so the stub must keep exactly that one job.

        Renaming ``jobs.ci`` in the stub silently invalidates every downstream ruleset —
        the checks would report under the new prefix while the ruleset still waits for
        the old one.
        """
        stub = yaml.safe_load(_CI_STUB.read_text(encoding="utf-8"))
        assert list(stub["jobs"]) == ["ci"], (
            f"{_CI_STUB.relative_to(_ROOT)}: the job id is the check-run prefix baked into "
            f"bundles/github/.github/{_RULESET.as_posix()}; renaming it breaks every "
            f"downstream ruleset (#1448)"
        )

    def test_root_ruleset_contexts_are_unprefixed(self) -> None:
        """The mother repo runs the jobs directly, so its contexts carry no prefix."""
        for context in _required_contexts(_ROOT / ".github" / _RULESET):
            assert " / " not in context, (
                f"{context!r}: this repo's own CI runs as top-level jobs and reports bare "
                f"check-run names — a prefix here can never be satisfied"
            )

    def test_bundle_ruleset_contexts_are_prefixed_with_the_caller_job_id(self) -> None:
        """The bundle copy must be the root copy with the caller's job id prepended."""
        root = _required_contexts(_ROOT / ".github" / _RULESET)
        bundle = _required_contexts(_ROOT / "bundles" / "github" / ".github" / _RULESET)
        assert bundle == [f"ci / {context}" for context in root], (
            "the bundle ruleset must list the same checks as the root one, each prefixed "
            "with the github-tests caller's job id (#1448)"
        )

    def test_required_contexts_name_jobs_that_exist(self) -> None:
        """Every required context must correspond to a job the CI workflow actually runs.

        A ruleset may only require checks that report; a renamed or deleted job leaves
        a required check permanently pending rather than failing loudly.
        """
        names = _ci_job_names()
        missing = [c for c in _required_contexts(_ROOT / ".github" / _RULESET) if c not in names]
        assert not missing, (
            f"required status checks name no job in .github/workflows/rhiza_ci.yml: {missing} "
            f"(known job check-run names: {sorted(names)})"
        )
