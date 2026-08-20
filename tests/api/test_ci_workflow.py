"""Tests for the rhiza_ci.yml workflow configuration."""

from __future__ import annotations

import json
import re
import subprocess  # nosec B404
import sys
from pathlib import Path

import pytest
import yaml

MULTI_OS_MATRIX = 'RHIZA_CI_OS_MATRIX=["ubuntu-latest","windows-latest"]'
WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_ci.yml"

# ci-os-matrix relies on `printf` from a POSIX shell; MinGW make on Windows
# doesn't reproduce the same stdout, and JSON quoting in make variable
# assignments is incompatible with cmd.exe expansion.
_skip_on_windows = pytest.mark.skipif(
    sys.platform == "win32", reason="ci-os-matrix requires a POSIX shell (not available on Windows)"
)


# The two `make -f .rhiza/rhiza.mk ci-os-matrix` tests lived here. That recipe retired with
# `rhiza.mk`; the value now comes from `uvx rhiza-task ci-os-matrix`, which is what the workflow
# has called since #1546 and what the test below asserts. rhiza-task tests the resolution itself
# (including the empty-string-means-unset rule the per-caller matrix depends on), so re-testing it
# through a make wrapper that no longer exists would be testing nothing.


def test_ci_generate_matrix_reads_the_os_matrix_from_the_cli(root):
    """The OS matrix must come from a pinned rhiza-task, not from a make file path.

    This step used to run ``make -f .rhiza/rhiza.mk -s ci-os-matrix``, which put a
    *file path* into the reusable contract: a consumer that has replaced the synced make
    layer with the ``rhiza-task`` CLI then has to keep a stub at exactly that path, whose
    only caller is this step. Both readers take the value from ``.rhiza/.env``, so the
    switch changes nothing for a repo still on the make layer.

    The pin is asserted too. An unpinned ``uvx rhiza-task ci-os-matrix`` would let the
    matrix a build runs on move under a workflow that is itself called at a tag.
    """
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    steps = workflow["jobs"]["generate-matrix"]["steps"]
    os_step = next(step for step in steps if step.get("id") == "os")

    assert re.search(r"uvx rhiza-task@\d+\.\d+\.\d+ ci-os-matrix", os_step["run"]), (
        f"the OS matrix step must call a pinned rhiza-task, got: {os_step['run']!r}"
    )
    assert ".rhiza/rhiza.mk" not in os_step["run"], (
        "naming .rhiza/rhiza.mk here forces every migrated consumer to keep a stub at that path for this one step"
    )
    assert any("astral-sh/setup-uv@" in step.get("uses", "") for step in steps), (
        "generate-matrix installs no uv, so `uvx` would not be on PATH"
    )


def test_ci_security_job_runs_security_scans(root):
    """CI security job must run the security scans through the rhiza-task CLI."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    security_job = workflow["jobs"]["security"]
    run_steps = [step.get("run", "") for step in security_job.get("steps", [])]

    assert any('uvx "$RHIZA_TASK" security' in run for run in run_steps)


def test_ci_jobs_define_timeout_budgets(root):
    """CI jobs must define explicit timeout budgets."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    jobs = workflow["jobs"]
    expected = {
        "generate-matrix": 5,
        "test": 20,
        "lowest-deps": 20,
        "typecheck": 5,
        "deptry": 5,
        "pre-commit": 5,
        "docs-coverage": 10,
        "security": 10,
        "license": 10,
        "rhiza-test": 5,
        "ci-gate": 5,
    }

    for job_name, timeout in expected.items():
        assert jobs[job_name]["timeout-minutes"] == timeout


def _gates_named_by_all(root: Path) -> list[str]:
    """Return the gate names ``all`` depends on, from the rhiza-task registry.

    The registry is keyed ``layer:name`` and populated by the ``@task`` decorator, so the
    task modules have to be imported before it is read. Only this repo's layer is consulted:
    ``rust:all`` and ``go:all`` name a slightly different set, and asserting a Rust gate runs
    in a Python repo's CI would be nonsense.

    Args:
        root: Repository root, used to locate the Makefile carrying the pin.

    Returns:
        The prerequisite gate names, in declaration order.
    """
    pin = re.search(r"^RHIZA_TASK \?= (\S+)", (root / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    assert pin, "the root Makefile no longer pins RHIZA_TASK"
    name, _, version = pin.group(1).partition("@")
    script = (
        "import importlib, json;"
        "[importlib.import_module('rhiza_task.tasks.' + m) for m in ('python', 'quality', 'book', 'extras', 'doctor')];"
        "from rhiza_task.spec import REGISTRY;"
        "print(json.dumps(list(REGISTRY['python:all'].needs)))"
    )
    proc = subprocess.run(  # nosec B603
        [
            "uv",
            "run",
            "--quiet",
            "--no-project",
            "--with",
            f"{name}=={version}" if version else name,
            "python",
            "-c",
            script,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    gates = json.loads(proc.stdout)
    assert gates, "the registry reports no prerequisites for `all`, so this guard would be inert"
    return gates


def test_every_gate_named_by_make_all_runs_in_ci(root):
    """Each target `make all` names must be invoked by some CI job.

    `make all` is the local aggregate, and a target that only ever runs there is a gate
    in name only: it constrains one developer's habits, not the repo. `rhiza-test` was
    exactly that (#1523) — it ran the rhiza checks, including the doctests
    `RHIZA_DOCTEST_FOLDERS` scopes (#1517), and no workflow ever invoked it.

    Derived from `all`'s own prerequisite list rather than a hand-written set, so adding
    a gate to `all` without wiring it into CI fails here instead of passing silently. That
    list used to be the `all:` line in `python.mk`; since this repo moved to the rhiza-task
    shim it comes from the CLI's task registry instead, which is the same derivation against
    the new source of truth.
    """
    gates = _gates_named_by_all(root)

    workflows = (root / ".github" / "workflows").glob("*.yml")
    invoked = "\n".join(wf.read_text(encoding="utf-8") for wf in workflows)

    # Either interface counts: the gates run through `uvx "$RHIZA_TASK" <gate>` since
    # v1.4.0 retired the make layer, while the mother-repo-only `e2e` is a real Make rule
    # in this repo's own Makefile. What must hold is that some workflow invokes the gate.
    missing = [gate for gate in gates if f'uvx "$RHIZA_TASK" {gate}' not in invoked and f"make {gate}" not in invoked]
    assert not missing, (
        f"these targets are named by `make all` but no .github/workflows job runs them: "
        f"{missing}. A gate that runs only locally cannot block a pull request (#1523)."
    )


def test_ci_gate_rolls_up_rhiza_test(root):
    """The roll-up gate must depend on rhiza-test, which is what makes it *required*.

    Branch protection requires the "CI gate" context and not the per-job names, so a job
    absent from `needs` reports its own check run and blocks nothing. Adding rhiza-test
    to the roll-up is what gave it teeth without a seventh required context — which would
    have meant editing the ruleset, its bundle copy, and the sync test pinning the
    `ci / ` prefix between them.
    """
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    gate = workflow["jobs"]["ci-gate"]
    assert "rhiza-test" in gate["needs"], (
        f"ci-gate needs {gate['needs']}, which omits rhiza-test — so a failing "
        f"rhiza-test would not block the PR (#1523)."
    )

    run_script = next(s["run"] for s in gate["steps"] if "needs." in s.get("run", ""))
    assert "needs.rhiza-test.result" in run_script, (
        "ci-gate lists rhiza-test in `needs` but never inspects its result, so the job "
        "runs and its outcome is discarded."
    )


def test_ci_cache_keys_match_audit_policy(root):
    """CI cache keys must follow the documented shared key format."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    test_steps = workflow["jobs"]["test"]["steps"]
    uv_cache_step = next(step for step in test_steps if step.get("name") == "Cache uv artifacts")
    assert uv_cache_step["with"]["key"] == "${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}"

    # The job id stays `pre-commit` and its display name stays "Pre-commit hooks": that
    # name is a required status check in .github/rulesets/main-branch-protection.json,
    # so renaming it would leave every PR waiting on a context that never reports.
    # What the hook runner is called is a detail of the recipe; what the check is called
    # is a contract with branch protection.
    pre_commit_steps = workflow["jobs"]["pre-commit"]["steps"]
    prek_cache_step = next(step for step in pre_commit_steps if step.get("name") == "Cache prek environments")
    assert prek_cache_step["with"]["path"] == "~/.cache/prek", (
        "prek caches under ~/.cache/prek, not pre-commit's directory"
    )
    assert prek_cache_step["with"]["key"] == "${{ runner.os }}-prek-${{ hashFiles('.pre-commit-config.yaml') }}", (
        "the key still hashes .pre-commit-config.yaml — prek reads the same file"
    )


def test_ci_test_job_runs_make_under_bash(root):
    """CI test job must run the test gate under bash for Windows compatibility."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    run_tests_step = next(step for step in workflow["jobs"]["test"]["steps"] if step.get("name") == "Run tests")
    assert run_tests_step["shell"] == "bash"
    assert 'uvx "$RHIZA_TASK" test' in run_tests_step["run"]


def test_ci_typecheck_job_documents_ty_and_mypy(root):
    """CI typecheck job must advertise the ty+mypy cross-check."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    typecheck_steps = workflow["jobs"]["typecheck"]["steps"]
    typecheck_step = next(step for step in typecheck_steps if step.get("run") == 'uvx "$RHIZA_TASK" typecheck')
    assert "ty and mypy" in typecheck_step["name"]


def test_ci_workflow_header_documents_classifier_driven_matrix(root):
    """CI workflow header must document that Python classifiers drive the matrix."""
    content = (root / WORKFLOW_PATH).read_text(encoding="utf-8")
    assert "Programming Language :: Python :: 3.x" in content
    assert "Adding/removing classifiers updates CI Python coverage automatically" in content


def test_ci_workflow_generate_matrix_uses_baipp_classifier_output(root):
    """CI matrix generation must use BAIPP classifier output instead of rhiza-tools."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    generate_matrix = workflow["jobs"]["generate-matrix"]
    steps = generate_matrix["steps"]
    versions_step = next(step for step in steps if step.get("id") == "versions")
    versions_output_step = next(step for step in steps if step.get("id") == "versions-output")

    assert "hynek/build-and-inspect-python-package@" in versions_step["uses"]
    assert "supported_python_classifiers_json_array" in versions_output_step["run"]
    assert generate_matrix["outputs"]["matrix"] == "${{ steps.versions-output.outputs.list }}"
    assert "make -f .rhiza/rhiza.mk -s version-matrix" not in versions_output_step["run"]
