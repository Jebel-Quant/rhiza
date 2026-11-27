"""The shipped pytest.ini turns pytest's silent-pass warnings into errors (#1832).

Without ``--strict-markers`` a misspelled marker is a warning, so ``-m "not strss"`` deselects
nothing and the run stays green. (``--strict-config`` follows once the
``timeout`` key moves into rhiza-task's ``test`` task; until then it would break a bare
``uv run pytest``.) Without ``xfail_strict`` a fixed bug hides behind its xfail.

Each test runs pytest in a scratch project carrying the bundle's own ``pytest.ini``, so what is
asserted is the behaviour consumers receive, not the presence of a string in a file.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 - fixed argument vectors
import sys
from pathlib import Path

_INI = Path(__file__).resolve().parents[2] / "bundles" / "python-core" / "pytest.ini"


def _run(tmp_path: Path, test_source: str, extra_ini: str = "") -> subprocess.CompletedProcess[str]:
    """Run pytest on one test module under the bundle's pytest.ini.

    Args:
        tmp_path: Scratch directory to use as the project root.
        test_source: Source of ``tests/test_probe.py``.
        extra_ini: Lines appended to the copied pytest.ini.

    Returns:
        The completed pytest process.
    """
    shutil.copyfile(_INI, tmp_path / "pytest.ini")
    if extra_ini:
        with (tmp_path / "pytest.ini").open("a", encoding="utf-8") as fh:
            fh.write(extra_ini)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_probe.py").write_text(test_source, encoding="utf-8")
    return subprocess.run(  # nosec B603
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-p", "no:xdist"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_the_ini_runs_clean(tmp_path: Path) -> None:
    """Positive control: a plain passing test passes, so the failures below are the rules biting."""
    result = _run(tmp_path, "def test_ok():\n    assert True\n")
    assert result.returncode == 0, result.stdout + result.stderr


def test_an_unregistered_marker_fails_collection(tmp_path: Path) -> None:
    """``--strict-markers``: a typo'd marker is an error rather than a warning."""
    source = "import pytest\n\n@pytest.mark.strss\ndef test_marked():\n    assert True\n"
    result = _run(tmp_path, source)
    assert result.returncode != 0
    assert "'strss' not found in `markers`" in result.stdout + result.stderr


def test_an_unexpected_pass_fails_the_run(tmp_path: Path) -> None:
    """``xfail_strict``: an xfail test that passes is reported as a failure."""
    source = "import pytest\n\n@pytest.mark.xfail\ndef test_fixed():\n    assert True\n"
    result = _run(tmp_path, source)
    assert result.returncode != 0
    assert "XPASS(strict)" in result.stdout
