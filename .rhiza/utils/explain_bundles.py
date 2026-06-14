"""Print all Rhiza bundles and profiles with descriptions and dependencies."""

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
    """Return True when a bundle belongs to the GitHub family."""
    return name.startswith("github-") or name in {"github", "gh-aw"}


def _is_gitlab(name: str) -> bool:
    """Return True when a bundle belongs to the GitLab family."""
    return name.startswith("gitlab-") or name == "gitlab"


def _bundle_group(name: str) -> str:
    """Map a bundle name to its display group."""
    if _is_github(name):
        return "github"
    if _is_gitlab(name):
        return "gitlab"
    return "base"


def _print_bundle(name: str, info: dict) -> None:  # type: ignore[type-arg]
    """Print one bundle entry with dependency metadata."""
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
