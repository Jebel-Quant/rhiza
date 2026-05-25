"""Integration tests for the bundle-centric directory layout.

Simulates what rhiza-cli does: resolves a set of bundle names, copies the
files (following symlinks to get real content) into a fresh directory, and
asserts that the resulting project looks exactly as expected.

Each test starts from a green-field temporary directory, so there is no
shared state between scenarios.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Sync helper (minimal stand-in for rhiza-cli bundle resolution)
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
    symlinks are copied as whole resolved trees (matching what a real sync
    would do) and file symlinks have their real content copied.
    """
    for name in bundle_names:
        bundle_dir = root / "bundles" / name
        if not bundle_dir.is_dir():
            pytest.fail(f"Bundle directory does not exist: bundles/{name}")

        for dirpath, dirs, files in os.walk(bundle_dir, followlinks=False):
            current = Path(dirpath)

            # Symlinked sub-directories: copy as whole resolved tree, skip recursion
            for d in dirs[:]:
                child = current / d
                if child.is_symlink():
                    dirs.remove(d)
                    _copy_entry(child, dest / child.relative_to(bundle_dir))

            # Files (plain or symlinks)
            for f in files:
                child = current / f
                _copy_entry(child, dest / child.relative_to(bundle_dir))


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
        for name in ("bootstrap.mk", "quality.mk", "releasing.mk", "custom-env.mk", "custom-task.mk"):
            assert (make_d / name).is_file(), f"Missing make.d fragment: {name}"

    def test_ruff_config_exists(self):
        """Ruff linting configuration is present."""
        assert (self.project / "ruff.toml").is_file()

    def test_docs_skeleton_exists(self):
        """Base documentation files are present."""
        assert (self.project / "docs" / "index.md").is_file()
        assert (self.project / "docs" / "mkdocs-base.yml").is_file()

    def test_no_symlinks_in_synced_project(self):
        """Synced files are real files, not symlinks — as a downstream project would receive."""
        for path in self.project.rglob("*"):
            if path.is_file():
                assert not path.is_symlink(), f"Unexpected symlink in synced project: {path.relative_to(self.project)}"


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

    def test_sync_workflow_exists(self):
        """Sync workflow stub is injected."""
        assert (self.project / ".github" / "workflows" / "rhiza_sync.yml").is_file()

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

    def test_no_github_workflows_injected(self):
        """Local profile must not produce any .github/workflows/ files."""
        workflows_dir = self.project / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml"))
            assert not workflow_files, (
                f"Local profile should not inject workflow files, found: {[f.name for f in workflow_files]}"
            )
