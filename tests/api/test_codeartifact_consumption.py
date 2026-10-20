"""Tests for opt-in AWS CodeArtifact dependency consumption in workflows."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - executes workflow/action shell in isolated temp dirs
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_ACTION = _ROOT / ".github" / "actions" / "rhiza-codeartifact-consume" / "action.yml"
_BASH = shutil.which("bash")


def _load_yaml(path: Path) -> dict:
    """Load a YAML document from ``path``."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _run(script: str, cwd: Path, **env: str) -> subprocess.CompletedProcess:
    """Run a shell script with GitHub's fail-fast bash flags."""
    if _BASH is None:
        pytest.skip("bash is not available")
    return subprocess.run(  # nosec B603
        [_BASH, "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
        cwd=cwd,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        check=False,
    )


def _step(workflow: dict, job: str, name: str) -> dict:
    """Return a uniquely named step from a workflow job."""
    matches = [step for step in workflow["jobs"][job]["steps"] if step.get("name") == name]
    assert len(matches) == 1, f"Expected one step named {name!r} in job {job!r}, found {len(matches)}"
    return matches[0]


def test_action_is_opt_in_and_exports_uv_named_index_credentials() -> None:
    """The helper must stay disabled by default and write uv-compatible credentials."""
    action = _load_yaml(_ACTION)
    inputs = action["inputs"]
    assert inputs["enabled"]["default"] == "false"
    assert "CODEARTIFACT_CONSUMPTION_ENABLED" in _ACTION.read_text(encoding="utf-8")

    export_step = next(
        step for step in action["runs"]["steps"] if step.get("name") == "Export uv named-index credentials"
    )
    script = export_step["run"]
    assert "aws codeartifact get-authorization-token" in script
    assert "UV_INDEX_${NORMALIZED_INDEX}_USERNAME=aws" in script
    assert "UV_INDEX_${NORMALIZED_INDEX}_PASSWORD=$token" in script


def test_action_validation_script_guards_and_normalizes(tmp_path: Path) -> None:
    """Run the action's validation shell for disabled/missing/fork/valid cases."""
    action = _load_yaml(_ACTION)
    validate = next(step for step in action["runs"]["steps"] if step.get("id") == "validate")
    script = validate["run"]

    output = tmp_path / "out"
    base_env = {
        "GITHUB_OUTPUT": str(output),
        "INPUT_AWS_REGION": "eu-west-2",
        "INPUT_AWS_ROLE_TO_ASSUME_READ": "arn:aws:iam::123456789012:role/rhiza-read",
        "INPUT_CODEARTIFACT_DOMAIN": "example-domain",
        "INPUT_CODEARTIFACT_DOMAIN_OWNER": "123456789012",
        "INPUT_CODEARTIFACT_UV_INDEX": "private.feed",
        "EVENT_NAME": "push",
        "HEAD_REPOSITORY": "acme/project",
        "CALLER_REPOSITORY": "acme/project",
    }

    output.write_text("", encoding="utf-8")
    disabled = _run(script, tmp_path, **base_env, INPUT_ENABLED="false")
    assert disabled.returncode == 0
    assert "enabled=false" in output.read_text(encoding="utf-8")

    output.write_text("", encoding="utf-8")
    missing_env = {**base_env, "INPUT_ENABLED": "true", "INPUT_AWS_REGION": ""}
    missing = _run(script, tmp_path, **missing_env)
    assert missing.returncode != 0
    assert "required settings are missing" in missing.stdout

    output.write_text("", encoding="utf-8")
    fork_env = {
        **base_env,
        "INPUT_ENABLED": "true",
        "EVENT_NAME": "pull_request",
        "HEAD_REPOSITORY": "fork/project",
    }
    fork_pr = _run(script, tmp_path, **fork_env)
    assert fork_pr.returncode != 0
    assert "not allowed on fork pull requests or pull_request_target" in fork_pr.stdout

    output.write_text("", encoding="utf-8")
    valid_env = {
        **base_env,
        "INPUT_ENABLED": "true",
        "INPUT_CODEARTIFACT_UV_INDEX": "private.feed-v2",
    }
    valid = _run(script, tmp_path, **valid_env)
    assert valid.returncode == 0
    action_output = output.read_text(encoding="utf-8")
    assert "enabled=true" in action_output
    assert "normalized_index=PRIVATE_FEED_V2" in action_output


def test_consuming_workflows_authenticate_before_private_dependency_resolution() -> None:
    """Supported jobs must run the helper before their first relevant dependency step."""
    helper = "Configure CodeArtifact credentials for uv named indexes"

    ci = _load_yaml(_ROOT / ".github/workflows/rhiza_ci.yml")
    ci_jobs = [
        "test",
        "lowest-deps",
        "typecheck",
        "deptry",
        "rhiza-test",
        "pre-commit",
        "docs-coverage",
        "security",
        "license",
    ]
    for job in ci_jobs:
        steps = ci["jobs"][job]["steps"]
        auth_idx = steps.index(_step(ci, job, helper))
        git_auth_idx = steps.index(_step(ci, job, "Configure git auth for private packages"))
        assert auth_idx < git_auth_idx

    benchmark = _load_yaml(_ROOT / ".github/workflows/rhiza_benchmark.yml")
    steps = benchmark["jobs"]["benchmark"]["steps"]
    assert steps.index(_step(benchmark, "benchmark", helper)) < steps.index(
        _step(benchmark, "benchmark", "Run benchmarks")
    )

    marimo = _load_yaml(_ROOT / ".github/workflows/rhiza_marimo.yml")
    steps = marimo["jobs"]["test-notebooks"]["steps"]
    assert steps.index(_step(marimo, "test-notebooks", helper)) < steps.index(
        _step(marimo, "test-notebooks", "Run notebook")
    )

    book = _load_yaml(_ROOT / ".github/workflows/rhiza_book.yml")
    steps = book["jobs"]["build"]["steps"]
    assert steps.index(_step(book, "build", helper)) < steps.index(
        _step(book, "build", "Sync the virtual environment for ${{ github.repository }}")
    )

    weekly = _load_yaml(_ROOT / ".github/workflows/rhiza_weekly.yml")
    for job, step_name in [
        ("dep-compat-test", "Resolve and install latest compatible dependencies"),
        ("semgrep", "Run Semgrep"),
    ]:
        steps = weekly["jobs"][job]["steps"]
        assert steps.index(_step(weekly, job, helper)) < steps.index(_step(weekly, job, step_name))

    release = _load_yaml(_ROOT / ".github/workflows/rhiza_release.yml")
    steps = release["jobs"]["build"]["steps"]
    assert steps.index(_step(release, "build", helper)) < steps.index(_step(release, "build", "Build"))


def test_shipped_wrappers_grant_id_token_for_codeartifact_opt_in() -> None:
    """Workflow wrappers that call supported reusable workflows must allow OIDC."""
    wrappers = [
        _ROOT / "bundles/github-tests/.github/workflows/rhiza_ci.yml",
        _ROOT / "bundles/github-tests/.github/workflows/rhiza_benchmark.yml",
        _ROOT / "bundles/github-marimo/.github/workflows/rhiza_marimo.yml",
        _ROOT / "bundles/github/.github/workflows/rhiza_weekly.yml",
    ]
    for path in wrappers:
        workflow = _load_yaml(path)
        assert (workflow.get("permissions") or {}).get("id-token") == "write", (
            f"{path.relative_to(_ROOT)} must grant id-token: write so CodeArtifact opt-in can assume the read role"
        )
