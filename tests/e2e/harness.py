"""Assemble a synced project per language layer and run its gates for real.

`tests/api/test_language_layer.py` asserts the layer *contract* from `make -n`
output: that `install` and `all` exist, and that each gate name expands to the
right command. That catches a renamed target or a dropped gate, but it cannot
catch a gate whose command is wrong — `make -n` never runs cargo, go or uv, so a
recipe that fails on every real project passes the dry-run test happily. The
`--ignore` flag in go-core's licence gate is the recorded example: the dry-run
test for it could only be written *after* someone ran the gate on a real project
and watched it fail on the project's own module.

This module closes that gap. For each layer it copies the bundles into a temp
directory (standing in for a `/rhiza:update` sync), writes the smallest project the
layer should be green on (see `scaffolds.py`), commits it, and runs `make install`.
The test modules then drive one gate per test against that project, for real.

Two properties keep this honest rather than merely expensive:

* **Opt-in.** Nothing runs unless ``RHIZA_E2E=1``, so `make test` stays fast and
  green offline. `make e2e` sets it.
* **Toolchain-gated.** A layer whose compiler is absent skips with a reason
  instead of failing, so a developer with no Rust installed is not blocked by the
  Rust layer's tests. That means a green local run proves nothing on its own —
  `.github/workflows/rhiza_e2e.yml` is where all three actually execute.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - drives git/make against a scratch project
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from defusedxml import ElementTree

from tests.e2e import scaffolds
from tests.util import run_make, strip_ansi, sync_bundles

GIT = shutil.which("git") or "/usr/bin/git"

# The suite runs real toolchains, downloads real tools and takes minutes per
# layer, so it never runs by accident.
ENABLE_FLAG = "RHIZA_E2E"

# Generous per-test ceiling. The first gate in a module absorbs the fixture cost
# (bundle copy, `make install`, and — on the first `fmt` — pre-commit provisioning
# node and every hook environment), and `go-tools` compiles five binaries from
# source. Applied as a module-level `pytest.mark.timeout` by each test module.
GATE_TIMEOUT_SECONDS = 1800


@dataclass(frozen=True)
class Layer:
    """One language layer, and everything needed to stand a real project on it.

    Attributes:
        name: Short label used in temp-dir names and skip messages.
        profile: The profile in `.rhiza/template-bundles.yml` this mirrors.
        bundles: Bundles to sync, in order.
        tools: Executables that must be on PATH, or the layer's tests skip.
        version: The version the layer's scaffold declares, tagged as `v{version}`
            after the initial commit. Without a tag the shipped self-tests that
            reconcile the version with it skip, and the assertion that matters most —
            that the release config can still find the version it is about to
            rewrite — would never run.
        files: Project files to write after the sync, keyed by relative path.
        executables: Paths within `files` to mark executable before `install` runs.
            A real consumer's script carries its execute bit in git; a scaffold
            writes plain text, so a layer that needs one has to say so. Empty for
            all three language layers — `local-setup.sh` is the only user.
    """

    name: str
    profile: str
    bundles: tuple[str, ...]
    tools: tuple[str, ...]
    version: str
    files: dict[str, str] = field(repr=False)
    executables: frozenset[str] = frozenset()


# `book` is in every set on purpose: book.mk declares `test:: ; @:` as a no-op
# default so `make book` works without a test bundle, and a layer's own `test::`
# rule has to coexist with it. Syncing book is what makes `make test` prove that.
#
# The set is now exactly the `local` profile. It used to carry `tests` as a fourth entry
# and deliberately omit `marimo`; both bundles were removed in #1632, each having shipped a
# single documentation page and nothing else. Nothing is lost from this suite by their
# going: the gates they were credited with -- `benchmark`, `hypothesis-test`, `stress`,
# `marimo-validate` -- are tasks in the pinned CLI, and none of them is named by `all`, so
# no assertion here ever reached one.
PYTHON = Layer(
    name="python",
    profile="local",
    bundles=("core", "python-core", "book"),
    tools=("git", "uv"),
    version="0.1.0",
    files=scaffolds.PYTHON_FILES,
)

RUST = Layer(
    name="rust",
    profile="rust-local",
    bundles=("core", "rust-core", "book"),
    tools=("git", "uv", "cargo", "rustup"),
    version="0.1.0",
    files=scaffolds.RUST_FILES,
)

GO = Layer(
    name="go",
    profile="go-local",
    bundles=("core", "go-core", "book"),
    tools=("git", "uv", "go"),
    version="0.0.0",
    files=scaffolds.GO_FILES,
)


@dataclass(frozen=True)
class Project:
    """An assembled, installed project standing in for a synced downstream repo.

    Attributes:
        layer: The layer it was built from.
        path: The project root.
        install: The completed `make install` run, so a test can assert on it
            without paying for a second install.
    """

    layer: Layer
    path: Path
    install: subprocess.CompletedProcess

    @property
    def install_output(self) -> str:
        """Return `make install`'s combined output, ANSI-stripped.

        Both streams, for the reason `gate` gives: rustup and the go command report
        progress on stderr, so which stream a line landed on is not something a test
        should have to know.
        """
        return strip_ansi(self.install.stdout) + strip_ansi(self.install.stderr)


def gate_env() -> dict[str, str]:
    """Return the environment for a nested make run.

    `make e2e` invokes pytest from a recipe, so this process inherits MAKEFLAGS
    (including the jobserver file descriptors) and MAKELEVEL. Passing those down
    to a make that is *not* a sub-make of the outer one makes it warn about a
    missing jobserver and, with `-s` inherited, silences the output a failing gate
    needs to report. Stripping them makes a gate behave identically whether it was
    reached through `make e2e` or a bare `pytest` run.
    """
    dropped = {"MAKEFLAGS", "MAKELEVEL", "MFLAGS", "MAKE_TERMOUT", "MAKE_TERMERR", "VIRTUAL_ENV"}
    return {key: value for key, value in os.environ.items() if key not in dropped}


def require_e2e_enabled() -> None:
    """Skip unless the opt-in flag is set."""
    if os.environ.get(ENABLE_FLAG) != "1":
        pytest.skip(f"end-to-end suite is opt-in: set {ENABLE_FLAG}=1 (or run `make e2e`)")


def require_toolchain(layer: Layer) -> None:
    """Skip when any executable the layer's gates call is missing.

    Args:
        layer: The layer about to be exercised.
    """
    missing = [tool for tool in layer.tools if shutil.which(tool) is None]
    if missing:
        pytest.skip(f"{layer.name} layer needs {', '.join(missing)} on PATH")


def _git(project: Path, *args: str) -> None:
    """Run a git command in the project, raising on failure.

    Args:
        project: Repository root.
        args: Arguments after the git executable.
    """
    subprocess.run([GIT, *args], cwd=project, check=True, capture_output=True)  # nosec B603


def _init_repo(project: Path, version: str) -> None:
    """Make the project a git repo with its scaffold committed and tagged.

    pre-commit reads the file list from git and refuses to run outside a
    repository, so `make fmt` needs both the repo and a commit. The remote is set
    because rhiza's own tooling reads `origin` to identify the project.

    The tag is what makes the rhiza checks do their real work. Every layer's release
    config derives the current version from the newest tag — for Go that *is* the version —
    so the checks reconcile the tag against the version in the manifest. On an untagged repo
    pytest-rhiza's `latest_tag` fixture skips, and all of them go with it, leaving the gate
    green for the wrong reason.

    Args:
        project: The assembled project root.
        version: Version the scaffold declares; tagged as `v{version}`.
    """
    _git(project, "init", "--initial-branch=main")
    _git(project, "config", "user.email", "e2e@example.com")
    _git(project, "config", "user.name", "Rhiza E2E")
    _git(project, "remote", "add", "origin", "https://github.com/jebel-quant/demo")
    _git(project, "add", ".")
    _git(project, "commit", "--no-verify", "-m", "Initial sync")
    _git(project, "tag", f"v{version}")


def _sync(root: Path, layer: Layer, project: Path) -> None:
    """Copy the layer's bundles into the project, dereferencing symlinks.

    Mirrors what a sync does: bundle files land at the paths they
    declare, with dogfood symlinks resolved to real content.

    Args:
        root: The rhiza repository root.
        layer: The layer whose bundles to copy.
        project: Destination project root.
    """
    # Every profile pairs `core` with a layer, and `core` ships the Makefile -- so the sync
    # delivers the front door too, and the suite exercises the file a consumer receives. It
    # used to call `write_shim` here, generating it from the CLI, back when `rhiza-task shim`
    # printed the template.
    sync_bundles(root, list(layer.bundles), project)


def assemble(layer: Layer, root: Path, workdir: Path, logger) -> Project:
    """Sync, scaffold, commit and install a project for one layer.

    Args:
        layer: The layer to build.
        root: The rhiza repository root.
        workdir: A directory to build in (one per layer).
        logger: Test logger.

    Returns:
        The installed project.
    """
    require_e2e_enabled()
    require_toolchain(layer)

    project = workdir / f"{layer.name}-project"
    project.mkdir(parents=True)
    _sync(root, layer, project)

    # The one project file derived rather than listed: it names the profile, and
    # deriving it from the layer keeps that claim tied to the bundles actually synced.
    files = {**layer.files, ".rhiza/template.yml": scaffolds.template_yml(layer.profile)}
    for relative, content in files.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    # Before `_init_repo`, so the bit is what gets committed -- which is how a real
    # consumer's hook arrives, and what `setup` refuses to run without.
    for relative in layer.executables:
        (project / relative).chmod(0o755)

    _init_repo(project, layer.version)
    logger.info("assembled %s project at %s from bundles %s", layer.name, project, ", ".join(layer.bundles))

    install = run_make(logger, ["install"], check=False, dry_run=False, env=gate_env(), cwd=project)
    if install.returncode != 0:
        pytest.fail(_report(layer, "install", install))
    return Project(layer=layer, path=project, install=install)


def _report(layer: Layer, target: str, proc: subprocess.CompletedProcess) -> str:
    """Return a failure message carrying the whole gate output.

    A gate fails for a reason buried in a compiler or linter's own output, so the
    assertion has to carry it — the alternative is a bare exit code and a rerun.

    Args:
        layer: The layer being exercised.
        target: The make target that ran.
        proc: The completed process.

    Returns:
        A multi-line failure message.
    """
    return (
        f"`make {target}` failed on the {layer.name} layer (exit {proc.returncode}).\n"
        f"--- stdout ---\n{strip_ansi(proc.stdout)}\n"
        f"--- stderr ---\n{strip_ansi(proc.stderr)}"
    )


def gate(project: Project, target: str, logger, env: dict[str, str] | None = None) -> str:
    """Run one gate for real and fail the test with its output if it is red.

    Both streams are returned joined, because which one a gate writes to is not a
    property the tests should care about: make's own `printf` lines go to stdout,
    while cargo and go send progress and diagnostics to stderr (nextest reports every
    test it ran there). Asserting on stdout alone would make a test's outcome depend
    on a tool's stream choice rather than on whether the gate did its job.

    Args:
        project: The assembled project.
        target: The make target to run.
        logger: Test logger.
        env: Environment for the run, defaulting to `gate_env()`. Passed by tests
            that need a gate to face a different machine than the one running them —
            a PATH without the cargo bin directory, say.

    Returns:
        The gate's combined output, ANSI-stripped, for tests that assert on what ran.
    """
    proc = run_make(logger, [target], check=False, dry_run=False, env=env or gate_env(), cwd=project.path)
    if proc.returncode != 0:
        pytest.fail(_report(project.layer, target, proc))
    return strip_ansi(proc.stdout) + strip_ansi(proc.stderr)


def assert_hooks_passed(out: str, hooks: tuple[str, ...]) -> None:
    """Assert each named pre-commit hook ran and passed in a `make fmt` run.

    An exit code cannot distinguish "every hook passed" from "no hook had anything
    to look at": pre-commit exits 0 when a hook matches no files and prints
    ``Skipped`` instead. That is exactly how a config whose ``types``/``files``
    filters stopped matching would look, and on a language layer whose hooks are all
    filtered by file type (cargo fmt, gofmt, go vet) it is the likely failure mode.

    Args:
        out: `make fmt` stdout, ANSI-stripped.
        hooks: Hook names as pre-commit prints them at the start of each result line.
    """
    for hook in hooks:
        line = next((candidate for candidate in out.splitlines() if candidate.startswith(hook)), None)
        assert line is not None, f"`make fmt` never ran the {hook!r} hook:\n{out}"
        assert line.rstrip().endswith("Passed"), f"the {hook!r} hook did not pass: {line.rstrip()}"


def line_rate(coverage_xml: Path) -> float:
    """Return the overall line rate from a Cobertura report.

    All three layers are required to write Cobertura XML to the same path
    (`_tests/coverage.xml`) because book.mk's badge step reads exactly that, so
    one reader serves pytest-cov, `cargo llvm-cov --cobertura` and
    gocover-cobertura alike — which is the point worth asserting.

    Args:
        coverage_xml: Path to the report.

    Returns:
        The root element's ``line-rate`` as a float between 0 and 1.
    """
    root = ElementTree.parse(coverage_xml).getroot()
    return float(root.get("line-rate"))
