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
import yaml

from tests.registry import require as require_registry
from tests.registry import resolves

_ROOT = Path(__file__).resolve().parents[2]
_DOCS = _ROOT / "docs"

# Pages deliberately outside the nav, each with the reason it is unreachable on purpose.
# Empty is the expected state: a page nobody can navigate to is a page nobody reads, and
# `test_every_nav_exclusion_is_still_needed` makes an entry here cost an explanation that
# stops being true the moment somebody links the page.
_NOT_IN_THE_NAV: dict[str, str] = {}


def _nav_pages() -> set[str]:
    """Return every docs-relative path the nav in ``mkdocs.yml`` points at.

    Returns:
        The string leaves of the ``nav:`` tree -- ``guides/DEMO.md``, ``paper/rhiza.pdf`` --
        with section titles and nesting flattened away.
    """
    nav = yaml.safe_load((_ROOT / "mkdocs.yml").read_text(encoding="utf-8")).get("nav", [])
    pages: set[str] = set()

    def walk(node: object) -> None:
        """Add every string leaf of ``node`` to ``pages``."""
        if isinstance(node, str):
            pages.add(node)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)

    walk(nav)
    return pages


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
    needs a LaTeX engine, so requiring the artefact here would make this skip on every
    machine without tectonic -- which is most of them, including CI's cheaper jobs.
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


def test_every_docs_page_is_reachable_from_the_nav() -> None:
    """A page the book publishes must be linked from the nav, or nobody can find it.

    The general case of :func:`test_the_compiled_paper_is_reachable_from_the_book`, and it
    was failing for four pages when it was written (#1612): ``guides/CUSTOMIZATION.md`` and
    ``troubleshooting.md`` -- both edited that same week -- plus
    ``operations/CI_PERFORMANCE.md`` and ``presentations/index.md``.

    mkdocs builds every markdown file under ``docs_dir`` whether the nav claims it or not, so
    an unlinked page is published and unreachable rather than missing. Nothing caught it from
    either side: ``book-nav`` checks that each nav *entry* resolves in the built site, which is
    this property in the other direction and passes vacuously on a page no entry mentions.

    Asserted against ``mkdocs.yml`` rather than the built site, for the reason the paper test
    gives: building needs zensical and the paper needs tectonic, so reading the config keeps
    this honest on a machine that has neither.
    """
    linked = _nav_pages()
    orphans = sorted(
        rel
        for rel in (str(p.relative_to(_DOCS)) for p in _DOCS.rglob("*.md"))
        if rel not in linked and rel not in _NOT_IN_THE_NAV
    )
    assert not orphans, (
        f"docs/ holds {orphans}, which mkdocs publishes but no nav entry in mkdocs.yml points "
        f"at. Add a nav entry, delete the page, or record it in _NOT_IN_THE_NAV with the "
        f"reason it is unreachable on purpose."
    )


def test_every_nav_exclusion_is_still_needed() -> None:
    """Each exclusion must name a page that exists and is still absent from the nav.

    Written as one test over the dict rather than a parametrization of it, because the dict is
    expected to be empty: parametrizing would report `got empty parameter set` -- a skip line
    in every run, for the state that is correct.
    """
    linked = _nav_pages()
    stale = {
        rel: ("no longer exists" if not (_DOCS / rel).is_file() else "is linked from the nav now")
        for rel in _NOT_IN_THE_NAV
        if not (_DOCS / rel).is_file() or rel in linked
    }
    assert not stale, f"_NOT_IN_THE_NAV entries that {stale} — drop them"


def test_the_root_mkdocs_inherits_the_base_config() -> None:
    """This repo's own `mkdocs.yml` must carry the `INHERIT:` that reads the base config.

    `bundles/book/` ships `docs/mkdocs-base.yml` and nothing makes a consumer read it: mkdocs
    merges it only when the root config names it in `INHERIT:`, and a config that omits the key
    builds a perfectly good site without it. `chebpy/chebpy` is in exactly that state, which is
    what #1633 reported -- 120 synced lines that nothing there reads.

    Measured against a bare config, what the omission costs under zensical is the light/dark
    palette toggle, the whole `theme.features` list, the back-to-top button and `pymdownx.snippets`
    resolution. None of that fails a build; the site simply comes out plainer, on every run.

    A downstream `mkdocs.yml` is repo-owned, so this repo cannot assert the key is there. What it
    can do is not be the counter-example: rhiza publishes the theme it ships to everyone else.
    """
    config = (_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    base = "docs/mkdocs-base.yml"
    assert (_ROOT / base).is_file(), f"{base} is missing, so the root config inherits from nothing"
    assert f"INHERIT: {base}" in config, (
        f"mkdocs.yml does not inherit {base}, so the theme rhiza ships to every consumer is "
        f"absent from rhiza's own book -- silently, because the build succeeds either way"
    )


def test_the_base_config_cannot_be_built_on_its_own() -> None:
    """The base config must declare no site, and its header must not offer a standalone build.

    Its header documented one for years -- `mkdocs serve -f docs/mkdocs-base.yml` -- and the
    command cannot work: with no `site_name`, mkdocs aborts with `Config value 'site_name':
    Required configuration not provided.` The absence is deliberate, because the site metadata is
    the consumer's, so the fix is to stop documenting the invocation rather than to add a name.

    The second retired claim was that `book` picks this file up when no root-level `mkdocs.yml` is
    found. It did under `book.mk`; rhiza-task's task prints `skipped  book  no mkdocs.yml` instead,
    measured against the pinned version. Both were shipped to every consumer, in the header of the
    file they describe, and nothing read either one.

    Asserted as an absence, the way `test_fmt_target_no_longer_needs_python_version` is: what
    matters is that the header stops telling a reader to run a command that aborts.
    """
    text = (_ROOT / "docs" / "mkdocs-base.yml").read_text(encoding="utf-8")
    header = "\n".join(line for line in text.splitlines() if line.startswith("#"))
    body = "\n".join(line for line in text.splitlines() if not line.startswith("#"))

    assert "site_name" not in body, (
        "the base config declares a site_name, so every consumer inheriting it publishes rhiza's "
        "site metadata as its own"
    )
    offered = [claim for claim in ("mkdocs serve -f", "mkdocs build -f", "will pick this file up") if claim in header]
    assert not offered, (
        f"the header offers {offered}, which no longer works: a standalone build aborts for want "
        f"of site_name, and `book` skips without a root mkdocs.yml (#1633)"
    )
