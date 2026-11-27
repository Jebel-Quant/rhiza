"""The weekly online zizmor run: same tool version, same files, same config as the gate.

The `zizmor` pre-commit hook gates every pull request with ``--offline``. The weekly
``zizmor-online`` job in rhiza_weekly.yml adds the audits that need the GitHub API. It is
only useful if it audits what the gate audits with the version the gate uses, and if it
cannot go green by auditing nothing. Each test pins one of those properties.
"""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404
from pathlib import Path

import pytest
import yaml

from tests.util import ZIZMOR_HOOK_FILES

_ROOT = Path(__file__).resolve().parents[2]
_WEEKLY = _ROOT / ".github" / "workflows" / "rhiza_weekly.yml"
_PRE_COMMIT = _ROOT / ".pre-commit-config.yaml"


@pytest.fixture(scope="module")
def job() -> dict:
    """Return the `zizmor-online` job of the weekly workflow."""
    jobs = yaml.safe_load(_WEEKLY.read_text(encoding="utf-8"))["jobs"]
    assert "zizmor-online" in jobs, "rhiza_weekly.yml has no zizmor-online job"
    return jobs["zizmor-online"]


@pytest.fixture(scope="module")
def audit_step(job: dict) -> dict:
    """Return the step that runs zizmor."""
    steps = [step for step in job["steps"] if "zizmor@" in step.get("run", "")]
    assert len(steps) == 1, f"expected one step running zizmor, got {len(steps)}"
    return steps[0]


class TestWeeklyZizmor:
    """The weekly run is the online complement of the offline gate."""

    def test_runs_only_in_the_mother_repo(self, job: dict) -> None:
        """Consumers' copies of these workflows are fixed here, not in the consumer."""
        assert job.get("if") == "github.repository == 'jebel-quant/rhiza'"

    def test_runs_online(self, audit_step: dict) -> None:
        """A token enables the online audits; --offline would turn them off again."""
        assert audit_step.get("env", {}).get("GH_TOKEN") == "${{ github.token }}"
        assert "--offline" not in audit_step["run"]

    def test_uses_the_gate_config(self, audit_step: dict) -> None:
        """The same exceptions file as the hook, so both agree on what is a finding."""
        assert "--config .github/zizmor.yml" in audit_step["run"]

    def test_does_not_hardcode_a_version(self, audit_step: dict) -> None:
        """The version comes from the hook's rev; a literal here would drift from it."""
        assert not re.search(r"zizmor@\d", audit_step["run"]), "read the version from the hook's rev"

    def test_reads_the_hook_rev(self, audit_step: dict) -> None:
        """The job's awk program, run on the real config, yields the hook's rev."""
        awk = shutil.which("awk")
        if awk is None:
            pytest.skip("awk is not installed")
        program = re.search(r"awk '([^']+)'", audit_step["run"])
        assert program, "the job no longer reads the version with awk"
        result = subprocess.run([awk, program.group(1), str(_PRE_COMMIT)], capture_output=True, text=True, check=True)  # nosec B603
        config = yaml.safe_load(_PRE_COMMIT.read_text(encoding="utf-8"))
        (rev,) = [r["rev"] for r in config["repos"] if r["repo"].endswith("zizmorcore/zizmor-pre-commit")]
        assert result.stdout.strip() == rev

    def test_audits_the_hook_file_set(self, audit_step: dict) -> None:
        """The job's file pattern is the hook's upstream `files` pattern, verbatim."""
        match = re.search(r"pattern='([^']+)'", audit_step["run"])
        assert match, "the job no longer defines its file pattern"
        assert match.group(1) == ZIZMOR_HOOK_FILES

    def test_fails_rather_than_auditing_nothing(self, audit_step: dict) -> None:
        """An empty version or an empty file list is an error, not a green run."""
        run = audit_step["run"]
        assert 'if [ -z "$version" ]' in run
        assert '"${#files[@]}" -eq 0' in run
        assert run.count("exit 1") >= 2
