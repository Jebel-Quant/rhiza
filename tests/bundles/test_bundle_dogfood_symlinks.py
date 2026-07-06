"""Guard the dogfood symlink invariant: root copies are symlinks into ``bundles/``.

Rhiza dogfoods its own templates. ``bundles/`` is the single source of truth, and every
root file that also ships in a bundle is a **relative symlink** into its owning bundle —
so one edit in the bundle propagates automatically. A small, documented set of files
**cannot** be symlinks and stay as real copies (see :func:`link_dogfood.is_dogfood_carveout`
and the dogfood section of ``CLAUDE.md``).

This module is the automated guard for that model. For every git-tracked root path that has
a same-path bundle counterpart it asserts one of two states holds, and fails otherwise:

* **carve-out** — the path is on the documented carve-out list, so it must be a *real file*
  (never a symlink); or
* **dogfood copy** — the path must be a *symlink resolving into* ``bundles/`` whose target
  exists and is byte-identical to its bundle source.

The failure that matters most is a byte-identical *plain-file duplicate* that is neither a
carve-out nor a symlink: that means someone added a bundle file without running
``make sync-self``, or a ``rhiza sync .`` re-materialised a copy — silently breaking the
single-source-of-truth guarantee. The check is driven by the very same helpers the linker
uses (:mod:`link_dogfood`), so the guard and the linker can never disagree about the rules.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _load_link_dogfood() -> ModuleType:
    """Import ``utils/link_dogfood.py`` as a module.

    ``utils/`` is not a package, so it is loaded from its file path — the same approach
    the ``explain_bundles`` tests use — to reuse the linker's carve-out predicate and
    bundle-indexing helpers verbatim rather than reimplementing them here.

    Returns:
        The imported ``link_dogfood`` module.
    """
    module_path = _ROOT / "utils" / "link_dogfood.py"
    spec = importlib.util.spec_from_file_location("link_dogfood", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_LINK_DOGFOOD = _load_link_dogfood()


def _dogfood_paths() -> tuple[list[str], list[str]]:
    """Split tracked root paths that have a bundle twin into carve-outs and dogfood copies.

    A path qualifies when git tracks it, it is not itself under ``bundles/``, and a bundle
    provides the same bundle-relative path. It is a carve-out when
    :func:`link_dogfood.is_dogfood_carveout` says so; otherwise it is expected to be a
    symlink into ``bundles/``.

    Returns:
        A ``(carveouts, dogfood_copies)`` pair of repo-root-relative POSIX path lists.
    """
    index = _LINK_DOGFOOD._bundle_index(_ROOT / "bundles")
    carveouts: list[str] = []
    dogfood_copies: list[str] = []
    for rel in _LINK_DOGFOOD._tracked_files(_ROOT):
        if rel.startswith("bundles/") or rel not in index:
            continue
        if _LINK_DOGFOOD.is_dogfood_carveout(rel):
            carveouts.append(rel)
        else:
            dogfood_copies.append(rel)
    return sorted(carveouts), sorted(dogfood_copies)


_CARVEOUTS, _DOGFOOD_COPIES = _dogfood_paths()


class TestDogfoodSymlinks:
    """Verify the root dogfood tree matches the single-source-of-truth symlink model."""

    def test_dogfood_copy_set_is_nonempty(self) -> None:
        """At least one dogfood symlink must exist.

        Without this guard the parametrised test below would silently collect zero cases
        (e.g. after a refactor that moved the bundle tree), making CI look green while the
        symlink invariant went entirely unchecked.
        """
        assert _DOGFOOD_COPIES, (
            "No dogfood symlink candidates found — the bundle layout moved or the mother "
            "repo stopped dogfooding it; update this test."
        )

    @pytest.mark.parametrize("rel", _DOGFOOD_COPIES, ids=_DOGFOOD_COPIES or ["<none>"])
    def test_dogfood_copy_is_symlink_into_bundles(self, rel: str) -> None:
        """Each non-carve-out dogfood path must be a symlink into a byte-identical bundle source.

        This is the drift catch: a real file here means a bundle twin was left un-linked
        (add a file then forget ``make sync-self``, or a ``rhiza sync`` re-materialised a
        copy), silently forking the single source of truth.
        """
        link = _ROOT / rel
        assert link.is_symlink(), (
            f"{rel}: has a bundle counterpart but is a real file, not a symlink — run "
            f"'make sync-self', or add it to link_dogfood._EXCLUDE if it is a deliberate "
            f"mother-repo override."
        )
        resolved = link.resolve()
        assert resolved.exists(), f"{rel}: dangling symlink -> {resolved}"
        try:
            relative_target = resolved.relative_to(_ROOT)
        except ValueError:
            relative_target = None
        assert relative_target is not None, f"{rel}: symlink escapes the repo, resolves to {resolved}"
        assert relative_target.parts[0] == "bundles", (
            f"{rel}: symlink must resolve into bundles/, resolves to {resolved}"
        )
        owners = _LINK_DOGFOOD._bundle_index(_ROOT / "bundles")[rel]
        assert resolved in {owner.resolve() for owner in owners}, (
            f"{rel}: symlink target {relative_target} is not a bundle owner of this path"
        )
        assert link.read_bytes() == resolved.read_bytes(), (
            f"{rel}: symlink content differs from its bundle source {relative_target}"
        )

    @pytest.mark.parametrize("rel", _CARVEOUTS, ids=_CARVEOUTS or ["<none>"])
    def test_carveout_stays_a_real_file(self, rel: str) -> None:
        """Each documented carve-out must remain a real file, never a symlink.

        The carve-outs exist precisely because a symlink breaks them (GitHub does not
        resolve symlinks for ``.github/`` config, git opens ``O_NOFOLLOW`` files without
        following links, and coverage would drop a symlinked ``.rhiza/utils/`` target). If
        one silently became a symlink the breakage would be subtle, so assert it directly.
        """
        assert not (_ROOT / rel).is_symlink(), (
            f"{rel}: is a documented dogfood carve-out and must stay a real file, but it is "
            f"a symlink — GitHub/git/coverage do not resolve symlinks for these paths."
        )
