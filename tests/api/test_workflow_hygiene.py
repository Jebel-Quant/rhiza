"""Tests that gate workflow hygiene: concurrency groups and precise action pins.

Rhiza-specific: covers both rhiza's own workflows (.github/workflows/) and the
workflow stubs shipped to downstream projects (bundles/*/.github/workflows/).
Lives in the mother repo's own tests/, so it does not sync downstream.

Two invariants:

1. Every workflow that runs its own jobs declares a top-level ``concurrency``
   block so superseded runs are cancelled instead of wasting CI minutes.
   Release and sync workflows are the exception: they queue
   (``cancel-in-progress: false``) because they must never be interrupted
   mid-publish or mid-push. Caller stubs that merely delegate to a reusable
   workflow must NOT declare concurrency: the reusable workflow already
   declares the same ``${{ github.workflow }}-${{ github.ref }}`` group, and a
   duplicate caller-level group deadlocks (the top-level run and the nested
   job each wait on the other for the shared group).
2. Every ``uses:`` reference is pinned to an exact version — a full
   ``vX.Y.Z``-style tag or a 40-character commit SHA — so upgrades only
   happen through reviewed dependency-update PRs. Local actions (``./...``)
   are exempt.
3. Every **third-party** action is pinned to a commit SHA, in the workflows rhiza
   ships as well as the ones it runs. A tag is a moving target: whoever owns the
   action can repoint ``v6`` — or ``v6.0.2`` — at a different commit, and every
   consumer runs it on the next release. Only ``jebel-quant/rhiza`` reusable-workflow
   refs may be tags, and they must be: ``[[tool.bumpversion.files]]`` rewrites
   ``@vX.Y.Z`` on every release, which is how a stub keeps pointing at the template
   version it was synced from.

   This was one population until #1611. The live workflows were SHA-pinned and
   ``bundles/github/.github/workflows/rhiza_release.yml`` — the one shipped workflow
   with steps of its own, and the most privileged one a consumer runs — carried 26 tag
   pins, several already behind their live twin. Nothing noticed, because invariant 2
   accepts either form and asked no further questions.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]

# Workflows that must queue rather than cancel in-progress runs.
_QUEUE_WORKFLOWS = {"rhiza_release.yml"}

# Exact tag (v1.2.3, optionally deeper like v0.3.1900000450) or full commit SHA.
_PRECISE_REF_RE = re.compile(r"@(v?\d+(\.\d+){2,}|[0-9a-f]{40})$")

# A 40-character commit SHA, the only acceptable pin for a third-party action.
_SHA_REF_RE = re.compile(r"@[0-9a-f]{40}$")

# Refs that may carry a tag: rhiza's own reusable workflows, whose tag *is* the template
# version and is rewritten by bump-my-version on every release.
_FIRST_PARTY_PREFIX = "jebel-quant/rhiza/"


# Names of compiler-generated workflows to exclude from hygiene checks (their
# content is owned by a generator, not hand-written). None currently exist;
# kept as the exclusion hook for any future generated workflows.
_GENERATED_WORKFLOWS: set[str] = set()


def _workflow_files() -> list[Path]:
    """Return every workflow file, rhiza's own and bundle-shipped stubs.

    Generated files (*.lock.yml) are excluded: their content is owned by a
    compiler, not written by hand.
    """
    patterns = (".github/workflows/*.yml", "bundles/*/.github/workflows/*.yml")
    return sorted(
        path
        for pattern in patterns
        for path in _ROOT.glob(pattern)
        if not path.name.endswith(".lock.yml") and path.name not in _GENERATED_WORKFLOWS
    )


_WORKFLOWS = _workflow_files()
_IDS = [str(p.relative_to(_ROOT)) for p in _WORKFLOWS]


def _load(path: Path) -> dict:
    """Load a workflow YAML file and return the parsed document."""
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _uses_refs(workflow: dict) -> list[str]:
    """Return every ``uses:`` reference in a workflow (job-level and step-level)."""
    refs: list[str] = []
    for job in (workflow.get("jobs") or {}).values():
        if "uses" in job:
            refs.append(job["uses"])
        for step in job.get("steps") or []:
            if "uses" in step:
                refs.append(step["uses"])
    return refs


def _delegates_to_reusable(workflow: dict) -> bool:
    """True if the workflow is a thin caller that delegates to a reusable workflow.

    Such stubs have a job-level ``uses:`` pointing at a reusable workflow file
    (``.../.github/workflows/<name>.yml@<ref>``). They must not declare their
    own ``concurrency`` block — the called workflow already does, and a shared
    group deadlocks the run.
    """
    for job in (workflow.get("jobs") or {}).values():
        uses = job.get("uses")
        if uses and ".github/workflows/" in uses and ".yml@" in uses:
            return True
    return False


class TestWorkflowConcurrency:
    """Every workflow must manage concurrency explicitly."""

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_has_concurrency_group(self, workflow_file: Path) -> None:
        """Job-running workflows declare a concurrency group; caller stubs must not."""
        workflow = _load(workflow_file)
        concurrency = workflow.get("concurrency")
        if _delegates_to_reusable(workflow):
            assert concurrency is None, (
                f"{workflow_file.name}: reusable-workflow caller must not declare a "
                f"top-level 'concurrency' block — it shares the called workflow's "
                f"group and deadlocks the run"
            )
            return
        assert isinstance(concurrency, dict), (
            f"{workflow_file.name}: missing top-level 'concurrency' block — "
            f"superseded runs will pile up instead of being cancelled or queued"
        )
        assert "group" in concurrency, f"{workflow_file.name}: concurrency block has no 'group'"

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_cancel_in_progress_policy(self, workflow_file: Path) -> None:
        """Release/sync workflows queue; other job-running workflows cancel superseded runs.

        Reusable-workflow callers carry no concurrency block of their own (the
        called workflow owns the policy, and a duplicate caller-level group
        deadlocks the run), so for them this asserts the block stays absent
        rather than checking a cancel-in-progress value.
        """
        workflow = _load(workflow_file)
        if _delegates_to_reusable(workflow):
            assert workflow.get("concurrency") is None, (
                f"{workflow_file.name}: reusable-workflow caller must not declare a "
                f"top-level 'concurrency' block — it shares the called workflow's "
                f"cancel-in-progress policy and a duplicate group deadlocks the run"
            )
            return
        concurrency = workflow.get("concurrency") or {}
        expected = workflow_file.name not in _QUEUE_WORKFLOWS
        assert concurrency.get("cancel-in-progress") is expected, (
            f"{workflow_file.name}: cancel-in-progress must be {expected} "
            f"({'cancel superseded runs' if expected else 'a release or sync must never be interrupted'})"
        )


class TestRunnerHardening:
    """Where `step-security/harden-runner` runs, and — deliberately — where it does not.

    Every job with steps of its own in `.github/workflows/` opens with it in
    `egress-policy: audit` mode. That is 36 jobs across 13 workflows, and pinning it here
    is what keeps a new workflow (or a new job in an old one) from quietly opting out.

    **It is deliberately not in the shipped release workflow, and that is a decision rather
    than the drift it looks like (#1611).** harden-runner is a third-party agent that
    monitors the runner and reports egress to a third-party service. Adding one to rhiza's
    own CI is rhiza's call; adding one to a *consumer's* release pipeline, on their runners
    and under their compliance regime, is theirs — and none of the shipped stub's steps needs
    it to do the release. Consumers are not left without it either way: every other stub
    delegates to a reusable workflow in this repository, so their CI, book, docker and paper
    jobs run these hardened jobs already.

    A consumer who wants it in their release pipeline adds the step; that is a two-line
    diff, and `exclude:` in `.rhiza/template.yml` keeps it across syncs.
    """

    @pytest.mark.parametrize(
        "workflow_file",
        [p for p in _WORKFLOWS if p.parent.parent.parent == _ROOT],
        ids=[str(p.relative_to(_ROOT)) for p in _WORKFLOWS if p.parent.parent.parent == _ROOT],
    )
    def test_every_live_job_hardens_the_runner_first(self, workflow_file: Path) -> None:
        """A job that runs steps must harden the runner before it runs any of them."""
        unhardened = [
            job_id
            for job_id, job in (_load(workflow_file).get("jobs") or {}).items()
            if (job.get("steps") or []) and "harden-runner" not in (job["steps"][0].get("uses") or "")
        ]
        assert not unhardened, (
            f"{workflow_file.name}: jobs {unhardened} run steps without hardening the runner "
            f"first — every other job in .github/workflows/ opens with step-security/"
            f"harden-runner in audit mode"
        )

    def test_the_shipped_workflows_harden_nothing(self) -> None:
        """The bundles must ship no harden-runner step — see this class's docstring.

        Asserted so the decision is visible where the divergence is, rather than being
        rediscovered as drift by the next person to diff a bundle against its live twin.
        Flipping this decision means deleting this test, which is the point.
        """
        shipping = [
            str(path.relative_to(_ROOT))
            for path in _WORKFLOWS
            if path.parent.parent.parent != _ROOT and "harden-runner" in path.read_text(encoding="utf-8")
        ]
        assert not shipping, (
            f"{shipping} ship a harden-runner step. Adding a third-party runner-monitoring "
            f"agent to a consumer's repository is their decision, not the template's (#1611)."
        )


class TestActionPinning:
    """Every action reference must be pinned to an exact version."""

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_uses_refs_are_precisely_pinned(self, workflow_file: Path) -> None:
        """All uses: refs must carry an exact vX.Y.Z tag or a full commit SHA."""
        imprecise = [
            ref
            for ref in _uses_refs(_load(workflow_file))
            if not ref.startswith("./") and not _PRECISE_REF_RE.search(ref)
        ]
        assert not imprecise, (
            f"{workflow_file.name}: imprecisely pinned actions {imprecise} — "
            f"pin to an exact vX.Y.Z tag or full commit SHA"
        )

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_third_party_actions_are_pinned_by_sha(self, workflow_file: Path) -> None:
        """Third-party actions must carry a commit SHA, shipped stubs included (#1611).

        A tag pin is only as trustworthy as the action's owner: `v6.0.2` is a ref, and a ref
        can be moved. That is the whole argument for SHA pinning, and it applies with more
        force to a workflow rhiza *ships* than to one it runs, because a consumer inherits the
        pin without choosing it.

        rhiza's own workflows have been SHA-pinned throughout. What this adds is the shipped
        half — in practice `bundles/github/.github/workflows/rhiza_release.yml`, the only
        shipped workflow with steps of its own; every other stub delegates to a reusable
        workflow, so its consumers already run the mother repo's SHA-pinned steps.
        """
        loose = [
            ref
            for ref in _uses_refs(_load(workflow_file))
            if not ref.startswith("./") and not ref.startswith(_FIRST_PARTY_PREFIX) and not _SHA_REF_RE.search(ref)
        ]
        assert not loose, (
            f"{workflow_file.name}: {loose} pinned by tag — pin third-party actions to a "
            f"commit SHA with a `# vX.Y.Z` comment, which is what Renovate maintains"
        )

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_first_party_reusable_workflows_are_pinned_by_tag(self, workflow_file: Path) -> None:
        """`jebel-quant/rhiza` refs must stay tags, which is the other half of the rule above.

        The exemption is not a weaker standard, it is a different mechanism: the tag names the
        template release a repository is synced to, and `[[tool.bumpversion.files]]` rewrites
        it across `bundles/**/.github/workflows/*.yml` on every release. A SHA there would
        pin a consumer to a commit no release names, and the rewrite would stop finding it.
        """
        wrong = [
            ref
            for ref in _uses_refs(_load(workflow_file))
            if ref.startswith(_FIRST_PARTY_PREFIX) and _SHA_REF_RE.search(ref)
        ]
        assert not wrong, (
            f"{workflow_file.name}: {wrong} pinned by SHA — rhiza's own reusable workflows are "
            f"pinned by tag, which is what the release rewrites"
        )

    def test_workflows_were_collected(self) -> None:
        """Guard against the collector silently matching nothing."""
        assert len(_WORKFLOWS) >= 20, "expected to collect rhiza and bundle workflows"
