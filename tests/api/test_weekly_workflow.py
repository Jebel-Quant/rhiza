"""Tests for the rhiza_weekly.yml workflow and its referenced Makefile targets.

Covers two layers:
- Structural: parse .github/workflows/rhiza_weekly.yml and assert every job,
  trigger, and key step is correctly defined.
- Behavioural: dry-run (make -n) the Makefile targets that the workflow invokes
  (semgrep, security, test) to confirm they are wired up without actually
  running them.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.util import run_make

WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_weekly.yml"
EXPECTED_JOBS = {"dep-compat-test", "semgrep", "link-check"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_workflow(root: Path) -> dict:
    """Load and parse the weekly workflow YAML file."""
    workflow_file = root / WORKFLOW_PATH
    if not workflow_file.exists():
        pytest.fail(f"Workflow file not found: {workflow_file}")
    with open(workflow_file) as fh:
        return yaml.safe_load(fh)


def _get_triggers(workflow: dict) -> dict:
    """Return the 'on' / triggers block.

    PyYAML parses the bare YAML keyword ``on`` as Python ``True``, so we look
    up both the string key and the boolean key to be robust.
    """
    return workflow.get("on") or workflow.get(True) or {}


def _step_commands(job: dict) -> list[str]:
    """Return all ``run`` strings from a job's steps."""
    return [step["run"] for step in job.get("steps", []) if "run" in step]


def _step_uses(job: dict) -> list[str]:
    """Return all ``uses`` strings from a job's steps."""
    return [step["uses"] for step in job.get("steps", []) if "uses" in step]


def _step_with_args(job: dict) -> list[dict]:
    """Return all steps that have a ``with`` block."""
    return [step for step in job.get("steps", []) if "with" in step]


# ---------------------------------------------------------------------------
# Structure tests — validate the YAML content of rhiza_weekly.yml
# ---------------------------------------------------------------------------


class TestWeeklyWorkflowStructure:
    """Validate the static content of rhiza_weekly.yml."""

    @pytest.fixture
    def workflow(self, root):
        """Load and return the parsed weekly workflow YAML."""
        return _load_workflow(root)

    # --- top-level keys ---

    def test_workflow_file_exists(self, root):
        """Workflow file must exist at the expected path."""
        assert (root / WORKFLOW_PATH).exists()

    def test_workflow_name(self, workflow):
        """Workflow name must be '(RHIZA) WEEKLY'."""
        assert workflow.get("name") == "(RHIZA) WEEKLY"

    def test_permissions_contents_read(self, workflow):
        """Workflow must declare contents: read permissions."""
        assert workflow.get("permissions", {}).get("contents") == "read"

    # --- triggers ---

    def test_schedule_trigger_present(self, workflow):
        """Workflow must have a schedule trigger."""
        triggers = _get_triggers(workflow)
        assert "schedule" in triggers, "workflow must have a schedule trigger"

    def test_schedule_cron_is_monday_morning(self, workflow):
        """Schedule cron must fire every Monday at 08:00 UTC."""
        schedules = _get_triggers(workflow)["schedule"]
        crons = [entry["cron"] for entry in schedules]
        assert "0 8 * * 1" in crons, f"Expected Monday 08:00 UTC cron, got: {crons}"

    def test_workflow_dispatch_trigger_present(self, workflow):
        """Workflow must support manual dispatch via workflow_dispatch."""
        assert "workflow_dispatch" in _get_triggers(workflow), (
            "workflow must support manual dispatch via workflow_dispatch"
        )

    # --- jobs present ---


# ---------------------------------------------------------------------------
# Link check — the two-pass retry that absorbs a transient 5xx
# ---------------------------------------------------------------------------


class TestLinkCheckRetry:
    """Pin the shape of link-check's retry.

    lychee cannot retry this failure itself: ``RetryExt for ErrorKind``
    (lychee-lib/src/retry.rs) retries a rejected status code only when it is 429, so a
    504 that arrives as a well-formed response is ``RejectedStatusCode(504)`` and fails
    on the first try whatever ``--max-retries`` says. The retry is therefore two passes
    of the action, and each half is asserted here: an advisory first pass, a pause, and
    a deciding second pass that runs only when the first found something. Dropping any
    one of them turns the job either flaky again or permanently green.
    """

    @pytest.fixture
    def link_check(self, root):
        """Return the link-check job."""
        workflow = _load_workflow(root)
        assert "link-check" in workflow["jobs"], "weekly workflow must define a link-check job"
        return workflow["jobs"]["link-check"]

    @pytest.fixture
    def lychee_steps(self, link_check):
        """Return the job's lychee steps, in order."""
        steps = [step for step in link_check.get("steps", []) if "lychee-action" in step.get("uses", "")]
        assert len(steps) == 2, f"expected two lychee passes, got {len(steps)}"
        return steps

    def test_first_pass_does_not_fail_the_job(self, lychee_steps):
        """The first pass reports without deciding, so one transient 5xx cannot go red."""
        first = lychee_steps[0]
        assert first["with"]["fail"] is False
        assert first.get("id"), "first pass needs an id so the retry can read its exit_code"

    def test_second_pass_decides(self, lychee_steps):
        """The second pass is the one that fails the job."""
        assert lychee_steps[1]["with"]["fail"] is True

    def test_second_pass_runs_only_after_a_failure(self, link_check, lychee_steps):
        """The retry is guarded on the first pass's exit code, not run unconditionally.

        Unconditional would double every weekly run's link traffic, and against a rate
        limiter that is how you manufacture the 429 the accept list is there to forgive.
        """
        first_id = lychee_steps[0]["id"]
        guard = f"steps.{first_id}.outputs.exit_code"
        assert guard in lychee_steps[1].get("if", ""), f"retry must be guarded on {guard}"

    def test_a_pause_separates_the_two_passes(self, link_check, lychee_steps):
        """A retry that fires immediately re-asks a server that is still failing."""
        steps = link_check["steps"]
        between = steps[steps.index(lychee_steps[0]) + 1 : steps.index(lychee_steps[1])]
        sleeps = [step for step in between if "sleep" in step.get("run", "")]
        assert sleeps, "the retry must wait before re-checking"
        assert steps.index(lychee_steps[0]) < steps.index(lychee_steps[1])

    def test_both_passes_check_the_same_links(self, link_check, lychee_steps):
        """Both passes take one argument list, so the deciding pass cannot check less.

        A second pass with its own copy of the arguments is a second thing to keep in
        step, and the failure mode is silent: the pass that fails the job checks a
        narrower set than the one that found the problem.
        """
        args = {step["with"]["args"] for step in lychee_steps}
        assert len(args) == 1, f"the two passes disagree about their arguments: {args}"
        assert "env.LYCHEE_ARGS" in args.pop(), "argument list should come from the job's env"
        assert "LYCHEE_ARGS" in link_check.get("env", {})


# ---------------------------------------------------------------------------
# Makefile dry-run tests — verify the targets invoked by the workflow compile
# ---------------------------------------------------------------------------


class TestWeeklyWorkflowMakeTargets:
    """Dry-run the Makefile targets that rhiza_weekly.yml invokes."""

    def test_semgrep_target_dry_run(self, logger):
        """Make semgrep must parse and plan without error."""
        result = run_make(logger, ["semgrep"])
        assert result.returncode == 0

    def test_test_target_dry_run(self, logger):
        """Make test must parse and plan without error."""
        result = run_make(logger, ["test"])
        assert result.returncode == 0

    def test_security_target_resolves(self, logger):
        """`make security` must resolve, so the weekly workflow's step cannot fail on a typo.

        This asserted bandit's banner text and its no-folders warning, both printed by
        ``quality.mk``'s recipe. That recipe retired to rhiza-task, so a dry run shows the
        delegation and nothing else. The property it was really protecting -- that the gate does
        not silently pass with nothing to scan -- moved with the recipe and is asserted where the
        scope now lives: ``tests/utils/test_gate_scope.py`` requires ``source_folder`` to name an
        existing folder holding Python, and ``tests/e2e/`` runs the gate for real.
        """
        result = run_make(logger, ["security"], check=False)
        assert result.returncode == 0, f"`make security` did not resolve: {result.stderr}"
        assert "no rule to make target" not in result.stderr.lower()

    def test_semgrep_target_in_help(self, logger):
        """Semgrep must be discoverable in `make help`.

        Still true, and worth keeping: ``semgrep`` is a CLI *task*, so the shim's ``help`` lists
        it. Only the five surviving fragments' targets are missing from help
        (Jebel-Quant/rhiza-task#20), and semgrep is not one of them.
        """
        result = run_make(logger, ["help"], dry_run=False)
        assert "semgrep" in result.stdout

    def test_security_target_in_help(self, logger):
        """Security must be discoverable in `make help` -- a CLI task, so it is listed."""
        result = run_make(logger, ["help"], dry_run=False)
        assert "security" in result.stdout
