"""Execute the publisher guards from both shipped GitHub release workflows."""

from __future__ import annotations

import itertools
import os
import re
import subprocess  # nosec B404 - executes repository-owned workflow scripts in fixture projects
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_PATHS = (
    ".github/workflows/rhiza_release.yml",
    "bundles/github/.github/workflows/rhiza_release.yml",
)


@pytest.fixture(params=_PATHS)
def workflow(request):
    """Load each real workflow copy independently."""
    return yaml.safe_load((_ROOT / request.param).read_text())


def _step(workflow, job, name):
    """Return a named workflow step."""
    return next(step for step in workflow["jobs"][job]["steps"] if step.get("name") == name)


def _run(step, directory, **environment):
    """Run the actual shell with Actions' fail-fast flags and isolated outputs."""
    output = directory / "github-output"
    output.write_text("")
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=directory,
        env={**os.environ, "GITHUB_OUTPUT": str(output), **environment},
        capture_output=True,
        text=True,
        check=False,
    )
    return result, output.read_text()


def _outputs(text):
    """Parse the single-line outputs used by publisher decisions."""
    return dict(line.split("=", 1) for line in text.splitlines())


def _plan(workflow, directory, *, mode="", buildable="true", private=False, action="action.yml", **environment):
    """Prepare project metadata and execute the publisher configuration guard."""
    classifier = '"Private :: Do Not Upload"' if private else ""
    (directory / "pyproject.toml").write_text(f'[project]\nname="demo"\nclassifiers=[{classifier}]\n')
    if action:
        target = directory / ".github/actions/release-publish" / action
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("runs:\n  using: composite\n  steps:\n    - shell: bash\n      run: exit 1\n")
    result, output = _run(
        _step(workflow, "pypi", "Validate publisher configuration"),
        directory,
        RELEASE_PUBLISHER=mode,
        BUILDABLE=buildable,
        TAG="v1.2.3-rc.1",
        PYPI_REPOSITORY_URL="",
        PYPI_TOKEN="",
        **environment,
    )
    return result, _outputs(output)


@pytest.mark.parametrize(
    ("mode", "buildable", "private"),
    itertools.product(("", "pypi", "custom", "none"), ("true", "false"), (True, False)),
)
def test_publisher_modes(workflow, tmp_path, mode, buildable, private):
    """Default/private/disabled decisions are explicit; custom cannot silently skip."""
    result, output = _plan(workflow, tmp_path, mode=mode, buildable=buildable, private=private)
    if mode == "custom" and buildable == "false":
        assert result.returncode != 0
        assert not output
        return
    assert result.returncode == 0, result.stderr
    publisher = mode or "pypi"
    publish = publisher != "none" and buildable == "true" and (publisher == "custom" or not private)
    assert output == {
        "publisher": publisher,
        "should_publish": str(publish).lower(),
        "public_pypi": str(publish and publisher == "pypi").lower(),
        "version": "1.2.3-rc.1",
    }


@pytest.mark.parametrize("mode", ["unknown", "PyPI", "CUSTOM", " ", "custom\npypi", "$(touch injected)"])
def test_unknown_modes_fail_closed(workflow, tmp_path, mode):
    """Malformed mode values never default to public publishing or execute shell."""
    result, output = _plan(workflow, tmp_path, mode=mode)
    assert result.returncode != 0
    assert not output
    assert not (tmp_path / "injected").exists()


@pytest.mark.parametrize("buildable", ["", "TRUE", "no", "true\n"])
def test_missing_build_output_fails(workflow, tmp_path, buildable):
    """An absent producer output is not equivalent to a non-package project."""
    result, output = _plan(workflow, tmp_path, buildable=buildable)
    assert result.returncode != 0
    assert not output


@pytest.mark.parametrize("action", [None, "action.yml", "action.yaml", "README.txt"])
def test_custom_action_is_required(workflow, tmp_path, action):
    """Both Actions metadata filenames work; missing metadata is fatal."""
    result, output = _plan(workflow, tmp_path, mode="custom", private=True, action=action)
    assert (result.returncode == 0) == (action in {"action.yml", "action.yaml"})
    if result.returncode:
        assert not output


@pytest.mark.parametrize(
    ("endpoint", "token", "valid"),
    [
        ("https://packages.example.org/upload/", "opaque", True),
        ("https://upload.pypi.org/legacy/", "opaque", True),
        ("https://packages.example.org/upload/", "", False),
        ("http://packages.example.org/upload/", "opaque", False),
        ("not-a-url", "opaque", False),
        ("******example.org", "opaque", False),
        ("https://packages.example.org:99999", "opaque", False),
        ("https://packages.example.org:", "opaque", False),
        ("https://packages.example.org/\n", "opaque", False),
    ],
)
def test_legacy_endpoint_configuration(workflow, tmp_path, endpoint, token, valid):
    """Legacy feeds stay token-based and never advertise public PyPI or feed conda."""
    step = _step(workflow, "pypi", "Validate publisher configuration")
    (tmp_path / "pyproject.toml").write_text('[project]\nname="demo"\n')
    result, text = _run(
        step,
        tmp_path,
        RELEASE_PUBLISHER="pypi",
        BUILDABLE="true",
        TAG="v1.2.3",
        PYPI_REPOSITORY_URL=endpoint,
        PYPI_TOKEN=token,
    )
    assert (result.returncode == 0) == valid
    if valid:
        assert _outputs(text)["public_pypi"] == "false"
        assert _outputs(text)["should_publish"] == "true"
    else:
        assert not text
        assert endpoint not in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("files", "valid"),
    [
        (None, False),
        ((), False),
        (("provenance.intoto.jsonl",), False),
        (("demo.whl",), True),
        (("demo.tar.gz",), True),
        (("demo.whl", "demo.tar.gz", "provenance.intoto.jsonl"), True),
    ],
)
def test_distributions_are_required(workflow, tmp_path, files, valid):
    """Absent/empty/provenance-only downloads fail instead of skipping publication."""
    dist = tmp_path / "release-dist"
    if files is not None:
        dist.mkdir()
        for name in files:
            (dist / name).write_bytes(b"already-built")
    result, _ = _run(_step(workflow, "pypi", "Require built distributions"), tmp_path, ARTIFACTS_DIR=str(dist))
    assert (result.returncode == 0) == valid
    if files:
        assert all((dist / name).read_bytes() == b"already-built" for name in files)


def test_a_directory_is_not_a_distribution(workflow, tmp_path):
    """A wheel-shaped directory cannot satisfy the artifact check."""
    dist = tmp_path / "release-dist"
    (dist / "demo.whl").mkdir(parents=True)
    result, _ = _run(_step(workflow, "pypi", "Require built distributions"), tmp_path, ARTIFACTS_DIR=str(dist))
    assert result.returncode != 0


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://packages.example.org/demo/1.2.3",
        "https://packages.example.org:443/demo?release=1#files",
        "https://8.8.8.8/demo",
        "https://[2606:4700:4700::1111]/demo",
        "https://packages.example.org/a%2Fb",
    ],
)
def test_safe_optional_url(workflow, tmp_path, url):
    """Only the validated optional public URL propagates, unchanged."""
    result, output = _run(_step(workflow, "pypi", "Validate publisher artifact URL"), tmp_path, ARTIFACT_URL=url)
    assert result.returncode == 0, result.stderr
    assert _outputs(output) == ({"artifact_url": url} if url else {})


@pytest.mark.parametrize(
    "url",
    [
        "http://example.org",
        "//example.org",
        "******example.org/path",
        "https://user@example.org",
        "https://@example.org",
        "https://",
        "https://example.org:",
        "https://example.org:abc",
        "https://example.org:0",
        "https://example.org:65536",
        "https://bad_host.example.org",
        "https://-bad.example.org",
        "https://bad..example.org",
        "https://[invalid]/",
        "https://localhost/",
        "https://127.0.0.1/",
        "https://10.0.0.1/",
        "https://[::1]/",
        "https://packages.local/",
        "https://example.org/a b",
        "https://example.org/a\tb",
        "https://example.org/a\nartifact_url=https://evil.example",
        "https://example.org/a\x01b",
        "https://example.org/a\x7fb",
        "https://example.org/a%0Ab",
        "https://example.org/a%20b",
        "https://example.org/<script>",
        "https://example.org/%3E",
        "https://example.org/`shell`",
        "https://example.org\\@evil.example",
        "https://example.org https://other.example",
    ],
)
def test_invalid_url_never_leaks(workflow, tmp_path, url):
    """Malformed/private/credential-bearing URLs fail without printing their contents."""
    result, output = _run(_step(workflow, "pypi", "Validate publisher artifact URL"), tmp_path, ARTIFACT_URL=url)
    assert result.returncode != 0
    assert not output
    assert url not in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("enabled", "publish", "public", "result"),
    itertools.product(("", "true", "false"), ("true", "false"), ("true", "false"), ("success", "failure")),
)
def test_conda_only_follows_public_pypi(workflow, tmp_path, enabled, publish, public, result):
    """Conda excludes custom publishers, legacy feeds, disabled and failed uploads."""
    completed, output = _run(
        _step(workflow, "conda", "Check if conda recipe should be generated"),
        tmp_path,
        PUBLISH_CONDA=enabled,
        SHOULD_PUBLISH=publish,
        PUBLIC_PYPI=public,
        PUBLISH_RESULT=result,
    )
    assert completed.returncode == 0
    expected = enabled != "false" and publish == public == "true" and result == "success"
    assert _outputs(output)["should_generate"] == str(expected).lower()


def _condition(expression, values, *, cancelled=False):
    """Evaluate the workflow's conjunction/disjunction grammar without Python eval."""
    expression = expression.removeprefix("${{").removesuffix("}}").strip()
    expression = expression.replace("!cancelled()", str(not cancelled).lower())
    for key, value in sorted(values.items(), key=lambda item: -len(item[0])):
        expression = expression.replace(key, repr(value))
    terms = []
    for disjunction in expression.split("||"):
        conjunction = []
        for atom in disjunction.split("&&"):
            atom = atom.strip()
            if atom in {"true", "false"}:
                conjunction.append(atom == "true")
                continue
            match = re.fullmatch(r"'([^']*)'\s*(==|!=)\s*'([^']*)'", atom)
            assert match is not None, f"Unsupported expression: {atom}"
            left, operator, right = match.groups()
            conjunction.append((left == right) if operator == "==" else (left != right))
        terms.append(all(conjunction))
    return any(terms)


@pytest.mark.parametrize("job", ["tag", "build", "draft-release", "pypi", "devcontainer", "conda"])
@pytest.mark.parametrize("result", ["success", "failure", "skipped", "cancelled"])
@pytest.mark.parametrize("cancelled", [True, False])
def test_finalisation_requires_upload_success(workflow, job, result, cancelled):
    """Optional conda cannot mask failures, including a failed local composite upload."""
    finalise = workflow["jobs"]["finalise-release"]
    assert set(finalise["needs"]) == {"tag", "build", "draft-release", "pypi", "devcontainer", "conda"}
    values = {f"needs.{name}.result": "success" for name in finalise["needs"]}
    values[f"needs.{job}.result"] = result
    assert _condition(finalise["if"], values, cancelled=cancelled) == (
        not cancelled and (job == "conda" or result == "success")
    )


def test_publisher_contract_and_order(workflow):
    """Action reuses tag-verified downloads, scoped credentials, and release OIDC."""
    jobs = workflow["jobs"]
    publisher = jobs["pypi"]
    assert publisher["environment"] == "release"
    assert publisher["permissions"] == {"contents": "read", "id-token": "write"}
    assert not publisher.get("continue-on-error")
    assert jobs["build"]["outputs"]["buildable"] == "${{ steps.buildable.outputs.buildable }}"
    for name in ("build", "draft-release", "pypi", "conda", "devcontainer", "finalise-release"):
        checkout = _step(workflow, name, "Checkout Code")
        assert checkout["with"]["ref"] == "refs/tags/${{ needs.tag.outputs.tag }}"
    assert _step(workflow, "pypi", "Checkout Code")["with"]["persist-credentials"] is False
    steps = publisher["steps"]
    names = [step["name"] for step in steps]
    ordered = [
        "Validate publisher configuration",
        "Download dist artifact",
        "Require built distributions",
        "Publish with repository action",
        "Validate publisher artifact URL",
    ]
    assert [names.index(name) for name in ordered] == sorted(names.index(name) for name in ordered)
    download = _step(workflow, "pypi", "Download dist artifact")
    action = _step(workflow, "pypi", "Publish with repository action")
    assert download["with"] == {"name": "dist", "path": "${{ github.workspace }}/release-dist"}
    assert action["uses"] == "./.github/actions/release-publish"
    assert action["with"] == {
        "artifacts-dir": download["with"]["path"],
        "tag": "${{ needs.tag.outputs.tag }}",
        "version": "${{ steps.publisher.outputs.version }}",
        "credentials": "${{ secrets.RELEASE_PUBLISH_CREDENTIALS }}",
    }
    assert not action.get("env")
    assert not publisher.get("env")
    for step in steps:
        assert not step.get("continue-on-error")
        assert "uv build" not in step.get("run", "")
        assert "toJSON(secrets)" not in str(step)
        if "run" in step:
            assert "${{" not in step["run"]
    triggers = workflow.get("on") or workflow[True]
    assert triggers["workflow_call"]["secrets"]["RELEASE_PUBLISH_CREDENTIALS"]["required"] is False
    assert publisher["outputs"]["artifact_url"] == "${{ steps.artifact_url.outputs.artifact_url }}"
    assert publisher["outputs"]["publisher"] == "${{ steps.publisher.outputs.publisher }}"
    pypi = _step(workflow, "pypi", "Publish to PyPI")
    assert pypi["with"]["repository-url"] == "${{ vars.PYPI_REPOSITORY_URL }}"
    assert pypi["with"]["password"] == "${{ secrets.PYPI_TOKEN }}"  # noqa: S105 - Actions expression, not a token
    for mode, publish in itertools.product(("pypi", "custom", "none"), ("true", "false")):
        values = {"steps.publisher.outputs.publisher": mode, "steps.publisher.outputs.should_publish": publish}
        assert _condition(action["if"], values) == (mode == "custom" and publish == "true")
        assert _condition(pypi["if"], values) == (mode == "pypi" and publish == "true")
        assert _condition(download["if"], values) == (publish == "true")


@pytest.mark.parametrize("message", ["", "### Published Package\n\n<https://packages.example.org/demo>"])
def test_optional_notes_do_not_abort_finalisation(workflow, tmp_path, message):
    """Empty final notes still reach gh release edit under bash -e."""
    gh = tmp_path / "gh"
    gh.write_text(
        '#!/bin/bash\nif [[ "$2" == "view" ]]; then echo "Existing notes"; '
        'else printf "%s\\n" "$@" > gh-arguments; fi\n'
    )
    gh.chmod(0o755)
    result, _ = _run(
        _step(workflow, "finalise-release", "Publish Release"),
        tmp_path,
        PATH=f"{tmp_path}:{os.environ['PATH']}",
        TAG="v1.2.3",
        DEVCONTAINER_MSG="",
        PYPI_MSG="",
        CUSTOM_MSG=message,
        CONDA_MSG="",
    )
    assert result.returncode == 0, result.stderr
    assert "--draft=false" in (tmp_path / "gh-arguments").read_text()
    notes = (tmp_path / "release-notes.md").read_text()
    assert notes == "Existing notes" + (f"\n\n{message}" if message else "")


def test_custom_notes_only_use_validated_url(workflow, tmp_path):
    """A custom release never infers a public package link from project metadata."""
    step = _step(workflow, "finalise-release", "Generate Custom Publisher Link")
    url = "https://packages.example.org/demo?a=b&version=1"
    result, output = _run(step, tmp_path, ARTIFACT_URL=url)
    assert result.returncode == 0
    assert f"<{url}>" in output
    assert "pypi.org" not in output
    assert step["env"] == {"ARTIFACT_URL": "${{ needs.pypi.outputs.artifact_url }}"}
    pypi = _step(workflow, "finalise-release", "Generate PyPI Link")
    for mode in ("custom", "none", "pypi"):
        values = {
            "needs.pypi.outputs.publisher": mode,
            "needs.pypi.outputs.should_publish": "true",
            "needs.pypi.result": "success",
            "needs.pypi.outputs.artifact_url": url,
        }
        assert _condition(pypi["if"], values) == (mode == "pypi")
        assert _condition(step["if"], values) == (mode == "custom")


@pytest.mark.parametrize("tag", ["v1.2.3", "v1.2.3-rc.1", "v1.2.3\npublisher=pypi", "$(touch injected)", "main"])
def test_reusable_tag_is_passed_without_shell_interpolation(workflow, tmp_path, tag):
    """The reusable tag input cannot inject shell or additional job outputs."""
    result, output = _run(
        _step(workflow, "tag", "Set Tag Variable"), tmp_path, INPUT_TAG=tag, GITHUB_REF="refs/tags/v9.9.9"
    )
    if tag in {"v1.2.3", "v1.2.3-rc.1"}:
        assert result.returncode == 0
        assert _outputs(output) == {"tag": tag}
    else:
        assert result.returncode != 0
        assert not output
    assert not (tmp_path / "injected").exists()


def test_no_placeholder_publisher_is_shipped():
    """Selecting custom without a repository implementation must never pass via a stub."""
    assert not (_ROOT / ".github/actions/release-publish").exists()
    assert not (_ROOT / "bundles/github/.github/actions/release-publish").exists()
