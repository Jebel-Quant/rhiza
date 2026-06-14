"""Fuzz the suppression-audit parser against arbitrary Python-like source text.

Run locally:
    RHIZA_FUZZ_ROOT=$(pwd) pip install atheris
    RHIZA_FUZZ_ROOT=$(pwd) python tests/fuzz/fuzz_suppression_audit.py -atheris_runs=10000

Run in ClusterFuzzLite: this file is built by .clusterfuzzlite/build.sh.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import atheris

# When running from the source tree (local development), add .rhiza/utils to
# sys.path so suppression_audit can be imported without installation.
# In ClusterFuzzLite, build.sh copies suppression_audit.py into tests/fuzz/
# before invoking PyInstaller, which allows PyInstaller to discover and bundle
# it into the frozen binary. At runtime inside the frozen binary, PyInstaller's
# import system loads the bundled copy regardless of filesystem paths.
_REPO_ROOT = Path(os.environ.get("RHIZA_FUZZ_ROOT", str(Path(__file__).resolve().parent.parent.parent)))
_utils_dir = str(_REPO_ROOT / ".rhiza" / "utils")
if _utils_dir not in sys.path:
    sys.path.insert(0, _utils_dir)

import suppression_audit  # noqa: E402


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
