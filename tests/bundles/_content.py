"""Shared helpers for the bundle-content suites.

Extracted from ``test_bundle_content_validity.py`` when that module was split (#1514).
It had grown to 864 lines and ranked **C (7.99)** on radon's maintainability index — the
only module in the repo below B — while carrying eleven unrelated test classes behind a
single set of helpers.

The three suites that came out of it (``test_bundle_parse_validity``,
``test_bundle_ci_content`` and the remainder of ``test_bundle_content_validity``) all
walk the same bundle tree and resolve the same bundle list, so those helpers live here
rather than being duplicated or re-imported across sibling test modules.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml


def _all_files_in_bundle(bundle_dir: Path) -> list[Path]:
    """Return every real file (resolving symlinks) inside a bundle directory."""
    files: list[Path] = []
    for dirpath, _dirs, filenames in os.walk(bundle_dir, followlinks=True):
        for name in filenames:
            p = Path(dirpath) / name
            if p.is_file():
                files.append(p)
    return files


def _load_bundle_names(root: Path) -> list[str]:
    """Return bundle names from .rhiza/template-bundles.yml."""
    bundles_file = root / ".rhiza" / "template-bundles.yml"
    if not bundles_file.exists():
        return []
    with bundles_file.open() as f:
        data = yaml.safe_load(f)
    return list(data.get("bundles", {}).keys())


def _language_layer_bundles(root: Path) -> list[str]:
    """Return the bundles declaring ``layer: language`` (python-core, rust-core, ...).

    Derived from the YAML rather than hard-coded, so a third language layer is
    covered by the layer-wide guards below the moment it is declared.
    """
    bundles_file = root / ".rhiza" / "template-bundles.yml"
    with bundles_file.open() as f:
        data = yaml.safe_load(f)
    return sorted(name for name, config in data.get("bundles", {}).items() if (config or {}).get("layer") == "language")


# Computed at import time: the layer-wide guards parametrise over it at collection time,
# so it cannot be a fixture.
_LAYER_BUNDLES = _language_layer_bundles(Path(__file__).resolve().parents[2])
