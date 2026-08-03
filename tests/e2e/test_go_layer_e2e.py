"""Every gate the `go-core` layer ships, run for real on a freshly synced module.

Go is where a dry-run test is least sufficient. Two of this layer's gates are
assembled rather than delegated — coverage converts a Go profile to Cobertura and
enforces the floor in awk, because `go test` has no `--fail-under`, and the licence
gate has to feed go-licenses the module's own path so it does not fail the project
for having no LICENSE of its own. Neither is checkable without running it: the
`--ignore` flag exists precisely because someone ran the gate on a real project and
watched it go red.

These run all of it — go test with the race detector, the profile conversion, vet
plus golangci-lint, revive's exported rule, govulncheck — on the smallest module a
correct layer should be green on.

Skips unless ``RHIZA_E2E=1`` and go is on PATH. See `harness.py`.
"""

from __future__ import annotations

import re

import pytest

from tests.e2e.harness import (
    GATE_TIMEOUT_SECONDS,
    GO,
    Project,
    assemble,
    assert_hooks_passed,
    gate,
    line_rate,
)

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(GATE_TIMEOUT_SECONDS)]

# The binaries the gates call. `go-tools` builds them into the project's own bin/
# rather than the developer's GOPATH, so a gate never depends on what happens to
# be installed globally.
GO_TOOLS = ("golangci-lint", "govulncheck", "go-licenses", "gocover-cobertura", "revive")


@pytest.fixture(scope="module")
def project(root, tmp_path_factory, logger) -> Project:
    """Sync core + go-core + book, scaffold a module, and install it."""
    return assemble(GO, root, tmp_path_factory.mktemp("e2e-go"), logger)


def test_install_is_the_thinnest_of_the_three_layers(project: Project):
    """`go mod download` and nothing else: no rustup step, no virtualenv.

    go.mod's `go`/`toolchain` directives make the go command fetch a matching
    compiler itself, which is why this layer has no equivalent of `rustup show`.
    """
    assert "Installation complete" in project.install_output
    assert not (project.path / ".venv").exists(), "the Go layer created a Python virtualenv"


def test_go_core_ships_the_version_constant_the_release_flow_writes_to(project: Project):
    """A Go module's version is its git tag, so the layer ships a file to carry it.

    Without `internal/version/version.go` the release flow has no version location
    and the release commit and its tag can drift apart. It arrives from the bundle,
    not the scaffold — deleting it from go-core would fail here.
    """
    version_go = project.path / "internal" / "version" / "version.go"
    assert version_go.is_file(), "go-core no longer ships internal/version/version.go"
    assert 'const Version = "' in version_go.read_text(encoding="utf-8")


def test_go_tools_provides_every_binary_the_gates_call(project: Project, logger):
    """After `go-tools`, each gate's binary exists in the project's bin/."""
    gate(project, "go-tools", logger)
    bin_dir = project.path / "bin"
    missing = [tool for tool in GO_TOOLS if not (bin_dir / tool).is_file()]
    assert not missing, f"`make go-tools` left {missing} uninstalled in {bin_dir}"


def test_test_gate_runs_the_suite_under_the_race_detector(project: Project, logger):
    """`go test ./...` with the layer's default flags, and it actually runs a test.

    Also the check that book.mk's no-op `test::` default coexists with the layer's
    real one: both rules are defined here, so a single-colon rule in either file
    would break the build rather than quietly run nothing.
    """
    out = gate(project, "test", logger)
    assert "example.com/demo/greeting" in out, f"go test did not run the scaffold's package:\n{out}"


def test_the_layer_brings_its_own_test_so_a_fresh_repo_tests_something(project: Project, logger):
    """The bundle's `internal/version` package runs a test, not "[no test files]".

    This is the gate's vacuity check, and it has to run for real: `go test ./...`
    exits 0 on a package with no test file, so the scaffold's own `greeting_test.go`
    would mask a go-core that shipped none. Asserting on the bundle's package
    instead is what fails if `version_test.go` is dropped from the layer.
    """
    out = gate(project, "test", logger)
    assert "example.com/demo/internal/version" in out, (
        f"go-core's own package reported no test run — a fresh Go repo's `make test` "
        f"passes without testing anything:\n{out}"
    )


def test_coverage_gate_converts_the_profile_and_enforces_the_floor(project: Project, logger):
    """Go emits a profile; the gate converts it to the Cobertura path book.mk reads.

    Three assembled steps in one gate — the atomic covermode the race build needs,
    gocover-cobertura's conversion, and the awk floor check that stands in for the
    `--fail-under` go test does not have.
    """
    out = gate(project, "coverage", logger)
    assert (project.path / "_tests" / "coverage.out").is_file(), "no Go coverage profile was written"

    coverage_xml = project.path / "_tests" / "coverage.xml"
    assert coverage_xml.is_file(), "`make coverage` did not write _tests/coverage.xml"
    assert line_rate(coverage_xml) >= 0.9, "the scaffold fell below the coverage floor the gate enforces"
    assert (project.path / "_tests" / "html-coverage" / "index.html").is_file()
    assert "floor: 90" in out, f"the coverage floor was never reported, so awk did not see a total:\n{out}"


def test_typecheck_gate_runs_vet_and_golangci_lint(project: Project, logger):
    """The compiler already type-checks, so the gate is vet plus the linter."""
    out = gate(project, "typecheck", logger)
    assert "Running go vet" in out
    assert "Running golangci-lint" in out


def test_docs_coverage_gate_requires_doc_comments_on_exported_items(project: Project, logger):
    """Revive's `exported` rule — pass/fail, the way Rust's `-D missing_docs` is.

    Runs against the bundle's own `internal/version` package as well as the
    scaffold, so an undocumented export shipped by go-core would fail here.
    """
    out = gate(project, "docs-coverage", logger)
    assert "Checking doc comments on exported items" in out


def test_security_gate_scans_for_known_vulnerabilities(project: Project, logger):
    """`govulncheck` — the pip-audit analogue. Needs the Go vulnerability database."""
    out = gate(project, "security", logger)
    assert "Running govulncheck" in out


def test_license_gate_ignores_the_projects_own_module(project: Project, logger):
    """go-licenses walks the project's own packages, not only its dependencies.

    Every freshly synced repo lacks a LICENSE file, so without the `--ignore`
    argument read from `go list -m` this gate is red on the first run of every Go
    project. That failure mode only exists when the gate really runs, which is why
    this test is the one that pins it.
    """
    out = gate(project, "license", logger)
    assert "Running license compliance scan" in out


def test_deps_gate_verifies_go_mod_is_tidy(project: Project, logger):
    """`go mod tidy -diff` is both halves of deptry in one command."""
    out = gate(project, "deps", logger)
    assert "Checking that go.mod and go.sum are tidy" in out


def test_rhiza_test_gate_actually_runs_the_shipped_suite(project: Project, logger):
    """`rhiza-test` must collect real tests, not report an empty directory.

    This assertion used to be its own inverse — it required "No .rhiza/tests directory
    found", pinning as intended the fact that nothing ever delivered the suite to a Go
    repo. `rhiza-test` is a prerequisite of `all`, so that made the gate vacuous on
    every Go project: the same hole as the empty `go test ./...` (#1467), one level up.

    `core` now ships the neutral harness and `go-core` its own `test_go_module.py`, so
    the payload arrives with the layer and no `tests` bundle is needed.
    """
    out = gate(project, "rhiza-test", logger)
    assert "No .rhiza/tests directory found" not in out, "the self-test suite was not delivered to a Go project"
    assert "test_go_module.py" in out, f"the Go layer's own self-tests did not run:\n{out}"
    # core's neutral half must arrive too, not just the layer's own module (#1472):
    assert "test_readme.py" in out, f"core's language-neutral README tests did not run:\n{out}"
    assert re.search(r"\d+ passed", out), f"rhiza-test collected nothing:\n{out}"
    # Nothing in the Go suite has a legitimate reason to skip on this scaffold, and the
    # ones that would — every test reconciling the Version constant with the newest tag —
    # are the whole point of tagging the scaffold in `_init_repo`.
    assert "skipped" not in out, f"a self-test skipped instead of running:\n{out}"


def test_fmt_gate_passes_every_pre_commit_hook(project: Project, logger):
    """The Go pre-commit config is clean on a fresh sync.

    Covers this layer's own hooks — gofmt, go vet, the go.mod tidiness check — and
    the neutral half that runs through uvx with no `.python-version` to read.

    Asserted per hook, not just on the exit code: the Go hooks are `types: [go]`, so
    a config that stopped matching Go files would report every one of them as
    skipped and still exit 0.
    """
    out = gate(project, "fmt", logger)
    assert_hooks_passed(out, ("gofmt", "go vet", "go.mod and go.sum are tidy", "markdownlint"))


def test_all_runs_the_whole_gate_set(project: Project, logger):
    """`make all` is green, and still chains every gate.

    Asserted on each gate's own output rather than the exit code alone: `all` is a
    prerequisite list, and a gate dropped from it leaves the aggregate passing while
    quietly checking less. Last, because it re-runs everything above.
    """
    out = gate(project, "all", logger)
    for gate_name, evidence in (
        ("fmt", "gofmt"),
        ("test", "example.com/demo/greeting"),
        ("docs-coverage", "Checking doc comments on exported items"),
        ("security", "Running govulncheck"),
        # The recipe's own line, not the pre-commit hook's near-identical name:
        # matching the hook name would let `fmt` alone satisfy this.
        ("deps", "Checking that go.mod and go.sum are tidy"),
        ("license", "Running license compliance scan"),
        ("typecheck", "Running go vet"),
    ):
        assert evidence in out, f"`make all` no longer runs the {gate_name} gate ({evidence!r})"
