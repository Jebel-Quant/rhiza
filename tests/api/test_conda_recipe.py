"""Conda-forge recipe generation: the shared script and both workflows that run it (#1701, #1746).

``bundles/github/.rhiza/scripts/conda_recipe.py`` holds the generate and verify logic. Two
workflows run it and must run it identically:

* ``rhiza_release.yml``'s ``conda`` job, right after the PyPI upload;
* ``rhiza_conda_recipe.yml``, dispatched for an existing release tag, which regenerates
  the recipe without republishing anything.

The step-level tests below execute each workflow's own ``run:`` lines against a fake
grayskull and a ``file://`` PyPI, so they test what a consumer actually runs rather than
the presence of words in the YAML. The unit tests drive the module directly for the paths
a workflow run cannot reach cheaply, such as the retry loop's sleeps.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess  # nosec B404 - running the workflows' own shell against a fake grayskull
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "bundles" / "github" / ".rhiza" / "scripts" / "conda_recipe.py"
_SPEC = importlib.util.spec_from_file_location("conda_recipe", _SCRIPT)
assert _SPEC is not None
assert _SPEC.loader is not None
conda_recipe = importlib.util.module_from_spec(_SPEC)
sys.modules["conda_recipe"] = conda_recipe
_SPEC.loader.exec_module(conda_recipe)

_RELEASE = Path(".github") / "workflows" / "rhiza_release.yml"
_RECIPE = Path(".github") / "workflows" / "rhiza_conda_recipe.yml"
_BUNDLE = Path("bundles") / "github"

# (workflow, job, the expression its steps read the tag from)
_ENTRY_POINTS = [
    (_RELEASE, "conda", "${{ needs.tag.outputs.tag }}"),
    (_BUNDLE / _RELEASE, "conda", "${{ needs.tag.outputs.tag }}"),
    (_RECIPE, "recipe", "${{ inputs.tag }}"),
    (_BUNDLE / _RECIPE, "recipe", "${{ inputs.tag }}"),
]
_ENTRY_IDS = [p.as_posix() for p, _, _ in _ENTRY_POINTS]
_RECIPE_WORKFLOWS = [_RECIPE, _BUNDLE / _RECIPE]
_RELEASE_WORKFLOWS = [_RELEASE, _BUNDLE / _RELEASE]

_TOOLS = ".rhiza-conda-tools"
_GENERATE = f"python {_TOOLS}/.rhiza/scripts/conda_recipe.py generate"
_VERIFY = f"python {_TOOLS}/.rhiza/scripts/conda_recipe.py verify"

_RELEASED = "1.2.3"
_SDIST_SHA = "a" * 64

# Stands in for grayskull 3.2.0, reproducing the behaviours the script has to tell apart:
#
# * without ``--no-use-v1-format`` it writes a V1 ``recipe.yaml`` and then crashes, as the real
#   one does when conda-recipe-manager is not installed (the second half of #1701);
# * with ``CRASH`` set it fails outright, standing in for any other real error;
# * for its first ``MISSING`` calls it does what the real one does on a PyPI 404 -- prints the
#   error and exits 0 having written nothing -- then writes a ``meta.yaml``.
_FAKE_GRAYSKULL = """#!/usr/bin/env bash
calls=$(( $(cat "$STATE/calls" 2>/dev/null || echo 0) + 1 ))
echo "$calls" > "$STATE/calls"
if [[ -n "${CRASH:-}" ]]; then
  echo "Traceback (most recent call last):" >&2
  exit 1
fi
if [[ " $* " != *" --no-use-v1-format "* ]]; then
  mkdir -p "${2%%==*}" && echo "schema_version: 1" > "${2%%==*}/recipe.yaml"
  echo "ImportError: Please install conda-recipe-manager from conda-forge to enable support for the V1 format." >&2
  exit 1
fi
if [[ "$calls" -le "${MISSING:-0}" ]]; then
  echo "Package seems to be missing."
  echo "Error code: 404"
  exit 0
fi
echo "$2" >> "$STATE/requests"
name="${2%%==*}"
version="${RECIPE_VERSION:-${2#*==}}"
mkdir -p "$name"
cat > "$name/meta.yaml" <<RECIPE
{% set name = "$name" %}
{% set version = "$version" %}

package:
  name: {{ name|lower }}
  version: {{ version }}

source:
  url: https://pypi.org/packages/source/{{ name[0] }}/{{ name }}/{{ name|replace('-', '_') }}-{{ version }}.tar.gz
  sha256: ${RECIPE_SHA:-$SDIST_SHA}
RECIPE
"""

# The variables the fake grayskull reads; cleared so the developer's environment cannot leak in.
_FAKE_ENV = ("CRASH", "MISSING", "RECIPE_VERSION", "RECIPE_SHA")


def _load(relative: Path) -> dict:
    """Parse a workflow file relative to the repository root."""
    return yaml.safe_load((_ROOT / relative).read_text(encoding="utf-8"))


def _step(relative: Path, job: str, name: str) -> dict:
    """Return the step called ``name`` in ``job`` of a workflow."""
    steps = _load(relative)["jobs"][job]["steps"]
    found = [s for s in steps if s.get("name") == name]
    assert len(found) == 1, f"{relative.as_posix()}: expected one step {name!r} in job {job!r}"
    return found[0]


def _pypi(tmp_path: Path, version: str = _RELEASED, sha: str = _SDIST_SHA, filename: str | None = None) -> str:
    """Write a PyPI JSON API response for ``ducktide`` and return a ``file://`` base URL serving it.

    Args:
        tmp_path: Scratch directory.
        version: The version PyPI reports as published for the requested release.
        sha: The SHA256 PyPI reports for the sdist.
        filename: The sdist filename PyPI reports; defaults to the one for ``version``.

    Returns:
        A ``file://`` URL standing in for ``https://pypi.org/pypi``.
    """
    api = tmp_path / "pypi"
    target = api / "ducktide" / _RELEASED / "json"
    target.parent.mkdir(parents=True)
    sdist = {"packagetype": "sdist", "filename": filename or f"ducktide-{version}.tar.gz", "digests": {"sha256": sha}}
    wheel = {"packagetype": "bdist_wheel", "filename": f"ducktide-{version}-py3-none-any.whl"}
    target.write_text(json.dumps({"info": {"version": version}, "urls": [wheel, sdist]}), encoding="utf-8")
    return api.as_uri()


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """A checked-out release tag with the tooling beside it, and a fake grayskull and python on PATH.

    The workspace deliberately holds no ``.rhiza/scripts/`` of its own: it stands for a release
    tagged before the script was synced, which is exactly the tag a regeneration targets. The
    script is reachable only through the tooling checkout, as in the workflows.
    """
    workspace, bin_dir, state = tmp_path / "workspace", tmp_path / "bin", tmp_path / "state"
    for d in (workspace, bin_dir, state):
        d.mkdir()
    (workspace / "pyproject.toml").write_text('[project]\nname = "ducktide"\n', encoding="utf-8")
    tools = workspace / _TOOLS / ".rhiza" / "scripts"
    tools.mkdir(parents=True)
    shutil.copyfile(_SCRIPT, tools / "conda_recipe.py")

    fake = bin_dir / "grayskull"
    fake.write_text(_FAKE_GRAYSKULL, encoding="utf-8")
    python = bin_dir / "python"
    python.write_text(f'#!/usr/bin/env bash\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    for tool in (fake, python):
        tool.chmod(0o755)

    for name in _FAKE_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("STATE", str(state))
    monkeypatch.setenv("SDIST_SHA", _SDIST_SHA)
    return workspace, state


def _run(command: str, cwd: Path, **env: str) -> subprocess.CompletedProcess[str]:
    """Run a workflow ``run:`` block the way the runner does (bash -eo pipefail)."""
    return subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", command],
        cwd=cwd,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        check=False,
    )


def _generate_and_verify(relative, job, sandbox, api, summary: Path | None = None, **recipe_env: str):
    """Run an entry point's generate step, then its verify step, as the workflow would.

    Returns:
        The generate and verify processes.
    """
    workspace, _ = sandbox
    generate = _step(relative, job, "Generate conda recipe with grayskull")
    verify = _step(relative, job, "Verify conda recipe against the published sdist")
    assert verify["env"]["PYPI_JSON_API"] == "https://pypi.org/pypi"
    tag = f"v{_RELEASED}"
    generated = _run(generate["run"], workspace, TAG=tag, **recipe_env)
    extra = {"GITHUB_STEP_SUMMARY": str(summary)} if summary else {}
    verified = _run(verify["run"], workspace, TAG=tag, PYPI_JSON_API=api, **extra)
    return generated, verified


# ---------------------------------------------------------------------------
# Both entry points run the same code
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("relative", "job", "tag_expr"), _ENTRY_POINTS, ids=_ENTRY_IDS)
def test_entry_point_runs_the_shared_script(relative, job, tag_expr):
    """Generation and verification are one command each, identical in every workflow.

    The logic used to be inline YAML in the release workflow; a second copy for the retry
    workflow would have been free to drift from it, which is the failure #1746 is about.
    """
    generate = _step(relative, job, "Generate conda recipe with grayskull")
    verify = _step(relative, job, "Verify conda recipe against the published sdist")
    assert generate["run"].strip() == _GENERATE
    assert verify["run"].strip() == _VERIFY
    assert generate["env"]["TAG"] == tag_expr
    assert verify["env"]["TAG"] == tag_expr


@pytest.mark.parametrize(("relative", "job", "tag_expr"), _ENTRY_POINTS, ids=_ENTRY_IDS)
def test_tooling_comes_from_the_workflow_commit_not_the_tag(relative, job, tag_expr):
    """The script is read from ``github.sha``, so an older release tag need not contain it.

    The ``github`` bundle syncs the script together with both workflows, so the commit a
    workflow was read from always carries the matching script. Reading it from the release
    tag instead would make regenerating any release tagged before the sync impossible.
    """
    checkout = _step(relative, job, "Checkout conda recipe tooling")
    assert checkout["uses"].startswith("actions/checkout@")
    assert checkout["with"] == {"ref": "${{ github.sha }}", "path": _TOOLS, "persist-credentials": False}


def test_grayskull_pin_is_the_same_in_every_entry_point():
    """An unpinned grayskull changed the output format once already (#1701); both runs share one pin."""
    installs = {_step(p, job, "Install grayskull")["run"].strip() for p, job, _ in _ENTRY_POINTS}
    assert len(installs) == 1, f"grayskull is installed differently across entry points: {installs}"
    assert re.fullmatch(r'python -m pip install "grayskull==[\d.]+"', installs.pop())


@pytest.mark.parametrize(("relative", "job", "tag_expr"), _ENTRY_POINTS, ids=_ENTRY_IDS)
def test_entry_point_uploads_the_conda_recipe_artifact(relative, job, tag_expr):
    """Both runs hand over the same artifact, so instructions for one apply to the other."""
    upload = _step(relative, job, "Upload conda recipe artifact")
    assert upload["with"] == {"name": "conda-recipe", "path": "conda-recipe/meta.yaml"}


# ---------------------------------------------------------------------------
# Executing each entry point's steps
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("relative", "job", "tag_expr"), _ENTRY_POINTS, ids=_ENTRY_IDS)
def test_matching_recipe_passes_and_says_it_was_not_published(relative, job, tag_expr, sandbox, tmp_path):
    """The one passing case, and the summary that keeps generation apart from publication."""
    summary = tmp_path / "summary.md"
    generated, verified = _generate_and_verify(relative, job, sandbox, _pypi(tmp_path), summary=summary)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert f"conda recipe matches ducktide-{_RELEASED}.tar.gz" in verified.stdout
    workspace, state = sandbox
    assert (state / "requests").read_text().split() == [f"ducktide=={_RELEASED}"]
    assert (workspace / "conda-recipe" / "meta.yaml").is_file()
    text = summary.read_text()
    assert "not published" in text
    assert "staged-recipes" in text


@pytest.mark.parametrize(("relative", "job", "tag_expr"), _ENTRY_POINTS, ids=_ENTRY_IDS)
def test_recipe_for_an_older_release_fails(relative, job, tag_expr, sandbox, tmp_path):
    """Stale metadata: a recipe for the previous release is not a success for this one (#1746)."""
    _, verified = _generate_and_verify(relative, job, sandbox, _pypi(tmp_path), RECIPE_VERSION="1.2.2")
    assert verified.returncode == 1
    assert "version 1.2.2 != 1.2.3" in verified.stdout
    assert "source ducktide-1.2.2.tar.gz != published sdist ducktide-1.2.3.tar.gz" in verified.stdout


@pytest.mark.parametrize(("relative", "job", "tag_expr"), _ENTRY_POINTS, ids=_ENTRY_IDS)
def test_recipe_with_the_wrong_checksum_fails(relative, job, tag_expr, sandbox, tmp_path):
    """A recipe whose SHA256 is not the published sdist's would build something else."""
    _, verified = _generate_and_verify(relative, job, sandbox, _pypi(tmp_path), RECIPE_SHA="b" * 64)
    assert verified.returncode == 1
    assert "sha256 " + "b" * 64 in verified.stdout


@pytest.mark.parametrize(("relative", "job", "tag_expr"), _ENTRY_POINTS, ids=_ENTRY_IDS)
def test_recipe_pointing_at_another_source_fails(relative, job, tag_expr, sandbox, tmp_path):
    """A source URL naming a file PyPI did not publish for this release fails, checksum aside."""
    api = _pypi(tmp_path, filename=f"ducktide-{_RELEASED}.zip")
    _, verified = _generate_and_verify(relative, job, sandbox, api)
    assert verified.returncode == 1
    assert f"!= published sdist ducktide-{_RELEASED}.zip" in verified.stdout


@pytest.mark.parametrize(("relative", "job", "tag_expr"), _ENTRY_POINTS, ids=_ENTRY_IDS)
def test_missing_pypi_release_fails(relative, job, tag_expr, sandbox, tmp_path):
    """No PyPI metadata for the tagged version is an error, not a pass by default."""
    _, verified = _generate_and_verify(relative, job, sandbox, (tmp_path / "nowhere").as_uri())
    assert verified.returncode == 1
    assert f"could not read PyPI metadata for ducktide {_RELEASED}" in verified.stdout


@pytest.mark.parametrize("relative", _RECIPE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_regenerating_an_existing_release(relative, sandbox, tmp_path):
    """Regenerate the recipe for an old tag after newer releases, without publishing anything.

    PyPI's "latest" is 2.0.0 here and the tag is 1.2.3. The tag's checkout has no script of its
    own (see the ``sandbox`` fixture). The regenerated recipe must still describe 1.2.3
    exactly, and the run must not touch the newer release.
    """
    api_root = tmp_path / "pypi"
    api = _pypi(tmp_path)
    latest = api_root / "ducktide" / "json"
    latest.write_text(json.dumps({"info": {"version": "2.0.0"}, "urls": []}), encoding="utf-8")
    workspace, state = sandbox
    assert not (workspace / ".rhiza").exists()

    generated, verified = _generate_and_verify(relative, "recipe", sandbox, api)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert (state / "requests").read_text().split() == [f"ducktide=={_RELEASED}"]
    assert f'{{% set version = "{_RELEASED}" %}}' in (workspace / "conda-recipe" / "meta.yaml").read_text()


# ---------------------------------------------------------------------------
# rhiza_conda_recipe.yml: retry without republishing
# ---------------------------------------------------------------------------


def _triggers(workflow: dict) -> dict:
    """Return ``on:``; pyyaml parses the bare key ``on`` as ``True``."""
    return workflow.get(True, workflow.get("on")) or {}


@pytest.mark.parametrize("relative", _RECIPE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_recipe_workflow_is_dispatched_by_hand_for_a_tag(relative):
    """Only a person starts it, and only for a named tag: no push, schedule or call trigger."""
    triggers = _triggers(_load(relative))
    assert set(triggers) == {"workflow_dispatch"}
    tag = triggers["workflow_dispatch"]["inputs"]["tag"]
    assert tag["required"] is True
    assert tag["type"] == "string"


@pytest.mark.parametrize("relative", _RECIPE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_recipe_workflow_cannot_publish(relative):
    """``contents: read`` and nothing else: no id-token, no environment, no secrets.

    This is what makes a retry safe to run at any time. Without OIDC or a token it cannot
    reach PyPI, and without a write scope it cannot touch the tag or the release.
    """
    workflow = _load(relative)
    assert workflow["permissions"] == {"contents": "read"}
    for job_id, job in workflow["jobs"].items():
        assert job.get("permissions", {"contents": "read"}) == {"contents": "read"}, job_id
        assert "environment" not in job, job_id
    text = (_ROOT / relative).read_text(encoding="utf-8")
    assert not re.search(r"secrets\.\w", text)
    assert "pypi-publish" not in text
    assert "gh release" not in text


def _validate(relative: Path, tmp_path: Path, tag: str, exists: bool) -> subprocess.CompletedProcess[str]:
    """Run the recipe workflow's tag validation against a fake ``gh`` that knows one tag."""
    bin_dir = tmp_path / "gh-bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(f'#!/usr/bin/env bash\necho "$@" >> "{tmp_path}/gh-calls"\nexit {0 if exists else 1}\n')
    gh.chmod(0o755)
    step = _step(relative, "recipe", "Validate tag")
    assert step["env"]["TAG"] == "${{ inputs.tag }}"
    return _run(
        step["run"],
        tmp_path,
        TAG=tag,
        GITHUB_REPOSITORY="acme/ducktide",
        PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
    )


@pytest.mark.parametrize("relative", _RECIPE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_recipe_workflow_accepts_an_existing_tag(relative, tmp_path):
    """A well-formed tag that exists passes, and existence is asked of this repository."""
    result = _validate(relative, tmp_path, "v1.2.3", exists=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "repos/acme/ducktide/git/ref/tags/v1.2.3" in (tmp_path / "gh-calls").read_text()


@pytest.mark.parametrize("relative", _RECIPE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_recipe_workflow_refuses_a_tag_that_does_not_exist(relative, tmp_path):
    """Regeneration is for an existing release; a typo must not fall through to grayskull."""
    result = _validate(relative, tmp_path, "v9.9.9", exists=False)
    assert result.returncode == 1
    assert "does not exist" in result.stdout


@pytest.mark.parametrize("relative", _RECIPE_WORKFLOWS, ids=lambda p: p.as_posix())
@pytest.mark.parametrize("tag", ["1.2.3", "main", "v1.2.3; rm -rf /", ""])
def test_recipe_workflow_refuses_a_malformed_tag(relative, tmp_path, tag):
    """The release workflow's tag pattern applies, before anything is checked out."""
    result = _validate(relative, tmp_path, tag, exists=True)
    assert result.returncode == 1
    assert "Invalid release tag" in result.stdout
    assert not (tmp_path / "gh-calls").exists()


# ---------------------------------------------------------------------------
# rhiza_release.yml: generation stays non-blocking and is reported as such
# ---------------------------------------------------------------------------


def _release_note(relative: Path, tmp_path: Path, result: str) -> str:
    """Run the release's conda note step for a given ``conda`` job result and return its message."""
    step = _step(relative, "finalise-release", "Generate Conda Recipe Note")
    output = tmp_path / f"output-{result}"
    ran = _run(step["run"], tmp_path, CONDA_RESULT=result, TAG="v1.2.3", GITHUB_OUTPUT=str(output))
    assert ran.returncode == 0, ran.stdout + ran.stderr
    return output.read_text()


@pytest.mark.parametrize("relative", _RELEASE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_release_note_distinguishes_generation_from_publication(relative, tmp_path):
    """A successful run says where the recipe is and that conda-forge still has to receive it."""
    note = _release_note(relative, tmp_path, "success")
    assert "not published to conda-forge" in note
    assert "`conda-recipe` workflow artifact" in note
    assert "staged-recipes" in note


@pytest.mark.parametrize("relative", _RELEASE_WORKFLOWS, ids=lambda p: p.as_posix())
def test_release_note_points_a_failed_generation_at_the_recipe_workflow(relative, tmp_path):
    """The conda job never blocks the release (#1537), so its failure must be visible in the notes."""
    step = _step(relative, "finalise-release", "Generate Conda Recipe Note")
    assert "needs.conda.result == 'failure'" in step["if"]
    note = _release_note(relative, tmp_path, "failure")
    recipe_name = _load(_BUNDLE / _RECIPE)["name"]
    assert f"`{recipe_name}`" in note
    assert "without republishing" in note


# ---------------------------------------------------------------------------
# The module itself
# ---------------------------------------------------------------------------


def test_generate_retries_when_grayskull_exits_zero_on_a_404(sandbox, monkeypatch):
    """A 404 that exits 0 must still be retried, a minute apart by default (#1701).

    ``grayskull pypi`` reports a missing package and exits 0, so a loop that trusted the
    exit status broke out on the first attempt -- the retry written for exactly this case
    never ran. ducktide v0.0.1 is the record of it.
    """
    workspace, state = sandbox
    monkeypatch.setenv("MISSING", "2")
    sleeps: list[float] = []
    recipe = conda_recipe.generate(workspace, f"v{_RELEASED}", sleep=sleeps.append)
    assert recipe == workspace / "conda-recipe" / "meta.yaml"
    assert (state / "calls").read_text().strip() == "3"
    assert sleeps == [60, 60]


def test_generate_gives_up_after_max_attempts(sandbox, monkeypatch):
    """Metadata that never appears fails after the last attempt, not before it."""
    workspace, state = sandbox
    monkeypatch.setenv("MISSING", "99")
    sleeps: list[float] = []
    with pytest.raises(conda_recipe.RecipeError, match=r"no meta\.yaml after 5 attempts"):
        conda_recipe.generate(workspace, f"v{_RELEASED}", sleep=sleeps.append)
    assert (state / "calls").read_text().strip() == "5"
    assert len(sleeps) == 4


def test_generate_fails_fast_when_grayskull_itself_fails(sandbox, monkeypatch):
    """A non-zero exit is a real error, not PyPI lag, so it is not retried (#1701)."""
    workspace, state = sandbox
    monkeypatch.setenv("CRASH", "1")
    with pytest.raises(conda_recipe.RecipeError, match="not a PyPI propagation delay"):
        conda_recipe.generate(workspace, f"v{_RELEASED}", sleep=pytest.fail)
    assert (state / "calls").read_text().strip() == "1"


def test_generate_asks_grayskull_for_a_meta_yaml():
    """Grayskull >= 3.2 writes a V1 ``recipe.yaml`` by default; the artifact is ``meta.yaml`` (#1701)."""
    assert "--no-use-v1-format" in conda_recipe.GRAYSKULL_FLAGS


def test_generate_without_grayskull_fails(tmp_path, monkeypatch):
    """A missing grayskull is reported as such rather than as a PyPI problem."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ducktide"\n')
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    with pytest.raises(conda_recipe.RecipeError, match="grayskull is not installed"):
        conda_recipe.generate(tmp_path, "v1.2.3")


@pytest.mark.parametrize("tag", ["1.2.3", "main", ""])
def test_release_version_rejects_non_release_tags(tag):
    """The script enforces the tag pattern itself, whichever workflow called it."""
    with pytest.raises(conda_recipe.RecipeError, match="invalid release tag"):
        conda_recipe.release_version(tag)


def test_package_name_requires_a_project_table(tmp_path):
    """A project without ``[project].name`` cannot have a PyPI recipe."""
    (tmp_path / "pyproject.toml").write_text("[tool.x]\n")
    with pytest.raises(conda_recipe.RecipeError, match=r"\[project\]\.name"):
        conda_recipe.package_name(tmp_path)


@pytest.mark.parametrize(
    ("text", "message"),
    [("{{ other }}", "unsupported expression"), ("{{ version|upper }}", "unsupported filter")],
)
def test_render_refuses_what_it_cannot_verify(text, message):
    """An expression outside the supported set fails as "cannot verify" rather than passing."""
    with pytest.raises(conda_recipe.RecipeError, match=message):
        conda_recipe._render(text, {"version": "1.2.3"})


def test_verify_without_a_recipe_fails(tmp_path):
    """Verify run before generate (or after a failed one) is an error."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ducktide"\n')
    with pytest.raises(conda_recipe.RecipeError, match="no generated recipe"):
        conda_recipe.verify(tmp_path, f"v{_RELEASED}", _pypi(tmp_path))


def test_verify_without_a_field_fails(tmp_path):
    """A recipe missing a line it is checked on cannot pass."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ducktide"\n')
    (tmp_path / "conda-recipe").mkdir()
    (tmp_path / "conda-recipe" / "meta.yaml").write_text("package:\n  version: 1.2.3\n")
    with pytest.raises(conda_recipe.RecipeError, match="no url: line"):
        conda_recipe.verify(tmp_path, f"v{_RELEASED}", _pypi(tmp_path))


def test_verify_needs_exactly_one_sdist(tmp_path):
    """Without exactly one sdist there is nothing unambiguous to verify against."""
    api = tmp_path / "pypi" / "ducktide" / _RELEASED / "json"
    api.parent.mkdir(parents=True)
    api.write_text(json.dumps({"info": {"version": _RELEASED}, "urls": []}))
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ducktide"\n')
    with pytest.raises(conda_recipe.RecipeError, match="lists 0 sdists"):
        conda_recipe.verify(tmp_path, f"v{_RELEASED}", (tmp_path / "pypi").as_uri())


def test_main_reports_errors_as_annotations(tmp_path, capsys):
    """Expected failures exit 1 with a workflow ``::error::`` line, not a traceback."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ducktide"\n')
    assert conda_recipe.main(["verify", "--project", str(tmp_path)], {"TAG": "main"}) == 1
    assert "::error::invalid release tag 'main'" in capsys.readouterr().out


def test_defaults_wait_for_pypi_long_enough():
    """Five attempts a minute apart: a first release has nothing on PyPI to fall back on (#1537)."""
    assert conda_recipe.ATTEMPTS == 5
    assert conda_recipe.RETRY_SECONDS == 60
