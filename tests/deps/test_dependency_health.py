"""Dependency health tests — validate pyproject.toml content."""

import tomllib


def _load_pyproject(root):
    """Load and return pyproject.toml content."""
    pyproject_path = root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with pyproject_path.open("rb") as f:
        return tomllib.load(f)


def test_pyproject_has_required_project_metadata(root):
    """Verify that pyproject.toml declares required basic project metadata."""
    pyproject = _load_pyproject(root)
    project = pyproject.get("project")
    assert isinstance(project, dict), "[project] section missing from pyproject.toml"

    required_fields = ["name", "version", "description", "readme", "requires-python"]
    missing = [field for field in required_fields if field not in project]
    assert not missing, f"Missing required [project] fields in pyproject.toml: {', '.join(missing)}"

    for field in required_fields:
        value = project[field]
        assert isinstance(value, str), f"[project].{field} must be a string"
        assert value.strip(), f"[project].{field} cannot be empty"


def test_pyproject_has_dependency_groups_section(root):
    """Verify that pyproject.toml defines [dependency-groups] as a table."""
    pyproject = _load_pyproject(root)
    groups = pyproject.get("dependency-groups")
    assert isinstance(groups, dict), "[dependency-groups] section missing from pyproject.toml"
