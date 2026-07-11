"""End-to-end validation of the GitLab CI templates — despite this repo being on GitHub.

The mother repo ships GitLab CI as a *template* for downstream consumers but runs
no GitLab pipeline itself, so a broken `.gitlab-ci.yml` (a bad `include:`, an
invalid job, or — as happened once — a container image tag that no longer exists
on the registry) would slip through GitHub-only CI. These tests close that gap by
assembling a ``gitlab-project`` (exactly the bundle set a downstream repo syncs)
and exercising it the way GitLab would, using tooling that needs no GitLab host:

* **image existence** (``test_pipeline_images_exist``) — every container image the
  pipeline (and the docker/devcontainer bundles) references is checked against its
  registry. This is the cheap guard that would have caught the retired
  ``ghcr.io/astral-sh/uv:*-bookworm`` tags. Needs network; skips (does not fail)
  when no registry is reachable.
* **schema / structure** (``test_pipeline_schema_validates``) — ``gitlab-ci-local``
  resolves every ``include:`` and validates the merged pipeline against GitLab's
  JSON schema, then lists the jobs. Needs Node/``npx``; skips when absent.
* **real execution** (``test_pinned_uv_image_runs_in_docker``) — the pinned uv
  image is pulled and a job is run inside it, proving the pipeline's default image
  actually works. Needs Docker and is opt-in (set ``RHIZA_GITLAB_DOCKER=1``) since
  it pulls a multi-hundred-MB image; marked ``gitlab_exec``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess  # nosec B404
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest
import yaml

from tests.util import sync_bundles

# The bundle closure a downstream `gitlab-project` profile expands to (mirrors
# tests/bundles/test_bundle_combinations.py::TestGitlabProjectProfileSync).
GITLAB_PROJECT_BUNDLES = [
    "core",
    "book",
    "marimo",
    "tests",
    "gitlab",
    "gitlab-book",
    "gitlab-marimo",
    "gitlab-tests",
]

# Pinned so a gitlab-ci-local release cannot silently change validation behaviour.
GITLAB_CI_LOCAL_VERSION = "4.73.0"

_NPX = shutil.which("npx")
_DOCKER = shutil.which("docker")
_GIT = shutil.which("git") or "/usr/bin/git"

# gitlab-ci-local is a POSIX-oriented tool (bash/Docker semantics); it is not a
# supported path on native Windows and crashes the xdist worker there. Its
# behaviour is platform-independent, so validating on Linux/macOS is sufficient.
# (The pure-network image-existence check stays cross-platform.)
_skip_on_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="gitlab-ci-local is unsupported on native Windows; validated on POSIX runners",
)

_MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)


# ---------------------------------------------------------------------------
# Assembling a synced gitlab-project
# ---------------------------------------------------------------------------


def _assemble_gitlab_project(root: Path, dest: Path) -> Path:
    """Sync the gitlab-project bundle closure into dest and make it a git repo.

    gitlab-ci-local reads git metadata (branch, remote, diff base for
    ``rules: changes:``); a bare init plus a self-referencing ``origin/main`` ref
    gives it everything it needs without a real remote.
    """
    sync_bundles(root, GITLAB_PROJECT_BUNDLES, dest)

    def git(*args: str) -> None:
        """Run a git command in the assembled project with global/system config disabled."""
        subprocess.run(  # nosec B603
            [_GIT, *args],
            cwd=dest,
            check=True,
            capture_output=True,
            env={**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"},
        )

    git("init", "-q", "-b", "main")
    git("config", "user.email", "ci@rhiza.test")
    git("config", "user.name", "rhiza ci")
    git("add", "-A")
    git("commit", "-qm", "assemble gitlab-project")
    git("remote", "add", "origin", str(dest))
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    return dest


# ---------------------------------------------------------------------------
# Image collection
# ---------------------------------------------------------------------------


def _walk_images(node: object) -> list[str]:
    """Recursively collect every container image reference in a loaded YAML doc.

    Handles GitLab's ``image:`` (string or ``{name: ...}``) and ``services:``
    (list of strings or ``{name: ...}``) wherever they appear (``default:`` or
    per-job).
    """
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "image":
                if isinstance(value, str):
                    found.append(value)
                elif isinstance(value, dict) and isinstance(value.get("name"), str):
                    found.append(value["name"])
            elif key == "services" and isinstance(value, list):
                for svc in value:
                    if isinstance(svc, str):
                        found.append(svc)
                    elif isinstance(svc, dict) and isinstance(svc.get("name"), str):
                        found.append(svc["name"])
            else:
                found.extend(_walk_images(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_walk_images(item))
    return found


def _collect_variables(project: Path) -> dict[str, str]:
    """Merge every ``variables:`` block across the assembled pipeline files."""
    variables: dict[str, str] = {}
    files = [project / ".gitlab-ci.yml", *sorted((project / ".gitlab" / "workflows").glob("*.yml"))]
    for path in files:
        if not path.is_file():
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        block = doc.get("variables") if isinstance(doc, dict) else None
        if isinstance(block, dict):
            for name, value in block.items():
                if isinstance(value, (str, int)):
                    variables.setdefault(str(name), str(value))
    return variables


def _resolve(image: str, variables: dict[str, str]) -> str | None:
    """Substitute ``$VAR`` / ``${VAR}`` tokens; return None if any remain unresolved."""
    resolved = re.sub(
        r"\$\{?(\w+)\}?",
        lambda m: variables.get(m.group(1), m.group(0)),
        image,
    )
    return None if "$" in resolved else resolved


def _collect_pipeline_images(project: Path) -> set[str]:
    """Return the concrete container images an assembled gitlab-project would pull."""
    variables = _collect_variables(project)
    images: set[str] = set()
    files = [project / ".gitlab-ci.yml", *sorted((project / ".gitlab" / "workflows").glob("*.yml"))]
    for path in files:
        if not path.is_file():
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for raw in _walk_images(doc):
            resolved = _resolve(raw, variables)
            if resolved:
                images.add(resolved)
    return images


def _dockerfile_args(text: str) -> dict[str, str]:
    """Parse ``ARG NAME=default`` declarations from a Dockerfile."""
    args: dict[str, str] = {}
    for match in re.finditer(r"^\s*ARG\s+(\w+)=([^\s]+)", text, re.MULTILINE):
        args[match.group(1)] = match.group(2)
    return args


def _collect_dockerfile_images(root: Path) -> set[str]:
    """Return the concrete base images from every Dockerfile the repo ships."""
    images: set[str] = set()
    for dockerfile in root.glob("**/Dockerfile"):
        if "node_modules" in dockerfile.parts:
            continue
        text = dockerfile.read_text(encoding="utf-8")
        args = _dockerfile_args(text)
        for match in re.finditer(r"^\s*FROM\s+(\S+)", text, re.MULTILINE):
            resolved = _resolve(match.group(1), args)
            if resolved and resolved.upper() != "SCRATCH":
                images.add(resolved)
    return images


def _collect_devcontainer_images(root: Path) -> set[str]:
    """Return the base image and feature refs from the devcontainer bundle."""
    images: set[str] = set()
    dc = root / "bundles" / "devcontainer" / ".devcontainer" / "devcontainer.json"
    if not dc.is_file():
        return images
    # devcontainer.json allows // comments; strip them before JSON parsing.
    stripped = re.sub(r"^\s*//.*$", "", dc.read_text(encoding="utf-8"), flags=re.MULTILINE)
    data = json.loads(stripped)
    if isinstance(data.get("image"), str):
        images.add(data["image"])
    for feature in data.get("features") or {}:
        images.add(feature)
    return images


# ---------------------------------------------------------------------------
# Registry existence check
# ---------------------------------------------------------------------------


def _parse_ref(ref: str) -> tuple[str, str, str]:
    """Split an image ref into (registry, repository, tag-or-digest)."""
    if "@" in ref:
        name, reference = ref.rsplit("@", 1)
    elif ":" in ref.rsplit("/", 1)[-1]:
        name, reference = ref.rsplit(":", 1)
    else:
        name, reference = ref, "latest"

    first = name.split("/", 1)[0]
    if "/" in name and ("." in first or ":" in first or first == "localhost"):
        registry, repository = name.split("/", 1)
    else:
        registry = "registry-1.docker.io"
        repository = name if "/" in name else f"library/{name}"
    return registry, repository, reference


def _manifest_status(ref: str, timeout: int = 20) -> int | None:
    """Return the HTTP status for a manifest HEAD-style GET, or None on network error.

    Follows the standard OCI token flow: an unauthenticated request that returns
    401 carries a ``WWW-Authenticate`` header pointing at a token endpoint; we
    fetch a pull token and retry. Works uniformly for ghcr.io, Docker Hub,
    gcr.io and quay.io; anonymous registries (mcr.microsoft.com) answer directly.
    """
    registry, repository, reference = _parse_ref(ref)
    url = f"https://{registry}/v2/{repository}/manifests/{urllib.parse.quote(reference, safe=':@')}"

    def fetch_manifest_status(token: str | None) -> int:
        """Fetch the manifest (optionally with a bearer token) and return the HTTP status."""
        req = urllib.request.Request(url, method="GET")  # noqa: S310 - https only, host from repo config
        req.add_header("Accept", _MANIFEST_ACCEPT)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310  # nosec B310
            return resp.status

    try:
        try:
            return fetch_manifest_status(None)
        except urllib.error.HTTPError as exc:
            if exc.code != 401:
                return exc.code
            challenge = exc.headers.get("WWW-Authenticate", "")
            realm = re.search(r'realm="([^"]+)"', challenge)
            if not realm:
                return 401
            params = {
                key: match.group(1)
                for key, match in (
                    ("service", re.search(r'service="([^"]+)"', challenge)),
                    ("scope", re.search(r'scope="([^"]+)"', challenge)),
                )
                if match
            }
            token_url = realm.group(1) + (f"?{urllib.parse.urlencode(params)}" if params else "")
            with urllib.request.urlopen(token_url, timeout=timeout) as tok_resp:  # noqa: S310  # nosec B310
                payload = json.load(tok_resp)
            token = payload.get("token") or payload.get("access_token")
            try:
                return fetch_manifest_status(token)
            except urllib.error.HTTPError as exc2:
                return exc2.code
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gitlab_project(root: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Assemble a synced gitlab-project once for the module."""
    dest = tmp_path_factory.mktemp("gitlab-project")
    return _assemble_gitlab_project(root, dest)


def _run_gitlab_ci_local(project: Path, *args: str) -> subprocess.CompletedProcess:
    """Invoke a pinned gitlab-ci-local against the assembled project."""
    assert _NPX is not None, "npx is required to run gitlab-ci-local"
    return subprocess.run(  # nosec B603
        [_NPX, "--yes", f"gitlab-ci-local@{GITLAB_CI_LOCAL_VERSION}", *args],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=600,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pipeline_images_exist(gitlab_project: Path, root: Path) -> None:
    """Every container image the GitLab pipeline / Dockerfiles reference must exist.

    Guards against the class of bug where a pinned tag is retired upstream (e.g.
    the removed ``ghcr.io/astral-sh/uv:*-bookworm`` tags). A definitive 404/absent
    fails the test; if no registry is reachable at all the test skips rather than
    flaking on a network outage.
    """
    images = (
        _collect_pipeline_images(gitlab_project) | _collect_dockerfile_images(root) | _collect_devcontainer_images(root)
    )
    assert images, "no container images discovered — collection logic is broken"

    missing: list[str] = []
    unreachable: list[str] = []
    reachable = 0
    for ref in sorted(images):
        status = _manifest_status(ref)
        if status is None:
            unreachable.append(ref)
        elif status == 200:
            reachable += 1
        elif status == 404:
            missing.append(f"{ref} -> HTTP {status}")
        else:
            unreachable.append(f"{ref} -> HTTP {status}")

    if missing:
        pytest.fail("Container image(s) do not exist on their registry:\n  " + "\n  ".join(missing))
    if reachable == 0:
        pytest.skip(f"no container registry reachable (checked {len(unreachable)} images); skipping")


@_skip_on_windows
@pytest.mark.skipif(_NPX is None, reason="npx (Node.js) not available; gitlab-ci-local cannot run")
def test_pipeline_schema_validates(gitlab_project: Path) -> None:
    """gitlab-ci-local must resolve every include and validate the merged schema.

    This is what catches a malformed job, a broken ``include:`` path, or a schema
    violation — the structural half that a plain image-existence check cannot see.
    """
    result = _run_gitlab_ci_local(gitlab_project, "--list")
    combined = result.stdout + result.stderr
    if result.returncode != 0 and re.search(r"getaddrinfo|ENOTFOUND|network|ECONNREFUSED", combined, re.I):
        pytest.skip(f"gitlab-ci-local could not fetch dependencies (offline):\n{combined[-500:]}")

    assert result.returncode == 0, f"gitlab-ci-local --list failed:\n{combined}"
    assert "json schema validated" in combined, f"schema was not validated:\n{combined}"
    # Sanity-check that the merged pipeline actually materialised jobs from the
    # included overlays (tests + pages), not an empty pipeline.
    assert re.search(r"\bci:test:", combined), f"expected ci:test jobs in merged pipeline:\n{combined}"
    assert "pages" in combined, f"expected the book/pages deploy job in merged pipeline:\n{combined}"


@pytest.mark.gitlab_exec
@_skip_on_windows
@pytest.mark.skipif(_DOCKER is None, reason="docker not available")
@pytest.mark.skipif(_NPX is None, reason="npx (Node.js) not available")
@pytest.mark.skipif(
    not os.environ.get("RHIZA_GITLAB_DOCKER"),
    reason="opt-in: set RHIZA_GITLAB_DOCKER=1 to run the Docker-backed GitLab job (pulls a large image)",
)
def test_pinned_uv_image_runs_in_docker(root: Path, tmp_path: Path) -> None:
    """The pinned ``$UV_IMAGE`` must actually pull and run a job under gitlab-ci-local.

    Proves the GitLab pipeline works end-to-end despite the repo being on GitHub:
    a synthetic single-job pipeline pinned to the *real* image from
    ``bundles/gitlab/.gitlab-ci.yml`` is executed in Docker and must run ``uv``.
    """
    variables = _collect_variables(root / "bundles" / "gitlab")
    uv_image = variables.get("UV_IMAGE")
    assert uv_image, "UV_IMAGE not found in bundles/gitlab/.gitlab-ci.yml"

    (tmp_path / ".gitlab-ci.yml").write_text(
        yaml.safe_dump({"smoke": {"image": uv_image, "script": ["uv --version"]}}, sort_keys=False),
        encoding="utf-8",
    )
    subprocess.run([_GIT, "init", "-q", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    subprocess.run([_GIT, "config", "user.email", "ci@example.invalid"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    subprocess.run([_GIT, "config", "user.name", "CI Smoke Test"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    subprocess.run([_GIT, "add", ".gitlab-ci.yml"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    subprocess.run([_GIT, "commit", "-q", "-m", "Initial commit"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603

    result = _run_gitlab_ci_local(tmp_path, "smoke")
    combined = result.stdout + result.stderr
    assert result.returncode == 0, f"gitlab-ci-local run of pinned uv image failed:\n{combined}"
    assert re.search(r"\buv\s+\d+\.\d+", combined), f"uv did not run inside {uv_image}:\n{combined}"
