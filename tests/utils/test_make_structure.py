"""Cross-file conflict gates for the modular Makefile system.

The modular layout (`.rhiza/rhiza.mk` auto-including every `.rhiza/make.d/*.mk`
alphabetically) means two fragment files can silently fight over the same target:
make resolves duplicate single-colon recipes with a last-definition-wins warning
that nothing in CI turns into a failure. These tests parse the fragments directly
and fail loudly on cross-file collisions.

Double-colon targets (`pre-install::`, `test::`, ...) are the sanctioned extension
mechanism — they are legitimately defined in several files and exempt here.
"""

import re
from collections import defaultdict
from pathlib import Path

# A target definition line: one or more target names, then `:` or `::`, at the
# start of a line (recipe lines start with a tab). `(?!=)` keeps `VAR := x`
# assignments out. Names containing `$(` (computed targets) are skipped later.
_TARGET_LINE = re.compile(r"^(?P<names>[^\t#:=][^:=]*?)\s*(?P<colon>::?)(?!=)")

_SECTION_HEADER = re.compile(r"^##@\s*(?P<title>.+?)\s*$")


def _make_fragments(root) -> list[Path]:
    """Return all Makefile fragments auto-included from .rhiza/make.d/."""
    fragments = sorted((root / ".rhiza" / "make.d").glob("*.mk"))
    assert fragments, "no fragments found in .rhiza/make.d/ — layout changed?"
    return fragments


def _single_colon_targets(path: Path) -> set[str]:
    """Parse the single-colon target names defined in one Makefile fragment.

    Skips recipe lines, comments, special targets (leading dot, e.g. .PHONY),
    computed target names, and the multi-definable double-colon hook targets.
    """
    targets: set[str] = set()
    in_define = False
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if in_define:
            in_define = stripped != "endef"
            continue
        if stripped.startswith("define "):
            in_define = True
            continue
        match = _TARGET_LINE.match(line)
        if not match or match.group("colon") == "::":
            continue
        for name in match.group("names").split():
            if name.startswith(".") or "$(" in name:
                continue
            targets.add(name)
    return targets


def test_no_duplicate_single_colon_targets_across_fragments(root):
    """No two .rhiza/make.d/*.mk files may define the same single-colon target.

    Make would accept the duplicate with a warning and silently use the last
    definition (alphabetically latest file), so the conflict must fail here.
    """
    owners: dict[str, list[str]] = defaultdict(list)
    for fragment in _make_fragments(root):
        for target in _single_colon_targets(fragment):
            owners[target].append(fragment.name)

    conflicts = {target: files for target, files in owners.items() if len(files) > 1}
    assert not conflicts, (
        "Single-colon targets defined in more than one .rhiza/make.d fragment "
        f"(last definition silently wins): {conflicts}. Use a double-colon hook "
        "target if multiple definitions are intentional."
    )


def test_no_duplicate_section_headers_across_fragments(root):
    """No two .rhiza/make.d/*.mk files may declare the same `##@` section header.

    `make help` groups targets under these headers; a colliding header merges two
    unrelated fragments into one confusing section.
    """
    owners: dict[str, list[str]] = defaultdict(list)
    for fragment in _make_fragments(root):
        for line in fragment.read_text().splitlines():
            match = _SECTION_HEADER.match(line)
            if match:
                owners[match.group("title")].append(fragment.name)

    conflicts = {title: files for title, files in owners.items() if len(files) > 1}
    assert not conflicts, f"`##@` section headers declared in more than one .rhiza/make.d fragment: {conflicts}"


def test_parser_sees_known_targets(root):
    """Sanity-check the parser against targets known to exist, so a regex regression cannot pass vacuously."""
    all_targets: set[str] = set()
    for fragment in _make_fragments(root):
        all_targets |= _single_colon_targets(fragment)

    expected = {"install", "clean", "doctor", "explain-bundles"}
    missing = expected - all_targets
    assert not missing, f"parser failed to find known single-colon targets: {missing}"
