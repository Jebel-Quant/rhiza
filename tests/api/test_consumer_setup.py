"""Exercise the provider-neutral setup contract before private dependency resolution."""

from __future__ import annotations

import os
import subprocess  # nosec B404 - executes the checked-in action shell in fixture projects
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_ACTION = _ROOT / ".github/actions/rhiza-consumer-setup/action.yml"


@pytest.mark.parametrize(
    ("enabled", "event", "head", "exists", "success"),
    [
        ("false", "push", "", False, True),
        ("true", "push", "", False, False),
        ("true", "push", "", True, True),
        ("true", "pull_request", "acme/project", True, True),
        ("true", "pull_request", "fork/project", True, False),
        ("true", "pull_request_target", "acme/project", True, False),
    ],
)
def test_setup_guard(tmp_path, enabled, event, head, exists, success):
    """Enabled setup requires a caller action and refuses untrusted events."""
    if exists:
        action = tmp_path / ".github/actions/rhiza-setup/action.yaml"
        action.parent.mkdir(parents=True)
        action.write_text("name: setup\n")
    definition = yaml.safe_load(_ACTION.read_text())
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", definition["runs"]["steps"][0]["run"]],
        cwd=tmp_path,
        env={
            **os.environ,
            "ENABLED": enabled,
            "EVENT_NAME": event,
            "HEAD_REPOSITORY": head,
            "CALLER_REPOSITORY": "acme/project",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert (result.returncode == 0) == success, result.stdout + result.stderr
    call = definition["runs"]["steps"][1]
    assert call["uses"] == "./.github/actions/rhiza-setup"
    assert call["if"] == "inputs.enabled == 'true'"
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
                    "pre-commit",
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
    for workflow, consumers in jobs.items():
        definition = yaml.safe_load((_ROOT / f".github/workflows/rhiza_{workflow}.yml").read_text())
        for job, dependency in consumers.items():
            steps = definition["jobs"][job]["steps"]
            names = [s.get("name") for s in steps]
            assert names.index("Run consumer dependency setup") < names.index(dependency)
            call = steps[names.index("Run consumer dependency setup")]
            assert call["env"] == {"RHIZA_SETUP_VARS": "${{ toJSON(vars) }}"}
            assert call["with"]["credentials"] == "${{ secrets.RHIZA_SETUP_CREDENTIALS }}"
            permissions = definition["jobs"][job].get("permissions", definition["permissions"])
            assert permissions["id-token"] == "write"
        text = str(definition)
        assert "CODEARTIFACT_" not in text
        assert "AWS_ROLE_TO_ASSUME_READ" not in text
        triggers = definition.get("on") or definition[True]
        assert triggers["workflow_call"]["secrets"]["RHIZA_SETUP_CREDENTIALS"]["required"] is False


def test_shipped_setup_matches_repository_action():
    """Template consumers receive the tested dispatcher, leaving their own hooks untouched."""
    assert (
        _ROOT / "bundles/github/.github/actions/rhiza-consumer-setup/action.yml"
    ).read_bytes() == _ACTION.read_bytes()
    for bundle in (_ROOT / "bundles").iterdir():
        assert not (bundle / ".github/actions/rhiza-setup").exists()
        if bundle.name != "github-pypi":
            assert not (bundle / ".github/actions/release-publish").exists()


@pytest.mark.parametrize(
    ("index", "expected"), [("private--feed", "PRIVATE__FEED"), ("_private.feed-", "_PRIVATE_FEED_")]
)
def test_codeartifact_example_preserves_uv_index_names(tmp_path, index, expected):
    """The optional provider example follows uv's character-by-character naming convention."""
    import json

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
        env={**os.environ, "RHIZA_SETUP_VARS": json.dumps(configuration), "GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"normalized_index={expected}" in output.read_text().splitlines()
