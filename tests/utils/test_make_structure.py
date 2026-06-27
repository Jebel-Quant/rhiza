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

_PHONY_LINE = re.compile(r"^\.PHONY:\s*(?P<names>.+)$")


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
    for line in path.read_text(encoding="utf-8").splitlines():
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


def _defined_targets(path: Path) -> set[str]:
    """Parse every target name (single- and double-colon) defined in one Makefile file.

    Unlike ``_single_colon_targets`` this keeps double-colon targets, because a
    ``.PHONY`` name is satisfied by a rule of either colour.
    """
    targets: set[str] = set()
    in_define = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if in_define:
            in_define = stripped != "endef"
            continue
        if stripped.startswith("define "):
            in_define = True
            continue
        match = _TARGET_LINE.match(line)
        if not match:
            continue
        for name in match.group("names").split():
            if name.startswith(".") or "$(" in name:
                continue
            targets.add(name)
    return targets


def _phony_names(path: Path) -> set[str]:
    """Return every target name declared on a ``.PHONY:`` line in one Makefile file."""
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _PHONY_LINE.match(line.strip())
        if match:
            names.update(name for name in match.group("names").split() if "$(" not in name)
    return names


def test_no_phony_target_without_recipe(root):
    """Every ``.PHONY`` name in a fragment must correspond to a real target rule.

    A ``.PHONY`` entry with no matching rule (e.g. a renamed or removed target
    whose declaration was left behind) silently does nothing — ``make <name>``
    prints "Nothing to be done". Fail loudly so dead declarations cannot
    accumulate. Definitions are resolved across all fragments plus rhiza.mk and
    the root Makefile, since a phony target may be defined outside the fragment
    that declares it (e.g. a double-colon hook).
    """
    sources = [*_make_fragments(root), root / ".rhiza" / "rhiza.mk", root / "Makefile"]
    defined: set[str] = set()
    for source in sources:
        defined |= _defined_targets(source)

    dead: dict[str, str] = {}
    for fragment in _make_fragments(root):
        for name in _phony_names(fragment):
            if name not in defined:
                dead[name] = fragment.name

    assert not dead, (
        f".PHONY names declared with no corresponding target rule: {dead}. "
        "Remove the stale declaration or define the target."
    )


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
        for line in fragment.read_text(encoding="utf-8").splitlines():
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
