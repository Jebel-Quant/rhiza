"""Contract and behavioural tests for opt-in consumer book setup."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - executes workflow shell in a temporary directory
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = _ROOT / ".github/workflows/rhiza_book.yml"
_BASH = shutil.which("bash")
_ACTION = ".github/actions/rhiza-book-setup/action.yml"
_ENABLED = "${{ inputs.book-setup }}"


@pytest.fixture
def workflow() -> dict:
    """Load the reusable workflow rather than a duplicate of its logic."""
    return yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))


def _step(workflow: dict, name: str) -> dict:
    """Find a unique named build step."""
    matching = [step for step in workflow["jobs"]["build"]["steps"] if step.get("name") == name]
    assert len(matching) == 1
    return matching[0]


def _run(script: str, cwd: Path, **env: str) -> subprocess.CompletedProcess:
    """Execute the actual workflow script with GitHub's fail-fast bash flags."""
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


def test_setup_is_disabled_and_secret_is_explicit(workflow: dict) -> None:
    """Legacy callers need neither an action nor a credential."""
    call = (workflow.get("on") or workflow[True])["workflow_call"]
    assert call["inputs"]["book-setup"]["type"] == "boolean"
    assert call["inputs"]["book-setup"]["default"] is False
    assert call["secrets"]["BOOK_SETUP_TOKEN"]["required"] is False
    setup = _step(workflow, "Run consumer book setup")
    assert setup["uses"] == "./.github/actions/rhiza-book-setup"
    assert setup["with"] == {"token": "${{ secrets.BOOK_SETUP_TOKEN }}"}
    for name in ("Validate consumer setup event", "Require consumer setup action", "Run consumer book setup"):
        assert _step(workflow, name)["if"] == _ENABLED
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert text.count("secrets.BOOK_SETUP_TOKEN") == 1
    assert "toJSON(secrets)" not in text
    assert not (_ROOT / _ACTION).exists(), "Rhiza must not supply the consumer-owned action"


def test_setup_uses_caller_revision_before_dependencies_and_caches(workflow: dict) -> None:
    """Trust validation precedes checkout; setup precedes every resolving/build step."""
    steps = workflow["jobs"]["build"]["steps"]
    checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["ref"] == "${{ github.sha }}"
    trust = _step(workflow, "Validate consumer setup event")
    require = _step(workflow, "Require consumer setup action")
    setup = _step(workflow, "Run consumer book setup")
    assert steps.index(trust) < steps.index(checkout) < steps.index(require) < steps.index(setup)
    for name in (
        "Install uv",
        "Configure git auth for private packages",
        "Cache MkDocs plugin cache",
        "Look for a paper",
        "Make the book",
    ):
        assert steps.index(setup) < steps.index(_step(workflow, name))
    sync = next(step for step in steps if "uv sync" in step.get("run", ""))
    assert steps.index(setup) < steps.index(sync)
    assert trust["env"] == {
        "EVENT_NAME": "${{ github.event_name }}",
        "HEAD_REPOSITORY": "${{ github.event.pull_request.head.repo.full_name }}",
        "CALLER_REPOSITORY": "${{ github.repository }}",
    }


@pytest.mark.parametrize(
    ("event", "head", "allowed"),
    [
        ("push", "", True),
        ("workflow_dispatch", "", True),
        ("pull_request", "consumer/project", True),
        ("pull_request", "fork/project", False),
        ("pull_request", "", False),
        ("pull_request_target", "consumer/project", False),
        ("pull_request_target", "fork/project", False),
    ],
)
def test_setup_event_guard(workflow: dict, tmp_path: Path, event: str, head: str, allowed: bool) -> None:
    """Even a fork with secrets enabled cannot reach credential-bearing local code."""
    result = _run(
        _step(workflow, "Validate consumer setup event")["run"],
        tmp_path,
        EVENT_NAME=event,
        HEAD_REPOSITORY=head,
        CALLER_REPOSITORY="consumer/project",
    )
    assert (result.returncode == 0) is allowed
    if not allowed:
        assert "::error::" in result.stdout
    assert workflow["jobs"]["build"]["if"] == "${{ !github.event.repository.fork }}"


@pytest.mark.parametrize("present", [False, True])
def test_missing_action_fails_closed(workflow: dict, tmp_path: Path, present: bool) -> None:
    """An enabled but unconfigured caller must fail rather than build without setup."""
    if present:
        action = tmp_path / _ACTION
        action.parent.mkdir(parents=True)
        action.write_text("runs:\n  using: composite\n  steps: []\n", encoding="utf-8")
    result = _run(_step(workflow, "Require consumer setup action")["run"], tmp_path)
    assert (result.returncode == 0) is present
    if not present:
        assert f"::error::book-setup requires {_ACTION}" in result.stdout


def test_setup_failure_blocks_upload_and_deployment(workflow: dict) -> None:
    """GitHub's implicit success gates must not be bypassed on any setup/build step."""
    build = workflow["jobs"]["build"]
    assert not build.get("continue-on-error", False)
    for step in build["steps"]:
        assert not step.get("continue-on-error", False)
        assert "always(" not in step.get("if", "")
        assert "failure(" not in step.get("if", "")
    deploy = workflow["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    assert "always(" not in deploy["if"]
    assert "failure(" not in deploy["if"]


@pytest.mark.parametrize("token", ["", "placeholder\ninjected=value", "placeholder\rvalue", "placeholder-%-token"])
def test_documented_action_checks_configuration_and_exports_masked_token(tmp_path: Path, token: str) -> None:
    """Run the example's real shell, including missing-token and env-injection guards."""
    text = (_ROOT / "docs/guides/BOOK.md").read_text(encoding="utf-8")
    block = text.split("```yaml\nname: Prepare private API access\n", 1)[1].split("```", 1)[0]
    action = yaml.safe_load("name: Prepare private API access\n" + block)
    env_file = tmp_path / "github-env"
    result = _run(action["runs"]["steps"][0]["run"], tmp_path, API_TOKEN=token, GITHUB_ENV=str(env_file))
    if not token or "\n" in token or "\r" in token:
        assert result.returncode != 0
        assert not env_file.exists()
    else:
        assert result.returncode == 0
        assert f"::add-mask::{token.replace('%', '%25')}" in result.stdout
        assert token not in result.stderr
        assert env_file.read_text(encoding="utf-8") == (
            f"PRIVATE_API_TOKEN={token}\nPRIVATE_API_URL=https://api.example.invalid\n"
        )
