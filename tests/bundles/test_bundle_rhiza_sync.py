"""Tests that files in bundle .rhiza/ directories are identical to root .rhiza/ files.

Each bundle that ships a .rhiza/ subdirectory is the authoritative source for those
files. The root .rhiza/ directory is the union of all those bundle-owned files, so
every bundle file must byte-for-byte match its root counterpart.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _bundle_rhiza_pairs() -> list[tuple[str, Path, Path]]:
    """Return (label, bundle_file, root_file) for every .rhiza/ file in every bundle."""
    pairs: list[tuple[str, Path, Path]] = []
    bundles_dir = _ROOT / "bundles"
    rhiza_root = _ROOT / ".rhiza"

    if not bundles_dir.is_dir():
        return pairs

    for bundle_dir in sorted(bundles_dir.iterdir()):
        if not bundle_dir.is_dir():
            continue
        bundle_rhiza = bundle_dir / ".rhiza"
        if not bundle_rhiza.is_dir():
            continue
        for file_path in sorted(bundle_rhiza.rglob("*")):
            if not file_path.is_file():
                continue
            if "__pycache__" in file_path.parts:
                continue
            relative = file_path.relative_to(bundle_rhiza)
            root_file = rhiza_root / relative
            label = f"{bundle_dir.name}/{relative}"
            pairs.append((label, file_path, root_file))

    return pairs


_PAIRS = _bundle_rhiza_pairs()


class TestBundleRhizaSync:
    """Verify that every bundle .rhiza/ file is byte-for-byte identical to root .rhiza/."""

    @pytest.mark.parametrize(
        ("label", "bundle_file", "root_file"),
        _PAIRS,
        ids=[p[0] for p in _PAIRS],
    )
    def test_bundle_file_matches_root(self, label: str, bundle_file: Path, root_file: Path) -> None:
        """Each bundle .rhiza/ file must exist in and match the root .rhiza/ directory."""
        assert root_file.exists(), f"{label}: missing from root .rhiza/ ({root_file.relative_to(_ROOT)})"
        assert bundle_file.read_bytes() == root_file.read_bytes(), (
            f"{label}: content differs between bundle and root .rhiza/"
        )
