"""The optional test-extra targets, after `test.mk` retired to rhiza-task.

This module read the fragment: that `benchmark` was defined, was `.PHONY`, depended on `install`,
and drove pytest-benchmark. All four assertions were about a file's text, and the file is gone —
`benchmark`, `hypothesis-test` and `stress` are registered tasks now, and rhiza-task tests their
recipes where those recipes live. There was a fourth, `mutation`, and it is gone rather than
moved (#1492).

Rewritten rather than deleted because of *how* it failed. Each test skipped itself when `test.mk`
was absent, so retiring the fragment turned four tests into four silent skips: green suite, four
fewer checks, no signal. The same trap caught `test_lfs.py` and `test_marimo_targets.py` in this
change, which is the argument for assertions that go red when their subject moves.
"""

from __future__ import annotations

import subprocess  # nosec B404
import tomllib
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]

# What the `tests` bundle exists to provide. None is named by `all` — they are the opt-in extras,
# each needing its own tool and folder convention. `mutation` was a fourth until #1492; rhiza no
# longer offers mutation testing, and `test_no_bundle_offers_a_mutation_gate` below pins that.
_EXTRA_TARGETS = ("benchmark", "hypothesis-test", "stress")


@pytest.mark.parametrize("target", _EXTRA_TARGETS)
def test_extra_target_resolves(target: str) -> None:
    """Each optional extra must still resolve, so retiring `test.mk` cost no entry point.

    A dry run rather than a real one: these are the expensive gates, and what is in question is
    whether the target exists, not whether the tool passes.

    Be clear about how little that proves, because the docstring here used to overstate it. The
    shim resolves *every* target through its ``%:`` catch-all, and ``make -n`` prints the ``uvx``
    line without running it — so ``make -n definitely-not-a-task`` also exits 0. This asserts that
    the shim is intact, not that the CLI has a task by this name; the pin's task inventory is
    ``test_bundle_cli_targets.py``'s job. That gap is why ``mutation`` passed here for as long as
    it was broken (#1492).
    """
    proc = subprocess.run(  # nosec B603
        ["make", "-n", target], cwd=_ROOT, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, f"`make {target}` did not resolve: {proc.stderr}"
    assert "no rule to make target" not in proc.stderr.lower(), (
        f"{target} resolves to no rule — the tests bundle's config has no gate left to feed"
    )


def test_the_benchmark_gate_has_something_to_measure_or_is_known_not_to() -> None:
    """Record whether `benchmark` has any input in *this* repo.

    Written as an observation rather than a demand, because the answer here is "no": rhiza ships
    configuration, so it has no ``tests/benchmarks/`` — while ``rhiza_benchmark.yml`` runs
    ``make benchmark`` on every push. That gate therefore measures nothing on this repo, and has
    for as long as the folder has been absent. It predates the rhiza-task migration and is not its
    doing.

    Asserted this way round so the fact is visible in the suite instead of being something a reader
    has to notice: if a benchmarks folder is ever added, the second branch takes over and starts
    requiring content, and if the workflow is dropped the first branch stops being reachable.
    """
    folder = Path(__file__).resolve().parents[2] / "tests" / "benchmarks"
    if not folder.is_dir():
        pytest.skip(
            "this repo has no tests/benchmarks/, so `make benchmark` measures nothing here — "
            "a pre-existing gap in rhiza_benchmark.yml, not a consequence of retiring test.mk"
        )
    assert sorted(folder.glob("test_*.py")), (
        "tests/benchmarks/ exists but holds no benchmark modules, so the gate collects nothing"
    )


def test_no_bundle_offers_a_mutation_gate() -> None:
    """No bundle may ship or advertise a mutation-testing gate (#1492).

    Rhiza offered `mutation` for as long as it was broken: mutmut 3 removed the two options and
    the subcommand the recipe used, and the recipe installed mutmut unpinned, so it failed in
    every consumer from the day of that release. Nothing caught it because no `all` named it and
    no workflow ran it.

    The decision is not to port it — mutmut 3.x has no CLI path for source paths at all, so a
    task would have to require `[tool.mutmut]` in every consumer's `pyproject.toml` or write one
    for them. This asserts the decision rather than trusting the prose: a bundle must ship no
    file mentioning mutmut, and no bundle description may promise a mutation gate.

    Scoped to shipped files and descriptions on purpose, so the rationale recorded in
    `template-bundles.yml`'s `notes` — which has to name the thing to explain it — stays legal.

    The dependency-group half is here rather than in `test_dependency_groups.py`, and the reason
    is worth stating: `mutmut` used to sit in that module's `_PROVISIONED_ON_THE_FLY` set, whose
    contract is "a target already injects this, so do not also declare it". No target injects it
    any more, so leaving it there would have asserted something untrue, and simply deleting the
    entry would have *permitted* a group to declare a tool nothing runs. It is a policy about
    mutation, so it belongs with the rest of the policy.
    """
    offenders = [
        str(path.relative_to(_ROOT))
        for path in sorted((_ROOT / "bundles").rglob("*"))
        if path.is_file() and "mutmut" in path.read_text(encoding="utf-8", errors="ignore").lower()
    ]
    assert not offenders, f"bundles ship mutation tooling again: {offenders}"

    bundles = yaml.safe_load((_ROOT / ".rhiza" / "template-bundles.yml").read_text())["bundles"]
    promising = sorted(name for name, spec in bundles.items() if "mutation" in (spec.get("description") or "").lower())
    assert not promising, f"bundle descriptions advertise a mutation gate again: {promising}"

    with (_ROOT / "pyproject.toml").open("rb") as fh:
        groups = tomllib.load(fh).get("dependency-groups", {})
    declaring = sorted(f"{group}:{dep}" for group, deps in groups.items() for dep in deps if "mutmut" in dep.lower())
    assert not declaring, f"a dependency group declares mutmut, which no target runs: {declaring}"
