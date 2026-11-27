"""Third-party pins must be immutable, and new releases must age before Renovate takes them.

Two supply-chain properties, both borrowed from fastapi/typer's setup:

- **Pre-commit hooks are pinned to a commit SHA, not a tag.** A tag is a movable pointer: a
  compromised upstream can re-point ``v1.2.3`` at new code, and every ``make fmt`` here and
  in every consumer runs it on the next cache miss. A SHA cannot move. The release it stands
  for is kept as a ``# frozen: <tag>`` comment, which is the format Renovate's pre-commit
  manager reads and rewrites (both the SHA and the comment, in one update). Workflow actions
  were already SHA-pinned; this extends the same rule to the hooks, root and bundled.
- **Renovate waits seven days before proposing a release** (``minimumReleaseAge``), so a
  compromised release has time to be yanked. Without it ``:automergeMinor`` could merge one
  within hours of publication. Rhiza's own packages are exempt: their flow is release, then
  bump the pin, and a week's wait only delays that.

The network test checks that each SHA is the commit its comment names. Renovate keeps the
two in step, but a hand edit can bump one and not the other, and the comment would then lie
about what runs.
"""

from __future__ import annotations

import functools
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argument vectors
from pathlib import Path

import pytest

from tests.util import frozen_revs

_ROOT = Path(__file__).resolve().parents[2]
_CONFIGS = [_ROOT / ".pre-commit-config.yaml", *sorted((_ROOT / "bundles").glob("*/.pre-commit-config.yaml"))]
_SHA = re.compile(r"[0-9a-f]{40}")

# Every renovate.json rhiza owns, mapped to the packages exempt from the release-age wait.
# Root: the two pinned CLIs plus the rhiza-hooks pre-commit repo. Bundle: consumers' only
# Jebel-Quant pin Renovate manages is pytest-rhiza; their hooks and rhiza-task arrive by sync.
_RENOVATE_EXEMPT = {
    "renovate.json": {"rhiza-task", "pytest-rhiza", "Jebel-Quant/rhiza-hooks"},
    "bundles/renovate/renovate.json": {"pytest-rhiza"},
}

_ALL_PINS = [
    pytest.param(config, repo, rev, tag, id=f"{config.relative_to(_ROOT)}:{repo.rsplit('/', 1)[-1]}")
    for config in _CONFIGS
    for repo, rev, tag in frozen_revs(config)
]


def test_the_scan_finds_the_pins_at_all() -> None:
    """Positive control: an empty parametrisation would pass every test below by skipping."""
    assert len(_CONFIGS) == 4, [str(c) for c in _CONFIGS]
    for config in _CONFIGS:
        assert frozen_revs(config), f"no hook revs found in {config}"


@pytest.mark.parametrize(("config", "repo", "rev", "tag"), _ALL_PINS)
def test_every_hook_is_frozen_to_a_sha(config: Path, repo: str, rev: str, tag: str | None) -> None:
    """Each rev is a full commit SHA carrying the ``# frozen: <tag>`` comment Renovate rewrites."""
    assert _SHA.fullmatch(rev), f"{config.name}: {repo} is pinned to {rev!r}, not a commit SHA"
    assert tag, f"{config.name}: {repo} has no '# frozen: <tag>' comment; Renovate needs it to update the pin"


@functools.cache
def _tag_commit(repo: str, tag: str) -> str | None:
    """Return the commit a tag points to, or None when the remote cannot be reached.

    Args:
        repo: The hook repository URL.
        tag: The tag name.

    Returns:
        The commit SHA (annotated tags dereferenced), or None on a network failure.
    """
    git = shutil.which("git")
    if git is None:
        return None
    try:
        out = subprocess.run(  # nosec B603
            [git, "ls-remote", repo, f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    refs = dict(reversed(line.split("\t")) for line in out.splitlines())
    return refs.get(f"refs/tags/{tag}^{{}}") or refs.get(f"refs/tags/{tag}")


@pytest.mark.parametrize(("config", "repo", "rev", "tag"), _ALL_PINS)
def test_the_sha_is_the_commit_the_comment_names(config: Path, repo: str, rev: str, tag: str | None) -> None:
    """A hand bump that moves the SHA or the comment alone makes the comment lie."""
    if tag is None:
        pytest.skip("not frozen; test_every_hook_is_frozen_to_a_sha reports it")
    commit = _tag_commit(repo, tag)
    if commit is None:
        pytest.skip(f"cannot resolve {repo}@{tag} (offline?)")
    assert rev == commit, f"{config.name}: {repo} '# frozen: {tag}' is {commit}, but rev is {rev}"


@pytest.mark.parametrize("path", sorted(_RENOVATE_EXEMPT))
class TestRenovateReleaseAge:
    """Renovate holds third-party releases back a week and nothing else."""

    @staticmethod
    def _config(path: str) -> dict:
        """Return the parsed renovate.json at a repo-relative path."""
        return json.loads((_ROOT / path).read_text(encoding="utf-8"))

    def test_waits_seven_days(self, path: str) -> None:
        """The cooldown is set at the top level, so every manager inherits it."""
        assert self._config(path).get("minimumReleaseAge") == "7 days"

    def test_does_not_treat_missing_timestamps_as_aged(self, path: str) -> None:
        """``timestamp-optional`` would let a release with no timestamp through on day one."""
        assert self._config(path).get("minimumReleaseAgeBehaviour", "timestamp-required") == "timestamp-required"

    def test_only_our_own_packages_are_exempt(self, path: str) -> None:
        """A rule that lifts the wait must name exactly rhiza's own packages."""
        rules = [r for r in self._config(path).get("packageRules", []) if "minimumReleaseAge" in r]
        exempt = {name for r in rules for name in r.get("matchPackageNames", [])}
        allowed_keys = {"description", "matchPackageNames", "minimumReleaseAge"}
        assert all(r["minimumReleaseAge"] == "0 days" and set(r) <= allowed_keys for r in rules)
        assert exempt == _RENOVATE_EXEMPT[path]
