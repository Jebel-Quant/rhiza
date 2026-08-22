"""The mother repo's own static gates must actually look at its own Python.

Rhiza ships configuration rather than a runtime library, so it has no ``src/``. Under the
make layer that meant ``SOURCE_FOLDER`` matched nothing and five path-scoped gates exited
**0** having measured nothing (#1505, #1511, #1516) — on the one repository that ships those
gates to everyone else. The fix was an accumulator per gate, with ``utils/`` contributed from
the retired ``.rhiza/make.d/bundles.mk``.

**This file was rewritten when the make layer was retired.** rhiza now runs on the
``rhiza-task`` shim, and the CLI has no accumulators: every path-scoped gate reads a single
``source_folder`` setting. So the six per-gate assertions collapse into one — the folder that
setting names must exist and hold Python — and the completeness argument changes shape.
It used to derive the expected gate list from ``*_FOLDERS ?=`` declarations in the bundles,
because a hardcoded list cannot fail when a gate is missing from it (which is how ``semgrep``
kept the pre-#1505 form through #1505). Under the CLI a gate cannot have a private scope to
forget: there is one field. What *can* still drift is a new folder setting appearing, so
:func:`test_no_unknown_folder_setting_has_appeared` derives from the CLI's own schema.

The migration immediately reintroduced #1517: ``rhiza-test`` reported ``ok`` while
pytest-rhiza's ``test_docstrings`` skipped with "No doctest folder found (looked for: src)",
because that check reads the ``RHIZA_DOCTEST_FOLDERS`` environment variable and rhiza-task
0.3.0 did not set it (Jebel-Quant/rhiza-task#18). The root ``Makefile`` wrapped the gate to
export it until 0.3.1 made the CLI do it; what is left here is a floor on the pin.
"""

from __future__ import annotations

import json
import re
import subprocess  # nosec B404 - fixed argument vectors
from pathlib import Path

import pytest

from tests.util import strip_ansi

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLES = _ROOT / "bundles"

# The folder settings the CLI exposes, and what this suite expects of each. `source_folder`
# is the one every path-scoped gate reads, so it is the one that must hold real Python.
# Every ``*_folder`` setting the pinned CLI exposes. The first three scope a *gate* and are
# asserted individually below; ``docker_folder`` and ``paper_folder`` arrived with rhiza-task
# 0.3.0 and scope a convenience task each -- `docker-build` looks for a Dockerfile there,
# `paper` for a root `.tex`. Neither is named by `all` and neither reports success on an empty
# folder: both skip with the folder in the reason, so a wrong value is visible rather than
# silent. They are listed to acknowledge them, which is what this set is for.
#
# That reasoning has since gone half stale for `paper_folder`, and
# :func:`test_paper_folder_is_inside_the_docs_tree` is the correction. It held while `paper`
# stood alone -- a skip names its folder, so a wrong value announces itself. rhiza-task 1.1.0
# made `paper` a prerequisite of `book`, and the PDF reaches the site with no copy step: it is
# published only because `paper_folder` sits inside `docs_dir` and mkdocs sweeps that tree.
# Move it out and the paper still compiles, the task still reports ok, and the site simply
# never gets the file. That half is silent, so it is asserted rather than acknowledged.
#
# ``docs_folder`` arrived with rhiza-task 1.1.0 and scopes the new ``docs-examples`` gate,
# which executes the fenced examples in the docs tree. This repo does not run it: `all` does
# not name it, and the fences here are checked by tests/docs/test_doc_consistency.py instead.
# Acknowledged rather than asserted for that reason -- if `docs-examples` is ever wired in,
# the folder needs the same existence guard `source_folder` has above, because the gate skips
# a missing tree rather than failing.
_KNOWN_FOLDER_SETTINGS = {
    "source_folder",
    "tests_folder",
    "marimo_folder",
    "docker_folder",
    "paper_folder",
    "docs_folder",
}


def _rhiza_task() -> str:
    """Return the pinned rhiza-task spec from the root Makefile.

    Read rather than hardcoded so this suite follows the pin instead of drifting from it.

    Returns:
        The ``rhiza-task@X.Y.Z`` spec.
    """
    match = re.search(r"^RHIZA_TASK \?= (\S+)", (_ROOT / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    assert match, "the root Makefile no longer pins RHIZA_TASK"
    return match.group(1)


def _rhiza_task_requirement() -> str:
    """Return the pin as a PEP 508 requirement, for ``uv run --with``.

    ``uvx`` accepts ``name@version``; ``--with`` needs ``name==version``. Converted rather
    than written twice so both forms follow the single pin in the Makefile.

    Returns:
        e.g. ``rhiza-task==0.2.0``.
    """
    name, _, version = _rhiza_task().partition("@")
    return f"{name}=={version}" if version else name


def _cli_print(setting: str) -> str:
    """Return one resolved setting, via ``rhiza-task print``.

    Args:
        setting: A config field name, e.g. ``source_folder``.

    Returns:
        The resolved value, whitespace-collapsed.
    """
    proc = subprocess.run(  # nosec B603
        ["uvx", _rhiza_task(), "print", setting],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return " ".join(strip_ansi(proc.stdout).split())


@pytest.fixture(scope="module")
def source_folder() -> str:
    """Return the folder every path-scoped gate resolves to."""
    return _cli_print("source_folder")


def test_source_folder_resolves_to_something(source_folder: str) -> None:
    """The setting must not be empty, or every path-scoped gate measures nothing."""
    assert source_folder, (
        "rhiza-task resolves an empty source_folder, so typecheck, security, docs-coverage, "
        "deps and semgrep would each exit 0 having scanned nothing (#1505). Set "
        "[tool.rhiza-task] source-folder in pyproject.toml."
    )


def test_source_folder_exists_and_holds_python(source_folder: str) -> None:
    """The named folder must exist and contain Python — the #1505 regression guard.

    Asserting existence is not pedantry: the default is ``src``, this repo has no ``src/``,
    and the CLI's gates skip a folder that is not a directory rather than failing. A wrong
    value here is therefore silent, which is exactly how #1505/#1511/#1516 survived.
    """
    path = _ROOT / source_folder
    assert path.is_dir(), (
        f"source_folder resolves to {source_folder!r}, which is not a directory. Every "
        f"path-scoped gate would skip it and report success having measured nothing."
    )
    assert sorted(path.rglob("*.py")), f"source_folder names {source_folder!r} but it holds no Python at all"


def test_source_folder_is_the_repos_own_tooling(source_folder: str) -> None:
    """It must be ``utils/`` — this repo's only non-test Python.

    ``utils/`` is the tooling behind ``make sync-self`` and the ``sync-self-check`` drift
    check. Named explicitly so a change of source root is a deliberate edit here rather than
    a silent narrowing of every gate.
    """
    assert source_folder == "utils", (
        f"source_folder is {source_folder!r}, expected 'utils' — where the tooling behind "
        f"`make sync-self` and the sync-self-check drift guard lives."
    )


def test_no_unknown_folder_setting_has_appeared() -> None:
    """A new ``*_folder`` setting in the CLI must be considered here, not arrive silently.

    This replaces the ``*_FOLDERS ?=`` derivation the make layer needed. Same inversion, new
    schema: the expectation comes from the CLI rather than from a list written by hand, so a
    gate scoped by some *other* folder cannot escape review the way ``semgrep`` did in #1505.
    """
    script = (
        "from dataclasses import fields;"
        "from rhiza_task.config import Config;"
        "import json;"
        "print(json.dumps(sorted(f.name for f in fields(Config) if f.name.endswith('_folder'))))"
    )
    proc = subprocess.run(  # nosec B603
        ["uv", "run", "--quiet", "--no-project", "--with", _rhiza_task_requirement(), "python", "-c", script],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    found = set(json.loads(proc.stdout))
    assert found, "introspection returned no folder settings at all, so this guard is inert"
    unknown = found - _KNOWN_FOLDER_SETTINGS
    assert not unknown, (
        f"rhiza-task exposes folder settings this suite does not know about: {sorted(unknown)}. "
        f"If a gate is scoped by one of them, guard it here."
    )


# The version in which rhiza-task began passing `source_folder` through to the doctest check
# itself (Jebel-Quant/rhiza-task#18). Below it, a bare delegation silently reintroduces #1517.
_SCOPE_PASSTHROUGH_SINCE = (0, 3, 1)


def test_the_pinned_cli_is_new_enough_to_scope_the_doctest_check() -> None:
    """The replacement for the `make -n` guard the root Makefile's wrapper used to allow.

    pytest-rhiza's ``test_docstrings`` reads its scope from ``RHIZA_DOCTEST_FOLDERS``,
    falling back to ``SOURCE_FOLDER`` in ``.rhiza/.env`` and then to a literal ``src``.
    ``quality.mk`` exported it from ``DOCSTRING_FOLDERS``; rhiza-task 0.3.0 did not -- so the
    check reported

        SKIPPED  No doctest folder found (looked for: src)

    while the gate still said ``ok rhiza-test``. That is #1517 exactly: this repo's only
    doctest examples unchecked, silently, behind a green gate. ``.rhiza/.env`` cannot carry
    the value because that file is gitignored, so CI would never see it.

    **rhiza-task 0.3.1 passes the scope through itself**, which is what let the wrapper go
    when the mother-repo targets moved to ``local.mk``. The property therefore lives inside
    the pin now, asserted upstream against the resolved config
    (``rhiza-task tests/test_tasks.py``, which pins the ``utils`` case this repo is). What is
    left here is the half upstream cannot see: that *this* repo pins a version which has it.

    A floor rather than a dry run, because there is no longer an export to read: with a bare
    delegation the variable is set inside the CLI process, and the only local way to observe
    it is to run the gate for real -- which fails the ``lowest-direct`` dependency job, where
    ``install``'s ``uv lock --check`` legitimately fails on a deliberately-mismatched
    lockfile. The other half of the property, that ``source_folder`` names this repo's own
    Python, is :func:`test_source_folder_is_the_repos_own_tooling`.
    """
    pin = re.search(
        r"^RHIZA_TASK \?= rhiza-task@(\d+)\.(\d+)\.(\d+)",
        (_ROOT / "Makefile").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert pin, "the shim must pin rhiza-task to an exact version"
    version = tuple(int(part) for part in pin.groups())
    assert version >= _SCOPE_PASSTHROUGH_SINCE, (
        f"rhiza-task is pinned at {'.'.join(map(str, version))}, which does not pass "
        f"source_folder to the doctest check -- `make rhiza-test` would report ok while "
        f"test_docstrings skipped with 'No doctest folder found (looked for: src)' (#1517). "
        f"Either pin >= {'.'.join(map(str, _SCOPE_PASSTHROUGH_SINCE))} or restore the "
        f"RHIZA_DOCTEST_FOLDERS export in local.mk."
    )


def test_claude_md_does_not_claim_the_suite_runs_without_coverage(source_folder: str) -> None:
    """CLAUDE.md must not describe ``make test`` as coverage-free while a scope resolves.

    The two halves drifted apart in #1525: #1516 gave ``test`` a coverage scope and ``utils``
    started being measured, but CLAUDE.md still told readers the suite ran "*without* a Python
    coverage number — by design". A contributor reading that would conclude a green
    ``make test`` proves nothing about coverage, when there is a 90% gate they can break.

    Keyed on the resolved scope, so if this repo ever legitimately returns to measuring
    nothing the claim becomes true again and this test stops objecting.
    """
    stale_claims = ("running tests without coverage", "without* a Python coverage number")
    prose = (_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    if not (_ROOT / source_folder).is_dir():
        pytest.skip("no coverage scope resolves, so the coverage-free claim holds")

    found = [claim for claim in stale_claims if claim in prose]
    assert not found, (
        f"CLAUDE.md still says {found} about this repo, but coverage is measured over "
        f"{source_folder!r} and enforced against coverage_fail_under (#1525)."
    )


def _interrogate_hook() -> dict:
    """Return the interrogate hook mapping from the root .pre-commit-config.yaml.

    Returns:
        The hook's YAML mapping.
    """
    import yaml

    config = yaml.safe_load((_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    for repo in config["repos"]:
        for hook in repo["hooks"]:
            if hook["id"] == "interrogate":
                return hook
    pytest.fail("the root .pre-commit-config.yaml no longer declares an interrogate hook")


def test_interrogate_hook_matches_this_repos_python(source_folder: str) -> None:
    """``make fmt``'s interrogate hook must be scoped to files this repo actually has.

    The same failure as the gates above, one layer out (#1535). The hook shipped
    ``files: ^src/`` — correct downstream, inert here — and reported "(no files to
    check)Skipped" on every ``make fmt``, which among twenty-odd Passed lines reads as a
    check that ran.

    Checked against the folders the gate measures rather than a hardcoded list, so the hook
    and the gate cannot drift apart.
    """
    pattern = re.compile(_interrogate_hook()["files"])
    folders = [f for f in (source_folder, "tests") if (_ROOT / f).is_dir()]
    assert folders, "no folder resolves, so there is nothing to scope the hook to"

    for folder in folders:
        candidates = sorted((_ROOT / folder).rglob("*.py"))
        assert candidates, f"docs-coverage names {folder!r} but it holds no Python at all"
        matched = [p for p in candidates if pattern.match(p.relative_to(_ROOT).as_posix())]
        assert matched, (
            f"the interrogate hook's files pattern {pattern.pattern!r} matches none of the "
            f"{len(candidates)} Python files under {folder}/, which docs-coverage does "
            f"measure. The hook would report '(no files to check)Skipped' and read as a "
            f"check that ran (#1535)."
        )


def test_interrogate_hook_and_gate_agree_on_the_threshold() -> None:
    """The ``[tool.interrogate]`` table must enforce what the docs-coverage gate enforces.

    The hook passes ``--config=pyproject.toml``; the gate passes its thresholds on the
    command line. Until #1535 the table did not exist, and interrogate falls back to its own
    defaults for a missing table rather than failing — so the hook enforced 80% where the
    gate enforced 100%, and a hook weaker than the gate it shadows passes work the gate will
    reject.

    The gate's number used to be read out of the shipped ``python.mk``. That fragment
    retired to rhiza-task, whose ``docs_coverage`` task hardcodes 100 -- so the constant
    here is the contract, and it is the pinned CLI's job to keep it.
    """
    import tomllib

    gate_threshold = 100

    table = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["interrogate"]
    assert table["fail-under"] == gate_threshold, (
        f"[tool.interrogate] fail-under is {table['fail-under']} but docs-coverage enforces "
        f"{gate_threshold}. The pre-commit hook reads the table and the gate reads the flag, "
        f"so they would disagree about whether the same code passes (#1535)."
    )
    for flag in ("ignore-init-method", "ignore-magic"):
        assert table.get(flag) is True, (
            f"[tool.interrogate] must set {flag} = true to match the `--{flag}` the docs-coverage recipe passes."
        )


def test_paper_folder_is_inside_the_docs_tree() -> None:
    """``paper_folder`` must sit inside ``docs/``, or the compiled PDF is never published.

    There is no copy step. ``book`` builds the paper, latexmk writes the PDF beside its source,
    and the file reaches the site because mkdocs copies everything under ``docs_dir``. So the
    publication depends entirely on where this setting points, and pointing it elsewhere fails
    in the quietest possible way -- ``paper`` succeeds, ``book`` succeeds, and the artefact is
    absent from the site with nothing reporting it.

    ``docs`` is spelled out rather than resolved from mkdocs, for the reason rhiza-task spells
    it out in the same place: ``docs_dir`` is mkdocs's setting, not one the CLI resolves, so
    both ends assume the default and this test pins that assumption rather than hiding it.
    """
    paper = _cli_print("paper_folder")
    assert paper, "paper_folder resolves to nothing, so `make paper` has no folder to search"

    resolved = (_ROOT / paper).resolve()
    docs = (_ROOT / "docs").resolve()
    assert resolved.is_relative_to(docs), (
        f"paper_folder resolves to {paper!r}, which is outside docs/. The book publishes the "
        f"PDF only because mkdocs sweeps docs_dir -- from there it would compile, report ok, "
        f"and never appear in the site."
    )
