"""Print all Rhiza bundles and profiles with descriptions and dependencies.

Run as a script from a project root that contains ``.rhiza/template-bundles.yml``.
It reads that file, groups every bundle into the base, GitHub, and GitLab families,
and prints a colourised summary of each bundle (with its ``requires``/``recommends``
dependencies) followed by the profiles and the bundles they expand to.

Example:
    Invoke through the Makefile target (the supported entry point)::

        $ make explain-bundles

    or run the module directly from the repository root::

        $ python .rhiza/utils/explain_bundles.py
"""

import sys

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

with open(".rhiza/template-bundles.yml") as f:
    data = yaml.safe_load(f)

bundles = data.get("bundles", {})
profiles = data.get("profiles", {})


def _is_github(name: str) -> bool:
    """Return True when a bundle belongs to the GitHub family.

    Args:
        name: The bundle name (e.g. ``github-tests`` or ``github-book``).

    Returns:
        True if the bundle is GitHub-specific, False otherwise.
    """
    return name.startswith("github-") or name == "github"


def _is_gitlab(name: str) -> bool:
    """Return True when a bundle belongs to the GitLab family.

    Args:
        name: The bundle name (e.g. ``gitlab-tests`` or ``gitlab``).

    Returns:
        True if the bundle is GitLab-specific, False otherwise.
    """
    return name.startswith("gitlab-") or name == "gitlab"


def _bundle_group(name: str) -> str:
    """Map a bundle name to its display group.

    Args:
        name: The bundle name to classify.

    Returns:
        One of ``"github"``, ``"gitlab"``, or ``"base"`` — the section
        heading the bundle is printed under.
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


groups: dict[str, dict] = {"base": {}, "github": {}, "gitlab": {}}  # type: ignore[type-arg]
for name, info in bundles.items():
    groups[_bundle_group(name)][name] = info

base_bundles = groups["base"]
github_bundles = groups["github"]
gitlab_bundles = groups["gitlab"]

print(f"\n{BOLD}Bundles{RESET}  ({len(bundles)} total)\n" + "─" * 72)

print(f"\n  {BOLD}Core & Feature{RESET}  ({len(base_bundles)})\n")
for name, info in base_bundles.items():
    _print_bundle(name, info)

print(f"\n  {BOLD}GitHub{RESET}  ({len(github_bundles)})\n")
for name, info in github_bundles.items():
    _print_bundle(name, info)

print(f"\n  {BOLD}GitLab{RESET}  ({len(gitlab_bundles)})\n")
for name, info in gitlab_bundles.items():
    _print_bundle(name, info)

print(f"\n{BOLD}Profiles{RESET}  ({len(profiles)} total)\n" + "─" * 72)
for name, info in profiles.items():
    desc = info.get("description", "").strip().splitlines()[0]
    members = info.get("bundles", [])
    print(f"  {GREEN}{BOLD}{name:<24}{RESET}{desc}")
    print(f"  {'':24}{DIM}expands to: {', '.join(members)}{RESET}")

print()
