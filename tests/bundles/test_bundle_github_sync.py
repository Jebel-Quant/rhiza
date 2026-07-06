"""Tests that dogfooded .github/ platform-config files match their bundle source.

Most root dogfood files are symlinks into ``bundles/`` (single source of truth). A
handful cannot be: GitHub reads ``.github/`` platform config (Dependabot, release
notes, secret-scanning, the PR template, rulesets) directly from the tree and does
**not** resolve symlinks, so those files must be real copies at the repo root. Their
counterparts in ``bundles/github/.github/`` therefore stay real too, and this test is
the guard that the two never drift.

Workflow files under ``.github/workflows/`` are intentionally excluded: the mother
repo ships its own live reusable workflows there, which differ by design from the
stub workflows the github bundle injects into downstream projects.

The check is driven from the bundle side, restricted to files the mother repo
actually dogfoods (i.e. a same-path root counterpart exists). Bundle-only files such
as ISSUE_TEMPLATE/ and DISCUSSION_TEMPLATE/ have no root twin and are skipped.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _github_dogfood_pairs() -> list[tuple[str, Path, Path]]:
    """Return (label, bundle_file, root_file) for each dogfooded .github/ copy.

    A pair is included when a non-workflow file in ``bundles/github/.github/`` has a
    same-path counterpart at the repository root — the set the mother repo dogfoods.
    """
    pairs: list[tuple[str, Path, Path]] = []
    bundle_github = _ROOT / "bundles" / "github" / ".github"
    if not bundle_github.is_dir():
        return pairs

    for bundle_file in sorted(bundle_github.rglob("*")):
        if not bundle_file.is_file() or "__pycache__" in bundle_file.parts:
            continue
        relative = bundle_file.relative_to(bundle_github)
        if relative.parts and relative.parts[0] == "workflows":
            continue  # live mother-repo workflows differ from bundle stubs by design
        root_file = _ROOT / ".github" / relative
        if not root_file.exists():
            continue  # bundle-only file (e.g. ISSUE_TEMPLATE/) — not dogfooded here
        pairs.append((f".github/{relative}", bundle_file, root_file))

    return pairs


_PAIRS = _github_dogfood_pairs()


class TestBundleGithubSync:
    """Verify dogfooded .github/ copies stay byte-identical to their bundle source."""

    def test_dogfood_set_is_nonempty(self) -> None:
        """At least one .github/ file must be dogfooded.

        Without this guard the parametrized test below would silently produce zero
        cases (e.g. after a refactor that moved the files), making CI appear green
        while the sync check never ran.
        """
        assert _PAIRS, (
            "No dogfooded .github/ files found — the github bundle moved its platform "
            "config, or the mother repo stopped dogfooding it; update this test."
        )

    @pytest.mark.parametrize(
        ("label", "bundle_file", "root_file"),
        _PAIRS,
        ids=[p[0] for p in _PAIRS],
    )
    def test_dogfooded_github_file_matches_bundle(self, label: str, bundle_file: Path, root_file: Path) -> None:
        """Each dogfooded .github/ copy must byte-match its bundle source.

        These files cannot be symlinks (GitHub does not follow symlinks for platform
        config), so unlike the symlinked dogfood files they can drift — edit both
        sides together, or the copies fall out of sync.
        """
        assert not root_file.is_symlink(), (
            f"{label}: must be a real file — GitHub does not resolve symlinks for .github/ "
            f"platform config (Dependabot, Actions, etc.)"
        )
        assert root_file.read_bytes() == bundle_file.read_bytes(), (
            f"{label}: dogfooded copy differs from bundle source "
            f"{bundle_file.relative_to(_ROOT)} — edit both sides to keep them in sync"
        )
