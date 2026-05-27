"""Bundle × platform compatibility matrix tests.

Generates every bundle × platform pair from template-bundles.yml and verifies
that the combination produces valid, non-conflicting output.  The matrix is
built dynamically at collection time using itertools.product so no manual
enumeration is needed.

Assertions per (bundle, platform) combination:
  - No YAML parse errors in any file delivered by the expanded bundle set
  - No deployment path is claimed by two bundles (file ownership conflict)
  - Every bundle referenced in a ``requires`` list is present in template-bundles.yml
"""

from __future__ import annotations

import itertools
import os
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLATFORMS = ["github", "gitlab"]

_YAML_EXTENSIONS = {".yml", ".yaml"}

# mkdocs config files use !!python/name: YAML tags that yaml.safe_load cannot
# parse — skip them for the YAML parse test (they are validated separately).
_YAML_SAFE_LOAD_SKIP = {"mkdocs-base.yml", "mkdocs.yml"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_bundles_data(root: Path) -> dict:
    """Load and return the parsed content of .rhiza/template-bundles.yml."""
    bundles_file = root / ".rhiza" / "template-bundles.yml"
    if not bundles_file.exists():
        pytest.skip("template-bundles.yml not found")
    with bundles_file.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _transitive_closure(seeds: list[str], bundles: dict) -> set[str]:
    """Return the full transitive ``requires`` closure starting from *seeds*.

    Unknown bundle names (not present in *bundles*) are silently included in
    the returned set so that callers can detect them and report an error.
    """
    closure: set[str] = set()
    queue = list(seeds)
    while queue:
        name = queue.pop()
        if name in closure:
            continue
        closure.add(name)
        if name in bundles:
            queue.extend(bundles[name].get("requires", []))
    return closure


def _deployment_paths(bundle_dir: Path) -> list[str]:
    """Return all deployment-relative paths for *bundle_dir*.

    Directory symlinks are treated as atomic entries (not recursed into);
    plain files and file symlinks are each listed individually.
    """
    paths: list[str] = []
    for dirpath, dirs, files in os.walk(bundle_dir, followlinks=False):
        current = Path(dirpath)
        for d in dirs[:]:
            child = current / d
            if child.is_symlink():
                dirs.remove(d)
                paths.append(str(child.relative_to(bundle_dir)))
        for f in files:
            paths.append(str((current / f).relative_to(bundle_dir)))
    return paths


def _yaml_files_in_bundle(bundle_dir: Path) -> list[Path]:
    """Return all YAML files inside *bundle_dir*, following symlinks."""
    results: list[Path] = []
    for dirpath, _dirs, files in os.walk(bundle_dir, followlinks=True):
        for fname in files:
            p = Path(dirpath) / fname
            if p.suffix in _YAML_EXTENSIONS and p.name not in _YAML_SAFE_LOAD_SKIP:
                results.append(p)
    return results


def _expanded_bundle_set(bundle_name: str, platform: str, bundles: dict) -> set[str]:
    """Return the transitive closure of *bundle_name* plus the *platform* bundle."""
    return _transitive_closure([bundle_name, platform], bundles)


# ---------------------------------------------------------------------------
# Matrix generation (evaluated once at collection time)
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent.parent
_BUNDLES_FILE = _ROOT / ".rhiza" / "template-bundles.yml"

if _BUNDLES_FILE.exists():
    with _BUNDLES_FILE.open(encoding="utf-8") as _fh:
        _ALL_DATA: dict = yaml.safe_load(_fh) or {}
else:
    _ALL_DATA = {}

_ALL_BUNDLES: dict = _ALL_DATA.get("bundles", {})
_ALL_BUNDLE_NAMES: list[str] = list(_ALL_BUNDLES.keys())

# Full matrix: every bundle name × every CI platform
_MATRIX: list[tuple[str, str]] = list(itertools.product(_ALL_BUNDLE_NAMES, PLATFORMS))
_MATRIX_IDS: list[str] = [f"{b}\u00d7{p}" for b, p in _MATRIX]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("bundle_name", "platform"), _MATRIX, ids=_MATRIX_IDS)
class TestBundlePlatformMatrix:
    """Compatibility matrix: every bundle × every CI platform (GitHub / GitLab).

    Each parametrised instance expands the bundle's transitive dependency
    closure together with the chosen platform bundle and then validates
    three independent invariants for that combination.
    """

    def test_no_yaml_parse_errors(self, root: Path, bundle_name: str, platform: str) -> None:
        """All YAML files in the expanded bundle set parse without error."""
        bundles_root = root / "bundles"
        expanded = _expanded_bundle_set(bundle_name, platform, _ALL_BUNDLES)
        errors: list[str] = []

        for name in sorted(expanded):
            bundle_dir = bundles_root / name
            if not bundle_dir.is_dir():
                continue
            for yaml_path in _yaml_files_in_bundle(bundle_dir):
                try:
                    with yaml_path.open(encoding="utf-8") as fh:
                        yaml.safe_load(fh)
                except yaml.YAMLError as exc:
                    rel = yaml_path.relative_to(bundle_dir)
                    errors.append(f"  [{name}] {rel}: {exc}")

        if errors:
            pytest.fail(
                f"YAML parse errors in ({bundle_name}\u00d7{platform}) combination:\n"
                + "\n".join(errors)
            )

    def test_no_file_ownership_conflict(self, root: Path, bundle_name: str, platform: str) -> None:
        """No deployment path is claimed by two bundles in the combination."""
        bundles_root = root / "bundles"
        expanded = _expanded_bundle_set(bundle_name, platform, _ALL_BUNDLES)
        path_owners: dict[str, list[str]] = {}

        for name in sorted(expanded):
            bundle_dir = bundles_root / name
            if not bundle_dir.is_dir():
                continue
            for dep_path in _deployment_paths(bundle_dir):
                path_owners.setdefault(dep_path, []).append(name)

        conflicts = {p: owners for p, owners in path_owners.items() if len(owners) > 1}
        if conflicts:
            lines = [f"  {p!r}: owned by {owners}" for p, owners in sorted(conflicts.items())]
            pytest.fail(
                f"File ownership conflicts in ({bundle_name}\u00d7{platform}) combination:\n"
                + "\n".join(lines)
            )

    def test_all_declared_dependencies_present(
        self, root: Path, bundle_name: str, platform: str
    ) -> None:
        """Every bundle referenced in a ``requires`` list exists in template-bundles.yml."""
        expanded = _expanded_bundle_set(bundle_name, platform, _ALL_BUNDLES)
        missing: list[str] = []

        for name in sorted(expanded):
            if name not in _ALL_BUNDLES:
                missing.append(f"  combination references unknown bundle '{name}'")
                continue
            for dep in _ALL_BUNDLES[name].get("requires", []):
                if dep not in _ALL_BUNDLES:
                    missing.append(
                        f"  [{name}] requires unknown bundle '{dep}'"
                    )

        if missing:
            pytest.fail(
                f"Missing bundle dependencies in ({bundle_name}\u00d7{platform}) combination:\n"
                + "\n".join(missing)
            )
