"""Smoke tests for .rhiza/utils/explain_bundles.py."""

from __future__ import annotations

import subprocess  # nosec B404 - subprocess execution is limited to local repo script
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / ".rhiza" / "utils" / "explain_bundles.py"


def test_explain_bundles_script_runs_and_prints_sections() -> None:
    """The explain-bundles utility should run and print top-level section headers."""
    result = subprocess.run([sys.executable, str(_SCRIPT)], capture_output=True, text=True, check=False)  # nosec B603

    assert result.returncode == 0, result.stderr
    assert "Bundles" in result.stdout
    assert "Profiles" in result.stdout
