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


@functools.cache
def _manager(dep: str = "rhiza-task") -> dict:
    """Return the custom manager that watches one pin.

    Args:
        dep: The manager's ``depNameTemplate``.

    Returns:
        The manager mapping from ``renovate.json``.
    """
    config = json.loads(_RENOVATE.read_text(encoding="utf-8"))
    managers = [m for m in config.get("customManagers", []) if m.get("depNameTemplate") == dep]
    assert len(managers) == 1, (
        f"expected exactly one custom manager for {dep} in renovate.json, found {len(managers)}. "
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


# The tectonic pin, as the workflows spell it: `TECTONIC_VERSION: "0.17.0"`.
_TECTONIC = re.compile(r'TECTONIC_VERSION:\s*"(\d+\.\d+\.\d+)"')


def _tectonic_files() -> list[str]:
    """Return the tracked files carrying a tectonic pin.

    Returns:
        Repo-relative paths, prose and history excluded.
    """
    out = []
    for path in _tracked_files():
        if path in _NOT_THE_MANAGER_S_JOB or path.startswith(_PROSE_PREFIXES):
            continue
        if _TECTONIC.search((_ROOT / path).read_text(encoding="utf-8", errors="replace")):
            out.append(path)
    return sorted(out)


class TestTheTectonicPin:
    """The engine pin gets the same treatment as the CLI pin, for the same reason.

    tectonic is not on any runner or in any container this template targets, so each caller
    downloads a pinned release asset. Two callers today: the paper workflows compile with it,
    and the book workflows need it because ``paper`` is a prerequisite of ``book`` -- a
    prerequisite that *skips* without the engine, which publishes a nav entry with no asset
    behind it and a green tick over the top.

    The failure mode being guarded is not a broken build but a silent one: an unmanaged pin
    ages, and the paper compiles fine on an old engine for a long time before it doesn't.
    """

    def test_the_scan_finds_the_pins_at_all(self) -> None:
        """Positive control: no files would make the assertions below vacuous."""
        found = _tectonic_files()
        assert len(found) >= 2, (
            f"found only {len(found)} file(s) carrying a tectonic pin: {found}. The paper "
            f"workflow and the book workflow both install the engine, so the scan is looking "
            f"in the wrong place."
        )

    @pytest.mark.parametrize("path", _tectonic_files())
    def test_every_pinned_file_is_matched_by_the_manager(self, path: str) -> None:
        """A pin no ``managerFilePatterns`` entry matches is a pin Renovate never bumps."""
        patterns = [_as_regex(p) for p in _manager("tectonic-typesetting/tectonic")["managerFilePatterns"]]
        assert any(p.search(path) for p in patterns), (
            f"{path} carries a TECTONIC_VERSION pin that no managerFilePatterns entry "
            f"matches, so Renovate will never bump it."
        )

    @pytest.mark.parametrize("path", _tectonic_files())
    def test_the_match_string_captures_every_occurrence(self, path: str) -> None:
        """Matching the file is not enough: the regex must capture each pin's version."""
        match_strings = [_match_string(s) for s in _manager("tectonic-typesetting/tectonic")["matchStrings"]]
        text = (_ROOT / path).read_text(encoding="utf-8")
        occurrences = _TECTONIC.findall(text)
        assert any([m.group("currentValue") for m in regex.finditer(text)] == occurrences for regex in match_strings), (
            f"{path} carries {len(occurrences)} tectonic pin(s) but no matchStrings entry captures all of them."
        )

    def test_every_pin_names_the_same_version(self) -> None:
        """Two engines across the workflows is a difference nothing would report.

        The paper workflow's PDF and the book's copy of it would be built by different
        versions, which is the kind of divergence that shows up as a rendering difference
        between the artifact and the published site rather than as a failure.
        """
        versions: dict[str, set[str]] = {}
        for path in _tectonic_files():
            for version in _TECTONIC.findall((_ROOT / path).read_text(encoding="utf-8")):
                versions.setdefault(version, set()).add(path)
        assert len(versions) == 1, (
            f"the tectonic pin disagrees with itself across files: "
            f"{ {v: sorted(p) for v, p in versions.items()} }. The paper artifact and the "
            f"book's copy of it would be built by different engines."
        )


# The uv pin in the shim, as written: `UV_VERSION ?= 0.13.10`.
_UV_VERSION = re.compile(r"^UV_VERSION \?= (\d+\.\d+\.\d+)$", re.MULTILINE)
_SHIM = "bundles/core/Makefile"


class TestTheUvInstallerPin:
    """The uv the shim bootstraps is pinned, and Renovate is what moves the pin (#1797).

    The shim downloads uv only when none is on PATH -- a fresh machine or a bare CI image,
    which is exactly where reproducibility matters. An unversioned installer URL makes that
    the one unpinned step in a toolchain that pins everything else, and every consumer
    inherits it. The unversioned URL itself is refused by
    ``tests/security/test_security_patterns.py``'s piped-installer allowlist.
    """

    def test_the_shim_pins_a_uv_version(self) -> None:
        """Exactly one semver ``UV_VERSION`` default, used by the installer URL."""
        text = (_ROOT / _SHIM).read_text(encoding="utf-8")
        pins = _UV_VERSION.findall(text)
        assert len(pins) == 1, f"expected one `UV_VERSION ?= X.Y.Z` in {_SHIM}, found {pins}"
        assert "astral.sh/uv/$(UV_VERSION)/install.sh" in text, (
            f"{_SHIM} no longer installs uv through the pinned URL; an unversioned "
            f"astral.sh/uv/install.sh installs whatever uv is newest"
        )
        assert "astral.sh/uv/install.sh" not in text, f"{_SHIM} still carries an unversioned installer URL"

    def test_the_manager_matches_the_shim_and_captures_the_pin(self) -> None:
        """A manager that finds the file but not the literal is a silent no-op (#1579)."""
        manager = _manager("uv")
        patterns = [_as_regex(p) for p in manager["managerFilePatterns"]]
        assert any(p.search(_SHIM) for p in patterns), f"no managerFilePatterns entry matches {_SHIM}"
        text = (_ROOT / _SHIM).read_text(encoding="utf-8")
        captured = [m.group("currentValue") for s in manager["matchStrings"] for m in _match_string(s).finditer(text)]
        assert captured == _UV_VERSION.findall(text), f"the uv manager captured {captured} from {_SHIM}"

    def test_the_root_makefile_is_not_matched(self) -> None:
        """The dogfood symlink stays out of reach, as for the rhiza-task manager."""
        patterns = [_as_regex(p) for p in _manager("uv")["managerFilePatterns"]]
        assert not any(p.search("Makefile") for p in patterns), (
            "the uv manager matches the root `Makefile`, a dogfood symlink Renovate would turn into a real file"
        )


# Renovate's built-in default for the gitlabci manager; ours extends it rather than replacing it.
_GITLABCI_DEFAULT = re.compile(r"\.gitlab-ci\.ya?ml$")
_LITERAL_IMAGE = re.compile(r"^\s*image:\s*[^$\s]", re.MULTILINE)


def _gitlab_files_with_literal_images() -> list[str]:
    """Return every tracked gitlab-bundle YAML file carrying an `image:` that is not a variable.

    Returns:
        Repo-relative paths.
    """
    return [
        path
        for path in _tracked_files()
        if path.startswith("bundles/gitlab")
        and path.endswith((".yml", ".yaml"))
        and _LITERAL_IMAGE.search((_ROOT / path).read_text(encoding="utf-8"))
    ]


# Every other place a uv version is pinned (#1818): the `version:` input of each
# astral-sh/setup-uv step, and the GitLab `UV_IMAGE` tag. Both shapes, as written.
_SETUP_UV = re.compile(r"astral-sh/setup-uv@[^\n]*\n(?:[^\n]*\n){0,6}?\s+version: \"(\d+\.\d+\.\d+)\"")
_UV_IMAGE = re.compile(r"UV_IMAGE: \"ghcr\.io/astral-sh/uv:(\d+\.\d+\.\d+)-")


def _uv_pins() -> dict[str, list[str]]:
    """Return every uv version pin in the tree, by file.

    Prose (docs, tests) is skipped: it quotes pins rather than carrying them. The
    Dockerfile builder image is deliberately absent -- the dockerfile manager owns it.

    Returns:
        Repo-relative path to the versions it pins, in file order.
    """
    pins: dict[str, list[str]] = {}
    for path in _tracked_files():
        if path.startswith(_PROSE_PREFIXES) or path in _NOT_THE_MANAGER_S_JOB:
            continue
        if not path.endswith((".yml", ".yaml", "Makefile")):
            continue
        text = (_ROOT / path).read_text(encoding="utf-8")
        found = _UV_VERSION.findall(text) + _SETUP_UV.findall(text) + _UV_IMAGE.findall(text)
        if found:
            pins[path] = found
    return pins


class TestEveryUvPinMovesTogether:
    """One uv version across the shim, the CI workflows and the GitLab image (#1818).

    The shim's pin had a manager and moved to 0.13.x; the setup-uv inputs and `UV_IMAGE`
    had none and stayed on 0.11.16, so a developer's bootstrap and every CI run used
    different uv releases -- the drift #1383 fixed once already. All of them now belong to
    the one `uv` manager, which Renovate bumps as a single dependency.
    """

    def test_the_scan_finds_the_pins_at_all(self) -> None:
        """Positive control: the shim, the CI workflow and the GitLab image all carry a pin."""
        pins = _uv_pins()
        assert {_SHIM, ".github/workflows/rhiza_ci.yml", "bundles/gitlab/.gitlab-ci.yml"} <= set(pins), sorted(pins)
        assert sum(len(v) for v in pins.values()) >= 20, "fewer setup-uv pins than the workflows carry"

    @pytest.mark.parametrize("path", sorted(_uv_pins()))
    def test_every_pinned_file_is_matched_by_the_manager(self, path: str) -> None:
        """A pin in a file no ``managerFilePatterns`` entry matches is a pin that only ages."""
        patterns = [_as_regex(p) for p in _manager("uv")["managerFilePatterns"]]
        assert any(p.search(path) for p in patterns), f"no uv managerFilePatterns entry matches {path}"

    @pytest.mark.parametrize("path", sorted(_uv_pins()))
    def test_the_match_strings_capture_every_pin(self, path: str) -> None:
        """Matching the file is not enough: the manager must capture each version in it."""
        text = (_ROOT / path).read_text(encoding="utf-8")
        captured = sorted(
            m.group("currentValue") for s in _manager("uv")["matchStrings"] for m in _match_string(s).finditer(text)
        )
        assert captured == sorted(_uv_pins()[path]), f"the uv manager captured {captured} from {path}"

    def test_every_pin_names_the_same_version(self) -> None:
        """Two uv releases across the toolchain is a difference nothing would report."""
        versions: dict[str, set[str]] = {}
        for path, found in _uv_pins().items():
            for version in found:
                versions.setdefault(version, set()).add(path)
        assert len(versions) == 1, f"uv pins disagree: { {v: sorted(p) for v, p in versions.items()} }"


class TestGitlabImageManager:
    """The pinned GitLab job images must be watched by Renovate (#1814).

    The built-in ``gitlabci`` manager reads only ``.gitlab-ci.yml`` by default, so the jobs
    under ``bundles/*/.gitlab/workflows/`` were invisible to it: an exact pin there would
    only age. ``renovate.json`` extends the manager's file patterns to those folders. Root
    only, for the reason the RHIZA_TASK manager gives: in a consumer these files are
    template-owned, and a bump there is overwritten by the next sync.
    """

    def test_the_scan_finds_the_images_at_all(self) -> None:
        """Positive control: the release, Renovate and quality-review workflows carry images."""
        assert len(_gitlab_files_with_literal_images()) >= 3

    def test_the_gitlabci_manager_is_enabled(self) -> None:
        """A file pattern on a disabled manager is a pattern nothing reads."""
        config = json.loads(_RENOVATE.read_text(encoding="utf-8"))
        assert "gitlabci" in config.get("enabledManagers", [])

    @pytest.mark.parametrize("path", _gitlab_files_with_literal_images())
    def test_every_image_file_is_matched_by_the_manager(self, path: str) -> None:
        """An image in a file the manager does not read is an image Renovate never bumps."""
        config = json.loads(_RENOVATE.read_text(encoding="utf-8"))
        patterns = [_as_regex(p) for p in config.get("gitlabci", {}).get("managerFilePatterns", [])]
        patterns.append(_GITLABCI_DEFAULT)
        assert any(p.search(path) for p in patterns), (
            f"{path} carries a pinned job image that the gitlabci manager does not read"
        )
