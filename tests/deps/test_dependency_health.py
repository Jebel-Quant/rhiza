"""Dependency health tests — validate pyproject.toml content."""

import tomllib

import pytest


def _load_pyproject(root):
    """Load and return pyproject.toml content."""
    pyproject_path = root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with pyproject_path.open("rb") as f:
        return tomllib.load(f)


# Required basic project metadata, one property per test (#1807): this was one C-rated function.
_REQUIRED_FIELDS = ["name", "description", "readme", "requires-python"]


@pytest.fixture
def project(root):
    """Return the ``[project]`` table of pyproject.toml, failing if it is missing."""
    project = _load_pyproject(root).get("project")
    assert isinstance(project, dict), "[project] section missing from pyproject.toml"
    return project


def _version_sources(project):
    """Return whether ``version`` is written as a non-empty string, and whether it is dynamic."""
    written = isinstance(project.get("version"), str) and project["version"].strip()
    derived = "version" in project.get("dynamic", [])
    return written, derived


def test_pyproject_has_required_project_metadata(project):
    """Verify that pyproject.toml declares required basic project metadata."""
    missing = [field for field in _REQUIRED_FIELDS if field not in project]
    assert not missing, f"Missing required [project] fields in pyproject.toml: {', '.join(missing)}"


@pytest.mark.parametrize("field", _REQUIRED_FIELDS)
def test_required_project_metadata_is_a_non_empty_string(project, field):
    """Each required metadata field holds a non-empty string."""
    value = project.get(field)
    assert isinstance(value, str), f"[project].{field} must be a string"
    assert value.strip(), f"[project].{field} cannot be empty"


def test_pyproject_declares_a_version(project):
    """Verify that pyproject.toml either writes ``version`` or lists it in ``dynamic``.

    ``version`` is required to be *declared*, not to be written: PEP 621 lets a project
    derive it from the VCS by listing it in ``dynamic``, which is what this repo does. This
    check listed it among the string fields until then, which is the same shape pytest-rhiza
    relaxed in its ``test_pyproject`` (pytest-rhiza#96) — a repo doing the right thing failed
    for having no number in the file.
    """
    written, derived = _version_sources(project)
    assert written or derived, (
        "[project] must either write `version` or list it in `dynamic` for the build backend to derive from the VCS"
    )


def test_pyproject_does_not_both_write_and_derive_the_version(project):
    """Verify that ``version`` is not both written and listed in ``dynamic``.

    Either source is acceptable on its own (see ``test_pyproject_declares_a_version`` and
    pytest-rhiza#96); declaring both leaves the build backend two answers to choose between.
    """
    written, derived = _version_sources(project)
    assert not (written and derived), "[project] cannot both write `version` and list it in `dynamic`"


def test_pyproject_has_dependency_groups_section(root):
    """Verify that pyproject.toml defines [dependency-groups] as a table."""
    pyproject = _load_pyproject(root)
    groups = pyproject.get("dependency-groups")
    assert isinstance(groups, dict), "[dependency-groups] section missing from pyproject.toml"
