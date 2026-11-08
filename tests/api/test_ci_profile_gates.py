"""Execute the CI profile gates of the optional workflows against consumer projects (#1744).

GitHub's ``on:`` triggers cannot read ``pyproject.toml``, so CodeQL and marimo start on
every pull request and a first ``profile`` job decides whether their expensive jobs run.
These tests run that job's shipped script, lifted out of the YAML, the way
``test_ci_profiles.py`` runs the CI planner -- and hold its profile resolution to the
planner's, so the two cannot disagree about what a configuration means.
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - executes checked-in workflow scripts
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOWS = _ROOT / ".github" / "workflows"

# Reusable workflow -> (bundle stub, the jobs the gate guards directly).
_GATED = {
    "rhiza_codeql.yml": ("bundles/github-tests/.github/workflows/rhiza_codeql.yml", ["analyze"]),
    "rhiza_marimo.yml": ("bundles/github-marimo/.github/workflows/rhiza_marimo.yml", ["list-notebooks"]),
}
_CODEQL_ENABLED = (
    "vars.CODEQL_ENABLED == 'true' ||\n"
    "(vars.CODEQL_ENABLED != 'false' && github.event.repository.visibility == 'public')\n"
)
_PROFILES = [None, "lean", "standard", "comprehensive"]
_EVENTS = ["pull_request", "push", "schedule", "workflow_dispatch"]


def _load(path: Path) -> dict:
    """Load a workflow file."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _triggers(workflow: dict) -> dict:
    """Return a workflow's triggers; PyYAML reads the ``on`` key as ``True``."""
    return workflow.get("on", workflow.get(True))


def _gate_script(name: str) -> str:
    """Return the shipped profile-gate script of a reusable workflow."""
    steps = _load(_WORKFLOWS / name)["jobs"]["profile"]["steps"]
    return next(step for step in steps if step.get("id") == "profile")["run"]


def _resolution_block(script: str) -> str:
    """Return the shared ``ci-profile resolution`` block, dedented, markers included."""
    lines = script.splitlines()
    start = next(i for i, line in enumerate(lines) if "# BEGIN ci-profile resolution" in line)
    end = next(i for i, line in enumerate(lines) if "# END ci-profile resolution" in line)
    return textwrap.dedent("\n".join(lines[start : end + 1]))


@pytest.fixture
def consumer(tmp_path):
    """Create a consumer project with a pyproject.toml and no CI profile."""
    project = tmp_path / "consumer"
    project.mkdir()
    (project / "pyproject.toml").write_text('[project]\nname = "consumer"\nversion = "0.1.0"\n')
    return project


def _gate(name, consumer, profile=None, event_name="pull_request", raw=None):
    """Run a workflow's gate script in ``consumer``, returning the process and its outputs."""
    if raw is not None or profile is not None:
        body = raw if raw is not None else f"profile = {json.dumps(profile)}"
        with (consumer / "pyproject.toml").open("a") as stream:
            stream.write(f"\n[tool.rhiza.ci]\n{body}\n")
    output = consumer.parent / "github-output.txt"
    output.write_text("")
    result = subprocess.run(  # nosec B603 - fixed interpreter running a checked-in script
        [sys.executable, "-c", _gate_script(name)],
        cwd=consumer,
        env={**os.environ, "GITHUB_EVENT_NAME": event_name, "GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        check=False,
    )
    outputs = dict(line.split("=", 1) for line in output.read_text().splitlines())
    return result, outputs


@pytest.mark.parametrize("name", sorted(_GATED))
def test_gate_resolves_the_profile_exactly_as_the_ci_planner(name):
    """One parser, copied: each gate's resolution block is byte-identical to the planner's.

    A reusable workflow cannot import code from this repository at its own tag -- the
    checkout it gets is the consumer's -- so the block is inlined in three places and this
    is what keeps them one definition.
    """
    planner = next(
        step
        for step in _load(_WORKFLOWS / "rhiza_ci.yml")["jobs"]["generate-matrix"]["steps"]
        if step.get("id") == "plan"
    )
    assert _resolution_block(_gate_script(name)) == _resolution_block(planner["run"])


@pytest.mark.parametrize("name", sorted(_GATED))
@pytest.mark.parametrize("profile", _PROFILES)
@pytest.mark.parametrize("event_name", _EVENTS)
def test_gate_skips_only_pull_requests_under_lean_and_standard(consumer, name, profile, event_name):
    """Lean and Standard skip PRs; pushes, schedules and manual runs always run; Comprehensive never skips."""
    result, outputs = _gate(name, consumer, profile, event_name)
    assert result.returncode == 0, result.stderr
    assert outputs["profile"] == (profile or "comprehensive")
    skipped = event_name == "pull_request" and profile in ("lean", "standard")
    assert outputs["run"] == json.dumps(not skipped)


@pytest.mark.parametrize("name", sorted(_GATED))
@pytest.mark.parametrize("raw", ['profile = "unknown"', 'profile = ""', "profile = true", 'profiel = "lean"'])
def test_invalid_profiles_fail_the_gate(consumer, name, raw):
    """A mistyped preset fails loudly rather than quietly skipping the optional workflow."""
    result, outputs = _gate(name, consumer, raw=raw)
    assert result.returncode != 0
    assert not outputs


@pytest.mark.parametrize("name", sorted(_GATED))
def test_every_expensive_job_waits_on_the_gate(name):
    """Each guarded job needs the gate and runs only on its verdict; the rest inherit the skip.

    A job reached only through a skipped job is skipped too, unless its condition calls a
    status function -- so no job may use ``always()`` or ``failure()`` to escape it.
    """
    jobs = _load(_WORKFLOWS / name)["jobs"]
    _, guarded = _GATED[name]
    for job_id in guarded:
        assert jobs[job_id]["needs"] == "profile"
        assert jobs[job_id]["if"] == "needs.profile.outputs.run == 'true'"
    for job_id, job in jobs.items():
        if job_id == "profile":
            continue
        assert job.get("needs"), f"{name}: {job_id} does not wait on the profile gate"
        condition = str(job.get("if", ""))
        assert "always()" not in condition
        assert "failure()" not in condition


@pytest.mark.parametrize("name", sorted(_GATED))
def test_gate_job_is_cheap_and_hardened(name):
    """The gate checks out, reads one file and exits: no uv, no matrix, a short budget."""
    job = _load(_WORKFLOWS / name)["jobs"]["profile"]
    assert job["runs-on"] == "ubuntu-latest"
    assert job["timeout-minutes"] <= 5
    assert job["permissions"] == {"contents": "read"}
    assert "strategy" not in job
    assert job["steps"][0]["uses"].startswith("step-security/harden-runner@")
    assert not any("setup-uv" in step.get("uses", "") for step in job["steps"])


def test_codeql_switch_moved_onto_the_gate():
    """CODEQL_ENABLED guards the gate, so a disabled CodeQL starts no runner at all."""
    jobs = _load(_WORKFLOWS / "rhiza_codeql.yml")["jobs"]
    assert jobs["profile"]["if"] == _CODEQL_ENABLED
    assert "CODEQL_ENABLED" not in jobs["analyze"]["if"]


def test_marimo_gate_is_unconditional():
    """Marimo had no repository switch, so its gate runs on every trigger."""
    assert "if" not in _load(_WORKFLOWS / "rhiza_marimo.yml")["jobs"]["profile"]


@pytest.mark.parametrize(
    ("name", "stub"),
    [(name, stub) for name, (stub, _) in sorted(_GATED.items())]
    + [("rhiza_benchmark.yml", "bundles/github-tests/.github/workflows/rhiza_benchmark.yml")],
)
def test_stub_triggers_match_the_reusable_workflow(name, stub):
    """The stub a consumer runs and the workflow this repo runs fire on the same events.

    Both offer manual dispatch, which is how a Lean or Standard project runs an optional
    workflow for a PR branch on demand.
    """
    live = dict(_triggers(_load(_WORKFLOWS / name)))
    live.pop("workflow_call")
    assert _triggers(_load(_ROOT / stub)) == live
    assert "workflow_dispatch" in live


def test_benchmark_needs_no_gate_because_it_never_runs_on_pull_requests():
    """Benchmarks run on default-branch pushes in every profile, so there is nothing to gate."""
    workflow = _load(_WORKFLOWS / "rhiza_benchmark.yml")
    assert "pull_request" not in _triggers(workflow)
    assert "profile" not in workflow["jobs"]


def test_book_deploys_only_from_the_default_branch():
    """The book never runs on PRs, and deploys only from the default branch in every profile."""
    stub = _load(_ROOT / "bundles/github-book/.github/workflows/rhiza_book.yml")
    assert "pull_request" not in _triggers(stub)
    deploy = _load(_WORKFLOWS / "rhiza_book.yml")["jobs"]["deploy"]["if"]
    assert "github.ref_name == github.event.repository.default_branch" in deploy
