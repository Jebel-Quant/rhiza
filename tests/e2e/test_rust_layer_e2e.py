"""Every gate the `rust-core` layer ships, run for real on a freshly synced crate.

The Rust layer's whole claim is parity: the same target names as `python-core`,
backed by cargo instead of uv. `tests/api/test_language_layer.py` checks the names
and the commands they expand to from `make -n`; nothing there ever invokes cargo,
so a flag cargo rejects, a component rustup never installed, or a report written
to the wrong path would all pass it.

These run the real thing — nextest, the doctests nextest skips, llvm-cov into the
Cobertura path book.mk badges, clippy, cargo-deny, cargo-machete — against the
smallest crate a correct layer should be green on.

Skips unless ``RHIZA_E2E=1`` and cargo/rustup are on PATH. See `harness.py`.
"""

from __future__ import annotations

import shutil

import pytest

from tests.e2e.harness import (
    GATE_TIMEOUT_SECONDS,
    RUST,
    Project,
    assemble,
    assert_hooks_passed,
    gate,
    line_rate,
)

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(GATE_TIMEOUT_SECONDS)]

# The cargo subcommands the gates call. `cargo-tools` installs them on demand;
# a gate whose subcommand is missing fails with a bare "no such command".
CARGO_TOOLS = ("cargo-nextest", "cargo-llvm-cov", "cargo-deny", "cargo-machete")


@pytest.fixture(scope="module")
def project(root, tmp_path_factory, logger) -> Project:
    """Sync core + rust-core + book, scaffold a crate, and install it."""
    return assemble(RUST, root, tmp_path_factory.mktemp("e2e-rust"), logger)


def test_install_materialises_the_toolchain_and_a_lockfile(project: Project):
    """`install` is rustup + cargo fetch, and fetch is what writes Cargo.lock.

    The lockfile matters beyond the fetch: the cargo-lock-is-current pre-commit
    hook runs `cargo metadata --locked`, which fails outright when no lock exists.
    So a layer whose install skipped the fetch would pass `install` and fail `fmt`.
    """
    assert (project.path / "Cargo.lock").is_file(), "install did not fetch dependencies (no Cargo.lock)"
    assert "Installation complete" in project.install_output


def test_install_does_not_create_a_python_virtualenv(project: Project):
    """`uv` stays a tool runner here: no `.venv`, because there is no Python project.

    The dry-run test asserts `uv sync` is absent from the recipe; this asserts the
    consequence, which is what would actually confuse a Rust developer.
    """
    assert not (project.path / ".venv").exists(), "the Rust layer created a Python virtualenv"


def test_cargo_tools_provides_every_subcommand_the_gates_call(project: Project, logger):
    """After `cargo-tools`, each gate's subcommand resolves on PATH."""
    gate(project, "cargo-tools", logger)
    missing = [tool for tool in CARGO_TOOLS if shutil.which(tool) is None]
    assert not missing, f"`make cargo-tools` left {missing} uninstalled"


def test_test_gate_runs_both_nextest_and_the_doctests(project: Project, logger):
    """Nextest runs the unit tests; the separate `cargo test --doc` line runs the rest.

    Asserted separately on purpose: nextest silently ignores doctests, so dropping
    the second command would leave a green `make test` that never ran the crate's
    documented examples. The scaffold has one of each so both halves have work.
    """
    out = gate(project, "test", logger)
    assert "greets_the_caller_by_name" in out, f"nextest did not run the unit test:\n{out}"
    assert "Running doctests" in out
    assert "test result: ok" in out, f"the doctests did not run:\n{out}"


def test_coverage_gate_writes_the_cobertura_report_book_mk_reads(project: Project, logger):
    """llvm-cov must land at `_tests/coverage.xml`, the same path pytest-cov uses.

    Requires the llvm-tools-preview component that rust-toolchain.toml pins, so
    this also proves `install`'s `rustup show` actually materialised the components
    rather than just the channel.
    """
    gate(project, "coverage", logger)
    coverage_xml = project.path / "_tests" / "coverage.xml"
    assert coverage_xml.is_file(), "`make coverage` did not write _tests/coverage.xml"
    assert line_rate(coverage_xml) >= 0.9, "the scaffold fell below the coverage floor the gate enforces"
    assert (project.path / "_tests" / "html-coverage").is_dir()


def test_typecheck_gate_runs_clippy_with_warnings_as_errors(project: Project, logger):
    """`rustc` already type-checks, so the analogous gate is a clean clippy pass."""
    out = gate(project, "typecheck", logger)
    assert "Running clippy" in out


def test_docs_coverage_gate_builds_docs_with_missing_docs_denied(project: Project, logger):
    """Rust's answer to interrogate: the doc build fails on any undocumented item."""
    gate(project, "docs-coverage", logger)
    assert (project.path / "target" / "doc").is_dir(), "cargo doc produced no documentation"


def test_security_gate_checks_the_advisory_database(project: Project, logger):
    """cargo-deny advisories — the pip-audit analogue. Needs the RustSec index."""
    out = gate(project, "security", logger)
    assert "Running cargo-deny advisories" in out


def test_license_gate_enforces_the_allow_list(project: Project, logger):
    """deny.toml is an allow-list, so the crate's own licence must be in it.

    An unlicensed scaffold fails here on itself rather than on a dependency, which
    is the Rust echo of the `--ignore` flag go-core needs for the same reason.
    """
    out = gate(project, "license", logger)
    assert "Running license compliance scan" in out


def test_deps_gate_reports_no_unused_dependencies(project: Project, logger):
    """cargo-machete is the deptry analogue: declared but unused crates."""
    out = gate(project, "deps", logger)
    assert "Checking for unused dependencies" in out


def test_rhiza_test_gate_skips_cleanly_without_a_tests_bundle(project: Project, logger):
    """`rust-local` ships no `.rhiza/tests`, so the self-test gate must no-op.

    `all` depends on `rhiza-test`, so a gate that failed on a missing directory
    would make `make all` red on every Rust project.
    """
    out = gate(project, "rhiza-test", logger)
    assert "No .rhiza/tests directory found" in out


def test_fmt_gate_passes_every_pre_commit_hook(project: Project, logger):
    """The Rust pre-commit config is clean on a fresh sync.

    Covers the hooks unique to this layer — cargo fmt, clippy, and the Cargo.lock
    currency check — plus the neutral half that runs through uvx whatever the
    language, which on a Rust project has no `.python-version` to read.

    Asserted per hook, not just on the exit code: the Rust hooks are `types: [rust]`,
    so a config that stopped matching Rust files would report every one of them as
    skipped and still exit 0.
    """
    out = gate(project, "fmt", logger)
    assert_hooks_passed(out, ("cargo fmt", "cargo clippy", "Cargo.lock is up to date", "markdownlint"))


def test_all_runs_the_whole_gate_set(project: Project, logger):
    """`make all` is green, and still chains every gate.

    Asserted on each gate's own output rather than the exit code alone: `all` is a
    prerequisite list, and a gate dropped from it leaves the aggregate passing while
    quietly checking less. Last, because it re-runs everything above.
    """
    out = gate(project, "all", logger)
    for gate_name, evidence in (
        ("fmt", "cargo fmt"),
        ("test", "greets_the_caller_by_name"),
        ("docs-coverage", "Building docs with missing_docs denied"),
        ("security", "Running cargo-deny advisories"),
        ("deps", "Checking for unused dependencies"),
        ("license", "Running license compliance scan"),
        ("typecheck", "Running clippy"),
    ):
        assert evidence in out, f"`make all` no longer runs the {gate_name} gate ({evidence!r})"
