"""Benchmarks for the dogfood linker — the one code path here whose cost grows with the template.

**Why this folder exists at all.** ``rhiza_benchmark.yml`` has run ``benchmark`` on every push
to ``main`` for as long as the workflow has existed, and this repo had no ``tests/benchmarks/``.
The gate's guard globs ``tests_folder`` for ``benchmarks/*.py``, so every one of those runs
printed ``skipped  benchmark  no benchmarks folder`` and exited 0: a green workflow, a step
summary with a duration in it, and nothing measured. That is the same silent-green shape as
#1505, #1511, #1516 and #1535, reached through a missing folder rather than a mis-scoped
variable, and ``tests/integration/test_benchmark_targets.py`` was already carrying it as a
recorded observation waiting to flip.

**Why not the blueprint.** The ``benchmarks`` bundle ships a ``test_benchmarks.py`` that times
string concatenation, a list comprehension and ``dict`` insertion. It says of itself that it is
placeholder code to be replaced, and it is right to: those numbers describe CPython's
performance, not rhiza's, so a regression in them would be a story about the interpreter. The
mother repo therefore writes its own rather than dogfooding that file — which is also why this
module's name deliberately does not collide with the bundle's. A root file whose path has a
bundle twin must be a symlink into it (``test_bundle_dogfood_symlinks.py``), and a same-path
copy that merely diverges is classified as an *undeclared* mother-repo override and left alone,
silently.

**What is worth measuring.** ``utils/link_dogfood.py`` is the only thing here with a cost that
scales: ``_bundle_index`` walks every file under ``bundles/``, and ``relink`` classifies every
git-tracked path against that index, reading bytes for each candidate whose size matches its
bundle owner's. Both grow as bundles are added, and both run in every ``make sync-self``,
``make sync-self-check`` and — via ``test_bundle_dogfood_symlinks.py``, twice per parametrised
case — every ``make test``. So this is the baseline that would notice the template outgrowing
its linker.

**Every benchmark asserts the size of what it measured**, and that is not decoration. A
benchmark whose input narrows to nothing gets *faster*, and faster reads as an improvement: an
empty bundle index or an empty tracked-file list would show up as a win in the very report meant
to catch regressions. The assertions are what make the timings mean something, so each one pins
that both arms of the work it times were actually reached.
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path
from types import ModuleType

import pytest

_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def linker() -> ModuleType:
    """Load ``utils/link_dogfood.py`` as a module.

    ``utils/`` is not a package, so it is loaded from its file path — the same approach
    ``tests/utils/test_link_dogfood.py`` and ``tests/bundles/test_bundle_dogfood_symlinks.py``
    take, and for the same reason: benchmark the linker's own helpers rather than a
    reimplementation of them.

    Returns:
        The imported ``link_dogfood`` module.
    """
    module_path = _ROOT / "utils" / "link_dogfood.py"
    spec = importlib.util.spec_from_file_location("link_dogfood", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tracked(linker: ModuleType) -> list[str]:
    """Return every git-tracked path, resolved once outside the measured region.

    ``_tracked_files`` shells out to ``git ls-files``, so calling it inside a benchmark would
    time the subprocess rather than the linker. Resolved once here, and skipped rather than
    failed where git is absent — the benchmark gate is opt-in tooling, not a correctness gate.

    Args:
        linker: The ``link_dogfood`` module.

    Returns:
        Repo-root-relative POSIX paths.
    """
    if shutil.which("git") is None:
        pytest.skip("git is not installed, so the tracked-file list cannot be resolved")
    return linker._tracked_files(_ROOT)


@pytest.fixture(scope="module")
def index(linker: ModuleType) -> dict[str, list[Path]]:
    """Return the bundle index, built once for the benchmarks that consume rather than build it.

    Args:
        linker: The ``link_dogfood`` module.

    Returns:
        The mapping from bundle-relative path to the bundle files providing it.
    """
    return linker._bundle_index(_ROOT / "bundles")


def test_building_the_bundle_index(benchmark, linker: ModuleType) -> None:
    """Time the ``bundles/`` tree walk that every dogfood operation starts with.

    This is the one measurement that grows purely with the template: one ``rglob`` over every
    bundle, and a path rewrite per file. Adding a bundle makes it slower, which is exactly the
    signal worth having a baseline for.

    The anchors are two paths the index must contain — ``core``'s front door and the Python
    layer's lint config — because an index built against a moved or renamed bundle tree comes
    back small and quick rather than empty and obviously wrong.
    """
    result = benchmark(linker._bundle_index, _ROOT / "bundles")

    assert result, "the bundle index is empty, so this benchmark timed a walk over nothing"
    for anchor in ("Makefile", "ruff.toml"):
        assert anchor in result, f"the bundle index has no entry for {anchor} — the bundle tree moved"


def test_deciding_the_carveout_predicate_for_every_tracked_path(benchmark, linker: ModuleType, tracked) -> None:
    """Time ``is_dogfood_carveout`` across the whole tracked-file list.

    The cheapest of the three, and the one run most often: it is the first question
    ``_classify_dogfood`` asks about every path, and the guard test asks it separately again.
    Pure string and ``Path`` work, no I/O.

    Both arms are pinned. A predicate that answered True for everything, or False for
    everything, would be *faster* than the real ladder while turning either the linker or its
    guard into a no-op — the failure this file's docstring is about.
    """
    carved = benchmark(lambda: [rel for rel in tracked if linker.is_dogfood_carveout(rel)])

    assert carved, "no tracked path is a carve-out, so the predicate's True arm was never reached"
    assert len(carved) < len(tracked), "every tracked path is a carve-out, so its False arm was never reached"


def test_classifying_every_tracked_path_against_the_index(benchmark, linker: ModuleType, tracked, index) -> None:
    """Time the full dogfood verdict for every tracked path — the work ``sync-self-check`` does.

    The index is prebuilt, so what is measured is the classification itself: the eligibility
    ladder, plus a ``stat`` and (where sizes match) a byte comparison for each path that has a
    bundle owner. That content read is the part that scales with both trees at once, and it is
    why this is timed separately from the walk above rather than as one end-to-end number.

    ``relink`` itself is deliberately not the subject: it would drag ``git ls-files`` and, in
    write mode, filesystem mutation into the measurement.

    Both verdicts that this repo's layout must produce are asserted. ``ambiguous`` is not —
    whether one occurs is the drift guard's business, not this file's.
    """
    verdicts = benchmark(lambda: [linker._classify_dogfood(_ROOT, rel, index)[0] for rel in tracked])

    assert "link" in verdicts, "no tracked path classified as a dogfood symlink — the linking arm was never reached"
    assert "skip" in verdicts, "every tracked path is a dogfood copy, which cannot be right"
