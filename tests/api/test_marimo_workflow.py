"""Tests for the rhiza_marimo.yml workflow configuration."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_marimo.yml"


def _list_notebooks_steps(root: Path) -> list[dict]:
    """Return the steps of the ``list-notebooks`` job.

    Args:
        root: Repository root.

    Returns:
        The job's step list.
    """
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)
    return workflow["jobs"]["list-notebooks"]["steps"]


def test_marimo_notebook_folder_comes_from_the_cli(root):
    """The notebook folder must come from a pinned rhiza-task, not from make's namespace.

    This step used to synthesise a makefile on stdin and read ``MARIMO_FOLDER`` out of
    make's variable namespace. That put a root ``Makefile`` -- and the variable's presence
    inside it -- into the reusable contract, which a consumer that has migrated to the
    ``rhiza-task`` CLI satisfies only by keeping an ``-include .rhiza/.env`` alive for this
    one probe. The CLI reads ``.rhiza/.env`` itself, so a repo on the synced make layer
    sees no change.

    The pin is asserted for the reason #1546 pins the OS matrix: an unpinned
    ``uvx rhiza-task`` would let the folder move under a workflow called at a tag.
    """
    steps = _list_notebooks_steps(root)
    notebooks_step = next(step for step in steps if step.get("id") == "notebooks")

    # Comment lines are stripped before the negative assertion: the step documents the
    # retired invocation verbatim, and a test that cannot tell an explanation from a
    # command would forbid saying what changed.
    script = "\n".join(line for line in notebooks_step["run"].splitlines() if not line.lstrip().startswith("#"))

    assert re.search(r"uvx rhiza-task@\d+\.\d+\.\d+ print marimo_folder", script), (
        f"the notebook folder must come from a pinned rhiza-task, got: {script!r}"
    )
    assert "-f Makefile" not in script, (
        "reading MARIMO_FOLDER out of make's namespace forces a migrated consumer "
        "to keep a Makefile include alive for this one probe"
    )


def test_marimo_list_notebooks_installs_uv(root):
    """``list-notebooks`` must install uv, or ``uvx`` is not on PATH.

    Only ``test-notebooks`` installed it before: this job's sole dependency was make.
    """
    steps = _list_notebooks_steps(root)

    assert any("astral-sh/setup-uv@" in step.get("uses", "") for step in steps), (
        "list-notebooks calls uvx, so it must install uv first"
    )
