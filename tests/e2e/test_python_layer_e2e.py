"""Every gate the `python-core` layer ships, run for real on a freshly synced project.

The dry-run tests in `tests/api/test_language_layer.py` prove the Python layer
*names* these gates and expands them to the right commands. These prove the
commands work: uv creates the venv and resolves a lock, pytest measures coverage
into the path book.mk badges, interrogate reaches 100%, ty and mypy accept the
code, and pre-commit's whole hook set passes on a project that was synced five
seconds ago.

That last one is the interesting case. A downstream project's first act after
`/rhiza:update` is `make all`, so a hook that cannot pass on a fresh sync is a
template bug that no amount of dry-run assertion would surface.

Skips unless ``RHIZA_E2E=1`` and uv is on PATH. See `harness.py`.
"""

from __future__ import annotations

import pytest

from tests.e2e.harness import (
    GATE_TIMEOUT_SECONDS,
    PYTHON,
    Project,
    assemble,
    assert_hooks_passed,
    gate,
    line_rate,
)

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(GATE_TIMEOUT_SECONDS)]


@pytest.fixture(scope="module")
def project(root, tmp_path_factory, logger) -> Project:
    """Sync core + python-core + book + tests, scaffold a project, and install it."""
    return assemble(PYTHON, root, tmp_path_factory.mktemp("e2e-python"), logger)


def test_install_creates_the_venv_and_resolves_a_lock(project: Project):
    """`install` is Python's: a uv virtualenv plus a resolved dependency set.

    The lock assertion matters beyond `install` itself — the uv-lock pre-commit
    hook regenerates uv.lock and fails when it changes, so a project whose first
    install left no lock behind cannot pass `fmt`.
    """
    assert (project.path / ".venv").is_dir(), "install did not create the project virtualenv"
    assert (project.path / "uv.lock").is_file(), "install did not resolve a lock file"
    assert "Installation complete" in project.install_output


def test_install_wires_up_the_pre_commit_hook(project: Project):
    """The layer installs git hooks, so a commit runs the same checks CI does."""
    assert (project.path / ".git" / "hooks" / "pre-commit").is_file(), "install did not install pre-commit's git hook"


def test_test_gate_runs_pytest_and_writes_the_reports_book_mk_reads(project: Project, logger):
    """The scaffold's one test runs, and coverage lands where the docs badge looks.

    Also the check that book.mk's no-op `test::` default has not swallowed the
    real one: both rules are defined here (book is synced), so an accidental
    single-colon rule in either file would make this fail rather than run nothing.
    """
    out = gate(project, "test", logger)
    # `[1 item]` rather than "collected 1 item": test.mk runs pytest under xdist,
    # which replaces the collection line with "N workers [1 item]".
    assert "[1 item]" in out, f"pytest did not collect the scaffold's test:\n{out}"
    assert "1 passed" in out, f"pytest did not report a passing test:\n{out}"

    coverage_xml = project.path / "_tests" / "coverage.xml"
    assert coverage_xml.is_file(), "`make test` did not write _tests/coverage.xml"
    assert line_rate(coverage_xml) == pytest.approx(1.0), "the scaffold is meant to be fully covered"
    assert (project.path / "_tests" / "html-coverage").is_dir()
    assert (project.path / "_tests" / "html-report" / "report.html").is_file()


def test_docs_coverage_gate_reaches_100_percent(project: Project, logger):
    """Interrogate at `--fail-under 100`: every module, class and function documented."""
    out = gate(project, "docs-coverage", logger)
    assert "100.0%" in out, f"interrogate did not report full docstring coverage:\n{out}"


def test_typecheck_gate_runs_both_checkers(project: Project, logger):
    """TYPECHECKER defaults to both, so ty and mypy --strict each get a turn."""
    out = gate(project, "typecheck", logger)
    assert "Running ty type checking" in out
    assert "Running mypy strict type checking" in out


def test_security_gate_scans_the_source(project: Project, logger):
    """Bandit runs over SOURCE_FOLDER with the shipped .bandit config."""
    out = gate(project, "security", logger)
    assert "Running bandit security scan" in out


def test_license_gate_accepts_a_permissive_dependency_set(project: Project, logger):
    """pip-licenses fails on GPL/LGPL/AGPL; the scaffold declares none."""
    out = gate(project, "license", logger)
    assert "Running license compliance scan" in out


def test_deptry_gate_finds_no_dependency_problems(project: Project, logger):
    """Deptry runs on the folders the synced bundles contribute, and is clean."""
    out = gate(project, "deptry", logger)
    assert "Running deptry on:" in out


def test_rhiza_test_gate_runs_the_shipped_self_tests(project: Project, logger):
    """The `.rhiza/tests` suite the tests bundle ships passes on a fresh sync.

    This is the gate that judges the *scaffold* against rhiza's own expectations —
    pyproject shape, README validity, doctests — which is exactly what a downstream
    project gets judged on.
    """
    out = gate(project, "rhiza-test", logger)
    assert "passed" in out, f"the shipped self-tests collected nothing:\n{out}"


def test_fmt_gate_passes_every_pre_commit_hook(project: Project, logger):
    """A freshly synced project is already clean under its own pre-commit config.

    Includes the hooks that rewrite files (ruff-format, uv-lock, interrogate):
    pre-commit fails a hook that modifies anything, so this asserts the shipped
    configs and the scaffold agree byte for byte.

    The per-hook assertions matter as much as the exit code — a config that stopped
    declaring ruff would still exit 0, and this gate would look green while linting
    nothing.
    """
    out = gate(project, "fmt", logger)
    assert_hooks_passed(out, ("ruff", "ruff format", "markdownlint", "bandit", "uv-lock", "interrogate"))


def test_all_runs_the_whole_gate_set(project: Project, logger):
    """`make all` — the aggregate a developer and CI both call — is green.

    Asserted on each gate's own output rather than on the exit code alone: `all` is
    a prerequisite list, and a gate dropped from it leaves the aggregate passing
    while quietly checking less. Last in the module because it re-runs everything.
    """
    out = gate(project, "all", logger)
    # Each string must be unique to its gate. interrogate runs in both `fmt` (as a
    # hook) and `docs-coverage` (as the gate), and both pytest runs print "N passed",
    # so the evidence is a line only one of them emits.
    for gate_name, evidence in (
        ("fmt", "ruff format"),
        ("deptry", "Running deptry on:"),
        ("test", "[1 item]"),
        ("docs-coverage", "Checking documentation coverage in:"),
        ("security", "Running bandit security scan"),
        ("license", "Running license compliance scan"),
        ("typecheck", "Running mypy strict type checking"),
    ):
        assert evidence in out, f"`make all` no longer runs the {gate_name} gate ({evidence!r})"
