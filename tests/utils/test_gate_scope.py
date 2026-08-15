"""The mother repo's own static gates must actually look at its own Python.

Rhiza ships configuration rather than a runtime library, so it has no ``src/`` and
``SOURCE_FOLDER`` matches nothing. Three of the four path-scoped gates keyed on that
variable alone, which meant ``make typecheck``, ``make security`` and ``make deps``
exited **0** having measured nothing here, and ``docs-coverage`` saw only the test
folders (#1505). A green ``make all`` therefore said less than it appeared to — on the
one repository that ships those gates to everyone else.

The fix was to give each gate the accumulator shape ``deps`` already had, and to
contribute ``utils/`` from ``.rhiza/make.d/bundles.mk``. What these tests pin is the
*outcome* rather than the wiring: a test that grepped ``bundles.mk`` for ``utils`` would
still pass if python.mk stopped reading the accumulator, which is precisely the
regression worth catching.

Each gate's folder list is expanded by **make**, not by the recipe's shell, so it is
visible in ``make -n`` output and no gate has to run. That distinction is what makes
these assertions possible: the recipes' ``[ -d ... ]`` warnings are printed by a dry run
whether or not they would fire, so the presence of a warning proves nothing and only the
expanded value does.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.util import run_make, strip_ansi

_ROOT = Path(__file__).resolve().parents[2]

# Each gate and the make-expanded fragment that carries its resolved folder list.
# For the three shell-variable gates that is the assignment itself; for `deps` it is
# deptry's own argument list, which python.mk expands inline.
_SCOPED_GATES = [
    ("typecheck", re.compile(r'typecheck_paths="([^"]*)"')),
    ("security", re.compile(r'bandit_paths="([^"]*)"')),
    ("docs-coverage", re.compile(r'docstring_paths="([^"]*)"')),
    # `(?!on:)` skips the "[INFO] Running deptry on:" banner and matches the invocation.
    ("deps", re.compile(r"deptry (?!on:)([^\n;\\]*)")),
]


@pytest.fixture(scope="module")
def gate_scopes() -> dict[str, str]:
    """Dry-run each scoped gate from the repository root and return its resolved folder list."""
    import logging

    log = logging.getLogger(__name__)
    scopes: dict[str, str] = {}
    for target, pattern in _SCOPED_GATES:
        out = strip_ansi(run_make(log, [target], cwd=_ROOT).stdout)
        match = pattern.search(out)
        assert match, f"could not find the resolved folder list for `make {target}` in:\n{out[-800:]}"
        scopes[target] = match.group(1).strip()
    return scopes


@pytest.mark.parametrize("target", [g[0] for g in _SCOPED_GATES])
def test_scoped_gate_resolves_a_non_empty_scope(target: str, gate_scopes: dict[str, str]) -> None:
    """Each path-scoped gate must resolve to at least one folder, or it measures nothing."""
    assert gate_scopes[target], (
        f"`make {target}` resolves an empty folder list, so it would exit 0 having scanned "
        f"nothing. Contribute a folder via the accumulators in .rhiza/make.d/bundles.mk (#1505)."
    )


@pytest.mark.parametrize("target", [g[0] for g in _SCOPED_GATES])
def test_scoped_gate_covers_utils(target: str, gate_scopes: dict[str, str]) -> None:
    """utils/ holds this repo's only non-test Python, so every scoped gate must include it."""
    assert "utils" in gate_scopes[target], (
        f"`make {target}` resolves to {gate_scopes[target]!r}, which omits utils/ — the "
        f"tooling behind `make sync-self` and the sync-self-check CI drift guard."
    )
