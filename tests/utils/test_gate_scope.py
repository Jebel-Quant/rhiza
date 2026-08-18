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
    """utils/ holds the sync tooling, so every scoped gate must include it."""
    assert "utils" in gate_scopes[target], (
        f"`make {target}` resolves to {gate_scopes[target]!r}, which omits utils/ — the "
        f"tooling behind `make sync-self` and the sync-self-check CI drift guard."
    )


# The static gates only. `deps` and `test` are excluded on purpose, with the reasons
# recorded next to the accumulators in bundles.mk: the package declares its dependencies
# in its own manifest, and its code runs under `make rhiza-test` rather than `make test`.
_STATIC_GATES = [g[0] for g in _SCOPED_GATES if g[0] in {"typecheck", "security", "docs-coverage", "semgrep"}]


@pytest.mark.parametrize("target", _STATIC_GATES)
def test_static_gate_covers_the_rhiza_test_package(target: str, gate_scopes: dict[str, str]) -> None:
    """packages/rhiza-test/ is this repo's other non-test Python and must be gated too.

    It arrived as ~700 lines the moment the conformance suite stopped being copied into
    each repo. Left out of the accumulators it would be code `make all` passes without
    reading — the #1505/#1516 failure, reintroduced by a directory that did not exist when
    those were fixed.
    """
    assert "packages/rhiza-test/src" in gate_scopes[target], (
        f"`make {target}` resolves to {gate_scopes[target]!r}, which omits the rhiza-test "
        f"package source. Contribute it via the accumulators in .rhiza/make.d/bundles.mk."
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


def _interrogate_hook() -> dict:
    """Return the interrogate hook mapping from the root .pre-commit-config.yaml."""
    import yaml

    config = yaml.safe_load((_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    for repo in config["repos"]:
        for hook in repo["hooks"]:
            if hook["id"] == "interrogate":
                return hook
    pytest.fail("the root .pre-commit-config.yaml no longer declares an interrogate hook")


def test_interrogate_hook_matches_this_repos_python(gate_scopes: dict[str, str]) -> None:
    """`make fmt`'s interrogate hook must be scoped to files this repo actually has.

    The same failure as the gates above, one layer out (#1535). The hook shipped
    ``files: ^src/`` — correct downstream, inert here, because rhiza ships configuration
    rather than a runtime library. It reported "(no files to check)Skipped" on every
    ``make fmt``, which in a list of twenty-odd Passed lines reads as a check that ran.

    Checked against the folders ``docs-coverage`` *resolves* rather than a hardcoded list,
    so the hook and the gate cannot drift apart: whatever the accumulator contributes, the
    hook must be able to see it.
    """
    pattern = re.compile(_interrogate_hook()["files"])
    folders = gate_scopes["docs-coverage"].split()
    assert folders, "docs-coverage resolves no folders, so there is nothing to scope the hook to"

    for folder in folders:
        candidates = sorted((_ROOT / folder).rglob("*.py"))
        assert candidates, f"docs-coverage names {folder!r} but it holds no Python at all"
        matched = [p for p in candidates if pattern.match(p.relative_to(_ROOT).as_posix())]
        assert matched, (
            f"the interrogate hook's files pattern {pattern.pattern!r} matches none of the "
            f"{len(candidates)} Python files under {folder}/, which `make docs-coverage` "
            f"does measure. The hook would report '(no files to check)Skipped' and read as "
            f"a check that ran (#1535)."
        )


def test_interrogate_hook_and_gate_agree_on_the_threshold() -> None:
    """The [tool.interrogate] table must enforce what python.mk's docs-coverage enforces.

    The hook passes ``--config=pyproject.toml``; the gate passes its thresholds on the
    command line. Until #1535 the table did not exist, and interrogate falls back to its
    own defaults for a missing table rather than failing — so the hook enforced 80% where
    the gate enforced 100%, and a hook weaker than the gate it shadows passes work the
    gate will reject.
    """
    import tomllib

    recipe = (_BUNDLES / "python-core" / ".rhiza" / "make.d" / "python.mk").read_text(encoding="utf-8")
    match = re.search(r"interrogate\s+-vv\s+--fail-under\s+(\d+)", recipe)
    assert match, "could not find the --fail-under flag in python.mk's docs-coverage recipe"
    gate_threshold = int(match.group(1))

    table = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["interrogate"]
    assert table["fail-under"] == gate_threshold, (
        f"[tool.interrogate] fail-under is {table['fail-under']} but `make docs-coverage` "
        f"enforces {gate_threshold}. The pre-commit hook reads the table and the gate reads "
        f"the flag, so they would disagree about whether the same code passes (#1535)."
    )
    for flag in ("ignore-init-method", "ignore-magic"):
        assert table.get(flag) is True, (
            f"[tool.interrogate] must set {flag} = true to match the `--{flag}` the docs-coverage recipe passes."
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
