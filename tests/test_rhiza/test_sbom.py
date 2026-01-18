"""Tests for SBOM (Software Bill of Materials) generation.

This file tests the SBOM generation functionality using Syft.
SBOM files provide supply chain transparency by listing all components
and dependencies in the software.

The workflow generates SBOM in multiple formats:
- SPDX JSON (https://spdx.dev/)
- CycloneDX JSON (https://cyclonedx.org/)
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

# Get absolute paths for executables to avoid S607 warnings
SHELL = shutil.which("sh") or "/bin/sh"
UVX = shutil.which("uvx") or "/usr/local/bin/uvx"


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary Python project for testing SBOM generation."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create a simple pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text("""[project]
name = "test-sbom-project"
version = "0.1.0"
description = "Test project for SBOM generation"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")

    # Create a simple source file
    src_dir = project_dir / "src" / "test_sbom_project"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('"""Test package."""\n__version__ = "0.1.0"\n')

    return project_dir


def test_sbom_generation_spdx(temp_project):
    """Test SBOM generation in SPDX JSON format."""
    output_file = temp_project / "sbom-test.spdx.json"

    # Generate SBOM using syft
    result = subprocess.run(
        [UVX, "syft", str(temp_project), "-o", f"spdx-json={output_file}"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Check command succeeded
    assert result.returncode == 0, f"SBOM generation failed: {result.stderr}"

    # Verify output file exists
    assert output_file.exists(), "SBOM file was not created"

    # Verify it's valid JSON
    with open(output_file) as f:
        sbom_data = json.load(f)

    # Verify SPDX structure
    assert "spdxVersion" in sbom_data, "Missing SPDX version field"
    assert "packages" in sbom_data, "Missing packages field"
    assert "SPDX" in sbom_data.get("spdxVersion", ""), "Not a valid SPDX document"

    # Verify packages were detected
    packages = sbom_data.get("packages", [])
    assert len(packages) > 0, "No packages detected in SBOM"


def test_sbom_generation_cyclonedx(temp_project):
    """Test SBOM generation in CycloneDX JSON format."""
    output_file = temp_project / "sbom-test.cyclonedx.json"

    # Generate SBOM using syft
    result = subprocess.run(
        [UVX, "syft", str(temp_project), "-o", f"cyclonedx-json={output_file}"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Check command succeeded
    assert result.returncode == 0, f"SBOM generation failed: {result.stderr}"

    # Verify output file exists
    assert output_file.exists(), "SBOM file was not created"

    # Verify it's valid JSON
    with open(output_file) as f:
        sbom_data = json.load(f)

    # Verify CycloneDX structure
    assert "bomFormat" in sbom_data, "Missing bomFormat field"
    assert sbom_data.get("bomFormat") == "CycloneDX", "Not a valid CycloneDX document"
    assert "components" in sbom_data, "Missing components field"

    # Verify components field is a list (can be empty)
    components = sbom_data.get("components", [])
    assert isinstance(components, list), "Components should be a list"


def test_sbom_contains_project_metadata(temp_project):
    """Test that SBOM contains project metadata."""
    output_file = temp_project / "sbom-metadata.spdx.json"

    # Generate SBOM
    result = subprocess.run(
        [UVX, "syft", str(temp_project), "-o", f"spdx-json={output_file}"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, f"SBOM generation failed: {result.stderr}"

    # Load and check metadata
    with open(output_file) as f:
        sbom_data = json.load(f)

    # Verify document has a name
    assert "name" in sbom_data, "Missing document name"

    # Verify creation timestamp
    assert "creationInfo" in sbom_data, "Missing creation info"


def test_sbom_on_actual_repo():
    """Test SBOM generation on the actual rhiza repository."""
    repo_root = Path(__file__).parent.parent.parent
    output_file = repo_root / "sbom-rhiza-test.spdx.json"

    try:
        # Generate SBOM for the actual repo
        result = subprocess.run(
            [UVX, "syft", str(repo_root), "-o", f"spdx-json={output_file}"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Check command succeeded
        assert result.returncode == 0, f"SBOM generation failed: {result.stderr}"

        # Verify output file exists
        assert output_file.exists(), "SBOM file was not created"

        # Verify it's valid JSON with packages
        with open(output_file) as f:
            sbom_data = json.load(f)

        assert "packages" in sbom_data, "Missing packages field"
        packages = sbom_data.get("packages", [])

        # The rhiza repo should have at least some packages detected
        # (from pyproject.toml dependencies)
        assert len(packages) > 0, f"Expected packages in SBOM, found {len(packages)}"

        # Print summary for manual verification
        print("\n✅ SBOM generated successfully!")
        print(f"📦 Total packages detected: {len(packages)}")
        print(f"📄 Output file: {output_file}")
        print(f"📏 File size: {output_file.stat().st_size} bytes")

    finally:
        # Clean up test file
        if output_file.exists():
            output_file.unlink()
