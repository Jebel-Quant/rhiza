"""Multi-bundle sync combination tests.

Each test class simulates a distinct user intent — a profile or a hand-picked set
of bundles — and asserts that the resulting project directory contains exactly the
files the user would expect.

Tests deliberately avoid importing `sync_bundles` from test_bundle_sync to keep the
files independent; the helper is small enough to duplicate and the duplication makes
each failure message self-contained.
"""

from __future__ import annotations

import os
import re
import shutil
import tomllib
from pathlib import Path

from packaging.requirements import Requirement

import pytest
import yaml

# ---------------------------------------------------------------------------
# Sync helper (same as test_bundle_sync.py — kept local for independence)
# ---------------------------------------------------------------------------


def _copy_entry(src: Path, dest: Path) -> None:
    """Copy src into dest, resolving any symlink to get the real content."""
    real = src.resolve() if src.is_symlink() else src
    dest.parent.mkdir(parents=True, exist_ok=True)
    if real.is_dir():
        shutil.copytree(real, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(real, dest)


def sync_bundles(root: Path, bundle_names: list[str], dest: Path) -> None:
    """Copy all files from the named bundles into dest.

    Walks each bundle directory without following symlinks, so directory
    symlinks are copied as whole resolved trees and file symlinks have their
    real content copied.
    """
    for name in bundle_names:
        bundle_dir = root / "bundles" / name
        if not bundle_dir.is_dir():
            pytest.fail(f"Bundle directory does not exist: bundles/{name}")

        for dirpath, dirs, files in os.walk(bundle_dir, followlinks=False):
            current = Path(dirpath)

            for d in dirs[:]:
                child = current / d
                if child.is_symlink():
                    dirs.remove(d)
                    _copy_entry(child, dest / child.relative_to(bundle_dir))

            for f in files:
                child = current / f
                _copy_entry(child, dest / child.relative_to(bundle_dir))


PARITY_JOB_COMMANDS = {
    "test": "make test",
    "docs-coverage": "make docs-coverage",
    "typecheck": "make typecheck",
    "deptry": "make deptry",
    "pre-commit": "make fmt",
    "validate": "make validate",
    "security": "make security",
    "license": "make license",
}


def _load_yaml(path: Path) -> dict:
    """Load a YAML document from disk."""
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _normalise_job_name(name: str) -> str:
    """Collapse forge-specific job namespaces to a shared parity key."""
    job_name = name.split(":", 1)[-1]
    return "validate" if job_name == "validation" else job_name


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


def _contains_make_command(commands: str, target: str) -> bool:
    """Return True when commands invoke the given Make target with or without -f."""
    return any(candidate in commands for candidate in (f"make {target}", f"make -f .rhiza/rhiza.mk {target}"))


def _group_has_dependency(group: list[str], package_name: str) -> bool:
    """Return True if a dependency group contains a given package name (exact match)."""
    return any(Requirement(dep).name.lower() == package_name.lower() for dep in group)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pyproject_declares_uv_dependency_groups(root: Path) -> None:
    """pyproject.toml should expose lint/test/docs uv groups for focused installs."""
    with (root / "pyproject.toml").open("rb") as fh:
        pyproject = tomllib.load(fh)

    groups = pyproject.get("dependency-groups", {})
    assert {"lint", "test", "docs"} <= set(groups)

    assert _group_has_dependency(groups["lint"], "ruff")
    assert _group_has_dependency(groups["lint"], "interrogate")
    assert _group_has_dependency(groups["lint"], "pre-commit")

    assert _group_has_dependency(groups["test"], "pytest")
    assert _group_has_dependency(groups["test"], "pytest-cov")
    assert _group_has_dependency(groups["test"], "hypothesis")
    assert _group_has_dependency(groups["test"], "mutmut")
    assert _group_has_dependency(groups["test"], "pytest-timeout")
    assert _group_has_dependency(groups["test"], "pytest-xdist")

    assert _group_has_dependency(groups["docs"], "marimo")
    assert _group_has_dependency(groups["docs"], "numpy")
    assert _group_has_dependency(groups["docs"], "pandas")
    assert _group_has_dependency(groups["docs"], "plotly")
    assert _group_has_dependency(groups["docs"], "mkdocs-material")
    assert _group_has_dependency(groups["docs"], "pdoc")


def test_core_bundle_pyproject_declares_uv_dependency_groups(root: Path) -> None:
    """bundles/core/pyproject.toml must expose lint/test/docs groups for downstream repos."""
    pyproject_path = root / "bundles" / "core" / "pyproject.toml"
    assert pyproject_path.is_file(), "bundles/core/pyproject.toml not found"

    with pyproject_path.open("rb") as fh:
        pyproject = tomllib.load(fh)

    groups = pyproject.get("dependency-groups", {})
    assert {"lint", "test", "docs"} <= set(groups), (
        f"bundles/core/pyproject.toml is missing dependency groups; found: {set(groups)}"
    )


class TestGitlabProjectProfileSync:
    """The 'gitlab-project' profile produces CI pipelines but zero .github/ files."""

    # Transitive closure of gitlab-project: gitlab-book, gitlab-marimo, gitlab-tests
    # which require book, marimo, tests, gitlab, core
    GITLAB_PROJECT_BUNDLES = [
        "core",
        "book",
        "marimo",
        "tests",
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

    def test_core_infrastructure_present(self) -> None:
        """Core Makefile and rhiza.mk must be present alongside GitLab CI."""
        assert (self.project / "Makefile").is_file()
        assert (self.project / ".rhiza" / "rhiza.mk").is_file()

    def test_test_mk_present(self) -> None:
        """test.mk fragment must be synced (from the tests bundle)."""
        assert (self.project / ".rhiza" / "make.d" / "test.mk").is_file()

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
        gitlab_test_job = _gitlab_jobs_from_includes(self.project)["ci:test"]
        gitlab_matrix = gitlab_test_job["parallel"]["matrix"][0]["PYTHON_VERSION"]

        assert "make -f .rhiza/rhiza.mk -s version-matrix" in github_matrix_source
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

        target = command.removeprefix("make ")
        assert _contains_make_command(github_commands, target)
        assert _contains_make_command(gitlab_commands, target)

    def test_gitlab_ci_jobs_define_timeout_budgets(self) -> None:
        """GitLab CI core jobs must define explicit timeout budgets."""
        gitlab_jobs = _gitlab_jobs_from_includes(self.project)
        expected = {
            "ci:test": "20m",
            "ci:docs-coverage": "10m",
            "ci:typecheck": "5m",
            "ci:deptry": "5m",
            "ci:pre-commit": "5m",
            "ci:validate": "5m",
            "ci:security": "10m",
            "ci:license": "10m",
        }

        for job_name, timeout in expected.items():
            assert gitlab_jobs[job_name]["timeout"] == timeout


class TestDockerBundleSync:
    """Syncing core + docker bundle produces containerisation scaffolding."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync core and docker bundles into a fresh directory."""
        sync_bundles(root, ["core", "docker"], tmp_path)
        self.project = tmp_path

    def test_dockerfile_exists(self) -> None:
        """Dockerfile must be present after syncing the docker bundle."""
        assert (self.project / "Dockerfile").is_file()

    def test_dockerignore_exists(self) -> None:
        """A .dockerignore file must be present."""
        # The docker bundle uses Dockerfile.dockerignore name convention
        dockerignore = self.project / "Dockerfile.dockerignore"
        alt_dockerignore = self.project / ".dockerignore"
        assert dockerignore.is_file() or alt_dockerignore.is_file(), (
            "Neither Dockerfile.dockerignore nor .dockerignore found"
        )

    def test_docker_mk_exists(self) -> None:
        """docker.mk Makefile fragment must be present."""
        assert (self.project / ".rhiza" / "make.d" / "docker.mk").is_file()

    def test_no_github_workflows_from_docker_bundle(self) -> None:
        """The plain docker bundle must not inject any GitHub workflows."""
        workflows = self.project / ".github" / "workflows"
        if workflows.exists():
            docker_wf = [f for f in workflows.glob("*.yml") if "docker" in f.name]
            assert not docker_wf, f"docker bundle unexpectedly injected: {[f.name for f in docker_wf]}"


class TestDockerWithGithubOverlaySync:
    """Syncing core + docker + github + github-docker adds the Docker CI workflow."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync core, docker, github, and github-docker bundles."""
        sync_bundles(root, ["core", "docker", "github", "github-docker"], tmp_path)
        self.project = tmp_path

    def test_docker_ci_workflow_exists(self) -> None:
        """rhiza_docker.yml CI workflow stub must be injected."""
        assert (self.project / ".github" / "workflows" / "rhiza_docker.yml").is_file()

    def test_docker_ci_workflow_is_valid_yaml(self) -> None:
        """The injected Docker CI workflow must be valid YAML."""
        wf = self.project / ".github" / "workflows" / "rhiza_docker.yml"
        parsed = yaml.safe_load(wf.read_text(encoding="utf-8"))
        assert parsed is not None


class TestLegalBundleSync:
    """Syncing the legal bundle provides LICENSE, SECURITY.md, and community docs."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync the legal bundle into a fresh directory."""
        sync_bundles(root, ["legal"], tmp_path)
        self.project = tmp_path

    def test_license_file_present(self) -> None:
        """LICENSE must exist at the project root."""
        assert (self.project / "LICENSE").is_file()

    def test_license_file_non_empty(self) -> None:
        """LICENSE must contain actual licence text."""
        content = (self.project / "LICENSE").read_text(encoding="utf-8")
        assert len(content) > 100, "LICENSE file is suspiciously short"

    def test_security_md_present(self) -> None:
        """SECURITY.md must be present for responsible disclosure."""
        assert (self.project / "SECURITY.md").is_file()

    def test_contributing_guide_present(self) -> None:
        """CONTRIBUTING.md must be present."""
        # May be at root or inside .rhiza/
        root_contrib = self.project / "CONTRIBUTING.md"
        rhiza_contrib = self.project / ".rhiza" / "CONTRIBUTING.md"
        assert root_contrib.is_file() or rhiza_contrib.is_file(), "CONTRIBUTING.md not found at project root or .rhiza/"

    def test_legal_files_produce_no_symlinks(self) -> None:
        """Synced legal files must be real files, not symlinks."""
        for path in self.project.rglob("*"):
            if path.is_file():
                assert not path.is_symlink(), f"Unexpected symlink: {path.relative_to(self.project)}"


class TestRenovateBundleSync:
    """Syncing the renovate bundle provides the Renovate bot configuration."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync the renovate bundle into a fresh directory."""
        sync_bundles(root, ["renovate"], tmp_path)
        self.project = tmp_path

    def test_renovate_json_present(self) -> None:
        """renovate.json must be present at the project root."""
        assert (self.project / "renovate.json").is_file()

    def test_renovate_json_is_valid(self) -> None:
        """renovate.json must be valid JSON."""
        import json

        content = (self.project / "renovate.json").read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert isinstance(parsed, dict), "renovate.json must be a JSON object"

    def test_renovate_json_has_extends(self) -> None:
        """renovate.json must declare 'extends' with at least one Renovate preset."""
        import json

        parsed = json.loads((self.project / "renovate.json").read_text(encoding="utf-8"))
        assert "extends" in parsed, "renovate.json missing 'extends' key"
        assert isinstance(parsed["extends"], list), "renovate.json 'extends' must be a list"
        assert len(parsed["extends"]) > 0, "renovate.json 'extends' must not be empty"


class TestGhAwBundleSync:
    """Syncing core + github + gh-aw produces agentic workflow infrastructure."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync core, github, and gh-aw bundles."""
        sync_bundles(root, ["core", "github", "gh-aw"], tmp_path)
        self.project = tmp_path

    def test_copilot_setup_steps_workflow_exists(self) -> None:
        """copilot-setup-steps.yml must be present to pre-configure the agent environment."""
        assert (self.project / ".github" / "workflows" / "copilot-setup-steps.yml").is_file()

    def test_gh_aw_validate_workflow_exists(self) -> None:
        """rhiza_gh-aw-validate.yml must be present to validate lock file freshness."""
        assert (self.project / ".github" / "workflows" / "rhiza_gh-aw-validate.yml").is_file()

    def test_gh_aw_mk_fragment_present(self) -> None:
        """gh-aw.mk Makefile fragment must be present."""
        assert (self.project / ".rhiza" / "make.d" / "gh-aw.mk").is_file()

    def test_hooks_json_present(self) -> None:
        """hooks.json quality gates must be present for agentic sessions."""
        assert (self.project / ".github" / "hooks" / "hooks.json").is_file()

    def test_hooks_json_is_valid_json(self) -> None:
        """hooks.json must be valid JSON."""
        import json

        hooks_json = self.project / ".github" / "hooks" / "hooks.json"
        parsed = json.loads(hooks_json.read_text(encoding="utf-8"))
        assert isinstance(parsed, (dict, list)), "hooks.json must be a JSON object or array"

    def test_copilot_instructions_present(self) -> None:
        """Copilot instructions file must be present for AI agent guidance."""
        assert (self.project / ".github" / "copilot-instructions.md").is_file()

    def test_agent_definitions_present(self) -> None:
        """At least one agent definition must exist in .github/agents/."""
        agents_dir = self.project / ".github" / "agents"
        assert agents_dir.is_dir(), ".github/agents/ directory not found"
        agent_files = list(agents_dir.glob("*.md"))
        assert len(agent_files) > 0, "No agent definition .md files found"


class TestBenchmarksBundleSync:
    """Syncing core + tests + benchmarks produces benchmark scaffolding."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync core, book, tests, and benchmarks bundles (transitive closure)."""
        sync_bundles(root, ["core", "book", "tests", "benchmarks"], tmp_path)
        self.project = tmp_path

    def test_benchmarks_test_directory_exists(self) -> None:
        """tests/benchmarks/ directory must be present."""
        assert (self.project / "tests" / "benchmarks").is_dir(), "tests/benchmarks/ not found"

    def test_test_mk_present(self) -> None:
        """test.mk must be present (benchmarks depend on test infrastructure)."""
        assert (self.project / ".rhiza" / "make.d" / "test.mk").is_file()

    def test_benchmarks_conftest_or_init_present(self) -> None:
        """Benchmarks test directory should contain a conftest or __init__ to set up fixtures."""
        benchmarks_dir = self.project / "tests" / "benchmarks"
        has_setup = (benchmarks_dir / "conftest.py").is_file() or (benchmarks_dir / "__init__.py").is_file()
        assert has_setup, "tests/benchmarks/ has no conftest.py or __init__.py"


class TestGithubProjectProfileSync:
    """The 'github-project' profile produces a complete, CI-wired project skeleton."""

    # Full transitive closure of github-project
    GITHUB_PROJECT_BUNDLES = [
        "core",
        "book",
        "marimo",
        "tests",
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

    def test_sync_workflow_present(self) -> None:
        """rhiza_sync.yml sync workflow must be present."""
        assert (self.project / ".github" / "workflows" / "rhiza_sync.yml").is_file()

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
            has_on = "on" in doc or True in doc
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
