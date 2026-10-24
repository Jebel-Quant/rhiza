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


def test_book_retains_deprecated_setup_aliases(workflow: dict) -> None:
    """Existing callers remain valid while the generic contract takes precedence."""
    call = (workflow.get("on") or workflow[True])["workflow_call"]
    assert call["inputs"]["book-setup"]["type"] == "boolean"
    assert call["inputs"]["book-setup"]["default"] is False
    assert call["secrets"]["BOOK_SETUP_TOKEN"]["required"] is False
    steps = workflow["jobs"]["build"]["steps"]
    setup = _step(workflow, "Run consumer dependency setup")
    checkout = next(s for s in steps if s.get("uses", "").startswith("actions/checkout@"))
    sync = next(s for s in steps if "uv sync" in s.get("run", ""))
    assert steps.index(checkout) < steps.index(setup) < steps.index(sync)
    guard = _step(workflow, "Validate consumer dependency setup")
    assert guard["if"] == "${{ vars.RHIZA_SETUP_ENABLED == 'true' || inputs.book-setup }}"
    assert setup["if"] == "${{ steps.consumer_setup.outputs.action == 'generic' }}"
    assert setup["with"]["credentials"] == "${{ secrets.RHIZA_SETUP_CREDENTIALS || secrets.BOOK_SETUP_TOKEN }}"
    legacy = _step(workflow, "Run deprecated consumer book setup")
    assert legacy["if"] == "${{ steps.consumer_setup.outputs.action == 'legacy' }}"
    assert legacy["uses"] == "./.github/actions/rhiza-book-setup"
    assert legacy["with"] == {"token": setup["with"]["credentials"]}
    assert steps.index(guard) < steps.index(setup) < steps.index(legacy) < steps.index(sync)


@pytest.mark.parametrize(
    ("legacy_enabled", "generic", "legacy", "expected"),
    [
        (False, "action.yml", None, "generic"),
        (True, None, "action.yml", "legacy"),
        (True, None, "action.yaml", "legacy"),
        (True, "action.yaml", "action.yml", "generic"),
        (True, "action.yml", None, "generic"),
        (False, None, "action.yml", None),
        (True, None, None, None),
    ],
)
def test_book_setup_selection(workflow, tmp_path, legacy_enabled, generic, legacy, expected):
    """Run the real guard: fallback is opt-in and never executes both actions."""
    for directory, filename in (("rhiza-setup", generic), ("rhiza-book-setup", legacy)):
        if filename:
            action = tmp_path / ".github/actions" / directory / filename
            action.parent.mkdir(parents=True)
            action.write_text("name: setup\n")
    output = tmp_path / "output"
    guard = _step(workflow, "Validate consumer dependency setup")
    result = _run(
        guard["run"],
        tmp_path,
        EVENT_NAME="push",
        HEAD_REPOSITORY="",
        CALLER_REPOSITORY="acme/project",
        LEGACY_BOOK_SETUP=str(legacy_enabled).lower(),
        GITHUB_OUTPUT=str(output),
    )
    assert (result.returncode == 0) == (expected is not None), result.stdout + result.stderr
    assert ("::warning::" in result.stdout) == legacy_enabled
    if expected:
        assert output.read_text() == f"action={expected}\n"
    else:
        assert not output.exists()


@pytest.mark.parametrize(("event", "head"), [("pull_request", "fork/project"), ("pull_request_target", "acme/project")])
def test_legacy_book_setup_rejects_untrusted_events(workflow, tmp_path, event, head):
    """Deprecated callers cannot bypass the generic hook's trust restrictions."""
    action = tmp_path / ".github/actions/rhiza-book-setup/action.yml"
    action.parent.mkdir(parents=True)
    action.write_text("name: setup\n")
    output = tmp_path / "output"
    result = _run(
        _step(workflow, "Validate consumer dependency setup")["run"],
        tmp_path,
        EVENT_NAME=event,
        HEAD_REPOSITORY=head,
        CALLER_REPOSITORY="acme/project",
        LEGACY_BOOK_SETUP="true",
        GITHUB_OUTPUT=str(output),
    )
    assert result.returncode != 0
    assert "not allowed" in result.stdout
    assert not output.exists()


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
