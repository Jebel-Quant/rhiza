"""What `rhiza_docker.yml` enforces, and whether the file it ships survives it.

#1651, in a consumer taking the v1.7.0 bump: the job went red on two hadolint findings in
`docker/Dockerfile` -- a file the template writes and the consumer does not -- and then a
second time on `Path does not exist: trivy-results.sarif`, because the SARIF upload ran
under `always()` while the scan that writes that file had been skipped by the first
failure. One info-level style finding, two red steps, nothing to fix in the repo it
failed in.

**Neither failure was reachable before**, and that is the part worth keeping. The job
probes `[ -f docker/Dockerfile ]`; the bundle deployed to the repository *root* until
#1641, so the probe missed, the job printed its skip notice and went green having linted,
built and scanned nothing -- in every consumer that had adopted the bundle. The mother repo
has no `docker/` either (the image builds a Python distribution, and rhiza ships
configuration), so dogfooding never reached it. #1641 moved the file, v1.7.0 delivered the
move, and the job ran for the first time. Same silent-green shape as #1505, #1511, #1516
and #1535, and the same lesson: the fix is not enough on its own, because nothing here was
ever *asking* the question.

So this module asks it three ways, and only one of them needs docker:

* **The lint contract.** The threshold the step declares, not the one its comment claimed.
  hadolint-action's own default is `info`, so the commented-out `failure-threshold: error`
  the step used to carry described behaviour it did not have -- an accurate-looking comment
  is worse than none, because it stops the next reader checking.
* **The SARIF consumers.** Derived: whichever step *writes* the report is the step the
  uploads must wait for. Naming the producing step rather than the file keeps this true
  through a rename of either.
* **The shipped Dockerfile itself**, run through the real linter. The offline assertion
  about numeric UIDs pins the rule that actually fired (DL3066); the docker-gated one is
  the only thing here that would notice a *different* rule firing tomorrow.

The hadolint image is derived from the action pin in the workflow rather than pinned again
here. A second pin for the same tool is a second thing to bump, and the one that ages is
always the one no dependency bot reads -- #1579 and #1582 in this repo's own history. It
costs a network fetch, which is a skip and not a failure.
"""

from __future__ import annotations

import functools
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argument vectors, never shell=True
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_DOCKERFILE = _ROOT / "bundles" / "docker" / "docker" / "Dockerfile"
_WORKFLOW = _ROOT / ".github" / "workflows" / "rhiza_docker.yml"
_DOCKER = shutil.which("docker")

# hadolint's severity ladder. The action accepts any of them; `ignore` disables the gate
# entirely, which is why a declared threshold is checked against this list rather than
# merely for being present.
_THRESHOLDS = ("ignore", "style", "info", "warning", "error")

# The action the lint step uses, and where its own Dockerfile lives -- that file is what
# names the hadolint image, so the version this suite runs follows the pin above it.
_HADOLINT_ACTION = "hadolint/hadolint-action"
_ACTION_DOCKERFILE = "https://raw.githubusercontent.com/{repo}/{ref}/Dockerfile"

# `USER 10001`, not `USER app_user`: a name exists only inside the image, which is what
# DL3066 says and what Kubernetes' runAsNonRoot enforces by refusing to admit the pod.
_USER = re.compile(r"^\s*USER\s+(\S+)", re.MULTILINE)


@functools.lru_cache(maxsize=1)
def _job_steps() -> list[dict]:
    """Return the steps of the workflow's single job.

    Returns:
        Every step, in file order.
    """
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    jobs = list(workflow["jobs"].values())
    assert len(jobs) == 1, f"{_WORKFLOW.name} grew a second job; this module assumes one"
    return list(jobs[0]["steps"])


def _step_using(action: str) -> dict:
    """Return the one step that uses the given action.

    Args:
        action: The action's ``owner/repo``, without a ref.

    Returns:
        The step mapping.
    """
    matches = [step for step in _job_steps() if str(step.get("uses", "")).startswith(f"{action}@")]
    assert len(matches) == 1, f"expected exactly one step using {action}, found {len(matches)}"
    return matches[0]


def _declared_threshold() -> str:
    """Return the failure threshold the hadolint step passes to the action.

    Returns:
        The threshold, or an empty string when the step declares none.
    """
    return str(_step_using(_HADOLINT_ACTION).get("with", {}).get("failure-threshold", "")).strip()


def test_the_hadolint_step_declares_its_failure_threshold() -> None:
    """An undeclared threshold is `info`, whatever the step's comment says.

    This is the half of #1651 that is not about the Dockerfile at all. The action declares
    `failure-threshold` with a default of `info`, so leaving it out fails the job on every
    style-level nit in a consumer's own Dockerfile -- while the step carried a commented-out
    `failure-threshold: error` and the words "default behavior" beside it.
    """
    threshold = _declared_threshold()
    assert threshold, (
        "the hadolint step declares no failure-threshold, so the action's own default "
        "(info) applies and every info-level finding fails the job (#1651). Declare one "
        "rather than describing it in a comment."
    )
    assert threshold in _THRESHOLDS, f"failure-threshold: {threshold!r} is not one of {list(_THRESHOLDS)}"


def test_the_sarif_uploads_wait_for_the_scan_that_writes_them() -> None:
    """`always()` alone uploads a report that a skipped scan never wrote.

    Derived rather than restated: the producing step is whichever one names the report as
    its `output`, and every other step naming that file has to condition on *that* step's
    outcome. A rename of the step or of the file leaves this assertion true.
    """
    steps = _job_steps()
    producers = [step for step in steps if str(step.get("with", {}).get("output", "")).endswith(".sarif")]
    assert len(producers) == 1, f"expected exactly one step writing a SARIF report, found {len(producers)}"
    producer = producers[0]
    report = str(producer["with"]["output"])
    producer_id = producer.get("id")
    assert producer_id, f"the step writing {report} has no `id:`, so no other step can wait for it"

    consumers = [
        step
        for step in steps
        if step is not producer and any(report in str(value) for value in step.get("with", {}).values())
    ]
    assert consumers, f"no step consumes {report}; the pattern has gone stale"
    for step in consumers:
        condition = str(step.get("if", ""))
        assert f"steps.{producer_id}.outcome" in condition, (
            f"step {step.get('name')!r} consumes {report} under `if: {condition}`, which does "
            f"not require the {producer_id!r} step to have run. A failed lint or build skips "
            f"the scan, and this step then fails with `Path does not exist` (#1651)."
        )


def test_every_user_instruction_names_a_numeric_uid() -> None:
    """DL3066, the rule that actually fired, and the reason it is worth obeying.

    A named USER is unresolvable outside the image: hadolint reports it, and a Kubernetes
    kubelet with `runAsNonRoot` set refuses to admit the pod because it cannot verify the
    user is not root. Both readings want the number.
    """
    users = _USER.findall(_DOCKERFILE.read_text(encoding="utf-8"))
    assert users, f"no USER instruction in {_DOCKERFILE.name}; the image would run as root"
    named = [user for user in users if not user.isdigit()]
    assert not named, (
        f"{_DOCKERFILE.name} switches to {named}, which only exists inside the image. "
        f"hadolint reports DL3066 at info level and Kubernetes' runAsNonRoot cannot verify "
        f"it (#1651). Give useradd a `-u <uid>` and name the number here."
    )


@functools.lru_cache(maxsize=1)
def _hadolint_image() -> str:
    """Return the hadolint image the pinned action runs, read from the action itself.

    Returns:
        The image reference, or an empty string when the action could not be fetched.
    """
    uses = str(_step_using(_HADOLINT_ACTION)["uses"])
    ref = uses.split("@", 1)[1]
    url = _ACTION_DOCKERFILE.format(repo=_HADOLINT_ACTION, ref=ref)
    try:
        with urllib.request.urlopen(url, timeout=20) as response:  # noqa: S310  # nosec B310
            body = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError):
        return ""
    match = re.search(r"^FROM\s+(\S+)", body, re.MULTILINE)
    return match.group(1) if match else ""


@pytest.mark.skipif(_DOCKER is None, reason="docker is not installed")
def test_the_action_pin_still_names_a_hadolint_image() -> None:
    """The control for the derivation below.

    An action whose Dockerfile moved, or a network that is not there, returns an empty
    string -- and an empty image would make the run below fail for a reason that has
    nothing to do with the Dockerfile under test. Separating the two is what stops an
    outage reading as a lint failure, or a moved file reading as a pass.
    """
    if not _hadolint_image():
        pytest.skip("could not read the pinned hadolint-action's Dockerfile (offline?)")


@pytest.mark.skipif(_DOCKER is None, reason="docker is not installed")
def test_the_shipped_dockerfile_passes_the_linter_it_ships_with() -> None:
    """The assertion #1651 is actually about: the template's own file, the real linter.

    Zero findings at *any* severity, rather than none above the declared threshold. The
    threshold is what keeps a consumer's own Dockerfile from failing this job over a style
    nit; it is not a licence for the file rhiza writes into every consumer to carry
    findings that each of them then sees in their own CI output.
    """
    image = _hadolint_image()
    if not image:
        pytest.skip("could not read the pinned hadolint-action's Dockerfile (offline?)")

    result = subprocess.run(  # nosec B603
        [_DOCKER, "run", "--rm", "-i", image, "hadolint", "--no-fail", "--format", "json", "-"],
        input=_DOCKERFILE.read_text(encoding="utf-8"),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"could not run {image}: {result.stderr.strip() or result.stdout.strip()}")

    findings = json.loads(result.stdout or "[]")
    assert not findings, (
        f"{_DOCKERFILE.relative_to(_ROOT)} has {len(findings)} hadolint finding(s), which "
        f"every consumer's docker job reports against a file they did not write (#1651): "
        + "; ".join(f"L{item['line']} {item['code']} {item['level']}: {item['message']}" for item in findings)
    )
