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

import json
import re
import subprocess  # nosec B404
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _pin() -> str:
    """Return the pinned rhiza-task spec from the root Makefile.

    Returns:
        The ``rhiza-task@X.Y.Z`` spec.
    """
    match = re.search(r"^RHIZA_TASK \?= (\S+)", (_ROOT / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        pytest.skip("the root Makefile no longer pins RHIZA_TASK")
    return match.group(1)


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

    Every task module is loaded, through the CLI's own `load_tasks`. Naming them by hand made
    this test's own coverage depend on a list nobody re-derives: rhiza-task 1.1.0 gave `book` a
    `paper` prerequisite, `paper` lives in a module the list did not mention, and the assertion
    reported a missing task where the real gap was the fixture.
    """
    name, _, version = _pin().partition("@")
    script = (
        "import json;"
        "from rhiza_task.cli import load_tasks; load_tasks();"
        "from rhiza_task.spec import REGISTRY;"
        "print(json.dumps({k: list(v.needs) for k, v in REGISTRY.items()}))"
    )
    proc = subprocess.run(  # nosec B603
        [
            "uv",
            "run",
            "--quiet",
            "--no-project",
            "--with",
            f"{name}=={version}" if version else name,
            "python",
            "-c",
            script,
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        pytest.skip("could not read the rhiza-task registry")
    registry = json.loads(proc.stdout)

    book = next((v for k, v in registry.items() if k.endswith("book")), None)
    assert book is not None, "`book` is not a registered task"
    missing = [n for n in book if f"python:{n}" not in registry and n not in registry]
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
