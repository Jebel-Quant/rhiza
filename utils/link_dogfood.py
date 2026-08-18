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

import argparse
import os
import shutil
import subprocess  # nosec B404  # git is invoked with a fixed, non-user argument list
import sys
import tempfile
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
        ".gitignore",  # mother-repo additions
        ".pre-commit-config.yaml",  # mother-repo additions
        ".python-version",  # mother-repo pinned version
        "SECURITY.md",  # mother-repo variant
        "renovate.json",  # mother-repo variant
        "Makefile",  # the rhiza-task shim, repo-owned (see _MAKE_LAYER_PREFIXES)
    }
)

# The synced make layer: shipped by the bundles, not run by the mother repo. rhiza migrated
# to the ``rhiza-task`` shim, so the root has a repo-owned ``Makefile`` and no ``rhiza.mk``
# or ``make.d/`` at all.
#
# Without this, ``sync-self`` would helpfully *recreate* every fragment as a root symlink on
# the next run — the linker's job is to link bundle-owned files into the root, and these are
# still bundle-owned. It would silently reinstate the layer this repo just left, and the
# root ``Makefile`` would be clobbered back into a symlink into ``bundles/core/``, taking
# rhiza's own ``e2e``/``sync-self`` targets with it.
#
# Prefix-matched rather than named: ``make.d`` holds one fragment per owning bundle, so a
# new one must be excluded by arriving, not by being added to a list here.
_MAKE_LAYER_PREFIXES = (".rhiza/rhiza.mk", ".rhiza/make.d/")

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
    * it belongs to the synced make layer (:data:`_MAKE_LAYER_PREFIXES`), which the bundles
      ship but the mother repo no longer runs;
    * it lives under ``.github/`` (GitHub reads platform config blobs directly and does
      not resolve symlinks); or
    * git opens it with ``O_NOFOLLOW`` (see :data:`_NO_FOLLOW_NAMES`), so a symlink yields
      an ELOOP warning and the file's rules are silently ignored.

    Both :func:`relink` and the dogfood-integrity test consult this single predicate so
    the linker and its guard can never disagree about what is allowed to be a real copy.

    Args:
        rel: A repository-root-relative path (POSIX form, as ``git ls-files`` reports it).

    Returns:
        True if ``rel`` must remain a real file; False if it is eligible for symlinking.

    Examples:
        An ordinary bundle-owned file is linked, not carved out:

        >>> is_dogfood_carveout("ruff.toml")
        False

        The synced make layer is carved out, because the bundles still ship it while the
        mother repo runs the ``rhiza-task`` shim instead. Without this the linker would
        recreate the whole layer at the root on the next ``sync-self``:

        >>> is_dogfood_carveout(".rhiza/rhiza.mk")
        True
        >>> is_dogfood_carveout(".rhiza/make.d/python.mk")
        True
        >>> is_dogfood_carveout("Makefile")
        True

        A declared mother-repo override stays a real file, because its content
        deliberately diverges from the bundle it would otherwise point at:

        >>> is_dogfood_carveout(".python-version")
        True
        >>> is_dogfood_carveout("SECURITY.md")
        True

        Anything under ``.github/`` stays real at any depth — GitHub reads these blobs
        directly and does not resolve symlinks:

        >>> is_dogfood_carveout(".github/dependabot.yml")
        True
        >>> is_dogfood_carveout(".github/rulesets/main-branch-protection.json")
        True

        The ``O_NOFOLLOW`` names are matched by *basename*, so a nested one is caught
        just as the root copy is. This is the case that is easy to get wrong: a
        symlinked ``.gitignore`` does not error loudly, it makes git ignore the file's
        rules while warning on every command.

        >>> is_dogfood_carveout(".gitignore")
        True
        >>> is_dogfood_carveout(".rhiza/.gitignore")
        True
        >>> is_dogfood_carveout("bundles/core/.gitattributes")
        True

        Note that ``.github`` matches as a prefix rather than a path component, so a
        directory merely *starting* with those characters is not carved out:

        >>> is_dogfood_carveout(".github-notes/README.md")
        False
    """
    return (
        rel in _EXCLUDE
        or rel.startswith(".github/")
        or rel.startswith(_MAKE_LAYER_PREFIXES)
        or Path(rel).name in _NO_FOLLOW_NAMES
    )


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
    result = subprocess.run(  # noqa: S603  # nosec B603  # resolved git path, fixed args, no shell
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
    fd, tmp_name = tempfile.mkstemp(prefix=f".{link.name}.", dir=link.parent)
    os.close(fd)
    tmp_link = Path(tmp_name)
    tmp_link.unlink()
    try:
        tmp_link.symlink_to(target)
        tmp_link.replace(link)
    finally:
        if tmp_link.exists() or tmp_link.is_symlink():
            tmp_link.unlink()
    return True


def _owner_by_content(root_path: Path, owners: list[Path]) -> tuple[str, Path | None]:
    """Pick the single bundle source whose bytes match ``root_path``.

    Split out of :func:`_classify_dogfood` so that function stays a short ladder of
    *eligibility* questions and this one holds the *content* comparison. Both halves
    return the same ``(kind, source)`` verdict, so the split is invisible to callers.

    Size is compared before content deliberately: a dogfood copy that diverges from
    its bundle source usually differs in length, so the cheap check settles most
    non-matches without reading either file. ``tests/utils/test_link_dogfood.py``
    pins that ordering.

    Args:
        root_path: The concrete root file being classified.
        owners: The bundle files that claim ``root_path``'s bundle-relative path.

    Returns:
        A ``(kind, source)`` verdict — see :func:`_classify_dogfood` for the vocabulary.
    """
    root_size = root_path.stat().st_size
    same_size_owners = [o for o in owners if o.stat().st_size == root_size]
    if not same_size_owners:
        return ("skip", None)  # diverges from every owner — an (undeclared) override; leave it real
    root_bytes = root_path.read_bytes()
    identical = [o for o in same_size_owners if o.read_bytes() == root_bytes]
    if not identical:
        return ("skip", None)  # diverges from every owner — an (undeclared) override; leave it real
    if len(identical) > 1:
        return ("ambiguous", None)
    return ("link", identical[0])


def _classify_dogfood(root: Path, rel: str, index: dict[str, list[Path]]) -> tuple[str, Path | None]:
    """Classify a tracked root path for dogfood linking.

    This is the eligibility decision for a single file, factored out of
    :func:`relink` so the loop there stays a straight-line consumer of the verdict.
    The byte-level comparison lives in :func:`_owner_by_content`; what remains here
    is the ladder of reasons a path never reaches it.

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
    # git O_NOFOLLOW files, and the .github/ tree) — all must stay real files.
    # See is_dogfood_carveout for the reasoning behind each case.
    if rel.startswith("bundles/") or is_dogfood_carveout(rel):
        return ("skip", None)
    owners = index.get(rel)
    if not owners:
        return ("skip", None)
    root_path = root / rel
    # A dangling link is what moving a bundle file between bundles leaves behind: the
    # root symlink still points at the old bundle path. There are no bytes to compare,
    # so the sole owner is the answer — and with several, the linker must not guess.
    if root_path.is_symlink() and not root_path.exists():
        return ("link", owners[0]) if len(owners) == 1 else ("ambiguous", None)
    return _owner_by_content(root_path, owners)


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


def _resolve_inputs(root: Path, index: dict[str, list[Path]] | None) -> tuple[dict[str, list[Path]], list[str]]:
    """Settle what to scan: the bundle index and the candidate root paths.

    Split out of :func:`relink` so that function is a loop over an already-decided
    input rather than a loop wrapped in setup. The caller-supplied-index branch is
    the one unit tests take, which is exactly why it is worth isolating: it must stay
    equivalent to the scan without duplicating it.

    Args:
        root: The repository root containing ``bundles/`` and the dogfood files.
        index: A pre-built bundle index, or None to scan ``bundles/`` and ``git ls-files``.

    Returns:
        The bundle index and the list of root-relative paths to classify.
    """
    if index is not None:
        return index, list(index.keys())
    bundles_dir = root / "bundles"
    if not bundles_dir.is_dir():
        sys.exit(f"{YELLOW}No bundles/ directory found at {root} — run from the rhiza repo root.{RESET}")
    return _bundle_index(bundles_dir), _tracked_files(root)


def _apply(root: Path, rel: str, source: Path, *, check: bool) -> str:
    """Link ``rel`` to ``source`` — or, in check mode, report that it would be.

    This holds the whole check-versus-write distinction, so :func:`relink` never
    branches on ``check`` itself and simply files each path under the verdict it gets
    back.

    Args:
        root: The repository root.
        rel: The dogfood file path relative to ``root``.
        source: The owning bundle file the symlink should target.
        check: When True, print and classify without writing anything.

    Returns:
        One of ``"pending"`` (check mode, not yet linked), ``"linked"`` (a symlink was
        created) or ``"unchanged"`` (already correct).
    """
    if check:
        if _link_is_current(root, rel, source):
            return "unchanged"
        print(f"  {YELLOW}would link{RESET} {rel} {DIM}->{RESET} {source.relative_to(root)}")
        return "pending"
    if _link_one(root, rel, source):
        print(f"  {GREEN}linked{RESET}    {rel} {DIM}->{RESET} {source.relative_to(root)}")
        return "linked"
    return "unchanged"


def relink(
    root: Path,
    index: dict[str, list[Path]] | None = None,
    *,
    check: bool = False,
) -> int:
    """Convert every eligible root dogfood copy into a relative symlink.

    A root file is eligible when it is tracked by git, not in ``_EXCLUDE``, and
    byte-identical to exactly one bundle source. Ambiguous matches (identical to
    more than one bundle) are skipped with a warning rather than guessed.

    In ``check`` mode nothing is written: the function only reports the copies that
    *would* be linked and returns non-zero if any are pending — the local drift check,
    reached as ``make sync-self-check``, for use before committing a new bundle file.

    In CI the same invariant is asserted by ``tests/bundles/test_bundle_dogfood_symlinks.py``
    inside ``make test``, which reuses this module's own carve-out predicate and bundle
    index so the two can never disagree. No workflow calls ``sync-self-check`` itself
    (#1532).

    Args:
        root: The repository root containing ``bundles/`` and the dogfood files.
        index: Optional pre-built bundle index mapping relative paths to their bundle
            source files.  When *None* (the default) the index is computed from the
            ``bundles/`` subdirectory of ``root`` and the candidate files are read from
            ``git ls-files``.  Pass an explicit mapping to skip the filesystem scan —
            primarily useful in unit tests that need to exercise the function in
            isolation without a real ``bundles/`` tree or git repository.
        check: When True, do not modify anything; only detect and report pending links.

    Returns:
        Process exit code: ``0`` on success, ``1`` if any file was ambiguous or (in
        ``check`` mode) if any eligible copy is not yet linked.
    """
    index, files = _resolve_inputs(root, index)
    verdicts: dict[str, list[str]] = {"linked": [], "unchanged": [], "pending": [], "ambiguous": []}

    for rel in files:
        kind, source = _classify_dogfood(root, rel, index)
        if kind == "ambiguous":
            verdicts["ambiguous"].append(rel)
        elif kind == "link" and source is not None:
            verdicts[_apply(root, rel, source, check=check)].append(rel)

    return _report(
        check=check,
        linked=len(verdicts["linked"]),
        unchanged=len(verdicts["unchanged"]),
        ambiguous=verdicts["ambiguous"],
        pending=verdicts["pending"],
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line.

    Uses argparse rather than scanning ``sys.argv`` (#1531). The distinction is not
    cosmetic on this tool: the default mode *rewrites tracked files as symlinks*, so a
    mistyped ``--check`` must be an error rather than silently falling through to the
    writing run.

    Args:
        argv: Arguments to parse, or None to read ``sys.argv[1:]``.

    Returns:
        The parsed namespace, carrying the boolean ``check``.
    """
    parser = argparse.ArgumentParser(
        prog="link_dogfood.py",
        description=(
            "Relink the mother repo's dogfood copies as relative symlinks into bundles/. "
            "Mother-repo tooling; run it via `make sync-self`."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "report what would be linked and exit non-zero if anything is pending, "
            "without writing (`make sync-self-check`)"
        ),
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(relink(Path(__file__).resolve().parent.parent, check=_parse_args().check))
