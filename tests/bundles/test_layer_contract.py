"""Properties that must hold across every language layer, not within one.

Split from ``test_bundle_sync.py`` in #1514, where they sat below 750 lines of
layer-specific sync assertions despite being the module's most load-bearing tests.

Each is a guard against a divergence that already happened once:

- ``TestNonPythonLayersShipADiscoverableBumpversionConfig`` — bump-my-version reads only
  four filenames and silently falls back to ``git describe`` when it finds none (#1453).
- ``TestALayersAllIsSatisfiableOnItsOwn`` — ``core + python-core`` alone once had an
  ``all`` that died on a missing rule, because the Python gates lived in the separate
  ``tests`` bundle while ``python.mk``'s ``all`` named them (#1475).
- ``TestEveryLayerDefinesTheSameGateNames`` — ``deps`` was named ``deptry`` on Python and
  ``deps`` everywhere else, so no language-neutral caller could invoke it (#1474).
"""

from __future__ import annotations

import functools
import json
import re
import subprocess  # nosec B404
import tomllib
from pathlib import Path

import pytest

from tests.util import sync_bundles


class TestNonPythonLayersShipADiscoverableBumpversionConfig:
    """Rust and Go must land their version config where bump-my-version looks (#1453).

    A Rust or Go repo has none of the four filenames bump-my-version searches, so
    unlike Python it cannot be told to put the block in a file it already owns — the
    layer has to ship one. That makes the placement load-bearing: the same config at
    ``.rhiza/.cfg.toml`` (where these layers used to put it) is never read, and the
    tool responds to finding no config by falling back to ``git describe`` instead of
    failing. A release then gets cut against whatever the last reachable tag says.
    """

    LAYERS = ("rust-core", "go-core")

    @pytest.fixture(params=LAYERS)
    def synced(self, request, tmp_path, root):
        """Sync one non-Python language layer and return (name, project dir)."""
        sync_bundles(root, ["core", request.param], tmp_path)
        return request.param, tmp_path

    def test_the_config_is_at_a_discovered_path(self, synced):
        """`.bumpversion.toml` is searched first; `.rhiza/.cfg.toml` is never searched."""
        layer, project = synced
        assert (project / ".bumpversion.toml").is_file(), f"{layer} ships no discoverable bumpversion config"
        assert not (project / ".rhiza" / ".cfg.toml").exists(), (
            f"{layer} still ships the inert .rhiza/.cfg.toml copy — bump-my-version never reads it"
        )

    def test_the_config_carries_no_current_version(self, synced):
        """A synced file must not own a value only the consuming repo can maintain.

        ``current_version`` would be reset to the template's number by every
        ``/rhiza:update``. Leaving it out makes bump-my-version read the version from
        the newest tag matching ``tag_name`` instead, which is what these layers want:
        a Go module's version *is* its tag, and a Rust crate's Cargo.toml is expected
        to agree with it.
        """
        layer, project = synced
        with (project / ".bumpversion.toml").open("rb") as fh:
            cfg = tomllib.load(fh)["tool"]["bumpversion"]
        assert "current_version" not in cfg, f"{layer}: a synced config cannot own the repo's version"
        assert cfg["tag_name"] == "v{new_version}", (
            f"{layer}: tag_name is also the pattern the current version is read from, so it must "
            f"match the tags the release flow creates"
        )

    @pytest.mark.parametrize("key", ["commit", "tag"])
    def test_the_release_flow_owns_the_commit_and_the_tag(self, synced, key):
        """`/rhiza:release` folds the changelog into the bump commit and tags it itself."""
        layer, project = synced
        with (project / ".bumpversion.toml").open("rb") as fh:
            cfg = tomllib.load(fh)["tool"]["bumpversion"]
        assert cfg[key] is False, (
            f"{layer}: {key} = true makes a bare `bump-my-version bump` duplicate what the release flow already does"
        )


@pytest.mark.parametrize("layer", ["python-core", "rust-core", "go-core"])
@functools.lru_cache(maxsize=1)
def _registry() -> dict[str, list[str]]:
    """Return the pinned CLI's task registry as ``{key: [prerequisite, ...]}``.

    Keys are ``layer:name`` for a layer-scoped task and bare ``name`` for a neutral one, which
    is how :mod:`rhiza_task.spec` stores them -- three layers may each define ``test``, and
    which one answers is decided per repository.

    The task modules must be imported before the registry is read: the ``@task`` decorator
    populates it at import time, and ``rhiza_task.tasks`` does not pull in its submodules.

    Returns:
        The registry, or an empty dict when the CLI cannot be reached.
    """
    root = Path(__file__).resolve().parents[2]
    match = re.search(r"^RHIZA_TASK \?= (\S+)", (root / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        return {}
    name, _, version = match.group(1).partition("@")
    script = (
        "import importlib, json;"
        "[importlib.import_module('rhiza_task.tasks.' + m)"
        " for m in ('python', 'rust', 'go', 'quality', 'book', 'extras', 'doctor')];"
        "from rhiza_task.spec import REGISTRY;"
        "print(json.dumps({k: list(v.needs) for k, v in REGISTRY.items()}))"
    )
    proc = subprocess.run(  # nosec B603
        [
            "uv",
            "run",
            "--quiet",
            "--no-project",
            "--with",
            f"{name}=={version}" if version else name,
            "python",
            "-c",
            script,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return json.loads(proc.stdout) if proc.returncode == 0 else {}


def _resolves(registry: dict[str, list[str]], layer: str, task: str) -> bool:
    """Report whether ``task`` resolves for ``layer``: layer-scoped first, then neutral.

    Args:
        registry: The task registry.
        layer: ``python``, ``rust`` or ``go``.
        task: A task name.

    Returns:
        True when some registered task answers that name for that layer.
    """
    return f"{layer}:{task}" in registry or task in registry


# The CLI's layer names, against the bundle names the rest of this module uses.
_LAYERS = {"python-core": "python", "rust-core": "rust", "go-core": "go"}


class TestALayersAllIsSatisfiableOnItsOwn:
    """One language layer must be enough to run that layer's `all`.

    This is the invariant #1475 established. `python.mk`'s `all` named `test`, `typecheck`,
    `security` and `docs-coverage` while the `tests` bundle defined them, and nothing made
    `tests` arrive — the dependency runs the other way. So `core + python-core` had an `all`
    that died on a missing rule, while the Rust and Go layers were self-contained.

    **Retargeted at the task registry**, because the layers ship no make fragments any more:
    the gates moved into rhiza-task, so "does every prerequisite of `all` have a rule" is now
    "does every prerequisite resolve to a registered task". Same property, and a stronger check
    than grepping three files' text — a name that resolves through the wrong layer fails here.
    """

    @pytest.mark.parametrize("layer", sorted(_LAYERS))
    def test_every_prerequisite_of_all_resolves(self, layer):
        """Each name in this layer's `all` must resolve to a registered task."""
        registry = _registry()
        if not registry:
            pytest.skip("could not read the rhiza-task registry")
        cli_layer = _LAYERS[layer]
        key = f"{cli_layer}:all"
        assert key in registry, f"{layer} defines no `all` task"

        missing = [name for name in registry[key] if not _resolves(registry, cli_layer, name)]
        assert not missing, (
            f"`all` on {layer} names {missing}, which resolve to no registered task. A gate that "
            f"only resolves once something else happens to be present is not part of the contract."
        )


class TestEveryLayerDefinesTheSameGateNames:
    """The layers must agree on gate *names*, whatever engine backs each one.

    The whole claim of the language-layer split is "same target names, different recipes" — that
    is what lets the CI workflows and the docs call a gate without knowing the language. `deptry`
    was the one row that broke it (#1474): python-core named the unused-dependency gate after the
    tool while rust-core and go-core called it `deps`, so no language-neutral caller could invoke
    it at all.

    CLAUDE.md documented the divergence, which is not the same as it being intended. This test is
    why the next one fails instead of getting written down — and it kept that job through the
    migration by moving from the fragments to the registry that replaced them.
    """

    # Deliberately not `install`/`all` — `tests/api/test_language_layer.py` covered those
    # behaviourally and rhiza-task tests them now. These are the gates a caller reaches by name.
    GATES = ("test", "typecheck", "security", "docs-coverage", "license", "deps", "coverage")

    @pytest.mark.parametrize("gate", GATES)
    def test_all_three_layers_define_the_gate(self, gate):
        """Each gate name must resolve for every language layer."""
        registry = _registry()
        if not registry:
            pytest.skip("could not read the rhiza-task registry")
        missing = [b for b, cli in sorted(_LAYERS.items()) if not _resolves(registry, cli, gate)]
        assert not missing, (
            f"`{gate}` does not resolve for {missing}. A gate the other layers provide under this "
            f"name makes the contract language-specific: a caller has to know what the project is "
            f"written in before it can run the gate."
        )
