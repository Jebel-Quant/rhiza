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
an accumulator some gate reads, and each must appear below. Adding a further path-scoped
gate now fails this suite until it is guarded, rather than joining silently.

That guard did its job, and also showed where it ends. ``coverage`` was the *sixth*
path-scoped gate and #1505 never converted it: ``test`` still passed
``--cov=$(SOURCE_FOLDER)`` behind a ``[ -d ... ]``, so here the suite ran and measured no
coverage whatsoever. Deriving from declarations catches a gate that has an accumulator and
is unguarded; it is structurally blind to one that never declared an accumulator at all.
#1516 gave ``coverage`` the same shape as the rest, which is what brings it into range of
the derivation — the lesson being that this file's completeness argument holds only once a
gate has opted into the convention.
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
    ("test", "COVERAGE_FOLDERS", re.compile(r'coverage_paths="([^"]*)"')),
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


def test_claude_md_does_not_claim_the_suite_runs_without_coverage(gate_scopes: dict[str, str]) -> None:
    """CLAUDE.md must not describe `make test` as coverage-free while the gate resolves a scope.

    The two halves drifted apart in #1525: #1516 gave `test` a COVERAGE_FOLDERS accumulator
    and `utils` started being measured, but CLAUDE.md's mother-repo note still told readers
    the suite ran "*without* a Python coverage number — by design". A contributor reading it
    would conclude a green `make test` proves nothing about coverage, when in fact there is a
    90% gate they can break.

    Checked against the *resolved* scope rather than a hardcoded expectation, so if this repo
    ever legitimately returns to measuring nothing, the claim becomes true again and this
    test stops objecting.
    """
    stale_claims = ("running tests without coverage", "without* a Python coverage number")
    prose = (_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    if not gate_scopes["test"]:
        pytest.skip("`make test` resolves an empty coverage scope, so the coverage-free claim holds")

    found = [claim for claim in stale_claims if claim in prose]
    assert not found, (
        f"CLAUDE.md still says {found} about this repo, but `make test` resolves a coverage "
        f"scope of {gate_scopes['test']!r} and enforces COVERAGE_FAIL_UNDER against it (#1525)."
    )


def test_rhiza_test_carries_the_docstring_scope_to_the_shipped_doctests(logger) -> None:
    """`make rhiza-test` must hand the shipped test_docstrings.py the same scope as docs-coverage.

    Not a member of ``_SCOPED_GATES``: ``RHIZA_DOCTEST_FOLDERS`` is not an accumulator of
    its own but a *carrier* for ``DOCSTRING_FOLDERS``, so the derivation above would flag
    it as stale. The property is worth pinning separately, because the two halves are one
    invariant — ``docs-coverage`` asking whether a docstring exists while the doctest
    runner looks somewhere else is exactly the split that let 23 examples in ``utils/`` go
    unchecked (#1517).
    """
    out = strip_ansi(run_make(logger, ["rhiza-test"], cwd=_ROOT).stdout)
    match = re.search(r'RHIZA_DOCTEST_FOLDERS="([^"]*)"', out)
    assert match, f"`make rhiza-test` no longer passes RHIZA_DOCTEST_FOLDERS:\n{out[-800:]}"
    scope = match.group(1).strip()
    assert scope, (
        "`make rhiza-test` resolves an empty doctest scope, so test_docstrings.py would "
        "skip and the repo's docstring examples would go unchecked (#1517)."
    )
    assert "utils" in scope, (
        f"`make rhiza-test` scopes doctests to {scope!r}, which omits utils/ — where this "
        f"repo's only non-test Python, and its only docstring examples, live."
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
        # encoding is explicit: the fragments carry UTF-8 prose (em dashes in the comment
        # blocks), and Windows would otherwise decode them as cp1252 and raise.
        declared.update(_ACCUMULATOR_DECL.findall(fragment.read_text(encoding="utf-8")))

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
