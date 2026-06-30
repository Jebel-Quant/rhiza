# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Replace the mother repo's dogfood copies with relative symlinks into ``bundles/``.

Rhiza dogfoods its own templates: many files exist both as the authoritative source
in ``bundles/<name>/...`` and as a byte-identical copy at the repository root. This
script makes ``bundles/`` the single source of truth by turning each such root copy
into a **relative** symlink pointing at its owning bundle file, so a single edit in
the bundle propagates automatically.

Only root files that are byte-identical to exactly one bundle source are linked.
Intentional mother-repo overrides (files that deliberately diverge from their bundle
source) and root-only files are listed in ``_EXCLUDE`` and left untouched. The script
is idempotent: correct symlinks are left as-is, and a copy that reappears (e.g. after
a local ``rhiza sync .``) is re-linked.

It is mother-repo-only tooling. Downstream consumers never run it — ``rhiza sync``
resolves symlinks to real content, so synced projects only ever receive real files.

Example:
    Invoke through the Makefile target (the supported entry point)::

        $ make sync-self

    or run the module directly from the repository root::

        $ python utils/link_dogfood.py
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - git is invoked with a fixed, non-user argument list
import sys
from pathlib import Path

_GIT = shutil.which("git") or "/usr/bin/git"

BLUE = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"

# Root files that must NOT be symlinked. Each either deliberately diverges from its
# bundle source (a documented mother-repo override) or has no single bundle owner.
# Keep this list in sync with the dogfood section of CLAUDE.md.
_EXCLUDE = frozenset(
    {
        ".claude/commands/rhiza_quality.md",  # mother-repo variant (no src/, rhiza-test gate)
        ".gitignore",  # mother-repo additions
        ".pre-commit-config.yaml",  # mother-repo additions
        ".python-version",  # mother-repo pinned version
        "SECURITY.md",  # mother-repo variant
        "renovate.json",  # mother-repo variant
    }
)

# Git opens these files with O_NOFOLLOW (a security measure), so a symlinked copy
# yields ELOOP — git warns on every command and silently ignores the file's rules.
# They must stay real files wherever they appear, so match them by basename.
_NO_FOLLOW_NAMES = frozenset({".gitignore", ".gitattributes", ".gitmodules", ".mailmap"})


def _bundle_index(bundles_dir: Path) -> dict[str, list[Path]]:
    """Map each bundle-relative path to the bundle files that provide it.

    Args:
        bundles_dir: The ``bundles/`` directory to scan.

    Returns:
        A mapping from a path *relative to its bundle* (e.g. ``.rhiza/rhiza.mk``)
        to the list of concrete bundle files at that path across all bundles.
    """
    index: dict[str, list[Path]] = {}
    for path in bundles_dir.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = Path(*path.relative_to(bundles_dir).parts[1:])  # drop the bundle name
        index.setdefault(str(relative), []).append(path)
    return index


def _tracked_files(root: Path) -> list[str]:
    """Return git-tracked paths, relative to the repository root, as POSIX strings.

    Args:
        root: The repository root (the directory containing ``.git``).

    Returns:
        The list of tracked file paths reported by ``git ls-files``.
    """
    result = subprocess.run(  # noqa: S603  # nosec B603 - resolved git path, fixed args, no shell
        [_GIT, "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _link_one(root: Path, rel: str, source: Path) -> bool:
    """Point the root file ``rel`` at its bundle ``source`` via a relative symlink.

    Args:
        root: The repository root.
        rel: The dogfood file path relative to ``root``.
        source: The owning bundle file the symlink should target.

    Returns:
        True if a new symlink was created, False if it was already correct.
    """
    link = root / rel
    target = os.path.relpath(source, start=link.parent)
    if link.is_symlink() and os.readlink(link) == target:
        return False
    link.unlink()
    link.symlink_to(target)
    return True


def relink(root: Path) -> int:
    """Convert every eligible root dogfood copy into a relative symlink.

    A root file is eligible when it is tracked by git, not in ``_EXCLUDE``, and
    byte-identical to exactly one bundle source. Ambiguous matches (identical to
    more than one bundle) are skipped with a warning rather than guessed.

    Args:
        root: The repository root containing ``bundles/`` and the dogfood files.

    Returns:
        Process exit code: ``0`` on success, ``1`` if any file was ambiguous.
    """
    bundles_dir = root / "bundles"
    if not bundles_dir.is_dir():
        sys.exit(f"{YELLOW}No bundles/ directory found at {root} — run from the rhiza repo root.{RESET}")

    index = _bundle_index(bundles_dir)
    linked = 0
    unchanged = 0
    ambiguous: list[str] = []

    for rel in _tracked_files(root):
        # Skip bundle sources themselves, declared overrides, git-special files that
        # git opens with O_NOFOLLOW, the .github/ tree (GitHub platform features —
        # Dependabot, Actions, PR templates, secret scanning, rulesets — read these
        # blobs directly and do NOT resolve symlinks), and .rhiza/utils/ (the coverage
        # target of `make rhiza-test`: coverage canonicalises a symlink to its realpath,
        # so --cov=.rhiza/utils would match nothing). All must stay real files.
        if rel in _EXCLUDE or rel.startswith(("bundles/", ".github/", ".rhiza/utils/")):
            continue
        if Path(rel).name in _NO_FOLLOW_NAMES:
            continue
        owners = index.get(rel)
        if not owners:
            continue
        root_bytes = (root / rel).read_bytes()
        identical = [o for o in owners if o.read_bytes() == root_bytes]
        if not identical:
            continue  # diverges from every owner — an (undeclared) override; leave it real
        if len(identical) > 1:
            ambiguous.append(rel)
            continue
        if _link_one(root, rel, identical[0]):
            print(f"  {GREEN}linked{RESET}    {rel} {DIM}->{RESET} {identical[0].relative_to(root)}")
            linked += 1
        else:
            unchanged += 1

    print(f"\n{BLUE}sync-self:{RESET} {linked} linked, {unchanged} already correct, {len(ambiguous)} ambiguous")
    if ambiguous:
        for rel in ambiguous:
            print(f"  {YELLOW}ambiguous{RESET} {rel} matches multiple bundles — link it by hand")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(relink(Path(__file__).resolve().parent.parent))
