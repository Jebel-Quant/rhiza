"""Tests for the rhiza_sync.yml workflow schedule configuration."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from api.conftest import run_make

WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_sync.yml"
DEFAULT_SYNC_SCHEDULE = "0 0 * * 1"
CUSTOM_SCHEDULE = "RHIZA_SYNC_SCHEDULE='0 6 * * 2'"


def _load_workflow(root: Path) -> dict:
    """Load and parse the sync workflow YAML file."""
    workflow_file = root / WORKFLOW_PATH
    if not workflow_file.exists():
        pytest.fail(f"Workflow file not found: {workflow_file}")
    with open(workflow_file) as fh:
        return yaml.safe_load(fh)


def _get_triggers(workflow: dict) -> dict:
    """Return the 'on' / triggers block."""
    return workflow.get("on") or workflow.get(True) or {}


def test_sync_schedule_make_target_defaults(logger):
    """sync-schedule must default to '0 0 * * 1' when RHIZA_SYNC_SCHEDULE is unset."""
    result = run_make(logger, ["-f", ".rhiza/rhiza.mk", "RHIZA_SYNC_SCHEDULE=", "sync-schedule"], dry_run=False)
    assert result.returncode == 0
    assert result.stdout.strip() == DEFAULT_SYNC_SCHEDULE


def test_sync_schedule_make_target_custom(logger):
    """sync-schedule must use the configured RHIZA_SYNC_SCHEDULE value."""
    result = run_make(
        logger,
        ["-f", ".rhiza/rhiza.mk", CUSTOM_SCHEDULE, "sync-schedule"],
        dry_run=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "0 6 * * 2"


def test_sync_workflow_cron_matches_env_schedule(root, logger):
    """Workflow cron must match the value emitted by the sync-schedule make target."""
    result = run_make(logger, ["-f", ".rhiza/rhiza.mk", "sync-schedule"], dry_run=False)
    assert result.returncode == 0
    configured_schedule = result.stdout.strip()

    workflow = _load_workflow(root)
    schedules = _get_triggers(workflow).get("schedule", [])
    crons = [entry["cron"] for entry in schedules]
    assert configured_schedule in crons, (
        f"Workflow cron {crons!r} does not match RHIZA_SYNC_SCHEDULE '{configured_schedule}'. "
        "Update .github/workflows/rhiza_sync.yml to match .rhiza/.env."
    )
