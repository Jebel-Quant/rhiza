"""Dependency health tests — validate pyproject.toml content."""

import tomllib


def _load_pyproject(root):
    """Load and return pyproject.toml content."""
    pyproject_path = root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with pyproject_path.open("rb") as f:
        return tomllib.load(f)


def test_pyproject_has_required_project_metadata(root):
    """Verify that pyproject.toml declares required basic project metadata.

    ``version`` is required to be *declared*, not to be written: PEP 621 lets a project
    derive it from the VCS by listing it in ``dynamic``, which is what this repo does. This
    check listed it among the string fields until then, which is the same shape pytest-rhiza
    relaxed in its ``test_pyproject`` (pytest-rhiza#96) — a repo doing the right thing failed
    for having no number in the file.
    """
    pyproject = _load_pyproject(root)
    project = pyproject.get("project")
    assert isinstance(project, dict), "[project] section missing from pyproject.toml"

    required_fields = ["name", "description", "readme", "requires-python"]
    missing = [field for field in required_fields if field not in project]
    assert not missing, f"Missing required [project] fields in pyproject.toml: {', '.join(missing)}"

    for field in required_fields:
        value = project[field]
        assert isinstance(value, str), f"[project].{field} must be a string"
        assert value.strip(), f"[project].{field} cannot be empty"

    written = isinstance(project.get("version"), str) and project["version"].strip()
    derived = "version" in project.get("dynamic", [])
    assert written or derived, (
        "[project] must either write `version` or list it in `dynamic` for the build backend to derive from the VCS"
    )
    assert not (written and derived), "[project] cannot both write `version` and list it in `dynamic`"


def test_pyproject_has_dependency_groups_section(root):
    """Verify that pyproject.toml defines [dependency-groups] as a table."""
    pyproject = _load_pyproject(root)
    groups = pyproject.get("dependency-groups")
    assert isinstance(groups, dict), "[dependency-groups] section missing from pyproject.toml"
