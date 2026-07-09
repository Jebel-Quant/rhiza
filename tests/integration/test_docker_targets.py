"""Tests for the Docker Makefile targets and their resilience.

Mirrors test_presentation_targets.py: the docker bundle ships make targets
(docker-build, docker-run, docker-clean) in .rhiza/make.d/docker.mk, and this
exercises them end-to-end against a synced repo rather than relying solely on
static bundle-content checks.
"""

import shutil
import subprocess  # nosec

import pytest

MAKE = shutil.which("make") or "/usr/bin/make"


@pytest.fixture
def docker_makefile(git_repo):
    """Return the docker.mk path or skip tests if missing."""
    makefile = git_repo / ".rhiza" / "make.d" / "docker.mk"
    if not makefile.exists():
        pytest.skip("docker.mk not found, skipping test")
    return makefile


def test_docker_targets_defined(git_repo, docker_makefile):
    """Docker targets must be defined and parseable even without a docker/ folder.

    docker-build short-circuits when no Dockerfile exists, so a dry-run (-n)
    verifies make can resolve the targets without invoking the docker CLI.
    """
    assert not (git_repo / "docker").exists()

    for target in ["docker-build", "docker-run", "docker-clean"]:
        result = subprocess.run([MAKE, "-n", target], cwd=git_repo, capture_output=True, text=True)  # nosec
        assert "no rule to make target" not in result.stderr.lower(), (
            f"Target {target} should be defined in .rhiza/make.d/docker.mk"
        )
        assert result.returncode == 0, f"Dry-run of {target} failed: {result.stderr}"


def test_docker_phony_targets(docker_makefile):
    """docker.mk must declare the expected phony targets."""
    content = docker_makefile.read_text()

    phony_targets = [line.strip() for line in content.splitlines() if line.startswith(".PHONY:")]
    assert phony_targets, "expected at least one .PHONY declaration in docker.mk"

    all_targets = set()
    for phony_line in phony_targets:
        all_targets.update(phony_line.split(":")[1].strip().split())

    expected_targets = {"docker-build", "docker-run", "docker-clean"}
    assert expected_targets.issubset(all_targets), (
        f"Expected phony targets to include {expected_targets}, got {all_targets}"
    )


def test_docker_run_depends_on_build(docker_makefile):
    """docker-run must depend on docker-build so a run always builds first."""
    content = docker_makefile.read_text()
    assert "docker-run: docker-build" in content, "docker-run should declare docker-build as a prerequisite"


def test_docker_recipes_drive_docker_cli(docker_makefile):
    """The recipes must build, run, and remove the configured image via the docker CLI."""
    content = docker_makefile.read_text()
    assert "DOCKER_IMAGE_NAME" in content, "docker.mk should expose a configurable DOCKER_IMAGE_NAME"
    assert "docker buildx build" in content, "docker-build should build via 'docker buildx build'"
    assert "docker run" in content, "docker-run should launch the container via 'docker run'"
    assert "docker rmi" in content, "docker-clean should remove the image via 'docker rmi'"
