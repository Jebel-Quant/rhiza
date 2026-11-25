"""Exercise the provider-neutral setup contract before private dependency resolution."""

from __future__ import annotations

import functools
import os
import subprocess  # nosec B404 - executes the checked-in action shell in fixture projects
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = _ROOT / ".github/workflows/rhiza_ci.yml"


@pytest.mark.parametrize(
    ("event", "head", "exists", "success"),
    [
        ("push", "", False, False),
        ("push", "", True, True),
        ("pull_request", "acme/project", True, True),
        ("pull_request", "fork/project", True, False),
        ("pull_request_target", "acme/project", True, False),
    ],
)
def test_setup_guard(tmp_path, event, head, exists, success):
    """Enabled setup requires a caller action and refuses untrusted events."""
    if exists:
        action = tmp_path / ".github/actions/rhiza-setup/action.yaml"
        action.parent.mkdir(parents=True)
        action.write_text("name: setup\n")
    steps = yaml.safe_load(_WORKFLOW.read_text())["jobs"]["test"]["steps"]
    guard = next(s for s in steps if s.get("name") == "Validate consumer dependency setup")
    call = next(s for s in steps if s.get("name") == "Run consumer dependency setup")
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", guard["run"]],
        cwd=tmp_path,
        env={
            **os.environ,
            "EVENT_NAME": event,
            "HEAD_REPOSITORY": head,
            "CALLER_REPOSITORY": "acme/project",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert (result.returncode == 0) == success, result.stdout + result.stderr
    assert call["uses"] == "./.github/actions/rhiza-setup"
    assert call["if"] == "${{ vars.RHIZA_SETUP_ENABLED == 'true' }}"
    assert not call.get("continue-on-error")


# Each supported job, and the first step in it that consumes dependencies. Setup must run
# before that step. One property per test (#1798): this was a single D-rated function in
# which the first failing job hid every later one.
_CI_GATES = (
    "test",
    "quality",
    "lowest-deps",
    "typecheck",
    "deptry",
    "rhiza-test",
    "docs-coverage",
    "security",
    "license",
    "dist-check",
)
_CONSUMERS = {
    "ci": {
        "generate-matrix": "Build package metadata and extract supported Python classifiers",
        **dict.fromkeys(_CI_GATES, "Configure git auth for private packages"),
    },
    "book": {"build": "Sync the virtual environment for ${{ github.repository }}"},
    "marimo": {"test-notebooks": "Run notebook"},
    "benchmark": {"benchmark": "Run benchmarks"},
    "weekly": {"dep-compat-test": "Resolve and install latest compatible dependencies", "semgrep": "Run Semgrep"},
    "release": {"build": "Build and validate distributions"},
}
_JOB_CASES = [
    (workflow, job, dependency) for workflow, consumers in _CONSUMERS.items() for job, dependency in consumers.items()
]
# The book accepts its legacy token as a fallback and keeps its own guard; every other
# workflow shares the CI guard verbatim.
_CREDENTIALS = {
    "book": "${{ secrets.RHIZA_SETUP_CREDENTIALS || secrets.BOOK_SETUP_TOKEN }}",
}
_PERMISSIONS = {
    "ci": {"contents": "read", "actions": "read"},
    "release": {"contents": "read", "id-token": "write", "attestations": "write"},
}


@functools.cache
def _definition(workflow):
    """Parse one live reusable workflow."""
    return yaml.safe_load((_ROOT / f".github/workflows/rhiza_{workflow}.yml").read_text())


def _setup_steps(workflow, job):
    """Return a job's steps, its setup call and its setup guard."""
    steps = _definition(workflow)["jobs"][job]["steps"]
    names = [s.get("name") for s in steps]
    call = steps[names.index("Run consumer dependency setup")]
    guard = steps[names.index("Validate consumer dependency setup")]
    return steps, call, guard


@pytest.mark.parametrize(("workflow", "job", "dependency"), _JOB_CASES)
def test_setup_before_dependency_resolution(workflow, job, dependency):
    """Every supported job authenticates before its first dependency-consuming step."""
    steps, call, guard = _setup_steps(workflow, job)
    names = [s.get("name") for s in steps]
    assert names.index("Run consumer dependency setup") < names.index(dependency)
    assert steps.index(guard) < steps.index(call)


@pytest.mark.parametrize(("workflow", "job", "dependency"), _JOB_CASES)
def test_setup_call_contract(workflow, job, dependency):
    """The call uses the caller's action with the forwarded credential and no extra env."""
    _, call, _ = _setup_steps(workflow, job)
    assert "env" not in call
    assert call["uses"] == "./.github/actions/rhiza-setup"
    assert call["with"]["credentials"] == _CREDENTIALS.get(workflow, "${{ secrets.RHIZA_SETUP_CREDENTIALS }}")


@pytest.mark.parametrize(("workflow", "job", "dependency"), [c for c in _JOB_CASES if c[0] != "book"])
def test_setup_guard_is_shared(workflow, job, dependency):
    """Outside the book, every job runs the CI guard verbatim, under the call's condition."""
    _, call, guard = _setup_steps(workflow, job)
    _, _, reference = _setup_steps(*_JOB_CASES[0][:2])
    assert guard == reference
    assert guard["if"] == call["if"]


@pytest.mark.parametrize(("workflow", "job", "dependency"), _JOB_CASES)
def test_setup_job_permissions(workflow, job, dependency):
    """Jobs get read access plus only what their workflow needs, never pages."""
    expected = _PERMISSIONS.get(workflow, {"contents": "read"})
    assert "pages" not in expected
    assert _definition(workflow)["jobs"][job]["permissions"] == expected
    if workflow != "release":
        assert _definition(workflow)["permissions"] == expected


@pytest.mark.parametrize("workflow", list(_CONSUMERS))
def test_setup_workflow_has_no_provider_configuration(workflow):
    """No provider-specific setup is baked in, and the setup credential is optional."""
    definition = _definition(workflow)
    text = str(definition)
    assert "CODEARTIFACT_" not in text
    assert "AWS_ROLE_TO_ASSUME_READ" not in text
    triggers = definition.get("on") or definition[True]
    assert triggers["workflow_call"]["secrets"]["RHIZA_SETUP_CREDENTIALS"]["required"] is False


def test_setup_has_no_synced_dispatcher_or_provider_configuration():
    """Consumers own setup code; guards travel with the versioned reusable workflow."""
    for bundle in (_ROOT / "bundles").iterdir():
        for action in ("rhiza-setup", "rhiza-consumer-setup", "release-publish"):
            assert not (bundle / f".github/actions/{action}").exists()
    for workflow in ("ci", "book", "marimo", "benchmark", "weekly", "release"):
        text = (_ROOT / f".github/workflows/rhiza_{workflow}.yml").read_text()
        assert "RHIZA_SETUP_VARS" not in text
        assert "rhiza-consumer-setup" not in text
    ci = yaml.safe_load(_WORKFLOW.read_text())
    assert not any("consumer dependency setup" in s.get("name", "") for s in ci["jobs"]["pre-commit"]["steps"])
    for path in (_ROOT / "bundles").glob("*/.github/workflows/*.yml"):
        if path.name in {"rhiza_ci.yml", "rhiza_benchmark.yml", "rhiza_marimo.yml", "rhiza_weekly.yml"}:
            assert "id-token: write" not in path.read_text()


@pytest.mark.parametrize(
    ("index", "expected"), [("private--feed", "PRIVATE__FEED"), ("_private.feed-", "_PRIVATE_FEED_")]
)
def test_codeartifact_example_preserves_uv_index_names(tmp_path, index, expected):
    """The optional provider example follows uv's character-by-character naming convention."""
    action = yaml.safe_load((_ROOT / "examples/dependency-setup/codeartifact/action.yml").read_text())
    output = tmp_path / "output"
    configuration = {
        "AWS_REGION": "eu-west-2",
        "AWS_ROLE_TO_ASSUME_READ": "arn:aws:iam::123456789012:role/read",
        "CODEARTIFACT_DOMAIN": "example",
        "CODEARTIFACT_DOMAIN_OWNER": "123456789012",
        "CODEARTIFACT_UV_INDEX": index,
    }
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", action["runs"]["steps"][0]["run"]],
        cwd=tmp_path,
        env={**os.environ, **configuration, "GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"normalized_index={expected}" in output.read_text().splitlines()


def test_book_build_does_not_inherit_deployment_permissions():
    """Even a deployment-capable caller cannot widen the book build's explicit scope."""
    definition = yaml.safe_load((_ROOT / ".github/workflows/rhiza_book.yml").read_text())
    stub = yaml.safe_load((_ROOT / "bundles/github-book/.github/workflows/rhiza_book.yml").read_text())
    caller = stub["jobs"]["book"]["permissions"]
    assert caller == {"contents": "read", "pages": "write", "id-token": "write"}
    build = definition["jobs"]["build"]
    assert definition["permissions"] == {"contents": "read"}
    assert build["permissions"] == {"contents": "read"}
    assert "pages" not in build["permissions"]
    assert "id-token" not in build["permissions"]
    assert definition["jobs"]["deploy"]["permissions"] == caller
