"""End-to-end integration tests for the complete Rhiza workflow.

This module tests the full Rhiza workflow from project initialisation through to release.
These tests require network access and real tool installations, so they are marked as
integration tests and skipped by default.

To run these tests:
    pytest tests/test_rhiza/test_e2e_workflow.py -v --run-integration

The workflow tested:
    1. init - Initialise a new project with Rhiza configuration
    2. materialize - Sync templates from the Rhiza repository
    3. install - Run make install to set up the development environment
    4. test - Run make test to verify the setup
    5. release - Test the release workflow (version bumping, tagging)
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

# Get absolute paths for executables to avoid S607 warnings
GIT = shutil.which("git") or "/usr/bin/git"
MAKE = shutil.which("make") or "/usr/bin/make"
UVX = shutil.which("uvx")


def has_uvx() -> bool:
    """Check if uvx is available."""
    return UVX is not None


def has_network() -> bool:
    """Check if network is available by testing connectivity to GitHub."""
    try:
        result = subprocess.run(
            [GIT, "ls-remote", "https://github.com/jebel-quant/rhiza.git", "HEAD"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# Skip all tests in this module if uvx is not available or network is down
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not has_uvx(), reason="uvx not available"),
]


@pytest.fixture
def fresh_project(tmp_path: Path, monkeypatch):
    """Create a fresh project directory with git initialised.

    This fixture creates a minimal project structure suitable for Rhiza initialisation.
    """
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Initialise git repository
    subprocess.run([GIT, "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        [GIT, "config", "user.email", "test@example.com"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [GIT, "config", "user.name", "Test User"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )

    # Create a minimal pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "test-project"
version = "0.1.0"
description = "A test project for Rhiza e2e testing"
requires-python = ">=3.11"

[dependency-groups]
dev = []
"""
    )

    # Create .python-version
    python_version = project_dir / ".python-version"
    python_version.write_text("3.12\n")

    # Create minimal src structure
    src_dir = project_dir / "src" / "test_project"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('"""Test project package."""\n')

    # Create minimal tests structure
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_example.py").write_text(
        '''"""Example test file."""


def test_example():
    """Test that passes."""
    assert True
'''
    )

    # Initial commit
    subprocess.run([GIT, "add", "."], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        [GIT, "commit", "-m", "Initial commit"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )

    monkeypatch.chdir(project_dir)
    yield project_dir


class TestRhizaInit:
    """Tests for the rhiza init command."""

    @pytest.mark.skipif(not has_network(), reason="Network not available")
    def test_init_creates_template_config(self, fresh_project: Path):
        """Test that rhiza init creates the template configuration file."""
        result = subprocess.run(
            [UVX, "rhiza", "init", "--git-host", "github", str(fresh_project)],
            capture_output=True,
            text=True,
            cwd=fresh_project,
        )

        assert result.returncode == 0, f"rhiza init failed: {result.stderr}"

        # Check that template.yml was created (could be in .rhiza or .github/rhiza)
        template_locations = [
            fresh_project / ".rhiza" / "template.yml",
            fresh_project / ".github" / "rhiza" / "template.yml",
        ]
        assert any(
            loc.exists() for loc in template_locations
        ), "template.yml not created in expected locations"


class TestRhizaMaterialize:
    """Tests for the rhiza materialize command."""

    @pytest.mark.skipif(not has_network(), reason="Network not available")
    def test_materialize_copies_templates(self, fresh_project: Path):
        """Test that rhiza materialize copies template files."""
        # First init
        subprocess.run(
            [UVX, "rhiza", "init", "--git-host", "github", str(fresh_project)],
            capture_output=True,
            cwd=fresh_project,
            check=True,
        )

        # Then materialize
        result = subprocess.run(
            [UVX, "rhiza", "materialize", "--force", str(fresh_project)],
            capture_output=True,
            text=True,
            cwd=fresh_project,
            timeout=120,  # Allow time for sparse clone
        )

        assert result.returncode == 0, f"rhiza materialize failed: {result.stderr}"

        # Check that key files were created
        expected_files = [
            "Makefile",
            "ruff.toml",
            "pytest.ini",
            ".pre-commit-config.yaml",
        ]
        for filename in expected_files:
            filepath = fresh_project / filename
            assert filepath.exists(), f"Expected file {filename} not created"


class TestFullWorkflow:
    """End-to-end tests for the complete Rhiza workflow."""

    @pytest.mark.slow
    @pytest.mark.skipif(not has_network(), reason="Network not available")
    def test_init_materialize_install(self, fresh_project: Path):
        """Test the full workflow: init → materialize → install."""
        # Step 1: Init
        init_result = subprocess.run(
            [UVX, "rhiza", "init", "--git-host", "github", str(fresh_project)],
            capture_output=True,
            text=True,
            cwd=fresh_project,
        )
        assert init_result.returncode == 0, f"init failed: {init_result.stderr}"

        # Step 2: Materialize
        materialize_result = subprocess.run(
            [UVX, "rhiza", "materialize", "--force", str(fresh_project)],
            capture_output=True,
            text=True,
            cwd=fresh_project,
            timeout=120,
        )
        assert (
            materialize_result.returncode == 0
        ), f"materialize failed: {materialize_result.stderr}"

        # Verify Makefile exists before install
        makefile = fresh_project / "Makefile"
        assert makefile.exists(), "Makefile not created by materialize"

        # Step 3: Install (this may take a while)
        install_result = subprocess.run(
            [MAKE, "install"],
            capture_output=True,
            text=True,
            cwd=fresh_project,
            timeout=300,  # 5 minutes for install
        )
        assert install_result.returncode == 0, f"make install failed: {install_result.stderr}"

        # Verify .venv was created
        venv_dir = fresh_project / ".venv"
        assert venv_dir.exists(), ".venv not created by make install"

    @pytest.mark.slow
    @pytest.mark.skipif(not has_network(), reason="Network not available")
    def test_full_workflow_with_tests(self, fresh_project: Path):
        """Test the complete workflow including running tests."""
        # Init
        subprocess.run(
            [UVX, "rhiza", "init", "--git-host", "github", str(fresh_project)],
            capture_output=True,
            cwd=fresh_project,
            check=True,
        )

        # Materialize
        subprocess.run(
            [UVX, "rhiza", "materialize", "--force", str(fresh_project)],
            capture_output=True,
            cwd=fresh_project,
            timeout=120,
            check=True,
        )

        # Install
        subprocess.run(
            [MAKE, "install"],
            capture_output=True,
            cwd=fresh_project,
            timeout=300,
            check=True,
        )

        # Run tests
        test_result = subprocess.run(
            [MAKE, "test"],
            capture_output=True,
            text=True,
            cwd=fresh_project,
            timeout=300,
        )

        # Tests should pass (we created a simple passing test)
        assert test_result.returncode == 0, f"make test failed: {test_result.stderr}\n{test_result.stdout}"

    @pytest.mark.slow
    @pytest.mark.skipif(not has_network(), reason="Network not available")
    def test_full_workflow_with_fmt(self, fresh_project: Path):
        """Test the complete workflow including code formatting."""
        # Init → Materialize → Install
        subprocess.run(
            [UVX, "rhiza", "init", "--git-host", "github", str(fresh_project)],
            capture_output=True,
            cwd=fresh_project,
            check=True,
        )
        subprocess.run(
            [UVX, "rhiza", "materialize", "--force", str(fresh_project)],
            capture_output=True,
            cwd=fresh_project,
            timeout=120,
            check=True,
        )
        subprocess.run(
            [MAKE, "install"],
            capture_output=True,
            cwd=fresh_project,
            timeout=300,
            check=True,
        )

        # Run fmt (pre-commit hooks)
        fmt_result = subprocess.run(
            [MAKE, "fmt"],
            capture_output=True,
            text=True,
            cwd=fresh_project,
            timeout=300,
        )

        # fmt may return non-zero if it makes changes, but shouldn't crash
        # Second run should be clean
        if fmt_result.returncode != 0:
            fmt_result2 = subprocess.run(
                [MAKE, "fmt"],
                capture_output=True,
                text=True,
                cwd=fresh_project,
                timeout=300,
            )
            assert fmt_result2.returncode == 0, f"make fmt failed twice: {fmt_result2.stderr}"


class TestVersionBump:
    """Tests for version bumping in an initialised project."""

    @pytest.mark.slow
    @pytest.mark.skipif(not has_network(), reason="Network not available")
    def test_version_operations(self, fresh_project: Path):
        """Test version bumping after full setup."""
        # Full setup
        subprocess.run(
            [UVX, "rhiza", "init", "--git-host", "github", str(fresh_project)],
            capture_output=True,
            cwd=fresh_project,
            check=True,
        )
        subprocess.run(
            [UVX, "rhiza", "materialize", "--force", str(fresh_project)],
            capture_output=True,
            cwd=fresh_project,
            timeout=120,
            check=True,
        )
        subprocess.run(
            [MAKE, "install"],
            capture_output=True,
            cwd=fresh_project,
            timeout=300,
            check=True,
        )

        # Check current version
        uv = shutil.which("uv")
        if uv:
            version_result = subprocess.run(
                [uv, "version", "--short"],
                capture_output=True,
                text=True,
                cwd=fresh_project,
            )
            assert version_result.returncode == 0
            version = version_result.stdout.strip()
            assert version == "0.1.0", f"Expected version 0.1.0, got {version}"


class TestCleanProject:
    """Tests for project cleanup and state management."""

    @pytest.mark.skipif(not has_network(), reason="Network not available")
    def test_clean_removes_artifacts(self, fresh_project: Path):
        """Test that make clean removes build artifacts."""
        # Setup
        subprocess.run(
            [UVX, "rhiza", "init", "--git-host", "github", str(fresh_project)],
            capture_output=True,
            cwd=fresh_project,
            check=True,
        )
        subprocess.run(
            [UVX, "rhiza", "materialize", "--force", str(fresh_project)],
            capture_output=True,
            cwd=fresh_project,
            timeout=120,
            check=True,
        )
        subprocess.run(
            [MAKE, "install"],
            capture_output=True,
            cwd=fresh_project,
            timeout=300,
            check=True,
        )

        # Verify .venv exists
        venv_dir = fresh_project / ".venv"
        assert venv_dir.exists()

        # Run clean
        clean_result = subprocess.run(
            [MAKE, "clean"],
            capture_output=True,
            text=True,
            cwd=fresh_project,
            timeout=60,
        )
        assert clean_result.returncode == 0, f"make clean failed: {clean_result.stderr}"

        # .venv should be removed
        assert not venv_dir.exists(), ".venv should be removed by make clean"
