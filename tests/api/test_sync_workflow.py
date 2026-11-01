"""Tests for the daily template-sync workflow (``rhiza_sync.yml``).

The reusable workflow lives in ``.github/workflows/`` and a daily stub in the ``github``
bundle calls it. It is ``/rhiza:update`` without Claude: compare ``ref`` in
``.rhiza/template.yml`` with the template's newest release, and when it is behind, bump
the ref, sync with rhiza-claude's scripts, and open a PR holding only template-owned files.

The structural tests pin the properties that make that PR safe to merge — staging from the
lock rather than ``git add --all``, the ``check-managed-files`` bypass on the sync commit,
the mother-repo guard. The behavioural tests lift the decision and the ref-rewrite shell out
of the YAML and run them, so a rewrite that keeps the step names but breaks the logic fails.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess  # nosec B404 - runs the workflow's own shell snippets
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_LIVE = _ROOT / ".github" / "workflows" / "rhiza_sync.yml"
_STUB = _ROOT / "bundles" / "github" / ".github" / "workflows" / "rhiza_sync.yml"
_BASH = shutil.which("bash")

_DECIDE_STEP = "Decide whether to sync"
_SYNC_STEP = "Bump the ref, sync and stage template-owned files"


def _load(path: Path) -> dict:
    """Return the parsed workflow at ``path``."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _triggers(doc: dict) -> dict:
    """Return the ``on:`` block (PyYAML parses a bare ``on`` key as ``True``)."""
    return doc.get("on") or doc.get(True) or {}


def _step_run(name: str) -> str:
    """Return the ``run:`` body of the named step in the live workflow's sync job."""
    steps = _load(_LIVE)["jobs"]["sync"]["steps"]
    matching = [step["run"] for step in steps if step.get("name") == name]
    assert len(matching) == 1, f"expected exactly one '{name}' step, found {len(matching)}"
    return matching[0]


class TestSyncStub:
    """The bundle stub runs daily and delegates to the reusable workflow."""

    def test_runs_daily_and_on_dispatch(self) -> None:
        """A daily cron plus manual dispatch: the whole point is a check every day."""
        triggers = _triggers(_load(_STUB))
        crons = [entry["cron"] for entry in triggers["schedule"]]
        assert len(crons) == 1
        _minute, _hour, dom, month, dow = crons[0].split()
        assert (dom, month, dow) == ("*", "*", "*"), f"{crons[0]!r} is not a daily schedule"
        assert "workflow_dispatch" in triggers

    def test_delegates_to_the_pinned_reusable_workflow(self) -> None:
        """The stub calls rhiza's reusable workflow at a release tag, forwarding GH_PAT by name."""
        job = _load(_STUB)["jobs"]["sync"]
        assert re.fullmatch(r"jebel-quant/rhiza/\.github/workflows/rhiza_sync\.yml@v\d+\.\d+\.\d+", job["uses"])
        assert job["secrets"] == {"GH_PAT": "${{ secrets.GH_PAT }}"}

    def test_grants_what_the_called_workflow_needs(self) -> None:
        """A caller cannot grant a called workflow less than it needs: push + open a PR."""
        permissions = _load(_STUB)["jobs"]["sync"]["permissions"]
        assert permissions == {"contents": "write", "pull-requests": "write"}


class TestSyncWorkflow:
    """The reusable workflow's safety properties."""

    def test_is_reusable(self) -> None:
        """It must be callable from the stub and declare the secret the stub maps."""
        call = _triggers(_load(_LIVE))["workflow_call"]
        assert call["secrets"]["GH_PAT"]["required"] is False

    def test_never_runs_on_the_mother_repo(self) -> None:
        """Rhiza is the template: it has no template.yml to bump."""
        assert "github.repository != 'jebel-quant/rhiza'" in _load(_LIVE)["jobs"]["sync"]["if"]

    def test_pins_the_sync_engine(self) -> None:
        """rhiza-claude is checked out at an exact tag, not a moving branch."""
        assert re.fullmatch(r"v\d+\.\d+\.\d+", _load(_LIVE)["env"]["RHIZA_CLAUDE_REF"])

    def test_stages_from_the_lock_only(self) -> None:
        """The PR may carry template-owned files only — stage_synced.py, never ``git add -A``."""
        script = _step_run(_SYNC_STEP)
        assert "stage_synced.py" in script
        assert not re.search(r"git add (-A|--all|\.)(\s|$)", script)

    def test_sync_commit_bypasses_check_managed_files(self) -> None:
        """The sync commit rewrites managed files wholesale, which is what that hook rejects."""
        assert "SKIP=check-managed-files git commit" in _step_run(_SYNC_STEP)

    def test_conflicts_take_upstream(self) -> None:
        """Exit 1 from sync.py means conflicts, resolved with resolve_conflicts.py."""
        assert "resolve_conflicts.py" in _step_run(_SYNC_STEP)


@pytest.mark.skipif(_BASH is None, reason="bash not available")
class TestDecision:
    """Run the decision step against (current, latest) pairs."""

    @staticmethod
    def _decide(tmp_path: Path, current: str, latest: str) -> tuple[str, str]:
        """Run the step and return (``sync`` output, annotations printed)."""
        output = tmp_path / "out"
        output.write_text("")
        env = {**os.environ, "CURRENT": current, "LATEST": latest, "GITHUB_OUTPUT": str(output)}
        result = subprocess.run(  # nosec B603
            [_BASH, "-c", _step_run(_DECIDE_STEP)], env=env, capture_output=True, text=True, check=True
        )
        values = dict(line.split("=", 1) for line in output.read_text().splitlines())
        return values["sync"], result.stdout

    @pytest.mark.parametrize(
        ("current", "latest", "expected"),
        [
            ("v1.9.0", "v1.10.0", "true"),
            ("v1.10.0", "v1.10.0", "false"),
            ("v1.11.0", "v1.10.0", "false"),
            ("v1.10.0", "v2.0.0", "false"),
            ("main", "v1.10.0", "false"),
        ],
    )
    def test_decision(self, tmp_path: Path, current: str, latest: str, expected: str) -> None:
        """Only a same-major, strictly newer release triggers a sync (sorted as versions, not text)."""
        sync, _ = self._decide(tmp_path, current, latest)
        assert sync == expected

    def test_major_bump_warns(self, tmp_path: Path) -> None:
        """A major bump is not silently skipped: it says to run /rhiza:update by hand."""
        _, stdout = self._decide(tmp_path, "v1.10.0", "v2.0.0")
        assert "::warning::" in stdout
        assert "major" in stdout


@pytest.mark.skipif(_BASH is None, reason="bash not available")
class TestRefRewrite:
    """The sed in the sync step rewrites only the top-level ref, whatever its quoting."""

    @staticmethod
    def _sed_line() -> str:
        """Return the ref-rewriting sed command from the sync step."""
        lines = [line.strip() for line in _step_run(_SYNC_STEP).splitlines() if line.strip().startswith("sed ")]
        assert len(lines) == 1
        # GNU sed's in-place flag on the runner; BSD sed (macOS) needs an explicit suffix.
        return lines[0].replace("sed -E -i ", "sed -E -i.bak ")

    @pytest.mark.parametrize("original", ['ref: "v1.9.0"', "ref: 'v1.9.0'", "ref: v1.9.0", 'template-branch: "v1.9.0"'])
    def test_rewrites_ref(self, tmp_path: Path, original: str) -> None:
        """Every accepted spelling ends as the new quoted tag; other keys are untouched."""
        rhiza = tmp_path / ".rhiza"
        rhiza.mkdir(exist_ok=True)
        template = rhiza / "template.yml"
        template.write_text(f'repository: "jebel-quant/rhiza"\n{original}\nprofiles:\n  - github-project\n')
        subprocess.run(  # nosec B603
            [_BASH, "-c", self._sed_line()],
            cwd=tmp_path,
            env={**os.environ, "LATEST": "v1.10.0"},
            check=True,
        )
        key = original.split(":")[0]
        assert template.read_text() == (
            f'repository: "jebel-quant/rhiza"\n{key}: "v1.10.0"\nprofiles:\n  - github-project\n'
        )
