"""Execute the shipped CI planner and gate against consumer projects and Git histories."""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - executes checked-in workflow scripts and fixture git commands
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = yaml.safe_load((_ROOT / ".github/workflows/rhiza_ci.yml").read_text())
_JOBS = _WORKFLOW["jobs"]
_PLAN = next(s for s in _JOBS["generate-matrix"]["steps"] if s.get("id") == "plan")
_GATE = next(s for s in _JOBS["ci-gate"]["steps"] if s.get("name", "").startswith("Verify"))
_VERSIONS = ["3.12", "3.13", "3.14"]
_PLATFORMS = ["ubuntu-latest", "macos-latest"]
_QUALITY = {"deptry", "rhiza-test", "pre-commit", "docs-coverage", "security", "license"}


def _git(folder, *args):
    """Run Git in a disposable consumer repository."""
    return subprocess.check_output(["git", "-C", str(folder), *args], text=True).strip()


@pytest.fixture
def consumer(tmp_path):
    """Create a consumer with a committed application and primary Python version."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "consumer"\nversion = "0.1.0"\n')
    (tmp_path / ".python-version").write_text("3.13.2\n")
    (tmp_path / "app.py").write_text("value = 1\n")
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "CI test")
    _git(tmp_path, "config", "user.email", "ci@example.invalid")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "Initial project")
    return tmp_path


def _plan(consumer, profile=None, event_name="pull_request", event=None, full=False, versions=None, platforms=None):
    """Execute the actual workflow Python step, returning its machine-readable outputs."""
    if profile is not None:
        with (consumer / "pyproject.toml").open("a") as stream:
            stream.write(f"\n[tool.rhiza.ci]\nprofile = {json.dumps(profile)}\n")
    # Runner files live outside the checkout so Git diff cannot accidentally include them.
    event_file = consumer.parent / f"{consumer.name}-event.json"
    output_file = consumer.parent / f"{consumer.name}-output.txt"
    event_file.write_text(json.dumps(event or {}))
    output_file.write_text("")
    result = subprocess.run(
        [sys.executable, "-c", _PLAN["run"]],
        cwd=consumer,
        env={
            **os.environ,
            "GITHUB_EVENT_PATH": str(event_file),
            "GITHUB_EVENT_NAME": event_name,
            "GITHUB_OUTPUT": str(output_file),
            "FULL_VALIDATION": str(full).lower(),
            "VERSIONS": json.dumps(_VERSIONS if versions is None else versions),
            "PLATFORMS": json.dumps(_PLATFORMS if platforms is None else platforms),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    outputs = dict(line.split("=", 1) for line in output_file.read_text().splitlines())
    return result, outputs


@pytest.mark.parametrize("profile", [None, "lean", "standard", "comprehensive"])
@pytest.mark.parametrize(
    ("event_name", "full"),
    [
        ("pull_request", False),
        ("push", False),
        ("schedule", False),
        ("workflow_dispatch", False),
        ("workflow_dispatch", True),
    ],
)
def test_profile_execution_plan(consumer, profile, event_name, full):
    """Every preset retains quality/security gates and broadens compatibility on demand."""
    result, plan = _plan(consumer, profile, event_name=event_name, full=full)
    assert result.returncode == 0, result.stderr
    lean = profile == "lean"
    broad = full or event_name == "schedule"
    assert plan["profile"] == (profile or "comprehensive")
    assert plan["primary"] == "3.13"
    assert json.loads(plan["test_matrix"]) == (["3.13"] if lean and not broad else _VERSIONS)
    assert json.loads(plan["test_os"]) == (["ubuntu-latest"] if lean and not broad else _PLATFORMS)
    required = set(json.loads(plan["required_jobs"]))
    assert {"generate-matrix", "test"} <= required
    assert ("lowest-deps" in required) == (broad or profile in (None, "comprehensive"))
    assert ("typecheck" in required) == (not lean)
    assert ({"quality"} if lean else _QUALITY) <= required
    assert plan["run_tests"] == "true"


@pytest.mark.parametrize("profile", ["lean", "standard", "comprehensive"])
@pytest.mark.parametrize("event_name", ["pull_request", "push"])
@pytest.mark.parametrize(
    ("paths", "docs_only"),
    [
        (["README.md", "docs/guide.md", "docs/images/plot.svg"], True),
        (["README.md", "app.py"], False),
        (["docs/conf.py"], False),
        ([".github/workflows/check.yml"], False),
        (["mkdocs.yml"], False),
        (["pyproject.toml"], False),
    ],
)
def test_documentation_change_detection(consumer, profile, event_name, paths, docs_only):
    """Only a complete diff containing exclusively recognised docs may omit application tests."""
    base = _git(consumer, "rev-parse", "HEAD")
    for name in paths:
        path = consumer / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as stream:
            stream.write("\n# changed\n")
    _git(consumer, "add", ".")
    _git(consumer, "commit", "-qm", "Change project files")
    event = {"before": base, "pull_request": {"base": {"sha": base}}}
    result, plan = _plan(consumer, profile, event_name=event_name, event=event)
    assert result.returncode == 0, result.stderr
    required = set(json.loads(plan["required_jobs"]))
    assert plan["run_tests"] == str(not docs_only).lower()
    assert ("test" in required) == (not docs_only)
    if docs_only:
        assert not {"test", "typecheck", "lowest-deps"} & required
    assert ({"quality"} if profile == "lean" else _QUALITY) <= required


@pytest.mark.parametrize("base", ["", "0" * 40, "a" * 40, "--help"])
def test_unknown_history_never_suppresses_tests(consumer, base):
    """New branches, unavailable commits and invalid revisions retain application checks."""
    result, plan = _plan(consumer, "lean", event={"pull_request": {"base": {"sha": base}}})
    assert result.returncode == 0, result.stderr
    assert plan["run_tests"] == "true"


def test_empty_diff_still_runs_tests(consumer):
    """A diff with no files is not sufficient evidence of a documentation-only change."""
    base = _git(consumer, "rev-parse", "HEAD")
    result, plan = _plan(consumer, "lean", event={"pull_request": {"base": {"sha": base}}})
    assert result.returncode == 0, result.stderr
    assert plan["run_tests"] == "true"


def test_renaming_code_into_docs_does_not_hide_code_deletion(consumer):
    """Both sides of a rename count, so moving code into docs still triggers tests."""
    base = _git(consumer, "rev-parse", "HEAD")
    _git(consumer, "mv", "app.py", "README.md")
    _git(consumer, "commit", "-qm", "Move code to docs")
    result, plan = _plan(consumer, "lean", event={"pull_request": {"base": {"sha": base}}})
    assert result.returncode == 0, result.stderr
    assert plan["run_tests"] == "true"


@pytest.mark.parametrize("setting", ["unknown", "", True, ["lean"]])
def test_invalid_profiles_fail_planning(consumer, setting):
    """Mistyped presets fail explicitly rather than silently selecting reduced checks."""
    result, outputs = _plan(consumer, setting)
    assert result.returncode != 0
    assert not outputs


@pytest.mark.parametrize(
    ("versions", "platforms"),
    [([], _PLATFORMS), (["3.14"], _PLATFORMS), (_VERSIONS, []), (["3.13\ninvalid"], _PLATFORMS)],
)
def test_invalid_matrices_fail_planning(consumer, versions, platforms):
    """Empty matrices or an unsupported primary version cannot produce a green empty suite."""
    result, outputs = _plan(consumer, versions=versions, platforms=platforms)
    assert result.returncode != 0
    assert not outputs


def test_missing_primary_uses_first_classifier(consumer):
    """Consumers without .python-version use the first declared classifier."""
    (consumer / ".python-version").unlink()
    result, plan = _plan(consumer, "lean")
    assert result.returncode == 0, result.stderr
    assert plan["primary"] == _VERSIONS[0]


def _gate(plan, changes=None):
    """Execute the shipped roll-up gate with simulated GitHub job results."""
    required = set(json.loads(plan["required_jobs"]))
    results = {name: {"result": "success" if name in required else "skipped"} for name in _JOBS if name != "ci-gate"}
    results["generate-matrix"]["outputs"] = plan
    for name, value in (changes or {}).items():
        results[name]["result"] = value
    return subprocess.run(
        [sys.executable, "-c", _GATE["run"]],
        env={**os.environ, "RESULTS": json.dumps(results)},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("profile", ["lean", "standard", "comprehensive"])
def test_gate_accepts_only_planned_success_and_intentional_skips(consumer, profile):
    """Intentional profile skips pass; every planned job must complete successfully."""
    result, plan = _plan(consumer, profile)
    assert result.returncode == 0, result.stderr
    assert _gate(plan).returncode == 0
    for name in json.loads(plan["required_jobs"]):
        for status in ["failure", "cancelled", "skipped"]:
            gate = _gate(plan, {name: status})
            assert gate.returncode != 0, (name, status, gate.stdout, gate.stderr)
    if profile == "lean":
        assert _gate(plan, {"security": "failure"}).returncode != 0


def test_gate_covers_every_job_and_profile_uses_the_existing_security_gates():
    """The gate covers all branches and Lean runs the same pinned checks after authenticated setup."""
    assert set(_JOBS["ci-gate"]["needs"]) == set(_JOBS) - {"ci-gate"}
    quality = _JOBS["quality"]
    commands = [s["run"] for s in quality["steps"] if s.get("name", "").startswith("Run ") and "run" in s]
    assert commands == [
        f'uvx "$RHIZA_TASK" {task}'
        for task in ["fmt", "deps", "typecheck", "rhiza-test", "docs-coverage", "security", "license"]
    ]
    assert not any(s.get("continue-on-error") for s in quality["steps"])
    for name in _QUALITY:
        assert _JOBS[name]["needs"] == "generate-matrix"
        assert _JOBS[name]["if"] == "needs.generate-matrix.outputs.consolidated != 'true'"
    assert _JOBS["test"]["if"] == "needs.generate-matrix.outputs.run_tests == 'true'"
    assert _JOBS["lowest-deps"]["if"] == "needs.generate-matrix.outputs.run_lowest == 'true'"
    assert (
        _JOBS["typecheck"]["if"]
        == "needs.generate-matrix.outputs.consolidated != 'true' && needs.generate-matrix.outputs.run_tests == 'true'"
    )
    assert quality["if"] == "needs.generate-matrix.outputs.consolidated == 'true'"
    matrix = _JOBS["test"]["strategy"]["matrix"]
    assert "test_matrix" in matrix["python-version"]
    assert "test_os" in matrix["os"]


def test_consumer_triggers_preserve_feature_branch_prs_and_manual_full_validation():
    """Consumers schedule compatibility checks and suppress branch pushes without filtering PR targets."""
    stub = yaml.safe_load((_ROOT / "bundles/github-tests/.github/workflows/rhiza_ci.yml").read_text())
    for workflow in [stub, _WORKFLOW]:
        triggers = workflow.get("on", workflow.get(True))
        assert triggers["pull_request"] is None
        assert triggers["push"] is None
        assert triggers["schedule"]
        assert triggers["workflow_dispatch"]["inputs"]["full-validation"]["type"] == "boolean"
    condition = (
        "github.event_name != 'push' || github.ref == format('refs/heads/{0}', github.event.repository.default_branch)"
    )
    assert stub["jobs"]["ci"]["if"] == condition
    assert _JOBS["generate-matrix"]["if"] == condition
    assert _JOBS["ci-gate"]["if"] == f"always() && ({condition})"
    assert stub["jobs"]["ci"]["with"]["full-validation"] == "${{ inputs.full-validation || false }}"
    assert _PLAN["env"]["FULL_VALIDATION"] == "${{ inputs.full-validation || false }}"


@pytest.mark.parametrize("profile", ["lean", "standard", "comprehensive"])
def test_gate_accepts_documentation_plan(consumer, profile):
    """Omitting application tests on verified docs-only diffs still produces a valid gate."""
    base = _git(consumer, "rev-parse", "HEAD")
    (consumer / "README.md").write_text("# Documentation\n")
    _git(consumer, "add", ".")
    _git(consumer, "commit", "-qm", "Documentation")
    result, plan = _plan(consumer, profile, event={"pull_request": {"base": {"sha": base}}})
    assert result.returncode == 0, result.stderr
    assert plan["run_tests"] == "false"
    assert _gate(plan).returncode == 0


def test_pr_detection_uses_every_commit(consumer):
    """A final docs-only commit cannot hide earlier application changes in the same PR."""
    base = _git(consumer, "rev-parse", "HEAD")
    (consumer / "app.py").write_text("value = 2\n")
    _git(consumer, "add", ".")
    _git(consumer, "commit", "-qm", "Application change")
    (consumer / "README.md").write_text("# Documentation\n")
    _git(consumer, "add", ".")
    _git(consumer, "commit", "-qm", "Documentation")
    result, plan = _plan(consumer, "lean", event={"pull_request": {"base": {"sha": base}}})
    assert result.returncode == 0, result.stderr
    assert plan["run_tests"] == "true"


@pytest.mark.parametrize("primary", ["3.14", "3.13.1\n3.14", "pypy3.13", ""])
def test_primary_version_is_validated(consumer, primary):
    """An unsupported or ambiguous primary interpreter must not silently alter the test matrix."""
    (consumer / ".python-version").write_text(primary)
    result, plan = _plan(consumer, "lean", versions=["3.12", "3.13"])
    assert result.returncode != 0
    assert not plan


def test_unknown_profile_keys_fail_planning(consumer):
    """Misspelled configuration keys must not silently fall back to a default profile."""
    with (consumer / "pyproject.toml").open("a") as stream:
        stream.write('\n[tool.rhiza.ci]\nprofiel = "lean"\n')
    result, plan = _plan(consumer)
    assert result.returncode != 0
    assert not plan


def test_gate_rejects_empty_plan(consumer):
    """A missing required-job list cannot be mistaken for a successful empty run."""
    result, plan = _plan(consumer)
    assert result.returncode == 0, result.stderr
    plan["required_jobs"] = "[]"
    assert _gate(plan, {"generate-matrix": "success"}).returncode != 0
