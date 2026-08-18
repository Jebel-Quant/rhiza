"""Per-bundle content checks: docs, Makefile fragments, legal, config.

What remains of the original 864-line module after #1514 split it three ways. Unlike its
two siblings, every class here inspects a *named* bundle or a named kind of file rather
than sweeping the whole tree:

- every bundle is described in ``template-bundles.yml`` and documented
- Makefile fragments expose at least one documented target (``## help`` comment)
- legal files have real content
- ``renovate.json`` carries the required schema declaration
- each language layer's ``.pre-commit-config.yaml`` names the config both prek entry
  points read (see the prek note in CLAUDE.md)
- the devcontainer definition is valid and self-consistent

The sweeping suites moved to ``test_bundle_parse_validity`` (YAML/JSON/TOML parse) and
``test_bundle_ci_content`` (workflow stubs, GitLab image pinning); shared helpers to
``tests/bundles/_content.py`` and the ``bundle_names`` fixture to ``conftest.py``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from tests.bundles._content import _LAYER_BUNDLES, _all_files_in_bundle


class TestBundleDocumentation:
    """Reference docs that describe bundles should stay aligned with bundle metadata."""

    def test_glossary_bundle_dependency_map_lists_all_bundles(self, root: Path, bundle_names: list[str]) -> None:
        """The glossary Mermaid bundle map should mention every defined bundle."""
        glossary = (root / "docs" / "reference" / "GLOSSARY.md").read_text(encoding="utf-8")

        match = re.search(r"### Bundle Dependency Map\n.*?```mermaid\n(.*?)\n```", glossary, re.DOTALL)
        assert match, "GLOSSARY.md should contain a Mermaid bundle dependency map"

        diagram = match.group(1)
        missing = [name for name in bundle_names if name not in diagram]
        assert not missing, f"Bundle dependency map is missing bundles: {missing}"

    @staticmethod
    def _readme_bundle_tables(root: Path) -> str:
        """Return the body of the README 'Available Template Bundles' tables section."""
        readme = (root / "README.md").read_text(encoding="utf-8")
        parts = readme.split("### Available Template Bundles", 1)
        assert len(parts) == 2, "README should contain an '### Available Template Bundles' section"
        # The bundle tables end at the closing pointer line back to template-bundles.yml.
        return parts[1].split("For a complete reference", 1)[0]

    def test_readme_bundle_tables_list_all_bundles(self, root: Path, bundle_names: list[str]) -> None:
        """Every bundle in template-bundles.yml must appear in the README bundle tables."""
        body = self._readme_bundle_tables(root)
        missing = [name for name in bundle_names if f"`{name}`" not in body]
        assert not missing, f"README bundle tables are missing bundles: {missing}"

    def test_readme_bundle_tables_have_no_stale_bundles(self, root: Path, bundle_names: list[str]) -> None:
        """Every bundle documented in the README bundle tables must be a defined bundle."""
        body = self._readme_bundle_tables(root)
        # First column of each table row, e.g. ``| `core` | ...``.
        documented = set(re.findall(r"^\|\s*`([a-z0-9-]+)`\s*\|", body, re.MULTILINE))
        stale = sorted(documented - set(bundle_names))
        assert not stale, f"README bundle tables document unknown bundles: {stale}"


# ---------------------------------------------------------------------------
# GitHub workflow stubs
# ---------------------------------------------------------------------------


# Prefix every reusable-workflow stub must call to delegate to this repository.
_REUSABLE_WORKFLOW_PREFIX = "jebel-quant/rhiza/.github/workflows/"

# rhiza_*.yml workflows that are intentionally NOT thin stubs.  rhiza_release.yml
# is a full release-automation workflow that runs many first-party steps itself
# rather than delegating to a reusable workflow.
_NON_STUB_RHIZA_WORKFLOWS = {"rhiza_release.yml"}


class TestMakefileFragments:
    """Makefile fragments in bundles must follow the help-comment convention."""

    def test_all_mk_files_have_at_least_one_documented_target(self, root: Path, bundle_names: list[str]) -> None:
        """Every .mk fragment that is not a customisation template must document at least one target with ##."""
        skip_names = {"custom-env.mk", "custom-task.mk", "README.md"}
        violations: list[str] = []
        for bundle_name in bundle_names:
            bundle_dir = root / "bundles" / bundle_name
            if not bundle_dir.is_dir():
                continue
            for mk_file in _all_files_in_bundle(bundle_dir):
                if mk_file.suffix != ".mk" or mk_file.name in skip_names:
                    continue
                content = mk_file.read_text(encoding="utf-8")
                # A documented target looks like: target: ... ## description
                if "##" not in content:
                    rel = mk_file.relative_to(root / "bundles")
                    violations.append(f"  [{bundle_name}] {rel}")
        if violations:
            pytest.fail("Makefile fragments without any ## help comment:\n" + "\n".join(violations))

    def test_all_mk_files_have_phony_declarations(self, root: Path, bundle_names: list[str]) -> None:
        """Makefile fragments that define targets should declare them as .PHONY."""
        skip_names = {"custom-env.mk", "custom-task.mk"}
        violations: list[str] = []
        for bundle_name in bundle_names:
            bundle_dir = root / "bundles" / bundle_name
            if not bundle_dir.is_dir():
                continue
            for mk_file in _all_files_in_bundle(bundle_dir):
                if mk_file.suffix != ".mk" or mk_file.name in skip_names:
                    continue
                content = mk_file.read_text(encoding="utf-8")
                # If the file defines targets (has :: or : rules) it should have .PHONY
                has_targets = any(
                    line.strip().endswith("::")
                    or (": " in line and not line.startswith("\t") and not line.startswith("#"))
                    for line in content.splitlines()
                )
                if has_targets and ".PHONY" not in content:
                    rel = mk_file.relative_to(root / "bundles")
                    violations.append(f"  [{bundle_name}] {rel}")
        if violations:
            pytest.fail("Makefile fragments with targets but no .PHONY declaration:\n" + "\n".join(violations))


class TestLegalBundleContent:
    """Files in the legal bundle must have real, non-trivial content."""

    @pytest.fixture
    def legal_dir(self, root: Path) -> Path:
        """Return the legal bundle directory."""
        d = root / "bundles" / "legal"
        if not d.is_dir():
            pytest.skip("legal bundle not present")
        return d

    def test_license_file_has_content(self, legal_dir: Path) -> None:
        """LICENSE file must be non-empty and at least 100 bytes."""
        license_file = legal_dir / "LICENSE"
        assert license_file.exists(), "LICENSE not found in legal bundle"
        size = license_file.stat().st_size
        assert size >= 100, f"LICENSE is suspiciously small: {size} bytes"

    def test_security_md_has_content(self, legal_dir: Path) -> None:
        """SECURITY.md must mention reporting or vulnerability."""
        security_md = legal_dir / "SECURITY.md"
        assert security_md.exists(), "SECURITY.md not found in legal bundle"
        content = security_md.read_text(encoding="utf-8").lower()
        assert any(w in content for w in ("report", "vulnerabilit", "disclose")), (
            "SECURITY.md does not mention reporting/vulnerability/disclosure"
        )

    def test_code_of_conduct_has_content(self, legal_dir: Path) -> None:
        """CODE_OF_CONDUCT.md must exist and reference behaviour standards."""
        coc = legal_dir / ".rhiza" / "CODE_OF_CONDUCT.md"
        if not coc.exists():
            coc = legal_dir / "CODE_OF_CONDUCT.md"
        assert coc.exists(), "CODE_OF_CONDUCT.md not found in legal bundle"
        content = coc.read_text(encoding="utf-8").lower()
        assert len(content) >= 200, "CODE_OF_CONDUCT.md is suspiciously short"


class TestRenovateBundleContent:
    """renovate.json in the renovate bundle must be a valid, non-trivial config."""

    @pytest.fixture
    def renovate_json(self, root: Path) -> dict:
        """Load and return the parsed renovate.json from the renovate bundle."""
        rj = root / "bundles" / "renovate" / "renovate.json"
        if not rj.exists():
            pytest.skip("renovate bundle not present")
        with rj.open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_renovate_json_has_extends(self, renovate_json: dict) -> None:
        """renovate.json must have an 'extends' key (best practice for Renovate presets)."""
        assert "extends" in renovate_json, "renovate.json missing 'extends' key"
        assert isinstance(renovate_json["extends"], list), "'extends' must be a list"
        assert len(renovate_json["extends"]) > 0, "'extends' list is empty"

    def test_renovate_json_has_enabled_managers(self, renovate_json: dict) -> None:
        """renovate.json must declare enabledManagers covering all required dependency surfaces."""
        assert "enabledManagers" in renovate_json, (
            "renovate.json should declare 'enabledManagers' to scope what Renovate updates"
        )
        enabled = renovate_json["enabledManagers"]
        assert isinstance(enabled, list), "'enabledManagers' must be a list"
        required = {"pep621", "github-actions", "gitlabci"}
        missing = required - set(enabled)
        assert not missing, f"renovate.json 'enabledManagers' is missing required managers: {sorted(missing)}"


def _layer_precommit(root: Path, layer: str) -> dict:
    """Load the .pre-commit-config.yaml shipped by a language-layer bundle."""
    cfg = root / "bundles" / layer / ".pre-commit-config.yaml"
    assert cfg.is_file(), (
        f"layer '{layer}' ships no .pre-commit-config.yaml. Every language layer owns that "
        "path — pre-commit hard-codes it, which is why the layers are alternatives."
    )
    with cfg.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class TestLayerPreCommitConfig:
    """Every language layer's .pre-commit-config.yaml must pin node for npm-based hooks.

    markdownlint-cli pulls a transitive dependency (ava) whose engines field is
    ``^22.20 || ^24.12 || >=26``.  Odd-numbered current node releases such as v25
    fall in the gap between those bands, so ``npm install`` aborts with EBADENGINE
    and the hook fails to install.  Pinning ``default_language_version.node`` makes
    pre-commit provision a compatible node via nodeenv instead of relying on the
    system runtime.  This guard stops the pin from silently disappearing downstream.

    The config used to live in ``core`` and this guard read it from there; the
    language-layer split moved it into ``python-core`` and gave ``rust-core`` a
    sibling, so the check now runs once per layer — and asserts the file exists
    rather than skipping, which is how the earlier version went quietly dead.
    """

    @pytest.mark.parametrize("layer", _LAYER_BUNDLES)
    def test_default_language_version_pins_node(self, root: Path, layer: str) -> None:
        """default_language_version.node must be a non-empty pin so npm hooks get a compatible runtime."""
        versions = _layer_precommit(root, layer).get("default_language_version")
        assert isinstance(versions, dict), (
            f"{layer} .pre-commit-config.yaml must declare a 'default_language_version' table "
            "pinning node for npm-based hooks (markdownlint-cli)"
        )
        node = versions.get("node")
        assert isinstance(node, str), "'default_language_version.node' must be a version string"
        assert node.strip(), (
            "'default_language_version.node' must be a non-empty version string to keep markdownlint-cli "
            "installable on odd-numbered current node releases (EBADENGINE guard)"
        )

    def test_layers_agree_on_shared_hook_revisions(self, root: Path) -> None:
        """A repo shared by two layers must be pinned to one rev in both.

        The layers differ by design in *which* hooks they run — ruff/bandit versus
        rustfmt/clippy. The neutral half (markdownlint, actionlint, schema checks,
        secret scanning, the rhiza hooks) is the same set of upstream repos, and
        nothing keeps them in step: Renovate bumps each config file separately, so
        the two layers drift apart one PR at a time until a Rust project is running
        a year-old actionlint. This fails the moment they diverge.
        """
        revs: dict[str, dict[str, str]] = {}
        for layer in _LAYER_BUNDLES:
            for repo in _layer_precommit(root, layer)["repos"]:
                if repo["repo"] == "local":  # no rev to compare; recipes are language-specific
                    continue
                revs.setdefault(repo["repo"], {})[layer] = repo["rev"]

        drifted = {repo: pins for repo, pins in revs.items() if len(pins) > 1 and len(set(pins.values())) > 1}
        assert not drifted, "language layers pin the same pre-commit repo at different revs:\n" + "\n".join(
            f"  {repo}: " + ", ".join(f"{layer}={rev}" for layer, rev in sorted(pins.items()))
            for repo, pins in sorted(drifted.items())
        )


# ---------------------------------------------------------------------------
# GitLab CI uv-image single-source pinning
# ---------------------------------------------------------------------------


_UV_IMAGE_LITERAL = re.compile(r"ghcr\.io/astral-sh/uv:")
_IMAGE_LINE = re.compile(r"^\s*image:\s*(\S+)")


class TestDevcontainerBundleContent:
    """The devcontainer bundle must ship a coherent, runnable dev-container setup.

    Goes beyond the JSONC non-empty check in TestBundleJsonValidity: it parses
    devcontainer.json (stripping its // comments) and verifies the config actually
    wires up the bootstrap script, a pinned base image, and the non-root user the
    bundle promises — the behaviour a downstream repo relies on after syncing it.
    """

    @pytest.fixture
    def devcontainer_dir(self, root: Path) -> Path:
        """Return the .devcontainer directory inside the devcontainer bundle."""
        d = root / "bundles" / "devcontainer" / ".devcontainer"
        if not d.is_dir():
            pytest.skip("devcontainer bundle not present")
        return d

    @pytest.fixture
    def devcontainer_config(self, devcontainer_dir: Path) -> dict:
        """Parse devcontainer.json, stripping its full-line // comments (JSONC)."""
        raw = (devcontainer_dir / "devcontainer.json").read_text(encoding="utf-8")
        stripped = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("//"))
        return json.loads(stripped)

    def test_devcontainer_json_parses(self, devcontainer_config: dict) -> None:
        """devcontainer.json must parse to a named JSON object once comments are stripped."""
        assert isinstance(devcontainer_config, dict), "devcontainer.json must be a JSON object"
        assert devcontainer_config.get("name"), "devcontainer.json must declare a 'name'"

    def test_oncreate_points_to_existing_bootstrap(self, devcontainer_dir: Path, devcontainer_config: dict) -> None:
        """OnCreateCommand must reference a bootstrap script that actually ships in the bundle."""
        on_create = devcontainer_config.get("onCreateCommand")
        assert on_create == ".devcontainer/bootstrap.sh", (
            f"onCreateCommand should run the bundled bootstrap script, got {on_create!r}"
        )
        assert (devcontainer_dir / "bootstrap.sh").exists(), (
            "bootstrap.sh referenced by onCreateCommand is missing from the bundle"
        )

    def test_bootstrap_is_a_shell_script(self, devcontainer_dir: Path) -> None:
        """bootstrap.sh must be a real shell script: a shebang plus the dependency-install step."""
        content = (devcontainer_dir / "bootstrap.sh").read_text(encoding="utf-8")
        assert content.startswith("#!"), "bootstrap.sh must start with a shebang line"
        assert "make install" in content, "bootstrap.sh should install dependencies via 'make install'"

    def test_base_image_is_pinned_python(self, devcontainer_config: dict) -> None:
        """The container image must be a tag-pinned devcontainers Python image."""
        image = devcontainer_config.get("image", "")
        assert "devcontainers/python" in image, f"expected a devcontainers Python base image, got {image!r}"
        assert ":" in image.rsplit("/", 1)[-1], f"base image should pin a tag, got {image!r}"

    def test_remote_user_is_vscode(self, devcontainer_config: dict) -> None:
        """The container must run as the non-root 'vscode' user."""
        assert devcontainer_config.get("remoteUser") == "vscode", "devcontainer should run as the 'vscode' user"

    def test_overlay_ci_triggers_on_devcontainer_changes(self, root: Path) -> None:
        """The github-devcontainer overlay must rebuild the image when .devcontainer/** changes."""
        wf = root / "bundles" / "github-devcontainer" / ".github" / "workflows" / "rhiza_devcontainer.yml"
        if not wf.exists():
            pytest.skip("github-devcontainer overlay not present")
        content = wf.read_text(encoding="utf-8")
        assert ".devcontainer/**" in content, "devcontainer CI overlay should trigger on .devcontainer/** path changes"
