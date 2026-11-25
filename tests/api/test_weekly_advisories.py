"""The weekly dependency-advisory audit, on GitHub and GitLab (#1804).

The Python layer's `security` task is bandit, which never looks at what is installed, while
rust-core and go-core audit dependencies. These jobs close that gap on a schedule instead of
in a gate, so an advisory published today notifies rather than failing somebody's pull
request. Each test pins one property the job comments promise.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_GITHUB = _ROOT / ".github" / "workflows" / "rhiza_weekly.yml"
_GITLAB = _ROOT / "bundles" / "gitlab" / ".gitlab" / "workflows" / "rhiza_weekly.yml"


@pytest.fixture(scope="module")
def github_job() -> dict:
    """Return the `advisories` job of the reusable GitHub weekly workflow."""
    jobs = yaml.safe_load(_GITHUB.read_text(encoding="utf-8"))["jobs"]
    assert "advisories" in jobs, "rhiza_weekly.yml has no advisories job"
    return jobs["advisories"]


@pytest.fixture(scope="module")
def gitlab_job() -> dict:
    """Return the `weekly:advisories` job of the GitLab weekly pipeline."""
    jobs = yaml.safe_load(_GITLAB.read_text(encoding="utf-8"))
    assert "weekly:advisories" in jobs, "the GitLab weekly pipeline has no weekly:advisories job"
    return jobs["weekly:advisories"]


@pytest.fixture(scope="module")
def github_commands(github_job: dict) -> list[str]:
    """Return the GitHub job's run commands, whitespace-normalised, in order."""
    return [" ".join(step["run"].split()) for step in github_job["steps"] if "run" in step]


@pytest.fixture(scope="module")
def gitlab_commands(gitlab_job: dict) -> list[str]:
    """Return the GitLab job's script lines, in order."""
    return list(gitlab_job["script"])


@pytest.fixture(params=["github", "gitlab"])
def commands(request: pytest.FixtureRequest) -> list[str]:
    """Return one platform's commands, so each property is asserted on both."""
    return request.getfixturevalue(f"{request.param}_commands")


def _export(commands: list[str]) -> str:
    """Return the single `uv export` command among a job's commands."""
    exports = [c for c in commands if c.startswith("uv export ")]
    assert len(exports) == 1, f"expected exactly one uv export, got {exports}"
    return exports[0]


def _audit(commands: list[str]) -> str:
    """Return the single pip-audit command among a job's commands."""
    audits = [c for c in commands if "pip-audit" in c]
    assert len(audits) == 1, f"expected exactly one pip-audit call, got {audits}"
    return audits[0]


def test_the_audit_reads_the_committed_lockfile(commands: list[str]) -> None:
    """`--frozen` audits what ships; resolving afresh would audit versions nobody uses."""
    assert "--frozen" in _export(commands).split()


def test_the_audit_covers_every_group_and_extra(commands: list[str]) -> None:
    """Dev and optional dependencies run in CI too, so they are audited with the rest."""
    flags = _export(commands).split()
    assert "--all-groups" in flags
    assert "--all-extras" in flags


def test_the_audit_runs_after_the_export_it_reads(commands: list[str]) -> None:
    """pip-audit reads the file the export just wrote, so it must come second."""
    assert commands.index(_export(commands)) < commands.index(_audit(commands))


def test_the_audit_reads_the_exported_file(commands: list[str]) -> None:
    """The `-o` target of the export is the `-r` input of the audit."""
    export, audit = _export(commands).split(), _audit(commands).split()
    assert export[export.index("-o") + 1] == audit[audit.index("-r") + 1]


def test_the_audit_never_resolves_or_installs(commands: list[str]) -> None:
    """`--disable-pip` over the hashed export needs no consumer setup and no private-index credentials."""
    assert "--disable-pip" in _audit(commands).split()


def test_the_github_audit_is_not_silenced(github_job: dict) -> None:
    """Red is the signal; on a schedule it blocks nothing, so continue-on-error would only hide it."""
    assert not github_job.get("continue-on-error")
    assert not any(step.get("continue-on-error") for step in github_job["steps"])


def test_the_gitlab_scheduled_audit_is_not_silenced(gitlab_job: dict) -> None:
    """Only the manual web trigger may fail softly; the scheduled run must go red."""
    scheduled = [r for r in gitlab_job["rules"] if r.get("if") == '$CI_PIPELINE_SOURCE == "schedule"']
    assert scheduled, "weekly:advisories does not run on the schedule"
    assert not scheduled[0].get("allow_failure")
    assert not gitlab_job.get("allow_failure")


def test_the_github_audit_reads_no_secrets() -> None:
    """Nothing in the job needs a credential, so none is referenced -- a wider blast radius buys nothing."""
    job_text = yaml.safe_dump(yaml.safe_load(_GITHUB.read_text(encoding="utf-8"))["jobs"]["advisories"])
    assert "secrets." not in job_text
