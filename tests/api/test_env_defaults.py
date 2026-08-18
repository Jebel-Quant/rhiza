"""Tests that Makefile variable defaults are applied when .rhiza/.env is absent.

Verifies that SOURCE_FOLDER, MARIMO_FOLDER, and RHIZA_CI_OS_MATRIX have sensible
built-in defaults so that .rhiza/.env is truly optional.
"""

from __future__ import annotations

import os
from pathlib import Path

from tests.util import run_make, strip_ansi

_DEFAULT_SOURCE_FOLDER = "src"
_DEFAULT_MARIMO_FOLDER = "docs/notebooks"
_DEFAULT_CI_OS_MATRIX = '["ubuntu-latest"]'


def _remove_env_file(tmp_path: Path) -> None:
    """Remove .rhiza/.env from the test directory so defaults kick in."""
    env_file = tmp_path / ".rhiza" / ".env"
    if env_file.exists():
        env_file.unlink()


class TestEnvFileOptional:
    """Verify that .rhiza/.env is optional and built-in defaults apply when absent."""

    def test_source_folder_default_without_env(self, logger, tmp_path):
        """SOURCE_FOLDER should default to 'src' when .rhiza/.env is absent."""
        _remove_env_file(tmp_path)
        env = {k: v for k, v in os.environ.items() if k != "SOURCE_FOLDER"}
        proc = run_make(logger, ["print-SOURCE_FOLDER"], dry_run=False, env=env)
        out = strip_ansi(proc.stdout)
        assert f"Value of SOURCE_FOLDER:\n{_DEFAULT_SOURCE_FOLDER}" in out

    def test_marimo_folder_default_without_env(self, logger, tmp_path):
        """MARIMO_FOLDER should default to 'docs/notebooks' when .rhiza/.env is absent."""
        _remove_env_file(tmp_path)
        env = {k: v for k, v in os.environ.items() if k != "MARIMO_FOLDER"}
        proc = run_make(logger, ["print-MARIMO_FOLDER"], dry_run=False, env=env)
        out = strip_ansi(proc.stdout)
        assert f"Value of MARIMO_FOLDER:\n{_DEFAULT_MARIMO_FOLDER}" in out

    def test_rhiza_ci_os_matrix_default_without_env(self, logger, tmp_path):
        r"""RHIZA_CI_OS_MATRIX should default to [\"ubuntu-latest\"] when .rhiza/.env is absent."""
        _remove_env_file(tmp_path)
        env = {k: v for k, v in os.environ.items() if k != "RHIZA_CI_OS_MATRIX"}
        # Use ci-os-matrix rather than print-% — it wraps the value in single quotes
        # so the JSON double-quotes are preserved in the shell output.
        proc = run_make(logger, ["ci-os-matrix"], dry_run=False, env=env)
        out = strip_ansi(proc.stdout).strip()
        assert out == _DEFAULT_CI_OS_MATRIX

    def test_env_file_overrides_default_source_folder(self, logger, tmp_path):
        """A value in .rhiza/.env should override the built-in SOURCE_FOLDER default."""
        env_file = tmp_path / ".rhiza" / ".env"
        env_file.write_text("SOURCE_FOLDER=custom_src\n")
        env = {k: v for k, v in os.environ.items() if k != "SOURCE_FOLDER"}
        proc = run_make(logger, ["print-SOURCE_FOLDER"], dry_run=False, env=env)
        out = strip_ansi(proc.stdout)
        assert "Value of SOURCE_FOLDER:\ncustom_src" in out

    def test_env_file_overrides_default_marimo_folder(self, logger, tmp_path):
        """A value in .rhiza/.env should override the built-in MARIMO_FOLDER default."""
        env_file = tmp_path / ".rhiza" / ".env"
        env_file.write_text("MARIMO_FOLDER=notebooks\n")
        env = {k: v for k, v in os.environ.items() if k != "MARIMO_FOLDER"}
        proc = run_make(logger, ["print-MARIMO_FOLDER"], dry_run=False, env=env)
        out = strip_ansi(proc.stdout)
        assert "Value of MARIMO_FOLDER:\nnotebooks" in out

    def test_env_file_overrides_default_ci_os_matrix(self, logger, tmp_path):
        """A value in .rhiza/.env should override the built-in RHIZA_CI_OS_MATRIX default."""
        env_file = tmp_path / ".rhiza" / ".env"
        env_file.write_text('RHIZA_CI_OS_MATRIX=["ubuntu-latest","macos-latest"]\n')
        env = {k: v for k, v in os.environ.items() if k != "RHIZA_CI_OS_MATRIX"}
        # Use ci-os-matrix rather than print-% — it wraps the value in single quotes
        # so the JSON double-quotes are preserved in the shell output.
        proc = run_make(logger, ["ci-os-matrix"], dry_run=False, env=env)
        out = strip_ansi(proc.stdout).strip()
        assert out == '["ubuntu-latest","macos-latest"]'


class TestExportedCiOsMatrixSurvivesTheShippedEnvFile:
    """Pin the precedence `.github/workflows/rhiza_ci.yml` depends on (#1545).

    The workflow selects the CI matrix per caller by *exporting* RHIZA_CI_OS_MATRIX:
    the mother repo opts itself into macOS, every consumer gets an empty string and
    falls through to the single-OS default (#1526). That only works while the shipped
    `.rhiza/.env` leaves the variable unset.

    It did not. `bundles/core/.rhiza/.env` pinned all three OSes with a plain `=`,
    and a makefile assignment outranks an environment variable in GNU make — so the
    workflow's value was discarded and everyone, mother repo and consumers alike, ran
    the full three-OS matrix.

    The existing tests could not catch it: each one either deletes `.rhiza/.env` or
    strips the variable from the environment, and `tests/api/test_ci_workflow.py`
    passes it as a command-line `make VAR=...`, which outranks the file. None of the
    three ever combined a populated `.env` with an exported variable, which is the
    one configuration CI actually runs in. These tests do.
    """

    def test_exported_value_wins_over_the_shipped_env_file(self, logger, tmp_path):
        """An exported RHIZA_CI_OS_MATRIX must survive the shipped .rhiza/.env.

        This is the mother-repo path: the workflow exports ubuntu+macos and expects
        to get it back.
        """
        assert (tmp_path / ".rhiza" / ".env").exists(), "fixture should have copied the shipped .env"
        env = {**os.environ, "RHIZA_CI_OS_MATRIX": '["ubuntu-latest","macos-latest"]'}
        proc = run_make(logger, ["ci-os-matrix"], dry_run=False, env=env)
        assert strip_ansi(proc.stdout).strip() == '["ubuntu-latest","macos-latest"]'

    def test_exported_empty_value_falls_back_to_the_single_os_default(self, logger, tmp_path):
        """An exported empty string must fall back to the single-OS default.

        This is the consumer path. `?=` treats an exported empty string as *set*, so
        the recipe resolves through `$(or ...)` to get the fallback — and the shipped
        `.env` must not pre-empt that with a value of its own.
        """
        assert (tmp_path / ".rhiza" / ".env").exists(), "fixture should have copied the shipped .env"
        env = {**os.environ, "RHIZA_CI_OS_MATRIX": ""}
        proc = run_make(logger, ["ci-os-matrix"], dry_run=False, env=env)
        assert strip_ansi(proc.stdout).strip() == _DEFAULT_CI_OS_MATRIX

    def test_shipped_env_file_does_not_pin_the_matrix(self, root: Path):
        """The shipped .env must not assign RHIZA_CI_OS_MATRIX at all.

        Asserted against the bundle source rather than the behaviour above, so the
        failure names the cause directly if someone reinstates the line.
        """
        shipped = root / "bundles" / "core" / ".rhiza" / ".env"
        assignments = [
            line for line in shipped.read_text().splitlines() if line.strip().startswith("RHIZA_CI_OS_MATRIX")
        ]
        assert assignments == [], (
            f"{shipped} must leave RHIZA_CI_OS_MATRIX unset so rhiza_ci.yml can select "
            f"the matrix per caller (#1526, #1545); found: {assignments}"
        )
