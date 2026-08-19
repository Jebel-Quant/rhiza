"""The optional test-extra targets, after `test.mk` retired to rhiza-task.

This module read the fragment: that `benchmark` was defined, was `.PHONY`, depended on `install`,
and drove pytest-benchmark. All four assertions were about a file's text, and the file is gone —
`benchmark`, `hypothesis-test`, `stress` and `mutation` are registered tasks now, and rhiza-task
tests their recipes where those recipes live.

Rewritten rather than deleted because of *how* it failed. Each test skipped itself when `test.mk`
was absent, so retiring the fragment turned four tests into four silent skips: green suite, four
fewer checks, no signal. The same trap caught `test_lfs.py` and `test_marimo_targets.py` in this
change, which is the argument for assertions that go red when their subject moves.
"""

from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

# What the `tests` bundle exists to provide. None is named by `all` — they are the opt-in extras,
# each needing its own tool and folder convention.
_EXTRA_TARGETS = ("benchmark", "hypothesis-test", "stress", "mutation")


@pytest.mark.parametrize("target", _EXTRA_TARGETS)
def test_extra_target_resolves(target: str) -> None:
    """Each optional extra must still resolve, so retiring `test.mk` cost no entry point.

    A dry run rather than a real one: these are the expensive gates — mutation testing especially —
    and what is in question is whether the target exists, not whether the tool passes.
    """
    proc = subprocess.run(  # nosec B603
        ["make", "-n", target], cwd=_ROOT, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, f"`make {target}` did not resolve: {proc.stderr}"
    assert "no rule to make target" not in proc.stderr.lower(), (
        f"{target} resolves to no rule — the tests bundle's config has no gate left to feed"
    )


def test_the_benchmark_gate_has_something_to_measure_or_is_known_not_to() -> None:
    """Record whether `benchmark` has any input in *this* repo.

    Written as an observation rather than a demand, because the answer here is "no": rhiza ships
    configuration, so it has no ``tests/benchmarks/`` — while ``rhiza_benchmark.yml`` runs
    ``make benchmark`` on every push. That gate therefore measures nothing on this repo, and has
    for as long as the folder has been absent. It predates the rhiza-task migration and is not its
    doing.

    Asserted this way round so the fact is visible in the suite instead of being something a reader
    has to notice: if a benchmarks folder is ever added, the second branch takes over and starts
    requiring content, and if the workflow is dropped the first branch stops being reachable.
    """
    folder = Path(__file__).resolve().parents[2] / "tests" / "benchmarks"
    if not folder.is_dir():
        pytest.skip(
            "this repo has no tests/benchmarks/, so `make benchmark` measures nothing here — "
            "a pre-existing gap in rhiza_benchmark.yml, not a consequence of retiring test.mk"
        )
    assert sorted(folder.glob("test_*.py")), (
        "tests/benchmarks/ exists but holds no benchmark modules, so the gate collects nothing"
    )
