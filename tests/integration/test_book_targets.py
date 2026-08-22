"""The book targets, after `book.mk` retired to rhiza-task.

This module read the fragment, and its most interesting test was about *resilience*: `book.mk`
defined no-op `test::`/`benchmark::`/`stress::`/`hypothesis-test::` anchors so that `make book`
resolved even when the `tests` bundle was not selected, and the book target itself checked for the
`book/` folder at runtime rather than existing only when it was present.

Both concerns are answered differently now, which is why the tests are rewritten rather than
ported. The double-colon anchors are gone with the make layer — the CLI's `book` task declares its
prerequisites in the registry, so a missing one is a resolution error rather than a silently
skipped rule. And the folder check lives in the task.

Rewritten rather than deleted because of *how* it failed: each test skipped itself when `book.mk`
was absent, so retiring the fragment turned four tests into four silent skips. The same trap caught
`test_lfs.py`, `test_marimo_targets.py` and `test_benchmark_targets.py` in this change.
"""

from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path

import pytest

from tests.registry import require as require_registry
from tests.registry import resolves

_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("target", ["book", "serve"])
def test_book_target_resolves(target: str) -> None:
    """The book targets must resolve, so retiring `book.mk` cost no entry point."""
    proc = subprocess.run(  # nosec B603
        ["make", "-n", target], cwd=_ROOT, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, f"`make {target}` did not resolve: {proc.stderr}"
    assert "no rule to make target" not in proc.stderr.lower()


def test_every_prerequisite_of_book_resolves() -> None:
    """`book`'s prerequisites must all be registered tasks.

    This is what the no-op `::` anchors were for. `book.mk` needed `test`, `benchmark`, `stress`
    and `hypothesis-test` to *exist* whether or not the `tests` bundle was selected, and satisfied
    that by defining each as a rule with an empty recipe — so `make book` never died on a missing
    rule, and never ran a gate that was not there.

    The registry replaces the trick: `book` names its prerequisites, and they resolve because the
    tasks are registered rather than because a fragment stubbed them. Asserted here because the
    property is the same one and its failure mode is identical — `book` dying on a name nothing
    provides.

    Read through :mod:`tests.registry`, which was the third copy of this subprocess until
    #1583. Naming the task modules by hand made this test's own coverage depend on a list
    nobody re-derives: rhiza-task 1.1.0 gave `book` a `paper` prerequisite, `paper` lives in a
    module the list did not mention, and the assertion reported a missing task where the real
    gap was the fixture. The shared reader walks the entry-point group the CLI itself walks,
    and asserts the registry is plausible before any caller reads it (#1584).
    """
    registry = require_registry()

    book = next((v for k, v in registry.items() if k.endswith("book")), None)
    assert book is not None, "`book` is not a registered task"
    missing = [n for n in book if not resolves(registry, "python", n)]
    assert not missing, (
        f"`book` names {missing}, which resolve to no registered task — the failure the no-op `::` "
        f"anchors in book.mk existed to prevent"
    )


def test_the_docs_folder_the_book_builds_from_exists() -> None:
    """`mkdocs.yml` and `docs/` must be present, or the build has no input.

    `book.mk` guarded on the folder at runtime and printed a warning; the task does its own
    checking, so what is worth asserting here is the repo's side of the contract.
    """
    assert (_ROOT / "mkdocs.yml").is_file(), "mkdocs.yml is missing, so `make book` has no config"
    assert (_ROOT / "docs").is_dir(), "docs/ is missing, so `make book` would build an empty site"


def test_the_compiled_paper_is_reachable_from_the_book() -> None:
    """A paper the book compiles must be linked from the nav, or nobody can find it.

    ``book`` gained ``paper`` as a prerequisite in rhiza-task 1.1.0, and the PDF reaches the
    site with no copy step at all -- ``paper_folder`` defaults to ``docs/paper``, which is
    inside ``docs_dir``, so mkdocs sweeps it up as an asset. That is the whole mechanism, and
    it has no opinion about whether anything *links* to the result.

    So this repo spent a release compiling ``docs/paper/rhiza.tex``, publishing the PDF into
    the built site, and referencing it from no nav entry in any mkdocs config. Every gate
    passed: the paper task succeeded, the book built, and ``book-nav`` -- which exists to
    catch a nav entry resolving to nothing -- had nothing to check, because nothing had been
    claimed.

    The two halves compose and neither is sufficient. This test says the paper is claimed;
    ``book-nav`` says the claim resolves in the built site. Asserted against the nav *text*
    rather than a built file, deliberately: the PDF only exists after ``make paper``, which
    needs a LaTeX distribution, so requiring the artefact here would make this skip on every
    machine without latexmk -- which is most of them, including CI's cheaper jobs.
    """
    tex = sorted((_ROOT / "docs" / "paper").glob("*.tex"))
    if not tex:
        pytest.skip("this repo ships no paper, so there is nothing for the book to link")

    config = (_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    unlinked = [t.stem for t in tex if f"paper/{t.stem}.pdf" not in config]
    assert not unlinked, (
        f"docs/paper/ holds {unlinked}, compiled by `book`'s `paper` prerequisite and published "
        f"into the site as an asset, but no nav entry in mkdocs.yml points at "
        f"paper/{unlinked[0]}.pdf. The build succeeds and the paper is unreachable."
    )
