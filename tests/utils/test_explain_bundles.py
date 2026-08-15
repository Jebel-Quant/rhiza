"""Unit tests for explain_bundles.py."""

from __future__ import annotations

import builtins
import importlib.util
import re
import sys
from pathlib import Path
from textwrap import dedent

import pytest

from tests.util import strip_ansi


def _load_module(root: Path, monkeypatch, tmp_path: Path, yaml_text: str):
    """Load explain_bundles.py against a temp project whose template-bundles.yml holds yaml_text.

    Since #1530 the import itself reads nothing — the chdir is what makes
    ``_config_path`` prefer the temp project once ``main`` is called.
    """
    module_path = root / "utils" / "explain_bundles.py"
    config_dir = tmp_path / ".rhiza"
    config_dir.mkdir()
    (config_dir / "template-bundles.yml").write_text(dedent(yaml_text), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    spec = importlib.util.spec_from_file_location(f"explain_bundles_{tmp_path.name}", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("github", "github"),
        ("github-tests", "github"),
        ("gitlab", "gitlab"),
        ("gitlab-book", "gitlab"),
        ("core", "base"),
    ],
)
def test_bundle_group_classifies_bundles(root, monkeypatch, tmp_path, name, expected):
    """Bundle groups should be assigned by platform prefix or default base."""
    module = _load_module(
        root,
        monkeypatch,
        tmp_path,
        """
        bundles: {}
        profiles: {}
        """,
    )

    assert module._bundle_group(name) == expected


def test_print_bundle_renders_dependencies_and_standalone_tag(root, monkeypatch, tmp_path, capsys):
    """Bundle rendering should show only the first description line and optional metadata."""
    module = _load_module(
        root,
        monkeypatch,
        tmp_path,
        """
        bundles: {}
        profiles: {}
        """,
    )
    capsys.readouterr()

    module._print_bundle(
        "github-tests",
        {
            "description": "GitHub workflows\nAdditional detail",
            "requires": ["tests"],
            "recommends": ["book"],
            "standalone": False,
        },
    )

    output = strip_ansi(capsys.readouterr().out)
    assert "github-tests            GitHub workflows  [not standalone]" in output
    assert "requires:   tests" in output
    assert "recommends: book" in output
    assert "Additional detail" not in output


def test_main_prints_grouped_bundle_and_profile_sections(root, monkeypatch, tmp_path, capsys):
    """Running main should render bundle and profile summaries from YAML."""
    module = _load_module(
        root,
        monkeypatch,
        tmp_path,
        """
        bundles:
          core:
            description: Core bundle
          github-tests:
            description: GitHub test workflows
          gitlab-book:
            description: GitLab docs workflow
            standalone: false
        profiles:
          local:
            description: Local development profile
            bundles: [core, github-tests]
        """,
    )
    capsys.readouterr()

    assert module.main() == 0

    output = strip_ansi(capsys.readouterr().out)
    assert module.group_bundles({"core": {"description": "Core bundle"}})["base"] == {
        "core": {"description": "Core bundle"}
    }
    assert "Bundles  (3 total)" in output
    assert "Core & Feature  (1)" in output
    assert "GitHub  (1)" in output
    assert "GitLab  (1)" in output
    assert "Profiles  (1 total)" in output
    assert "expands to: core, github-tests" in output


def test_import_reads_nothing_and_works_outside_a_project(root, monkeypatch, tmp_path, capsys):
    """The module must import from a directory holding no config, printing nothing (#1530).

    The regression this pins is the original defect: the config was opened at import
    time via a *relative* path, so importing from anywhere but a project root raised
    ``FileNotFoundError`` before a single function could be called.
    """
    monkeypatch.chdir(tmp_path)

    spec = importlib.util.spec_from_file_location("explain_bundles_no_project", root / "utils" / "explain_bundles.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert capsys.readouterr().out == ""
    assert module._bundle_group("github-tests") == "github"


def test_config_path_falls_back_to_the_repo_that_ships_the_script(root, monkeypatch, tmp_path):
    """With no config in the current directory, the script explains its own repo.

    This is the half that makes the module usable from anywhere: the fallback is
    resolved from ``__file__``, not from the process working directory.
    """
    module = _load_module(root, monkeypatch, tmp_path, "bundles: {}\nprofiles: {}\n")
    assert module._config_path() == tmp_path / ".rhiza" / "template-bundles.yml"

    monkeypatch.chdir(tmp_path / ".rhiza")  # a directory with no .rhiza/ of its own
    assert module._config_path() == root / ".rhiza" / "template-bundles.yml"


def test_main_exits_with_guidance_when_no_config_exists(root, monkeypatch, tmp_path):
    """A missing config must fail loudly rather than print an empty summary.

    The expected text is built from the module's own ``_CONFIG_REL`` rather than
    written out: it is a ``Path``, so it renders with a backslash on Windows, and
    hard-coding the POSIX form failed the whole Windows matrix while passing locally.
    """
    module = _load_module(root, monkeypatch, tmp_path, "bundles: {}\nprofiles: {}\n")
    monkeypatch.setattr(module, "_config_path", lambda: tmp_path / "absent" / "template-bundles.yml")

    with pytest.raises(SystemExit, match=re.escape(f"No {module._CONFIG_REL} found")):
        module.main()


def test_import_exits_with_install_hint_when_pyyaml_is_missing(root, monkeypatch, tmp_path):
    """A missing PyYAML dependency should surface the install guidance."""
    module_path = root / "utils" / "explain_bundles.py"
    monkeypatch.chdir(tmp_path)
    original_import = builtins.__import__

    def _fake_import(name: str, *args, **kwargs):
        """Stand in for __import__, raising ImportError for ``yaml`` to simulate the missing dep."""
        if name == "yaml":
            raise ImportError
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    spec = importlib.util.spec_from_file_location("explain_bundles_missing_yaml", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    with pytest.raises(SystemExit, match="pyyaml is not installed — run: make install"):
        spec.loader.exec_module(module)
