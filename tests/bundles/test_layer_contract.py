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

import re
import tomllib

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
class TestALayersAllIsSatisfiableOnItsOwn:
    """`core` + one language layer must be enough to run that layer's `all`.

    This is the invariant #1475 established. `python.mk`'s `all` named `test`,
    `typecheck`, `security` and `docs-coverage` while the `tests` bundle defined them,
    and nothing made `tests` arrive — the dependency runs the other way. So
    `core + python-core` had an `all` that died on a missing rule, while the Rust and Go
    layers were self-contained. No shipped profile reached it (all three Python profiles
    select `tests`), which is exactly why it went unnoticed; a hand-written
    `.rhiza/template.yml` of `[core, python-core]` did.

    Parametrised over all three layers rather than written for Python, because the point
    is the property, not the one instance of it that was broken.
    """

    def test_every_prerequisite_of_all_has_a_rule(self, tmp_path, root, layer):
        """Each name in `all`'s prerequisite list is defined by some synced fragment."""
        sync_bundles(root, ["core", layer], tmp_path)
        fragments = list((tmp_path / ".rhiza").rglob("*.mk"))
        assert fragments, f"{layer} synced no make fragments"

        text = {f: f.read_text(encoding="utf-8") for f in fragments}

        all_line = next(
            (line for body in text.values() for line in body.splitlines() if line.startswith("all:")),
            None,
        )
        assert all_line, f"{layer} defines no `all` target"
        prerequisites = all_line.split("##")[0].split(":", 1)[1].split()

        defined = {
            line.split(":", 1)[0].rstrip(":")
            for body in text.values()
            for line in body.splitlines()
            if re.match(r"^[a-z][a-z0-9-]*::? ", line) or re.match(r"^[a-z][a-z0-9-]*::?$", line)
        }

        missing = [name for name in prerequisites if name not in defined]
        assert not missing, (
            f"`make all` on core + {layer} names {missing}, which no synced fragment defines. "
            f"Either the layer must define them or they belong in core — a gate that only "
            f"resolves once another bundle happens to be selected is not part of the contract."
        )


class TestEveryLayerDefinesTheSameGateNames:
    """The layers must agree on gate *names*, whatever engine backs each one.

    The whole claim of the language-layer split is "same target names, different
    recipes" — that is what lets book.mk, the CI workflows and the docs call a gate
    without knowing the language. `deptry` was the one row that broke it (#1474):
    python-core named the unused-dependency gate after the tool while rust-core and
    go-core called it `deps`, so `make deps` failed on Python and `make deptry` on the
    other two, and no language-neutral caller could invoke it at all.

    CLAUDE.md documented the divergence, which is not the same as it being intended.
    This test is why the next one fails instead of getting written down.
    """

    # Deliberately not `install`/`all` — `tests/api/test_language_layer.py` covers those
    # behaviourally. These are the gates a caller reaches for by name.
    GATES = ("test", "typecheck", "security", "docs-coverage", "license", "deps")

    @pytest.mark.parametrize("gate", GATES)
    def test_all_three_layers_define_the_gate(self, tmp_path, root, gate):
        """Each gate name must be defined by every language layer."""
        missing = []
        for layer in ("python-core", "rust-core", "go-core"):
            project = tmp_path / layer
            sync_bundles(root, ["core", layer], project)
            defined = {
                line.split(":", 1)[0]
                for fragment in (project / ".rhiza").rglob("*.mk")
                for line in fragment.read_text(encoding="utf-8").splitlines()
                if re.match(r"^[a-z][a-z0-9-]*::? ", line)
            }
            if gate not in defined:
                missing.append(layer)

        assert not missing, (
            f"`{gate}` is not defined by {missing}. A gate the other layers provide under "
            f"this name makes the contract language-specific: a caller has to know what the "
            f"project is written in before it can run the gate."
        )
