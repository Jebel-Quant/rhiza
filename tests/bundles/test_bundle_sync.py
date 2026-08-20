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

    def test_core_ships_the_front_door_and_none_of_the_make_layer(self):
        """Core must ship a ``Makefile`` and no ``rhiza.mk`` or fragments of its own.

        The Makefile half has been asserted in both directions now, and the reason it flipped
        back is worth keeping. It could not be synced while ``uvx rhiza-task shim`` printed it and
        a repo owned the copy: a template-owned file would have let ``/rhiza:update`` clobber
        whatever the repo appended -- which for this repo was its own ``e2e``/``sync-self``
        targets, so the risk was not hypothetical. Those targets moved to ``local.mk`` (which core
        deliberately does not ignore) and the CLI stopped defining a template, leaving the front
        door where every other config file lives.

        The fragments are the half that must never come back: a ``Makefile`` forwarding to a
        pinned CLI is one file and one version, where ``rhiza.mk`` plus ``make.d/`` was 1481
        synced lines of recipes.
        """
        assert (self.project / "Makefile").is_file(), (
            "core ships no Makefile, so a synced project has no front door at all -- `make test` "
            "reports `No rule to make target` until someone writes one by hand"
        )
        assert not (self.project / ".rhiza" / "rhiza.mk").exists(), "core ships rhiza.mk again"
        stale = sorted((self.project / ".rhiza").rglob("*.mk"))
        assert not stale, f"core ships make fragments again: {[f.name for f in stale]}"

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

    def test_uv_is_still_provisioned_without_a_language_layer(self):
        """Something must still bootstrap uv, whatever the project is written in.

        core's ``bootstrap.mk`` had an ``install-uv`` target for this, and the reason it was
        core's rather than a layer's has not changed: uvx runs prek, mkdocs and semgrep whatever
        the language. The job lives in the shim, which resolves ``UVX`` to ``./bin/uvx`` and has a
        rule to download it -- so ``make <anything>`` still works on a bare runner, which is what
        keeps rhiza's own required ``Pre-commit hooks`` check green.

        Read from the synced file, which needs no network and no subprocess. While the CLI printed
        the shim this had to generate it, and *skipped* when ``uvx`` could not be reached -- so the
        assertion protecting a required status check was the one that quietly stopped running
        offline.
        """
        shim = (self.project / "Makefile").read_text(encoding="utf-8")
        assert "UVX ?=" in shim, "the shim no longer resolves a uvx path"
        assert "astral.sh/uv/install.sh" in shim, (
            "the shim no longer downloads uv, so `make fmt` fails on a runner without it"
        )

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

    def test_python_core_ships_no_make_fragment(self):
        """The Python gates are the CLI's now, not ``python.mk``'s.

        The contract itself -- that a layer provides ``install``, ``all``, ``deps``, ``license``
        and the rest under names no caller has to translate -- is asserted against the task
        registry in ``test_layer_contract.py``, which is where it moved. What is left to check
        here is that the fragment does not come back alongside it, which would give a consumer two
        definitions of every gate and no way to know which one ran.
        """
        stale = sorted((self.project / ".rhiza").rglob("*.mk"))
        assert not stale, f"python-core ships make fragments again: {[f.name for f in stale]}"

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

    def test_tests_bundle_ships_no_make_fragment(self):
        """The optional extras are CLI tasks now, not ``test.mk`` targets.

        ``benchmark``, ``hypothesis-test``, ``stress`` and ``mutation`` are what this bundle
        exists for, and all four are registered tasks — so the fragment that defined them has
        nothing left to own. What the bundle still ships is its *configuration*, which the
        assertions below cover.
        """
        stale = sorted((self.project / ".rhiza").rglob("*.mk"))
        assert not stale, f"the tests bundle ships make fragments again: {[f.name for f in stale]}"

    def test_no_rhiza_tests_folder_is_synced(self):
        """The sync must not deliver a `.rhiza/tests` folder any more (#1540).

        It used to carry the shared `conftest.py` and one module per bundle. The checks are
        the pinned pytest-rhiza dependency now, named through `RHIZA_CHECKS`, so a folder
        appearing here again would mean a bundle re-added template-owned test code — which
        nothing runs, since the gate names modules rather than paths.
        """
        assert not (self.project / ".rhiza" / "tests").exists(), (
            "the sync delivered a .rhiza/tests folder; the rhiza checks are a dependency (#1540)"
        )

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
