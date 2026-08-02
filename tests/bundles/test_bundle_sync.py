"""Integration tests for the bundle-centric directory layout.

Simulates what rhiza-cli does: resolves a set of bundle names, copies the
files (following symlinks to get real content) into a fresh directory, and
asserts that the resulting project looks exactly as expected.

Each test starts from a green-field temporary directory, so there is no
shared state between scenarios.
"""

from __future__ import annotations

import re
import tomllib

import pytest
import yaml

from tests.util import sync_bundles

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


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
        """python.mk owns the target names the rest of the template calls."""
        python_mk = (self.project / ".rhiza" / "make.d" / "python.mk").read_text(encoding="utf-8")
        for target in ("install:", "all:", "deptry:", "license:", "rhiza-test:"):
            assert target in python_mk, f"python.mk is missing {target}"

    def test_bumpversion_config_targets_pyproject(self):
        """The bump-my-version config points at pyproject.toml, so it is Python's."""
        cfg = (self.project / ".rhiza" / ".cfg.toml").read_text(encoding="utf-8")
        assert 'filename = "pyproject.toml"' in cfg


class TestRustCoreBundleSync:
    """Syncing core + rust-core produces a working Rust project layer.

    The mother repo is a Python project, so nothing here is dogfooded at the root —
    these assertions are the only thing standing between a broken rust-core file and
    a downstream Rust repo.
    """

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync the core and rust-core bundles into a fresh directory."""
        sync_bundles(root, ["core", "rust-core"], tmp_path)
        self.project = tmp_path

    @pytest.mark.parametrize(
        "name", ["rust-toolchain.toml", "rustfmt.toml", "clippy.toml", "deny.toml", ".pre-commit-config.yaml"]
    )
    def test_rust_toolchain_config_is_present(self, name):
        """The cargo-side counterparts of ruff.toml/.bandit all arrive."""
        assert (self.project / name).is_file(), f"Missing Rust toolchain file: {name}"

    @pytest.mark.parametrize("name", ["ruff.toml", ".bandit", ".python-version", "pytest.ini"])
    def test_python_tooling_is_absent(self, name):
        """A Rust repo gets no Python config — the layers are alternatives, not additions."""
        assert not (self.project / name).exists(), f"{name} belongs to python-core, not rust-core"

    def test_rust_mk_provides_the_language_contract(self):
        """rust.mk owns the same target names python.mk does, plus the cargo-backed gates."""
        rust_mk = (self.project / ".rhiza" / "make.d" / "rust.mk").read_text(encoding="utf-8")
        for target in ("install:", "all:", "test::", "coverage:", "typecheck:", "docs-coverage:", "rhiza-test:"):
            assert target in rust_mk, f"rust.mk is missing {target}"

    def test_only_one_language_fragment_is_synced(self):
        """python.mk and rust.mk both define `install` — receiving both would be a clash."""
        fragments = sorted(p.name for p in (self.project / ".rhiza" / "make.d").iterdir())
        assert "rust.mk" in fragments
        assert "python.mk" not in fragments

    def test_no_symlinks_in_synced_project(self):
        """Synced files are real files, as a downstream project would receive them."""
        for path in self.project.rglob("*"):
            if path.is_file():
                assert not path.is_symlink(), f"Unexpected symlink in synced project: {path.relative_to(self.project)}"


class TestRustBumpversionConfig:
    """The Rust `.rhiza/.cfg.toml` must rewrite the crate version and nothing else.

    This is the subtlest file rust-core ships. bump-my-version applies ``search`` to
    *every* occurrence in a file, so the config anchors its pattern to the
    ``[package]`` table — otherwise a dependency that happens to be pinned at the
    same version as the crate gets silently rewritten too, and the release lands a
    broken dependency spec. The comments in the file say so; this test proves it, by
    running the config's own regex the way bump-my-version does.
    """

    CURRENT = "1.2.3"
    NEW = "1.3.0"

    CARGO_TOML = """\
[package]
name = "demo"
version = "1.2.3"
edition = "2024"

[dependencies]
serde = "1.2.3"

[dependencies.tracing]
version = "1.2.3"
features = ["std"]
"""

    @pytest.fixture(autouse=True)
    def config(self, tmp_path, root):
        """Sync rust-core and load its bump-my-version configuration."""
        sync_bundles(root, ["core", "rust-core"], tmp_path)
        with (tmp_path / ".rhiza" / ".cfg.toml").open("rb") as fh:
            self.cfg = tomllib.load(fh)["tool"]["bumpversion"]
        self.project = tmp_path

    def _bump(self) -> str:
        """Apply the configured search/replace to CARGO_TOML exactly as bump-my-version would."""
        spec = self.cfg["files"][0]
        assert spec["filename"] == "Cargo.toml"
        assert spec.get("regex") is True, "the [package] anchor is a regex; without regex=true it is a literal"
        search = spec["search"].format(current_version=self.CURRENT)
        replace = spec["replace"].format(new_version=self.NEW)
        return re.sub(search, replace, self.CARGO_TOML)

    def test_the_crate_version_is_bumped(self):
        """The [package] version — the one the release is about — must change."""
        result = self._bump()
        assert f'[package]\nname = "demo"\nversion = "{self.NEW}"' in result

    def test_a_dependency_pinned_at_the_same_version_is_untouched(self):
        """The anchor exists for exactly this case; an unanchored search would rewrite it."""
        result = self._bump()
        assert 'serde = "1.2.3"' in result, "a shorthand dependency pin was rewritten"
        assert f'[dependencies.tracing]\nversion = "{self.CURRENT}"' in result, (
            "the version key of a [dependencies.*] table was rewritten — the [package] anchor is not holding"
        )

    def test_exactly_one_version_line_changes(self):
        """Belt and braces: one occurrence of the new version, wherever the anchor matched."""
        assert self._bump().count(f'"{self.NEW}"') == 1

    def test_cargo_lock_is_refreshed_by_hook_not_by_search_replace(self):
        """Cargo.lock lists every dependency's version, so it must never be a `files` entry."""
        filenames = [f["filename"] for f in self.cfg["files"]]
        assert "Cargo.lock" not in filenames, (
            "Cargo.lock records dependency versions too; a search/replace entry would rewrite any "
            "dependency pinned at the crate's version. Refresh it with `cargo update` instead."
        )
        hooks = " ".join(self.cfg.get("pre_commit_hooks", []))
        assert "cargo update" in hooks, "nothing refreshes Cargo.lock, so the bumped tree dirties itself"
        assert "git add Cargo.lock" in hooks, "the refreshed lockfile is never staged into the bump commit"

    def test_prerelease_parts_are_semver_spellings(self):
        """Cargo rejects PEP 440 short forms like `1.2.3-a.1`, so the values are spelled out."""
        values = self.cfg["parts"]["release"]["values"]
        assert "alpha" in values
        assert "a" not in values


class TestProfileRustLocalSync:
    """Syncing the 'rust-local' profile yields a Rust project with no hosted CI."""

    RUST_LOCAL_BUNDLES = ["core", "rust-core", "book"]  # transitive closure of the 'rust-local' profile

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync all bundles in the rust-local profile transitive closure."""
        sync_bundles(root, self.RUST_LOCAL_BUNDLES, tmp_path)
        self.project = tmp_path

    def test_the_language_contract_is_available(self):
        """`install` and `all` exist, which is what makes the profile usable at all."""
        rust_mk = (self.project / ".rhiza" / "make.d" / "rust.mk").read_text(encoding="utf-8")
        assert "install:" in rust_mk
        assert "all:" in rust_mk

    def test_docs_skeleton_exists(self):
        """The book bundle is language-neutral, so a Rust project gets docs too."""
        assert (self.project / "docs" / "index.md").is_file()
        assert (self.project / "docs" / "mkdocs-base.yml").is_file()

    def test_book_badge_step_and_rust_coverage_agree_on_the_report_path(self):
        """book.mk badges `_tests/coverage.xml`; the Rust `coverage` target must write it."""
        book_mk = (self.project / ".rhiza" / "make.d" / "book.mk").read_text(encoding="utf-8")
        rust_mk = (self.project / ".rhiza" / "make.d" / "rust.mk").read_text(encoding="utf-8")
        assert "_tests/coverage.xml" in book_mk
        assert "_tests/coverage.xml" in rust_mk

    def test_no_github_workflows_injected(self):
        """rust-local is local-first: the Rust CI workflows do not exist yet."""
        workflows_dir = self.project / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml"))
            assert not workflow_files, (
                f"rust-local should not inject workflow files, found: {[f.name for f in workflow_files]}"
            )

    def test_no_gitlab_ci_injected(self):
        """Nor the GitLab half of hosted CI."""
        assert not (self.project / ".gitlab-ci.yml").exists()

    def test_exactly_one_pre_commit_config(self):
        """Two layers would fight over this path; the profile selects exactly one."""
        configs = list(self.project.rglob(".pre-commit-config.yaml"))
        assert len(configs) == 1, f"expected one .pre-commit-config.yaml, found {configs}"
        with configs[0].open(encoding="utf-8") as fh:
            hook_ids = {hook["id"] for repo in yaml.safe_load(fh)["repos"] for hook in repo["hooks"]}
        assert "cargo-clippy" in hook_ids, "the synced pre-commit config is not the Rust one"
        assert not hook_ids & {"ruff", "bandit", "interrogate", "uv-lock"}, (
            "python-core's hooks leaked into a Rust profile"
        )


class TestCoreAndTestsBundleSync:
    """Syncing core + tests bundles adds pytest infrastructure."""

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync core and tests bundles into a fresh directory."""
        sync_bundles(root, ["core", "tests"], tmp_path)
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
