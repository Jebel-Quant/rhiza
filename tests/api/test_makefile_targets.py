"""Tests for the Makefile targets and help output using safe dry-runs.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

These tests validate that the Makefile exposes expected targets and emits
the correct commands without actually executing them, by invoking `make -n`
(dry-run). We also pass `-s` to reduce noise in CI logs. This approach keeps
tests fast, portable, and free of side effects like network or environment
changes.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

from tests.util import run_make, strip_ansi


def assert_uvx_command_uses_version(output: str, tmp_path, command_fragment: str):
    """Assert uvx command uses .python-version when present, else fallback checks."""
    python_version_file = tmp_path / ".python-version"
    if python_version_file.exists():
        python_version = python_version_file.read_text().strip()
        assert f"uvx -p {python_version} {command_fragment}" in output
    else:
        assert "uvx -p" in output
        assert command_fragment in output


class TestMakefile:
    """Smoke tests for Makefile help and common targets using make -n."""

    def test_default_goal_is_help(self, logger):
        """Default goal should render the help index with known targets."""
        proc = run_make(logger)
        out = proc.stdout
        assert "Usage:" in out
        assert "Targets:" in out
        # ensure a few known targets appear in the help index
        for target in ["install", "fmt", "deps", "test", "help"]:
            assert target in out

    def test_help_target(self, logger):
        """Explicit `make help` prints usage, targets, and section headers."""
        proc = run_make(logger, ["help"])
        out = proc.stdout
        assert "Usage:" in out
        assert "Targets:" in out
        assert "Bootstrap" in out or "Meta" in out  # section headers

    def test_doctor_target_appears_in_help(self, logger):
        """Doctor target should appear in help under the Dev section."""
        proc = run_make(logger, ["help"])
        out = proc.stdout
        assert "Dev" in out
        assert "doctor" in out

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="uses POSIX '#!/usr/bin/env sh' fake-bin scripts on a ':'-separated PATH; unsupported on Windows",
    )
    def test_doctor_markers_are_ascii(self, logger):
        """`doctor`'s status markers must be ASCII, on every platform.

        They were ✅/❌ until the Windows jobs showed what that costs: mingw's printf does
        not pass the UTF-8 literals through intact, so the markers reached the CI log — and
        any test reading them — as cp1252 mojibake (`â`, `Œ` for the bytes of ❌). That was
        true before any test asserted on them; it was simply invisible.

        A diagnostic is the last place to spend a portability budget on decoration, so the
        markers are plain text and this pins them that way.
        """
        out = strip_ansi(run_make(logger, ["doctor"], dry_run=False, check=False).stdout)
        assert "[ OK ]" in out, f"doctor did not report a passing check:\n{out!r}"
        assert out.isascii(), f"doctor emitted non-ASCII, which Windows mangles:\n{out!r}"

    def test_doctor_fails_when_minimum_version_is_not_met(self, logger, tmp_path):
        """Doctor should exit non-zero when a prerequisite version is below the minimum."""
        fake_bin = tmp_path / "fake-bin"
        fake_bin.mkdir(exist_ok=True)

        for name, content in {
            "uv": "#!/usr/bin/env sh\necho 'uv 0.3.0'\n",
            "python": "#!/usr/bin/env sh\necho 'Python 3.12.2'\n",
            "make": "#!/usr/bin/env sh\necho 'GNU Make 4.4.1'\n",
            "git": "#!/usr/bin/env sh\necho 'git version 2.44.0'\n",
        }.items():
            script = fake_bin / name
            script.write_text(content)
            script.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"

        proc = run_make(logger, ["doctor"], dry_run=False, check=False, env=env)
        out = strip_ansi(proc.stdout)
        assert proc.returncode != 0
        assert "[FAIL] uv" in out
        assert "0.3.0" in out
        assert "0.4.0" in out

    def test_fmt_target_dry_run(self, logger, tmp_path):
        """Fmt target should invoke pre-commit via uvx with Python version in dry-run output."""
        # Create clean environment without PYTHON_VERSION so Makefile reads from .python-version
        env = os.environ.copy()
        env.pop("PYTHON_VERSION", None)

        proc = run_make(logger, ["fmt"], env=env)
        out = proc.stdout
        assert "prek run --all-files" in out, "fmt should run prek over every file"

    def test_deptry_target_dry_run(self, logger, tmp_path):
        """Deptry target should invoke deptry via uvx with Python version in dry-run output."""
        # Create a mock SOURCE_FOLDER directory so the deptry command runs
        source_folder = tmp_path / "src"
        source_folder.mkdir(exist_ok=True)

        # Update .env to set SOURCE_FOLDER
        env_file = tmp_path / ".rhiza" / ".env"
        env_content = env_file.read_text()
        env_content += "\nSOURCE_FOLDER=src\n"
        env_file.write_text(env_content)

        # Create clean environment without PYTHON_VERSION so Makefile reads from .python-version
        env = os.environ.copy()
        env.pop("PYTHON_VERSION", None)

        proc = run_make(logger, ["deps"], env=env)

        out = proc.stdout
        assert_uvx_command_uses_version(out, tmp_path, "deptry src")

    def test_typecheck_target_dry_run(self, logger):
        """Typecheck target should invoke ty and mypy via uv run, self-provisioned with --with."""
        proc = run_make(logger, ["typecheck"])
        out = proc.stdout
        # Both type checkers are invoked, each provisioned on the fly so a clean
        # .venv (lockfile only, no pre-installed ty/mypy) still runs the gate.
        assert "uv run --with ty ty check" in out
        assert "uv run --with mypy mypy --strict" in out

    def test_test_target_dry_run(self, logger):
        """Test target should invoke pytest via uv with coverage and HTML outputs in dry-run output."""
        proc = run_make(logger, ["test"])
        out = proc.stdout
        # Expect key steps
        assert "mkdir -p _tests/html-coverage _tests/html-report" in out
        # Check for uv command running pytest with its plugins provisioned on the fly
        assert "uv run --with pytest" in out
        assert "--with pytest-cov" in out
        # Check for XML coverage report
        assert "--cov-report=xml:_tests/coverage.xml" in out

    def test_test_target_without_source_folder(self, logger, tmp_path):
        """Test target should run without coverage when no coverage folder resolves.

        Asserts the *resolved scope* rather than the shell that computes it. This test
        used to pin the literal `if [ -d nonexistent_src ]`, which #1516 replaced with the
        COVERAGE_FOLDERS accumulator every other path-scoped gate already used — so it was
        testing the wiring, and broke on a change that preserved the behaviour exactly.
        `coverage_paths` is expanded by make, so a dry run shows the real scope.
        """
        # Update .env to set SOURCE_FOLDER to a non-existent directory
        env_file = tmp_path / ".rhiza" / ".env"
        env_content = env_file.read_text()
        env_content += "\nSOURCE_FOLDER=nonexistent_src\n"
        env_file.write_text(env_content)

        # Create tests folder
        tests_folder = tmp_path / "tests"
        tests_folder.mkdir(exist_ok=True)

        proc = run_make(logger, ["test"])
        out = proc.stdout
        # The accumulator seeds itself only from a SOURCE_FOLDER that exists, so nothing
        # contributes one here and the gate measures no coverage.
        assert 'coverage_paths=""' in out
        # Should still run pytest, and still write the HTML test report.
        assert "uv run --with pytest" in out
        assert "--html=_tests/html-report/report.html" in out

    def test_test_target_measures_the_source_folder_when_it_exists(self, logger, tmp_path):
        """The default case: an existing SOURCE_FOLDER seeds COVERAGE_FOLDERS by itself.

        The companion to the test above, and the reason #1516 is not a behaviour change
        for a project laid out conventionally: it gets exactly the previous scope without
        setting anything.
        """
        (tmp_path / "src").mkdir(exist_ok=True)
        (tmp_path / "tests").mkdir(exist_ok=True)

        proc = run_make(logger, ["test"])
        out = proc.stdout
        assert 'coverage_paths="src"' in out
        assert "--cov-fail-under=" in out

    def test_docs_coverage_target_dry_run(self, logger):
        """Docs coverage should run interrogate over the docstring paths."""
        proc = run_make(logger, ["docs-coverage"])
        out = proc.stdout
        assert "uv run --with interrogate interrogate" in out

    def test_security_target_runs_bandit(self, logger):
        """Security target should run bandit (or skip with a warning)."""
        proc = run_make(logger, ["security"])
        out = proc.stdout
        assert "rhiza-tools" not in out
        assert "pip-audit" not in out
        assert "Running bandit security scan in:" in out
        assert "No bandit scan folders found" in out

    def test_benchmark_target_dry_run(self, logger):
        """Benchmark target should run pytest in benchmark-only mode against the benchmarks folder."""
        proc = run_make(logger, ["benchmark"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        assert "/benchmarks/" in out
        assert "--benchmark-only" in out

    def test_stress_target_dry_run(self, logger):
        """Stress target should run pytest selecting the stress marker."""
        proc = run_make(logger, ["stress"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        assert "uv run --with pytest" in out
        assert "-m stress" in out

    def test_hypothesis_test_target_dry_run(self, logger):
        """Hypothesis-test target should run pytest selecting property-based tests with statistics."""
        proc = run_make(logger, ["hypothesis-test"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        assert '-m "hypothesis or property"' in out
        assert "--hypothesis-show-statistics" in out

    def test_mutation_target_dry_run(self, logger):
        """Mutation target should run mutmut against SOURCE_FOLDER with the tests directory."""
        proc = run_make(logger, ["mutation"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        assert "mutmut run" in out
        assert "--paths-to-mutate=" in out

    def test_test_pyproject_target_dry_run(self, logger):
        """Test-pyproject runs the one installed check by module name, not by path.

        Since #1540 the check is a module in pytest-rhiza rather than a file the template
        syncs, so there is nothing in the tree for pytest to be pointed at — the shortcut
        has to name it the way `rhiza-test` does, with `--pyargs`.
        """
        proc = run_make(logger, ["test-pyproject"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        assert "pytest-rhiza==" in out, f"the shortcut no longer installs the pinned checks:\n{out}"
        assert "pytest --pyargs pytest_rhiza.checks.test_pyproject" in out

    def test_all_target_chains_ci_subtargets(self, logger):
        """The `all` aggregator should chain the CI sub-targets (fmt, test, docs-coverage, security)."""
        proc = run_make(logger, ["all"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        # Markers proving the prerequisite chain expands each sub-target's recipe.
        assert "prek run --all-files" in out  # fmt
        assert "uv run --with pytest" in out  # test
        assert "pytest --pyargs" in out  # rhiza-test
        assert "uv run --with interrogate interrogate" in out  # docs-coverage
        assert "Running bandit security scan in:" in out  # security

    def test_python_version_defaults_to_3_13_if_missing(self, logger, tmp_path):
        """`PYTHON_VERSION` should default to `3.13` if .python-version is missing."""
        # Ensure .python-version does not exist
        python_version_file = tmp_path / ".python-version"
        if python_version_file.exists():
            python_version_file.unlink()

        # Create clean environment without PYTHON_VERSION
        env = os.environ.copy()
        env.pop("PYTHON_VERSION", None)

        proc = run_make(logger, ["print-PYTHON_VERSION"], dry_run=False, env=env)
        out = strip_ansi(proc.stdout)
        assert "Value of PYTHON_VERSION:\n3.13" in out

    def test_uv_no_modify_path_is_exported(self, logger):
        """`UV_NO_MODIFY_PATH` should be set to `1` in the Makefile."""
        proc = run_make(logger, ["print-UV_NO_MODIFY_PATH"], dry_run=False)
        out = strip_ansi(proc.stdout)
        assert "Value of UV_NO_MODIFY_PATH:\n1" in out

    def test_that_target_coverage_is_configurable(self, logger):
        """Test target should respond to COVERAGE_FAIL_UNDER variable."""
        # Default case: ensure the flag is present
        proc = run_make(logger, ["test"])
        assert "--cov-fail-under=" in proc.stdout

        # Override case: ensure the flag takes the specific value
        proc_override = run_make(logger, ["test", "COVERAGE_FAIL_UNDER=42"])
        assert "--cov-fail-under=42" in proc_override.stdout

    def test_license_target_dry_run(self, logger):
        """License target should invoke pip-licenses via uv run --with in dry-run output."""
        proc = run_make(logger, ["license"])
        out = proc.stdout
        assert "uv run --with pip-licenses pip-licenses" in out
        assert "--fail-on=" in out
        assert "GPL" in out

    def test_license_fail_on_is_configurable(self, logger):
        """License target should use the LICENSE_FAIL_ON variable for the fail-on list."""
        proc = run_make(logger, ["license", "LICENSE_FAIL_ON=MIT;Apache"])
        out = proc.stdout
        assert '--fail-on="MIT;Apache"' in out

    def test_semgrep_target_dry_run(self, logger):
        """Semgrep target should invoke semgrep against SOURCE_FOLDER with the rhiza config."""
        proc = run_make(logger, ["semgrep"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        assert "Running Semgrep" in out
        assert "semgrep --config .rhiza/semgrep.yml" in out

    def test_todos_target_dry_run(self, logger):
        """Todos target should grep the codebase for TODO/FIXME/HACK markers."""
        proc = run_make(logger, ["todos"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        assert "(TODO|FIXME|HACK):" in out
        assert "grep -nHE" in out

    def test_serve_target_uses_uv_run_python_http_server(self, logger):
        """Serve target should use uv run instead of directly calling python3."""
        proc = run_make(logger, ["serve"])
        out = proc.stdout
        assert "uv run python -m http.server 8000" in out


class TestMakefileRootFixture:
    """What this repo's own root Makefile must be, now that it is the rhiza-task shim.

    Every other test in this module runs against a tmp_path assembled from ``bundles/``, so
    they assert what a *consumer* receives. These two assert what the *mother repo* runs,
    and the two answers deliberately differ: rhiza migrated to the shim first so the
    dogfooding proves it before any consumer is affected.

    The assertion that used to live here grepped the Makefile and its ``.rhiza/make.d``
    fragments for ``install:``/``fmt:``/``test:``/``deps:``. That cannot survive the shim and
    should not: the whole point is that those names are *not* in the file any more -- a `%:`
    catch-all forwards them to the CLI. Grepping for target names would have to be deleted
    or weakened on every migration; asserting the forwarding contract holds instead.
    """

    def test_makefile_exists_at_root(self, root: Path) -> None:
        """Makefile should exist at repository root, and be a real file, not a symlink.

        It stopped being a dogfood symlink into ``bundles/core/`` when it became the shim:
        it now carries this repo's own ``e2e``/``sync-self`` targets, which must not ship.
        """
        makefile = root / "Makefile"
        assert makefile.is_file()
        assert not makefile.is_symlink(), (
            "the root Makefile is repo-owned now -- a symlink into bundles/core/ would ship "
            "rhiza's own mother-repo targets to every consumer"
        )

    def test_makefile_forwards_unknown_targets_to_a_pinned_cli(self, root: Path) -> None:
        """The shim's contract: a catch-all rule, a pinned version, and no gate recipes."""
        content = (root / "Makefile").read_text(encoding="utf-8")

        assert re.search(r"^RHIZA_TASK \?= rhiza-task@\d+\.\d+\.\d+", content, re.MULTILINE), (
            "the shim must pin rhiza-task to an exact version: an unpinned CLI is a gate that moves under you"
        )
        assert re.search(r"^%:", content, re.MULTILINE), "without the `%:` catch-all no gate resolves at all"

    def test_makefile_keeps_the_mother_repo_only_targets(self, root: Path) -> None:
        """The five targets rehomed from the retired .rhiza/make.d/bundles.mk.

        They live in the Makefile rather than ``local.mk`` because ``local.mk`` is
        gitignored and CI invokes two of them -- ``make e2e`` from rhiza_e2e.yml and
        ``make gitlab-docker-test`` from rhiza_weekly.yml.
        """
        content = (root / "Makefile").read_text(encoding="utf-8")
        for target in ("explain-bundles", "sync-self", "sync-self-check", "e2e", "gitlab-docker-test"):
            assert re.search(rf"^{re.escape(target)}:", content, re.MULTILINE), (
                f"`{target}` must be an explicit rule -- the `%:` catch-all would otherwise "
                f"forward it to the CLI, which has no such task"
            )
