"""Tests for GitHub workflow stubs injected by the github-* bundles.

Rhiza-specific: validates that rhiza's own workflow stubs reference
jebel-quant/rhiza and carry the expected structure. Lives in tests/,
the mother repo's own suite, so it does not sync to downstream projects.

Workflow stubs in downstream projects are thin wrappers that delegate
to the reusable canonical workflows in jebel-quant/rhiza.  These tests
verify that:

- Every injected .github/workflows/*.yml file is valid YAML
- Each workflow has a 'name' and 'on' field
- Workflows that use the reusable pattern reference jebel-quant/rhiza
- The CI workflow exposes expected job names
- The release workflow has proper trigger conditions
- The sync workflow runs on a schedule
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


@pytest.fixture(scope="module")
def workflows_dir(root: Path) -> Path:
    """Return the path to .github/workflows/ or skip if absent."""
    d = root / ".github" / "workflows"
    if not d.is_dir():
        pytest.skip(".github/workflows/ not found — github bundle not synced")
    return d


# Names of compiler-generated workflows to exclude from stub checks. None
# currently exist; *.lock.yml files are filtered separately below. Kept as the
# exclusion hook for any future generated workflows.
_GENERATED_WORKFLOWS: set[str] = set()


@pytest.fixture(scope="module")
def workflow_files(workflows_dir: Path) -> list[Path]:
    """Return all hand-written .yml files in the workflows directory."""
    return sorted(
        path
        for path in workflows_dir.glob("*.yml")
        if not path.name.endswith(".lock.yml") and path.name not in _GENERATED_WORKFLOWS
    )


def _load_workflow(path: Path) -> dict:
    """Load a workflow YAML file and return the parsed document."""
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class TestWorkflowStructure:
    """Structural validation for all injected workflow files."""

    def test_all_workflows_are_valid_yaml(self, workflow_files: list[Path]) -> None:
        """Every .yml file in workflows/ must parse as valid YAML without error."""
        errors: list[str] = []
        for wf in workflow_files:
            try:
                with wf.open(encoding="utf-8") as fh:
                    yaml.safe_load(fh)
            except yaml.YAMLError as exc:
                errors.append(f"  {wf.name}: {exc}")
        if errors:
            pytest.fail("YAML errors in workflow files:\n" + "\n".join(errors))

    def test_all_workflows_have_name(self, workflow_files: list[Path]) -> None:
        """Every workflow must declare a 'name' field for legibility in GitHub UI."""
        missing: list[str] = []
        for wf in workflow_files:
            doc = _load_workflow(wf)
            if not isinstance(doc, dict) or "name" not in doc:
                missing.append(f"  {wf.name}")
        if missing:
            pytest.fail("Workflows missing 'name' field:\n" + "\n".join(missing))

    def test_all_workflows_have_on_trigger(self, workflow_files: list[Path]) -> None:
        """Every workflow must declare at least one trigger via the 'on' key.

        Note: pyyaml parses the bare YAML key 'on' as Python boolean True because
        'on' is a valid YAML boolean literal.  We check for both True and the string
        'on' to handle both the parsed representation and any future parser changes.
        """
        missing: list[str] = []
        for wf in workflow_files:
            doc = _load_workflow(wf)
            if not isinstance(doc, dict):
                missing.append(f"  {wf.name}")
                continue
            has_on = "on" in doc or True in doc
            if not has_on:
                missing.append(f"  {wf.name}")
        if missing:
            pytest.fail("Workflows missing 'on' trigger:\n" + "\n".join(missing))

    def test_all_workflows_have_jobs(self, workflow_files: list[Path]) -> None:
        """Every workflow must define at least one job."""
        missing: list[str] = []
        for wf in workflow_files:
            doc = _load_workflow(wf)
            if not isinstance(doc, dict):
                continue
            jobs = doc.get("jobs") or {}
            if not jobs:
                missing.append(f"  {wf.name}")
        if missing:
            pytest.fail("Workflows with no jobs defined:\n" + "\n".join(missing))

    def test_reusable_workflow_stubs_reference_jebel_quant(self, workflow_files: list[Path]) -> None:
        """Stub workflows that use the 'uses:' pattern must point to jebel-quant/rhiza."""
        violations: list[str] = []
        for wf in workflow_files:
            content = wf.read_text(encoding="utf-8")
            if "uses:" not in content:
                continue
            if "jebel-quant/rhiza" not in content:
                violations.append(f"  {wf.name}: uses: present but no jebel-quant/rhiza reference")
        if violations:
            pytest.fail("Stub workflows not delegating to jebel-quant/rhiza:\n" + "\n".join(violations))

    def test_no_workflow_is_empty(self, workflow_files: list[Path]) -> None:
        """No workflow file should be a null (empty) YAML document."""
        empty: list[str] = []
        for wf in workflow_files:
            doc = _load_workflow(wf)
            if doc is None:
                empty.append(f"  {wf.name}")
        if empty:
            pytest.fail("Empty workflow files (null YAML document):\n" + "\n".join(empty))


class TestCiWorkflow:
    """Tests specific to the CI workflow (rhiza_ci.yml)."""

    @pytest.fixture
    def ci_workflow(self, workflows_dir: Path) -> dict:
        """Load and return the CI workflow YAML."""
        ci_path = workflows_dir / "rhiza_ci.yml"
        if not ci_path.exists():
            pytest.skip("rhiza_ci.yml not found")
        return _load_workflow(ci_path)

    def _get_triggers(self, workflow_doc: dict) -> dict:
        """Extract the 'on' triggers from a workflow document.

        pyyaml parses 'on:' as the Python boolean True (YAML boolean literal).
        This helper retrieves the trigger mapping regardless of key type.
        """
        return workflow_doc.get(True, workflow_doc.get("on", {})) or {}

    def test_ci_workflow_has_push_trigger(self, ci_workflow: dict) -> None:
        """CI workflow must be triggered by push events."""
        triggers = self._get_triggers(ci_workflow)
        assert "push" in triggers or "push" in str(triggers), "CI workflow must be triggered on push"

    def test_ci_workflow_has_pull_request_trigger(self, ci_workflow: dict) -> None:
        """CI workflow must be triggered by pull_request events."""
        triggers = self._get_triggers(ci_workflow)
        assert "pull_request" in triggers or "pull_request" in str(triggers), (
            "CI workflow must be triggered on pull_request"
        )

    def test_ci_workflow_exposes_workflow_call(self, ci_workflow: dict) -> None:
        """CI workflow must support workflow_call for use as a reusable workflow."""
        triggers = self._get_triggers(ci_workflow)
        assert "workflow_call" in triggers or "workflow_call" in str(triggers), (
            "CI workflow must support workflow_call (reusable workflow pattern)"
        )

    def test_ci_workflow_has_permissions(self, ci_workflow: dict) -> None:
        """CI workflow must declare explicit permissions (principle of least privilege)."""
        assert "permissions" in ci_workflow, (
            "CI workflow should declare explicit permissions to limit GitHub token scope"
        )

    def test_ci_workflow_verifies_clean_working_tree_after_tests(self, ci_workflow: dict) -> None:
        """CI workflow should fail if tests leave tracked or untracked files behind."""
        steps = ci_workflow.get("jobs", {}).get("test", {}).get("steps", [])
        verify_step = next((step for step in steps if step.get("name") == "Verify clean working tree"), None)

        assert verify_step is not None, "CI workflow should verify that tests leave the working tree clean"
        assert verify_step.get("if") == "matrix.python-version == '3.12' && matrix.os == 'ubuntu-latest'"

        run = verify_step.get("run", "")
        assert "git status --porcelain" in run, "clean-tree verification must detect untracked files"
        assert "git diff --exit-code" in run, "clean-tree verification must detect tracked modifications"
        assert "printf '%s\\n' \"$status\"" in run, "clean-tree verification should print dirty paths on failure"

    def test_ci_workflow_runs_clean_tree_check_after_tests(self, ci_workflow: dict) -> None:
        """The clean-tree verification should run after the test command completes."""
        steps = ci_workflow.get("jobs", {}).get("test", {}).get("steps", [])
        step_names = [step.get("name") for step in steps]

        assert step_names.index("Run tests") < step_names.index("Verify clean working tree")

    def test_ci_gate_tolerates_cancelled_results(self, ci_workflow: dict) -> None:
        """CI gate must accept 'cancelled' alongside 'success' to survive transient runner cancellations.

        When a matrix leg is cancelled mid-run (e.g. by the concurrency group or a
        transient runner failure), GitHub sets the parent job result to 'cancelled'.
        The gate must not block the PR in that case; it should only fail on 'failure'
        or 'skipped' results.
        """
        gate_steps = ci_workflow.get("jobs", {}).get("ci-gate", {}).get("steps", [])
        # Matched on the step's *shape* rather than its exact title: the title names the
        # jobs being rolled up, so it changes whenever one joins (rhiza-test did in #1523)
        # and an equality check would fail for a reason that has nothing to do with the
        # cancelled-result property under test.
        verify_step = next(
            (s for s in gate_steps if s.get("name", "").startswith("Verify") and "needs." in s.get("run", "")),
            None,
        )
        assert verify_step is not None, "CI gate must have a verification step reading job results"

        run_script = verify_step.get("run", "")
        # The gate must not simply check `!= "success"` — it must also allow `cancelled`.
        assert "cancelled" in run_script, (
            "CI gate must accept 'cancelled' results to tolerate transient runner cancellations; "
            "see: https://github.com/Jebel-Quant/rhiza/actions/runs/28344335938/job/83965148182"
        )


def _get_workflow_triggers(workflow_doc: dict) -> dict:
    """Extract the 'on' triggers from a parsed workflow document.

    pyyaml parses 'on:' as Python boolean True (YAML boolean literal).
    This helper retrieves the trigger mapping regardless of key type.
    """
    return workflow_doc.get(True, workflow_doc.get("on", {})) or {}


class TestReleaseWorkflow:
    """Tests specific to the release workflow (rhiza_release.yml)."""

    @pytest.fixture
    def release_workflow(self, workflows_dir: Path) -> dict:
        """Load and return the release workflow YAML."""
        release_path = workflows_dir / "rhiza_release.yml"
        if not release_path.exists():
            pytest.skip("rhiza_release.yml not found")
        return _load_workflow(release_path)

    def test_release_workflow_has_push_tags_trigger(self, release_workflow: dict) -> None:
        """Release workflow must be triggered by tag pushes (v* pattern).

        The rhiza release workflow fires when a version tag is pushed — the standard
        GitHub Actions pattern for release automation.  Tags gate the release rather
        than workflow_dispatch, ensuring every published release is traceable to a tag.
        """
        triggers = _get_workflow_triggers(release_workflow)
        assert "push" in triggers or "push" in str(triggers), (
            "release workflow must be triggered by tag push (push: tags: [v*])"
        )

    def test_release_workflow_push_trigger_is_tag_scoped(self, release_workflow: dict) -> None:
        """Release workflow push trigger must be scoped to version tags, not all branches."""
        triggers = _get_workflow_triggers(release_workflow)
        push_config = triggers.get("push", {}) if isinstance(triggers, dict) else {}
        assert "tags" in str(push_config), (
            "release workflow push trigger should be scoped to tags (e.g. tags: ['v*']), not fire on every branch push"
        )


class TestWeeklyWorkflow:
    """Tests specific to the weekly checks workflow (rhiza_weekly.yml)."""

    @pytest.fixture
    def weekly_workflow(self, workflows_dir: Path) -> dict:
        """Load and return the weekly workflow YAML."""
        weekly_path = workflows_dir / "rhiza_weekly.yml"
        if not weekly_path.exists():
            pytest.skip("rhiza_weekly.yml not found")
        return _load_workflow(weekly_path)

    def test_weekly_workflow_has_schedule(self, weekly_workflow: dict) -> None:
        """Weekly workflow must run on a schedule to catch dependency drift."""
        triggers = _get_workflow_triggers(weekly_workflow)
        assert "schedule" in triggers or "schedule" in str(triggers), "weekly workflow should run on a schedule"

    def test_weekly_workflow_has_cron_expression(self, weekly_workflow: dict) -> None:
        """Weekly workflow schedule must define a cron expression."""
        triggers = _get_workflow_triggers(weekly_workflow)
        schedule_val = triggers.get("schedule") if isinstance(triggers, dict) else None
        if schedule_val is None:
            pytest.skip("schedule not structured as expected")
        # cron expressions typically appear as a list of dicts with 'cron' key
        cron_found = any(
            "cron" in str(item) for item in (schedule_val if isinstance(schedule_val, list) else [schedule_val])
        )
        assert cron_found, "weekly workflow schedule should define a cron expression"


class TestBenchmarkWorkflow:
    """Tests specific to the benchmark workflow (rhiza_benchmark.yml)."""

    @pytest.fixture
    def benchmark_workflow(self, workflows_dir: Path) -> dict:
        """Load and return the benchmark workflow YAML."""
        benchmark_path = workflows_dir / "rhiza_benchmark.yml"
        if not benchmark_path.exists():
            pytest.skip("rhiza_benchmark.yml not found")
        return _load_workflow(benchmark_path)

    def test_benchmark_workflow_pushes_to_main_only(self, benchmark_workflow: dict) -> None:
        """Benchmark workflow should run only on push to main."""
        triggers = _get_workflow_triggers(benchmark_workflow)
        push_config = triggers.get("push", {}) if isinstance(triggers, dict) else {}
        branches = push_config.get("branches", []) if isinstance(push_config, dict) else []
        assert branches == ["main"], "benchmark workflow push trigger should be scoped to main only"
        assert "pull_request" not in str(triggers), "benchmark workflow must not run on pull requests"

    def test_benchmark_workflow_supports_workflow_call(self, benchmark_workflow: dict) -> None:
        """Benchmark workflow should support workflow_call for reuse from stubs."""
        triggers = _get_workflow_triggers(benchmark_workflow)
        assert "workflow_call" in triggers or "workflow_call" in str(triggers), (
            "benchmark workflow must support workflow_call (reusable workflow pattern)"
        )


class TestPaperWorkflow:
    """The paper workflow must not write to the repository (#1494).

    It used to push the compiled PDF to an orphan ``paper`` branch. Git refs are paths, so
    ``refs/heads/paper`` cannot coexist with ``refs/heads/paper/anything`` -- and the push
    therefore failed outright in any repository using the branch prefix a paper-writing team
    reaches for first. Worse, it stayed broken after such a topic branch was merged, until
    somebody also deleted it.

    Renaming the target (the issue's first suggestion) would have moved the collision rather
    than removed it, broken every consumer just as thoroughly, and left a stale PDF behind on
    the old branch with nothing going red. The branch had also stopped being the only durable
    home: ``book`` gained ``paper`` as a prerequisite in rhiza-task 1.1.0 and ``paper_folder``
    sits inside ``docs_dir``, so the PDF ships as a site asset -- guarded by ``book-nav`` and
    by ``test_the_compiled_paper_is_reachable_from_the_book``.

    So the step is gone, and these assertions are about what must not come back.
    """

    @pytest.fixture
    def paper_workflow_text(self, workflows_dir: Path) -> str:
        """Return the paper workflow's raw text, or skip when it is not synced."""
        path = workflows_dir / "rhiza_paper.yml"
        if not path.exists():
            pytest.skip("rhiza_paper.yml not found")
        return path.read_text(encoding="utf-8")

    def test_the_paper_workflow_pushes_to_no_branch(self, paper_workflow_text: str) -> None:
        """No `git push` is *executed*: the PDF reaches consumers via the book and the artifact.

        Asserted against the text rather than the parsed document because a `run:` block is an
        opaque string to YAML -- the thing being forbidden is a shell command, so the shell is
        what has to be read.

        Matched on a line that *starts* a `git push`, not on any line mentioning one. A naive
        substring search fails on this very workflow: the stale-branch warning tells the reader
        to run `git push origin --delete paper`, which is the retired command named as advice
        rather than run. Comments are skipped for the same reason.
        """
        offending = [
            line.strip()
            for line in paper_workflow_text.splitlines()
            if re.match(r"^(?:[^#]*(?:&&|\|\||;)\s*)?git\s+push\b", line.strip())
        ]
        assert not offending, (
            "the paper workflow pushes to a branch again: "
            f"{offending}. A top-level ref collides with any `paper/<topic>` branch (#1494); "
            "the PDF is published by the book as a site asset instead."
        )

    def test_the_paper_workflow_asks_for_no_write_scope(self, workflows_dir: Path) -> None:
        """`contents: write` existed only for the retired push, so it must not be requested.

        Checked at every level -- workflow and each job -- because a job-level grant would
        reinstate the capability without touching the top of the file.
        """
        path = workflows_dir / "rhiza_paper.yml"
        if not path.exists():
            pytest.skip("rhiza_paper.yml not found")
        doc = _load_workflow(path)

        scopes = [doc.get("permissions") or {}]
        scopes += [job.get("permissions") or {} for job in (doc.get("jobs") or {}).values()]
        writers = [scope for scope in scopes if isinstance(scope, dict) and scope.get("contents") == "write"]
        assert not writers, (
            "the paper workflow requests `contents: write`, which it needed only for the "
            "branch push retired in #1494. Compiling a PDF and uploading an artifact need "
            "no write access to the repository."
        )

    def test_the_github_paper_stub_grants_no_write_scope(self, root: Path) -> None:
        """The bundle stub must cap the reusable workflow at `contents: read`.

        The stub is the half a consumer actually syncs, and it carries its own `permissions:`
        block -- so the live workflow dropping the write scope proves nothing about them. The
        two travel together: the same release that ships this stub also bumps its
        `@vX.Y.Z` ref (`[[tool.bumpversion.files]]` globs `bundles/**/.github/workflows/*.yml`),
        so a consumer never has a read-only stub pointing at a version that still pushes.
        """
        path = root / "bundles" / "github-paper" / ".github" / "workflows" / "rhiza_paper.yml"
        assert path.is_file(), "the github-paper bundle ships no rhiza_paper.yml stub"
        doc = _load_workflow(path)

        for name, job in (doc.get("jobs") or {}).items():
            scope = job.get("permissions") or {}
            assert scope.get("contents") != "write", (
                f"the github-paper stub grants `contents: write` to job '{name}'. That scope "
                "existed only for the branch push retired in #1494."
            )
