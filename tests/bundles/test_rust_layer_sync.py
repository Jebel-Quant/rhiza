"""What a project syncing the Rust layer actually receives.

Split from ``test_bundle_sync.py`` in #1514. Covers the ``rust-core`` bundle's file set,
the ``.bumpversion.toml`` it ships (which deliberately omits ``current_version`` — see the
release-config discussion in CLAUDE.md), and the ``rust-local`` profile assembled from it.
"""

from __future__ import annotations

import functools
import re
import subprocess  # nosec B404
import tomllib
from pathlib import Path

import pytest
import yaml

from tests.util import sync_bundles


@functools.lru_cache(maxsize=1)
def _cli_task_sources() -> str:
    """Return the concatenated source of the pinned CLI's modules.

    Returns:
        The text, or "" when the CLI cannot be reached.
    """
    root = Path(__file__).resolve().parents[2]
    match = re.search(r"^RHIZA_TASK \?= (\S+)", (root / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        return ""
    name, _, version = match.group(1).partition("@")
    proc = subprocess.run(  # nosec B603
        [
            "uv",
            "run",
            "--quiet",
            "--no-project",
            "--with",
            f"{name}=={version}" if version else name,
            "python",
            "-c",
            "import pathlib, rhiza_task;"
            "print('\\n'.join(p.read_text() for p in pathlib.Path(rhiza_task.__file__).parent.rglob('*.py')))",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else ""


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

    def test_the_semgrep_config_arrives_without_a_python_bundle(self):
        """`make semgrep` must be runnable on a Rust project (#1475).

        The config moved from the `tests` bundle to `core` because `quality.mk` — core's —
        is what names it. Before that a Rust sync got the target and not the file.
        """
        assert (self.project / ".rhiza" / "semgrep.yml").is_file(), (
            "core's semgrep target has no config on a Rust project"
        )

    def test_no_language_fragment_is_synced_at_all(self):
        """A language layer must ship no make fragment, so two layers cannot collide through one.

        This guarded the original clash: ``python.mk``, ``rust.mk`` and ``go.mk`` each defined
        ``install``, so receiving two meant two recipes for one target and no way to know which
        ran. The gates moved to rhiza-task, where the layer is part of the registry key
        (``rust:install``) and the collision is structurally impossible.

        The layers *do* still claim overlapping paths on purpose -- ``.pre-commit-config.yaml``
        in all three, ``.bumpversion.toml`` in the two non-Python ones -- so "one layer per repo"
        is still enforced, just by those files rather than by these.

        This also replaces the companion test that listed the target names the fragment had to
        define, and that it must not redefine ``rhiza-test``. Both are the registry's business
        now: ``test_layer_contract.py`` asserts the gate names for all three layers at once, and
        the layer key makes a duplicate impossible rather than merely forbidden. Asserted as an
        absence so a fragment cannot quietly return and reintroduce the ambiguity.
        """
        make_d = self.project / ".rhiza" / "make.d"
        stale = sorted(f.name for f in make_d.rglob("*.mk")) if make_d.is_dir() else []
        assert not stale, f"rust-core ships make fragments again: {stale}"

    def test_no_symlinks_in_synced_project(self):
        """Synced files are real files, as a downstream project would receive them."""
        for path in self.project.rglob("*"):
            if path.is_file():
                assert not path.is_symlink(), f"Unexpected symlink in synced project: {path.relative_to(self.project)}"


class TestRustBumpversionConfig:
    """The Rust `.bumpversion.toml` must rewrite the crate version and nothing else.

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
        with (tmp_path / ".bumpversion.toml").open("rb") as fh:
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

    def test_the_profile_ships_no_make_fragment(self):
        """The profile must not deliver a language fragment.

        This asserted that ``rust.mk`` defined ``install`` and ``all`` -- the contract that makes
        the profile usable. That contract is the task registry's now, and
        ``test_layer_contract.py`` asserts it for all three layers at once against the registry
        itself, which is a stronger check than grepping one file for two strings. What is worth
        keeping here is the negative: the profile must not ship a fragment that would shadow it.
        """
        make_d = self.project / ".rhiza" / "make.d"
        stale = sorted(f.name for f in make_d.rglob("*.mk")) if make_d.is_dir() else []
        assert not stale, f"the profile ships make fragments again: {stale}"

    def test_docs_skeleton_exists(self):
        """The book bundle is language-neutral, so a Rust project gets docs too."""
        assert (self.project / "docs" / "index.md").is_file()
        assert (self.project / "docs" / "mkdocs-base.yml").is_file()

    def test_book_badge_step_and_rust_coverage_agree_on_the_report_path(self):
        """The book's badge step and the Rust `coverage` task must name one path.

        Worth keeping through the migration: two independent pieces have to agree on
        ``_tests/coverage.xml``, and nothing fails loudly when they stop -- the badge just renders
        "unknown" against a report that was written elsewhere. Both halves used to be make
        fragments; both are rhiza-task tasks now, so the assertion reads the CLI's own source
        rather than files that no longer ship.
        """
        source = _cli_task_sources()
        if not source:
            pytest.skip("could not read the rhiza-task task sources")
        assert source.count("_tests/coverage.xml") >= 2, (
            "the coverage report path appears fewer than twice in rhiza-task's tasks, so the book "
            "badge step and the coverage task may no longer agree on where the report lands"
        )

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
