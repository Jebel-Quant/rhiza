"""Where ``dist-check`` runs: before every publish, and on every PR (#1743).

chebfun 0.11.0 declared ``license-files = ["LICENSE"]`` while its repository held
``LICENSE.rst``; the backend accepted it, the release went out, and the published metadata
carries no licence. The release workflows compared only the built *filenames* with the tag,
so nothing here could have seen it. rhiza-task's ``dist-check`` reads the artifacts back --
declared licence files packaged and recorded, and a wheel rebuilt from the sdist outside the
checkout agreeing with the rest -- and this module holds the four places that call it:

- both GitHub copies of the release workflow (the live one and the bundle's, which ships
  whole because PyPI Trusted Publishing validates the calling file), where it *replaces*
  ``uv build`` so the folder it validated is the folder that is uploaded;
- the GitLab release twin, the same way;
- ``rhiza_ci.yml`` and the GitLab quality pipeline, so the failure arrives on the PR rather
  than on release day.

The second half is the pin. A workflow runs whichever CLI its own ``RHIZA_TASK`` names, so
the wiring is only live once that version *has* the task. ``test_each_pinned_cli_has_dist_check``
asks each pin directly, and it is expected to fail until rhiza-task releases ``dist-check``
and the pins move -- the dependency stated as a red test rather than as a PR note.
"""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404 - fixed argument vectors, never shell=True
from functools import cache
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_UVX = shutil.which("uvx")

_GITHUB_RELEASES = (
    _ROOT / ".github" / "workflows" / "rhiza_release.yml",
    _ROOT / "bundles" / "github" / ".github" / "workflows" / "rhiza_release.yml",
)
_CI = _ROOT / ".github" / "workflows" / "rhiza_ci.yml"
_GITLAB_RELEASE = _ROOT / "bundles" / "gitlab" / ".gitlab" / "workflows" / "rhiza_release.yml"
_GITLAB_QUALITY = _ROOT / "bundles" / "gitlab" / ".gitlab" / "workflows" / "rhiza_quality.yml"

_STRICT = 'uvx "$RHIZA_TASK" dist-check --strict'
_PLAIN = 'uvx "$RHIZA_TASK" dist-check'

# A bare `uv build` on a line of its own: what dist-check replaced. Matched per line so the
# prose and messages that *mention* `uv build` in the verification step do not count.
_BARE_BUILD = re.compile(r"^\s*uv build\b", re.MULTILINE)


def _load(path: Path) -> dict:
    """Parse a workflow file.

    Args:
        path: The YAML file.

    Returns:
        Its top-level mapping.
    """
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _step_index(steps: list[dict], predicate) -> int:
    """Return the position of the single step matching a predicate.

    Args:
        steps: A job's steps.
        predicate: Called with each step.

    Returns:
        Its index.
    """
    found = [i for i, step in enumerate(steps) if predicate(step)]
    assert len(found) == 1, f"expected exactly one matching step, found {len(found)}"
    return found[0]


@pytest.mark.parametrize("path", _GITHUB_RELEASES, ids=lambda p: str(p.relative_to(_ROOT)))
def test_the_github_release_builds_through_dist_check(path: Path) -> None:
    """dist-check replaces ``uv build``, before the tag check and before the upload.

    Order is the property: the tag comparison reads the filenames dist-check left in
    ``dist/``, and the upload must carry exactly what was validated. ``--strict`` because a
    skip would mean nothing was built.

    Args:
        path: One of the two release workflow copies.
    """
    workflow = _load(path)
    assert workflow["env"]["RHIZA_TASK"].startswith("rhiza-task@")
    steps = workflow["jobs"]["build"]["steps"]

    build = _step_index(steps, lambda s: s.get("run", "").strip() == _STRICT)
    verify = _step_index(steps, lambda s: s.get("name") == "Verify built distribution matches the tag")
    upload = _step_index(steps, lambda s: s.get("name") == "Upload dist artifact")
    assert build < verify < upload
    assert steps[build]["if"] == "steps.buildable.outputs.buildable == 'true'"

    rebuilt = [s.get("name") for s in steps if _BARE_BUILD.search(s.get("run", ""))]
    assert not rebuilt, f"{rebuilt} build outside dist-check, so what is uploaded was not validated"


def test_ci_runs_dist_check_in_every_profile() -> None:
    """Its own job in standard/comprehensive, a step in lean's consolidated job.

    Both check out full history: a version derived from git needs the tags, or the sdist
    carries the fallback version and the check validates that consistently.
    """
    jobs = _load(_CI)["jobs"]
    job = jobs["dist-check"]
    assert [s["run"] for s in job["steps"] if "run" in s and "dist-check" in s["run"]] == [_PLAIN]
    for name in ("dist-check", "quality"):
        checkout = next(s for s in jobs[name]["steps"] if s.get("uses", "").startswith("actions/checkout@"))
        assert checkout["with"]["fetch-depth"] == 0, f"{name} must fetch the tags dist-check builds from"
    assert _PLAIN in [s.get("run") for s in jobs["quality"]["steps"]]
    assert "dist-check" in jobs["ci-gate"]["needs"]


def test_the_gitlab_release_builds_through_dist_check() -> None:
    """The GitLab twin carries the same replacement, and the pin it needs."""
    pipeline = _load(_GITLAB_RELEASE)
    assert pipeline["variables"]["RHIZA_TASK"].startswith("rhiza-task@")
    script = "\n".join(pipeline["release:build"]["script"])
    assert _STRICT in script
    assert not _BARE_BUILD.search(script), "release:build still runs uv build outside dist-check"
    assert script.index(_STRICT) < script.index("Built distribution verified")


def test_the_gitlab_quality_pipeline_runs_dist_check() -> None:
    """The PR-time half on GitLab, with the history a derived version needs."""
    job = _load(_GITLAB_QUALITY)["quality:dist-check"]
    assert _PLAIN in job["script"]
    assert job["variables"]["GIT_DEPTH"] == "0"


def _pins() -> list[str]:
    """Return every distinct ``rhiza-task@X.Y.Z`` the wired workflows pin.

    Returns:
        The pins, sorted.
    """
    found = set()
    for path in (*_GITHUB_RELEASES, _CI, _GITLAB_RELEASE, _GITLAB_QUALITY):
        found |= set(re.findall(r"rhiza-task@\d+\.\d+\.\d+", path.read_text(encoding="utf-8")))
    return sorted(found)


@cache
def _tasks(pin: str) -> frozenset[str] | None:
    """Ask a pinned CLI which tasks it has.

    Args:
        pin: A ``rhiza-task@X.Y.Z`` spec.

    Returns:
        The task names, or ``None`` when the CLI could not be run (offline).
    """
    assert _UVX is not None
    result = subprocess.run(  # nosec B603
        [_UVX, pin, "list", "--all"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=_ROOT,
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        return None
    return frozenset(line.split()[0] for line in result.stdout.splitlines() if line.strip())


def test_the_pin_scan_and_task_list_are_not_empty() -> None:
    """The control for the derivation below, which could otherwise pass by measuring nothing.

    An empty pin scan would parametrize zero cases -- green, and checking nothing -- so it
    must find at least one pin. And a task list read wrongly would be short rather than
    absent, so it must contain `setup`, which every pin since 0.3 carries; `dist-check`
    missing from a list that also lacks `setup` is a parse problem, not a release problem.
    """
    pins = _pins()
    assert pins, "no rhiza-task pin found in the workflows that call dist-check"
    if _UVX is None:
        pytest.skip("uvx not available; cannot ask the pinned CLI what it knows")
    tasks = _tasks(pins[0])
    if tasks is None:
        pytest.skip(f"could not run {pins[0]} (offline?)")
    assert "setup" in tasks, f"`{pins[0]} list --all` parsed to {sorted(tasks)}: the parser is wrong"


@pytest.mark.skipif(_UVX is None, reason="uvx not available; cannot ask the pinned CLI what it knows")
@pytest.mark.parametrize("pin", _pins())
def test_each_pinned_cli_has_dist_check(pin: str) -> None:
    """The wiring above is dead until the CLI it calls has the task.

    Args:
        pin: One pinned CLI version.
    """
    tasks = _tasks(pin)
    if tasks is None:
        pytest.skip(f"could not run {pin} (offline?)")
    assert "dist-check" in tasks, (
        f"{pin} has no `dist-check` task, so every workflow wired to it fails with an unknown "
        f"task. It ships in the rhiza-task release after Jebel-Quant/rhiza-task#212; bump every "
        f"RHIZA_TASK pin to that version (Renovate groups them into one PR)."
    )
