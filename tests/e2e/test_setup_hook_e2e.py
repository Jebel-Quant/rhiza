"""`local-setup.sh` runs, on a freshly synced project, through the real chain.

This is the one assertion that would have caught the bug the hook replaced. Rhiza
documented shadowing `install` in `local.mk` as the way to install a native binary
— graphviz was its worked example — and that recipe never ran: the Makefile's `%:`
catch-all forwards the *goal* to the pinned CLI, which resolves `install` inside its
own task graph and consults no make rule of that name, and CI never invokes make at
all. It fired only when someone typed `make install` by hand, which is exactly how
a consumer would test it and conclude it worked.

So what is proved here is deliberately the whole chain and not the task: a project
assembled from real bundles, with a committed executable hook, whose `make install`
leaves the hook's side effect behind. Nothing shorter distinguishes a seam that
works from the one that looked like it did — `tests/api/` dry runs cannot, because
the delegation line is identical either way.

Python is the layer under test because one is enough for a chain that is
language-neutral: `setup` is a neutral task, and rhiza-task's own suite asserts all
three layers' `install` names it. The negative case — a hook present but not
executable, which fails rather than passing quietly — is covered there too, and
reproducing it here would cost a second full assemble for a branch that never
touches rhiza's own wiring.

Skips unless ``RHIZA_E2E=1`` and uv is on PATH. See `harness.py`.
"""

from __future__ import annotations

import dataclasses

import pytest

from tests.e2e.harness import GATE_TIMEOUT_SECONDS, PYTHON, Project, assemble

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(GATE_TIMEOUT_SECONDS)]

SENTINEL = "setup-hook-ran.txt"
"""What the hook leaves behind. A file rather than a printed line, because stdout
would also carry the hook's own `echo` from the scaffold and prove less: the file
exists only if the script actually executed."""

HOOK = f"""#!/usr/bin/env bash
set -euo pipefail
# Stands in for `apt-get install -y graphviz`, without needing a package manager,
# the network, or root in CI.
printf 'provisioned\\n' > "$(dirname "$0")/{SENTINEL}"
"""

WITH_HOOK = dataclasses.replace(
    PYTHON,
    files={**PYTHON.files, "local-setup.sh": HOOK},
    executables=frozenset({"local-setup.sh"}),
)
"""The Python layer plus a committed, executable hook.

`executables` is not decoration: `setup` refuses to run a hook without the bit, so a
scaffold that only wrote the text would assert the failure path while looking like
the success one.
"""


@pytest.fixture(scope="module")
def project(root, tmp_path_factory, logger) -> Project:
    """Assemble a Python project that ships a `local-setup.sh`, and install it."""
    return assemble(WITH_HOOK, root, tmp_path_factory.mktemp("e2e-setup-hook"), logger)


def test_install_runs_the_repo_owned_hook(project: Project):
    """`make install` executes the hook — the property the old recipe never had.

    The sentinel is the whole assertion. `ok  setup` in the summary would pass on a
    task that found no hook and said so, which is the shape being ruled out.
    """
    sentinel = project.path / SENTINEL
    assert sentinel.is_file(), (
        f"`make install` did not run local-setup.sh: no {SENTINEL}.\n"
        f"This is the failure the hook exists to remove — the seam resolves, reports "
        f"success, and provisions nothing.\n{project.install_output[-800:]}"
    )
    assert sentinel.read_text(encoding="utf-8").strip() == "provisioned"


def test_the_hook_is_reported_and_precedes_the_dependency_sync(project: Project):
    """It runs before `uv sync`, and says so — a build dependency is needed by then.

    Ordering is the half that matters for a native library a wheel has to compile
    against: arriving after the sync is arriving too late. Asserted on the run
    summary rather than the venv, since both steps succeed either way.
    """
    out = project.install_output
    assert "ok  setup" in out, f"the setup task did not report success:\n{out[-800:]}"
    assert "nothing to provision" not in out, (
        f"setup reported no hook, on a project that ships one — the file was not seen:\n{out[-800:]}"
    )
    assert out.index("ok  setup") < out.index("ok  install"), (
        f"setup must complete before install's own body, not after it:\n{out[-800:]}"
    )
