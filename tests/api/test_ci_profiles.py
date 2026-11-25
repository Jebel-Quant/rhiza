"""Execute the shipped CI planner and gate against consumer projects and Git histories."""

from __future__ import annotations

import functools
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
_QUALITY = {"deptry", "rhiza-test", "pre-commit", "docs-coverage", "security", "license", "dist-check"}


def _git(folder, *args):
    """Run Git in a disposable consumer repository."""
    return subprocess.check_output(["git", "-C", str(folder), *args], text=True).strip()


def _init_consumer(folder):
    """Commit an application and primary Python version into ``folder``."""
    (folder / "pyproject.toml").write_text('[project]\nname = "consumer"\nversion = "0.1.0"\n')
    (folder / ".python-version").write_text("3.13.2\n")
    (folder / "app.py").write_text("value = 1\n")
    _git(folder, "init", "-b", "main")
    _git(folder, "config", "user.name", "CI test")
    _git(folder, "config", "user.email", "ci@example.invalid")
    _git(folder, "add", ".")
    _git(folder, "commit", "-qm", "Initial project")
    return folder


@pytest.fixture
def consumer(tmp_path):
    """Create a consumer with a committed application and primary Python version."""
    return _init_consumer(tmp_path)


def _plan(
    consumer,
    profile=None,
    event_name="pull_request",
    event=None,
    full=False,
    versions=None,
    platforms=None,
    runners=None,
):
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
            "TEST_RUNNER": "",
            "QUALITY_RUNNER": "",
            **(runners or {}),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    outputs = dict(line.split("=", 1) for line in output_file.read_text().splitlines())
    return result, outputs


@pytest.fixture(scope="module")
def planned(tmp_path_factory):
    """Plan each preset and trigger once, in its own consumer, for the tests that split its properties."""

    @functools.cache
    def plan(profile, event_name, full):
        """Run the planner for one preset and trigger, failing with its stderr if planning fails."""
        project = _init_consumer(tmp_path_factory.mktemp("planned"))
        result, outputs = _plan(project, profile, event_name=event_name, full=full)
        assert result.returncode == 0, result.stderr
        return outputs

    return plan


def _scope(profile, event_name, full):
    """Return whether a preset plans a narrow matrix on a trigger, and whether it adds lowest-deps."""
    broad = full or event_name == "schedule"
    narrow = profile == "lean" and not broad
    lowest = broad or profile in (None, "comprehensive")
    return narrow, lowest


# Every preset on every trigger. One property per test (#1807): this was one C-rated function.
_PRESETS = pytest.mark.parametrize("profile", [None, "lean", "standard", "comprehensive"])
_TRIGGERS = pytest.mark.parametrize(
    ("event_name", "full"),
    [
        ("pull_request", False),
        ("push", False),
        ("schedule", False),
        ("workflow_dispatch", False),
        ("workflow_dispatch", True),
    ],
)


@_PRESETS
@_TRIGGERS
def test_profile_execution_plan(planned, profile, event_name, full):
    """Every preset names itself, plans the primary version and runs the application tests."""
    plan = planned(profile, event_name, full)
    assert plan["profile"] == (profile or "comprehensive")
    assert plan["primary"] == "3.13"
    assert plan["run_tests"] == "true"


@_PRESETS
@_TRIGGERS
def test_profile_matrix_broadens_compatibility_on_demand(planned, profile, event_name, full):
    """Only Lean narrows the matrix, and a schedule or full validation broadens it again."""
    plan = planned(profile, event_name, full)
    narrow, _ = _scope(profile, event_name, full)
    assert json.loads(plan["test_matrix"]) == (["3.13"] if narrow else _VERSIONS)
    assert json.loads(plan["test_os"]) == (["ubuntu-latest"] if narrow else _PLATFORMS)


@_PRESETS
@_TRIGGERS
def test_profile_retains_quality_and_security_gates(planned, profile, event_name, full):
    """Every preset retains quality/security gates; lowest-deps and typecheck follow the preset."""
    plan = planned(profile, event_name, full)
    _, lowest = _scope(profile, event_name, full)
    lean = profile == "lean"
    required = set(json.loads(plan["required_jobs"]))
    assert {"generate-matrix", "test"} <= required
    assert ("lowest-deps" in required) == lowest
    assert ("typecheck" in required) == (not lean)
    assert ({"quality"} if lean else _QUALITY) <= required


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


# The gate and job wiring, one property per test (#1807): this was one C-rated function, in
# which the first wrong condition hid every later one.
_QUALITY_TASKS = ["fmt", "deps", "typecheck", "rhiza-test", "docs-coverage", "security", "license", "dist-check"]
_PLANNED = "needs.generate-matrix.outputs"
_CONDITIONS = {
    "test": f"{_PLANNED}.run_tests == 'true'",
    "lowest-deps": f"{_PLANNED}.run_lowest == 'true'",
    "typecheck": f"{_PLANNED}.consolidated != 'true' && {_PLANNED}.run_tests == 'true'",
    "quality": f"{_PLANNED}.consolidated == 'true'",
}
_STUB = yaml.safe_load((_ROOT / "bundles/github-tests/.github/workflows/rhiza_ci.yml").read_text())
_DEFAULT_BRANCH_ONLY_PUSH = (
    "github.event_name != 'push' || github.ref == format('refs/heads/{0}', github.event.repository.default_branch)"
)
_FULL_VALIDATION = "${{ inputs.full-validation || false }}"


def _run_commands(job):
    """Return the commands of a job's ``Run ...`` steps, in order."""
    named = [s for s in job["steps"] if s.get("name", "").startswith("Run ")]
    return [s["run"] for s in named if "run" in s]


def test_gate_covers_every_job():
    """The gate needs every other job, so no branch of the plan escapes the roll-up."""
    assert set(_JOBS["ci-gate"]["needs"]) == set(_JOBS) - {"ci-gate"}


def test_consolidated_quality_runs_the_existing_security_gates():
    """Lean runs the same pinned checks as the split jobs, after authenticated setup, and none may fail open."""
    quality = _JOBS["quality"]
    assert _run_commands(quality) == [f'uvx "$RHIZA_TASK" {task}' for task in _QUALITY_TASKS]
    assert not any(s.get("continue-on-error") for s in quality["steps"])


@pytest.mark.parametrize("name", sorted(_QUALITY))
def test_split_quality_jobs_yield_to_the_consolidated_job(name):
    """Each split quality job follows the plan and stands down when Lean consolidates them."""
    assert _JOBS[name]["needs"] == "generate-matrix"
    assert _JOBS[name]["if"] == f"{_PLANNED}.consolidated != 'true'"


@pytest.mark.parametrize(("name", "condition"), _CONDITIONS.items())
def test_planned_jobs_run_on_their_plan_output(name, condition):
    """Test, lowest-deps, typecheck and the consolidated quality job each run on their plan output."""
    assert _JOBS[name]["if"] == condition


def test_test_matrix_comes_from_the_plan():
    """The test job's Python versions and platforms are the planned ones."""
    matrix = _JOBS["test"]["strategy"]["matrix"]
    assert "test_matrix" in matrix["python-version"]
    assert "test_os" in matrix["os"]


@pytest.mark.parametrize("workflow", [_STUB, _WORKFLOW], ids=["stub", "reusable"])
def test_consumer_triggers_preserve_feature_branch_prs_and_manual_full_validation(workflow):
    """Consumers schedule compatibility checks and offer full validation without filtering PR targets."""
    triggers = workflow.get("on", workflow.get(True))
    assert triggers["pull_request"] is None
    assert triggers["push"] is None
    assert triggers["schedule"]
    assert triggers["workflow_dispatch"]["inputs"]["full-validation"]["type"] == "boolean"


def test_consumer_suppresses_branch_pushes():
    """Only default-branch pushes run, in the stub and in every entry job of the reusable workflow."""
    assert _STUB["jobs"]["ci"]["if"] == _DEFAULT_BRANCH_ONLY_PUSH
    assert _JOBS["generate-matrix"]["if"] == _DEFAULT_BRANCH_ONLY_PUSH
    assert _JOBS["ci-gate"]["if"] == f"always() && ({_DEFAULT_BRANCH_ONLY_PUSH})"


def test_manual_full_validation_reaches_the_planner():
    """The stub forwards the dispatch input and the planner reads it, defaulting to false."""
    assert _STUB["jobs"]["ci"]["with"]["full-validation"] == _FULL_VALIDATION
    assert _PLAN["env"]["FULL_VALIDATION"] == _FULL_VALIDATION


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


# Runner selection (#1764): the caller's value reaches `runs-on` unchanged, or planning fails.
_QUALITY_JOBS = _QUALITY | {"typecheck", "quality"}
_TEST_JOBS = {"lowest-deps"}
_HOSTED_JOBS = {"generate-matrix", "ci-gate"}


def test_runner_inputs_are_declared_and_reach_the_planner_through_env():
    """Both inputs are optional strings, and the planner reads them only through its environment."""
    inputs = _WORKFLOW.get("on", _WORKFLOW.get(True))["workflow_call"]["inputs"]
    for name, env in [("test-runner", "TEST_RUNNER"), ("quality-runner", "QUALITY_RUNNER")]:
        assert inputs[name] == {**inputs[name], "type": "string", "default": ""}
        assert _PLAN["env"][env] == f"${{{{ inputs.{name} || '' }}}}"
        assert f"inputs.{name}" not in _PLAN["run"]


def test_every_job_runs_on_the_planned_runner_or_is_deliberately_hosted():
    """A new job cannot hard-code `ubuntu-latest` and silently escape the caller's selection."""
    planned = "${{ fromJSON(needs.generate-matrix.outputs.%s) }}"
    assert set(_JOBS) == _QUALITY_JOBS | _TEST_JOBS | _HOSTED_JOBS | {"test"}
    for name in _QUALITY_JOBS:
        assert _JOBS[name]["runs-on"] == planned % "quality_runner", name
    for name in _TEST_JOBS:
        assert _JOBS[name]["runs-on"] == planned % "test_runner", name
    for name in _HOSTED_JOBS:
        assert _JOBS[name]["runs-on"] == "ubuntu-latest", name
    outputs = _JOBS["generate-matrix"]["outputs"]
    assert outputs["test_runner"] == "${{ steps.plan.outputs.test_runner }}"
    assert outputs["quality_runner"] == "${{ steps.plan.outputs.quality_runner }}"


def test_only_linux_test_entries_move_and_platform_selectors_survive():
    """`matrix.os` stays the platform name, so coverage upload still selects one Linux job."""
    test = _JOBS["test"]
    assert test["runs-on"] == (
        "${{ matrix.os == 'ubuntu-latest' && fromJSON(needs.generate-matrix.outputs.test_runner) || matrix.os }}"
    )
    selectors = [step.get("if", "") for step in test["steps"]]
    assert sum("matrix.os == 'ubuntu-latest'" in condition for condition in selectors) >= 2


def test_runners_default_to_hosted_ubuntu(consumer):
    """No selection keeps today's runner for every routed job."""
    result, outputs = _plan(consumer)
    assert result.returncode == 0, result.stderr
    assert json.loads(outputs["test_runner"]) == "ubuntu-latest"
    assert json.loads(outputs["quality_runner"]) == "ubuntu-latest"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("private-linux", "private-linux"),
        ("  private-linux  ", "private-linux"),
        ('"private-linux"', "private-linux"),
        ('["private-linux", "ci-run-123-1"]', ["private-linux", "ci-run-123-1"]),
        ('{"group": "private"}', {"group": "private"}),
        ('{"group": "private", "labels": ["linux", "x64"]}', {"group": "private", "labels": ["linux", "x64"]}),
        ('{"labels": "linux"}', {"labels": "linux"}),
    ],
)
@pytest.mark.parametrize("variable", ["TEST_RUNNER", "QUALITY_RUNNER"])
def test_valid_runner_selections_pass_through(consumer, variable, raw, expected):
    """Every `runs-on` shape survives planning unchanged, and the other selection keeps its default."""
    result, outputs = _plan(consumer, runners={variable: raw})
    assert result.returncode == 0, result.stderr
    key, other = ("test_runner", "quality_runner") if variable == "TEST_RUNNER" else ("quality_runner", "test_runner")
    assert json.loads(outputs[key]) == expected
    assert json.loads(outputs[other]) == "ubuntu-latest"


@pytest.mark.parametrize(
    "raw",
    [
        "[]",
        '[""]',
        '["linux", 3]',
        '""',
        "{}",
        '{"group": ""}',
        '{"labels": []}',
        '{"group": "private", "os": "linux"}',
        '["unterminated"',
        '"multi\\nline"',
    ],
)
@pytest.mark.parametrize("variable", ["TEST_RUNNER", "QUALITY_RUNNER"])
def test_invalid_runner_selections_fail_planning(consumer, variable, raw):
    """A malformed selection fails in the planner rather than queueing a job that never starts."""
    result, outputs = _plan(consumer, runners={variable: raw})
    assert result.returncode != 0
    assert variable in result.stderr
    assert not outputs


@pytest.mark.parametrize("profile", ["lean", "standard", "comprehensive"])
@pytest.mark.parametrize("full", [False, True])
def test_runner_selection_never_changes_the_plan(consumer, profile, full):
    """Choosing a runner preserves the profile's Python versions, platforms and required jobs."""
    _, default = _plan(consumer, profile, event_name="workflow_dispatch", full=full)
    _, routed = _plan(
        consumer,
        event_name="workflow_dispatch",
        full=full,
        runners={"TEST_RUNNER": '["private-linux"]', "QUALITY_RUNNER": '{"group": "private"}'},
    )
    ignored = {"test_runner", "quality_runner"}
    assert {k: v for k, v in routed.items() if k not in ignored} == {
        k: v for k, v in default.items() if k not in ignored
    }
