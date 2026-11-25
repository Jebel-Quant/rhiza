"""Behavioural tests for the weekly branch-protection drift check (#1817).

The committed ``.github/rulesets/main-branch-protection.json`` changes no live setting, and
every other test reads the file -- so a ruleset nobody re-applied looked correct everywhere
except on GitHub. The live ruleset here kept requiring five contexts #1744 removed and never
required ``E2E gate`` (#1813). The ``ruleset-drift`` job compares the two every week.

These tests run the job's actual scripts, lifted out of the workflow YAML: the fetch step
against a fake ``gh`` on ``PATH``, the comparison against fixture rulesets. A rewrite that
keeps the step names but breaks the logic still fails here. The property guarded hardest is
the one this repository has been burnt by most: the check must not pass by measuring
nothing, so an API error fails while only a genuinely absent ruleset skips.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess  # nosec B404 - runs the workflow's own scripts against fixtures
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_WEEKLY = _ROOT / ".github" / "workflows" / "rhiza_weekly.yml"
_BASH = shutil.which("bash")
_RULESET_FILE = ".github/rulesets/main-branch-protection.json"


def _job() -> dict:
    """Return the ``ruleset-drift`` job of the reusable weekly workflow."""
    jobs = yaml.safe_load(_WEEKLY.read_text(encoding="utf-8"))["jobs"]
    assert "ruleset-drift" in jobs, "rhiza_weekly.yml has no ruleset-drift job"
    return jobs["ruleset-drift"]


def _step(name: str) -> dict:
    """Return the job's step with the given name."""
    matching = [step for step in _job()["steps"] if step.get("name") == name]
    assert len(matching) == 1, f"expected one '{name}' step in ruleset-drift, found {len(matching)}"
    return matching[0]


def _ruleset(*contexts: str) -> dict:
    """Return a minimal ruleset requiring the given status-check contexts."""
    return {
        "name": "main-branch-protection",
        "rules": [
            {"type": "deletion"},
            {
                "type": "required_status_checks",
                "parameters": {"required_status_checks": [{"context": c} for c in contexts]},
            },
        ],
    }


def _outputs(path: Path) -> dict[str, str]:
    """Parse a ``$GITHUB_OUTPUT`` file into a mapping."""
    if not path.exists():
        return {}
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)


@pytest.mark.skipif(_BASH is None or sys.platform == "win32", reason="needs a POSIX bash for the fake gh")
class TestFetchStep:
    """The fetch step skips only when there is nothing to compare, and fails on anything else."""

    @staticmethod
    def _run(tmp_path: Path, *, with_file: bool, ids: str = "", gh_fails: bool = False) -> subprocess.CompletedProcess:
        """Run the fetch script in a scratch repository with a fake ``gh``."""
        repo = tmp_path / "repo"
        repo.mkdir()
        if with_file:
            (repo / _RULESET_FILE).parent.mkdir(parents=True)
            (repo / _RULESET_FILE).write_text(json.dumps(_ruleset("CI gate")), encoding="utf-8")

        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        live = tmp_path / "live.json"
        live.write_text(json.dumps(_ruleset("CI gate")), encoding="utf-8")
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(
            "#!/usr/bin/env bash\n"
            f'if [ "{int(gh_fails)}" = 1 ]; then echo "HTTP 403" >&2; exit 1; fi\n'
            'case "$*" in\n'
            f"  *--paginate*) printf '%s' '{ids}' ;;\n"
            f'  *) cat "{live}" ;;\n'
            "esac\n",
            encoding="utf-8",
        )
        fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IXUSR)

        runner_temp = tmp_path / "runner-temp"
        runner_temp.mkdir()
        env = {
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "GITHUB_OUTPUT": str(tmp_path / "output"),
            "GITHUB_REPOSITORY": "owner/repo",
            "RUNNER_TEMP": str(runner_temp),
            **_step("Fetch the live ruleset").get("env", {}),
        }
        env.pop("GH_TOKEN", None)  # the workflow expression, not a value
        assert _BASH is not None
        return subprocess.run(  # nosec B603
            [_BASH, "-c", _step("Fetch the live ruleset")["run"]],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_no_ruleset_file_skips_with_a_notice(self, tmp_path: Path) -> None:
        """A repository that ships no ruleset has nothing to drift from."""
        result = self._run(tmp_path, with_file=False)
        assert result.returncode == 0, result.stderr
        assert "::notice::" in result.stdout
        assert _outputs(tmp_path / "output")["skip"] == "true"

    def test_no_applied_ruleset_skips_with_a_notice(self, tmp_path: Path) -> None:
        """A consumer that never applied the ruleset is not drifting; say so and skip."""
        result = self._run(tmp_path, with_file=True, ids="")
        assert result.returncode == 0, result.stderr
        assert "::notice::" in result.stdout
        assert _outputs(tmp_path / "output")["skip"] == "true"

    def test_an_applied_ruleset_is_fetched_for_comparison(self, tmp_path: Path) -> None:
        """One live ruleset of that name: its JSON lands in RUNNER_TEMP and the compare step runs."""
        result = self._run(tmp_path, with_file=True, ids="17605978")
        assert result.returncode == 0, result.stderr
        outputs = _outputs(tmp_path / "output")
        assert outputs["skip"] == "false"
        assert outputs["id"] == "17605978"
        assert (tmp_path / "runner-temp" / "live-ruleset.json").exists()

    def test_two_rulesets_of_the_same_name_fail(self, tmp_path: Path) -> None:
        """Which ruleset is meant is ambiguous, and guessing would compare the wrong one."""
        result = self._run(tmp_path, with_file=True, ids="1\n2")
        assert result.returncode != 0
        assert "::error::" in result.stdout

    def test_an_api_error_fails_rather_than_skipping(self, tmp_path: Path) -> None:
        """The check must not go green by measuring nothing."""
        result = self._run(tmp_path, with_file=True, gh_fails=True)
        assert result.returncode != 0
        assert _outputs(tmp_path / "output").get("skip") != "true"


class TestCompareStep:
    """The comparison passes only when the live ruleset requires exactly the committed checks."""

    @staticmethod
    def _run(tmp_path: Path, committed: dict, live: dict) -> subprocess.CompletedProcess:
        """Run the comparison script against two fixture rulesets."""
        committed_path = tmp_path / "committed.json"
        live_path = tmp_path / "live.json"
        committed_path.write_text(json.dumps(committed), encoding="utf-8")
        live_path.write_text(json.dumps(live), encoding="utf-8")
        step = _step("Compare the required status checks")
        assert step.get("shell") == "python"
        env = {
            **os.environ,
            "RULESET_FILE": str(committed_path),
            "LIVE_FILE": str(live_path),
            "RULESET_ID": "17605978",
            "GITHUB_REPOSITORY": "owner/repo",
        }
        return subprocess.run(  # nosec B603
            [sys.executable, "-c", step["run"]], env=env, capture_output=True, text=True, check=False
        )

    def test_matching_checks_pass_in_any_order(self, tmp_path: Path) -> None:
        """Order is not drift: GitHub returns the contexts in its own order."""
        result = self._run(tmp_path, _ruleset("CI gate", "E2E gate"), _ruleset("E2E gate", "CI gate"))
        assert result.returncode == 0, result.stdout

    def test_a_check_missing_live_fails_and_names_it(self, tmp_path: Path) -> None:
        """The #1817 case: the file requires E2E gate and the live ruleset does not."""
        result = self._run(tmp_path, _ruleset("CI gate", "E2E gate"), _ruleset("CI gate"))
        assert result.returncode == 1
        assert "::error::" in result.stdout
        assert "E2E gate" in result.stdout
        assert "gh api --method PUT repos/owner/repo/rulesets/17605978" in result.stdout

    def test_a_stale_check_required_live_fails(self, tmp_path: Path) -> None:
        """The other half of #1817: contexts #1744 removed, still required live."""
        result = self._run(tmp_path, _ruleset("CI gate"), _ruleset("CI gate", "Pre-commit hooks"))
        assert result.returncode == 1
        assert "Pre-commit hooks" in result.stdout


class TestWiring:
    """The job runs where it must and cannot be silenced."""

    def test_comparison_runs_only_after_a_successful_fetch(self) -> None:
        """A skipped fetch skips the comparison; nothing else does."""
        assert _step("Compare the required status checks")["if"] == "steps.fetch.outputs.skip == 'false'"

    def test_the_job_is_not_allowed_to_fail_quietly(self) -> None:
        """Red is the signal on a schedule, as for the advisories job."""
        job = _job()
        assert "continue-on-error" not in job
        assert all("continue-on-error" not in step for step in job["steps"])

    def test_the_mother_ruleset_file_is_the_one_compared(self) -> None:
        """Both steps read the path GitHub's ruleset copy lives at."""
        assert _step("Fetch the live ruleset")["env"]["RULESET_FILE"] == _RULESET_FILE
        assert _step("Compare the required status checks")["env"]["RULESET_FILE"] == _RULESET_FILE
        assert (_ROOT / _RULESET_FILE).exists()
