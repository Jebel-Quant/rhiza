"""Every third-party action is pinned to one SHA across live and shipped workflows (#1786).

Most of what the ``github`` bundle ships under ``.github/workflows/`` is a thin stub that
calls a reusable workflow in this repository, so the third-party pins a consumer runs are
the ones in the root ``.github/workflows/`` -- one copy, bumped by Dependabot. Two files
cannot be stubs and ship whole: ``rhiza_release.yml`` (PyPI Trusted Publishing validates
the *calling* file, so a stub would publish under rhiza's identity) and
``rhiza_conda_recipe.yml``. Their pins live in ``bundles/`` as well as at the root.

Nothing bumps the bundle copies. Dependabot's ``github-actions`` entry scans
``directory: "/"`` -- the root ``.github/workflows`` only -- and Renovate's
``enabledManagers`` leaves ``github-actions`` out. So a Dependabot bump moved the live
copies and left the shipped ones behind, and consumers inherited a release workflow --
the one holding ``id-token: write`` -- running older actions than this repo does.

The rule is stated over *all* workflow files rather than those two by name, so a third
workflow that starts shipping whole is covered without anyone remembering this test:
each third-party action resolves to exactly one ref. A bump that touches only one copy
fails here, naming every file on each side of the split.

Out of scope by design: local actions (``./...``), which have no ref, and this
repository's own reusable workflows (``jebel-quant/rhiza/...``), which stubs pin to a
release tag that ``[[tool.bumpversion.files]]`` rewrites on every release.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]

# This repository's own reusable workflows are tag-pinned and moved by bump-my-version.
_SELF_PREFIX = "jebel-quant/rhiza/"


def _workflow_files() -> list[Path]:
    """Return every GitHub workflow and composite-action file, live and shipped."""
    roots = [_ROOT / ".github", *sorted((_ROOT / "bundles").glob("*/.github"))]
    files: list[Path] = []
    for root in roots:
        files.extend(sorted((root / "workflows").glob("*.yml")))
        files.extend(sorted((root / "workflows").glob("*.yaml")))
        files.extend(sorted(root.glob("actions/**/action.yml")))
        files.extend(sorted(root.glob("actions/**/action.yaml")))
    return files


def _uses(node: Any) -> list[str]:
    """Collect every ``uses:`` value in a parsed workflow, at any depth.

    Parsing rather than grepping keeps commented-out examples (``#   uses: ...@v1``)
    out of the result.
    """
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "uses" and isinstance(value, str):
                found.append(value)
            else:
                found.extend(_uses(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_uses(item))
    return found


def _third_party_pins() -> dict[str, dict[str, list[str]]]:
    """Map each third-party action to the refs it is pinned to, and the files using each."""
    pins: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for path in _workflow_files():
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for value in _uses(document):
            if value.startswith(("./", "docker://")) or value.lower().startswith(_SELF_PREFIX):
                continue
            action, sep, ref = value.partition("@")
            if not sep:
                continue
            relative = str(path.relative_to(_ROOT))
            if relative not in pins[action][ref]:
                pins[action][ref].append(relative)
    return pins


class TestActionPinParity:
    """A third-party action never carries two different pins across the tree."""

    def test_the_whole_shipped_workflows_are_in_scope(self) -> None:
        """The two files this guard exists for are found, so it cannot pass vacuously."""
        scanned = {str(p.relative_to(_ROOT)) for p in _workflow_files()}
        for name in ("rhiza_release.yml", "rhiza_conda_recipe.yml"):
            assert f"bundles/github/.github/workflows/{name}" in scanned
            assert f".github/workflows/{name}" in scanned

    def test_shipped_and_live_copies_share_pins(self) -> None:
        """At least one action is pinned in both a bundle and the root, so parity is tested."""
        shared = [
            action
            for action, refs in _third_party_pins().items()
            if any(f.startswith("bundles/") for files in refs.values() for f in files)
            and any(f.startswith(".github/") for files in refs.values() for f in files)
        ]
        assert shared, "no third-party action appears in both a bundle and the live workflows"

    @pytest.mark.parametrize("action", sorted(_third_party_pins()))
    def test_action_has_a_single_pin(self, action: str) -> None:
        """Every use of ``action`` names the same ref, wherever the workflow lives."""
        refs = _third_party_pins()[action]
        if len(refs) > 1:
            detail = "\n".join(f"  @{ref}: {', '.join(files)}" for ref, files in sorted(refs.items()))
            pytest.fail(
                f"{action} is pinned to {len(refs)} different refs; a bump moved only some copies.\n"
                f"Dependabot scans only the root .github/workflows, so the bundle copies are the "
                f"likely laggards -- move them to the live pin.\n{detail}"
            )
