"""Renovate's custom managers must still match the pins they were written for.

A custom manager whose file pattern matches nothing is **not an error to Renovate**. It
reports no failure and opens no PR; the pin it was watching simply stops being updated. That
is how the pytest-rhiza manager died: it targeted ``RHIZA_CHECKS_VERSION`` in
``.rhiza/make.d/quality.mk``, the make layer retired (#1556 here, #1557 for the bundle), and
the pin aged through two releases before anyone looked (#1579).

``RHIZA_TASK`` then repeated the lesson with no manager at all. It sat at 0.3.1 while
upstream shipped 1.0.0 and 1.1.0, and #1580 moved all eleven literals by hand. #1582 added
the manager; this module is the half that keeps it honest, because adding a manager without a
test only moves the silent-failure mode one level up.

**Three claims are asserted, and the third is the counter-intuitive one:**

1. Every ``rhiza-task@X.Y.Z`` literal in the tree lies in a file the manager matches.
2. Every such line matches the manager's ``matchStrings``, capturing ``currentValue``.
3. The **root** ``Makefile`` is deliberately *not* matched. It is a dogfood symlink into
   ``bundles/core/``, and a writer following that path would replace the link with a regular
   file -- silently undoing #1576 and leaving two copies of the shim to drift. The bundle
   file is the one that carries the pin; the root one only reflects it.

A fourth invariant comes along for free and is worth as much as the others: all eleven
literals must name the **same** version. Renovate groups by dep+version and so keeps them in
step, but a hand bump does not, and a repo whose shim and workflows name different CLIs runs
its gates on two versions without saying so.
"""

from __future__ import annotations

import functools
import json
import re
import subprocess  # nosec B404 - fixed argument vectors
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_RENOVATE = _ROOT / "renovate.json"

# The pin as it appears in every shape: `RHIZA_TASK ?= rhiza-task@1.1.0`, the quoted
# `RHIZA_TASK: "rhiza-task@1.1.0"`, and the inline `uvx rhiza-task@1.1.0 print ...`.
_PIN = re.compile(r"rhiza-task@(\d+\.\d+\.\d+)")

# Where a literal may live without the manager being expected to update it.
#
# CHANGELOG.md records what *was* pinned, so rewriting it would falsify history. The root
# Makefile is the dogfood symlink -- see the module docstring's third claim. Nothing else is
# exempt: a new home for the pin should fail this suite until the manager learns about it.
_NOT_THE_MANAGER_S_JOB = {"CHANGELOG.md", "Makefile"}

# Documentation and tests reference the pin as prose or as a pattern, not as a pin to bump.
_PROSE_PREFIXES = ("docs/", "tests/", "README.md", "CLAUDE.md")


@functools.lru_cache(maxsize=1)
def _tracked_files() -> tuple[str, ...]:
    """Return every tracked path that is a regular file, symlinks excluded.

    Returns:
        Repo-relative paths, with mode-120000 entries dropped.
    """
    proc = subprocess.run(  # nosec B603
        ["git", "ls-files", "-s"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    out = []
    for line in proc.stdout.splitlines():
        meta, _, path = line.partition("\t")
        if meta.split()[0] != "120000":
            out.append(path)
    return tuple(out)


@functools.lru_cache(maxsize=1)
def _manager() -> dict:
    """Return the custom manager that watches the rhiza-task pin.

    Returns:
        The manager mapping from ``renovate.json``.
    """
    config = json.loads(_RENOVATE.read_text(encoding="utf-8"))
    managers = [m for m in config.get("customManagers", []) if m.get("depNameTemplate") == "rhiza-task"]
    assert len(managers) == 1, (
        f"expected exactly one custom manager for rhiza-task in renovate.json, found {len(managers)}. "
        f"Two managers for one dependency race each other; none means the pin only ages (#1579, #1582)."
    )
    return managers[0]


def _as_regex(pattern: str) -> re.Pattern[str]:
    """Convert one Renovate ``managerFilePatterns`` entry to a Python regex.

    Renovate accepts either a glob or a ``/regex/`` literal; this repo's managers use the
    regex form throughout, so only the delimiters have to come off.

    Args:
        pattern: The entry as written in ``renovate.json``.

    Returns:
        The compiled pattern.
    """
    delimited = (
        f"managerFilePatterns entry {pattern!r} is not in the /regex/ form the other "
        f"managers here use; a glob would need different handling in this test"
    )
    assert pattern.startswith("/"), delimited
    assert pattern.endswith("/"), delimited
    return re.compile(pattern[1:-1])


def _match_string(pattern: str) -> re.Pattern[str]:
    """Compile one Renovate ``matchStrings`` entry as a Python regex.

    Renovate's regexes are **JavaScript**, where a named group is ``(?<name>...)``; Python
    spells it ``(?P<name>...)`` and raises ``re.error: unknown extension ?<c`` on the other
    form. So the config is correct as written and this test has to translate, not the other
    way round -- "fixing" renovate.json to satisfy Python would break the manager.

    Args:
        pattern: The entry as written in ``renovate.json``.

    Returns:
        The compiled pattern, with named groups in Python syntax.
    """
    return re.compile(re.sub(r"\(\?<(?![=!])", "(?P<", pattern))


def _pinned_files() -> list[str]:
    """Return the tracked files carrying a rhiza-task pin the manager should own.

    Returns:
        Repo-relative paths, prose and history excluded.
    """
    out = []
    for path in _tracked_files():
        if path in _NOT_THE_MANAGER_S_JOB or path.startswith(_PROSE_PREFIXES):
            continue
        if _PIN.search((_ROOT / path).read_text(encoding="utf-8", errors="replace")):
            out.append(path)
    return sorted(out)


def test_the_scan_finds_the_pins_at_all() -> None:
    """Positive control: an empty file list would make every assertion below vacuous.

    Named first because it is the one that fails if the pin is renamed, moved wholesale, or
    if ``_PROSE_PREFIXES`` grows until it swallows the real thing.
    """
    found = _pinned_files()
    assert len(found) >= 9, (
        f"found only {len(found)} file(s) carrying a rhiza-task pin: {found}. The shim and the "
        f"live workflows alone are more than that, so the scan is looking in the wrong place "
        f"and the coverage assertions below prove nothing."
    )
    assert "bundles/core/Makefile" in found, "the shim is where the pin lives; the scan must see it"


@pytest.mark.parametrize("path", _pinned_files())
def test_every_pinned_file_is_matched_by_the_manager(path: str) -> None:
    """A file carrying the pin that no ``managerFilePatterns`` entry matches is unwatched.

    This is the assertion that would have caught #1579 before the pin aged: the manager
    still parses, still validates, and matches nothing.
    """
    patterns = [_as_regex(p) for p in _manager()["managerFilePatterns"]]
    assert any(p.search(path) for p in patterns), (
        f"{path} carries a rhiza-task pin that no managerFilePatterns entry matches, so "
        f"Renovate will never bump it. A partial bump leaves the shim and the workflows "
        f"naming different CLIs (#1582)."
    )


@pytest.mark.parametrize("path", _pinned_files())
def test_the_match_string_captures_every_occurrence(path: str) -> None:
    """Matching the file is not enough: the regex must also capture each pin's version.

    A ``matchStrings`` that finds the file but not the literal is the same silent no-op one
    level down -- Renovate reports the manager as having found no dependency, which is not an
    error either.
    """
    match_strings = [_match_string(s) for s in _manager()["matchStrings"]]
    text = (_ROOT / path).read_text(encoding="utf-8")
    occurrences = _PIN.findall(text)
    for regex in match_strings:
        captured = [m.group("currentValue") for m in regex.finditer(text)]
        if len(captured) == len(occurrences):
            assert captured == occurrences, f"{path}: captured {captured}, expected {occurrences}"
            return
    pytest.fail(
        f"{path} carries {len(occurrences)} rhiza-task pin(s) but no matchStrings entry "
        f"captures all of them. rhiza_ci.yml carries two — an env var and an inline `uvx` "
        f"call — so a regex anchored on `RHIZA_TASK:` alone silently misses one."
    )


def test_the_root_makefile_is_not_matched() -> None:
    """The dogfood symlink must stay out of the manager's reach.

    Renovate writing through ``Makefile`` would replace the symlink with a regular file,
    quietly undoing #1576 and leaving two copies of the shim free to drift. The bundle file
    is the pin's home; the root path only reflects it.
    """
    patterns = [_as_regex(p) for p in _manager()["managerFilePatterns"]]
    assert not any(p.search("Makefile") for p in patterns), (
        "a managerFilePatterns entry matches the root `Makefile`, which is a dogfood symlink "
        "into bundles/core/. Renovate would turn it into a real file on the first bump. "
        "Match `bundles/core/Makefile` instead."
    )


def test_every_pin_names_the_same_version() -> None:
    """A split pin runs the gates on two CLIs without saying so.

    Renovate keeps the literals in step by grouping on dep+version; a hand bump does not,
    which is the failure this asserts against. #1580 moved eleven literals at once and this
    is what proves it moved all of them.
    """
    versions: dict[str, set[str]] = {}
    for path in _pinned_files():
        for version in _PIN.findall((_ROOT / path).read_text(encoding="utf-8")):
            versions.setdefault(version, set()).add(path)
    assert len(versions) == 1, (
        f"the rhiza-task pin disagrees with itself across files: "
        f"{ {v: sorted(p) for v, p in versions.items()} }. Every literal must name one "
        f"version, or the shim and CI run different gates."
    )


# --------------------------------------------------------------------------------------
# Action pins: the same question as above, asked of `uses:` rather than of `rhiza-task@`.
# --------------------------------------------------------------------------------------

# `uses: owner/repo[/path]@ref`, which is every action reference that resolves to another
# repository. `./`-relative refs are local and have no version to bump.
_USES_RE = re.compile(r"^\s*(?:-\s+)?uses:\s*([A-Za-z0-9][\w.-]*/[\w./-]+)@\S+", re.MULTILINE)

# rhiza's own reusable workflows. Deliberately unwatched: the release rewrites the tag.
_FIRST_PARTY = "jebel-quant/rhiza/"

# What Renovate's `github-actions` manager matches without configuration. Anchored at the
# repository root -- which is the whole of #1610: `bundles/github/.github/workflows/` is not
# under `^.github/`, so the shipped pins were matched by nothing and only aged.
_RENOVATE_DEFAULT_PATTERNS = (
    re.compile(r"^(?:workflow-templates|\.(?:github|gitea|forgejo)/(?:workflows|actions))/.+\.ya?ml$"),
    re.compile(r"(^|/)action\.ya?ml$"),
)

# Dependabot's `github-actions` ecosystem reads `<directory>/.github/workflows` and nothing
# else -- it has no globbing over the tree, which is why it cannot cover the bundles either.
_DEPENDABOT = _ROOT / ".github" / "dependabot.yml"


def _third_party_action_files() -> list[str]:
    """Return every tracked workflow that references a third-party action.

    Returns:
        Repo-relative paths, sorted; first-party reusable-workflow callers excluded.
    """
    out = []
    for path in _tracked_files():
        if not (path.startswith(".github/workflows/") or ".github/workflows/" in path):
            continue
        text = (_ROOT / path).read_text(encoding="utf-8", errors="replace")
        if any(not ref.startswith(_FIRST_PARTY) for ref in _USES_RE.findall(text)):
            out.append(path)
    return sorted(out)


@functools.lru_cache(maxsize=1)
def _renovate_action_scope() -> tuple[list[re.Pattern[str]], list[str]]:
    """Return Renovate's github-actions file patterns and the paths it is switched off for.

    Returns:
        ``(patterns, disabled_prefixes)`` -- the configured patterns plus the manager's own
        defaults, and the ``matchFileNames`` globs of every rule disabling the manager.
    """
    config = json.loads(_RENOVATE.read_text(encoding="utf-8"))
    assert "github-actions" in config["enabledManagers"], (
        "the github-actions manager is not enabled, so nothing Renovate does covers the shipped workflows (#1610)"
    )
    configured = [_as_regex(p) for p in config.get("github-actions", {}).get("managerFilePatterns", [])]
    disabled = [
        glob.removesuffix("/**")
        for rule in config.get("packageRules", [])
        if rule.get("enabled") is False and "github-actions" in (rule.get("matchManagers") or [])
        for glob in (rule.get("matchFileNames") or [])
    ]
    return [*configured, *_RENOVATE_DEFAULT_PATTERNS], disabled


@functools.lru_cache(maxsize=1)
def _dependabot_action_dirs() -> tuple[str, ...]:
    """Return the workflow directories Dependabot's github-actions ecosystem covers."""
    config = yaml.safe_load(_DEPENDABOT.read_text(encoding="utf-8"))
    return tuple(
        f"{entry['directory'].strip('/')}/.github/workflows".lstrip("/")
        for entry in config.get("updates", [])
        if entry.get("package-ecosystem") == "github-actions"
    )


def _watchers(path: str) -> list[str]:
    """Return the names of every bot configured to bump the action pins in ``path``."""
    patterns, disabled = _renovate_action_scope()
    watchers = []
    if any(p.search(path) for p in patterns) and not any(path.startswith(d) for d in disabled):
        watchers.append("Renovate")
    if any(path.startswith(d) for d in _dependabot_action_dirs()):
        watchers.append("Dependabot")
    return watchers


def test_the_action_scan_finds_the_workflows() -> None:
    """Positive control: an empty file list makes every assertion below vacuous."""
    found = _third_party_action_files()
    assert len(found) >= 10, f"found only {len(found)} workflow(s) with a third-party action: {found}"
    assert "bundles/github/.github/workflows/rhiza_release.yml" in found, (
        "the shipped release workflow is the one bundle file with third-party actions; a scan "
        "that misses it proves nothing about #1610"
    )


@pytest.mark.parametrize("path", _third_party_action_files())
def test_every_third_party_action_pin_is_watched(path: str) -> None:
    """Exactly one bot must be configured to bump each file's action pins.

    Zero is #1610: `bundles/github/.github/workflows/rhiza_release.yml` carried 26 pins that
    Renovate's root-anchored defaults did not match and Dependabot's directory-scoped
    ecosystem could not reach, so `actions/checkout` sat at v6.0.2 while the live copies had
    moved three releases on. A manager matching nothing is not an error to Renovate -- it
    opens no PR and reports no failure.

    Two is the opposite failure and just as real: both bots would open a PR for the same bump,
    and the loser of the race rebases forever.
    """
    watchers = _watchers(path)
    assert watchers, (
        f"no dependency bot is configured to bump the action pins in {path}. Renovate's "
        f"github-actions defaults are anchored at the repository root and Dependabot reads "
        f"`<directory>/.github/workflows` only, so a file outside both is watched by nothing "
        f"and its pins simply age (#1610)."
    )
    assert len(watchers) == 1, (
        f"{path} is watched by {watchers} — two bots bumping one file means two PRs per bump. "
        f"Give the file to one of them."
    )


def test_the_bundle_and_live_pins_agree() -> None:
    """The same action must be pinned to the same commit everywhere it appears.

    The action-pin twin of `test_every_pin_names_the_same_version`, and the state this
    repository was actually in: the live workflows and the shipped one named different
    commits for six of the eleven actions they share, which is drift with a security edge —
    a consumer's release pipeline ran older code than the mother repo's did.
    """
    pins: dict[str, dict[str, set[str]]] = {}
    for path in _third_party_action_files():
        text = (_ROOT / path).read_text(encoding="utf-8")
        for match in re.finditer(r"uses:\s*([A-Za-z0-9][\w.-]*/[\w./-]+)@(\S+)", text):
            action, ref = match.group(1), match.group(2)
            if action.startswith(_FIRST_PARTY):
                continue
            pins.setdefault(action, {}).setdefault(ref, set()).add(path)
    split = {
        action: {ref: sorted(paths) for ref, paths in refs.items()} for action, refs in pins.items() if len(refs) > 1
    }
    assert not split, f"actions pinned to more than one ref across the tree: {split}"


def test_a_synced_repository_gets_a_bot_for_its_action_pins() -> None:
    """The consumer half of #1610: a SHA pin nobody bumps is a pin that rots.

    SHA-pinning the shipped workflows (#1611) makes this load-bearing rather than tidy. A tag
    pin at least follows patch releases of the action; a SHA follows nothing at all, so a
    synced repository with no bot configured freezes on the commit it was synced with — and
    reads as hardened while it does.

    Both halves are asserted because a consumer may adopt either bundle: `renovate` ships the
    Renovate config, `github` ships `dependabot.yml`. `bundles/github/.github/CONFIG.md`
    promises exactly this to the reader, which is the claim under test.
    """
    renovate = json.loads((_ROOT / "bundles" / "renovate" / "renovate.json").read_text(encoding="utf-8"))
    assert "github-actions" in renovate["enabledManagers"], (
        "the renovate bundle does not enable the github-actions manager, so a consumer's "
        "SHA-pinned workflows would never be bumped"
    )

    dependabot = yaml.safe_load(
        (_ROOT / "bundles" / "github" / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    )
    ecosystems = {entry.get("package-ecosystem") for entry in dependabot.get("updates", [])}
    assert "github-actions" in ecosystems, (
        "the github bundle's dependabot.yml declares no github-actions ecosystem, so a "
        "consumer relying on Dependabot alone would never see an action bump"
    )
