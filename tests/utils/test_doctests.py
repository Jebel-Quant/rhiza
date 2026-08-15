"""Run the doctests in ``utils/``, and fail if there are none to run.

The mother repo had 100% docstring coverage and zero executable examples (#1512).
``make docs-coverage`` asks whether a docstring *exists*; nothing asked whether what it
claims is still true. The gate that would — the shipped ``.rhiza/tests/test_docstrings.py``
— cannot reach this repo's Python for two independent reasons, and fixing either alone
would not help:

* it resolves its search root from ``SOURCE_FOLDER`` (default ``src``), and rhiza ships
  configuration rather than a runtime library, so no such directory exists; and
* it walks *packages*, discovering them by ``__init__.py``. ``utils/`` is a flat pair of
  scripts with no ``__init__.py``, so it would be skipped even if pointed at directly.

Rather than widen the shipped test — which every downstream consumer syncs, and whose
skip-on-no-``src/`` behaviour is correct for them — the mother repo brings its own
runner, exactly as ``.rhiza/make.d/bundles.mk`` brings its own gate-scope accumulators
for the same underlying reason.

The second assertion is the load-bearing one. ``doctest.testmod`` reports success on a
module with no examples, so a runner that only checked for failures would have passed
just as happily before #1512 as after it — measuring nothing, which is the exact failure
mode being closed.
"""

from __future__ import annotations

import doctest
import importlib.util
import sys
from pathlib import Path

import pytest

# The modules to run doctests over. Listed rather than globbed so that adding a module to
# utils/ without examples is a deliberate choice made here, not a silent omission.
_MODULES = ("link_dogfood", "explain_bundles")


def _load(root: Path, name: str):  # type: ignore[no-untyped-def]
    """Load ``utils/<name>.py`` as an importable module."""
    module_path = root / "utils" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", _MODULES)
def test_doctests_pass(root: Path, name: str) -> None:
    """Every doctest example in the module must evaluate to its documented output."""
    module = _load(root, name)
    results = doctest.testmod(
        module,
        verbose=False,
        optionflags=(doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE),
    )
    assert results.failed == 0, f"{name}: {results.failed}/{results.attempted} doctests failed"


@pytest.mark.parametrize("name", _MODULES)
def test_module_carries_examples(root: Path, name: str) -> None:
    """Each module must carry at least one example, or the check above measures nothing."""
    module = _load(root, name)
    results = doctest.testmod(module, verbose=False)
    assert results.attempted > 0, (
        f"utils/{name}.py has no doctest examples. `make docs-coverage` will still report "
        f"100% — it only checks that docstrings exist — so nothing would verify that this "
        f"module's documented behaviour is still accurate (#1512)."
    )
