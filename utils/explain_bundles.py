# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Print all Rhiza bundles and profiles with descriptions and dependencies.

It reads ``.rhiza/template-bundles.yml``, groups every bundle into the base, GitHub,
and GitLab families, and prints a colourised summary of each bundle (with its
``requires``/``recommends`` dependencies) followed by the profiles and the bundles
they expand to.

Importing this module has **no side effects**: the YAML is read and the summary
printed only when :func:`main` runs. That is deliberate (#1530) — the config used to
be opened at import time through a *relative* path, so the module was importable only
from the repository root, and every consumer (a doctest, a test, another script) had
to chdir first.

Example:
    Invoke through the Makefile target (the supported entry point)::

        $ make explain-bundles

    or run the module directly, from any directory::

        $ python utils/explain_bundles.py
"""

import sys
from pathlib import Path

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    sys.exit("pyyaml is not installed — run: make install")

BLUE = "\033[36m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"

# The config's path relative to whichever project root holds it.
_CONFIG_REL = Path(".rhiza") / "template-bundles.yml"


def _is_github(name: str) -> bool:
    """Return True when a bundle belongs to the GitHub family.

    Args:
        name: The bundle name (e.g. ``github-tests`` or ``github-book``).

    Returns:
        True if the bundle is GitHub-specific, False otherwise.

    Examples:
        The feature bundle itself and every platform overlay built on it:

        >>> _is_github("github")
        True
        >>> _is_github("github-tests")
        True

        Feature bundles and the other platform's overlays are not:

        >>> _is_github("core")
        False
        >>> _is_github("gitlab-tests")
        False

        The hyphen in the prefix is load-bearing — it keeps a hypothetical unrelated
        bundle whose name merely begins with these letters out of the family:

        >>> _is_github("githubbub")
        False
    """
    return name.startswith("github-") or name == "github"


def _is_gitlab(name: str) -> bool:
    """Return True when a bundle belongs to the GitLab family.

    Args:
        name: The bundle name (e.g. ``gitlab-tests`` or ``gitlab``).

    Returns:
        True if the bundle is GitLab-specific, False otherwise.

    Examples:
        >>> _is_gitlab("gitlab")
        True
        >>> _is_gitlab("gitlab-book")
        True
        >>> _is_gitlab("github-book")
        False
        >>> _is_gitlab("book")
        False
    """
    return name.startswith("gitlab-") or name == "gitlab"


def _bundle_group(name: str) -> str:
    """Map a bundle name to its display group.

    Args:
        name: The bundle name to classify.

    Returns:
        One of ``"github"``, ``"gitlab"``, or ``"base"`` — the section
        heading the bundle is printed under.

    Examples:
        >>> _bundle_group("github-marimo")
        'github'
        >>> _bundle_group("gitlab-quality-review")
        'gitlab'

        Everything that is not platform-specific groups under ``base`` — the feature
        bundles and the language layers alike:

        >>> _bundle_group("marimo")
        'base'
        >>> _bundle_group("python-core")
        'base'
    """
    if _is_github(name):
        return "github"
    if _is_gitlab(name):
        return "gitlab"
    return "base"


def _print_bundle(name: str, info: dict) -> None:  # type: ignore[type-arg]
    """Print one bundle entry with dependency metadata.

    Args:
        name: The bundle name, used as the row label.
        info: The bundle's mapping from ``template-bundles.yml``. Recognised
            keys are ``description``, ``requires``, ``recommends``, and
            ``standalone``; all are optional and default sensibly.

    Returns:
        None. The formatted entry is written to standard output.
    """
    desc = info.get("description", "").strip().splitlines()[0]
    requires = info.get("requires") or []
    recommends = info.get("recommends") or []
    standalone = info.get("standalone", True)
    tag = "" if standalone else f"  {DIM}[not standalone]{RESET}"
    print(f"  {BLUE}{BOLD}{name:<24}{RESET}{desc}{tag}")
    if requires:
        print(f"  {'':24}{DIM}requires:   {YELLOW}{', '.join(requires)}{RESET}")
    if recommends:
        print(f"  {'':24}{DIM}recommends: {', '.join(recommends)}{RESET}")


def _config_path() -> Path:
    """Locate ``.rhiza/template-bundles.yml``.

    The current directory wins when it holds a config, so the script still explains
    *this* project when run from a project root. Otherwise the path is resolved
    relative to this file, which is what makes the module usable from anywhere —
    including from a test or a doctest that never changes directory.

    Returns:
        The config path to read. It is not guaranteed to exist; :func:`main` reports
        a missing file rather than letting ``open`` raise.
    """
    local = Path.cwd() / _CONFIG_REL
    if local.is_file():
        return local
    return Path(__file__).resolve().parent.parent / _CONFIG_REL


def group_bundles(bundles: dict) -> dict[str, dict]:  # type: ignore[type-arg]
    """Split every bundle into its display group.

    Args:
        bundles: The ``bundles`` mapping from ``template-bundles.yml``.

    Returns:
        A mapping with exactly the keys ``base``, ``github`` and ``gitlab``, each
        holding the bundles that belong to that family. Empty families are kept so
        callers can render a heading with a count of zero.

    Examples:
        >>> groups = group_bundles({"core": {}, "github-tests": {}})
        >>> sorted(groups)
        ['base', 'github', 'gitlab']
        >>> list(groups["base"])
        ['core']
        >>> list(groups["github"])
        ['github-tests']
        >>> groups["gitlab"]
        {}
    """
    groups: dict[str, dict] = {"base": {}, "github": {}, "gitlab": {}}  # type: ignore[type-arg]
    for name, info in bundles.items():
        groups[_bundle_group(name)][name] = info
    return groups


def main() -> int:
    """Read the bundle config and print the bundle and profile summary.

    Returns:
        ``0`` on success. A missing config exits non-zero with guidance instead of
        returning, so the caller never prints an empty summary and claims success.
    """
    config = _config_path()
    if not config.is_file():
        sys.exit(f"{YELLOW}No {_CONFIG_REL} found — run from a project root that has one.{RESET}")

    with open(config) as f:
        data = yaml.safe_load(f)

    bundles = data.get("bundles", {})
    profiles = data.get("profiles", {})
    groups = group_bundles(bundles)

    print(f"\n{BOLD}Bundles{RESET}  ({len(bundles)} total)\n" + "─" * 72)
    for heading, key in (("Core & Feature", "base"), ("GitHub", "github"), ("GitLab", "gitlab")):
        print(f"\n  {BOLD}{heading}{RESET}  ({len(groups[key])})\n")
        for name, info in groups[key].items():
            _print_bundle(name, info)

    print(f"\n{BOLD}Profiles{RESET}  ({len(profiles)} total)\n" + "─" * 72)
    for name, info in profiles.items():
        desc = info.get("description", "").strip().splitlines()[0]
        members = info.get("bundles", [])
        print(f"  {GREEN}{BOLD}{name:<24}{RESET}{desc}")
        print(f"  {'':24}{DIM}expands to: {', '.join(members)}{RESET}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
