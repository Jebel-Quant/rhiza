"""Byte-identity sync tests for the core bundle, the Python layer and the profiles.

Reduced to this scope in #1514: the module had reached 838 lines at maintainability index
**B (9.49)**, carrying the sync assertions for all three language layers plus the
cross-layer contract in one file.

The Rust and Go layers moved to ``test_rust_layer_sync.py`` and ``test_go_layer_sync.py``
— each is self-contained, since a layer's sync assertions never reference another's — and
the properties that hold *across* layers moved to ``test_layer_contract.py``.
"""

from __future__ import annotations

import tomllib

import pytest
import yaml

from tests.util import sync_bundles


class TestCoreBundleSync:
    """Syncing the core bundle produces the expected project skeleton."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync the core bundle into a fresh directory."""
        sync_bundles(root, ["core"], tmp_path)
        self.project = tmp_path

    def test_makefile_exists(self):
        """Makefile is present at the project root."""
        assert (self.project / "Makefile").is_file()

    def test_rhiza_mk_exists(self):
        """Core make infrastructure is in place."""
        assert (self.project / ".rhiza" / "rhiza.mk").is_file()

    def test_make_d_fragments_exist(self):
        """All core Makefile fragments are present."""
        make_d = self.project / ".rhiza" / "make.d"
        for name in ("bootstrap.mk", "doctor.mk", "quality.mk", "custom-env.mk", "custom-task.mk"):
            assert (make_d / name).is_file(), f"Missing make.d fragment: {name}"

    def test_cliff_config_exists(self):
        """git-cliff config is synced by the core bundle."""
        assert (self.project / "cliff.toml").is_file()

    def test_cliff_config_uses_keep_a_changelog_groups(self):
        """cliff.toml keeps semantic changelog groupings instead of git-cliff defaults."""
        cliff_toml = (self.project / "cliff.toml").read_text(encoding="utf-8")
        assert "New Features" in cliff_toml
        assert "Bug Fixes" in cliff_toml
        assert "Documentation" in cliff_toml
        assert "Dependencies" in cliff_toml
        assert "skip = true" in cliff_toml

    def test_pyproject_template_exists(self, test_data_dir):
        """Core bundle ships a pyproject.toml template."""
        assert (test_data_dir / "pyproject.toml").is_file()

    def test_pyproject_template_has_required_structure(self, test_data_dir):
        """Core pyproject template has the minimum Rhiza-required sections."""
        with (test_data_dir / "pyproject.toml").open("rb") as f:
            pyproject = tomllib.load(f)

        project = pyproject.get("project", {})
        assert isinstance(project, dict), "[project] section missing from pyproject.toml template"

        for field in ("name", "version", "description", "readme", "requires-python"):
            value = project.get(field)
            assert isinstance(value, str), f"[project].{field} missing in pyproject.toml template"
            assert value.strip(), f"[project].{field} cannot be empty in pyproject.toml template"

        groups = pyproject.get("dependency-groups", {})
        assert isinstance(groups, dict), "[dependency-groups] section missing from pyproject.toml template"

    def test_no_symlinks_in_synced_project(self):
        """Synced files are real files, not symlinks — as a downstream project would receive."""
        for path in self.project.rglob("*"):
            if path.is_file():
                assert not path.is_symlink(), f"Unexpected symlink in synced project: {path.relative_to(self.project)}"


class TestCoreIsLanguageNeutral:
    """Core alone ships no language toolchain — that is the language layer's job."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync only the core bundle into a fresh directory."""
        sync_bundles(root, ["core"], tmp_path)
        self.project = tmp_path

    @pytest.mark.parametrize("name", ["ruff.toml", ".bandit", ".python-version", ".pre-commit-config.yaml"])
    def test_python_tooling_is_not_in_core(self, name):
        """Python-only config moved to python-core and must not come back."""
        assert not (self.project / name).exists(), f"{name} belongs to python-core, not core"

    def test_core_defines_no_install_or_all_target(self):
        """`install` and `all` are the language layer's contract, not core's."""
        fragments = list((self.project / ".rhiza").rglob("*.mk"))
        assert fragments, "core ships no make fragments at all"
        for fragment in fragments:
            for line in fragment.read_text(encoding="utf-8").splitlines():
                assert not line.startswith("install:"), f"{fragment.name} defines install"
                assert not line.startswith("all:"), f"{fragment.name} defines all"

    def test_core_still_provisions_uv_as_a_tool_runner(self):
        """Uvx runs pre-commit/mkdocs/semgrep whatever the language, so core keeps it."""
        bootstrap = (self.project / ".rhiza" / "make.d" / "bootstrap.mk").read_text(encoding="utf-8")
        assert "install-uv:" in bootstrap

    def test_core_ships_the_semgrep_config_its_own_target_reads(self):
        """`semgrep` is a core target, so its config cannot live in a Python-only bundle.

        Until #1475 `.rhiza/semgrep.yml` was shipped by `tests` (which requires
        python-core) while `quality.mk` — core's — ran
        ``semgrep --config .rhiza/semgrep.yml``. On a Rust crate that broke outright:
        SOURCE_FOLDER defaults to `src`, which a crate has, so the guard passed and
        semgrep ran against a file that was never synced. Asserted here rather than only
        in the Rust class because the mismatch is core's to avoid.
        """
        assert (self.project / ".rhiza" / "semgrep.yml").is_file(), (
            "core defines `make semgrep` but does not ship the config it names"
        )


class TestPythonCoreBundleSync:
    """Syncing core + python-core produces a working Python project layer."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync the core and python-core bundles into a fresh directory."""
        sync_bundles(root, ["core", "python-core"], tmp_path)
        self.project = tmp_path

    @pytest.mark.parametrize("name", ["ruff.toml", ".bandit", ".python-version", ".pre-commit-config.yaml"])
    def test_python_tooling_is_present(self, name):
        """The Python toolchain config the old core used to ship still arrives."""
        assert (self.project / name).is_file(), f"Missing Python toolchain file: {name}"

    def test_ruff_config_does_not_pin_target_version(self):
        """Ruff config should infer target version from project metadata."""
        content = (self.project / "ruff.toml").read_text(encoding="utf-8")
        assert "target-version =" not in content

    def test_python_mk_provides_the_language_contract(self):
        """python.mk owns the target names the rest of the template calls.

        ``rhiza-test`` is deliberately absent: its recipe is language-neutral, so it moved
        to core's quality.mk in #1471 rather than existing identically in all three layers.
        """
        python_mk = (self.project / ".rhiza" / "make.d" / "python.mk").read_text(encoding="utf-8")
        for target in ("install:", "all:", "deps:", "license:"):
            assert target in python_mk, f"python.mk is missing {target}"
        assert "rhiza-test:" not in python_mk, (
            "python.mk redefines rhiza-test, which core now owns — two recipes for one "
            "target name is exactly what #1471 removed"
        )

    @pytest.mark.parametrize("name", [".bumpversion.toml", ".bumpversion.cfg", "setup.cfg", ".rhiza/.cfg.toml"])
    def test_no_bumpversion_config_is_shipped(self, name):
        """Python's version config belongs in the repo's own pyproject.toml (#1453).

        bump-my-version searches four filenames and stops at the first with a
        bumpversion section. pyproject.toml is one of them and is last, so a block
        there rewrites PEP 621 ``[project].version`` natively — while a synced
        ``.bumpversion.toml`` would *shadow* it, and the ``.rhiza/.cfg.toml`` this
        layer used to ship was never searched at all and so did nothing. Either way a
        rhiza-owned file is the wrong home: it cannot carry ``current_version``,
        because the next sync would overwrite the consuming repo's version with the
        template's.

        Rust and Go are the opposite case — no discoverable file exists in those
        languages, so their layers do ship a root ``.bumpversion.toml``.
        """
        assert not (self.project / name).exists(), (
            f"{name} would take precedence over (or silently replace) the repo's own "
            f"pyproject.toml [tool.bumpversion] table"
        )


class TestCoreAndTestsBundleSync:
    """Syncing the Python layer plus the tests bundle adds pytest infrastructure.

    ``python-core`` is in the list because the ``tests`` bundle requires it, and since
    #1475 it is what owns ``pytest.ini`` and the four gates ``all`` names — this bundle
    carries only the optional extras. Syncing ``tests`` without it was never a real
    configuration.
    """

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync core, python-core and tests bundles into a fresh directory."""
        sync_bundles(root, ["core", "python-core", "tests"], tmp_path)
        self.project = tmp_path

    def test_pytest_ini_exists(self):
        """pytest.ini is present."""
        assert (self.project / "pytest.ini").is_file()

    def test_pytest_ini_has_testpaths(self):
        """pytest.ini configures testpaths."""
        content = (self.project / "pytest.ini").read_text()
        assert "testpaths" in content

    def test_pytest_ini_disables_live_logging_by_default(self):
        """pytest.ini disables noisy live CLI logging by default."""
        content = (self.project / "pytest.ini").read_text()
        assert "log_cli = false" in content

    def test_test_mk_exists(self):
        """test.mk Makefile fragment is present."""
        assert (self.project / ".rhiza" / "make.d" / "test.mk").is_file()

    def test_rhiza_tests_conftest_exists(self):
        """Shared test infrastructure (conftest.py) is present."""
        assert (self.project / ".rhiza" / "tests" / "conftest.py").is_file()

    def test_semgrep_config_exists(self):
        """Semgrep static analysis config is present."""
        assert (self.project / ".rhiza" / "semgrep.yml").is_file()


class TestGithubOverlaySync:
    """Syncing github + github-tests injects stub CI workflows as real files."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync core, github, and github-tests bundles."""
        sync_bundles(root, ["core", "github", "tests", "github-tests"], tmp_path)
        self.project = tmp_path

    def test_ci_workflow_exists(self):
        """CI workflow stub is injected."""
        assert (self.project / ".github" / "workflows" / "rhiza_ci.yml").is_file()

    def test_ci_workflow_is_stub(self):
        """Injected CI workflow delegates to the shared reusable workflow."""
        content = (self.project / ".github" / "workflows" / "rhiza_ci.yml").read_text()
        assert "uses: jebel-quant/rhiza/.github/workflows/rhiza_ci.yml" in content

    def test_dependabot_config_exists(self):
        """Dependabot config is present."""
        assert (self.project / ".github" / "dependabot.yml").is_file()

    def test_injected_workflows_are_valid_yaml(self):
        """Every injected workflow file parses as valid YAML."""
        workflows_dir = self.project / ".github" / "workflows"
        for wf in workflows_dir.glob("*.yml"):
            with open(wf, encoding="utf-8") as f:
                parsed = yaml.safe_load(f)
            assert parsed is not None, f"Empty or invalid YAML: {wf.name}"


class TestProfileLocalSync:
    """Syncing the 'local' profile (book + marimo + tests) injects no workflow files."""

    LOCAL_BUNDLES = ["book", "marimo", "tests", "core"]  # transitive closure of 'local' profile

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync all bundles in the local profile transitive closure."""
        sync_bundles(root, self.LOCAL_BUNDLES, tmp_path)
        self.project = tmp_path

    def test_docs_skeleton_exists(self):
        """Base documentation files from the book bundle are present."""
        assert (self.project / "docs" / "index.md").is_file()
        assert (self.project / "docs" / "mkdocs-base.yml").is_file()

    def test_no_github_workflows_injected(self):
        """Local profile must not produce any .github/workflows/ files."""
        workflows_dir = self.project / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml"))
            assert not workflow_files, (
                f"Local profile should not inject workflow files, found: {[f.name for f in workflow_files]}"
            )
