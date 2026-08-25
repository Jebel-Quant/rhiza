"""Byte-identity sync tests for bundles adopted together.

What remains after #1514 split the module: the per-bundle and bundle-plus-overlay sync
checks, each small and each asserting the same shape — sync this combination, and the
files a consumer receives are byte-identical to the bundle sources.

The CI-parity suites for the two hosted profiles moved to ``test_profile_ci_parity.py``
and the dependency-group assertions to ``test_dependency_groups.py``.

``TestVscodeBundleSync`` stays here deliberately: ``_EXEMPT['vscode']`` in
``test_bundle_test_coverage.py`` names this module as where that bundle is covered.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
import yaml

# pytest's own hookspecs, read rather than listed: the alternative is a hand-written set of
# names that goes stale silently. Private, so the anchor assertion in the test using it is
# what turns a pytest reorganisation into a failure instead of a check that accepts anything.
from _pytest import hookspec

from tests.registry import require as require_registry
from tests.registry import resolves
from tests.util import sync_bundles

# Hook-name prefixes the `benchmark` gate does provide, because its own plugin declares them.
# The gate runs `pytest` with `pytest-benchmark` and `pygal`; pygal is a charting library and
# contributes no hooks.
_GATE_PLUGIN_HOOK_PREFIXES = ("pytest_benchmark_",)


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

    def test_docker_ships_no_make_fragment(self) -> None:
        """The bundle's payload is the Dockerfile; its targets come from the pinned CLI.

        ``.rhiza/make.d/docker.mk`` was the fragment carrying ``docker-build``,
        ``docker-run`` and ``docker-clean``. They are rhiza-task tasks now, reached
        through the shim's catch-all, and that the pin still carries them is asserted by
        ``tests/api/test_bundle_cli_targets.py``. A fragment reappearing here would
        shadow the CLI, since an explicit rule beats a pattern rule.
        """
        assert not (self.project / ".rhiza" / "make.d").exists()

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


class TestDevcontainerBundleSync:
    """Syncing the devcontainer bundle provides the VS Code DevContainer configuration."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync the devcontainer bundle into a fresh directory."""
        sync_bundles(root, ["devcontainer"], tmp_path)
        self.project = tmp_path

    def test_devcontainer_json_exists(self) -> None:
        """devcontainer.json must be present after syncing the devcontainer bundle."""
        assert (self.project / ".devcontainer" / "devcontainer.json").is_file()

    def test_bootstrap_sh_exists(self) -> None:
        """bootstrap.sh post-create script must be present."""
        assert (self.project / ".devcontainer" / "bootstrap.sh").is_file()

    def test_no_github_workflows_from_devcontainer_bundle(self) -> None:
        """The plain devcontainer bundle must not inject any GitHub workflows."""
        workflows = self.project / ".github" / "workflows"
        if workflows.exists():
            devcontainer_wf = [f for f in workflows.glob("*.yml") if "devcontainer" in f.name]
            assert not devcontainer_wf, (
                f"devcontainer bundle unexpectedly injected: {[f.name for f in devcontainer_wf]}"
            )


class TestVscodeBundleSync:
    """Syncing the vscode bundle provides recommended extensions and workspace settings."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync the vscode bundle into a fresh directory."""
        sync_bundles(root, ["vscode"], tmp_path)
        self.project = tmp_path

    def test_extensions_json_exists(self) -> None:
        """.vscode/extensions.json must be present after syncing the vscode bundle."""
        assert (self.project / ".vscode" / "extensions.json").is_file()

    def test_extensions_json_has_recommendations(self) -> None:
        """.vscode/extensions.json must declare a non-empty recommendations list."""
        data = json.loads((self.project / ".vscode" / "extensions.json").read_text())
        assert isinstance(data.get("recommendations"), list)
        assert data["recommendations"], "recommendations list must not be empty"

    def test_settings_json_exists(self) -> None:
        """.vscode/settings.json must be present after syncing the vscode bundle."""
        assert (self.project / ".vscode" / "settings.json").is_file()

    def test_settings_json_is_valid(self) -> None:
        """.vscode/settings.json must parse as valid JSON."""
        data = json.loads((self.project / ".vscode" / "settings.json").read_text())
        assert isinstance(data, dict)

    def test_no_github_workflows_from_vscode_bundle(self) -> None:
        """The plain vscode bundle must not inject any GitHub workflows."""
        workflows = self.project / ".github" / "workflows"
        if workflows.exists():
            assert not list(workflows.glob("*.yml")), "vscode bundle unexpectedly injected workflow files"


class TestDevcontainerWithGithubOverlaySync:
    """Syncing devcontainer + github + github-devcontainer adds the DevContainer CI workflow."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync devcontainer, github, and github-devcontainer bundles."""
        sync_bundles(root, ["devcontainer", "github", "github-devcontainer"], tmp_path)
        self.project = tmp_path

    def test_devcontainer_ci_workflow_exists(self) -> None:
        """rhiza_devcontainer.yml CI workflow stub must be injected."""
        assert (self.project / ".github" / "workflows" / "rhiza_devcontainer.yml").is_file()

    def test_devcontainer_ci_workflow_is_valid_yaml(self) -> None:
        """The injected DevContainer CI workflow must be valid YAML."""
        wf = self.project / ".github" / "workflows" / "rhiza_devcontainer.yml"
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
        content = (self.project / "renovate.json").read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert isinstance(parsed, dict), "renovate.json must be a JSON object"

    def test_renovate_json_has_extends(self) -> None:
        """renovate.json must declare 'extends' with at least one Renovate preset."""
        parsed = json.loads((self.project / "renovate.json").read_text(encoding="utf-8"))
        assert "extends" in parsed, "renovate.json missing 'extends' key"
        assert isinstance(parsed["extends"], list), "renovate.json 'extends' must be a list"
        assert len(parsed["extends"]) > 0, "renovate.json 'extends' must not be empty"


class TestBenchmarksBundleSync:
    """Syncing core + python-core + benchmarks produces benchmark scaffolding."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path: Path, root: Path) -> None:
        """Sync core, python-core, book and benchmarks (transitive closure)."""
        sync_bundles(root, ["core", "python-core", "book", "benchmarks"], tmp_path)
        self.project = tmp_path

    def test_benchmarks_test_directory_exists(self) -> None:
        """tests/benchmarks/ directory must be present."""
        assert (self.project / "tests" / "benchmarks").is_dir(), "tests/benchmarks/ not found"

    def test_the_benchmark_task_is_registered(self) -> None:
        """``benchmark`` must be a task the CLI can run.

        This asserted that ``test.mk`` was synced, on the grounds that benchmarks depend on the
        test infrastructure. The fragment retired to rhiza-task, so what matters is that the task
        exists — the dependency is expressed in its registry entry rather than by a file arriving.
        """
        registry = require_registry()
        assert resolves(registry, "python", "benchmark"), (
            "`benchmark` resolves to no registered task, so this bundle's config has no gate to feed"
        )

    def test_benchmarks_conftest_or_init_present(self) -> None:
        """Benchmarks test directory should contain a conftest or __init__ to set up fixtures."""
        benchmarks_dir = self.project / "tests" / "benchmarks"
        has_setup = (benchmarks_dir / "conftest.py").is_file() or (benchmarks_dir / "__init__.py").is_file()
        assert has_setup, "tests/benchmarks/ has no conftest.py or __init__.py"

    def test_the_synced_scaffolding_declares_no_hook_the_gate_cannot_provide(self) -> None:
        """No synced benchmark module may implement a hook from a plugin the gate does not install.

        This is the one way a *template* file can break the gate it ships with, and it did.
        ``conftest.py`` defined ``pytest_html_report_title`` while the ``benchmark`` task injects
        only ``pytest-benchmark`` and ``pygal`` — it writes a histogram and a JSON file, not an
        HTML report. pluggy validates hook *names* at ``perform_collect``, so this is not an
        unused function: pytest raises ``PluginValidationError: unknown hook`` as an
        INTERNALERROR and exits 3 having collected nothing. Every consumer of this bundle whose
        environment did not happen to carry pytest-html had a ``make benchmark`` that could not
        run, and — since ``book`` needs ``benchmark`` — no ``make book`` either.

        Two properties made it survivable for so long, and both argue for a guard rather than a
        fixed assertion about that one name. The ``test`` gate passes
        ``--ignore=$(tests_folder)/benchmarks``, so the file is never collected by the gate
        everything else runs; and the mother repo shipped no ``tests/benchmarks/`` of its own, so
        the benchmark gate skipped here and dogfooding never reached it either. The check is
        therefore written against the *rule* — the gate's environment is pytest plus
        pytest-benchmark — so the next borrowed hook fails as well.

        The core hookspec list is derived rather than written down, so it cannot rot into a set of
        names pytest no longer has; the anchor assertion is what keeps that derivation from
        narrowing to nothing and passing everything.
        """
        core_hooks = frozenset(name for name in dir(hookspec) if name.startswith("pytest_"))
        assert "pytest_collection_modifyitems" in core_hooks, (
            "pytest's hookspec module yielded no recognisable hook names, so this check would "
            "accept anything — pytest moved them and this derivation needs updating"
        )

        offenders: list[str] = []
        for path in sorted((self.project / "tests" / "benchmarks").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            offenders += [
                f"{path.name}::{node.name}"
                for node in tree.body
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and node.name.startswith("pytest_")
                and node.name not in core_hooks
                and not node.name.startswith(_GATE_PLUGIN_HOOK_PREFIXES)
            ]

        assert not offenders, (
            f"synced benchmark scaffolding implements hooks the `benchmark` gate provides no "
            f"plugin for, which makes pytest exit 3 before collecting anything: {offenders}"
        )
