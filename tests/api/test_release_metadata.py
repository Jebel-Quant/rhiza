"""Tests for release metadata required by PyPI and Zenodo."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path


def _load_pyproject(root: Path) -> dict:
    """Load and return the parsed ``pyproject.toml`` file."""
    with (root / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)


def test_pyproject_has_build_backend(root: Path) -> None:
    """The project metadata must define a build backend so release artifacts can be built."""
    pyproject = _load_pyproject(root)

    assert "build-system" in pyproject, "pyproject.toml must define a PEP 517 build backend"
    assert pyproject["tool"]["setuptools"]["packages"] == []


def test_pyproject_retains_pypi_kill_switch(root: Path) -> None:
    """The ``Private :: Do Not Upload`` classifier must remain so PyPI publishing stays disabled."""
    pyproject = _load_pyproject(root)

    assert "Private :: Do Not Upload" in pyproject["project"]["classifiers"], (
        "the PyPI kill-switch classifier must be present until publishing is deliberately enabled"
    )


def test_zenodo_metadata_exists_with_required_fields(root: Path) -> None:
    """Zenodo metadata must exist so published GitHub releases can be archived."""
    pyproject = _load_pyproject(root)
    zenodo_path = root / ".zenodo.json"

    assert zenodo_path.is_file(), ".zenodo.json must exist at the repository root"

    metadata = json.loads(zenodo_path.read_text(encoding="utf-8"))
    assert metadata["title"] == pyproject["project"]["name"]
    assert metadata["description"] == pyproject["project"]["description"]
    assert metadata["license"] == "MIT"
    assert metadata["upload_type"] == "software"
    assert metadata["access_right"] == "open"
    assert metadata["keywords"] == pyproject["project"]["keywords"]
    assert metadata["creators"], ".zenodo.json must declare at least one creator"
    assert all(creator.get("name") for creator in metadata["creators"])
