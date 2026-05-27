"""Tests for downstream-project sync invariants.

Validates that the bundle layout guarantees a downstream project receives a
coherent, self-consistent set of files — regardless of which profile they chose.

These tests exercise the sync logic itself (not just the bundle structure) by
actually copying bundle files into a temporary directory and asserting on the
resulting filesystem state.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404
from pathlib import Path

import pytest
import yaml

# Get absolute paths for executables to avoid S607 warnings
GIT = shutil.which("git") or "/usr/bin/git"
MAKE = shutil.which("make") or "/usr/bin/make"

# ---------------------------------------------------------------------------
# Sync helper (mirrors tests/bundles/test_bundle_sync.py — kept local)
# ---------------------------------------------------------------------------


def _copy_entry(src: Path, dest: Path) -> None:
    """Copy src into dest, resolving any symlink to get the real content."""
    real = src.resolve() if src.is_symlink() else src
    dest.parent.mkdir(parents=True, exist_ok=True)
    if real.is_dir():
        shutil.copytree(real, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(real, dest)


def sync_bundles(bundles_root: Path, bundle_names: list[str], dest: Path) -> None:
    """Copy all files from the named bundles into dest."""
    for name in bundle_names:
        bundle_dir = bundles_root / name
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


@pytest.fixture(scope="module")
def bundles_root(root: Path) -> Path:
    """Return the bundles/ directory."""
    return root / "bundles"


# ---------------------------------------------------------------------------
# Cross-platform isolation: GitHub and GitLab bundles must not bleed
# ---------------------------------------------------------------------------


class TestPlatformIsolation:
    """GitHub and GitLab bundle files must not co-mingle in a single project."""

    def test_gitlab_project_profile_has_no_github_workflows(self, bundles_root: Path, tmp_path: Path) -> None:
        """GitLab-project profile sync must produce zero .github/workflows/*.yml files."""
        gitlab_bundles = ["core", "book", "marimo", "tests", "gitlab", "gitlab-book", "gitlab-marimo", "gitlab-tests"]
        sync_bundles(bundles_root, gitlab_bundles, tmp_path)

        workflows_dir = tmp_path / ".github" / "workflows"
        if workflows_dir.exists():
            yml_files = list(workflows_dir.glob("*.yml"))
            assert not yml_files, (
                f"GitLab-project profile produced GitHub workflow files: {[f.name for f in yml_files]}"
            )

    def test_github_project_profile_has_no_gitlab_ci(self, bundles_root: Path, tmp_path: Path) -> None:
        """GitHub-project profile sync must not produce a .gitlab-ci.yml file."""
        github_bundles = ["core", "book", "marimo", "tests", "github", "github-book", "github-marimo", "github-tests"]
        sync_bundles(bundles_root, github_bundles, tmp_path)

        assert not (tmp_path / ".gitlab-ci.yml").is_file(), "GitHub-project profile should not produce .gitlab-ci.yml"

    def test_local_profile_has_no_ci_workflows(self, bundles_root: Path, tmp_path: Path) -> None:
        """Local profile sync must produce no CI workflow files at all."""
        local_bundles = ["core", "book", "marimo", "tests"]
        sync_bundles(bundles_root, local_bundles, tmp_path)

        github_wf = tmp_path / ".github" / "workflows"
        gitlab_wf = tmp_path / ".gitlab" / "workflows"

        github_files = list(github_wf.glob("*.yml")) if github_wf.exists() else []
        gitlab_files = list(gitlab_wf.glob("*.yml")) if gitlab_wf.exists() else []

        assert not github_files, f"Local profile injected GitHub workflows: {[f.name for f in github_files]}"
        assert not gitlab_files, f"Local profile injected GitLab workflows: {[f.name for f in gitlab_files]}"


# ---------------------------------------------------------------------------
# File idempotency: syncing the same bundle twice must not break the project
# ---------------------------------------------------------------------------


class TestSyncIdempotency:
    """Syncing the same bundles twice must produce identical results."""

    def test_double_sync_is_idempotent(self, bundles_root: Path, tmp_path: Path) -> None:
        """Syncing core + tests twice must produce the same set of files."""
        dest1 = tmp_path / "first"
        dest2 = tmp_path / "second"

        sync_bundles(bundles_root, ["core", "tests"], dest1)
        sync_bundles(bundles_root, ["core", "tests"], dest2)

        # Sync again into dest1 (simulate re-sync)
        sync_bundles(bundles_root, ["core", "tests"], dest1)

        files1 = {p.relative_to(dest1) for p in dest1.rglob("*") if p.is_file()}
        files2 = {p.relative_to(dest2) for p in dest2.rglob("*") if p.is_file()}

        only_first = files1 - files2
        only_second = files2 - files1
        assert files1 == files2, (
            f"Double-sync produced different files.\nOnly in first: {only_first}\nOnly in second: {only_second}"
        )


# ---------------------------------------------------------------------------
# Core bundle invariants regardless of profile
# ---------------------------------------------------------------------------


class TestCoreInvariantsAcrossProfiles:
    """Every profile sync includes core infrastructure files."""

    PROFILES = {
        "local": ["core", "book", "marimo", "tests"],
        "github-project": ["core", "book", "marimo", "tests", "github", "github-book", "github-marimo", "github-tests"],
        "gitlab-project": ["core", "book", "marimo", "tests", "gitlab", "gitlab-book", "gitlab-marimo", "gitlab-tests"],
    }

    @pytest.mark.parametrize(("profile", "bundles"), list(PROFILES.items()))
    def test_makefile_present_in_all_profiles(
        self, profile: str, bundles: list[str], bundles_root: Path, tmp_path: Path
    ) -> None:
        """Every profile sync must produce a root Makefile."""
        dest = tmp_path / profile
        sync_bundles(bundles_root, bundles, dest)
        assert (dest / "Makefile").is_file(), f"Profile '{profile}': Makefile not found"

    @pytest.mark.parametrize(("profile", "bundles"), list(PROFILES.items()))
    def test_rhiza_mk_present_in_all_profiles(
        self, profile: str, bundles: list[str], bundles_root: Path, tmp_path: Path
    ) -> None:
        """Every profile sync must produce the core .rhiza/rhiza.mk file."""
        dest = tmp_path / profile
        sync_bundles(bundles_root, bundles, dest)
        assert (dest / ".rhiza" / "rhiza.mk").is_file(), f"Profile '{profile}': .rhiza/rhiza.mk not found"

    @pytest.mark.parametrize(("profile", "bundles"), list(PROFILES.items()))
    def test_no_symlinks_in_any_profile(
        self, profile: str, bundles: list[str], bundles_root: Path, tmp_path: Path
    ) -> None:
        """Synced files must be real files — no symlinks should survive the copy."""
        dest = tmp_path / profile
        sync_bundles(bundles_root, bundles, dest)
        symlinks = [p for p in dest.rglob("*") if p.is_symlink()]
        assert not symlinks, f"Profile '{profile}': unexpected symlinks after sync: " + ", ".join(
            str(s.relative_to(dest)) for s in symlinks
        )


# ---------------------------------------------------------------------------
# Workflow stub content after sync
# ---------------------------------------------------------------------------


class TestWorkflowStubsAfterSync:
    """Workflow stubs must contain correct content once copied to a downstream project."""

    @pytest.fixture(autouse=True)
    def synced_github_project(self, bundles_root: Path, tmp_path: Path) -> None:
        """Sync the full github-project closure into a fresh temp directory."""
        bundles = ["core", "book", "marimo", "tests", "github", "github-book", "github-marimo", "github-tests"]
        sync_bundles(bundles_root, bundles, tmp_path)
        self.project = tmp_path

    def test_ci_stub_delegates_to_shared_workflow(self) -> None:
        """rhiza_ci.yml stub must delegate to the shared reusable workflow."""
        ci_yml = self.project / ".github" / "workflows" / "rhiza_ci.yml"
        if not ci_yml.exists():
            pytest.skip("rhiza_ci.yml not found after sync")
        content = ci_yml.read_text(encoding="utf-8")
        assert "uses: jebel-quant/rhiza/.github/workflows/rhiza_ci.yml" in content, (
            "CI stub must delegate to jebel-quant/rhiza shared CI workflow"
        )

    def test_all_synced_workflows_are_valid_yaml(self) -> None:
        """Every workflow file in the synced project must parse as valid YAML.

        Note: pyyaml parses the 'on:' trigger key as Python boolean True — this is
        expected and correct behaviour; it does not indicate a parse failure.
        """
        workflows_dir = self.project / ".github" / "workflows"
        errors: list[str] = []
        for wf in workflows_dir.glob("*.yml"):
            try:
                with wf.open(encoding="utf-8") as fh:
                    yaml.safe_load(fh)
            except yaml.YAMLError as exc:
                errors.append(f"  {wf.name}: {exc}")
        if errors:
            pytest.fail("YAML errors in synced workflows:\n" + "\n".join(errors))

    def test_book_stub_delegates_to_shared_workflow(self) -> None:
        """rhiza_book.yml stub must delegate to the shared reusable book workflow."""
        book_yml = self.project / ".github" / "workflows" / "rhiza_book.yml"
        if not book_yml.exists():
            pytest.skip("rhiza_book.yml not found after sync")
        content = book_yml.read_text(encoding="utf-8")
        assert "uses: jebel-quant/rhiza/.github/workflows/rhiza_book.yml" in content, (
            "Book stub must delegate to jebel-quant/rhiza shared book workflow"
        )


class TestDownstreamRepoEndToEndSync:
    """End-to-end sync against a minimal downstream repository."""

    @staticmethod
    def _init_minimal_downstream_repo(root: Path, downstream: Path) -> None:
        """Create a minimal downstream repo that can run make sync."""
        (downstream / ".rhiza" / "make.d").mkdir(parents=True, exist_ok=True)

        shutil.copy2(root / "Makefile", downstream / "Makefile")
        shutil.copy2(root / ".rhiza" / "rhiza.mk", downstream / ".rhiza" / "rhiza.mk")
        shutil.copy2(root / ".rhiza" / ".rhiza-version", downstream / ".rhiza" / ".rhiza-version")
        shutil.copy2(root / ".rhiza" / "make.d" / "bootstrap.mk", downstream / ".rhiza" / "make.d" / "bootstrap.mk")

        (downstream / ".rhiza" / "template.yml").write_text(
            "repository: jebel-quant/rhiza\nref: main\ntemplates:\n  - core\n  - tests\n",
            encoding="utf-8",
        )
        (downstream / "pyproject.toml").write_text(
            '[project]\nname = "downstream-test-project"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )

        subprocess.run([GIT, "init"], cwd=downstream, check=True, capture_output=True)  # nosec B603
        subprocess.run(
            [GIT, "config", "user.email", "test@example.com"], cwd=downstream, check=True, capture_output=True
        )  # nosec B603
        subprocess.run([GIT, "config", "user.name", "Rhiza Tests"], cwd=downstream, check=True, capture_output=True)  # nosec B603
        subprocess.run(  # nosec B603
            [GIT, "remote", "add", "origin", "https://example.com/acme/downstream.git"],
            cwd=downstream,
            check=True,
            capture_output=True,
        )
        subprocess.run([GIT, "add", "."], cwd=downstream, check=True, capture_output=True)  # nosec B603
        subprocess.run(
            [GIT, "commit", "-m", "initial downstream scaffold"], cwd=downstream, check=True, capture_output=True
        )  # nosec B603

    def test_sync_populates_expected_files(self, root: Path, tmp_path: Path) -> None:
        """Sync should produce a functional core+tests downstream tree."""
        self._init_minimal_downstream_repo(root, tmp_path)

        proc = subprocess.run(  # nosec B603
            [MAKE, "sync"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert proc.returncode == 0, f"make sync failed\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        assert (tmp_path / "pytest.ini").is_file()
        assert (tmp_path / ".rhiza" / "tests" / "conftest.py").is_file()
        assert (tmp_path / ".rhiza" / "make.d" / "test.mk").is_file()

        pytest_ini = (tmp_path / "pytest.ini").read_text(encoding="utf-8")
        makefile = (tmp_path / "Makefile").read_text(encoding="utf-8")
        assert "testpaths" in pytest_ini
        assert "include .rhiza/rhiza.mk" in makefile
