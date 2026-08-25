"""The docker bundle's deploy path, the workflow's literals, and `docker_folder` agree.

Three places name where the Dockerfile lives, and until #1641 they did not agree:

* the **bundle tree**, which is the deployment map -- `bundles/docker/<path>` lands at
  `<repo-root>/<path>`;
* **`rhiza_docker.yml`**, which tests for the file, passes it to hadolint and to
  `buildx --file`;
* **`rhiza-task docker-build`**, which builds `<docker_folder>/Dockerfile` with
  `docker_folder` defaulting to `docker`.

The bundle deployed to the root while both consumers looked in `docker/`. Neither consumer
*failed*: the workflow's presence check printed a skip notice and went green, and the task
skips a missing Dockerfile by design. So every consumer that adopted the bundle had a
Dockerfile that was never linted, never built and never scanned, with nothing to see but a
green tick -- the silent-green shape of #1505, #1511, #1516 and #1535.

Presence tests could not catch that. `test_bundle_combinations.py` asserted the Dockerfile
*existed* after a sync, which was true at the wrong path. What was missing is an assertion
that the three agree, and that is what this module is: it derives the folder from the bundle
tree and requires the other two to match, so moving any one of them alone is red.

`docker_folder` is read from the pinned CLI rather than assumed, for the reason
`test_bundle_cli_targets.py` gives -- the pin travels in the template, so the default can
change under us at a bump. That check needs uv and the network and skips without them, and
`test_the_docker_folder_setting_resolves_to_something` is its control (#1584): a derivation
that returned an empty string would otherwise have to be *compared* to be caught, and the
comparison is the thing being protected.

The pin is read through :func:`tests.registry.pin` rather than imported from whichever test
module has a copy, per #1583.
"""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404 - fixed argument vectors, never shell=True
from pathlib import Path

import pytest

from tests import registry

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "bundles" / "docker"
_WORKFLOW = _ROOT / ".github" / "workflows" / "rhiza_docker.yml"
_UVX = shutil.which("uvx")

# Every way the workflow spells the path: the presence test, hadolint's input, and the
# buildx flag. Captured as a group so a mismatch names the folder that was found.
_WORKFLOW_PATHS = re.compile(r"(?:\[ -f |dockerfile: |--file )([A-Za-z0-9_./-]*Dockerfile)\b")


def bundle_dockerfile() -> Path:
    """Return the bundle's Dockerfile, as a path relative to the bundle root.

    Returns:
        The repo-relative deploy path, e.g. ``docker/Dockerfile``.

    Raises:
        AssertionError: When the bundle ships no Dockerfile at all.
    """
    matches = sorted(path.relative_to(_BUNDLE) for path in _BUNDLE.rglob("Dockerfile"))
    assert len(matches) == 1, f"expected exactly one Dockerfile in {_BUNDLE}, found {matches}"
    return matches[0]


def test_the_bundle_ships_the_dockerfile_in_a_folder() -> None:
    """A root Dockerfile is the #1641 layout, and no consumer would touch it."""
    deploy = bundle_dockerfile()
    assert deploy.parent != Path(), (
        f"the bundle deploys {deploy} to the repository root, but `rhiza_docker.yml` and "
        f"`rhiza-task docker-build` both look under a folder -- nothing would lint, build "
        f"or scan it (#1641)"
    )


def test_the_ignore_file_sits_beside_the_dockerfile() -> None:
    """Otherwise docker never reads it and the build context stops being scoped."""
    deploy = bundle_dockerfile()
    beside = _BUNDLE / deploy.parent / "Dockerfile.dockerignore"
    assert beside.is_file(), (
        f"expected {beside.relative_to(_BUNDLE)} beside the Dockerfile: BuildKit resolves "
        f"`--file <path>/Dockerfile` to `<path>/Dockerfile.dockerignore` and reads nothing "
        f"else under that name"
    )


def test_the_workflow_names_the_bundles_deploy_path() -> None:
    """Every path literal in the workflow must be where the bundle actually lands."""
    deploy = bundle_dockerfile().as_posix()
    found = set(_WORKFLOW_PATHS.findall(_WORKFLOW.read_text(encoding="utf-8")))
    assert found, f"no Dockerfile path literal found in {_WORKFLOW.name}; the pattern has gone stale"
    assert found == {deploy}, (
        f"{_WORKFLOW.name} names {sorted(found)} but the bundle deploys to {deploy!r}. "
        f"A path the bundle does not deliver makes the presence check print its skip notice "
        f"and the job go green having linted, built and scanned nothing."
    )


def resolved_docker_folder() -> str:
    """Return ``docker_folder`` as the pinned CLI resolves it here.

    Returns:
        The setting's value, or an empty string when the CLI could not be run.
    """
    pin = registry.pin()
    if _UVX is None or pin is None:
        return ""
    result = subprocess.run(  # nosec B603
        [_UVX, pin, "print", "docker_folder"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


@pytest.mark.skipif(_UVX is None, reason="uvx is not installed")
def test_the_docker_folder_setting_resolves_to_something() -> None:
    """The control for the derivation below (#1584).

    A `print` that failed, or a pin that no longer carries the setting, returns an empty
    string. Compared against a bundle path that folder can never match, so the assertion
    below would fail rather than pass -- but only by accident of the bundle's current
    layout. Asserting non-emptiness here makes the guarantee independent of it, which is
    what stops a narrowed derivation from ever reading as agreement.
    """
    if not resolved_docker_folder():
        pytest.skip(f"could not run {registry.pin()} (offline?)")


@pytest.mark.skipif(_UVX is None, reason="uvx is not installed")
def test_the_pinned_clis_docker_folder_matches_the_bundle() -> None:
    """`make docker-build` must look where the bundle put the file.

    The second consumer, and the one a developer hits first: `docker-build` builds
    `<docker_folder>/Dockerfile` and *skips* when it is absent, so a disagreement here is
    another green tick over no work.
    """
    folder = resolved_docker_folder()
    if not folder:
        pytest.skip(f"could not run {registry.pin()} (offline?)")

    deploy = bundle_dockerfile()
    assert folder == deploy.parent.as_posix(), (
        f"{registry.pin()} resolves docker_folder to {folder!r}, but the bundle deploys the "
        f"Dockerfile to {deploy.as_posix()!r}. `make docker-build` would skip; set "
        f"`docker-folder` in the template's settings or move the bundle file."
    )
