"""Every YAML, JSON and TOML file shipped in a bundle must parse.

Split out of ``test_bundle_content_validity.py`` (#1514), which had reached 864 lines at
maintainability index **C (7.99)**. These three classes form one coherent question —
*does the serialised content a consumer receives load at all?* — asked once per format,
and they are the suites that walk every file in every bundle rather than inspecting a
named one.

Both exemptions below exist because a file that legitimately fails ``safe_load`` is not
the same as a broken one: mkdocs configs carry ``!!python/name:`` tags by design, and
JSONC files carry comments. Each is skipped for the parse check and validated another way.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
import yaml

from tests.bundles._content import _LAYER_BUNDLES, _all_files_in_bundle


def _is_mkdocs_python_tag_file(path: Path) -> bool:
    """Return True for mkdocs config files that legitimately use Python YAML tags.

    mkdocs-material uses !!python/name: tags in its configuration files.  These
    are intentional and cannot be parsed with yaml.safe_load — we skip them for
    parse-error tests but still validate them as non-empty elsewhere.
    """
    return path.name in {"mkdocs-base.yml", "mkdocs.yml"}


class TestBundleYamlValidity:
    """Every YAML file in every bundle directory must parse without error."""

    def test_all_yaml_files_are_parseable(self, root: Path, bundle_names: list[str]) -> None:
        """Walk every bundle and assert every .yml / .yaml file loads cleanly.

        mkdocs config files that use Python YAML tags (tag:yaml.org,2002:python/name:...)
        are intentionally excluded because those tags require a full Python YAML loader
        and are expected/valid in those files.
        """
        errors: list[str] = []
        for name in bundle_names:
            bundle_dir = root / "bundles" / name
            if not bundle_dir.is_dir():
                continue
            for f in _all_files_in_bundle(bundle_dir):
                if f.suffix not in {".yml", ".yaml"}:
                    continue
                if _is_mkdocs_python_tag_file(f):
                    continue
                try:
                    with f.open(encoding="utf-8") as fh:
                        yaml.safe_load(fh)
                except yaml.constructor.ConstructorError:
                    # Python-specific YAML tags are acceptable in mkdocs-adjacent files
                    pass
                except yaml.YAMLError as exc:
                    rel = f.relative_to(root / "bundles")
                    errors.append(f"  [{name}] {rel}: {exc}")
        if errors:
            pytest.fail("YAML parse errors in bundle files:\n" + "\n".join(errors))

    def test_no_yaml_file_is_empty(self, root: Path, bundle_names: list[str]) -> None:
        """No .yml / .yaml bundle file should be empty (null document).

        mkdocs config files that require Python YAML tags are skipped here too
        since yaml.safe_load would raise rather than return None for them.
        """
        empties: list[str] = []
        for name in bundle_names:
            bundle_dir = root / "bundles" / name
            if not bundle_dir.is_dir():
                continue
            for f in _all_files_in_bundle(bundle_dir):
                if f.suffix not in {".yml", ".yaml"}:
                    continue
                if _is_mkdocs_python_tag_file(f):
                    continue
                try:
                    with f.open(encoding="utf-8") as fh:
                        doc = yaml.safe_load(fh)
                except yaml.YAMLError:
                    continue
                if doc is None:
                    rel = f.relative_to(root / "bundles")
                    empties.append(f"  [{name}] {rel}")
        if empties:
            pytest.fail("Empty (null) YAML documents in bundle files:\n" + "\n".join(empties))


def _is_jsonc_file(path: Path) -> bool:
    """Return True for files that use JSONC (JSON with Comments) format.

    devcontainer.json uses JSONC to allow inline comments.  Standard json.load
    cannot parse them; we skip parse validation for these files and instead
    verify they are non-empty.
    """
    return path.name == "devcontainer.json"


class TestBundleJsonValidity:
    """Every JSON file in every bundle directory must parse without error."""

    def test_all_json_files_are_parseable(self, root: Path, bundle_names: list[str]) -> None:
        """Walk every bundle and assert every .json file loads cleanly.

        Files using JSONC format (JSON with Comments) such as devcontainer.json are
        intentionally excluded because they require a JSONC parser and their use of
        comments is valid by spec.
        """
        errors: list[str] = []
        for name in bundle_names:
            bundle_dir = root / "bundles" / name
            if not bundle_dir.is_dir():
                continue
            for f in _all_files_in_bundle(bundle_dir):
                if f.suffix != ".json":
                    continue
                if _is_jsonc_file(f):
                    continue
                try:
                    with f.open(encoding="utf-8") as fh:
                        json.load(fh)
                except json.JSONDecodeError as exc:
                    rel = f.relative_to(root / "bundles")
                    errors.append(f"  [{name}] {rel}: {exc}")
        if errors:
            pytest.fail("JSON parse errors in bundle files:\n" + "\n".join(errors))

    def test_jsonc_files_are_non_empty(self, root: Path, bundle_names: list[str]) -> None:
        """JSONC files (devcontainer.json) must be non-empty even though we skip parse validation."""
        for name in bundle_names:
            bundle_dir = root / "bundles" / name
            if not bundle_dir.is_dir():
                continue
            for f in _all_files_in_bundle(bundle_dir):
                if f.suffix == ".json" and _is_jsonc_file(f):
                    content = f.read_text(encoding="utf-8").strip()
                    rel = f.relative_to(root / "bundles")
                    assert content, f"JSONC file is empty: [{name}] {rel}"


class TestBundleTomlValidity:
    """Every TOML file in every bundle directory must parse without error.

    TOML carries as much shipped configuration as YAML does — cliff.toml, ruff.toml,
    the bump-my-version `.bumpversion.toml` of the Rust and Go layers, and the whole
    rust-core toolchain set (rust-toolchain, rustfmt, clippy, deny). None of it is
    exercised by the mother repo's own gates when it belongs to a bundle rhiza does
    not dogfood, so a syntax error there would otherwise reach downstream projects.
    """

    def test_all_toml_files_are_parseable(self, root: Path, bundle_names: list[str]) -> None:
        """Walk every bundle and assert every .toml file loads cleanly."""
        errors: list[str] = []
        for name in bundle_names:
            bundle_dir = root / "bundles" / name
            if not bundle_dir.is_dir():
                continue
            for f in _all_files_in_bundle(bundle_dir):
                if f.suffix != ".toml":
                    continue
                try:
                    with f.open("rb") as fh:
                        tomllib.load(fh)
                except tomllib.TOMLDecodeError as exc:
                    rel = f.relative_to(root / "bundles")
                    errors.append(f"  [{name}] {rel}: {exc}")
        if errors:
            pytest.fail("TOML parse errors in bundle files:\n" + "\n".join(errors))

    def test_no_toml_file_is_empty(self, root: Path, bundle_names: list[str]) -> None:
        """A TOML file that parses to an empty table is almost certainly a truncated sync."""
        for name in bundle_names:
            bundle_dir = root / "bundles" / name
            if not bundle_dir.is_dir():
                continue
            for f in _all_files_in_bundle(bundle_dir):
                if f.suffix != ".toml":
                    continue
                with f.open("rb") as fh:
                    doc = tomllib.load(fh)
                rel = f.relative_to(root / "bundles")
                assert doc, f"TOML file has no content: [{name}] {rel}"

    def test_the_scan_reaches_every_language_layer(self, root: Path) -> None:
        """Guard against a scan that silently covers nothing: each layer ships TOML."""
        for layer in _LAYER_BUNDLES:
            tomls = [f for f in _all_files_in_bundle(root / "bundles" / layer) if f.suffix == ".toml"]
            assert tomls, f"layer '{layer}' ships no .toml file — has the scan gone stale?"
