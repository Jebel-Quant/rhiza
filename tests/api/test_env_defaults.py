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


class TestExportedCiOsMatrixSurvivesAPresentEnvFile:
    """Pin the precedence `.github/workflows/rhiza_ci.yml` depends on (#1545).

    The workflow selects the CI matrix per caller by *exporting* RHIZA_CI_OS_MATRIX:
    the mother repo opts itself into macOS, every consumer gets an empty string and
    falls through to the single-OS default (#1526). That only works while no
    `.rhiza/.env` in scope assigns the variable.

    Core once shipped one that did. `bundles/core/.rhiza/.env` pinned all three OSes
    with a plain `=`, and a makefile assignment outranks an environment variable in
    GNU make — so the workflow's value was discarded and everyone, mother repo and
    consumers alike, ran the full three-OS matrix.

    The tests that existed then could not catch it: each one either deletes
    `.rhiza/.env` or strips the variable from the environment, and
    `tests/api/test_ci_workflow.py` passes it as a command-line `make VAR=...`, which
    outranks the file. None ever combined a populated `.env` with an exported
    variable, which is the one configuration CI actually runs in. These do.

    Core now ships no `.rhiza/.env` — `test_core_ships_no_env_file_at_all` pins that,
    and it is the structural fix. What these two still cover is the case that fix does
    not reach: a **consumer's own** `.rhiza/.env`, which rhiza.mk still includes. The
    fixture supplies one carrying an unrelated setting, so a file being present for
    its own reasons must not break the hand-off.
    """

    def test_exported_value_wins_over_a_present_env_file(self, logger, tmp_path):
        """An exported RHIZA_CI_OS_MATRIX must survive a present .rhiza/.env.

        This is the mother-repo path: the workflow exports ubuntu+macos and expects
        to get it back.
        """
        assert (tmp_path / ".rhiza" / ".env").exists(), "fixture should have provided a .rhiza/.env"
        env = {**os.environ, "RHIZA_CI_OS_MATRIX": '["ubuntu-latest","macos-latest"]'}
        proc = run_make(logger, ["ci-os-matrix"], dry_run=False, env=env)
        assert strip_ansi(proc.stdout).strip() == '["ubuntu-latest","macos-latest"]'

    def test_exported_empty_value_falls_back_to_the_single_os_default(self, logger, tmp_path):
        """An exported empty string must fall back to the single-OS default.

        This is the consumer path. `?=` treats an exported empty string as *set*, so
        the recipe resolves through `$(or ...)` to get the fallback — and a present
        `.env` must not pre-empt that with a value of its own.
        """
        assert (tmp_path / ".rhiza" / ".env").exists(), "fixture should have provided a .rhiza/.env"
        env = {**os.environ, "RHIZA_CI_OS_MATRIX": ""}
        proc = run_make(logger, ["ci-os-matrix"], dry_run=False, env=env)
        assert strip_ansi(proc.stdout).strip() == _DEFAULT_CI_OS_MATRIX

    def test_core_ships_no_env_file_at_all(self, root: Path):
        """Core must ship no `.rhiza/.env`, which is what makes #1545 unrepeatable.

        This replaces an assertion that the shipped file merely left
        RHIZA_CI_OS_MATRIX unset. Checking one line inside the file treated the
        pinning as the bug; the bug was that a *template-owned* makefile fragment
        could name any variable at all, because a makefile assignment outranks an
        exported environment variable and so removes it from the workflow's reach.
        The two values it did carry — SOURCE_FOLDER, MARIMO_FOLDER — were identical
        to rhiza.mk's `?=` defaults, so deleting the file changed no resolved value
        and removed the only mechanism by which a synced file could shadow a caller.

        Asserted against the bundle source, so the failure names the cause directly
        if someone reinstates the file. A *consumer's own* .rhiza/.env stays
        supported: rhiza.mk still `-include`s it, and the two tests above pin that a
        present file does not break the matrix hand-off.
        """
        shipped = root / "bundles" / "core" / ".rhiza" / ".env"
        assert not shipped.exists(), (
            f"{shipped} must not exist: a template-owned assignment outranks the export "
            f"rhiza_ci.yml uses to select the matrix per caller (#1526, #1545). Project "
            f"settings belong in a [tool.rhiza-task] table in pyproject.toml."
        )
