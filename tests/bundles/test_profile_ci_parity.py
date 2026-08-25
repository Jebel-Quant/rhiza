"""The two hosted profiles must run the same gates as each other.

Split from ``test_bundle_combinations.py`` in #1514 (631 lines, maintainability index
**B (15.84)**). These are the heaviest suites in that module and the only ones that parse
pipeline definitions: they assemble ``github-project`` and ``gitlab-project`` and check
that each platform's jobs invoke the same ``make`` targets, so a gate added to one
platform's CI cannot silently skip the other.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tests.util import sync_bundles

# The gate each job must invoke, keyed by job name. These are rhiza-task task names
# rather than Make targets: v1.4.0 retired the synced make layer, so both pipelines now
# reach the CLI directly and `make <gate>` resolves nothing in a synced project.
PARITY_JOB_COMMANDS = {
    "test": "test",
    "docs-coverage": "docs-coverage",
    "typecheck": "typecheck",
    "deptry": "deps",
    "pre-commit": "fmt",
    "security": "security",
    "license": "license",
}


def _load_yaml(path: Path) -> dict:
    """Load a YAML document from disk."""
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _normalise_job_name(name: str) -> str:
    """Collapse forge-specific job namespaces to a shared parity key."""
    return name.split(":", 1)[-1]


def _supported_python_versions(root: Path) -> list[str]:
    """Return the supported Python versions declared in pyproject classifiers."""
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    return re.findall(r"Programming Language :: Python :: (3\.\d+)", pyproject)


def _gitlab_jobs_from_includes(project: Path) -> dict[str, dict]:
    """Load all included GitLab workflow jobs from the synced project."""
    pipeline = _load_yaml(project / ".gitlab-ci.yml")
    jobs: dict[str, dict] = {}

    for include in pipeline.get("include", []):
        local_path = include.get("local") if isinstance(include, dict) else None
        if not local_path:
            continue
        # Honour GitLab `exists:` include rules: an include guarded by an
        # `exists` clause is a no-op when the referenced file is absent (used by
        # opt-in overlay bundles such as gitlab-quality-review). Skip it here so
        # the profile-sync assertions match what GitLab would actually run.
        skip = False
        for rule in include.get("rules", []) if isinstance(include, dict) else []:
            exists = rule.get("exists") if isinstance(rule, dict) else None
            if exists and not any((project / candidate).exists() for candidate in exists):
                skip = True
                break
        if skip:
            continue
        workflow = _load_yaml(project / local_path)
        for name, job in workflow.items():
            if isinstance(job, dict) and not name.startswith("."):
                jobs[name] = job

    return jobs


def _job_commands(job: dict, key: str) -> list[str]:
    """Return the shell commands for a GitHub or GitLab job block."""
    commands = job.get(key, []) or []
    if isinstance(commands, str):
        return [commands]
    return [str(command) for command in commands]


def _contains_gate_invocation(commands: str, target: str) -> bool:
    """Return True when the commands invoke the given gate, by either interface.

    The CLI form is what both pipelines ship now. The Make forms are still accepted
    because a consumer pinned to an older tag, or one that kept a repo-owned target
    shadowing the catch-all, invokes the same gate through them -- what this asserts is
    that the job runs the gate at all, not which front door it uses.
    """
    candidates = (
        f'uvx "$RHIZA_TASK" {target}',
        f"make {target}",
        f"make -f .rhiza/rhiza.mk {target}",
    )
    return any(candidate in commands for candidate in candidates)


class TestGitlabProjectProfileSync:
    """The 'gitlab-project' profile produces CI pipelines but zero .github/ files."""

    # Transitive closure of gitlab-project: gitlab-book, gitlab-marimo, gitlab-tests
    # which require book, python-core, gitlab, core
    GITLAB_PROJECT_BUNDLES = [
        "core",
        "book",
        "gitlab",
        "gitlab-book",
        "gitlab-marimo",
        "gitlab-tests",
    ]

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync the gitlab-project profile bundle closure into a fresh directory."""
        sync_bundles(root, self.GITLAB_PROJECT_BUNDLES, tmp_path)
        self.project = tmp_path

    def test_gitlab_ci_file_exists(self) -> None:
        """GitLab CI pipeline file must be present."""
        assert (self.project / ".gitlab-ci.yml").is_file(), ".gitlab-ci.yml not found"

    def test_gitlab_workflows_directory_exists(self) -> None:
        """GitLab workflow helpers live under .gitlab/workflows/."""
        assert (self.project / ".gitlab" / "workflows").is_dir()

    def test_no_github_workflows_injected(self) -> None:
        """GitLab profile must not produce any .github/workflows/ files."""
        workflows = self.project / ".github" / "workflows"
        if workflows.exists():
            files = list(workflows.glob("*.yml"))
            assert not files, f"Unexpected GitHub workflows in GitLab project: {[f.name for f in files]}"

    def test_gitlab_ci_is_valid_yaml(self) -> None:
        """The injected .gitlab-ci.yml must parse as valid YAML."""
        content = (self.project / ".gitlab-ci.yml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert parsed is not None, ".gitlab-ci.yml is empty or invalid YAML"

    def test_the_front_door_is_synced_and_the_gate_fragments_are_not(self) -> None:
        """The profile must ship a ``Makefile`` and no ``rhiza.mk`` or gate fragment.

        Both halves matter and they used to move together. The GitLab pipeline calls ``make test``,
        ``make fmt`` and the rest — which ``test_ci_workflows_expose_same_core_job_names`` below
        checks — so a profile shipping no front door leaves a pipeline with nothing to call: for
        the interval when ``uvx rhiza-task shim`` printed it, every consumer had to run that by
        hand before its own CI could pass. ``core`` owns the file again, so the sync delivers it.

        What must stay gone is the *content* the fragments held. A ``Makefile`` that forwards to a
        pinned CLI is one file and one version; ``rhiza.mk`` plus ``make.d/`` was 1481 synced lines
        of recipes, and a repo that still has them on disk shadows the CLI rather than merely
        duplicating it.
        """
        assert (self.project / "Makefile").is_file(), (
            "the profile ships no Makefile, so `make test` in the pipeline has no front door"
        )
        assert not (self.project / ".rhiza" / "rhiza.mk").exists(), "the profile ships rhiza.mk again"
        make_d = self.project / ".rhiza" / "make.d"
        stale = sorted(f.name for f in make_d.rglob("*.mk")) if make_d.is_dir() else []
        assert not stale, f"the profile ships gate fragments again: {stale}"

    def test_ci_workflows_expose_same_core_job_names(self, root: Path) -> None:
        """GitHub and GitLab CI definitions must expose the same core parity jobs."""
        github_jobs = _load_yaml(root / ".github" / "workflows" / "rhiza_ci.yml")["jobs"]
        gitlab_jobs = _gitlab_jobs_from_includes(self.project)
        expected = set(PARITY_JOB_COMMANDS)

        github_job_names = {_normalise_job_name(name) for name in github_jobs}
        gitlab_job_names = {_normalise_job_name(name) for name in gitlab_jobs}

        assert github_job_names & expected == expected
        assert gitlab_job_names & expected == expected

    def test_ci_workflows_share_python_version_matrix(self, root: Path) -> None:
        """GitHub and GitLab CI must reference the same supported Python versions."""
        github_workflow = _load_yaml(root / ".github" / "workflows" / "rhiza_ci.yml")
        github_generate_steps = github_workflow["jobs"]["generate-matrix"]["steps"]
        github_matrix_source = "\n".join(
            step["run"] for step in github_generate_steps if isinstance(step, dict) and "run" in step
        )
        versions_step = next(step for step in github_generate_steps if step.get("id") == "versions")
        gitlab_test_job = _gitlab_jobs_from_includes(self.project)["ci:test"]
        gitlab_matrix = gitlab_test_job["parallel"]["matrix"][0]["PYTHON_VERSION"]

        assert "hynek/build-and-inspect-python-package" in versions_step["uses"]
        assert "supported_python_classifiers_json_array" in github_matrix_source
        assert github_workflow["jobs"]["test"]["strategy"]["matrix"]["python-version"] == (
            "${{ fromJson(needs.generate-matrix.outputs.matrix) }}"
        )
        assert gitlab_matrix == _supported_python_versions(root)

    @pytest.mark.parametrize(("job_name", "command"), PARITY_JOB_COMMANDS.items())
    def test_ci_workflows_match_core_commands(self, root: Path, job_name: str, command: str) -> None:
        """GitHub and GitLab CI must run equivalent commands for core parity jobs."""
        github_jobs = _load_yaml(root / ".github" / "workflows" / "rhiza_ci.yml")["jobs"]
        gitlab_jobs = _gitlab_jobs_from_includes(self.project)

        github_job = next(job for name, job in github_jobs.items() if _normalise_job_name(name) == job_name)
        gitlab_job = next(job for name, job in gitlab_jobs.items() if _normalise_job_name(name) == job_name)

        github_commands = "\n".join(
            _job_commands(step, "run")[0] for step in github_job.get("steps", []) if "run" in step
        )
        gitlab_commands = "\n".join(_job_commands(gitlab_job, "script"))

        assert _contains_gate_invocation(github_commands, command)
        assert _contains_gate_invocation(gitlab_commands, command)

    def test_gitlab_ci_jobs_define_timeout_budgets(self) -> None:
        """GitLab CI core jobs must define explicit timeout budgets."""
        gitlab_jobs = _gitlab_jobs_from_includes(self.project)
        expected = {
            "ci:test": "20m",
            "ci:docs-coverage": "10m",
            "ci:typecheck": "5m",
            "ci:deptry": "5m",
            "ci:pre-commit": "5m",
            "ci:security": "10m",
            "ci:license": "10m",
        }

        for job_name, timeout in expected.items():
            assert gitlab_jobs[job_name]["timeout"] == timeout


class TestGithubProjectProfileSync:
    """The 'github-project' profile produces a complete, CI-wired project skeleton."""

    # Full transitive closure of github-project
    GITHUB_PROJECT_BUNDLES = [
        "core",
        "book",
        "github",
        "github-book",
        "github-marimo",
        "github-tests",
    ]

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync the full github-project bundle closure."""
        sync_bundles(root, self.GITHUB_PROJECT_BUNDLES, tmp_path)
        self.project = tmp_path

    def test_ci_workflow_present(self) -> None:
        """rhiza_ci.yml CI workflow must be present."""
        assert (self.project / ".github" / "workflows" / "rhiza_ci.yml").is_file()

    def test_codeql_workflow_present(self) -> None:
        """rhiza_codeql.yml security workflow must be present."""
        assert (self.project / ".github" / "workflows" / "rhiza_codeql.yml").is_file()

    def test_book_workflow_present(self) -> None:
        """rhiza_book.yml documentation workflow must be present."""
        assert (self.project / ".github" / "workflows" / "rhiza_book.yml").is_file()

    def test_benchmark_workflow_present(self) -> None:
        """rhiza_benchmark.yml benchmark workflow must be present."""
        assert (self.project / ".github" / "workflows" / "rhiza_benchmark.yml").is_file()

    def test_marimo_workflow_present(self) -> None:
        """rhiza_marimo.yml notebook workflow must be present."""
        assert (self.project / ".github" / "workflows" / "rhiza_marimo.yml").is_file()

    def test_all_injected_workflows_are_valid_yaml(self) -> None:
        """Every injected workflow must be valid YAML with required fields.

        Note: pyyaml parses 'on:' as Python boolean True (YAML boolean literal).
        We check for both True and the string 'on' as valid trigger keys.
        """
        workflows_dir = self.project / ".github" / "workflows"
        errors: list[str] = []
        for wf in workflows_dir.glob("*.yml"):
            with wf.open(encoding="utf-8") as fh:
                doc = yaml.safe_load(fh)
            if not isinstance(doc, dict):
                errors.append(f"  {wf.name}: not a YAML mapping")
                continue
            # pyyaml parses 'on:' as True; check both forms
            has_on = "on" in doc or any(k is True for k in doc)
            if not has_on:
                errors.append(f"  {wf.name}: missing 'on' trigger")
            if "jobs" not in doc:
                errors.append(f"  {wf.name}: missing 'jobs'")
        if errors:
            pytest.fail("Workflow validation failures:\n" + "\n".join(errors))

    def test_no_gitlab_files_injected(self) -> None:
        """github-project profile must not produce any GitLab CI files."""
        assert not (self.project / ".gitlab-ci.yml").is_file(), (
            ".gitlab-ci.yml should not be present in a github-project sync"
        )
        gitlab_dir = self.project / ".gitlab"
        if gitlab_dir.exists():
            # .gitlab/ dir might exist if some other mechanism wrote it; workflows should not
            gitlab_wf = list((gitlab_dir / "workflows").glob("*.yml")) if (gitlab_dir / "workflows").exists() else []
            assert not gitlab_wf, f"Unexpected GitLab workflows found: {[f.name for f in gitlab_wf]}"

    def test_dependabot_present(self) -> None:
        """dependabot.yml must be present from the github bundle."""
        assert (self.project / ".github" / "dependabot.yml").is_file()

    def test_docs_skeleton_present(self) -> None:
        """docs/ directory with mkdocs base config must be present."""
        assert (self.project / "docs" / "index.md").is_file()
        assert (self.project / "docs" / "mkdocs-base.yml").is_file()
