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

**Why the list below is derived rather than written down.** #1505 fixed four gates and
left ``semgrep`` on the old ``[ -d $(SOURCE_FOLDER) ]`` form (#1511) — not through
carelessness about that gate, but because ``semgrep`` is owned by core's ``quality.mk``
while the other four live in ``python.mk``, so it sat outside both the file being edited
and the hand-written ``_SCOPED_GATES`` list here. A hardcoded list of gates cannot fail
when a gate is missing from it, which made this suite blind to exactly the bug it was
written to prevent, for as long as the bug existed.

So ``test_every_declared_accumulator_is_guarded`` derives the expected set from the
bundle sources: every ``*_FOLDERS ?=`` declaration across ``bundles/*/.rhiza/make.d/`` is
an accumulator some gate reads, and each must appear below. Adding a sixth path-scoped
gate now fails this suite until it is guarded, rather than joining silently.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.util import run_make, strip_ansi

_ROOT = Path(__file__).resolve().parents[2]

# Each gate, the accumulator it reads, and the make-expanded fragment that carries its
# resolved folder list. For the four shell-variable gates that is the assignment itself;
# for `deps` it is deptry's own argument list, which python.mk expands inline.
#
# The accumulator name is not decoration: `test_every_declared_accumulator_is_guarded`
# checks this column against the `*_FOLDERS ?=` declarations in the bundle sources, so a
# new path-scoped gate cannot be added without being guarded here.
_SCOPED_GATES = [
    ("typecheck", "TYPECHECK_FOLDERS", re.compile(r'typecheck_paths="([^"]*)"')),
    ("security", "BANDIT_FOLDERS", re.compile(r'bandit_paths="([^"]*)"')),
    ("docs-coverage", "DOCSTRING_FOLDERS", re.compile(r'docstring_paths="([^"]*)"')),
    ("semgrep", "SEMGREP_FOLDERS", re.compile(r'semgrep_paths="([^"]*)"')),
    # `(?!on:)` skips the "[INFO] Running deptry on:" banner and matches the invocation.
    ("deps", "DEPTRY_FOLDERS", re.compile(r"deptry (?!on:)([^\n;\\]*)")),
]

# Where the accumulators are declared. Every language layer and core may own some, so the
# search is over all bundles rather than a named pair of files.
_BUNDLES = _ROOT / "bundles"
_ACCUMULATOR_DECL = re.compile(r"^([A-Z_]+_FOLDERS)\s*\?=", re.MULTILINE)


@pytest.fixture(scope="module")
def gate_scopes() -> dict[str, str]:
    """Dry-run each scoped gate from the repository root and return its resolved folder list."""
    import logging

    log = logging.getLogger(__name__)
    scopes: dict[str, str] = {}
    for target, _accumulator, pattern in _SCOPED_GATES:
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


def test_every_declared_accumulator_is_guarded() -> None:
    """Every ``*_FOLDERS ?=`` accumulator in the bundles must be covered by ``_SCOPED_GATES``.

    This is the test that would have caught #1511 in #1505. The two assertions above are
    parametrised over a hand-written list, so a gate absent from that list is not tested
    and cannot fail — which is how ``semgrep`` kept the pre-#1505 ``[ -d ... ]`` form
    through a change whose whole purpose was removing it.

    Deriving the expectation from the bundle sources inverts that: a new path-scoped gate
    declares an accumulator, and declaring one without guarding it fails here.
    """
    declared: set[str] = set()
    for fragment in sorted(_BUNDLES.glob("*/.rhiza/make.d/*.mk")):
        declared.update(_ACCUMULATOR_DECL.findall(fragment.read_text()))

    assert declared, (
        "no `*_FOLDERS ?=` declarations found under bundles/*/.rhiza/make.d/ — the "
        "accumulator convention has moved and this guard no longer reads anything."
    )

    guarded = {accumulator for _target, accumulator, _pattern in _SCOPED_GATES}
    unguarded = declared - guarded

    assert not unguarded, (
        f"these folder accumulators are declared in the bundles but no gate in "
        f"_SCOPED_GATES reads them: {sorted(unguarded)}. A path-scoped gate that is not "
        f"listed there is never checked for resolving an empty scope, so it can exit 0 "
        f"having measured nothing — the #1511 regression. Add the gate to _SCOPED_GATES "
        f"with the regex that matches its resolved folder list in `make -n` output."
    )

    stale = guarded - declared
    assert not stale, (
        f"_SCOPED_GATES names accumulators that no bundle declares: {sorted(stale)}. "
        f"Either the gate was removed, or the accumulator was renamed and this list "
        f"was not updated."
    )
