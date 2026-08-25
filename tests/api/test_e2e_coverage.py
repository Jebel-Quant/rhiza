"""Every end-to-end module is named by a job in `rhiza_e2e.yml`.

`make e2e` runs `tests/e2e` whole, so a new module is picked up locally the moment it
is written. CI is the opposite: each job narrows with `E2E_ARGS` to a named file list,
one per language layer, because a job installs only its own toolchain. Nothing
reconciles the two.

That asymmetry has a failure mode with no symptom. A module no job names is collected
by nothing, the E2E workflow still reports success, and the only evidence is a test
count in a log nobody reads. It is the shape this repository keeps finding — #1505,
#1511, #1516, #1535 — and it happened here: `test_setup_hook_e2e.py` was added, passed
locally under `make e2e`, and ran in none of the three CI jobs while the workflow went
green.

Asserted against the workflow's shell rather than a hand-kept list, so adding a module
and forgetting the job is a red test rather than a quiet gap. The reverse -- a job
naming a module that no longer exists -- is caught too, since `pytest` would exit 4 on
the missing path and that is worth failing here instead of in CI.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = _ROOT / ".github" / "workflows" / "rhiza_e2e.yml"
_E2E_DIR = _ROOT / "tests" / "e2e"

# `E2E_ARGS=<value>`, bare or quoted. The value is a whitespace-separated path list, which
# is why this captures the whole of it rather than one path: `make e2e E2E_ARGS="a b"` is
# how a job runs two modules, and matching a single path would silently see only the first.
_E2E_ARGS = re.compile(r"""E2E_ARGS=(?:"([^"]*)"|'([^']*)'|(\S+))""")


def _named_modules() -> set[str]:
    """Return every `tests/e2e/*.py` path the workflow's jobs name.

    Returns:
        Repo-relative paths, as written in the workflow.
    """
    source = _WORKFLOW.read_text(encoding="utf-8")
    named: set[str] = set()
    for match in _E2E_ARGS.finditer(source):
        value = next(group for group in match.groups() if group is not None)
        named.update(part for part in value.split() if part.endswith(".py"))
    return named


def _e2e_modules() -> set[str]:
    """Return every end-to-end test module on disk.

    Returns:
        Repo-relative paths.
    """
    return {
        f"tests/e2e/{path.name}"
        for path in _E2E_DIR.glob("test_*.py")
        if path.name != "harness.py"  # not a test module, and not glob-matched anyway
    }


def test_the_workflow_names_at_least_one_module() -> None:
    """The regex still matches, so the two assertions below cannot pass vacuously."""
    assert _named_modules(), (
        f"no E2E_ARGS assignment found in {_WORKFLOW.name}; the pattern has gone stale and "
        f"the coverage assertions below would pass over nothing"
    )


@pytest.mark.parametrize("module", sorted(_e2e_modules()))
def test_every_e2e_module_runs_in_ci(module: str) -> None:
    """A module no job names is collected by nothing, and the workflow still goes green.

    Args:
        module: The end-to-end module that must appear in some job's `E2E_ARGS`.
    """
    assert module in _named_modules(), (
        f"{module} is not named by any job in {_WORKFLOW.name}, so it never runs in CI. "
        f"`make e2e` runs tests/e2e whole and will pass locally, which is what makes this "
        f"silent. Add it to the E2E_ARGS of whichever job installs the toolchain it needs."
    )


@pytest.mark.parametrize("module", sorted(_named_modules()))
def test_every_named_module_exists(module: str) -> None:
    """A job naming a module that was renamed or removed fails the whole job on exit 4.

    Args:
        module: A path named in some job's `E2E_ARGS`.
    """
    assert (_ROOT / module).is_file(), (
        f"{_WORKFLOW.name} names {module}, which does not exist -- pytest exits 4 on a "
        f"missing path, so that job fails rather than skipping the module."
    )
