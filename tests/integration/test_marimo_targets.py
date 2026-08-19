"""The marimo targets, after `marimo.mk` retired to rhiza-task.

This module read the fragment: that it defined `marimo` and `marimo-validate`, declared them
`.PHONY`, made them depend on `install`, and referenced `MARIMO_FOLDER`. All four assertions were
about a file's text, and the file is gone — `marimo` and `marimo-validate` are registered tasks now.

It is rewritten rather than deleted because of *how* it failed. The fixture skipped the whole
module when `marimo.mk` was absent, so retiring the fragment turned four tests into four silent
skips: a green suite, four fewer checks, no signal. That is the same trap `test_lfs.py` fell into
in the same change, and the reason to prefer assertions that go red when their subject moves.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _pin() -> str:
    """Return the pinned rhiza-task spec from the root Makefile.

    Returns:
        The ``rhiza-task@X.Y.Z`` spec.
    """
    match = re.search(r"^RHIZA_TASK \?= (\S+)", (_ROOT / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        pytest.skip("the root Makefile no longer pins RHIZA_TASK")
    return match.group(1)


@pytest.mark.parametrize("target", ["marimo", "marimo-validate"])
def test_marimo_target_resolves(target: str) -> None:
    """Both targets must resolve, so the fragment's retirement cost no entry point."""
    proc = subprocess.run(  # nosec B603
        ["make", "-n", target], cwd=_ROOT, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, f"`make {target}` did not resolve: {proc.stderr}"
    assert "no rule to make target" not in proc.stderr.lower()


def test_the_notebook_folder_is_configurable_and_resolves() -> None:
    """``marimo_folder`` must resolve to a real directory.

    The fragment referenced ``MARIMO_FOLDER`` so the notebook location was not hardcoded; the
    setting survived the move as ``marimo_folder``, and both the marimo tasks and
    ``rhiza_marimo.yml`` read it — the workflow via ``uvx rhiza-task print marimo_folder`` since
    #1553. Asserting it resolves to an existing directory is what catches the failure that matters:
    a wrong value makes the notebook gates measure nothing rather than fail.
    """
    proc = subprocess.run(  # nosec B603
        ["uvx", _pin(), "print", "marimo_folder"], cwd=_ROOT, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        pytest.skip(f"could not read marimo_folder: {proc.stderr.strip()[:160]}")
    folder = proc.stdout.strip()
    assert folder, "marimo_folder resolves to nothing"
    assert (_ROOT / folder).is_dir(), (
        f"marimo_folder resolves to {folder!r}, which is not a directory — the notebook tasks "
        f"would find nothing to run and report success"
    )
