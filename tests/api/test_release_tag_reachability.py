"""Behavioural tests for the release workflow's tag-reachability guard (issue #1454).

The ``Validate Tag`` job used to check only that a release did not already exist and
that the version was strictly newer than the highest tag. Neither is reachability, so
a tag on a dangling commit passed both. That happens routinely: cut a release on a
branch, squash-merge the PR, and the bump content lands on the default branch under a
new SHA while the tag stays on the pre-squash commit. The tag is then orphaned —
``git describe`` skips the release, and regenerating ``CHANGELOG.md`` with git-cliff
silently deletes that version's section, because git-cliff cannot place a boundary at
a tag it cannot reach.

These tests run the guard's actual shell script — lifted out of the workflow YAML — in
purpose-built repositories, so a rewrite that keeps the step name but breaks the logic
still fails here. Asserting on the ``::error::``/``::warning::`` annotations rather
than on the exit code alone keeps the operator-facing message part of the contract.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - building throwaway git repos for the guard to inspect
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_GIT = shutil.which("git") or "/usr/bin/git"
_BASH = shutil.which("bash")

# Deterministic authorship, so the fixtures never depend on a configured git user.
# Everything else is inherited: pinning PATH would strip `git` from the Git Bash
# environment used on Windows runners, where the interpreter and the tools it calls
# live outside the POSIX prefixes.
_GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "rhiza-test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "rhiza-test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}

_STEP_NAME = "Ensure the tagged commit is reachable from a branch"
_LIVE_WORKFLOW = _ROOT / ".github" / "workflows" / "rhiza_release.yml"
_BUNDLE_WORKFLOW = _ROOT / "bundles" / "github" / ".github" / "workflows" / "rhiza_release.yml"


def _guard_script(workflow: Path) -> str:
    """Return the ``run:`` body of the reachability step in a release workflow."""
    jobs = yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]
    steps = jobs["tag"]["steps"]
    matching = [step["run"] for step in steps if step.get("name") == _STEP_NAME]
    assert len(matching) == 1, (
        f"{workflow.relative_to(_ROOT)}: expected exactly one '{_STEP_NAME}' step in the "
        f"tag job, found {len(matching)} (issue #1454)"
    )
    return matching[0]


def _git(*args: str, cwd: Path) -> str:
    """Run a git command in ``cwd`` and return its stdout."""
    result = subprocess.run(  # nosec B603
        [_GIT, *args], cwd=cwd, capture_output=True, text=True, check=True, env={**os.environ, **_GIT_IDENTITY}
    )
    return result.stdout


def _commit(repo: Path, message: str, content: str) -> None:
    """Write a file and commit it, so each commit has a distinct tree."""
    (repo / "file.txt").write_text(content, encoding="utf-8")
    _git("add", "-A", cwd=repo)
    _git("commit", "-qm", message, cwd=repo)


def _run_guard(script: str, repo: Path, tag: str, default_branch: str = "main") -> subprocess.CompletedProcess:
    """Execute the guard script against ``repo`` the way the workflow would."""
    assert _BASH is not None  # guarded by the skipif on the class
    return subprocess.run(  # nosec B603
        [_BASH, "-c", script],
        cwd=repo,
        capture_output=True,
        text=True,
        env={**os.environ, **_GIT_IDENTITY, "TAG": tag, "DEFAULT_BRANCH": default_branch},
    )


@pytest.fixture(scope="module")
def guard() -> str:
    """The guard script as shipped in the bundle (what downstream repos run)."""
    return _guard_script(_BUNDLE_WORKFLOW)


@pytest.fixture
def origin(tmp_path: Path) -> Path:
    """A bare ``origin`` with a single commit on ``main``, plus a clone to work in."""
    bare = tmp_path / "origin.git"
    _git("init", "--bare", "-q", "--initial-branch=main", str(bare), cwd=tmp_path)

    seed = tmp_path / "seed"
    seed.mkdir()
    _git("init", "-q", "--initial-branch=main", cwd=seed)
    _commit(seed, "initial", "one")
    _git("remote", "add", "origin", str(bare), cwd=seed)
    _git("push", "-q", "origin", "main", cwd=seed)
    return bare


@pytest.fixture
def clone(tmp_path: Path, origin: Path) -> Path:
    """A fresh clone of ``origin`` — the shape the release job checks out."""
    work = tmp_path / "work"
    _git("clone", "-q", str(origin), str(work), cwd=tmp_path)
    return work


class TestGuardIsWiredIntoBothWorkflows:
    """The guard must exist, and the two copies of it must not drift apart."""

    def test_live_and_bundle_workflows_share_one_guard(self) -> None:
        """The mother repo's live workflow and the synced bundle must run the same check.

        The two files differ by design (SHA-pinned actions here, tag-pinned downstream),
        so nothing byte-compares them — but a guard that exists only upstream protects
        exactly the repo that never had the problem.
        """
        assert _guard_script(_LIVE_WORKFLOW) == _guard_script(_BUNDLE_WORKFLOW)

    def test_guard_runs_before_the_release_is_built(self) -> None:
        """The check belongs in the ``tag`` job, which every later job depends on."""
        workflow = yaml.safe_load(_BUNDLE_WORKFLOW.read_text(encoding="utf-8"))
        for name, job in workflow["jobs"].items():
            if name == "tag":
                continue
            needs = job.get("needs", [])
            needs = [needs] if isinstance(needs, str) else needs
            assert needs, f"job '{name}' has no needs — it would run even if tag validation failed"


@pytest.mark.skipif(
    _BASH is None or sys.platform == "win32",
    reason=(
        "the guard is a GitHub Actions `run:` step, and the release job it belongs to runs on "
        "ubuntu-latest only — executing its shell through Git Bash would exercise the MSYS "
        "argument-translation layer rather than the guard. The structural tests above still run "
        "on every platform."
    ),
)
class TestTagReachability:
    """Run the guard against the three histories a release tag can have."""

    def test_tag_on_the_default_branch_passes(self, guard: str, clone: Path) -> None:
        """The normal case: the tag is an ancestor of the default branch."""
        _commit(clone, "chore: release v1.0.0", "two")
        _git("tag", "v1.0.0", cwd=clone)
        _git("push", "-q", "origin", "main", "v1.0.0", cwd=clone)

        result = _run_guard(guard, clone, "v1.0.0")

        assert result.returncode == 0, result.stdout + result.stderr
        assert "is an ancestor of main" in result.stdout
        assert "::warning::" not in result.stdout

    def test_orphaned_tag_from_a_squash_merge_fails(self, guard: str, clone: Path) -> None:
        """The observed failure: the tag sits on a pre-squash commit no branch contains.

        Reproduces ``Jebel-Quant/rhiza-hooks`` v0.7.0 — the release branch was
        squash-merged, so the bump landed on the default branch under a new SHA and the
        tag stayed behind on a commit that is now unreachable from every branch.
        """
        _git("checkout", "-q", "-b", "release", cwd=clone)
        _commit(clone, "Chore: bump version 0.9.0 → 1.0.0", "two")
        _git("tag", "v1.0.0", cwd=clone)
        _git("push", "-q", "origin", "v1.0.0", cwd=clone)  # tag only: the branch is never pushed

        # The squash-merge: same content, new SHA, on the default branch.
        _git("checkout", "-q", "main", cwd=clone)
        _commit(clone, "Chore: bump version 0.9.0 → 1.0.0 (#42)", "two")
        _git("push", "-q", "origin", "main", cwd=clone)
        _git("branch", "-qD", "release", cwd=clone)

        result = _run_guard(guard, clone, "v1.0.0")

        assert result.returncode == 1, result.stdout + result.stderr
        assert "::error::" in result.stdout
        assert "which no branch contains" in result.stdout
        assert "re-tag the merged commit" in result.stdout

    def test_tag_on_a_non_default_branch_warns_but_passes(self, guard: str, clone: Path) -> None:
        """A maintenance release is legitimate; only the changelog caveat is reported.

        Failing here would break hotfix releases cut from a maintenance branch, which
        are not the defect: the commit is reachable, so nothing is orphaned. The
        warning records that a changelog regenerated from the default branch still
        will not see this release.
        """
        _git("checkout", "-q", "-b", "maintenance-1.x", cwd=clone)
        _commit(clone, "chore: release v1.0.1", "two")
        _git("tag", "v1.0.1", cwd=clone)
        _git("push", "-q", "origin", "maintenance-1.x", "v1.0.1", cwd=clone)

        result = _run_guard(guard, clone, "v1.0.1")

        assert result.returncode == 0, result.stdout + result.stderr
        assert "::warning::" in result.stdout
        assert "origin/maintenance-1.x" in result.stdout
        assert "::error::" not in result.stdout

    def test_unresolvable_default_branch_fails_closed(self, guard: str, clone: Path) -> None:
        """A default branch the guard cannot resolve must stop the release, not skip it.

        Fetching or naming the default branch can fail; silently treating that as
        "reachable" would disable the guard exactly when history is unusual.
        """
        _commit(clone, "chore: release v1.0.0", "two")
        _git("tag", "v1.0.0", cwd=clone)
        _git("push", "-q", "origin", "main", "v1.0.0", cwd=clone)

        result = _run_guard(guard, clone, "v1.0.0", default_branch="trunk")

        assert result.returncode == 1, result.stdout + result.stderr
        assert "Cannot resolve the default branch" in result.stdout
