"""Verify that the optional PyPI implementation works with the generic publisher contract."""

from __future__ import annotations

import os
import subprocess  # nosec B404 - executes the checked-in publisher shell in fixture projects
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_ACTION = _ROOT / "examples/publishing/pypi/action.yml"


def _run(step, directory, **environment):
    """Execute an adapter step with GitHub's failure semantics."""
    output = directory / "output"
    output.write_text("")
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=directory,
        env={**os.environ, "GITHUB_WORKSPACE": str(directory), "GITHUB_OUTPUT": str(output), **environment},
        capture_output=True,
        text=True,
        check=False,
    )
    return result, dict(line.split("=", 1) for line in output.read_text().splitlines())


@pytest.mark.parametrize(
    ("private", "files", "success"),
    [
        (False, ["demo.whl", "demo.tar.gz", "provenance.intoto.jsonl"], True),
        (False, ["provenance.intoto.jsonl"], False),
        (True, ["demo.whl"], False),
    ],
)
def test_pypi_stages_verified_distributions(tmp_path, private, files, success):
    """PyPI receives unchanged distributions; private or absent packages cannot upload."""
    classifier = '"Private :: Do Not Upload"' if private else ""
    (tmp_path / "pyproject.toml").write_text(f'[project]\nname="demo"\nclassifiers=[{classifier}]\n')
    artifacts = tmp_path / "release-dist"
    artifacts.mkdir()
    for name in files:
        (artifacts / name).write_bytes(b"verified release bytes")
    action = yaml.safe_load(_ACTION.read_text())
    result, output = _run(action["runs"]["steps"][0], tmp_path, ARTIFACTS_DIR=str(artifacts))
    assert (result.returncode == 0) == success, result.stderr
    if success:
        staging = tmp_path / output["directory"]
        assert sorted(p.name for p in staging.iterdir()) == ["demo.tar.gz", "demo.whl"]
        assert all(p.read_bytes() == b"verified release bytes" for p in staging.iterdir())
    else:
        assert not output
    upload = action["runs"]["steps"][1]
    assert upload["uses"].startswith("pypa/gh-action-pypi-publish@")
    assert upload["with"]["password"] == "${{ inputs.credentials }}"  # noqa: S105 - Actions input reference
    assert upload["with"]["packages-dir"] == "${{ steps.prepare.outputs.directory }}/"
    assert all(not step.get("continue-on-error") and not step.get("if") for step in action["runs"]["steps"])


def test_pypi_success_outputs_feed_generic_release_notes_and_conda(tmp_path):
    """The adapter reports its link and public publication only after the upload step."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname="demo"\n')
    action = yaml.safe_load(_ACTION.read_text())
    result, output = _run(action["runs"]["steps"][2], tmp_path, VERSION="1.2.3")
    assert result.returncode == 0, result.stderr
    assert output == {"artifact-url": "https://pypi.org/project/demo/1.2.3/", "public-pypi": "true"}
    assert action["outputs"]["artifact-url"]["value"] == "${{ steps.link.outputs.artifact-url }}"
    assert action["outputs"]["public-pypi"]["value"] == "${{ steps.link.outputs.public-pypi }}"


def test_opt_in_bundle_ships_the_supported_adapter():
    """The maintained bundle has the tested behavior and remains outside default profiles."""
    shipped = yaml.safe_load((_ROOT / "bundles/github-pypi/.github/actions/release-publish/action.yml").read_text())
    example = yaml.safe_load(_ACTION.read_text())
    assert shipped["runs"] == example["runs"]
    assert shipped["inputs"] == example["inputs"]
    assert shipped["outputs"] == example["outputs"]
    bundles = yaml.safe_load((_ROOT / ".rhiza/template-bundles.yml").read_text())
    assert "github-pypi" in bundles["bundles"]
    assert all("github-pypi" not in profile["bundles"] for profile in bundles["profiles"].values())
