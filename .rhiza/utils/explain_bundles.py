"""Print all Rhiza bundles and profiles with descriptions and dependencies."""

import sys

try:
    import yaml
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

print(f"\n{BOLD}Bundles{RESET}  ({len(bundles)} total)\n" + "─" * 72)
for name, info in bundles.items():
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

print(f"\n{BOLD}Profiles{RESET}  ({len(profiles)} total)\n" + "─" * 72)
for name, info in profiles.items():
    desc = info.get("description", "").strip().splitlines()[0]
    members = info.get("bundles", [])
    print(f"  {GREEN}{BOLD}{name:<24}{RESET}{desc}")
    print(f"  {'':24}{DIM}expands to: {', '.join(members)}{RESET}")

print()
