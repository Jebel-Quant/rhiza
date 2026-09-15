"""Tests that gate workflow hygiene: concurrency groups and precise action pins.

Rhiza-specific: covers both rhiza's own workflows (.github/workflows/) and the
workflow stubs shipped to downstream projects (bundles/*/.github/workflows/).
Lives in the mother repo's own tests/, so it does not sync downstream.

Three invariants:

1. Every workflow that runs its own jobs declares a top-level ``concurrency``
   block so superseded runs are cancelled instead of wasting CI minutes.
   Release and sync workflows are the exception: they queue
   (``cancel-in-progress: false``) because they must never be interrupted
   mid-publish or mid-push. Caller stubs that merely delegate to a reusable
   workflow must NOT declare concurrency: the reusable workflow already
   declares the same ``${{ github.workflow }}-${{ github.ref }}`` group, and a
   duplicate caller-level group deadlocks (the top-level run and the nested
   job each wait on the other for the shared group).
2. Every ``uses:`` reference is pinned to an exact version — a full
   ``vX.Y.Z``-style tag or a 40-character commit SHA — so upgrades only
   happen through reviewed dependency-update PRs. Local actions (``./...``)
   are exempt.
3. Every caller stub forwards secrets **by name**, never with ``secrets: inherit``,
   and forwards exactly the secrets the called workflow declares — which in turn
   must be exactly the secrets it reads. GitHub honours ``inherit`` only when the
   caller is in the reusable workflow's own organisation or enterprise, so from any
   other organisation it forwarded nothing and private dependencies failed to
   install (#1689). A mapped-but-undeclared secret fails the run at parse time,
   and a read-but-undeclared one arrives empty, so both halves are pinned.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]

# Workflows that must queue rather than cancel in-progress runs.
_QUEUE_WORKFLOWS = {"rhiza_release.yml"}

# Exact tag (v1.2.3, optionally deeper like v0.3.1900000450) or full commit SHA.
_PRECISE_REF_RE = re.compile(r"@(v?\d+(\.\d+){2,}|[0-9a-f]{40})$")


# Names of compiler-generated workflows to exclude from hygiene checks (their
# content is owned by a generator, not hand-written). None currently exist;
# kept as the exclusion hook for any future generated workflows.
_GENERATED_WORKFLOWS: set[str] = set()


def _workflow_files() -> list[Path]:
    """Return every workflow file, rhiza's own and bundle-shipped stubs.

    Generated files (*.lock.yml) are excluded: their content is owned by a
    compiler, not written by hand.
    """
    patterns = (".github/workflows/*.yml", "bundles/*/.github/workflows/*.yml")
    return sorted(
        path
        for pattern in patterns
        for path in _ROOT.glob(pattern)
        if not path.name.endswith(".lock.yml") and path.name not in _GENERATED_WORKFLOWS
    )


_WORKFLOWS = _workflow_files()
_IDS = [str(p.relative_to(_ROOT)) for p in _WORKFLOWS]


def _load(path: Path) -> dict:
    """Load a workflow YAML file and return the parsed document."""
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _uses_refs(workflow: dict) -> list[str]:
    """Return every ``uses:`` reference in a workflow (job-level and step-level)."""
    refs: list[str] = []
    for job in (workflow.get("jobs") or {}).values():
        if "uses" in job:
            refs.append(job["uses"])
        for step in job.get("steps") or []:
            if "uses" in step:
                refs.append(step["uses"])
    return refs


def _delegates_to_reusable(workflow: dict) -> bool:
    """True if the workflow is a thin caller that delegates to a reusable workflow.

    Such stubs have a job-level ``uses:`` pointing at a reusable workflow file
    (``.../.github/workflows/<name>.yml@<ref>``). They must not declare their
    own ``concurrency`` block — the called workflow already does, and a shared
    group deadlocks the run.
    """
    for job in (workflow.get("jobs") or {}).values():
        uses = job.get("uses")
        if uses and ".github/workflows/" in uses and ".yml@" in uses:
            return True
    return False


class TestWorkflowConcurrency:
    """Every workflow must manage concurrency explicitly."""

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_has_concurrency_group(self, workflow_file: Path) -> None:
        """Job-running workflows declare a concurrency group; caller stubs must not."""
        workflow = _load(workflow_file)
        concurrency = workflow.get("concurrency")
        if _delegates_to_reusable(workflow):
            assert concurrency is None, (
                f"{workflow_file.name}: reusable-workflow caller must not declare a "
                f"top-level 'concurrency' block — it shares the called workflow's "
                f"group and deadlocks the run"
            )
            return
        assert isinstance(concurrency, dict), (
            f"{workflow_file.name}: missing top-level 'concurrency' block — "
            f"superseded runs will pile up instead of being cancelled or queued"
        )
        assert "group" in concurrency, f"{workflow_file.name}: concurrency block has no 'group'"

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_cancel_in_progress_policy(self, workflow_file: Path) -> None:
        """Release/sync workflows queue; other job-running workflows cancel superseded runs.

        Reusable-workflow callers carry no concurrency block of their own (the
        called workflow owns the policy, and a duplicate caller-level group
        deadlocks the run), so for them this asserts the block stays absent
        rather than checking a cancel-in-progress value.
        """
        workflow = _load(workflow_file)
        if _delegates_to_reusable(workflow):
            assert workflow.get("concurrency") is None, (
                f"{workflow_file.name}: reusable-workflow caller must not declare a "
                f"top-level 'concurrency' block — it shares the called workflow's "
                f"cancel-in-progress policy and a duplicate group deadlocks the run"
            )
            return
        concurrency = workflow.get("concurrency") or {}
        expected = workflow_file.name not in _QUEUE_WORKFLOWS
        assert concurrency.get("cancel-in-progress") is expected, (
            f"{workflow_file.name}: cancel-in-progress must be {expected} "
            f"({'cancel superseded runs' if expected else 'a release or sync must never be interrupted'})"
        )


class TestActionPinning:
    """Every action reference must be pinned to an exact version."""

    @pytest.mark.parametrize("workflow_file", _WORKFLOWS, ids=_IDS)
    def test_uses_refs_are_precisely_pinned(self, workflow_file: Path) -> None:
        """All uses: refs must carry an exact vX.Y.Z tag or a full commit SHA."""
        imprecise = [
            ref
            for ref in _uses_refs(_load(workflow_file))
            if not ref.startswith("./") and not _PRECISE_REF_RE.search(ref)
        ]
        assert not imprecise, (
            f"{workflow_file.name}: imprecisely pinned actions {imprecise} — "
            f"pin to an exact vX.Y.Z tag or full commit SHA"
        )

    def test_workflows_were_collected(self) -> None:
        """Guard against the collector silently matching nothing."""
        assert len(_WORKFLOWS) >= 20, "expected to collect rhiza and bundle workflows"


# --- Invariant 3: secrets are forwarded by name ------------------------------

# Secrets a called workflow may read without the caller declaring or forwarding them.
_IMPLICIT_SECRETS = {"GITHUB_TOKEN"}
_SECRET_REF_RE = re.compile(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)")
_REUSABLE_USES_RE = re.compile(r"^jebel-quant/rhiza/\.github/workflows/([A-Za-z0-9_.-]+\.yml)@")


def _triggers(workflow: dict) -> dict:
    """Return the ``on:`` mapping; pyyaml parses the bare key ``on`` as boolean ``True``."""
    return workflow.get(True, workflow.get("on", {})) or {}


def _delegating_jobs(workflow: dict) -> dict[str, dict]:
    """Return the jobs of a caller stub that delegate to one of rhiza's reusable workflows."""
    return {
        job_id: job
        for job_id, job in (workflow.get("jobs") or {}).items()
        if _REUSABLE_USES_RE.match(job.get("uses") or "")
    }


def _called_workflow(uses: str) -> Path:
    """Resolve a stub's ``uses:`` to the reusable workflow in this repo.

    The stubs pin ``jebel-quant/rhiza/.github/workflows/<name>.yml@<tag>`` and this
    *is* jebel-quant/rhiza, so the callee at HEAD is the local file — which is also the
    version the stub will call once the tag that ships both of them is cut.
    """
    match = _REUSABLE_USES_RE.match(uses)
    assert match, f"not a reusable-workflow reference: {uses}"
    path = _ROOT / ".github" / "workflows" / match.group(1)
    assert path.is_file(), f"{uses} names a workflow this repo does not ship: {path.relative_to(_ROOT)}"
    return path


def _secrets_read(path: Path) -> set[str]:
    """Every ``secrets.<NAME>`` a workflow's text references, minus the ones GitHub always provides.

    Read from the text rather than the parsed YAML: most references sit inside ``run:``
    blocks and ``with:`` values, which a YAML loader hands back as opaque strings.
    """
    return set(_SECRET_REF_RE.findall(path.read_text(encoding="utf-8"))) - _IMPLICIT_SECRETS


def _secrets_declared(workflow: dict) -> dict[str, dict]:
    """The ``on.workflow_call.secrets`` mapping, or empty when the workflow declares none."""
    return (_triggers(workflow).get("workflow_call") or {}).get("secrets") or {}


_STUBS = [path for path in _WORKFLOWS if _delegating_jobs(_load(path))]
_STUB_IDS = [str(p.relative_to(_ROOT)) for p in _STUBS]
_CALLED = sorted({_called_workflow(job["uses"]) for path in _STUBS for job in _delegating_jobs(_load(path)).values()})
_CALLED_IDS = [str(p.relative_to(_ROOT)) for p in _CALLED]


class TestSecretForwarding:
    """Caller stubs forward exactly the secrets their reusable workflow declares, by name."""

    def test_stubs_were_collected(self) -> None:
        """The invariant is vacuous if the stub discovery finds nothing."""
        assert _STUBS, "no caller stubs found under bundles/*/.github/workflows/ — discovery is broken"
        assert _CALLED, "no reusable workflow resolved from the stubs — the uses: pattern has changed"

    @pytest.mark.parametrize("stub", _STUBS, ids=_STUB_IDS)
    def test_no_stub_inherits_secrets(self, stub: Path) -> None:
        """``secrets: inherit`` forwards nothing to a caller outside jebel-quant's organisation."""
        jobs = _delegating_jobs(_load(stub))
        inheriting = [job_id for job_id, job in jobs.items() if job.get("secrets") == "inherit"]
        assert not inheriting, (
            f"{stub.relative_to(_ROOT)}: jobs {inheriting} use `secrets: inherit`. GitHub honours it "
            "only when the caller is in the reusable workflow's own organisation or enterprise, so "
            "every other consumer's GH_PAT silently never arrived (#1689). Map each secret by name."
        )

    @pytest.mark.parametrize("called", _CALLED, ids=_CALLED_IDS)
    def test_called_workflow_declares_every_secret_it_reads(self, called: Path) -> None:
        """A secret read but not declared arrives empty once the caller stops inheriting."""
        read = _secrets_read(called)
        declared = set(_secrets_declared(_load(called)))
        assert read == declared, (
            f"{called.relative_to(_ROOT)}: reads {sorted(read)} but declares {sorted(declared)} under "
            f"workflow_call.secrets — undeclared: {sorted(read - declared)}, unused: {sorted(declared - read)}. "
            "A caller can only forward what the callee declares, so declare exactly what is read."
        )

    @pytest.mark.parametrize("called", _CALLED, ids=_CALLED_IDS)
    def test_declared_secrets_are_optional(self, called: Path) -> None:
        """A consumer with no private dependencies must still run, on the `github.token` fallback."""
        declared = _secrets_declared(_load(called))
        required = [name for name, spec in declared.items() if (spec or {}).get("required") is not False]
        assert not required, (
            f"{called.relative_to(_ROOT)}: {required} lack `required: false`. A required secret fails "
            "every consumer that has not defined it; the stub forwards an absent secret as empty and "
            "the workflow falls back to github.token, which is what a repo without private deps needs."
        )

    @pytest.mark.parametrize("stub", _STUBS, ids=_STUB_IDS)
    def test_stub_forwards_exactly_the_declared_secrets(self, stub: Path) -> None:
        """Mapped == declared, each under its own name: `NAME: ${{ secrets.NAME }}`."""
        problems: list[str] = []
        for job_id, job in _delegating_jobs(_load(stub)).items():
            declared = set(_secrets_declared(_load(_called_workflow(job["uses"]))))
            mapped = job.get("secrets") or {}
            if not isinstance(mapped, dict):
                problems.append(f"{job_id}: secrets is {mapped!r}, not a mapping")
                continue
            if set(mapped) != declared:
                problems.append(
                    f"{job_id}: forwards {sorted(mapped)} but {job['uses'].split('@')[0]} declares "
                    f"{sorted(declared)} — missing {sorted(declared - set(mapped))}, "
                    f"undeclared {sorted(set(mapped) - declared)}"
                )
            for name, value in mapped.items():
                if value != f"${{{{ secrets.{name} }}}}":
                    problems.append(f"{job_id}: {name} is forwarded as {value!r}, expected ${{{{ secrets.{name} }}}}")
        assert not problems, f"{stub.relative_to(_ROOT)}:\n  " + "\n  ".join(problems)
