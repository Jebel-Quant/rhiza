"""Tests for the template bundles configuration file.

This file validates the structure and consistency of .rhiza/template-bundles.yml,
ensuring all bundle definitions are properly formatted and reference existing files.
"""

from __future__ import annotations

import pytest
import yaml


@pytest.fixture
def template_bundles_path(root):
    """Return path to template-bundles.yml."""
    return root / ".rhiza" / "template-bundles.yml"


@pytest.fixture
def template_bundles(template_bundles_path):
    """Load and return template bundles configuration."""
    with open(template_bundles_path) as f:
        return yaml.safe_load(f)


class TestTemplateBundlesStructure:
    """Tests for template bundles YAML structure."""

    def test_template_bundles_file_exists(self, template_bundles_path):
        """Template bundles configuration file should exist."""
        assert template_bundles_path.exists()

    def test_template_bundles_is_valid_yaml(self, template_bundles_path):
        """Template bundles file should be valid YAML."""
        with open(template_bundles_path) as f:
            data = yaml.safe_load(f)
            assert data is not None

    def test_has_version_field(self, template_bundles):
        """Template bundles should have a version field."""
        assert "version" in template_bundles
        assert isinstance(template_bundles["version"], str)

    def test_has_bundles_section(self, template_bundles):
        """Template bundles should have a bundles section."""
        assert "bundles" in template_bundles
        assert isinstance(template_bundles["bundles"], dict)

    def test_has_metadata_section(self, template_bundles):
        """Template bundles should have a metadata section."""
        assert "metadata" in template_bundles
        assert isinstance(template_bundles["metadata"], dict)


class TestTemplateBundleDefinitions:
    """Tests for individual bundle definitions."""

    def test_all_bundles_have_required_fields(self, template_bundles):
        """Each bundle should have required fields."""
        bundles = template_bundles.get("bundles", {})
        required_fields = {"description", "files"}

        for bundle_name, bundle_config in bundles.items():
            assert isinstance(bundle_config, dict), f"Bundle {bundle_name} should be a dict"
            for field in required_fields:
                assert field in bundle_config, f"Bundle {bundle_name} missing {field}"

    def test_bundle_descriptions_are_strings(self, template_bundles):
        """Bundle descriptions should be strings."""
        bundles = template_bundles.get("bundles", {})
        for bundle_name, bundle_config in bundles.items():
            assert isinstance(bundle_config["description"], str), f"Bundle {bundle_name} description should be a string"

    def test_bundle_files_are_lists(self, template_bundles):
        """Bundle files should be lists."""
        bundles = template_bundles.get("bundles", {})
        for bundle_name, bundle_config in bundles.items():
            assert isinstance(bundle_config["files"], list), f"Bundle {bundle_name} files should be a list"

    def test_core_bundle_is_marked_required(self, template_bundles):
        """Core bundle should be marked as required."""
        bundles = template_bundles.get("bundles", {})
        assert "core" in bundles
        assert bundles["core"].get("required") is True

    def test_book_bundle_has_dependencies(self, template_bundles):
        """Book bundle should declare its dependency on tests."""
        bundles = template_bundles.get("bundles", {})
        assert "book" in bundles
        book_bundle = bundles["book"]
        assert "requires" in book_bundle
        assert "tests" in book_bundle["requires"]

    def test_dependency_bundles_exist(self, template_bundles):
        """All bundles referenced in requires/recommends should exist."""
        bundles = template_bundles.get("bundles", {})
        bundle_names = set(bundles.keys())

        for bundle_name, bundle_config in bundles.items():
            # Check required dependencies
            if "requires" in bundle_config:
                for dep in bundle_config["requires"]:
                    assert dep in bundle_names, f"Bundle {bundle_name} requires non-existent bundle {dep}"

            # Check recommended dependencies
            if "recommends" in bundle_config:
                for dep in bundle_config["recommends"]:
                    assert dep in bundle_names, f"Bundle {bundle_name} recommends non-existent bundle {dep}"


class TestExpectedBundles:
    """Tests that expected bundles are defined."""

    EXPECTED_BUNDLES = {
        "core",
        "legal",
        "tests",
        "benchmarks",
        "docker",
        "marimo",
        "book",
        "devcontainer",
        "gitlab",
        "presentation",
    }

    def test_expected_bundles_are_defined(self, template_bundles):
        """All expected bundles should be defined."""
        bundles = template_bundles.get("bundles", {})
        bundle_names = set(bundles.keys())

        for expected_bundle in self.EXPECTED_BUNDLES:
            assert expected_bundle in bundle_names, f"Expected bundle {expected_bundle} not found"

    def test_metadata_counts_match_bundles(self, template_bundles):
        """Metadata total_bundles should match actual bundle count."""
        bundles = template_bundles.get("bundles", {})
        metadata = template_bundles.get("metadata", {})

        if "total_bundles" in metadata:
            assert metadata["total_bundles"] == len(bundles), "Metadata total_bundles doesn't match actual bundle count"


class TestExamplesSection:
    """Tests for the examples section."""

    def test_has_examples_section(self, template_bundles):
        """Template bundles should have an examples section."""
        assert "examples" in template_bundles
        assert isinstance(template_bundles["examples"], dict)

    def test_examples_reference_valid_bundles(self, template_bundles):
        """Example configurations should only reference valid bundles."""
        bundles = template_bundles.get("bundles", {})
        bundle_names = set(bundles.keys())
        examples = template_bundles.get("examples", {})

        for example_name, example_config in examples.items():
            if "templates" in example_config:
                for template in example_config["templates"]:
                    # core is auto-included, so we don't check it
                    if template != "core":
                        assert template in bundle_names, (
                            f"Example {example_name} references non-existent bundle {template}"
                        )
