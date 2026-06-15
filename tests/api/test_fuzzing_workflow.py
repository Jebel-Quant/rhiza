"""Tests for the rhiza_fuzzing.yml workflow and ClusterFuzzLite configuration."""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(".github") / "workflows" / "rhiza_fuzzing.yml"
PROJECT_PATH = Path(".clusterfuzzlite") / "project.yaml"
FUZZER_PATH = Path("tests") / "fuzz" / "fuzz_suppression_audit.py"


def _workflow_triggers(workflow_doc: dict) -> dict:
    """Extract workflow triggers regardless of how YAML parsed the `on` key."""
    return workflow_doc.get(True, workflow_doc.get("on", {})) or {}


def test_fuzzing_workflow_uses_clusterfuzzlite_actions(root):
    """The fuzzing workflow must build and run fuzzers with ClusterFuzzLite."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    action_refs = [step["uses"] for job in workflow["jobs"].values() for step in job.get("steps", []) if "uses" in step]

    assert any(ref.startswith("google/clusterfuzzlite/actions/build_fuzzers@") for ref in action_refs)
    assert any(ref.startswith("google/clusterfuzzlite/actions/run_fuzzers@") for ref in action_refs)


def test_fuzzing_workflow_covers_pull_requests_and_batch_runs(root):
    """The workflow must cover both PR fuzzing and scheduled batch fuzzing."""
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    triggers = _workflow_triggers(workflow)

    assert "pull_request" in triggers
    assert "schedule" in triggers
    assert "workflow_dispatch" in triggers
    assert "code-change" in str(workflow["jobs"]["pr-fuzzing"])
    assert "batch" in str(workflow["jobs"]["batch-fuzzing"])


def test_fuzzing_steps_skip_when_no_clusterfuzzlite_config(root):
    """build/run fuzzers must be gated on a detected .clusterfuzzlite/ config.

    The config is repo-specific and not shipped by any Rhiza bundle, so a
    downstream repo without it must skip fuzzing (the job stays green) instead
    of failing in build_fuzzers. Every clusterfuzzlite step is guarded by the
    detection step's output.
    """
    with (root / WORKFLOW_PATH).open(encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)

    for job_name, job in workflow["jobs"].items():
        steps = job.get("steps", [])
        detect = [s for s in steps if s.get("id") == "cfl"]
        assert detect, f"{job_name}: missing the ClusterFuzzLite config-detection step (id: cfl)"

        guarded = [s for s in steps if "uses" in s and "clusterfuzzlite" in s["uses"]]
        assert guarded, f"{job_name}: expected clusterfuzzlite steps"
        for step in guarded:
            assert "cfl" in step.get("if", ""), (
                f"{job_name}: step '{step.get('name')}' must be gated on the config-detection output"
            )


def test_clusterfuzzlite_configuration_targets_python(root):
    """ClusterFuzzLite config must declare Python and a real Atheris harness."""
    with (root / PROJECT_PATH).open(encoding="utf-8") as fh:
        project = yaml.safe_load(fh)

    fuzz_target = (root / FUZZER_PATH).read_text(encoding="utf-8")

    assert project["language"] == "python"
    assert "import atheris" in fuzz_target
    assert "suppression_audit.py" in fuzz_target
