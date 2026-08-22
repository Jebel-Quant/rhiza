"""``pyproject.toml``'s uv dependency groups, here and in the core bundle.

Split from ``test_bundle_combinations.py`` in #1514. Two independent properties: the
declared groups exist and carry what the gates import, and no group declares a tool that
the Makefile provisions on the fly via ``uv run --with`` — a duplicate declaration that
would drift out of step with the recipe that actually pins it.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement


def _group_has_dependency(group: list[str], package_name: str) -> bool:
    """Return True if a dependency group contains a given package name (exact match)."""
    return any(Requirement(dep).name.lower() == package_name.lower() for dep in group)


def test_pyproject_declares_uv_dependency_groups(root: Path) -> None:
    """pyproject.toml should expose test/docs uv groups for focused installs."""
    with (root / "pyproject.toml").open("rb") as fh:
        pyproject = tomllib.load(fh)

    groups = pyproject.get("dependency-groups", {})
    # 'lint' is deliberately not in this set (#1484) — prek/uvx provision every linter,
    # so the group had nothing to hold and existed only as `lint = []`.
    assert {"test", "docs"} <= set(groups)

    # The test group declares exactly the third-party libraries `tests/` imports.
    # python-dotenv used to sit here too, and was the clearest case of the drift this
    # test now guards (#1484): nothing under tests/ imports it, and its one consumer —
    # pytest-rhiza's test_docstrings check — is run by `rhiza-test`, which
    # injects `--with python-dotenv` itself.
    assert _group_has_dependency(groups["test"], "pytest")
    assert _group_has_dependency(groups["test"], "pyyaml")
    assert _group_has_dependency(groups["test"], "defusedxml")
    assert _group_has_dependency(groups["test"], "packaging")

    # The docs group declares the notebook imports so deptry can resolve them.
    assert _group_has_dependency(groups["docs"], "marimo")
    assert _group_has_dependency(groups["docs"], "numpy")
    assert _group_has_dependency(groups["docs"], "pandas")
    assert _group_has_dependency(groups["docs"], "plotly")


_PROVISIONED_ON_THE_FLY = frozenset(
    {
        "ty",
        "mypy",
        "typer",
        "ruff",
        "interrogate",
        "pre-commit",
        "prek",
        "deptry",
        "bandit",
        "hypothesis",
        "pip-licenses",
        "pytest-cov",
        "pytest-xdist",
        "pytest-html",
        "pytest-timeout",
        "pytest-mock",
        "pytest-benchmark",
    }
)


def test_no_dependency_group_declares_an_on_the_fly_tool(root: Path) -> None:
    """No [dependency-groups] entry may duplicate a tool its make target already injects."""
    with (root / "pyproject.toml").open("rb") as fh:
        pyproject = tomllib.load(fh)

    offenders = {
        f"{group}:{Requirement(dep).name}"
        for group, deps in pyproject.get("dependency-groups", {}).items()
        for dep in deps
        if Requirement(dep).name.lower() in _PROVISIONED_ON_THE_FLY
    }
    assert not offenders, (
        "these dependency-group entries duplicate a tool provisioned by `uv run --with` "
        f"or `uvx`; remove them and let the make target own the version: {sorted(offenders)}"
    )


def test_core_bundle_pyproject_declares_uv_dependency_groups(test_data_dir: Path) -> None:
    """The starter pyproject fixture must expose the test/docs groups.

    The path is tests/resources/pyproject.toml, not a bundle file: no bundle ships a
    pyproject.toml at all, so this is the example skeleton rather than synced content.
    'lint' left the expected set in #1484 along with the group itself.
    """
    pyproject_path = test_data_dir / "pyproject.toml"
    assert pyproject_path.is_file(), f"{test_data_dir / 'pyproject.toml'} not found"

    with pyproject_path.open("rb") as fh:
        pyproject = tomllib.load(fh)

    groups = pyproject.get("dependency-groups", {})
    assert {"test", "docs"} <= set(groups), f"{pyproject_path} is missing dependency groups; found: {set(groups)}"
