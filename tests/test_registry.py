"""The positive control for every test that derives an expectation from the pinned CLI.

#1580 bumped rhiza-task across two majors and broke three tests. Neither break was the bump's
fault: both were derivations that **narrowed** instead of failing.

- Three modules read the task registry after importing a hand-written list of task modules.
  1.1.0 gave ``book`` a ``paper`` prerequisite, ``paper`` lived in a module no list named, and
  the assertion reported a missing task where the gap was its own fixture.
- ``TestToolClaims`` decided which tools "run" by text-scanning the CLI's source, so a new
  docstring *explaining* that pip-audit is not wired up registered as an invocation.

The second surfaced as a red test only because it already had a control --
``test_the_invocation_scan_found_something``. Without that, the scan could have returned an
empty set and every doc-claim assertion would have passed vacuously. The registry derivations
had no equivalent, and failed loudly this time only by luck: the narrowed registry happened to
be missing a name that another assertion looked at. A narrowing in a direction nothing checked
would have been silent.

This module is that missing control, and it is deliberately in ``tests/`` root rather than
beside one of the callers: the property belongs to :mod:`tests.registry`, which all of them
now share, not to any one of them.
"""

from __future__ import annotations

import pytest

from tests import registry as reg


def test_the_pin_is_readable() -> None:
    """Everything here rests on finding the pin in the shim; assert that first."""
    assert reg.pin(), (
        "the root Makefile no longer pins RHIZA_TASK, so every registry-derived test in this "
        "suite silently degrades to a skip"
    )


def test_the_registry_loads_and_carries_its_anchors() -> None:
    """The registry must be reachable and plausible -- the control the derivations lacked.

    :func:`tests.registry.load` asserts the anchors itself, so reaching this line at all is
    most of the property. Restated here as a named test so a failure says *this* rather than
    surfacing inside whichever unrelated assertion happened to touch the registry first.
    """
    loaded = reg.load()
    if loaded is None:
        pytest.skip(f"could not read the task registry from {reg.pin()}")
    assert len(loaded) > 20, (
        f"the registry holds only {len(loaded)} task(s), which is fewer than any released "
        f"rhiza-task has carried. A derivation this thin measures almost nothing (#1584)."
    )


def test_both_kinds_of_key_are_present() -> None:
    """Layer-scoped and neutral keys must both appear, because a narrowing can drop one.

    This is the shape of the #1580 failure rather than a restatement of the anchor list: a
    partial set of task modules yields a registry that looks populated while missing a whole
    category. ``fmt`` is neutral (it answers to its bare name, which is what ``core`` was) and
    ``python:test`` is layer-scoped, so requiring one of each catches a derivation that
    resolved only half the registry.
    """
    loaded = reg.require()
    assert any(":" in key for key in loaded), "no layer-scoped keys at all, so no layer's tasks loaded"
    assert any(":" not in key for key in loaded), "no neutral keys at all, so the language-neutral tasks did not load"


def test_resolves_prefers_the_layer_then_falls_back_to_neutral() -> None:
    """``resolves`` must answer for both key shapes, or half the callers are wrong.

    ``test`` exists per layer, ``fmt`` only neutrally, and a caller asking about either must
    get True. A ``resolves`` that only checked the layer-scoped form would silently report
    every neutral task as missing.
    """
    loaded = reg.require()
    assert reg.resolves(loaded, "python", "test"), "a layer-scoped gate must resolve for its own layer"
    assert reg.resolves(loaded, "python", "fmt"), "a neutral task must resolve for any layer"
    assert not reg.resolves(loaded, "python", "definitely-not-a-task"), (
        "resolves() answers True for a name nothing registers, so every assertion built on it is vacuous"
    )


def test_an_unavailable_cli_is_a_skip_and_not_an_empty_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    """``require`` must skip when the CLI is unreachable, never hand back an empty registry.

    The old helper returned ``{}`` for both "could not run the CLI" and "the CLI said
    nothing", which is what let a narrowed derivation read as an outage. Asserted by
    monkeypatching the loader, because the real unavailable case cannot be produced on a
    machine that has ``uv`` -- and ``env -i`` breaks the network in this sandbox rather than
    only the PATH.
    """
    monkeypatch.setattr(reg, "load", lambda: None)
    with pytest.raises(BaseException, match="could not read the task registry") as excinfo:
        reg.require()
    assert excinfo.type is pytest.skip.Exception, (
        f"require() raised {excinfo.type.__name__} rather than skipping, so an offline run "
        f"fails the suite instead of reporting the gate as unmeasured"
    )
