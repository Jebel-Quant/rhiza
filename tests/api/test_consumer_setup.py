"""Exercise the provider-neutral setup contract before private dependency resolution."""

from __future__ import annotations

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


def test_setup_before_dependency_resolution():
    """Every supported job authenticates before its first dependency-consuming step."""
    jobs = {
        "ci": {
            "generate-matrix": "Build package metadata and extract supported Python classifiers",
            **dict.fromkeys(
                [
                    "test",
                    "lowest-deps",
                    "typecheck",
                    "deptry",
                    "rhiza-test",
                    "docs-coverage",
                    "security",
                    "license",
                ],
                "Configure git auth for private packages",
            ),
        },
        "book": {"build": "Sync the virtual environment for ${{ github.repository }}"},
        "marimo": {"test-notebooks": "Run notebook"},
        "benchmark": {"benchmark": "Run benchmarks"},
        "weekly": {"dep-compat-test": "Resolve and install latest compatible dependencies", "semgrep": "Run Semgrep"},
        "release": {"build": "Build"},
    }
    tested_guard = None
    for workflow, consumers in jobs.items():
        definition = yaml.safe_load((_ROOT / f".github/workflows/rhiza_{workflow}.yml").read_text())
        for job, dependency in consumers.items():
            steps = definition["jobs"][job]["steps"]
            names = [s.get("name") for s in steps]
            assert names.index("Run consumer dependency setup") < names.index(dependency)
            call = steps[names.index("Run consumer dependency setup")]
            guard = steps[names.index("Validate consumer dependency setup")]
            if tested_guard is None:
                tested_guard = guard
            if workflow != "book":
                assert guard == tested_guard
            assert steps.index(guard) < steps.index(call)
            if workflow != "book":
                assert guard["if"] == call["if"]
            assert "env" not in call
            assert call["uses"] == "./.github/actions/rhiza-setup"
            credentials = "${{ secrets.RHIZA_SETUP_CREDENTIALS }}"
            if workflow == "book":
                credentials = "${{ secrets.RHIZA_SETUP_CREDENTIALS || secrets.BOOK_SETUP_TOKEN }}"
            assert call["with"]["credentials"] == credentials
            expected = {"contents": "read"}
            if workflow == "ci":
                expected["actions"] = "read"
            elif workflow == "release":
                expected.update({"id-token": "write", "attestations": "write"})
            assert definition["jobs"][job]["permissions"] == expected
            assert "pages" not in expected
            if workflow != "release":
                assert definition["permissions"] == expected
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
