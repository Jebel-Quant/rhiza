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

import re
import shutil
from pathlib import Path

import pytest

from tests.util import run_make, setup_rhiza_git_repo, strip_ansi

# The names every language layer owns. Adding a name here is a promise every layer
# must keep — the classes below assert it for `python-core` and `rust-core` alike.
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

    def test_docs_coverage_denies_undocumented_items(self, logger):
        """Rust's answer to interrogate: pass/fail on `missing_docs` rather than a percentage."""
        out = strip_ansi(run_make(logger, ["docs-coverage"], check=False).stdout)
        assert "-D missing_docs" in out
        assert "cargo doc" in out

    def test_install_does_not_reach_for_uv_sync(self, logger):
        """A Rust `install` is rustup + cargo fetch; uv is only the tool runner."""
        out = strip_ansi(run_make(logger, ["install"], check=False).stdout)
        assert "cargo fetch" in out
        assert "uv sync" not in out

    def test_cargo_tools_bootstraps_every_subcommand_the_gates_call(self, logger):
        """A gate whose cargo subcommand is not installed fails with a bare 'no such command'."""
        out = strip_ansi(run_make(logger, ["cargo-tools"], check=False).stdout)
        assert "cargo-binstall" in out, "prebuilt binaries are what keep this from being a multi-minute build"
        for tool in ("cargo-nextest", "cargo-llvm-cov", "cargo-deny", "cargo-machete"):
            assert tool in out, f"`cargo-tools` does not install {tool}, which a gate below calls"

    def test_all_chains_the_rust_gates(self, logger):
        """The mirror of `test_all_chains_the_python_gates` — a dropped gate shows up here.

        Asserted on the expanded recipes rather than the prerequisite list, so a gate
        that is named but whose recipe has been gutted still fails.
        """
        out = strip_ansi(run_make(logger, ["all"], check=False).stdout)
        assert "pre-commit run --all-files" in out  # fmt, from core
        for gate, command in (
            ("test", "cargo nextest run"),
            ("docs-coverage", "-D missing_docs"),
            ("security", "cargo deny check advisories"),
            ("deps", "cargo machete"),
            ("license", "cargo deny check licenses"),
            ("typecheck", "cargo clippy"),
        ):
            assert command in out, f"`make all` no longer runs the {gate} gate ({command})"

    def test_all_runs_the_doctests_nextest_skips(self, logger):
        """Nextest ignores doctests; dropping the `cargo test --doc` line silently stops testing them."""
        assert "cargo test --doc" in strip_ansi(run_make(logger, ["all"], check=False).stdout)

    def test_rhiza_test_still_runs_the_python_self_tests(self, logger):
        """The template's own suite validates YAML and READMEs, so it stays Python under uv."""
        out = strip_ansi(run_make(logger, ["rhiza-test"], check=False).stdout)
        assert "pytest .rhiza/tests" in out

    def test_neutral_tooling_works_without_a_python_version_file(self, logger):
        """`fmt` runs pre-commit through `uvx -p $(PYTHON_VERSION)` whatever the language.

        A Rust repo ships no `.python-version`, so the whole language-neutral half of
        the template rests on the fallback in rhiza.mk resolving to a real version —
        an empty `-p` would break `fmt` on every Rust project at once.
        """
        out = strip_ansi(run_make(logger, ["fmt"], check=False).stdout)
        assert not (self.project / ".python-version").exists(), "fixture drifted: this asserts the fallback path"
        assert re.search(r"-p \d+\.\d+ pre-commit run --all-files", out), (
            f"`make fmt` did not resolve PYTHON_VERSION to a usable value:\n{out}"
        )


class TestGoLayerKeepsTheSameContract:
    """`go-core` is the third peer, assembled into a temp dir like the Rust one.

    No cargo, no go: these assert the layer *declares* the contract and maps each
    gate to its Go equivalent, which is what lets book.mk and the CI workflows stay
    language-agnostic. There is no Go toolchain in this repo to run them against.
    """

    @pytest.fixture(autouse=True)
    def go_project(self, root: Path, tmp_path: Path, monkeypatch):
        """Assemble core + go-core into a project, standing in for a sync."""
        project = tmp_path / "go-project"
        (project / ".rhiza" / "make.d").mkdir(parents=True)
        shutil.copy(root / "Makefile", project / "Makefile")
        shutil.copy(root / ".rhiza" / "rhiza.mk", project / ".rhiza" / "rhiza.mk")
        for fragment in (root / "bundles" / "core" / ".rhiza" / "make.d").iterdir():
            shutil.copy(fragment, project / ".rhiza" / "make.d" / fragment.name)
        shutil.copy(
            root / "bundles" / "go-core" / ".rhiza" / "make.d" / "go.mk",
            project / ".rhiza" / "make.d" / "go.mk",
        )
        (project / "go.mod").write_text("module example.com/demo\n\ngo 1.24\n")
        monkeypatch.chdir(project)
        setup_rhiza_git_repo()
        self.project = project

    @pytest.mark.parametrize("target", LANGUAGE_LAYER_TARGETS)
    def test_every_contract_target_resolves(self, logger, target):
        """The same names the other layers provide, so callers need not branch."""
        proc = run_make(logger, [target], check=False)
        assert "no rule to make target" not in proc.stderr.lower()

    @pytest.mark.parametrize(
        ("target", "expected"),
        [
            ("typecheck", "go vet"),
            ("security", "govulncheck"),
            ("license", "go-licenses check"),
            ("deps", "go mod tidy -diff"),
            ("test", "go test ./..."),
            ("docs-coverage", "revive"),
        ],
    )
    def test_gate_maps_to_its_go_equivalent(self, logger, target, expected):
        """Each gate has a Go counterpart under the same target name."""
        out = strip_ansi(run_make(logger, [target], check=False).stdout)
        assert expected in out, f"`make {target}` should run {expected}"

    def test_coverage_writes_the_report_book_mk_reads(self, logger):
        """book.mk badges `_tests/coverage.xml`; go emits a profile, so it must be converted."""
        out = strip_ansi(run_make(logger, ["coverage"], check=False).stdout)
        assert "-coverprofile=_tests/coverage.out" in out
        assert "gocover-cobertura" in out
        assert "_tests/coverage.xml" in out

    def test_coverage_enforces_the_floor_go_test_will_not(self, logger):
        """`go test` has no --fail-under, so dropping the awk check silently drops the gate."""
        out = strip_ansi(run_make(logger, ["coverage"], check=False).stdout)
        assert "go tool cover -func" in out
        assert "floor" in out

    def test_coverage_is_atomic_because_the_test_run_is_a_race_build(self, logger):
        """The default `set` covermode is not race-safe; mixing them corrupts counts."""
        assert "-covermode=atomic" in strip_ansi(run_make(logger, ["coverage"], check=False).stdout)

    def test_install_is_the_thinnest_of_the_three_layers(self, logger):
        """go.mod's toolchain directive replaces rustup; uv stays a tool runner only."""
        out = strip_ansi(run_make(logger, ["install"], check=False).stdout)
        assert "go mod download" in out
        assert "uv sync" not in out
        # The command, not the word: go.mk's recipe comments mention rustup to explain
        # its absence, and `make -n` prints recipe comments.
        assert "rustup show" not in out

    def test_license_gate_ignores_the_projects_own_module(self, logger):
        """go-licenses walks the project's own packages, not just its dependencies.

        Found by running the gate on a real synced project: without
        `--ignore <module path>` it fails on the project itself for having no LICENSE
        file, which every freshly synced repo lacks — the profile would ship a gate
        that is red on the first run. The path must come from `go list -m` rather than
        be hard-coded, or it only works for one module.
        """
        out = strip_ansi(run_make(logger, ["license"], check=False).stdout)
        assert "go-licenses check ./..." in out
        assert "--ignore" in out, "the gate fails on a project with no LICENSE without this"
        assert "go list -m" in out, "the ignored path must be read from go.mod, not hard-coded"

    def test_go_tools_bootstraps_every_binary_the_gates_call(self, logger):
        """A gate whose binary is missing fails with a bare 'no such file'."""
        out = strip_ansi(run_make(logger, ["go-tools"], check=False).stdout)
        for tool in ("golangci-lint", "govulncheck", "go-licenses", "gocover-cobertura", "revive"):
            assert tool in out, f"`go-tools` does not install {tool}, which a gate below calls"

    def test_all_chains_the_go_gates(self, logger):
        """The mirror of the Python and Rust `all` tests — a dropped gate shows up here."""
        out = strip_ansi(run_make(logger, ["all"], check=False).stdout)
        assert "pre-commit run --all-files" in out  # fmt, from core
        for gate, command in (
            ("test", "go test ./..."),
            ("docs-coverage", "revive"),
            ("security", "govulncheck"),
            ("deps", "go mod tidy -diff"),
            ("license", "go-licenses check"),
            ("typecheck", "go vet"),
        ):
            assert command in out, f"`make all` no longer runs the {gate} gate ({command})"

    def test_rhiza_test_still_runs_the_python_self_tests(self, logger):
        """The template's own suite validates YAML and READMEs, so it stays Python under uv."""
        out = strip_ansi(run_make(logger, ["rhiza-test"], check=False).stdout)
        assert "pytest .rhiza/tests" in out

    def test_neutral_tooling_works_without_a_python_version_file(self, logger):
        """As with Rust: no `.python-version`, so `fmt` rests on the rhiza.mk fallback."""
        out = strip_ansi(run_make(logger, ["fmt"], check=False).stdout)
        assert not (self.project / ".python-version").exists(), "fixture drifted: this asserts the fallback path"
        assert re.search(r"-p \d+\.\d+ pre-commit run --all-files", out), (
            f"`make fmt` did not resolve PYTHON_VERSION to a usable value:\n{out}"
        )


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
