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
