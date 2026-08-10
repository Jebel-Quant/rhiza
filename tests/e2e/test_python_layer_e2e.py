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
    gate_env,
    line_rate,
)
from tests.util import run_make, strip_ansi

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
    """The scaffold's test runs, and coverage lands where the docs badge looks.

    Also the check that book.mk's no-op `test::` default has not swallowed the
    real one: both rules are defined here (book is synced), so an accidental
    single-colon rule in either file would make this fail rather than run nothing.
    """
    out = gate(project, "test", logger)
    # Two items: the scaffold's own test plus the starter the layer ships (#1476).
    # `[2 items]` rather than "collected 2 items": test.mk runs pytest under xdist,
    # which replaces the collection line with "N workers [2 items]".
    assert "[2 items]" in out, f"pytest did not collect both tests:\n{out}"
    assert "2 passed" in out, f"pytest did not report both tests passing:\n{out}"

    coverage_xml = project.path / "_tests" / "coverage.xml"
    assert coverage_xml.is_file(), "`make test` did not write _tests/coverage.xml"
    assert line_rate(coverage_xml) == pytest.approx(1.0), "the scaffold is meant to be fully covered"
    assert (project.path / "_tests" / "html-coverage").is_dir()
    assert (project.path / "_tests" / "html-report" / "report.html").is_file()


def test_the_layer_brings_its_own_test_so_a_fresh_repo_tests_something(project: Project, logger):
    """The layer's own starter test runs — not just the scaffold's (#1476).

    This is the gate's vacuity check, and it has to name the *shipped* file. `make test`
    short-circuits on an empty `tests/` with a warning and exit 0, so a fresh Python repo
    passed `make test` — and `make all` — while measuring nothing. The scaffold writes its
    own `tests/test_greeting.py`, which means the sibling test above would stay green even
    if python-core shipped no starter at all.

    That is exactly how the Go instance of this survived until #1467: the scaffold's
    `greeting_test.go` masked it until the assertion was repointed at the bundle's own
    `internal/version` package. Asserting on `test_rhiza_packaging.py` is the Python
    equivalent — drop it from the layer and this fails.

    Read from the HTML report rather than from stdout, because `test` runs pytest under
    xdist (`-n auto`), which replaces per-file output with a bare progress line: the
    filename never appears in the console at all. The report is written by the same gate
    and records each test id with its outcome, so this can require **Passed** rather than
    merely collected — a starter that silently skipped would satisfy the item count and
    still measure nothing.
    """
    gate(project, "test", logger)

    assert (project.path / "tests" / "test_rhiza_packaging.py").is_file(), (
        "python-core no longer ships a starter test, so a fresh repo's `tests/` is empty "
        "and `make test` short-circuits with a warning and exit 0"
    )

    report = (project.path / "_tests" / "html-report" / "report.html").read_text(encoding="utf-8")
    assert "test_rhiza_packaging.py::test_the_installed_version_matches_pyproject" in report, (
        "the starter test was not collected by `make test`"
    )
    # The report embeds its data as HTML-escaped JSON, hence the entity-quoted needle.
    assert "&#34;result&#34;: &#34;Passed&#34;, &#34;testId&#34;: &#34;tests/test_rhiza_packaging.py" in report, (
        "the starter test did not pass — a skip here means it measured nothing, which is the vacuum #1476 was about"
    )


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


def test_license_gate_actually_rejects_a_matching_licence(project: Project, logger):
    """The gate must go red on a match -- the case nothing else here covers.

    Every other assertion about this gate is that it stays green, which a gate
    that can never fail also satisfies. That is not hypothetical: `--fail-on`
    compares against the *whole* licence string, so before `--partial-match` was
    added the default `GPL;LGPL;AGPL` matched no real classifier and the gate was
    inert.

    `IT` is the probe because it is a strict substring of `MIT` and equal to no
    licence any package reports. Whole-string matching cannot match it, so this
    test fails without `--partial-match`; substring matching must. It needs no
    copyleft dependency installed to prove the point, and every Python venv has
    an MIT-licensed package in it.
    """
    proc = run_make(
        logger,
        ["license", "LICENSE_FAIL_ON=IT"],
        check=False,
        dry_run=False,
        env=gate_env(),
        cwd=project.path,
    )

    assert proc.returncode != 0, (
        "license gate reported success on a matching licence -- --fail-on is inert:\n" + proc.stdout[-2000:]
    )
    assert "fail-on license" in strip_ansi(proc.stdout) + strip_ansi(proc.stderr)


def test_license_gate_honours_an_exemption(project: Project, logger):
    """A package named in LICENSE_IGNORE_PACKAGES drops out of the scan entirely.

    The exemption is what makes the gate above survivable: a project with a
    legitimate copyleft *development* dependency needs a way to say so once,
    visibly, rather than deleting the gate that keeps catching it.

    Asserted by absence from the report rather than by flipping a failure to a
    pass, which would depend on guessing every package that could match.
    """
    out = gate(project, "license", logger, env={**gate_env(), "LICENSE_IGNORE_PACKAGES": "pytest"})

    assert "Running license compliance scan" in out
    assert "pytest" not in out, "pytest was scanned despite being exempted:\n" + out[-2000:]


def test_deptry_gate_finds_no_dependency_problems(project: Project, logger):
    """Deptry runs on the folders the synced bundles contribute, and is clean."""
    out = gate(project, "deps", logger)
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
        ("deps", "Running deptry on:"),
        ("test", "[2 items]"),  # the scaffold's test plus the layer's starter (#1476)
        ("docs-coverage", "Checking documentation coverage in:"),
        ("security", "Running bandit security scan"),
        ("license", "Running license compliance scan"),
        ("typecheck", "Running mypy strict type checking"),
    ):
        assert evidence in out, f"`make all` no longer runs the {gate_name} gate ({evidence!r})"
