"""Tests for the .rhiza/requirements folder structure.

This test ensures that the requirements folder exists and contains the expected
requirement files for development dependencies.
"""

from pathlib import Path


class TestRequirementsFolder:
    """Tests for the .rhiza/requirements folder structure."""

    def test_requirements_folder_exists(self, root):
        """Requirements folder should exist in .rhiza directory."""
        requirements_dir = root / ".rhiza" / "requirements"
        assert requirements_dir.exists(), ".rhiza/requirements directory should exist"
        assert requirements_dir.is_dir(), ".rhiza/requirements should be a directory"

    def test_requirements_files_exist(self, root):
        """All expected requirements files should exist."""
        requirements_dir = root / ".rhiza" / "requirements"
        expected_files = [
            "tests.txt",
            "marimo.txt",
            "docs.txt",
            "tools.txt",
        ]
        for filename in expected_files:
            filepath = requirements_dir / filename
            assert filepath.exists(), f"{filename} should exist in requirements folder"
            assert filepath.is_file(), f"{filename} should be a file"

    def test_requirements_files_not_empty(self, root):
        """Requirements files should not be empty."""
        requirements_dir = root / ".rhiza" / "requirements"
        expected_files = [
            "tests.txt",
            "marimo.txt",
            "docs.txt",
            "tools.txt",
        ]
        for filename in expected_files:
            filepath = requirements_dir / filename
            content = filepath.read_text()
            # Filter out comments and empty lines
            lines = [
                line.strip()
                for line in content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            assert len(lines) > 0, f"{filename} should contain at least one dependency"

    def test_pyproject_has_no_dev_dependencies(self, root):
        """pyproject.toml should not have optional-dependencies section."""
        pyproject_path = root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml should exist"

        content = pyproject_path.read_text()
        assert (
            "[project.optional-dependencies]" not in content
        ), "pyproject.toml should not have [project.optional-dependencies] section"

    def test_marimo_not_in_main_dependencies(self, root):
        """marimo should not be in main dependencies of pyproject.toml."""
        pyproject_path = root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml should exist"

        content = pyproject_path.read_text()

        # Find the dependencies section
        in_dependencies = False
        for line in content.splitlines():
            if line.strip().startswith("dependencies = ["):
                in_dependencies = True
            elif in_dependencies and "]" in line:
                in_dependencies = False
            elif in_dependencies and "marimo" in line.lower():
                assert False, "marimo should not be in main dependencies"

    def test_readme_exists_in_requirements_folder(self, root):
        """README.md should exist in requirements folder."""
        readme_path = root / ".rhiza" / "requirements" / "README.md"
        assert readme_path.exists(), "README.md should exist in requirements folder"
        assert readme_path.is_file(), "README.md should be a file"
        content = readme_path.read_text()
        assert len(content) > 0, "README.md should not be empty"
