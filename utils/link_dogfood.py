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


def is_dogfood_carveout(rel: str) -> bool:
    """Report whether root dogfood path ``rel`` must stay a real file, not a symlink.

    A carve-out is a root file that has a bundle counterpart but deliberately is *not*
    linked into ``bundles/``. Three reasons, all documented in the dogfood section of
    ``CLAUDE.md``:

    * it is a declared mother-repo override in :data:`_EXCLUDE`;
    * it lives under ``.github/`` (GitHub reads platform config blobs directly and does
      not resolve symlinks) or ``.rhiza/utils/`` (the ``make rhiza-test`` coverage target,
      whose realpath a symlink would move out of ``--cov`` scope); or
    * git opens it with ``O_NOFOLLOW`` (see :data:`_NO_FOLLOW_NAMES`), so a symlink yields
      an ELOOP warning and the file's rules are silently ignored.

    Both :func:`relink` and the dogfood-integrity test consult this single predicate so
    the linker and its guard can never disagree about what is allowed to be a real copy.

    Args:
        rel: A repository-root-relative path (POSIX form, as ``git ls-files`` reports it).

    Returns:
        True if ``rel`` must remain a real file; False if it is eligible for symlinking.
    """
    return rel in _EXCLUDE or rel.startswith((".github/", ".rhiza/utils/")) or Path(rel).name in _NO_FOLLOW_NAMES


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


def _link_is_current(root: Path, rel: str, source: Path) -> bool:
    """Report whether ``rel`` is already the correct relative symlink to ``source``.

    Args:
        root: The repository root.
        rel: The dogfood file path relative to ``root``.
        source: The owning bundle file the symlink should target.

    Returns:
        True if ``rel`` is a symlink already pointing at ``source``, False otherwise
        (missing symlink, real file, or symlink to a different target).
    """
    link = root / rel
    target = os.path.relpath(source, start=link.parent)
    return link.is_symlink() and os.readlink(link) == target


def _link_one(root: Path, rel: str, source: Path) -> bool:
    """Point the root file ``rel`` at its bundle ``source`` via a relative symlink.

    Args:
        root: The repository root.
        rel: The dogfood file path relative to ``root``.
        source: The owning bundle file the symlink should target.

    Returns:
        True if a new symlink was created, False if it was already correct.
    """
    if _link_is_current(root, rel, source):
        return False
    link = root / rel
    target = os.path.relpath(source, start=link.parent)
    link.unlink()
    link.symlink_to(target)
    return True


def _classify_dogfood(root: Path, rel: str, index: dict[str, list[Path]]) -> tuple[str, Path | None]:
    """Classify a tracked root path for dogfood linking.

    This is the eligibility decision for a single file, factored out of
    :func:`relink` so the loop there stays a straight-line consumer of the verdict.

    Args:
        root: The repository root.
        rel: A repository-root-relative path (POSIX form, as ``git ls-files`` reports it).
        index: The bundle index from :func:`_bundle_index`.

    Returns:
        A ``(kind, source)`` verdict:

        * ``("skip", None)`` — not an eligible dogfood copy: a bundle source itself,
          a carve-out, a path with no bundle owner, or one that diverges from every
          owner (an undeclared mother-repo override that must stay a real file);
        * ``("ambiguous", None)`` — byte-identical to more than one bundle source, so
          the linker refuses to guess an owner;
        * ``("link", source)`` — should be a relative symlink to the unique bundle
          file ``source``.
    """
    # Skip bundle sources themselves and every carve-out (declared overrides,
    # git O_NOFOLLOW files, the .github/ tree, and .rhiza/utils/) — all must stay
    # real files. See is_dogfood_carveout for the reasoning behind each case.
    if rel.startswith("bundles/") or is_dogfood_carveout(rel):
        return ("skip", None)
    owners = index.get(rel)
    if not owners:
        return ("skip", None)
    root_bytes = (root / rel).read_bytes()
    identical = [o for o in owners if o.read_bytes() == root_bytes]
    if not identical:
        return ("skip", None)  # diverges from every owner — an (undeclared) override; leave it real
    if len(identical) > 1:
        return ("ambiguous", None)
    return ("link", identical[0])


def _report(*, check: bool, linked: int, unchanged: int, ambiguous: list[str], pending: list[str]) -> int:
    """Print the run summary and return the process exit code.

    Args:
        check: Whether the run was a non-writing drift check.
        linked: Number of symlinks created (write mode).
        unchanged: Number of files already correct.
        ambiguous: Paths that matched more than one bundle source.
        pending: Paths a check-mode run found not yet linked.

    Returns:
        ``0`` on success, ``1`` if anything was ambiguous or (in check mode) pending.
    """
    verb = "would link" if check else "linked"
    count = len(pending) if check else linked
    print(f"\n{BLUE}sync-self:{RESET} {count} {verb}, {unchanged} already correct, {len(ambiguous)} ambiguous")
    for rel in ambiguous:
        print(f"  {YELLOW}ambiguous{RESET} {rel} matches multiple bundles — link it by hand")
    if pending:
        print(f"{YELLOW}Dogfood symlinks are out of date — run 'make sync-self' and commit the result.{RESET}")
    return 1 if (ambiguous or pending) else 0


def relink(root: Path, *, check: bool = False) -> int:
    """Convert every eligible root dogfood copy into a relative symlink.

    A root file is eligible when it is tracked by git, not in ``_EXCLUDE``, and
    byte-identical to exactly one bundle source. Ambiguous matches (identical to
    more than one bundle) are skipped with a warning rather than guessed.

    In ``check`` mode nothing is written: the function only reports the copies that
    *would* be linked and returns non-zero if any are pending. This is the CI drift
    guard — it fails a build when someone adds a bundle file (or lets a copy reappear)
    without running ``make sync-self``.

    Args:
        root: The repository root containing ``bundles/`` and the dogfood files.
        check: When True, do not modify anything; only detect and report pending links.

    Returns:
        Process exit code: ``0`` on success, ``1`` if any file was ambiguous or (in
        ``check`` mode) if any eligible copy is not yet linked.
    """
    bundles_dir = root / "bundles"
    if not bundles_dir.is_dir():
        sys.exit(f"{YELLOW}No bundles/ directory found at {root} — run from the rhiza repo root.{RESET}")

    index = _bundle_index(bundles_dir)
    linked = 0
    unchanged = 0
    ambiguous: list[str] = []
    pending: list[str] = []

    for rel in _tracked_files(root):
        kind, source = _classify_dogfood(root, rel, index)
        if kind == "ambiguous":
            ambiguous.append(rel)
            continue
        if kind == "skip" or source is None:
            continue
        if check:
            if _link_is_current(root, rel, source):
                unchanged += 1
            else:
                print(f"  {YELLOW}would link{RESET} {rel} {DIM}->{RESET} {source.relative_to(root)}")
                pending.append(rel)
        elif _link_one(root, rel, source):
            print(f"  {GREEN}linked{RESET}    {rel} {DIM}->{RESET} {source.relative_to(root)}")
            linked += 1
        else:
            unchanged += 1

    return _report(check=check, linked=linked, unchanged=unchanged, ambiguous=ambiguous, pending=pending)


if __name__ == "__main__":
    sys.exit(relink(Path(__file__).resolve().parent.parent, check="--check" in sys.argv[1:]))
