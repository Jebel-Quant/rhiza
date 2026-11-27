"""The shipped pytest.ini turns pytest's silent-pass warnings into errors (#1832).

Without ``--strict-markers`` a misspelled marker is a warning, so ``-m "not strss"`` deselects
nothing and the run stays green. Without ``--strict-config`` an unknown ini key is a warning,
which is how ``timeout = 60`` did nothing under a bare ``uv run pytest``: only pytest-timeout
knows the key, and only ``make test`` installs it. The key is gone; rhiza-task's ``test``
passes ``--timeout`` itself. Without ``xfail_strict`` a fixed bug hides behind its xfail.

Each test runs pytest in a scratch project carrying the bundle's own ``pytest.ini``, so what is
asserted is the behaviour consumers receive, not the presence of a string in a file.
"""

from __future__ import annotations

import configparser
import re
import shutil
import subprocess  # nosec B404 - fixed argument vectors
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
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
    assert "PytestConfigWarning" not in result.stdout + result.stderr


def test_an_unregistered_marker_fails_collection(tmp_path: Path) -> None:
    """``--strict-markers``: a typo'd marker is an error rather than a warning."""
    source = "import pytest\n\n@pytest.mark.strss\ndef test_marked():\n    assert True\n"
    result = _run(tmp_path, source)
    assert result.returncode != 0
    assert "'strss' not found in `markers`" in result.stdout + result.stderr


def test_an_unknown_ini_key_is_an_error(tmp_path: Path) -> None:
    """``--strict-config``: a key no plugin claims fails the run instead of being ignored."""
    result = _run(tmp_path, "def test_ok():\n    assert True\n", extra_ini="no_such_option = 1\n")
    assert result.returncode != 0
    assert "no_such_option" in result.stdout + result.stderr


def test_the_ini_carries_no_plugin_only_key() -> None:
    """The ini has no ``timeout`` key, the one only pytest-timeout knows.

    Under ``make test`` the plugin is installed, so strict config alone would not catch the
    key coming back -- but every bare ``uv run pytest`` would then fail on it.
    """
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(_INI, encoding="utf-8")
    assert "timeout" not in parser["pytest"]


def test_the_pinned_cli_supplies_the_timeout() -> None:
    """The timeout moved into rhiza-task, so the pinned version must actually supply one."""
    uvx = shutil.which("uvx")
    if uvx is None:
        pytest.skip("uvx not available; cannot ask the pinned CLI")
    makefile = (_ROOT / "bundles" / "core" / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^RHIZA_TASK \?= (\S+)", makefile, re.MULTILINE)
    assert match, "bundles/core/Makefile must pin RHIZA_TASK"
    result = subprocess.run(  # nosec B603
        [uvx, "-q", match.group(1), "print", "test_timeout"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        pytest.skip(f"cannot run {match.group(1)} (offline?): {result.stderr[-300:]}")
    assert int(result.stdout.strip()) > 0, f"{match.group(1)} supplies no per-test timeout"


def test_the_suite_collects_without_pytest_timeout() -> None:
    """``stress``, ``hypothesis-test`` and ``benchmark`` run pytest with no pytest-timeout.

    Under ``--strict-markers`` a ``@pytest.mark.timeout`` the ini does not register fails
    collection there. That broke the book build on main after #1835 -- PR CI never runs those
    tasks -- so it is asserted here, with the plugin switched off, over the whole suite.
    """
    result = subprocess.run(  # nosec B603
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-p",
            "no:timeout",
            "-p",
            "no:xdist",
            "-p",
            "no:cacheprovider",
            "tests",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    assert " collected" in result.stdout, "collected nothing, so this proves nothing"


def test_an_unexpected_pass_fails_the_run(tmp_path: Path) -> None:
    """``xfail_strict``: an xfail test that passes is reported as a failure."""
    source = "import pytest\n\n@pytest.mark.xfail\ndef test_fixed():\n    assert True\n"
    result = _run(tmp_path, source)
    assert result.returncode != 0
    assert "XPASS(strict)" in result.stdout
