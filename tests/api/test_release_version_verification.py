"""Behavioural tests for the release workflow's version checks.

The ``build`` job answers one question twice: does the thing being released actually
carry the version the tag names? For a project that *writes* its version, reading
``pyproject.toml`` answers it. For one that derives it from the VCS — PEP 621's
``dynamic = ["version"]`` with a backend plugin such as hatch-vcs, which rhiza itself
now uses — there is nothing written to read, and ``uv version --short`` does not return
a differing number: it exits 2 with "We cannot get or set dynamic project versions". The
step that called it unconditionally therefore failed *every* release of such a project,
which is why the check is in two halves now:

- ``Verify version matches tag`` compares the written number, and says so and skips when
  the declaration is dynamic.
- ``Verify built distribution matches the tag`` compares what ``uv build`` produced. That
  is where a derived version can actually be wrong, and the failure it catches is silent
  otherwise: hatch-vcs and setuptools-scm fall back rather than fail, so a checkout that
  cannot see the tag builds ``0.1.dev1+g<sha>`` and publishes it under a green tick.

Both are run here as shell, lifted out of the workflow YAML the way
``test_release_tag_reachability.py`` runs the reachability guard, so a rewrite that keeps
the step name but breaks the logic still fails. The scripts read their tag from ``TAG``
in the environment rather than from an interpolated ``${{ }}`` expression, which is what
makes that possible at all.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - running the workflow's own shell against fixture projects
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_BASH = shutil.which("bash")
_UV = shutil.which("uv")

_LIVE_WORKFLOW = _ROOT / ".github" / "workflows" / "rhiza_release.yml"
_BUNDLE_WORKFLOW = _ROOT / "bundles" / "github" / ".github" / "workflows" / "rhiza_release.yml"

_WRITTEN_STEP = "Verify version matches tag"
_BUILT_STEP = "Verify built distribution matches the tag"


def _step(workflow: Path, name: str) -> dict:
    """Return the single ``build`` step with this name.

    Args:
        workflow: The release workflow to read.
        name: The step's ``name:``.

    Returns:
        The step mapping.
    """
    steps = yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]["build"]["steps"]
    matching = [step for step in steps if step.get("name") == name]
    assert len(matching) == 1, (
        f"{workflow.relative_to(_ROOT)}: expected exactly one '{name}' step in the build job, found {len(matching)}"
    )
    return matching[0]


def _run(script: str, cwd: Path, tag: str) -> subprocess.CompletedProcess:
    """Execute a step's shell the way the workflow would.

    Args:
        script: The step's ``run:`` body.
        cwd: The project directory to run it in.
        tag: The value of ``TAG``, i.e. the release tag.

    Returns:
        The completed process.
    """
    assert _BASH is not None  # guarded by the skipif on the classes below
    return subprocess.run(  # nosec B603
        # `-e` because that is how GitHub invokes a `run:` block (`bash -e {0}`): a probe
        # that cannot run must fail the step rather than fall through to a branch chosen
        # from an empty variable.
        [_BASH, "-e", "-c", script],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, "TAG": tag},
    )


def _project(directory: Path, body: str) -> Path:
    """Write a minimal ``pyproject.toml`` and return its directory.

    Args:
        directory: Where to write it.
        body: The ``[project]`` lines that follow ``name``.

    Returns:
        The directory, for chaining.
    """
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "pyproject.toml").write_text(
        f'[project]\nname = "demo"\n{body}requires-python = ">=3.11"\ndependencies = []\n',
        encoding="utf-8",
    )
    return directory


@pytest.fixture(scope="module")
def uv_provisioning() -> None:
    """Skip the module when uv cannot provision the scripts' ephemeral dependencies.

    Both steps reach for `uv run --with ...`, so offline they fail for a reason that has
    nothing to do with the logic under test — the same trade
    ``test_bundle_cli_targets.py`` makes. CI has a network, where the distinction stops
    mattering.
    """
    if _UV is None:
        pytest.skip("uv not available; the workflow's version checks are uv scripts")
    result = subprocess.run(  # nosec B603
        [_UV, "run", "--with", "tomli", "--with", "packaging", "--no-project", "python3", "-c", "import tomli"],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        pytest.skip(f"uv cannot provision tomli/packaging (offline?):\n{result.stderr[-400:]}")


@pytest.fixture(scope="module")
def written_check() -> str:
    """The written-version check as shipped in the bundle (what downstream repos run).

    Returns:
        The step's shell.
    """
    return _step(_BUNDLE_WORKFLOW, _WRITTEN_STEP)["run"]


@pytest.fixture(scope="module")
def built_check() -> str:
    """The built-distribution check as shipped in the bundle.

    Returns:
        The step's shell.
    """
    return _step(_BUNDLE_WORKFLOW, _BUILT_STEP)["run"]


class TestBothChecksAreWiredIntoBothWorkflows:
    """Structural half: the steps exist, agree across the two copies, and are ordered."""

    @pytest.mark.parametrize("name", [_WRITTEN_STEP, _BUILT_STEP])
    def test_live_and_bundle_workflows_share_one_script(self, name: str) -> None:
        """The mother repo's live workflow and the synced bundle must run the same check.

        The two files differ by design (SHA-pinned actions here, tag-pinned downstream),
        so nothing byte-compares them — but a check that exists only upstream protects
        exactly the repo that never had the problem.

        Args:
            name: The step whose shell is compared.
        """
        assert _step(_LIVE_WORKFLOW, name)["run"] == _step(_BUNDLE_WORKFLOW, name)["run"]

    @pytest.mark.parametrize("workflow", [_LIVE_WORKFLOW, _BUNDLE_WORKFLOW])
    def test_each_check_reads_the_tag_from_the_environment(self, workflow: Path) -> None:
        """`TAG` must come through ``env:``, not be interpolated into the shell.

        Interpolating ``${{ needs.tag.outputs.tag }}`` into the script would put a tag
        chosen by whoever pushed it into a shell command, and would leave the logic
        untestable outside Actions — which is how it went unnoticed that the step could
        not run on a dynamic version at all.

        Args:
            workflow: The release workflow to read.
        """
        for name in (_WRITTEN_STEP, _BUILT_STEP):
            step = _step(workflow, name)
            assert step.get("env", {}).get("TAG") == "${{ needs.tag.outputs.tag }}", (
                f"{workflow.relative_to(_ROOT)}: '{name}' must take the tag from env.TAG"
            )
            assert "needs.tag.outputs.tag" not in step["run"], (
                f"{workflow.relative_to(_ROOT)}: '{name}' interpolates the tag into its shell"
            )

    @pytest.mark.parametrize("workflow", [_LIVE_WORKFLOW, _BUNDLE_WORKFLOW])
    def test_the_built_distribution_is_checked_after_the_build(self, workflow: Path) -> None:
        """A check that runs before ``uv build`` would measure a stale or absent dist/.

        Args:
            workflow: The release workflow to read.
        """
        names = [
            step.get("name") for step in yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]["build"]["steps"]
        ]
        assert names.index(_BUILT_STEP) > names.index("Build"), (
            f"{workflow.relative_to(_ROOT)}: '{_BUILT_STEP}' must follow the Build step"
        )

    @pytest.mark.parametrize("workflow", [_LIVE_WORKFLOW, _BUNDLE_WORKFLOW])
    def test_the_built_distribution_check_is_gated_on_a_buildable_project(self, workflow: Path) -> None:
        """It shares the Build step's condition: a virtual project produces no dist/.

        Args:
            workflow: The release workflow to read.
        """
        condition = _step(workflow, _BUILT_STEP)["if"]
        assert condition == _step(workflow, "Build")["if"], (
            f"{workflow.relative_to(_ROOT)}: '{_BUILT_STEP}' must run exactly when Build does"
        )


def test_this_repo_declares_its_version_in_exactly_one_place() -> None:
    """Rhiza's own version is the git tag — and all three halves of that must agree.

    ``[project]`` deriving the version while ``[tool.bumpversion]`` still carries a
    ``current_version`` (or a ``[[files]]`` entry naming pyproject.toml) would put the
    number back in a file, and a release would then bump a copy nothing reads. The
    absent ``current_version`` is also the signal ``/rhiza:release`` uses to tell a
    tag-derived repo from one with a written version, so it is load-bearing rather than
    tidy.
    """
    config = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "version" in config["project"].get("dynamic", []), (
        "[project] must derive its version from the VCS; see the comment above `dynamic`"
    )
    assert "version" not in config["project"], "[project] cannot both write a version and list it in `dynamic`"

    bumpversion = config["tool"]["bumpversion"]
    assert "current_version" not in bumpversion, (
        "[tool.bumpversion] must not carry a version of its own — it is read from the newest tag"
    )
    assert not [entry for entry in bumpversion.get("files", []) if entry.get("filename") == "pyproject.toml"], (
        "there is no `version = ...` line in pyproject.toml for a bump to rewrite"
    )


@pytest.mark.skipif(
    _BASH is None or sys.platform == "win32",
    reason=(
        "these are GitHub Actions `run:` steps, and the release job they belong to runs on "
        "ubuntu-latest only — executing their shell through Git Bash would exercise the MSYS "
        "argument-translation layer rather than the checks. The structural tests above still "
        "run on every platform."
    ),
)
@pytest.mark.usefixtures("uv_provisioning")
class TestTheWrittenVersionCheck:
    """Run the written-version check against the three shapes a project can have."""

    def test_a_written_version_matching_the_tag_passes(self, written_check: str, tmp_path: Path) -> None:
        """The ordinary case.

        Args:
            written_check: The step's shell.
            tmp_path: pytest's temporary directory.
        """
        project = _project(tmp_path / "match", 'version = "1.2.3"\n')

        result = _run(written_check, project, "v1.2.3")

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Version verified: 1.2.3" in result.stdout

    def test_a_written_version_that_differs_from_the_tag_fails(self, written_check: str, tmp_path: Path) -> None:
        """The failure the step exists for, named in an operator-facing annotation.

        Args:
            written_check: The step's shell.
            tmp_path: pytest's temporary directory.
        """
        project = _project(tmp_path / "mismatch", 'version = "1.2.2"\n')

        result = _run(written_check, project, "v1.2.3")

        assert result.returncode == 1, result.stdout + result.stderr
        assert "::error::Version mismatch" in result.stdout

    def test_a_dynamic_version_is_reported_and_not_compared(self, written_check: str, tmp_path: Path) -> None:
        """The regression this split exists for: `uv version --short` must not be called.

        A project on hatch-vcs has no written number, and calling uv for one exits 2 —
        failing a release that is perfectly well-formed. The step must say what it did
        instead of passing silently, since a check that measures nothing reads exactly
        like one that passed.

        Args:
            written_check: The step's shell.
            tmp_path: pytest's temporary directory.
        """
        project = _project(tmp_path / "dynamic", 'dynamic = ["version"]\n')

        result = _run(written_check, project, "v1.2.3")

        assert result.returncode == 0, result.stdout + result.stderr
        assert "dynamic" in result.stdout
        assert "::error::" not in result.stdout


@pytest.mark.skipif(
    _BASH is None or sys.platform == "win32",
    reason="see TestTheWrittenVersionCheck — the release job runs on ubuntu-latest only",
)
@pytest.mark.usefixtures("uv_provisioning")
class TestTheBuiltDistributionCheck:
    """Run the artifact check against the distributions a build can leave behind.

    The filenames are fabricated rather than built: the step parses names, so a real
    ``uv build`` would only add a toolchain dependency and the wait for it. What matters
    is that the dev-version fallback is refused and the tagged version is not.
    """

    @staticmethod
    def _dist(directory: Path, *names: str) -> Path:
        """Create ``dist/`` holding empty files with these names.

        Args:
            directory: The project directory to create.
            names: The distribution filenames.

        Returns:
            The project directory.
        """
        dist = directory / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        for name in names:
            (dist / name).touch()
        return directory

    def test_a_distribution_at_the_tag_version_passes(self, built_check: str, tmp_path: Path) -> None:
        """Both artifacts carry the released version.

        Args:
            built_check: The step's shell.
            tmp_path: pytest's temporary directory.
        """
        project = self._dist(tmp_path / "ok", "demo-1.2.3-py3-none-any.whl", "demo-1.2.3.tar.gz")

        result = _run(built_check, project, "v1.2.3")

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Built distribution verified at 1.2.3" in result.stdout

    def test_a_dev_version_from_an_invisible_tag_is_refused(self, built_check: str, tmp_path: Path) -> None:
        """The silent failure: setuptools-scm/hatch-vcs fall back instead of failing.

        A shallow checkout, or one without tags, derives ``0.1.dev1+g<sha>`` — and every
        earlier step in the release is green, so without this the wrong version reaches
        PyPI with no error anywhere.

        Args:
            built_check: The step's shell.
            tmp_path: pytest's temporary directory.
        """
        project = self._dist(tmp_path / "devfallback", "demo-0.1.dev1-py3-none-any.whl", "demo-0.1.dev1.tar.gz")

        result = _run(built_check, project, "v1.2.3")

        assert result.returncode == 1, result.stdout + result.stderr
        assert "::error::Built distribution does not carry the release version 1.2.3" in result.stdout
        assert "fetch" in result.stdout, "the annotation must name the checkout as the thing to look at"

    def test_an_empty_dist_is_refused(self, built_check: str, tmp_path: Path) -> None:
        """A build that produced nothing must not read as a verified release.

        Args:
            built_check: The step's shell.
            tmp_path: pytest's temporary directory.
        """
        project = self._dist(tmp_path / "empty")

        result = _run(built_check, project, "v1.2.3")

        assert result.returncode == 1, result.stdout + result.stderr
        assert "no distribution in dist/" in result.stdout
