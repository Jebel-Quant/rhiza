"""The five bundles whose targets moved from `.rhiza/make.d/` into rhiza-task.

Until rhiza-task 0.3.0, `docker`, `github`, `lfs`, `paper` and `presentation` each
shipped a make fragment, and five test modules dry-ran those recipes -- asserting that
`view-prs` emitted `gh pr list`, that `docker.mk` declared `DOCKER_IMAGE_NAME`, and so
on. The fragments are gone; the recipes are task bodies in rhiza-task, with their own
suite, and dry-running the shim now prints one `uvx` line whatever the target.

What is left for *this* repository to assert is narrower and, unlike those dry runs,
guards a risk that did not exist before: the pin. `RHIZA_TASK` is the whole version
contract, so a bump that dropped or renamed a task would take `make view-prs` from every
consumer on the `github-project` profile, and nothing in rhiza would notice -- the shim
resolves any target, and the CLI's "unknown task" error only appears at run time.

So this module reads the pin out of the root Makefile, asks *that exact version* of the
CLI what it knows, and requires every retired target to be in the answer. It needs uv and
the network, and skips cleanly without them, which keeps `make test` green offline.
"""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404 - fixed argument vectors, never shell=True
from pathlib import Path

import pytest

from tests.util import run_make

_ROOT = Path(__file__).resolve().parents[2]
_UVX = shutil.which("uvx")

# Every target the five fragments defined, by the bundle that owned it. The internal
# guards -- `require-gh`, `gh-install`, `require-marp` -- are deliberately absent: two
# were "is this tool installed?" spelled twice because make cannot say it once, and the
# third installed a global npm package as a side effect. rhiza-task says it once, as a
# guard whose failure is a skip carrying the install hint.
BUNDLE_TARGETS = {
    "github": ("view-prs", "view-issues", "failed-workflows", "workflow-status", "latest-release", "whoami"),
    "docker": ("docker-build", "docker-run", "docker-clean"),
    "lfs": ("lfs-install", "lfs-pull", "lfs-track", "lfs-status"),
    "paper": ("paper", "paper-clean"),
    "presentation": ("presentation", "presentation-pdf", "presentation-serve"),
}

ALL_TARGETS = tuple(target for targets in BUNDLE_TARGETS.values() for target in targets)


def pinned_cli() -> str:
    """Return the ``rhiza-task@X.Y.Z`` spec the root Makefile pins.

    Returns:
        The pin, e.g. ``rhiza-task@0.3.0``.
    """
    content = (_ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^RHIZA_TASK \?= (\S+)", content, re.MULTILINE)
    assert match, "the root Makefile must pin RHIZA_TASK -- asserted by test_makefile_targets.py"
    return match.group(1)


@pytest.fixture(scope="module")
def cli_tasks() -> set[str]:
    """Return the task names the pinned rhiza-task exposes.

    Returns:
        Every task name in ``rhiza-task list --all``.
    """
    if _UVX is None:
        pytest.skip("uvx not available; cannot ask the pinned CLI what it knows")
    result = subprocess.run(  # nosec B603
        [_UVX, pinned_cli(), "list", "--all"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=_ROOT,
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        # An unresolvable pin offline is an outage, not a regression. A *wrong* pin fails
        # the same way, which is the one false negative here -- and rhiza_ci.yml runs this
        # with a network, where the distinction stops mattering.
        pytest.skip(f"could not run {pinned_cli()} (offline?):\n{result.stderr[-400:]}")
    # `list` renders a rich table, so the task name is the first column of each row.
    return {line.split()[0] for line in result.stdout.splitlines() if line.strip()}


@pytest.mark.parametrize("bundle", sorted(BUNDLE_TARGETS))
def test_the_pinned_cli_still_provides_the_bundles_targets(bundle: str, cli_tasks: set[str]) -> None:
    """Every target the bundle's retired fragment defined is a task in the pinned CLI.

    Args:
        bundle: The bundle whose targets are checked.
        cli_tasks: What the pinned rhiza-task exposes.
    """
    missing = [target for target in BUNDLE_TARGETS[bundle] if target not in cli_tasks]
    assert not missing, (
        f"the `{bundle}` bundle's targets {missing} are not in {pinned_cli()}. Consumers reach "
        f"these through the shim's catch-all, so a pin that no longer carries them removes the "
        f"targets silently -- `make {missing[0]}` fails only when someone runs it."
    )


def test_the_pinned_cli_still_carries_the_setup_hook(cli_tasks: set[str]) -> None:
    """`setup` is what runs a consumer's `local-setup.sh`, and its loss would be silent.

    Its own case rather than a sixth `BUNDLE_TARGETS` entry, because it is not a retired
    fragment's target -- no bundle ever shipped a `setup` recipe. It is guarded here for a
    sharper reason than the five above. Those fail loudly when someone types the target; this
    one is never typed at all. Every layer's `install` names it as a prerequisite, and an
    unresolvable prerequisite is *skipped* rather than an error -- so a pin that stopped
    carrying it would leave every consumer's `install` quietly running no provisioning hook,
    with every gate still green and a missing native binary as the only symptom.

    Args:
        cli_tasks: What the pinned rhiza-task exposes.
    """
    assert "setup" in cli_tasks, (
        f"{pinned_cli()} has no `setup` task, so `local-setup.sh` would never run. Consumers "
        f"reach it only as a prerequisite of `install`, and a prerequisite the CLI cannot "
        f"resolve is skipped rather than failed -- nothing would report this at run time."
    )


@pytest.mark.parametrize("target", ALL_TARGETS)
def test_the_shim_forwards_each_target_to_the_cli(logger, target: str) -> None:
    """`make <target>` resolves and delegates rather than failing on a missing rule.

    The other half of the contract: the CLI having a task is no use if make cannot reach
    it. Asserted on the dry run's delegation line, since no recipe exists to inspect.

    Args:
        logger: The test logger.
        target: The target to resolve.
    """
    result = run_make(logger, [target], check=False)
    assert result.returncode == 0, f"`make {target}` did not resolve: {result.stderr}"
    assert "no rule to make target" not in result.stderr.lower(), (
        f"{target} resolves to nothing -- the `%:` catch-all should have forwarded it"
    )
    assert "rhiza-task" in result.stdout, f"`make -n {target}` should print the CLI delegation; got:\n{result.stdout}"
