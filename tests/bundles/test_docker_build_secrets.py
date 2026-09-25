"""How a private dependency's credential reaches the image build, and how it must not.

#1691: `rhiza_docker.yml` runs `uv sync` *inside* the builder stage of the Dockerfile the
`docker` bundle ships. The runner-side `configure-git-auth` step every other workflow uses
writes a `git config --global` the build stage never sees, so #1690 -- which forwards
`GH_PAT` to every reusable workflow by name -- could fix nothing here. The credential has
to cross the container boundary, and *how* it crosses is the whole point of this module:

* **As a BuildKit secret, never a build arg.** A `--build-arg` is recorded in the image and
  readable with `docker history`; a `--mount=type=secret` exists only for the instruction
  that mounts it and lands in no layer. The first test forbids the former by name shape.
* **Derived, both ways.** The secret ids the workflow passes and the ids the Dockerfile
  mounts must be the same set -- a secret passed but never mounted is silently unused, one
  mounted but never passed is silently empty -- and each one the workflow passes must come
  from a secret it declares under `workflow_call.secrets`, or #1690's parity breaks.
* **Readable by the build user.** BuildKit mounts a secret root-owned and mode 0400. The
  Dockerfile switches to `USER 10001` before the install, so a mount without `uid=` is an
  unreadable file and the build fails with `Permission denied` for exactly the consumer
  who set the secret. The uid is derived from the `USER` instruction, not restated.
* **Absent means no-op.** Each mounted secret is guarded by `[ -s /run/secrets/<id> ]`, so
  a project with no private dependencies -- and every fork PR, which receives no secrets --
  builds exactly as before.
* **Git is there to use it.** The slim base image ships no git, and a `[tool.uv.sources]`
  Git entry is fetched by shelling out to it; without this the credential is configured
  for a command that does not exist.
"""

from __future__ import annotations

import functools
import re
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_DOCKERFILE = _ROOT / "bundles" / "docker" / "docker" / "Dockerfile"
_WORKFLOW = _ROOT / ".github" / "workflows" / "rhiza_docker.yml"

# `--secret id=gh_pat,env=GH_PAT` on the buildx command line.
_PASSED_SECRET = re.compile(r"--secret\s+id=(?P<id>[a-z0-9_]+),env=(?P<env>[A-Z][A-Z0-9_]*)")
# `--mount=type=secret,id=gh_pat,uid=10001` on a RUN instruction; the option order is free.
_MOUNTED_SECRET = re.compile(r"--mount=type=secret,(?P<opts>[^\s\\]+)")
_ARG = re.compile(r"^\s*ARG\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
_USER = re.compile(r"^\s*USER\s+(\S+)", re.MULTILINE)
_FROM = re.compile(r"^\s*FROM\s", re.MULTILINE)
# An ARG whose name says it carries a credential.
_CREDENTIAL_LIKE = re.compile(r"TOKEN|PAT\b|SECRET|PASSWORD|PASSWD|CREDENTIAL|API_KEY|INDEX_URL", re.IGNORECASE)


def _dockerfile() -> str:
    """The shipped Dockerfile's text."""
    return _DOCKERFILE.read_text(encoding="utf-8")


def _builder_stage() -> str:
    """The text of the first stage -- everything before the second FROM."""
    text = _dockerfile()
    froms = list(_FROM.finditer(text))
    return text[: froms[1].start()] if len(froms) > 1 else text


@functools.lru_cache(maxsize=1)
def _build_step() -> dict:
    """The step that runs `docker buildx build`, found by what it does rather than its name."""
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    for job in workflow["jobs"].values():
        for step in job.get("steps") or []:
            if "docker buildx build" in (step.get("run") or ""):
                return step
    pytest.fail(f"{_WORKFLOW.name} has no step running `docker buildx build`")


def _declared_secrets() -> set[str]:
    """The names under `on.workflow_call.secrets`."""
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    triggers = workflow.get(True, workflow.get("on", {})) or {}
    return set((triggers.get("workflow_call") or {}).get("secrets") or {})


def _passed() -> dict[str, str]:
    """Secret id -> environment variable, as the buildx command line passes them."""
    return {m.group("id"): m.group("env") for m in _PASSED_SECRET.finditer(_build_step()["run"])}


def _mounted() -> dict[str, dict[str, str]]:
    """Secret id -> the mount's other options, as the Dockerfile mounts them."""
    mounts: dict[str, dict[str, str]] = {}
    for match in _MOUNTED_SECRET.finditer(_dockerfile()):
        opts = dict(opt.split("=", 1) for opt in match.group("opts").split(","))
        mounts[opts.pop("id")] = opts
    return mounts


def test_no_build_arg_carries_a_credential() -> None:
    """A build arg is written into the image; `docker history` reads it back out."""
    offending = [name for name in _ARG.findall(_dockerfile()) if _CREDENTIAL_LIKE.search(name)]
    assert not offending, (
        f"{_DOCKERFILE.relative_to(_ROOT)} declares ARG {offending}. A build argument is recorded in "
        "the image metadata and readable with `docker history`, so a token passed that way ships "
        "inside every image built from it. Pass it as a BuildKit secret and mount it (#1691)."
    )


def test_the_workflow_passes_secrets_and_the_dockerfile_mounts_the_same_ones() -> None:
    """Passed but unmounted is silently unused; mounted but unpassed is silently empty."""
    passed, mounted = set(_passed()), set(_mounted())
    assert passed, f"{_WORKFLOW.name}'s build step passes no `--secret id=...,env=...`"
    assert passed == mounted, (
        f"{_WORKFLOW.name} passes secrets {sorted(passed)} but {_DOCKERFILE.name} mounts "
        f"{sorted(mounted)} -- passed only: {sorted(passed - mounted)}, mounted only: "
        f"{sorted(mounted - passed)}. Neither half works without the other, and neither fails "
        "visibly on its own."
    )


def test_every_passed_secret_comes_from_a_declared_workflow_secret() -> None:
    """The env each `--secret` reads must be set from a secret the workflow declares (#1690)."""
    env = _build_step().get("env") or {}
    declared = _declared_secrets()
    problems = []
    for secret_id, var in _passed().items():
        if var not in env:
            problems.append(f"{secret_id}: env {var} is not set on the build step")
        elif env[var] != f"${{{{ secrets.{var} }}}}":
            problems.append(f"{secret_id}: env {var} is {env[var]!r}, not ${{{{ secrets.{var} }}}}")
        if var not in declared:
            problems.append(f"{secret_id}: {var} is not declared under workflow_call.secrets")
    assert not problems, f"{_WORKFLOW.name}:\n  " + "\n  ".join(problems)


def test_secret_mounts_are_readable_by_the_build_user() -> None:
    """BuildKit's default is a root-owned 0400 file, which the non-root build user cannot read."""
    users = _USER.findall(_builder_stage())
    assert users, "the builder stage never switches user; the secret-mount uid has nothing to match"
    uid = users[-1]
    wrong = {sid: opts.get("uid") for sid, opts in _mounted().items() if opts.get("uid") != uid}
    assert not wrong, (
        f"{_DOCKERFILE.name} runs the install as USER {uid} but mounts {wrong} -- each mount needs "
        f"`uid={uid}`, or the secret is a root-owned 0400 file and the build fails with "
        "`Permission denied` precisely for the consumer who configured the secret."
    )


def test_an_absent_secret_is_a_no_op() -> None:
    """Each mount is consulted only through a `[ -s /run/secrets/<id> ]` guard."""
    text = _dockerfile()
    unguarded = [sid for sid in _mounted() if f"[ -s /run/secrets/{sid} ]" not in text]
    assert not unguarded, (
        f"{_DOCKERFILE.name} mounts {unguarded} without an `[ -s /run/secrets/<id> ]` guard. An "
        "undefined secret arrives as an empty file; reading it unconditionally configures git "
        "with an empty token and breaks the build for every project with no private dependencies."
    )


def test_the_builder_stage_has_git() -> None:
    """A `[tool.uv.sources]` Git entry is fetched by shelling out to git; slim images ship none."""
    assert re.search(r"apt-get install[^\n\\]*\bgit\b", _builder_stage()), (
        f"the builder stage of {_DOCKERFILE.name} installs no git. The `uv` slim image is built on "
        "python:*-slim, which has none, so a private Git dependency fails with `git: command not "
        "found` before the mounted credential is ever consulted."
    )
