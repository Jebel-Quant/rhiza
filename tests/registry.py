"""One reader for the pinned CLI's task registry, with the control that keeps it honest.

Four modules across three test packages need the same answer -- does this task name resolve,
and what does it depend on -- and until #1583 each had its own copy of the subprocess that
asks. Three copies drifted independently, and one of them reached into another test module
for the helpers it was missing: ``test_bundle_combinations`` imported ``_registry`` and
``_resolves`` from ``tests.bundles.test_layer_contract``, by their private names.

That is what #1583 is about. Two ``test_*`` modules coupled through private names neither
declared, sharing an ``lru_cache`` across a boundary that does not exist as far as either
file's reader is concerned.

The import is described here rather than quoted, deliberately (#1587). Quoted as a code
block it was the only occurrence of that pattern left in the tree, and textually identical
to the thing it replaced -- so the guard in
``tests/test_suite_structure.py`` would have needed a carve-out for the very module that
documents the rule, keyed on a filename, exempting exactly the file where a regression
would be least visible.

**The deeper problem was #1584, and it is why this module raises rather than returns.** The
old helper answered an unreachable CLI and an empty registry the *same* way -- with ``{}`` --
so every caller wrote ``if not registry: pytest.skip(...)`` and a registry that loaded fine
but came back empty was reported as an environment problem. That is a derived expectation
narrowing to nothing while the suite stays green, which is the exact failure #1580 hit twice.
So the two outcomes are separated here:

- **Unavailable** -- no pin, no ``uv``, no network -- is an outage. :func:`require` skips,
  and says which.
- **Reachable but implausible** -- the registry loaded and does not contain the tasks this
  repo is built on -- is a **failure**, raised from :func:`load` where no caller can mistake
  it for a skip.

The anchors in :data:`_ANCHORS` are that second check. They are deliberately tasks whose
disappearance would be a breaking change upstream rather than a routine rename, so this stays
a smoke test of the derivation and not a second copy of the layer contract.
"""

from __future__ import annotations

import functools
import json
import re
import subprocess  # nosec B404 - fixed argument vectors
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]

# Read from the shim rather than hardcoded, so this follows the pin instead of drifting from
# it -- the same reason every other module here reads it out of the Makefile.
_PIN = re.compile(r"^RHIZA_TASK \?= (\S+)", re.MULTILINE)

# `load_tasks` is the CLI's own entry-point walk. Naming task modules by hand instead is how
# `book`'s `paper` prerequisite went unseen when rhiza-task 1.1.0 added it (#1580).
_SCRIPT = (
    "import json;"
    "from rhiza_task.cli import load_tasks; load_tasks();"
    "from rhiza_task.spec import REGISTRY;"
    "print(json.dumps({k: list(v.needs) for k, v in REGISTRY.items()}))"
)

# Tasks whose absence means the registry did not load properly, rather than that rhiza-task
# reorganised itself: the Python layer's aggregate, a neutral task, and a layer-scoped gate.
# One of each kind, because a derivation can narrow to *part* of the registry -- which is
# precisely what a hand-written module list did.
_ANCHORS = ("python:all", "fmt", "python:test")


def pin() -> str | None:
    """Return the ``rhiza-task@X.Y.Z`` spec the root Makefile pins.

    Returns:
        The spec, or None when the Makefile no longer pins one.
    """
    match = _PIN.search((_ROOT / "Makefile").read_text(encoding="utf-8"))
    return match.group(1) if match else None


@functools.lru_cache(maxsize=1)
def load() -> dict[str, list[str]] | None:
    """Return the registry as ``{key: [prerequisite, ...]}``, or None when unreachable.

    Keys are ``layer:name`` for a layer-scoped task and a bare ``name`` for a neutral one,
    which is how :mod:`rhiza_task.spec` stores them: three layers may each define ``test``,
    and which one answers is decided per repository.

    The failure *outcome* is cached along with the success, so a run without a network pays
    for one ``uv`` invocation rather than one per caller.

    Returns:
        The registry, or None when there is no pin or the CLI could not be run.

    Raises:
        AssertionError: When the CLI ran but the registry does not contain :data:`_ANCHORS`.
            Deliberately not a skip -- see this module's docstring.
    """
    spec = pin()
    if spec is None:
        return None
    name, _, version = spec.partition("@")
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
            _SCRIPT,
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    registry: dict[str, list[str]] = json.loads(proc.stdout)

    missing = [anchor for anchor in _ANCHORS if anchor not in registry]
    assert not missing, (
        f"{spec}'s task registry loaded but is missing {missing}, so every test deriving "
        f"expectations from it is measuring less than it reads. Either the pin is broken or "
        f"`load_tasks` stopped importing what it used to -- both are regressions, not "
        f"reasons to skip (#1584)."
    )
    return registry


def require() -> dict[str, list[str]]:
    """Return the registry, skipping the calling test when the CLI cannot be reached.

    Returns:
        The registry, guaranteed non-empty and carrying every anchor.
    """
    registry = load()
    if registry is None:
        pytest.skip(f"could not read the task registry from {pin() or 'an unpinned CLI'}")
    return registry


def resolves(registry: dict[str, list[str]], layer: str, task: str) -> bool:
    """Report whether ``task`` resolves for ``layer``: layer-scoped first, then neutral.

    Args:
        registry: The task registry.
        layer: ``python``, ``rust`` or ``go``.
        task: A task name.

    Returns:
        True when some registered task answers that name for that layer.
    """
    return f"{layer}:{task}" in registry or task in registry
