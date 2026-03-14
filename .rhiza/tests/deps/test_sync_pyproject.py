"""Tests for .rhiza/utils/sync_pyproject.py.

This file and its associated tests flow down via a SYNC action from the
jebel-quant/rhiza repository (https://github.com/jebel-quant/rhiza).

Verifies that sync_pyproject.py:
- Exists and has valid Python syntax
- Is a no-op when no ``pyproject:`` section is present in template.yml
- Correctly patches ``requires-python`` when specified
- Correctly replaces ``classifiers`` when specified
- Leaves ``name``, ``version``, ``description``, ``dependencies`` untouched
- ``--dry-run`` does not modify the file
- ``--check`` exits non-zero when changes would be made

Security Notes:
- S101 (assert usage): Asserts are appropriate in test code for validating conditions
"""

from __future__ import annotations

import ast
import importlib.util
import textwrap
import tomllib
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SCRIPT_PATH = Path(__file__).parent.parent.parent / "utils" / "sync_pyproject.py"

_MINIMAL_PYPROJECT = textwrap.dedent("""\
    [project]
    name = "my-project"
    version = "1.2.3"
    description = "A test project"
    requires-python = ">=3.10"
    dependencies = ["requests>=2.0"]

    [dependency-groups]
    dev = ["pytest"]
""")

_TEMPLATE_NO_PYPROJECT = textwrap.dedent("""\
    repository: Jebel-Quant/rhiza
    ref: v0.9.0
    templates:
      - core
""")

_TEMPLATE_WITH_REQUIRES_PYTHON = textwrap.dedent("""\
    repository: Jebel-Quant/rhiza
    ref: v0.9.0
    templates:
      - core
    pyproject:
      requires-python: ">=3.11"
""")

_TEMPLATE_WITH_CLASSIFIERS = textwrap.dedent("""\
    repository: Jebel-Quant/rhiza
    ref: v0.9.0
    templates:
      - core
    pyproject:
      classifiers:
        - "Programming Language :: Python :: 3"
        - "Programming Language :: Python :: 3.11"
""")

_TEMPLATE_WITH_BOTH = textwrap.dedent("""\
    repository: Jebel-Quant/rhiza
    ref: v0.9.0
    templates:
      - core
    pyproject:
      requires-python: ">=3.12"
      classifiers:
        - "Programming Language :: Python :: 3"
        - "Programming Language :: Python :: 3.12"
""")

_TEMPLATE_WITH_LICENSE_STRING = textwrap.dedent("""\
    repository: Jebel-Quant/rhiza
    ref: v0.9.0
    templates:
      - core
    pyproject:
      license: "MIT"
""")

_TEMPLATE_WITH_LICENSE_TABLE = textwrap.dedent("""\
    repository: Jebel-Quant/rhiza
    ref: v0.9.0
    templates:
      - core
    pyproject:
      license:
        text: "MIT"
""")

_TEMPLATE_WITH_README = textwrap.dedent("""\
    repository: Jebel-Quant/rhiza
    ref: v0.9.0
    templates:
      - core
    pyproject:
      readme: "README.md"
""")


def _make_project(tmp_path: Path, pyproject_content: str, template_content: str) -> Path:
    """Create a minimal fake project directory for testing."""
    # Simulate <project>/.rhiza/utils/sync_pyproject.py layout
    (tmp_path / ".rhiza" / "utils").mkdir(parents=True)
    (tmp_path / ".rhiza" / "template.yml").write_text(template_content, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # Place a copy of the real script so imports work from the fake project root
    real_script = SCRIPT_PATH.read_text(encoding="utf-8")
    (tmp_path / ".rhiza" / "utils" / "sync_pyproject.py").write_text(real_script, encoding="utf-8")

    return tmp_path


def _run_sync(tmp_path: Path, argv: list[str] | None = None) -> int:
    """Import and run sync_pyproject.main() in the context of *tmp_path*."""
    script = tmp_path / ".rhiza" / "utils" / "sync_pyproject.py"
    spec = importlib.util.spec_from_file_location("sync_pyproject_test", script)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None

    # We need to monkey-patch the module's Path(__file__) lookup.
    # The easiest way: temporarily chdir into tmp_path so relative resolution
    # works, BUT sync_pyproject uses resolve(), so we patch __file__ directly.
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    # Patch _resolve_paths to return our tmp directories
    def _patched_resolve_paths():
        return (
            tmp_path,
            tmp_path / ".rhiza" / "template.yml",
            tmp_path / "pyproject.toml",
        )

    mod._resolve_paths = _patched_resolve_paths  # type: ignore[attr-defined]
    return mod.main(argv or [])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestScriptExists:
    """Verify that the script file exists and is syntactically valid."""

    def test_script_file_exists(self):
        """sync_pyproject.py must exist at .rhiza/utils/sync_pyproject.py."""
        assert SCRIPT_PATH.exists(), f"sync_pyproject.py not found at {SCRIPT_PATH}"

    def test_script_has_valid_syntax(self):
        """sync_pyproject.py must be valid Python."""
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as exc:
            pytest.fail(f"sync_pyproject.py has a syntax error: {exc}")

    def test_script_has_module_docstring(self):
        """sync_pyproject.py must have a module-level docstring."""
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        docstring = ast.get_docstring(tree)
        assert docstring, "sync_pyproject.py is missing a module docstring"

    def test_script_mentions_rhiza_sync(self):
        """Module docstring must mention jebel-quant/rhiza SYNC origin."""
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "jebel-quant/rhiza" in source.lower() or "SYNC" in source, (
            "sync_pyproject.py should note it flows from jebel-quant/rhiza"
        )


class TestNoOp:
    """No changes made when conditions don't require it."""

    def test_no_pyproject_section_is_noop(self, tmp_path):
        """No pyproject: section → exit 0, file unchanged."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_NO_PYPROJECT)
        original = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")

        rc = _run_sync(tmp_path)

        assert rc == 0
        assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original

    def test_already_up_to_date_is_noop(self, tmp_path):
        """If requires-python already matches, file should not change."""
        pyproject = textwrap.dedent("""\
            [project]
            name = "my-project"
            version = "1.2.3"
            requires-python = ">=3.11"
            dependencies = []
        """)
        _make_project(tmp_path, pyproject, _TEMPLATE_WITH_REQUIRES_PYTHON)
        original = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")

        rc = _run_sync(tmp_path)

        assert rc == 0
        assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original

    def test_missing_template_yml_is_noop(self, tmp_path):
        """If template.yml doesn't exist, exit 0 without modifying anything."""
        (tmp_path / "pyproject.toml").write_text(_MINIMAL_PYPROJECT, encoding="utf-8")
        # No .rhiza/template.yml created

        # Need to create fake script path too
        (tmp_path / ".rhiza" / "utils").mkdir(parents=True)
        real_script = SCRIPT_PATH.read_text(encoding="utf-8")
        (tmp_path / ".rhiza" / "utils" / "sync_pyproject.py").write_text(real_script, encoding="utf-8")

        original = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
        rc = _run_sync(tmp_path)

        assert rc == 0
        assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original


class TestRequiresPython:
    """Tests for patching [project].requires-python."""

    def test_patches_requires_python(self, tmp_path):
        """requires-python should be updated to the template value."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_REQUIRES_PYTHON)

        rc = _run_sync(tmp_path)

        assert rc == 0
        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["requires-python"] == ">=3.11"

    def test_preserves_name_version_description(self, tmp_path):
        """Patching requires-python must not touch name/version/description."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_REQUIRES_PYTHON)

        _run_sync(tmp_path)

        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["name"] == "my-project"
        assert result["project"]["version"] == "1.2.3"
        assert result["project"]["description"] == "A test project"

    def test_preserves_dependencies(self, tmp_path):
        """Patching requires-python must not touch dependencies."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_REQUIRES_PYTHON)

        _run_sync(tmp_path)

        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["dependencies"] == ["requests>=2.0"]

    def test_preserves_dependency_groups(self, tmp_path):
        """Patching requires-python must not touch [dependency-groups]."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_REQUIRES_PYTHON)

        _run_sync(tmp_path)

        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["dependency-groups"]["dev"] == ["pytest"]


class TestClassifiers:
    """Tests for patching [project].classifiers."""

    def test_replaces_classifiers(self, tmp_path):
        """Classifiers list should be replaced with template values."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_CLASSIFIERS)

        rc = _run_sync(tmp_path)

        assert rc == 0
        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["classifiers"] == [
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.11",
        ]

    def test_classifiers_replaces_existing(self, tmp_path):
        """Existing classifiers not in the template list should be removed."""
        pyproject = textwrap.dedent("""\
            [project]
            name = "my-project"
            version = "1.0.0"
            requires-python = ">=3.10"
            classifiers = [
                "Old Classifier :: Should Be Gone",
            ]
            dependencies = []
        """)
        _make_project(tmp_path, pyproject, _TEMPLATE_WITH_CLASSIFIERS)

        _run_sync(tmp_path)

        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert "Old Classifier :: Should Be Gone" not in result["project"]["classifiers"]
        assert "Programming Language :: Python :: 3" in result["project"]["classifiers"]


class TestDryRun:
    """Tests for --dry-run flag."""

    def test_dry_run_does_not_modify_file(self, tmp_path):
        """--dry-run must not write any changes to pyproject.toml."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_REQUIRES_PYTHON)
        original = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")

        rc = _run_sync(tmp_path, argv=["--dry-run"])

        assert rc == 0
        assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original

    def test_dry_run_exits_zero(self, tmp_path):
        """--dry-run should exit 0 even when there are pending changes."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_REQUIRES_PYTHON)

        rc = _run_sync(tmp_path, argv=["--dry-run"])

        assert rc == 0


class TestCheck:
    """Tests for --check flag."""

    def test_check_exits_nonzero_when_changes_pending(self, tmp_path):
        """--check should exit non-zero when changes would be made."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_REQUIRES_PYTHON)

        rc = _run_sync(tmp_path, argv=["--check"])

        assert rc != 0

    def test_check_does_not_modify_file(self, tmp_path):
        """--check must not write changes."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_REQUIRES_PYTHON)
        original = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")

        _run_sync(tmp_path, argv=["--check"])

        assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original

    def test_check_exits_zero_when_up_to_date(self, tmp_path):
        """--check should exit 0 when there are no pending changes."""
        pyproject = textwrap.dedent("""\
            [project]
            name = "my-project"
            version = "1.2.3"
            requires-python = ">=3.11"
            dependencies = []
        """)
        _make_project(tmp_path, pyproject, _TEMPLATE_WITH_REQUIRES_PYTHON)

        rc = _run_sync(tmp_path, argv=["--check"])

        assert rc == 0


class TestBothFields:
    """Tests when both requires-python and classifiers are in the template."""

    def test_patches_both_fields(self, tmp_path):
        """Both requires-python and classifiers should be updated."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_BOTH)

        rc = _run_sync(tmp_path)

        assert rc == 0
        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["requires-python"] == ">=3.12"
        assert "Programming Language :: Python :: 3.12" in result["project"]["classifiers"]

    def test_preserves_unrelated_fields(self, tmp_path):
        """Patching multiple fields must still preserve name/version/description/deps."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_BOTH)

        _run_sync(tmp_path)

        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["name"] == "my-project"
        assert result["project"]["version"] == "1.2.3"
        assert result["project"]["description"] == "A test project"
        assert result["project"]["dependencies"] == ["requests>=2.0"]


class TestLicense:
    """Tests for patching [project].license."""

    def test_patches_license_string(self, tmp_path):
        """License as a plain string should be written as a string."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_LICENSE_STRING)

        rc = _run_sync(tmp_path)

        assert rc == 0
        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["license"] == "MIT"

    def test_patches_license_table(self, tmp_path):
        """License as a mapping should be written as an inline table."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_LICENSE_TABLE)

        rc = _run_sync(tmp_path)

        assert rc == 0
        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["license"] == {"text": "MIT"}

    def test_license_noop_when_already_matching_string(self, tmp_path):
        """License should not change if it already matches the template value."""
        pyproject = textwrap.dedent("""\
            [project]
            name = "my-project"
            version = "1.0.0"
            license = "MIT"
            dependencies = []
        """)
        _make_project(tmp_path, pyproject, _TEMPLATE_WITH_LICENSE_STRING)
        original = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")

        rc = _run_sync(tmp_path)

        assert rc == 0
        assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original

    def test_license_preserves_other_fields(self, tmp_path):
        """Patching license must not touch name/version/dependencies."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_LICENSE_STRING)

        _run_sync(tmp_path)

        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["name"] == "my-project"
        assert result["project"]["version"] == "1.2.3"
        assert result["project"]["dependencies"] == ["requests>=2.0"]


class TestReadme:
    """Tests for patching [project].readme."""

    def test_patches_readme(self, tmp_path):
        """Readme should be updated to the template value."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_README)

        rc = _run_sync(tmp_path)

        assert rc == 0
        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["readme"] == "README.md"

    def test_readme_noop_when_already_matching(self, tmp_path):
        """Readme should not change if it already matches the template value."""
        pyproject = textwrap.dedent("""\
            [project]
            name = "my-project"
            version = "1.0.0"
            readme = "README.md"
            dependencies = []
        """)
        _make_project(tmp_path, pyproject, _TEMPLATE_WITH_README)
        original = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")

        rc = _run_sync(tmp_path)

        assert rc == 0
        assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original

    def test_readme_preserves_other_fields(self, tmp_path):
        """Patching readme must not touch name/version/dependencies."""
        _make_project(tmp_path, _MINIMAL_PYPROJECT, _TEMPLATE_WITH_README)

        _run_sync(tmp_path)

        with (tmp_path / "pyproject.toml").open("rb") as f:
            result = tomllib.load(f)
        assert result["project"]["name"] == "my-project"
        assert result["project"]["version"] == "1.2.3"
        assert result["project"]["dependencies"] == ["requests>=2.0"]
