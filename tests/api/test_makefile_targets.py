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
import sys

import pytest

from tests.api.conftest import SPLIT_MAKEFILES
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
        for target in ["install", "fmt", "deptry", "test", "help"]:
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
        assert "[❌] uv" in out
        assert "0.3.0" in out
        assert "0.4.0" in out

    def test_fmt_target_dry_run(self, logger, tmp_path):
        """Fmt target should invoke pre-commit via uvx with Python version in dry-run output."""
        # Create clean environment without PYTHON_VERSION so Makefile reads from .python-version
        env = os.environ.copy()
        env.pop("PYTHON_VERSION", None)

        proc = run_make(logger, ["fmt"], env=env)
        out = proc.stdout
        assert_uvx_command_uses_version(out, tmp_path, "pre-commit run --all-files")

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

        proc = run_make(logger, ["deptry"], env=env)

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
        """Test target should run without coverage when SOURCE_FOLDER doesn't exist."""
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
        # Should see warning about missing source folder
        assert "if [ -d nonexistent_src ]" in out
        # Should still run pytest but without coverage flags
        assert "uv run --with pytest" in out
        assert "--html=_tests/html-report/report.html" in out

    def test_docs_coverage_target_dry_run(self, logger):
        """Docs coverage should run interrogate over the docstring paths."""
        proc = run_make(logger, ["docs-coverage"])
        out = proc.stdout
        assert "uv run --with interrogate interrogate" in out

    def test_security_target_runs_pip_audit_and_bandit(self, logger):
        """Security target should run pip-audit via rhiza-tools and bandit (or skip warning)."""
        proc = run_make(logger, ["security"])
        out = proc.stdout
        assert "rhiza-tools" in out
        assert "pip-audit" in out
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
        """Test-pyproject target should run the pyproject structure test module via pytest."""
        proc = run_make(logger, ["test-pyproject"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        assert "uv run --with pytest pytest .rhiza/tests/test_pyproject.py" in out

    def test_all_target_chains_ci_subtargets(self, logger):
        """The `all` aggregator should chain the CI sub-targets (fmt, test, docs-coverage, security)."""
        proc = run_make(logger, ["all"])
        out = proc.stdout
        assert "no rule to make target" not in proc.stderr.lower()
        # Markers proving the prerequisite chain expands each sub-target's recipe.
        assert "pre-commit run --all-files" in out  # fmt
        assert "uv run --with pytest" in out  # test / rhiza-test
        assert "uv run --with interrogate interrogate" in out  # docs-coverage
        assert "pip-audit" in out  # security

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
    """Tests for root fixture usage in Makefile tests."""

    def test_makefile_exists_at_root(self, root):
        """Makefile should exist at repository root."""
        makefile = root / "Makefile"
        assert makefile.exists()
        assert makefile.is_file()

    def test_makefile_contains_targets(self, root):
        """Makefile should contain expected targets (including split files)."""
        makefile = root / "Makefile"
        content = makefile.read_text(encoding="utf-8")

        # Read split Makefiles as well (they contain non-ASCII glyphs, so decode as UTF-8
        # explicitly — Windows' default cp1252 codec would choke on them).
        for split_file in SPLIT_MAKEFILES:
            split_path = root / split_file
            if split_path.exists():
                content += "\n" + split_path.read_text(encoding="utf-8")

        expected_targets = ["install", "fmt", "test", "deptry", "help"]
        for target in expected_targets:
            assert f"{target}:" in content or f".PHONY: {target}" in content
