"""What a project syncing the Go layer actually receives.

Split from ``test_bundle_sync.py`` in #1514. Covers the ``go-core`` bundle's file set —
including the starter ``internal/version/version.go`` and its test, which exist because
``go mod init`` writes no Go file and ``go test`` exits 0 on a package with none — the
``.bumpversion.toml`` anchored to that version constant, and the ``go-local`` profile.
"""

from __future__ import annotations

import tomllib

import pytest
import yaml

from tests.util import sync_bundles


class TestGoCoreBundleSync:
    """Syncing core + go-core produces a working Go project layer.

    Like rust-core, nothing here is dogfooded at the root — and unlike rust-core,
    there is no Go toolchain in this environment at all, so these file-level
    assertions are the whole safety net.
    """

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync the core and go-core bundles into a fresh directory."""
        sync_bundles(root, ["core", "go-core"], tmp_path)
        self.project = tmp_path

    @pytest.mark.parametrize("name", [".golangci.yml", "revive.toml", ".pre-commit-config.yaml"])
    def test_go_toolchain_config_is_present(self, name):
        """The Go-side counterparts of ruff.toml/clippy.toml all arrive."""
        assert (self.project / name).is_file(), f"Missing Go toolchain file: {name}"

    @pytest.mark.parametrize("name", ["ruff.toml", ".bandit", ".python-version", "clippy.toml", "deny.toml"])
    def test_sibling_layer_config_is_absent(self, name):
        """A Go repo gets neither the Python nor the Rust toolchain — layers are alternatives."""
        assert not (self.project / name).exists(), f"{name} belongs to another language layer"

    def test_the_semgrep_config_arrives_without_a_python_bundle(self):
        """`make semgrep` must be runnable on a Go project (#1475).

        The config moved from the `tests` bundle to `core` because `quality.mk` — core's —
        is what names it. Before that a Go sync got the target and not the file.
        """
        assert (self.project / ".rhiza" / "semgrep.yml").is_file(), (
            "core's semgrep target has no config on a Go project"
        )

    def test_go_mk_provides_the_language_contract(self):
        """go.mk owns the same target names its siblings do, plus the go-backed gates.

        ``rhiza-test`` is deliberately absent: its recipe is language-neutral, so it moved
        to core's quality.mk in #1471 rather than existing identically in all three layers.
        """
        go_mk = (self.project / ".rhiza" / "make.d" / "go.mk").read_text(encoding="utf-8")
        for target in ("install:", "all:", "test::", "coverage:", "typecheck:", "docs-coverage:"):
            assert target in go_mk, f"go.mk is missing {target}"
        assert "rhiza-test:" not in go_mk, (
            "go.mk redefines rhiza-test, which core now owns — two recipes for one "
            "target name is exactly what #1471 removed"
        )

    def test_only_one_language_fragment_is_synced(self):
        """python.mk, rust.mk and go.mk all define `install` — receiving two would be a clash."""
        fragments = sorted(p.name for p in (self.project / ".rhiza" / "make.d").iterdir())
        assert "go.mk" in fragments
        assert "python.mk" not in fragments
        assert "rust.mk" not in fragments

    def test_the_version_constant_ships_with_the_layer(self):
        """Unlike Cargo.toml, this file does not exist in a Go project unless rhiza puts it there."""
        version_go = self.project / "internal" / "version" / "version.go"
        assert version_go.is_file(), (
            "go-core must ship internal/version/version.go — a Go module has no manifest, so "
            "without it the release flow has no version location to write to"
        )
        source = version_go.read_text(encoding="utf-8")
        assert source.startswith("// Package version"), "the package doc comment the docs-coverage gate requires"
        assert 'const Version = "0.0.0"' in source

    def test_the_layer_ships_a_test_so_the_test_gate_is_not_vacuous(self):
        """`go test ./...` exits 0 on a package with no test file, printing "[no test files]".

        So a freshly synced Go project passed `make test` — and `make all` — while
        running nothing at all. Rust never had this hole: `cargo init --lib` leaves an
        `it_works` test behind, while `go mod init` writes no Go file whatsoever, so
        the layer has to bring the first test itself.
        """
        version_test = self.project / "internal" / "version" / "version_test.go"
        assert version_test.is_file(), (
            "go-core must ship internal/version/version_test.go — without a single test "
            "file a fresh Go repo's `make test` is green without testing anything"
        )
        source = version_test.read_text(encoding="utf-8")
        assert "func Test" in source, "the file ships no test function, so it does not close the vacuum"

        # Comments are stripped before the literal check: the file explains in prose why
        # it does not compare against "0.0.0", and matching that would fail the test for
        # documenting the very trap it avoids.
        code = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("//"))
        assert '"0.0.0"' not in code, (
            "the test must not compare against the literal shipped version: bump-my-version "
            "rewrites version.go and not this file, so a literal turns red on the first release"
        )

    def test_no_symlinks_in_synced_project(self):
        """Synced files are real files, as a downstream project would receive them."""
        for path in self.project.rglob("*"):
            if path.is_file():
                assert not path.is_symlink(), f"Unexpected symlink in synced project: {path.relative_to(self.project)}"


class TestGoBumpversionConfig:
    """The Go `.bumpversion.toml` must write the one version location a Go module has.

    Go is the odd layer out: pyproject.toml and Cargo.toml carry a version, a Go
    module does not — its version is the git tag. The layer ships a `Version`
    constant to serve as that location, so this checks the release config and the
    shipped file agree, by running the config's own search the way bump-my-version
    does. A rename on either side breaks the release with `ignore_missing_files
    = false`, and this is what catches it first.
    """

    CURRENT = "1.2.3"
    NEW = "1.3.0"

    @pytest.fixture(autouse=True)
    def config(self, tmp_path, root):
        """Sync go-core and load its bump-my-version configuration."""
        sync_bundles(root, ["core", "go-core"], tmp_path)
        with (tmp_path / ".bumpversion.toml").open("rb") as fh:
            self.cfg = tomllib.load(fh)["tool"]["bumpversion"]
        self.project = tmp_path

    def test_the_configured_file_is_the_file_the_bundle_ships(self):
        """`ignore_missing_files = false`, so a path typo fails the release, not a test."""
        assert self.cfg["ignore_missing_files"] is False
        filenames = [f["filename"] for f in self.cfg["files"]]
        assert filenames == ["internal/version/version.go"]
        assert (self.project / filenames[0]).is_file(), "the config points at a file the layer does not ship"

    def test_the_search_matches_the_shipped_constant(self):
        """The declaration in version.go and the pattern in .bumpversion.toml must stay in step."""
        spec = self.cfg["files"][0]
        source = (self.project / spec["filename"]).read_text(encoding="utf-8")
        # Version numbers are literal here; substitute the shipped 0.0.0 to match.
        assert spec["search"].format(current_version="0.0.0") in source, (
            "the bump-my-version search does not match the constant in version.go — "
            "the release would fail with 'did not find current version'"
        )

    def test_a_version_in_prose_is_not_rewritten(self):
        """Anchoring on `const Version =` is what keeps a doc comment or example safe."""
        spec = self.cfg["files"][0]
        search = spec["search"].format(current_version=self.CURRENT)
        replace = spec["replace"].format(new_version=self.NEW)
        source = f'// Version was {self.CURRENT} in the last release.\nconst Version = "{self.CURRENT}"\n'
        result = source.replace(search, replace)
        assert f"// Version was {self.CURRENT} in the last release." in result
        assert f'const Version = "{self.NEW}"' in result

    def test_no_lockfile_hook_is_needed(self):
        """go.sum records dependency checksums only, so there is nothing to refresh."""
        assert not self.cfg.get("pre_commit_hooks"), (
            "the Go layer needs no post-bump hook; go.sum never records the module's own version"
        )

    def test_the_tag_is_the_semver_go_expects(self):
        """Go resolves module versions from `vX.Y.Z` tags, and rejects PEP 440 short forms."""
        assert self.cfg["tag_name"] == "v{new_version}"
        values = self.cfg["parts"]["release"]["values"]
        assert "alpha" in values
        assert "a" not in values


class TestProfileGoLocalSync:
    """Syncing the 'go-local' profile yields a Go project with no hosted CI."""

    GO_LOCAL_BUNDLES = ["core", "go-core", "book"]  # transitive closure of the 'go-local' profile

    @pytest.fixture(autouse=True)
    def synced(self, tmp_path, root):
        """Sync all bundles in the go-local profile transitive closure."""
        sync_bundles(root, self.GO_LOCAL_BUNDLES, tmp_path)
        self.project = tmp_path

    def test_the_language_contract_is_available(self):
        """`install` and `all` exist, which is what makes the profile usable at all."""
        go_mk = (self.project / ".rhiza" / "make.d" / "go.mk").read_text(encoding="utf-8")
        assert "install:" in go_mk
        assert "all:" in go_mk

    def test_docs_skeleton_exists(self):
        """The book bundle is language-neutral, so a Go project gets docs too."""
        assert (self.project / "docs" / "index.md").is_file()
        assert (self.project / "docs" / "mkdocs-base.yml").is_file()

    def test_book_badge_step_and_go_coverage_agree_on_the_report_path(self):
        """book.mk badges `_tests/coverage.xml`; the Go `coverage` target must write it."""
        book_mk = (self.project / ".rhiza" / "make.d" / "book.mk").read_text(encoding="utf-8")
        go_mk = (self.project / ".rhiza" / "make.d" / "go.mk").read_text(encoding="utf-8")
        assert "_tests/coverage.xml" in book_mk
        assert "_tests/coverage.xml" in go_mk

    def test_no_github_workflows_injected(self):
        """go-local is local-first: the Go CI workflows do not exist yet."""
        workflows_dir = self.project / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml"))
            assert not workflow_files, (
                f"go-local should not inject workflow files, found: {[f.name for f in workflow_files]}"
            )

    def test_no_gitlab_ci_injected(self):
        """Nor the GitLab half of hosted CI."""
        assert not (self.project / ".gitlab-ci.yml").exists()

    def test_exactly_one_pre_commit_config(self):
        """Three layers now claim this path; the profile selects exactly one."""
        configs = list(self.project.rglob(".pre-commit-config.yaml"))
        assert len(configs) == 1, f"expected one .pre-commit-config.yaml, found {configs}"
        with configs[0].open(encoding="utf-8") as fh:
            hook_ids = {hook["id"] for repo in yaml.safe_load(fh)["repos"] for hook in repo["hooks"]}
        assert "go-mod-tidy" in hook_ids, "the synced pre-commit config is not the Go one"
        assert not hook_ids & {"ruff", "bandit", "interrogate", "uv-lock", "cargo-clippy"}, (
            "a sibling layer's hooks leaked into a Go profile"
        )
