"""Execute the opt-in CodeArtifact action shells without AWS or publishing credentials."""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - runs repository-owned action scripts with mocked providers
import sys
from pathlib import Path

import pytest
import yaml

from tests.util import sync_bundles

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "bundles/github-codeartifact"
_ADAPTER = yaml.safe_load((_BUNDLE / ".github/actions/release-publish/action.yml").read_text())
_PROVIDER = yaml.safe_load((_BUNDLE / ".github/actions/codeartifact-publish/action.yml").read_text())
_VALIDATE, _UV, _AUTH, _UPLOAD = _PROVIDER["runs"]["steps"]
_VARIABLES = {
    "AWS_REGION": "eu-west-1",
    "AWS_ROLE_TO_ASSUME_PUBLISH": "arn:aws:iam::123456789012:role/releases/publish",
    "CODEARTIFACT_DOMAIN": "packages",
    "CODEARTIFACT_DOMAIN_OWNER": "987654321012",
    "CODEARTIFACT_REPOSITORY": "python",
}


def _run(step, directory, environment):
    """Execute exact action shell text with the runner's fail-fast settings."""
    output = directory / "github-output"
    output.write_text("")
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=directory,
        env={**os.environ, **environment, "GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        check=False,
    )
    return result, output.read_text()


@pytest.fixture
def publish_env(tmp_path):
    """Provide real artifacts and mock AWS/uv executables recording no credentials."""
    dist = tmp_path / "verified dist"
    dist.mkdir()
    for name in ("example-1.2.3-py3-none-any.whl", "example-1.2.3.tar.gz", "provenance.intoto.jsonl"):
        (dist / name).write_bytes(b"original verified bytes")
    aws = tmp_path / "aws"
    aws.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open('aws-calls', 'a') as output: output.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "operation = sys.argv[2]\n"
        "if operation == os.environ.get('FAIL_AWS'):\n"
        "    print('sensitive provider diagnostic', file=sys.stderr)\n"
        "    sys.exit(17)\n"
        "print(os.environ['ENDPOINT'] if operation == 'get-repository-endpoint' else os.environ['TEST_TOKEN'])\n"
    )
    aws.chmod(0o755)
    uv = tmp_path / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "assert os.environ['UV_PUBLISH_PASSWORD'] == os.environ['TEST_TOKEN']\n"
        "with open('uv-call', 'w') as output: json.dump(sys.argv[1:], output)\n"
        "if os.environ.get('FAIL_UV'):\n"
        "    print(os.environ['UV_PUBLISH_PASSWORD'], file=sys.stderr)\n"
        "    sys.exit(19)\n"
    )
    uv.chmod(0o755)
    return {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "ARTIFACTS_DIR": str(dist),
        "TAG": "v1.2.3",
        "VERSION": "1.2.3",
        "REGION": _VARIABLES["AWS_REGION"],
        "ROLE": _VARIABLES["AWS_ROLE_TO_ASSUME_PUBLISH"],
        "DOMAIN": _VARIABLES["CODEARTIFACT_DOMAIN"],
        "OWNER": _VARIABLES["CODEARTIFACT_DOMAIN_OWNER"],
        "REPOSITORY": _VARIABLES["CODEARTIFACT_REPOSITORY"],
        "DNS_SUFFIX": "amazonaws.com",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": "refs/tags/v1.2.3",
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "fixture-oidc",
        "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.invalid/oidc",
        "ENDPOINT": "https://packages-987654321012.d.codeartifact.eu-west-1.amazonaws.com/pypi/python/",
        "TEST_TOKEN": "fixture-codeartifact-token",
    }


def test_explicit_adoption_only(tmp_path):
    """No profile or mother-repo action adopts this draft; its closure supplies both actions."""
    config = yaml.safe_load((_ROOT / ".rhiza/template-bundles.yml").read_text())
    definition = config["bundles"]["github-codeartifact"]
    assert definition["requires"] == ["github", "python-core"]
    assert "DRAFT / DO NOT RELEASE" in definition["notes"]
    assert "_rhiza_merge.merge_one" in definition["notes"]
    for profile in config["profiles"].values():
        assert "github-codeartifact" not in str(profile)
    closure = set()
    pending = ["github-codeartifact"]
    while pending:
        name = pending.pop()
        if name not in closure:
            closure.add(name)
            pending.extend(config["bundles"][name].get("requires", []))
    assert closure == {"github-codeartifact", "github", "python-core", "core"}
    sync_bundles(_ROOT, sorted(closure), tmp_path)
    paths = {".github/actions/release-publish/action.yml", ".github/actions/codeartifact-publish/action.yml"}
    assert {str(path.relative_to(_BUNDLE)) for path in _BUNDLE.rglob("*") if path.is_file()} == paths
    for path in paths:
        assert (tmp_path / path).read_bytes() == (_BUNDLE / path).read_bytes()
        assert not (tmp_path / path).is_symlink()
        assert not (_ROOT / path).exists()
    assert not (_ROOT / "bundles/github/.github/actions/release-publish").exists()


def test_adapter_contract_and_configuration(tmp_path):
    """The stable custom contract bridges workflow vars using only supported composite contexts."""
    assert set(_ADAPTER["inputs"]) == {"artifacts-dir", "tag", "version", "credentials"}
    assert "outputs" not in _ADAPTER
    steps = _ADAPTER["runs"]["steps"]
    result, output = _run(steps[0], tmp_path, {"RHIZA_RELEASE_PUBLISH_VARS": json.dumps(_VARIABLES)})
    assert result.returncode == 0, result.stderr
    assert dict(line.split("=", 1) for line in output.splitlines()) == {
        "region": _VARIABLES["AWS_REGION"],
        "role": _VARIABLES["AWS_ROLE_TO_ASSUME_PUBLISH"],
        "domain": _VARIABLES["CODEARTIFACT_DOMAIN"],
        "owner": _VARIABLES["CODEARTIFACT_DOMAIN_OWNER"],
        "repository": _VARIABLES["CODEARTIFACT_REPOSITORY"],
    }
    assert steps[1]["uses"] == "./.github/actions/codeartifact-publish"
    for name in ("artifacts-dir", "tag", "version"):
        assert steps[1]["with"][name] == "${{ inputs." + name + " }}"
    assert "credentials" not in steps[1]["with"]
    for action in (_ADAPTER, _PROVIDER):
        assert "vars." not in str(action) and "secrets." not in str(action)
        assert "artifact-url" not in action.get("outputs", {})
        for step in action["runs"]["steps"]:
            assert not step.get("continue-on-error")
            assert "${{" not in step.get("run", "")


@pytest.mark.parametrize("config", ["", "invalid", "null", "[]", "{}", '{"AWS_REGION":"x\\ny=injected"}'])
def test_invalid_adapter_config_is_not_written(tmp_path, config):
    """Missing, malformed or multiline variables cannot inject action outputs."""
    result, output = _run(_ADAPTER["runs"]["steps"][0], tmp_path, {"RHIZA_RELEASE_PUBLISH_VARS": config})
    assert result.returncode != 0
    assert not output


def test_oidc_order_and_pin():
    """Validation precedes OIDC; no static keys, fallback authentication or credential outputs."""
    assert _VALIDATE["id"] == "validate"
    assert _AUTH["uses"] == "aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd"
    inputs = _AUTH["with"]
    assert inputs["unset-current-credentials"] == "true"
    assert inputs["output-env-credentials"] == "true"
    for name in ("translate-env-variables", "use-existing-credentials", "force-skip-oidc",
                 "role-chaining", "output-credentials"):
        assert inputs[name] == "false"
    assert "aws-access-key-id" not in inputs and "aws-secret-access-key" not in inputs
    assert inputs["allowed-account-ids"] == "${{ steps.validate.outputs.account }}"
    assert inputs["audience"] == "${{ steps.validate.outputs.audience }}"
    workflow = yaml.safe_load((_ROOT / ".github/workflows/rhiza_release.yml").read_text())
    setup = next(step for step in workflow["jobs"]["build"]["steps"] if step["name"] == "Install uv")
    assert _UV["uses"] == setup["uses"] and _UV["with"] == setup["with"]
    assert "GITHUB_ENV" not in _UPLOAD["run"] and "GITHUB_OUTPUT" not in _UPLOAD["run"]
    assert "aws codeartifact login" not in _UPLOAD["run"]


@pytest.mark.parametrize(
    ("partition", "region", "suffix"),
    [("aws", "eu-west-1", "amazonaws.com"), ("aws-cn", "cn-north-1", "amazonaws.com.cn"),
     ("aws-us-gov", "us-gov-west-1", "amazonaws.com")],
)
def test_validation_and_partition(tmp_path, publish_env, partition, region, suffix):
    """Commercial, China and GovCloud roles derive the appropriate endpoint suffix and audience."""
    publish_env.update(ROLE=f"arn:{partition}:iam::123456789012:role/publish", REGION=region)
    result, output = _run(_VALIDATE, tmp_path, publish_env)
    assert result.returncode == 0, result.stderr
    assert output == f"account=123456789012\naudience=sts.{suffix}\nsuffix={suffix}\n"
    assert not (tmp_path / "aws-calls").exists()


@pytest.mark.parametrize(
    ("key", "value"),
    [("REGION", ""), ("REGION", "eu-west-1\n"), ("REGION", "cn-north-1"),
     ("ROLE", ""), ("ROLE", "arn:aws:iam::123:role/publish"), ("DOMAIN", "-bad"),
     ("OWNER", "123"), ("REPOSITORY", "bad/path"), ("REPOSITORY", "python\n"),
     ("TAG", "main"), ("VERSION", "1.2.4"), ("GITHUB_REF", "refs/heads/main"),
     ("GITHUB_EVENT_NAME", "pull_request"), ("GITHUB_EVENT_NAME", "pull_request_target"),
     ("ACTIONS_ID_TOKEN_REQUEST_TOKEN", ""), ("ACTIONS_ID_TOKEN_REQUEST_URL", ""),
     ("ARTIFACTS_DIR", "relative"), ("ARTIFACTS_DIR", "/nonexistent-codeartifact-fixture")],
)
def test_invalid_inputs_fail_before_auth(tmp_path, publish_env, key, value):
    """Invalid or absent configuration fails before credentials or any provider command."""
    publish_env[key] = value
    result, output = _run(_VALIDATE, tmp_path, publish_env)
    assert result.returncode != 0
    assert not output
    assert not (tmp_path / "aws-calls").exists()


@pytest.mark.parametrize("shape", ["empty", "provenance", "symlink", "directory", "zero", "directory-link"])
def test_unsafe_artifacts_fail_before_auth(tmp_path, publish_env, shape):
    """No artifacts, fake distributions and symlinked paths cannot reach authentication."""
    dist = Path(publish_env["ARTIFACTS_DIR"])
    for path in dist.iterdir():
        path.unlink()
    if shape == "provenance":
        (dist / "provenance.intoto.jsonl").write_text("{}")
    elif shape == "symlink":
        (dist / "source").write_bytes(b"not verified")
        (dist / "example.whl").symlink_to(dist / "source")
    elif shape == "directory":
        (dist / "example.whl").mkdir()
    elif shape == "zero":
        (dist / "example.whl").touch()
    elif shape == "directory-link":
        (dist / "example.whl").write_bytes(b"not verified")
        link = tmp_path / "dist-link"
        link.symlink_to(dist, target_is_directory=True)
        publish_env["ARTIFACTS_DIR"] = str(link)
    result, output = _run(_VALIDATE, tmp_path, publish_env)
    assert result.returncode != 0
    assert not output
    assert not (tmp_path / "aws-calls").exists()


def test_upload_only_verified_distributions(tmp_path, publish_env):
    """Upload uses the discovered private URL, OIDC token and explicit files, never a rebuild."""
    result, output = _run(_UPLOAD, tmp_path, publish_env)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"::add-mask::{publish_env['TEST_TOKEN']}\n"
    assert not output
    args = json.loads((tmp_path / "uv-call").read_text())
    assert args[:11] == ["publish", "--no-config", "--no-cache", "--publish-url", publish_env["ENDPOINT"],
                         "--username", "aws", "--trusted-publishing", "never", "--keyring-provider", "disabled"]
    assert {Path(path).suffix for path in args[11:]} == {".whl", ".gz"}
    assert all(Path(path).read_bytes() == b"original verified bytes" for path in args[11:])
    calls = [json.loads(line) for line in (tmp_path / "aws-calls").read_text().splitlines()]
    assert [call[1] for call in calls] == ["get-repository-endpoint", "get-authorization-token"]
    assert calls[1][calls[1].index("--duration-seconds") + 1] == "0"
    for path in tmp_path.iterdir():
        if path.is_file():
            assert publish_env["TEST_TOKEN"] not in path.read_text()


@pytest.mark.parametrize("endpoint", ["", "None", "https://upload.pypi.org/legacy/",
                                     "http://packages.example.org/", "https://example.org/\ninjected",
                                     "https://packages-987654321012.d.codeartifact.eu-west-1.amazonaws.com.evil/pypi/python/"])
def test_untrusted_endpoint_stops_before_token(tmp_path, publish_env, endpoint):
    """Only the exact expected HTTPS AWS repository endpoint receives a token."""
    publish_env["ENDPOINT"] = endpoint
    result, output = _run(_UPLOAD, tmp_path, publish_env)
    assert result.returncode != 0
    assert not output and not (tmp_path / "uv-call").exists()
    assert len((tmp_path / "aws-calls").read_text().splitlines()) == 1


@pytest.mark.parametrize("token", ["", "None", "bad\ntoken", "bad\rtoken", "bad token"])
def test_invalid_token_is_masked_and_not_used(tmp_path, publish_env, token):
    """Malformed tokens cannot inject workflow commands or reach uv."""
    publish_env["TEST_TOKEN"] = token
    result, output = _run(_UPLOAD, tmp_path, publish_env)
    assert result.returncode != 0
    assert result.stdout.startswith("::add-mask::")
    assert len(result.stdout.splitlines()) == 2
    assert not output and not (tmp_path / "uv-call").exists()


@pytest.mark.parametrize("failure", ["get-repository-endpoint", "get-authorization-token", "uv"])
def test_provider_failures_propagate_without_credentials(tmp_path, publish_env, failure):
    """Authentication/upload errors fail closed without leaking provider diagnostics."""
    publish_env["FAIL_UV" if failure == "uv" else "FAIL_AWS"] = failure
    result, output = _run(_UPLOAD, tmp_path, publish_env)
    assert result.returncode != 0 and not output
    assert "sensitive provider diagnostic" not in result.stdout + result.stderr
    assert publish_env["TEST_TOKEN"] not in result.stderr
    assert publish_env["TEST_TOKEN"] not in result.stdout.replace(f"::add-mask::{publish_env['TEST_TOKEN']}", "")
