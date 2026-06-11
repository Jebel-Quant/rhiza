"""Tests that gate workflow hygiene: concurrency groups and precise action pins.

Rhiza-specific: covers both rhiza's own workflows (.github/workflows/) and the
workflow stubs shipped to downstream projects (bundles/*/.github/workflows/).
Lives in tests/, not .rhiza/tests/, so it does not sync downstream.

Two invariants:

1. Every workflow declares a top-level ``concurrency`` block so superseded
   runs are cancelled instead of wasting CI minutes. Release and sync
   workflows are the exception: they queue (``cancel-in-progress: false``)
   because they must never be interrupted mid-publish or mid-push.
2. Every ``uses:`` reference is pinned to an exact version — a full
   ``vX.Y.Z``-style tag or a 40-character commit SHA — so upgrades only
   happen through reviewed dependency-update PRs. Local actions (``./...``)
   are exempt.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]

# Workflows that must queue rather than cancel in-progress runs.
_QUEUE_WORKFLOWS = {"rhiza_release.yml", "rhiza_sync.yml"}

# Exact tag (v1.2.3, optionally deeper like v0.3.1900000450) or full commit SHA.
_PRECISE_REF_RE = re.compile(r"@(v?\d+(\.\d+){2,}|[0-9a-f]{40})$")


def _workflow_files() -> list[Path]:
    """Return every workflow file, rhiza's own and bundle-shipped stubs.

    Generated files (*.lock.yml, compiled from gh-aw .md sources) are excluded:
    their content is owned by the gh-aw compiler, not by hand.
    """
    patterns = (".github/workflows/*.yml", "bundles/*/.github/workflows/*.yml")
    return sorted(path for pattern in patterns for path in _ROOT.glob(pattern) if not path.name.endswith(".lock.yml"))


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


class TestWorkflowConcurrency:
    """Every workflow must manage concurrency explicitly."""

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_has_concurrency_group(self, workflow_file: Path) -> None:
        """Each workflow must declare a top-level concurrency group."""
        workflow = _load(workflow_file)
        concurrency = workflow.get("concurrency")
        assert isinstance(concurrency, dict), (
            f"{workflow_file.name}: missing top-level 'concurrency' block — "
            f"superseded runs will pile up instead of being cancelled or queued"
        )
        assert "group" in concurrency, f"{workflow_file.name}: concurrency block has no 'group'"

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_cancel_in_progress_policy(self, workflow_file: Path) -> None:
        """Release/sync workflows queue; everything else cancels superseded runs."""
        concurrency = _load(workflow_file).get("concurrency") or {}
        expected = workflow_file.name not in _QUEUE_WORKFLOWS
        assert concurrency.get("cancel-in-progress") is expected, (
            f"{workflow_file.name}: cancel-in-progress must be {expected} "
            f"({'cancel superseded runs' if expected else 'a release or sync must never be interrupted'})"
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

    def test_workflows_were_collected(self) -> None:
        """Guard against the collector silently matching nothing."""
        assert len(_WORKFLOWS) >= 20, "expected to collect rhiza and bundle workflows"
