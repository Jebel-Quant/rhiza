"""Tests for go.mod, the Version constant, and the release config that rewrites it.

This file and its associated tests flow down via a SYNC action from the
jebel-quant/rhiza repository (https://github.com/jebel-quant/rhiza).

The Go counterpart of ``test_pyproject.py``. Written in Python and run through uv by
``make rhiza-test`` rather than as a ``_test.go``, for the same reason the rest of the
suite is: it validates *configuration*, and the release flow that reads it is Python
tooling. ``uv`` lives in ``core`` precisely so it is available whatever the project's
language.

Where it does **not** overlap with ``internal/version/version_test.go``: that one runs
inside the module and asserts the shape of the constant. This one asserts the wiring
around it — that ``.bumpversion.toml`` still points at the file, and that the constant
agrees with the tag. A Go test could read git too, but the invariants here belong with
the release config rather than with the package.

Validates that:
- go.mod exists, declares a module path, and pins a `go` directive `make deps` supports
- internal/version/version.go still carries the constant the release flow writes to
- .bumpversion.toml is the config bump-my-version discovers, and targets that constant
- the constant matches the latest git tag (vX.Y.Z → X.Y.Z)
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

# The one place a Go module's version exists in the source tree.
_VERSION_GO = Path("internal") / "version" / "version.go"

# `const Version = "..."` — the literal .bumpversion.toml searches for.
_VERSION_CONST_RE = re.compile(r'^const\s+Version\s*=\s*"([^"]*)"', re.MULTILINE)

_MODULE_RE = re.compile(r"^module\s+(\S+)", re.MULTILINE)
_GO_DIRECTIVE_RE = re.compile(r"^go\s+(\d+)\.(\d+)", re.MULTILINE)

# `go mod tidy -diff`, which `make deps` is, landed in 1.23. Below that the gate fails
# with an unrecognised flag rather than with a dependency problem.
_MIN_GO = (1, 23)

# The only filenames bump-my-version auto-discovers (#1453). A Go module owns none of
# them — it has no manifest at all — which is why go-core ships the first one.
_DISCOVERABLE_CONFIGS = (".bumpversion.toml", ".bumpversion.cfg", "setup.cfg", "pyproject.toml")


def _has_bumpversion_section(path: Path) -> bool:
    """Report whether a config file carries a bumpversion section at all.

    Args:
        path: Candidate config file; a missing or malformed file counts as absent.

    Returns:
        True when the file declares ``[tool.bumpversion]`` (TOML) or ``[bumpversion]``
        (INI).
    """
    if not path.is_file():
        return False
    if path.suffix == ".cfg":
        return "[bumpversion]" in path.read_text(encoding="utf-8")
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError:
        return False
    return isinstance(data.get("tool", {}).get("bumpversion"), dict)


@pytest.fixture(scope="module")
def go_mod(root: Path) -> str:
    """Return the text of go.mod."""
    path = root / "go.mod"
    if not path.is_file():
        pytest.skip("go.mod not found")
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def declared_version(root: Path) -> str:
    """Return the value of the ``Version`` constant in internal/version/version.go."""
    path = root / _VERSION_GO
    if not path.is_file():
        pytest.fail(
            f"{_VERSION_GO.as_posix()} not found. A Go module's version is its git tag, so this "
            f"constant is the only version location in the tree and .bumpversion.toml writes to "
            f"it; without the file the release flow has nowhere to write. Restore it from the "
            f"go-core bundle."
        )
    match = _VERSION_CONST_RE.search(path.read_text(encoding="utf-8"))
    if match is None:
        pytest.fail(
            f'{_VERSION_GO.as_posix()} declares no `const Version = "..."` line. That literal is '
            f"what .bumpversion.toml searches for, and with ignore_missing_version = false the "
            f"release fails on it rather than warning."
        )
    return match.group(1)


@pytest.fixture(scope="module")
def bumpversion(root: Path) -> dict:
    """Return the [tool.bumpversion] table from .bumpversion.toml."""
    path = root / ".bumpversion.toml"
    if not path.is_file():
        pytest.skip(".bumpversion.toml not found — reported by TestBumpversionConfig")
    with path.open("rb") as handle:
        return tomllib.load(handle).get("tool", {}).get("bumpversion", {})


class TestGoMod:
    """Tests for go.mod's presence and the directives the gates depend on."""

    def test_go_mod_exists(self, root: Path) -> None:
        """go.mod must exist at the project root."""
        assert (root / "go.mod").is_file(), "go.mod not found at project root"

    def test_module_path_declared(self, go_mod: str) -> None:
        """go.mod must declare a module path."""
        match = _MODULE_RE.search(go_mod)
        assert match is not None, "go.mod declares no `module` directive"
        assert match.group(1).strip(), "go.mod's `module` directive is empty"

    def test_go_directive_is_recent_enough_for_the_deps_gate(self, go_mod: str) -> None:
        """The `go` directive must be at least 1.23.

        Not a general preference: ``make deps`` is ``go mod tidy -diff``, and that flag
        landed in 1.23. An older directive fails the gate with an unrecognised flag,
        which reads as a tooling break rather than as a version floor. A newer toolchain
        on the machine does not help — the directive is what sets the language version.
        """
        match = _GO_DIRECTIVE_RE.search(go_mod)
        assert match is not None, "go.mod declares no `go` directive"
        found = (int(match.group(1)), int(match.group(2)))
        assert found >= _MIN_GO, (
            f"go.mod pins go {found[0]}.{found[1]}, but `make deps` runs `go mod tidy -diff` "
            f"which requires {_MIN_GO[0]}.{_MIN_GO[1]} or newer"
        )


class TestVersionConstant:
    """The release flow's only writable version location must stay writable."""

    def test_version_file_exists(self, root: Path) -> None:
        """internal/version/version.go must be present."""
        assert (root / _VERSION_GO).is_file(), (
            f"{_VERSION_GO.as_posix()} is missing; it is the only version location in a Go "
            f"module's source tree and .bumpversion.toml writes to it"
        )

    def test_version_is_semver(self, declared_version: str) -> None:
        """The constant must parse as MAJOR.MINOR.PATCH with an optional pre-release.

        ``version_test.go`` asserts the same shape from inside the module. Duplicated
        deliberately: that test can be deleted by a project that adds its own, and this
        invariant belongs to the release config either way.
        """
        assert re.match(r"^\d+\.\d+\.\d+(?:-[a-z]+\.\d+)?$", declared_version), (
            f"Version = {declared_version!r} does not match the shape .bumpversion.toml parses "
            f"(MAJOR.MINOR.PATCH with an optional -pre.N suffix)"
        )


class TestBumpversionConfig:
    """The release flow must find a version config, not silently invent one (#1453).

    bump-my-version searches four filenames and stops. Finding none it does **not**
    fail — it falls back to ``git describe`` and reports the last reachable tag as the
    current version. For Go that fallback is especially easy to miss, because reading
    the version from the tag is *also* what the shipped config does deliberately; the
    difference is that the real config knows where to write the value back.
    """

    def test_a_discoverable_config_exists(self, root: Path) -> None:
        """A bumpversion section must live in a file bump-my-version actually reads."""
        found = [name for name in _DISCOVERABLE_CONFIGS if _has_bumpversion_section(root / name)]
        hint = ""
        if (root / ".rhiza" / ".cfg.toml").is_file():
            hint = (
                " A leftover .rhiza/.cfg.toml is present: that path is never auto-discovered "
                "(it predates the fix for issue #1453) and can be deleted."
            )
        assert found, (
            f"No bumpversion config was found in any file bump-my-version searches "
            f"({', '.join(_DISCOVERABLE_CONFIGS)}). It will silently fall back to "
            f"`git describe` and write the new version nowhere. Restore the .bumpversion.toml "
            f"the go-core bundle ships.{hint}"
        )

    def test_no_other_config_shadows_the_go_config(self, root: Path) -> None:
        """No second bumpversion section may compete with .bumpversion.toml.

        ``.bumpversion.toml`` is searched first and wins, so a table declared in a
        pyproject.toml the repo carries for tooling is inert — and being inert, it
        drifts out of step unnoticed.
        """
        if not _has_bumpversion_section(root / ".bumpversion.toml"):
            pytest.skip("no .bumpversion.toml — reported by test_a_discoverable_config_exists")
        duplicates = [
            name
            for name in _DISCOVERABLE_CONFIGS
            if name != ".bumpversion.toml" and _has_bumpversion_section(root / name)
        ]
        assert not duplicates, (
            f"{duplicates} also declares a bumpversion section. .bumpversion.toml is searched "
            f"first and wins, so the other config never runs."
        )

    def test_the_config_does_not_pin_a_current_version(self, bumpversion: dict) -> None:
        """``current_version`` must stay absent from a synced config.

        The file is owned by rhiza, so a value only the consuming repo can maintain
        would be reset by the next ``/rhiza:update``. For a Go module omitting it is
        not even a compromise: the module version *is* the newest tag, which is exactly
        what bump-my-version then reads.
        """
        assert "current_version" not in bumpversion, (
            "[tool.bumpversion].current_version is set in a file rhiza syncs; the next "
            "/rhiza:update would overwrite it. Omit the key — for Go the tag is the version."
        )

    def test_the_config_targets_the_version_constant(self, bumpversion: dict) -> None:
        """A ``[[files]]`` entry must point at internal/version/version.go.

        Without it the bump still "succeeds" while writing the new version nowhere at
        all — Go has no manifest to fall back on, so the constant is the whole story.
        """
        targets = [entry.get("filename") for entry in bumpversion.get("files", [])]
        assert _VERSION_GO.as_posix() in targets, (
            f"no [[tool.bumpversion.files]] entry targets {_VERSION_GO.as_posix()} (found "
            f"{targets}); a bump would write the new version nowhere"
        )

    def test_the_version_search_is_anchored_to_the_declaration(self, bumpversion: dict) -> None:
        """The search must include `const Version`, not just a bare version string.

        ``search`` is applied to every occurrence in the file, and version.go's own doc
        comment explains the release flow — so a bare number would also rewrite a
        version mentioned in prose or in an example.
        """
        entries = [entry for entry in bumpversion.get("files", []) if entry.get("filename") == _VERSION_GO.as_posix()]
        if not entries:
            pytest.skip("no version.go entry — reported by test_the_config_targets_the_version_constant")
        for entry in entries:
            search = str(entry.get("search", ""))
            assert "const Version" in search, (
                f"the version.go entry's search {search!r} is not anchored to the declaration; "
                f"it would also rewrite a version appearing in a comment or an example"
            )

    def test_the_release_flow_owns_the_commit_and_the_tag(self, bumpversion: dict) -> None:
        """``/rhiza:release`` folds the changelog into the bump commit and tags it itself."""
        for key in ("commit", "tag"):
            assert bumpversion.get(key, False) is False, (
                f"[tool.bumpversion].{key} must be false: the release flow commits and tags "
                f"itself so the changelog lands in the bump commit, and a bare "
                f"`bump-my-version bump` would otherwise add a second commit and a duplicate tag"
            )


class TestGitTagVersion:
    """Harmony between the latest git tag and the Version constant.

    Reachability of that tag is asserted by ``test_release_tags.py``, which ``core``
    ships for every language layer.
    """

    def test_latest_tag_matches_the_version_constant(self, latest_tag: str, declared_version: str) -> None:
        """The latest git tag (vX.Y.Z) must match the ``Version`` constant.

        For Go this is the definition of the version rather than a consistency check:
        consumers resolve the module at the tag, so a constant that disagrees means a
        built binary reports a version nobody can ``go get``. The release flow keeps
        them in step by rewriting the constant and tagging in one commit; drift means
        someone edited one of the two by hand.
        """
        assert latest_tag.lstrip("v") == declared_version, (
            f"Latest git tag {latest_tag!r} does not match the Version constant "
            f"{declared_version!r} in {_VERSION_GO.as_posix()}. Consumers resolve the module at "
            f"the tag, so the built binary would report a version that cannot be fetched."
        )
