"""Properties of the test suite itself, enforced rather than left to review.

Two invariants live here, both established by hand and both previously unguarded — which is
the whole reason this module exists. An invariant that holds because four people remembered
is one edit away from not holding.

**No test module may import another** (#1583, guarded by #1587). ``test_bundle_combinations``
used to reach into ``test_layer_contract`` for two private helpers, coupling the files through
names neither declared and sharing an ``lru_cache`` across a boundary invisible to either
file's reader. #1586 moved the helpers to :mod:`tests.registry`; this guards the result.

**Every module that derives an expectation from the pinned CLI must declare its control**
(#1584, guarded by #1588). This is the harder one, and the design is worth reading before
editing.

The failure mode is a derivation that **narrows** instead of erroring: the CLI answers with
less than it used to, the expectation set shrinks to match, and the assertion built on it
passes while measuring nothing. #1580 hit that twice in one version bump. The tell is that
both instances were *found by accident* — one because the narrowed registry happened to be
missing a name another assertion looked at, the other because its module already had a
control. Nothing was watching for the class.

So each detected module names the control that protects it, and this module checks the name
resolves to something real. Two dicts rather than one, because the detector is deliberately
**over-inclusive**: it flags anything that runs a subprocess while mentioning the pin, which
catches modules that merely run ``uvx`` for an unrelated tool. A detector that could miss a
new deriver would be worse than one with written-down exceptions, so the false positives go
in :data:`_NOT_DERIVERS` with a reason each.

What this does *not* do is check that a control is correct — only that the author was made to
name one. That is the honest limit of a structural check, and it is still the difference
between a convention and a rule.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TESTS = _ROOT / "tests"

# A test module importing another test module, which #1583 removed and #1587 made checkable.
_CROSS_TEST_IMPORT = re.compile(r"^\s*(?:from|import)\s+tests\.[a-z_]+\.test_", re.MULTILINE)

# How a module reaches the pinned CLI: reading the pin out of the shim, borrowing a helper
# that does, or importing the shared reader.
_TOUCHES_THE_PIN = re.compile(
    r"RHIZA_TASK \\\?=|pinned_cli|_rhiza_task_requirement|from tests import registry|from tests\.registry import"
)

# An argv element that names uv as the runner. `--with` is the `uv run` form, `uvx`/`_UVX`
# the direct one.
_NAMES_UV = re.compile(r'"uvx"|_UVX|"--with"')

# Every module the detector flags, mapped to the control that protects its derivation. The
# value is a function name that must exist in that module -- so this cannot rot into a list of
# names that no longer mean anything, which is the failure mode of every allowlist.
_CONTROLS = {
    # The anchors are checked inside `load` itself, so every importer inherits them.
    "tests/registry.py": "load",
    "tests/api/test_ci_workflow.py": "_gates_named_by_all",
    "tests/bundles/test_bundle_combinations.py": "test_the_benchmark_task_is_registered",
    "tests/bundles/test_layer_contract.py": "test_every_prerequisite_of_all_resolves",
    "tests/integration/test_book_targets.py": "test_every_prerequisite_of_book_resolves",
    # Not the registry: these read the CLI's own source text and assert a lower bound on what
    # they find, which fails rather than passes when the derivation returns less.
    "tests/bundles/test_go_layer_sync.py": "_cli_task_sources",
    "tests/bundles/test_rust_layer_sync.py": "_cli_task_sources",
    # Resolved settings. Each asserts the value is non-empty before asserting anything about
    # its content -- see test_docs_targets's `_cli_setting`, where the ordering matters.
    "tests/integration/test_docs_targets.py": "_cli_setting",
    "tests/integration/test_marimo_targets.py": "test_the_notebook_folder_is_configurable_and_resolves",
    "tests/utils/test_gate_scope.py": "test_source_folder_resolves_to_something",
    "tests/docs/test_doc_consistency.py": "_invoked_tools",
    # The fixture narrowing makes every `missing` assertion fail rather than pass, so the
    # control is structural: there is no direction in which a thinner task list reads as green.
    "tests/api/test_bundle_cli_targets.py": "cli_tasks",
    # The control module for the shared reader. It is a deriver like any other -- it calls
    # `load()` -- so it declares itself rather than being exempted for being the control.
    "tests/test_registry.py": "test_the_registry_loads_and_carries_its_anchors",
}

# Modules the detector flags that do not derive anything from the pin. Each names the tool it
# actually runs, because "it runs uvx" is the whole reason it was flagged.
_NOT_DERIVERS = {
    "tests/integration/test_sbom.py": "runs `uvx cyclonedx-bom`; the pin is not involved",
    "tests/security/test_security_patterns.py": "runs `uvx bandit` out-of-tree; the pin is not involved",
    # This module matches its own detector: `_NAMES_UV` and `_TOUCHES_THE_PIN` are literals in
    # the source above. It reads files and never runs anything.
    "tests/test_suite_structure.py": "holds the detector's own patterns as string literals",
}


def _modules() -> list[Path]:
    """Return every Python file under ``tests/``.

    Returns:
        Absolute paths, sorted.
    """
    return sorted(_TESTS.rglob("*.py"))


def _rel(path: Path) -> str:
    """Return a path as the repo-relative string the dicts above are keyed by.

    Args:
        path: An absolute path inside the repository.

    Returns:
        The POSIX-style relative path.
    """
    return path.relative_to(_ROOT).as_posix()


def _runs_a_subprocess(tree: ast.AST) -> bool:
    """Report whether this module calls ``.run(...)`` anywhere.

    Matched on the attribute alone rather than on ``subprocess.run``, so a module that aliases
    the import is still caught.

    Args:
        tree: The parsed module.

    Returns:
        True when some ``.run()`` call is present.
    """
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run"
        for node in ast.walk(tree)
    )


def _derivers() -> list[str]:
    """Return the modules that look like they derive something from the pinned CLI.

    Over-inclusive by design -- see this module's docstring. A module qualifies two ways, and
    the second is not a convenience: importing :mod:`tests.registry` derives from the CLI
    *transitively*, with no subprocess of its own anywhere in the file. #1586 moved four
    modules into exactly that shape, so a detector keyed on subprocesses alone would have
    stopped seeing the majority of the derivations in this suite -- which
    :func:`test_no_declaration_outlives_its_module` is what caught.

    Returns:
        Repo-relative paths, sorted.
    """
    found = []
    for path in _modules():
        text = path.read_text(encoding="utf-8")
        borrows_the_reader = "from tests.registry import" in text or "from tests import registry" in text
        runs_it_directly = _runs_a_subprocess(ast.parse(text)) and bool(
            _TOUCHES_THE_PIN.search(text) or _NAMES_UV.search(text)
        )
        if borrows_the_reader or runs_it_directly:
            found.append(_rel(path))
    return found


def _defines(path: Path, name: str) -> bool:
    """Report whether a module defines a function or method of this name.

    Args:
        path: The module to read.
        name: The function name to look for, at any nesting depth.

    Returns:
        True when some ``def``/``async def`` in the module carries that name.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name for node in ast.walk(tree)
    )


@pytest.mark.parametrize("module", _modules(), ids=_rel)
def test_no_test_module_imports_another(module: Path) -> None:
    """A test module must not import from another test module (#1583).

    Shared helpers belong in a plain module -- :mod:`tests.registry`, :mod:`tests.util` -- not
    in whichever ``test_*`` file happened to need them first. The import that prompted this
    also shared an ``lru_cache`` between two files, which is a state dependency neither one
    declares.
    """
    text = module.read_text(encoding="utf-8")
    offenders = _CROSS_TEST_IMPORT.findall(text)
    assert not offenders, (
        f"{_rel(module)} imports from another test module: {[o.strip() for o in offenders]}. "
        f"Move the shared helper into a non-test module (tests/registry.py, tests/util.py) and "
        f"import it from both (#1583)."
    )


def test_the_cross_import_guard_can_actually_fire() -> None:
    """Positive control for the guard above, which currently has nothing to find.

    An assertion that passes because its pattern matches nothing is the exact defect this
    file exists to prevent, and the guard above is in that position: the tree is clean, so it
    would pass just as happily with a broken regex. Asserted against a literal instead.
    """
    assert _CROSS_TEST_IMPORT.search("from tests.bundles.test_layer_contract import _registry"), (
        "the cross-test-import pattern no longer matches the import it was written for, so "
        "test_no_test_module_imports_another is passing vacuously"
    )
    assert not _CROSS_TEST_IMPORT.search("from tests.registry import require"), (
        "the pattern matches an import of a non-test helper, which is the thing #1586 moved "
        "*to* -- it would fail the suite for doing the right thing"
    )


@pytest.mark.parametrize("module", _derivers())
def test_every_cli_derivation_declares_its_control(module: str) -> None:
    """A module reading the pinned CLI must name the control that protects it (#1584).

    Failing here means one of three things, and the fix differs:

    - the module derives an expectation from the CLI -> give it a control that fails when the
      derivation returns less, and name it in ``_CONTROLS``;
    - it runs ``uvx`` for an unrelated tool -> record it in ``_NOT_DERIVERS`` with which tool;
    - it no longer touches the CLI at all -> remove its entry.
    """
    assert module in _CONTROLS or module in _NOT_DERIVERS, (
        f"{module} runs the pinned CLI (or uv) but declares no control. A derivation that "
        f"narrows instead of erroring passes while measuring nothing -- #1580 hit that twice "
        f"in one bump. Add it to _CONTROLS naming the test or helper that guards it, or to "
        f"_NOT_DERIVERS if it only runs an unrelated tool."
    )


@pytest.mark.parametrize("module", sorted(_CONTROLS))
def test_each_declared_control_exists(module: str) -> None:
    """The named control must be a real function, or ``_CONTROLS`` is decoration.

    This is what stops the dict becoming the kind of allowlist that outlives what it lists.
    Renaming a control without updating its entry fails here rather than silently leaving the
    module unguarded.
    """
    path = _ROOT / module
    assert path.is_file(), f"_CONTROLS names {module}, which does not exist"
    assert _defines(path, _CONTROLS[module]), (
        f"_CONTROLS says {module} is guarded by {_CONTROLS[module]!r}, but that module defines "
        f"no such function. Either the control was renamed or it was removed -- if removed, the "
        f"derivation is now unguarded."
    )


@pytest.mark.parametrize("module", sorted(_CONTROLS) + sorted(_NOT_DERIVERS))
def test_no_declaration_outlives_its_module(module: str) -> None:
    """Both dicts must describe modules the detector still flags.

    A stale entry is not harmless: it is a claim that some file was reviewed for this property,
    and the reader has no way to tell a current claim from one about a file that stopped
    touching the CLI three refactors ago.
    """
    assert module in _derivers(), (
        f"{module} is declared in _CONTROLS or _NOT_DERIVERS but no longer looks like it "
        f"touches the pinned CLI. Drop the entry -- a declaration nobody can check reads as "
        f"review that did not happen."
    )
