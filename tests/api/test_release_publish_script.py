"""Direct tests of the synced publisher guards, including their CLI error boundary."""

from __future__ import annotations

import configparser
import importlib.util
import itertools
import os
import re
import runpy
import tomllib
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = Path("bundles/github/.rhiza/scripts/release_publish.py")
_SPEC = importlib.util.spec_from_file_location("release_publish", _ROOT / _SCRIPT)
assert _SPEC is not None
assert _SPEC.loader is not None
publisher = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(publisher)


@pytest.mark.parametrize(
    ("mode", "buildable", "private"),
    list(itertools.product(("", "pypi", "custom", "none"), ("true", "false"), (True, False))),
)
def test_decisions(tmp_path, mode, buildable, private):
    """Exercise every publisher/private/buildable combination directly under coverage."""
    classifier = '"Private :: Do Not Upload"' if private else ""
    (tmp_path / "pyproject.toml").write_text(f"[project]\nclassifiers=[{classifier}]\n")
    action = tmp_path / ".github/actions/release-publish/action.yaml"
    action.parent.mkdir(parents=True)
    action.write_text("name: publisher\n")
    if mode == "custom" and buildable == "false":
        with pytest.raises(publisher.PublisherError, match="requires a buildable"):
            publisher.validate_publisher(mode, buildable, "", "v1.2.3", tmp_path)
        return
    expected_mode = mode or "pypi"
    publish = expected_mode != "none" and buildable == "true" and (expected_mode == "custom" or not private)
    assert publisher.validate_publisher(mode, buildable, "", "v1.2.3", tmp_path) == {
        "publisher": expected_mode,
        "should_publish": str(publish).lower(),
        "public_pypi": str(publish and expected_mode == "pypi").lower(),
        "version": "1.2.3",
    }


@pytest.mark.parametrize(
    ("mode", "buildable", "endpoint", "message"),
    [
        ("unknown", "true", "", "RELEASE_PUBLISHER"),
        ("pypi", "", "", "buildable"),
        ("pypi", "true", "http://private.example", "PYPI_REPOSITORY_URL"),
        ("custom", "true", "", "action.yml or action.yaml"),
    ],
)
def test_invalid_configuration(tmp_path, mode, buildable, endpoint, message):
    """Invalid configuration never returns partial outputs."""
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    with pytest.raises(publisher.PublisherError, match=message):
        publisher.validate_publisher(mode, buildable, endpoint, "v1.2.3", tmp_path)


@pytest.mark.parametrize(
    ("url", "valid"),
    [
        ("https://packages/upload/", True),
        ("https://packages.internal./upload/", True),
        ("https://10.0.0.1/upload/", True),
        ("https://[fd00::1]:8443/upload/", True),
        ("https://packages.example.org/upload/?channel=stable", True),
        ("******example.org", False),
        ("https://@example.org", False),
        ("https://bad_host.example.org", False),
        ("https://[invalid]/", False),
        ("https://example.org:65536", False),
        ("https://example.org:0", False),
        ("https://example.org:", False),
        ("https://example.org/\n", False),
        ("https://example.org/a\x7fb", False),
        ("http://example.org", False),
        ("not-a-url", False),
        ("https://" + "a" * 254 + "/", False),
    ],
)
def test_endpoint(url, valid):
    """Endpoint syntax is checked without rejecting private package indexes."""
    assert publisher.valid_endpoint(url) is valid


@pytest.mark.parametrize(
    ("url", "valid"),
    [
        ("", True),
        ("https://packages.example.org/a%2Fb", True),
        ("https://8.8.8.8/demo", True),
        ("https://[2606:4700:4700::1111]:443/demo", True),
        ("https://localhost", False),
        ("https://example.org.", False),
        ("https://packages.local", False),
        ("https://packages.internal", False),
        ("https://packages.localhost", False),
        ("https://127.0.0.1", False),
        ("https://127.1", False),
        ("https://999.999.999.999", False),
        ("******example.org", False),
        ("https://@example.org", False),
        ("https://example.org:65536", False),
        ("https://example.org:0", False),
        ("https://example.org:", False),
        ("https://[invalid]", False),
        ("https://example.org/a%0Ab", False),
        ("https://example.org/%3E", False),
        ("https://example.org/a\x01b", False),
        ("https://example.org/a\x7fb", False),
        ("https://bad_host.example.org", False),
        ("http://example.org", False),
        ("HTTPS://example.org", False),
    ],
)
def test_artifact_url(url, valid):
    """Optional links must be safe public HTTPS URLs and are never normalized."""
    if valid:
        assert publisher.validate_artifact_url(url) == ({"artifact_url": url} if url else {})
    else:
        with pytest.raises(publisher.PublisherError, match="one public credential-free HTTPS URL"):
            publisher.validate_artifact_url(url)


@pytest.mark.parametrize("filename", ["demo.whl", "demo.tar.gz", "provenance.intoto.jsonl", None])
def test_distributions(tmp_path, filename):
    """Only files with distribution extensions satisfy the read-only guard."""
    (tmp_path / "directory.whl").mkdir()
    if filename:
        (tmp_path / filename).write_bytes(b"built")
    if filename in {"demo.whl", "demo.tar.gz"}:
        assert publisher.require_distributions(tmp_path) is None
        assert (tmp_path / filename).read_bytes() == b"built"
    else:
        with pytest.raises(publisher.PublisherError, match="contains no wheel or sdist"):
            publisher.require_distributions(tmp_path)


@pytest.mark.parametrize("command", ["validate-publisher", "require-distributions", "validate-artifact-url"])
def test_missing_environment(command, capsys):
    """Each CLI command fails closed when its required environment is absent."""
    assert publisher.main([command], {}) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "::error::Missing or invalid publisher configuration or output file\n"


@pytest.mark.parametrize("contents", [None, "credential = [broken", "project = 1", "[project]\nclassifiers = 1"])
def test_bad_metadata(tmp_path, monkeypatch, capsys, contents):
    """Missing/malformed metadata fails cleanly without printing its contents."""
    monkeypatch.chdir(tmp_path)
    if contents is not None:
        (tmp_path / "pyproject.toml").write_text(contents)
    environment = {"RELEASE_PUBLISHER": "", "BUILDABLE": "true", "PYPI_REPOSITORY_URL": "", "TAG": "v1.2.3"}
    assert publisher.main(["validate-publisher"], environment) == 1
    assert capsys.readouterr().err == "::error::Missing or invalid publisher configuration or output file\n"


_SAFE_ERROR = "::error::Missing or invalid publisher configuration or output file\n"


# The CLI appends validated outputs only, with a safe diagnostic on expected failures.
# One property per test (#1807).


@pytest.fixture
def cli_environment(tmp_path, monkeypatch):
    """Return a CLI environment whose ``GITHUB_OUTPUT`` already holds an unrelated line."""
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "output"
    output.write_text("existing=value\n")
    return {
        "RELEASE_PUBLISHER": "none",
        "BUILDABLE": "true",
        "PYPI_REPOSITORY_URL": "",
        "TAG": "v1.2.3",
        "GITHUB_OUTPUT": str(output),
    }


def test_main_appends_publisher_outputs(cli_environment):
    """validate-publisher appends its outputs after what GITHUB_OUTPUT already holds."""
    assert publisher.main(["validate-publisher"], cli_environment) == 0
    assert Path(cli_environment["GITHUB_OUTPUT"]).read_text() == (
        "existing=value\npublisher=none\nshould_publish=false\npublic_pypi=false\nversion=1.2.3\n"
    )


def test_main_accepts_an_empty_artifact_url():
    """An empty artifact URL is valid and needs no output file."""
    assert publisher.main(["validate-artifact-url"], {"ARTIFACT_URL": ""}) == 0


def test_main_rejects_an_unsafe_artifact_url(capsys):
    """An unsafe artifact URL fails with a diagnostic that does not echo it."""
    assert publisher.main(["validate-artifact-url"], {"ARTIFACT_URL": "******example.org"}) == 1
    assert capsys.readouterr().err == ("::error::Publisher artifact-url must be one public credential-free HTTPS URL\n")


def test_main_appends_a_valid_artifact_url(cli_environment):
    """A valid artifact URL is appended to GITHUB_OUTPUT."""
    cli_environment["ARTIFACT_URL"] = "https://example.org/release"
    assert publisher.main(["validate-artifact-url"], cli_environment) == 0
    assert Path(cli_environment["GITHUB_OUTPUT"]).read_text().endswith("artifact_url=https://example.org/release\n")


def test_main_fails_safely_on_an_unwritable_output(tmp_path, cli_environment, capsys):
    """A GITHUB_OUTPUT that cannot be written fails with the generic safe diagnostic."""
    cli_environment["ARTIFACT_URL"] = "https://example.org/release"
    cli_environment["GITHUB_OUTPUT"] = str(tmp_path)
    assert publisher.main(["validate-artifact-url"], cli_environment) == 1
    assert capsys.readouterr().err == _SAFE_ERROR


def test_main_accepts_built_distributions(tmp_path):
    """require-distributions succeeds when the artifacts directory holds a wheel."""
    (tmp_path / "demo.whl").write_bytes(b"built")
    assert publisher.main(["require-distributions"], {"ARTIFACTS_DIR": str(tmp_path)}) == 0


def test_main_rejects_an_unknown_command():
    """An unknown command is a usage error (exit status 2)."""
    with pytest.raises(SystemExit, match="2"):
        publisher.main(["unknown"], {})


def test_entrypoint(monkeypatch):
    """Executing the synced file uses the same CLI and propagates its exit status."""
    monkeypatch.setattr("sys.argv", [str(_SCRIPT), "validate-artifact-url"])
    monkeypatch.setenv("ARTIFACT_URL", "")
    with pytest.raises(SystemExit, match="0"):
        runpy.run_path(str(_ROOT / _SCRIPT), run_name="__main__")


def test_helper_is_shipped_and_dogfooded():
    """The real bundle file and relative dogfood symlink have one implementation."""
    source = _ROOT / _SCRIPT
    dogfood = _ROOT / ".rhiza/scripts/release_publish.py"
    assert source.is_file()
    assert not source.is_symlink()
    assert dogfood.is_symlink()
    assert not Path(os.readlink(dogfood)).is_absolute()
    assert dogfood.resolve() == source
    for workflow in (_ROOT / "bundles").glob("*/.github/workflows/rhiza_release.yml"):
        assert (workflow.parents[2] / ".rhiza/scripts/release_publish.py").resolve() == source


# The authoritative script is eligible for Ruff, Bandit and Python CodeQL.
# One scanner per test (#1807).


@pytest.fixture(scope="module")
def hooks():
    """Return the parsed root pre-commit configuration."""
    return yaml.safe_load((_ROOT / ".pre-commit-config.yaml").read_text())


@pytest.fixture(scope="module")
def codeql_job():
    """Return the CodeQL workflow's analyze job."""
    codeql = yaml.safe_load((_ROOT / ".github/workflows/rhiza_codeql.yml").read_text())
    return codeql["jobs"]["analyze"]


def _hook(hooks: dict, name: str) -> dict:
    """Return the pre-commit hook with id ``name``."""
    return next(hook for repo in hooks["repos"] for hook in repo["hooks"] if hook["id"] == name)


def test_script_is_not_excluded_from_pre_commit(hooks):
    """The pre-commit global exclude does not hide the script."""
    assert not re.search(hooks.get("exclude", "^$"), _SCRIPT.as_posix())


@pytest.mark.parametrize("name", ["ruff", "ruff-format", "bandit"])
def test_script_is_reached_by_hook(hooks, name):
    """Each scanner hook's ``files`` matches the script and its ``exclude`` does not."""
    hook = _hook(hooks, name)
    assert re.search(hook.get("files", ""), _SCRIPT.as_posix())
    assert not re.search(hook.get("exclude", "^$"), _SCRIPT.as_posix())


def test_script_is_not_excluded_from_bandit():
    """The .bandit exclude list does not cover the script."""
    bandit = configparser.ConfigParser()
    bandit.read(_ROOT / ".bandit")
    assert not any(part.strip() in _SCRIPT.as_posix() for part in bandit["bandit"]["exclude"].split(","))


def test_script_is_not_excluded_from_ruff():
    """ruff.toml's exclude patterns do not cover the script."""
    ruff = tomllib.loads((_ROOT / "ruff.toml").read_text())
    assert not any(_SCRIPT.match(pattern) for pattern in ruff["exclude"])


def test_codeql_analyzes_python(codeql_job):
    """CodeQL's matrix includes Python with no build."""
    assert {"language": "python", "build-mode": "none"} in codeql_job["strategy"]["matrix"]["include"]


def test_codeql_uses_the_default_configuration(codeql_job):
    """CodeQL is initialised per matrix language with no config that could narrow its paths."""
    initialization = next(step for step in codeql_job["steps"] if step.get("name") == "Initialize CodeQL")
    assert initialization["with"]["languages"] == "${{ matrix.language }}"
    assert "config-file" not in initialization["with"]
    assert "config" not in initialization["with"]
