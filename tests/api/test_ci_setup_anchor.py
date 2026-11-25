"""The consumer-setup guard in `rhiza_ci.yml` is written once and aliased everywhere (#1806).

The guard refuses consumer setup on fork pull requests and `pull_request_target`. It used
to be pasted into eleven jobs, so an edit that missed one copy would silently weaken that
job alone. A composite action cannot hold it: in a reusable workflow,
`./.github/actions/...` resolves against the caller's checkout. So the steps are YAML
anchors on the first job and aliases on every other one.

`test_consumer_setup.py` already proves that each job runs the guard verbatim and in
order, but it reads the *parsed* workflow, where a pasted copy and an alias look the
same. These tests read the source text, which is the only place the difference exists.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "rhiza_ci.yml"
_ANCHORS = ("consumer_setup_guard", "consumer_setup_run")
# Each line is unique to one of the two steps, so counting it counts copies of that step.
_STEP_MARKERS = (
    "Consumer setup is not allowed on fork pull requests or pull_request_target.",
    "uses: ./.github/actions/rhiza-setup",
)


@pytest.fixture(scope="module")
def source() -> str:
    """Return the raw text of the reusable CI workflow."""
    return _CI.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def guarded_jobs() -> list[str]:
    """Return the CI jobs whose parsed steps include the consumer-setup guard."""
    jobs = yaml.safe_load(_CI.read_text(encoding="utf-8"))["jobs"]
    return [
        name
        for name, job in jobs.items()
        if any(step.get("name") == "Validate consumer dependency setup" for step in job.get("steps", []))
    ]


@pytest.mark.parametrize("marker", _STEP_MARKERS)
def test_each_setup_step_body_is_written_once(source: str, marker: str) -> None:
    """The guard's shell and the setup call each appear once in the file, however many jobs run them."""
    assert source.count(marker) == 1, f"{marker!r} is pasted into the workflow more than once; alias the anchor"


@pytest.mark.parametrize("anchor", _ANCHORS)
def test_each_anchor_is_defined_once(source: str, anchor: str) -> None:
    """Exactly one job defines each anchor, so there is exactly one copy to edit."""
    assert source.count(f"- &{anchor}\n") == 1


@pytest.mark.parametrize("anchor", _ANCHORS)
def test_every_other_guarded_job_aliases_the_anchor(source: str, guarded_jobs: list[str], anchor: str) -> None:
    """Every guarded job except the one that defines the anchor reaches the steps through an alias."""
    assert len(guarded_jobs) > 1, "no job runs the consumer-setup guard; the alias check would pass vacuously"
    assert source.count(f"- *{anchor}\n") == len(guarded_jobs) - 1
