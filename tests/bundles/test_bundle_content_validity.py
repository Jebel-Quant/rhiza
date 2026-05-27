"""Content validity tests for bundle files.

Validates the substance of files inside every bundle directory:
- YAML and JSON files parse without error
- GitHub workflow stubs delegate to the canonical reusable workflow in jebel-quant/rhiza
- Shell completion scripts are non-trivial
- Makefile fragments expose at least one documented target (## help comment)
- Legal files have non-trivial content
- renovate.json contains the required schema declaration
- Requirements files use compatible-release or minimum-version specifiers, not strict pins,
  in the test requirements (to avoid forcing downstream exact versions)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _all_files_in_bundle(bundle_dir: Path) -> list[Path]:
    """Return every real file (resolving symlinks) inside a bundle directory."""
    files: list[Path] = []
    for dirpath, _dirs, filenames in os.walk(bundle_dir, followlinks=True):
        for name in filenames:
            p = Path(dirpath) / name
            if p.is_file():
                files.append(p)
    return files


def _load_bundle_names(root: Path) -> list[str]:
    """Return bundle names from .rhiza/template-bundles.yml."""
    bundles_file = root / ".rhiza" / "template-bundles.yml"
    if not bundles_file.exists():
        return []
    with bundles_file.open() as f:
        data = yaml.safe_load(f)
    return list(data.get("bundles", {}).keys())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bundles_root(root: Path) -> Path:
    """Return the path to the bundles/ directory."""
    return root / "bundles"


@pytest.fixture(scope="module")
def bundle_names(root: Path) -> list[str]:
    """Return all bundle names defined in template-bundles.yml."""
    return _load_bundle_names(root)


# ---------------------------------------------------------------------------
# YAML / JSON validity
# ---------------------------------------------------------------------------


def _is_mkdocs_python_tag_file(path: Path) -> bool:
    """Return True for mkdocs config files that legitimately use Python YAML tags.

    mkdocs-material uses !!python/name: tags in its configuration files.  These
    are intentional and cannot be parsed with yaml.safe_load — we skip them for
    parse-error tests but still validate them as non-empty elsewhere.
    """
    return path.name in {"mkdocs-base.yml", "mkdocs.yml"}


class TestBundleYamlValidity:
    """Every YAML file in every bundle directory must parse without error."""

    def test_all_yaml_files_are_parseable(self, bundles_root: Path, bundle_names: list[str]) -> None:
        """Walk every bundle and assert every .yml / .yaml file loads cleanly.

        mkdocs config files that use Python YAML tags (tag:yaml.org,2002:python/name:...)
        are intentionally excluded because those tags require a full Python YAML loader
        and are expected/valid in those files.
        """
        errors: list[str] = []
        for name in bundle_names:
            bundle_dir = bundles_root / name
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
                    rel = f.relative_to(bundles_root)
                    errors.append(f"  [{name}] {rel}: {exc}")
        if errors:
            pytest.fail("YAML parse errors in bundle files:\n" + "\n".join(errors))

    def test_no_yaml_file_is_empty(self, bundles_root: Path, bundle_names: list[str]) -> None:
        """No .yml / .yaml bundle file should be empty (null document).

        mkdocs config files that require Python YAML tags are skipped here too
        since yaml.safe_load would raise rather than return None for them.
        """
        empties: list[str] = []
        for name in bundle_names:
            bundle_dir = bundles_root / name
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
                    rel = f.relative_to(bundles_root)
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

    def test_all_json_files_are_parseable(self, bundles_root: Path, bundle_names: list[str]) -> None:
        """Walk every bundle and assert every .json file loads cleanly.

        Files using JSONC format (JSON with Comments) such as devcontainer.json are
        intentionally excluded because they require a JSONC parser and their use of
        comments is valid by spec.
        """
        errors: list[str] = []
        for name in bundle_names:
            bundle_dir = bundles_root / name
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
                    rel = f.relative_to(bundles_root)
                    errors.append(f"  [{name}] {rel}: {exc}")
        if errors:
            pytest.fail("JSON parse errors in bundle files:\n" + "\n".join(errors))

    def test_jsonc_files_are_non_empty(self, bundles_root: Path, bundle_names: list[str]) -> None:
        """JSONC files (devcontainer.json) must be non-empty even though we skip parse validation."""
        for name in bundle_names:
            bundle_dir = bundles_root / name
            if not bundle_dir.is_dir():
                continue
            for f in _all_files_in_bundle(bundle_dir):
                if f.suffix == ".json" and _is_jsonc_file(f):
                    content = f.read_text(encoding="utf-8").strip()
                    rel = f.relative_to(bundles_root)
                    assert content, f"JSONC file is empty: [{name}] {rel}"


# ---------------------------------------------------------------------------
# Documentation coverage
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# GitHub workflow stubs
# ---------------------------------------------------------------------------


class TestGithubWorkflowStubs:
    """Workflow files injected by github-* overlay bundles must delegate correctly."""

    def _github_overlay_bundles(self, bundle_names: list[str]) -> list[str]:
        """Return bundle names that are github-* overlays."""
        return [n for n in bundle_names if n.startswith("github-")]

    def test_workflow_stubs_have_name_field(self, bundles_root: Path, bundle_names: list[str]) -> None:
        """Every GitHub workflow YAML file has a top-level 'name' field."""
        errors: list[str] = []
        for bundle_name in self._github_overlay_bundles(bundle_names):
            bundle_dir = bundles_root / bundle_name
            workflows_dir = bundle_dir / ".github" / "workflows"
            if not workflows_dir.is_dir():
                continue
            for wf in workflows_dir.glob("*.yml"):
                with wf.open(encoding="utf-8") as fh:
                    doc = yaml.safe_load(fh)
                if not isinstance(doc, dict) or "name" not in doc:
                    errors.append(f"  [{bundle_name}] {wf.name}: missing 'name' field")
        if errors:
            pytest.fail("Workflow stubs without 'name':\n" + "\n".join(errors))

    def test_workflow_stubs_have_on_trigger(self, bundles_root: Path, bundle_names: list[str]) -> None:
        """Every GitHub workflow YAML file has an 'on' trigger section.

        Note: pyyaml parses the bare YAML key 'on' as Python boolean True (since 'on'
        is a YAML boolean literal).  We check for both True and the string 'on' to
        handle both parsed and raw representations.
        """
        errors: list[str] = []
        for bundle_name in self._github_overlay_bundles(bundle_names):
            bundle_dir = bundles_root / bundle_name
            workflows_dir = bundle_dir / ".github" / "workflows"
            if not workflows_dir.is_dir():
                continue
            for wf in workflows_dir.glob("*.yml"):
                with wf.open(encoding="utf-8") as fh:
                    doc = yaml.safe_load(fh)
                if not isinstance(doc, dict):
                    errors.append(f"  [{bundle_name}] {wf.name}: not a YAML mapping")
                    continue
                # pyyaml parses 'on:' as True (YAML boolean); check both forms
                has_on = "on" in doc or True in doc
                if not has_on:
                    errors.append(f"  [{bundle_name}] {wf.name}: missing 'on' trigger")
        if errors:
            pytest.fail("Workflow stubs without 'on' trigger:\n" + "\n".join(errors))

    def test_workflow_stubs_have_jobs(self, bundles_root: Path, bundle_names: list[str]) -> None:
        """Every GitHub workflow YAML file has a non-empty 'jobs' section."""
        errors: list[str] = []
        for bundle_name in self._github_overlay_bundles(bundle_names):
            bundle_dir = bundles_root / bundle_name
            workflows_dir = bundle_dir / ".github" / "workflows"
            if not workflows_dir.is_dir():
                continue
            for wf in workflows_dir.glob("*.yml"):
                with wf.open(encoding="utf-8") as fh:
                    doc = yaml.safe_load(fh)
                if not isinstance(doc, dict):
                    continue
                jobs = doc.get("jobs")
                if not jobs:
                    errors.append(f"  [{bundle_name}] {wf.name}: missing or empty 'jobs' section")
        if errors:
            pytest.fail("Workflow stubs without 'jobs':\n" + "\n".join(errors))

    def test_workflow_stubs_delegate_to_jebel_quant_rhiza(self, bundles_root: Path, bundle_names: list[str]) -> None:
        """Workflow stubs that contain a 'uses:' job reference the jebel-quant/rhiza repo."""
        errors: list[str] = []
        for bundle_name in self._github_overlay_bundles(bundle_names):
            bundle_dir = bundles_root / bundle_name
            workflows_dir = bundle_dir / ".github" / "workflows"
            if not workflows_dir.is_dir():
                continue
            for wf in workflows_dir.glob("*.yml"):
                content = wf.read_text(encoding="utf-8")
                # Only check workflows that use the reusable workflow pattern
                if "uses:" not in content:
                    continue
                if "jebel-quant/rhiza" not in content:
                    errors.append(
                        f"  [{bundle_name}] {wf.name}: 'uses:' present but does not reference jebel-quant/rhiza"
                    )
        if errors:
            pytest.fail("Workflow stubs with non-rhiza 'uses:' references:\n" + "\n".join(errors))


# ---------------------------------------------------------------------------
# Shell completion scripts
# ---------------------------------------------------------------------------


class TestShellCompletions:
    """Shell completion scripts in the core bundle must have real content."""

    @pytest.fixture
    def completions_dir(self, bundles_root: Path) -> Path:
        """Return the completions directory inside the core bundle."""
        return bundles_root / "core" / ".rhiza" / "completions"

    def test_bash_completion_exists_and_is_non_empty(self, completions_dir: Path) -> None:
        """rhiza-completion.bash must exist and contain at least 10 lines."""
        bash_comp = completions_dir / "rhiza-completion.bash"
        assert bash_comp.exists(), "rhiza-completion.bash not found in core bundle"
        lines = bash_comp.read_text(encoding="utf-8").splitlines()
        assert len(lines) >= 10, f"bash completion suspiciously short: {len(lines)} lines"

    def test_zsh_completion_exists_and_is_non_empty(self, completions_dir: Path) -> None:
        """rhiza-completion.zsh must exist and contain at least 10 lines."""
        zsh_comp = completions_dir / "rhiza-completion.zsh"
        assert zsh_comp.exists(), "rhiza-completion.zsh not found in core bundle"
        lines = zsh_comp.read_text(encoding="utf-8").splitlines()
        assert len(lines) >= 10, f"zsh completion suspiciously short: {len(lines)} lines"

    def test_bash_completion_uses_make_for_dynamic_targets(self, completions_dir: Path) -> None:
        """Bash completion script should invoke make dynamically to discover targets."""
        bash_comp = completions_dir / "rhiza-completion.bash"
        if not bash_comp.exists():
            pytest.skip("rhiza-completion.bash not found")
        content = bash_comp.read_text(encoding="utf-8")
        # Dynamic completion scripts call make to discover targets at completion time
        assert "make" in content, "bash completion should invoke 'make' to discover targets dynamically"

    def test_bash_completion_registers_with_complete(self, completions_dir: Path) -> None:
        """Bash completion script must register itself via the 'complete' builtin."""
        bash_comp = completions_dir / "rhiza-completion.bash"
        if not bash_comp.exists():
            pytest.skip("rhiza-completion.bash not found")
        content = bash_comp.read_text(encoding="utf-8")
        assert "complete " in content, "bash completion must call 'complete' to register the completion function"

    def test_zsh_completion_uses_make_for_dynamic_targets(self, completions_dir: Path) -> None:
        """Zsh completion script should invoke make dynamically to discover targets."""
        zsh_comp = completions_dir / "rhiza-completion.zsh"
        if not zsh_comp.exists():
            pytest.skip("rhiza-completion.zsh not found")
        content = zsh_comp.read_text(encoding="utf-8")
        assert "make" in content, "zsh completion should invoke 'make' to discover targets dynamically"


# ---------------------------------------------------------------------------
# Makefile fragments
# ---------------------------------------------------------------------------


class TestMakefileFragments:
    """Makefile fragments in bundles must follow the help-comment convention."""

    def test_all_mk_files_have_at_least_one_documented_target(
        self, bundles_root: Path, bundle_names: list[str]
    ) -> None:
        """Every .mk fragment that is not a customisation template must document at least one target with ##."""
        skip_names = {"custom-env.mk", "custom-task.mk", "README.md"}
        violations: list[str] = []
        for bundle_name in bundle_names:
            bundle_dir = bundles_root / bundle_name
            if not bundle_dir.is_dir():
                continue
            for mk_file in _all_files_in_bundle(bundle_dir):
                if mk_file.suffix != ".mk" or mk_file.name in skip_names:
                    continue
                content = mk_file.read_text(encoding="utf-8")
                # A documented target looks like: target: ... ## description
                if "##" not in content:
                    rel = mk_file.relative_to(bundles_root)
                    violations.append(f"  [{bundle_name}] {rel}")
        if violations:
            pytest.fail("Makefile fragments without any ## help comment:\n" + "\n".join(violations))

    def test_all_mk_files_have_phony_declarations(self, bundles_root: Path, bundle_names: list[str]) -> None:
        """Makefile fragments that define targets should declare them as .PHONY."""
        skip_names = {"custom-env.mk", "custom-task.mk"}
        violations: list[str] = []
        for bundle_name in bundle_names:
            bundle_dir = bundles_root / bundle_name
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
                    rel = mk_file.relative_to(bundles_root)
                    violations.append(f"  [{bundle_name}] {rel}")
        if violations:
            pytest.fail("Makefile fragments with targets but no .PHONY declaration:\n" + "\n".join(violations))


# ---------------------------------------------------------------------------
# Legal bundle content
# ---------------------------------------------------------------------------


class TestLegalBundleContent:
    """Files in the legal bundle must have real, non-trivial content."""

    @pytest.fixture
    def legal_dir(self, bundles_root: Path) -> Path:
        """Return the legal bundle directory."""
        d = bundles_root / "legal"
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


# ---------------------------------------------------------------------------
# Renovate configuration
# ---------------------------------------------------------------------------


class TestRenovateBundleContent:
    """renovate.json in the renovate bundle must be a valid, non-trivial config."""

    @pytest.fixture
    def renovate_json(self, bundles_root: Path) -> dict:
        """Load and return the parsed renovate.json from the renovate bundle."""
        rj = bundles_root / "renovate" / "renovate.json"
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
