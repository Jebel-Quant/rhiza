"""Tests for Cargo.toml structure and the release config that rewrites it.

This file and its associated tests flow down via a SYNC action from the
jebel-quant/rhiza repository (https://github.com/jebel-quant/rhiza).

The Rust counterpart of ``test_pyproject.py``. Written in Python and run through uv by
``make rhiza-test`` rather than as a ``#[test]``, for the same reason the rest of the
suite is: it validates *configuration*, and the release flow that reads it is Python
tooling. ``uv`` lives in ``core`` precisely so it is available whatever the project's
language.

Validates that Cargo.toml:
- is syntactically valid TOML
- contains the [package] fields cargo publish requires
- declares a semver version
- carries a license or license-file, which deny.toml's allow-list checks against
- version matches the latest git tag (vX.Y.Z → X.Y.Z)

…and that the shipped .bumpversion.toml can still write the version back:
- it is the config bump-my-version discovers, and nothing shadows it
- it points at Cargo.toml's [package] table, anchored
- it leaves the commit and the tag to /rhiza:release
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+")

# cargo tolerates more than this, but a crate that cannot be published is a crate whose
# release flow breaks at the last step rather than the first.
_REQUIRED_PACKAGE_FIELDS = ("name", "version", "edition", "description")

# The only filenames bump-my-version auto-discovers (#1453). A Rust project owns none of
# them natively, which is why rust-core ships the first one.
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
def cargo_toml(root: Path) -> dict:
    """Load and return Cargo.toml as a parsed dict."""
    path = root / "Cargo.toml"
    if not path.exists():
        pytest.skip("Cargo.toml not found")
    with path.open("rb") as handle:
        return tomllib.load(handle)


@pytest.fixture(scope="module")
def package(cargo_toml: dict) -> dict:
    """Return the [package] table, skipping on a virtual workspace manifest.

    A workspace root legitimately has no ``[package]`` — it carries only
    ``[workspace]`` — and its members hold the versions. Nothing here applies.
    """
    table = cargo_toml.get("package")
    if not isinstance(table, dict):
        if "workspace" in cargo_toml:
            pytest.skip("virtual workspace manifest — the members carry the versions")
        pytest.fail("Cargo.toml is missing a [package] table")
    return table


@pytest.fixture(scope="module")
def bumpversion(root: Path) -> dict:
    """Return the [tool.bumpversion] table from .bumpversion.toml."""
    path = root / ".bumpversion.toml"
    if not path.is_file():
        pytest.skip(".bumpversion.toml not found — reported by TestBumpversionConfig")
    with path.open("rb") as handle:
        return tomllib.load(handle).get("tool", {}).get("bumpversion", {})


class TestCargoToml:
    """Tests for basic Cargo.toml existence and validity."""

    def test_cargo_toml_exists(self, root: Path) -> None:
        """Cargo.toml must exist at the project root."""
        assert (root / "Cargo.toml").is_file(), "Cargo.toml not found at project root"

    def test_cargo_toml_is_valid_toml(self, root: Path) -> None:
        """Cargo.toml must be syntactically valid TOML."""
        with (root / "Cargo.toml").open("rb") as handle:
            data = tomllib.load(handle)
        assert isinstance(data, dict), "Parsed Cargo.toml must be a TOML table"


class TestPackageFields:
    """Tests for required fields within the [package] table."""

    @pytest.mark.parametrize("field", _REQUIRED_PACKAGE_FIELDS)
    def test_required_field_present(self, package: dict, field: str) -> None:
        """Each required [package] field must be present."""
        assert field in package, f"[package] is missing required field '{field}'"

    def test_name_is_non_empty_string(self, package: dict) -> None:
        """[package].name must be a non-empty string."""
        name = package.get("name", "")
        assert isinstance(name, str), "[package].name must be a string"
        assert name.strip(), "[package].name must be a non-empty string"

    def test_version_follows_semver(self, package: dict) -> None:
        """[package].version must follow semver (MAJOR.MINOR.PATCH).

        Not merely a convention here: ``.bumpversion.toml``'s ``parse`` regex and its
        ``tag_name = "v{new_version}"`` both assume this shape, and a version cargo
        accepts but that regex does not would fail the release rather than the build.
        """
        version = package.get("version", "")
        if isinstance(version, dict):
            pytest.skip("[package].version is inherited from the workspace")
        assert _SEMVER_RE.match(str(version)), (
            f"[package].version {version!r} does not follow semver (expected MAJOR.MINOR.PATCH)"
        )

    def test_description_is_non_empty_string(self, package: dict) -> None:
        """[package].description must be a non-empty string."""
        desc = package.get("description", "")
        if isinstance(desc, dict):
            pytest.skip("[package].description is inherited from the workspace")
        assert isinstance(desc, str), "[package].description must be a string"
        assert desc.strip(), "[package].description must be a non-empty string"

    def test_a_license_is_declared(self, package: dict) -> None:
        """[package] must declare `license` or `license-file`.

        ``make license`` is ``cargo deny check licenses`` and deny.toml is an
        allow-list, so a crate with no licence of its own fails that gate on itself
        rather than on a dependency.
        """
        declared = [key for key in ("license", "license-file") if package.get(key)]
        assert declared, (
            "[package] declares neither 'license' nor 'license-file'; `make license` runs "
            "cargo-deny against an allow-list and fails a crate that does not state its own"
        )


class TestBumpversionConfig:
    """The release flow must find a version config, not silently invent one (#1453).

    bump-my-version searches four filenames and stops. Finding none it does **not**
    fail — it falls back to ``git describe`` and reports the last reachable tag as the
    current version, so a release can be cut at a version that already exists. A Rust
    project owns none of those four filenames natively, so ``rust-core`` ships a root
    ``.bumpversion.toml``; these tests assert it is still the file that wins and still
    points where the version actually lives.
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
            f"`git describe`, so a release can be cut at a version that already exists. "
            f"Restore the .bumpversion.toml the rust-core bundle ships.{hint}"
        )

    def test_no_pyproject_shadows_the_rust_config(self, root: Path) -> None:
        """A stray ``[tool.bumpversion]`` in pyproject.toml must not take over.

        ``.bumpversion.toml`` is searched first, so this is about the reverse mistake:
        a Rust repo that also carries a Python manifest (a helper package, a docs
        toolchain) and declares the table there too now has two configs, only one of
        which knows about Cargo.toml.
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
            f"first and wins, so the other config is inert — and being inert, it drifts."
        )

    def test_the_config_does_not_pin_a_current_version(self, bumpversion: dict) -> None:
        """``current_version`` must stay absent from a synced config.

        The file is owned by rhiza, so a value only the consuming repo can maintain
        would be reset by the next ``/rhiza:update``. Omitting it makes bump-my-version
        derive the version from the newest tag matching ``tag_name``, which is what
        Cargo.toml carries in any repo whose crate version and tags agree.
        """
        assert "current_version" not in bumpversion, (
            "[tool.bumpversion].current_version is set in a file rhiza syncs; the next "
            "/rhiza:update would overwrite it. Omit the key and let the newest tag supply it."
        )

    def test_the_config_targets_cargo_toml(self, bumpversion: dict) -> None:
        """A ``[[files]]`` entry must point at Cargo.toml, or nothing gets rewritten.

        With no entry for it the bump still "succeeds": it rewrites ``current_version``
        in its own config, tags nothing, and leaves ``[package].version`` untouched.
        """
        targets = [entry.get("filename") for entry in bumpversion.get("files", [])]
        assert "Cargo.toml" in targets, (
            f"no [[tool.bumpversion.files]] entry targets Cargo.toml (found {targets}); "
            f"a bump would leave [package].version untouched"
        )

    def test_the_cargo_toml_pattern_is_anchored_to_the_package_table(self, bumpversion: dict) -> None:
        """The search must be anchored, or it rewrites a same-numbered dependency.

        ``search``/``replace`` are applied to *every* occurrence in the file, so a bare
        ``version = "{current_version}"`` also rewrites a ``[dependencies]`` entry that
        happens to share the crate's number.
        """
        entries = [entry for entry in bumpversion.get("files", []) if entry.get("filename") == "Cargo.toml"]
        if not entries:
            pytest.skip("no Cargo.toml entry — reported by test_the_config_targets_cargo_toml")
        for entry in entries:
            search = str(entry.get("search", ""))
            assert entry.get("regex") is True, (
                f"the Cargo.toml entry's search {search!r} is not a regex, so it cannot be "
                f"anchored to the [package] table and would also rewrite a [dependencies] pin "
                f"sharing the crate's version"
            )
            # Backslashes stripped before matching: the anchored form is a regex, so the
            # table header is escaped there as `\[package\]`.
            assert "[package]" in search.replace("\\", ""), (
                f"the Cargo.toml entry's search {search!r} does not mention the [package] table; "
                f"an unanchored version pattern also rewrites a [dependencies] entry that happens "
                f"to share the crate's number"
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
    """Harmony between the latest git tag and the crate version.

    Reachability of that tag is asserted by ``test_release_tags.py``, which ``core``
    ships for every language layer.
    """

    def test_latest_tag_matches_cargo_version(self, latest_tag: str, package: dict) -> None:
        """The latest git tag (vX.Y.Z) must match [package].version.

        This is the invariant ``.bumpversion.toml`` relies on rather than a style
        preference. With no ``current_version`` key, bump-my-version reads the current
        version from the newest tag and then searches Cargo.toml for it; if the two
        disagree the next release fails with "did not find current version" — loudly,
        but only at release time, which is the worst moment to find out.
        """
        version = package.get("version")
        if isinstance(version, dict):
            pytest.skip("[package].version is inherited from the workspace")
        assert latest_tag.lstrip("v") == str(version), (
            f"Latest git tag {latest_tag!r} does not match [package].version {version!r}. "
            f"bump-my-version derives the current version from the tag and then looks for it "
            f"in Cargo.toml, so the next release would fail to find it."
        )
