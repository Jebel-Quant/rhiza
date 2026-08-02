"""The language-layer contract: what `core` promises, and what a layer must supply.

`core` used to be a Python project in disguise — it created a virtualenv, ran
`uv sync`, and named Python gates in `all`. Splitting it left `core` with the make
framework and uv-as-a-tool-runner, and moved everything language-specific into a
layer bundle: `python-core`, which ships `.rhiza/make.d/python.mk`.

The contract that makes a second language possible is a set of **target names**.
`book.mk`, `test.mk` and the CI workflows call `make install` without knowing what
the project is written in, so every language layer must define the same names with
its own recipes. These tests pin both halves: that core alone does *not* define
them, and that the Python layer does — behaviourally, by expanding the recipes.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.util import run_make, setup_rhiza_git_repo, strip_ansi

# The names every language layer owns. Adding a name here is a promise a future
# `rust-core` must also keep.
LANGUAGE_LAYER_TARGETS = ("install", "all")


class TestPythonLayerProvidesTheContract:
    """The `python-core` layer defines the target names the rest of the template calls."""

    def test_the_layer_ships_exactly_one_make_fragment(self, root: Path):
        """One fragment per layer keeps `rust.mk` from colliding with `python.mk`."""
        fragments = sorted((root / "bundles" / "python-core" / ".rhiza" / "make.d").iterdir())
        assert [f.name for f in fragments] == ["python.mk"]

    def test_install_creates_a_venv_and_syncs_the_project(self, logger):
        """`install` is Python's: a uv virtualenv plus a dependency sync."""
        out = strip_ansi(run_make(logger, ["install"]).stdout)
        assert "venv" in out
        assert "sync" in out

    def test_all_chains_the_python_gates(self, logger):
        """`all` names the per-language gate set, so it belongs to the layer."""
        out = strip_ansi(run_make(logger, ["all"]).stdout)
        assert "pre-commit run --all-files" in out  # fmt, from core
        assert "deptry" in out  # deptry, from the layer
        assert "pip-licenses" in out  # license, from the layer

    @pytest.mark.parametrize("target", LANGUAGE_LAYER_TARGETS)
    def test_every_contract_target_resolves(self, logger, target):
        """A missing layer target would surface as 'no rule to make target'."""
        proc = run_make(logger, [target])
        assert "no rule to make target" not in proc.stderr.lower()


class TestRustLayerKeepsTheSameContract:
    """`rust-core` is a peer of `python-core`, not a special case.

    The mother repo is a Python project, so the Rust layer cannot be dogfooded at the
    root — these assemble it into a temp dir instead. They deliberately do not invoke
    cargo: what matters here is that the layer *declares* the same contract, which is
    what lets book.mk and the CI workflows stay language-agnostic.
    """

    @pytest.fixture(autouse=True)
    def rust_project(self, root: Path, tmp_path: Path, monkeypatch):
        """Assemble core + rust-core into a project, standing in for a sync."""
        project = tmp_path / "rust-project"
        (project / ".rhiza" / "make.d").mkdir(parents=True)
        shutil.copy(root / "Makefile", project / "Makefile")
        shutil.copy(root / ".rhiza" / "rhiza.mk", project / ".rhiza" / "rhiza.mk")
        for fragment in (root / "bundles" / "core" / ".rhiza" / "make.d").iterdir():
            shutil.copy(fragment, project / ".rhiza" / "make.d" / fragment.name)
        shutil.copy(
            root / "bundles" / "rust-core" / ".rhiza" / "make.d" / "rust.mk",
            project / ".rhiza" / "make.d" / "rust.mk",
        )
        (project / "Cargo.toml").write_text('[package]\nname = "demo"\nversion = "0.1.0"\n')
        monkeypatch.chdir(project)
        setup_rhiza_git_repo()
        self.project = project

    @pytest.mark.parametrize("target", LANGUAGE_LAYER_TARGETS)
    def test_every_contract_target_resolves(self, logger, target):
        """The same names python-core provides, so callers need not branch."""
        proc = run_make(logger, [target], check=False)
        assert "no rule to make target" not in proc.stderr.lower()

    @pytest.mark.parametrize(
        ("target", "expected"),
        [
            ("typecheck", "clippy"),
            ("security", "deny check advisories"),
            ("license", "deny check licenses"),
            ("deps", "machete"),
            ("test", "nextest"),
        ],
    )
    def test_gate_maps_to_its_cargo_equivalent(self, logger, target, expected):
        """Each Python gate has a Rust counterpart under the same target name."""
        out = strip_ansi(run_make(logger, [target], check=False).stdout)
        assert expected in out, f"`make {target}` should run {expected}"

    def test_coverage_writes_the_report_book_mk_reads(self, logger):
        """book.mk badges `_tests/coverage.xml`; llvm-cov must write exactly that path."""
        out = strip_ansi(run_make(logger, ["coverage"], check=False).stdout)
        assert "_tests/coverage.xml" in out
        assert "--cobertura" in out

    def test_install_does_not_reach_for_uv_sync(self, logger):
        """A Rust `install` is rustup + cargo fetch; uv is only the tool runner."""
        out = strip_ansi(run_make(logger, ["install"], check=False).stdout)
        assert "cargo fetch" in out
        assert "uv sync" not in out


class TestCoreAloneHasNoLanguageLayer:
    """Without a layer, core is inert on exactly the targets a layer owns."""

    @pytest.fixture(autouse=True)
    def core_only(self, root: Path, tmp_path: Path, monkeypatch):
        """Assemble a project from core's fragments alone — no python.mk.

        Built in a subdirectory because the module-wide fixture in conftest.py has
        already laid out a *full* project in ``tmp_path``, python.mk included — which
        is precisely what this class must not have.
        """
        project = tmp_path / "core-only"
        (project / ".rhiza" / "make.d").mkdir(parents=True)
        shutil.copy(root / "Makefile", project / "Makefile")
        shutil.copy(root / ".rhiza" / "rhiza.mk", project / ".rhiza" / "rhiza.mk")
        for fragment in (root / "bundles" / "core" / ".rhiza" / "make.d").iterdir():
            shutil.copy(fragment, project / ".rhiza" / "make.d" / fragment.name)
        monkeypatch.chdir(project)
        setup_rhiza_git_repo()

    @pytest.mark.parametrize("target", LANGUAGE_LAYER_TARGETS)
    def test_contract_target_is_absent(self, logger, target):
        """Core must not define what a language layer owns, or two layers would clash."""
        proc = run_make(logger, [target], check=False)
        assert proc.returncode != 0
        assert "no rule to make target" in proc.stderr.lower()

    def test_help_still_works_without_a_language_layer(self, logger):
        """The framework half of core stands on its own."""
        out = strip_ansi(run_make(logger, ["help"], dry_run=False).stdout)
        assert "install-uv" in out, "core still provisions the tool runner"
