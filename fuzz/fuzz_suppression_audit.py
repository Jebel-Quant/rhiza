"""Fuzz the suppression-audit parser against arbitrary Python-like source text.

Run locally:
    RHIZA_FUZZ_ROOT=$(pwd) pip install atheris
    RHIZA_FUZZ_ROOT=$(pwd) python fuzz/fuzz_suppression_audit.py -atheris_runs=10000

Run in ClusterFuzzLite: this file is built by .clusterfuzzlite/build.sh.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import atheris

_REPO_ROOT = Path(os.environ.get("RHIZA_FUZZ_ROOT", "/src/rhiza"))
_MODULE_PATH = _REPO_ROOT / ".rhiza" / "utils" / "suppression_audit.py"
_MODULE_SPEC = importlib.util.spec_from_file_location("rhiza_suppression_audit", _MODULE_PATH)
_LOAD_ERROR = "Unable to load suppression_audit.py"

if _MODULE_SPEC is None or _MODULE_SPEC.loader is None:
    raise ImportError(_LOAD_ERROR)

suppression_audit = importlib.util.module_from_spec(_MODULE_SPEC)
sys.modules[_MODULE_SPEC.name] = suppression_audit
_MODULE_SPEC.loader.exec_module(suppression_audit)


def test_one_input(data: bytes) -> None:
    """Exercise the tokenizer and suppression extraction on arbitrary source text."""
    source = data.decode("utf-8", errors="replace")
    with tempfile.TemporaryDirectory() as tmpdir:
        candidate = Path(tmpdir) / "candidate.py"
        candidate.write_text(source, encoding="utf-8", errors="replace")
        suppressions = suppression_audit.scan_file(candidate)
        suppression_audit.count_non_empty_lines(candidate)
        suppression_audit._nosec_cves(suppressions)
        suppression_audit.compute_grade(float(len(suppressions)))


def main() -> None:
    """Run the Atheris fuzz loop."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
