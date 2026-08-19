"""The book build's extra-package configuration, after the make layer retired.

This module tested ``MKDOCS_EXTRA_PACKAGES`` through ``make -n book``: the variable was defined
in ``book.mk``, and a dry run showed the ``--with`` flags it expanded into. Both halves are gone.
``book.mk`` retired with the rest of the covered fragments, and ``make book`` now delegates to
the CLI, so a dry run shows one line -- ``uvx rhiza-task@X.Y.Z book`` -- and the flags are
decided inside the task from ``mkdocs_extra_packages``.

What survives is the property that mattered, and it is here because it broke: migrating this
repo to the shim silently dropped its own override. The old root Makefile carried
``MKDOCS_EXTRA_PACKAGES = --with 'mkdocstrings[python]'`` above the include; replacing that file
with the shim lost the line, ``mkdocs_extra_packages`` defaults to empty, and ``make book``
built the site *successfully* without the plugin that renders the API reference. No failure,
just pages missing their generated content.
"""

from __future__ import annotations

import json
import re
import subprocess  # nosec B404
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _cli_setting(name: str) -> str:
    """Return one resolved setting from the pinned CLI.

    Args:
        name: A config field name.

    Returns:
        The resolved value as printed, whitespace-collapsed.
    """
    match = re.search(r"^RHIZA_TASK \?= (\S+)", (_ROOT / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        pytest.skip("the root Makefile no longer pins RHIZA_TASK")
    proc = subprocess.run(  # nosec B603
        ["uvx", match.group(1), "print", name],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        pytest.skip(f"could not read {name} from the CLI: {proc.stderr.strip()[:160]}")
    return " ".join(proc.stdout.split())


def test_book_build_still_gets_mkdocstrings() -> None:
    """This repo's book build must still pull in the mkdocstrings plugin.

    The regression guard for the override the shim migration dropped. Asserted against the
    *resolved* setting rather than against ``pyproject.toml``'s text, so it also catches the case
    where the table is present but some higher layer overrides it away.
    """
    assert "mkdocstrings" in _cli_setting("mkdocs_extra_packages"), (
        "mkdocs_extra_packages no longer includes mkdocstrings, so `make book` would build the "
        "site without the plugin that renders the API reference -- successfully, and with the "
        "generated pages missing. Set mkdocs-extra-packages in [tool.rhiza-task]."
    )


def test_extra_packages_are_bare_specs_not_flags() -> None:
    """The value must be package specs, not ``--with`` flags.

    The make variable held the flags (``--with 'mkdocstrings[python]'``); the CLI passes the
    value as ``withs=`` and adds ``--with`` itself. Carrying the old spelling across would
    produce ``--with --with`` and a uv usage error -- which is an easy mistake to make when
    porting the setting, and a confusing one to debug.
    """
    value = _cli_setting("mkdocs_extra_packages")
    assert "--with" not in value, (
        f"mkdocs_extra_packages is {value!r}; the CLI adds `--with` itself, so the setting must "
        f"hold bare specs such as 'mkdocstrings[python]'"
    )


def test_book_target_resolves_through_the_shim() -> None:
    """``make book`` must still resolve -- via the catch-all rather than a fragment recipe."""
    proc = subprocess.run(  # nosec B603
        ["make", "-n", "book"], cwd=_ROOT, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, f"`make book` did not resolve: {proc.stderr}"
    assert "no rule to make target" not in proc.stderr.lower()
    assert "rhiza-task" in proc.stdout, (
        f"`make book` should delegate to the CLI now that book.mk is retired, got: {proc.stdout!r}"
    )
    assert "--with-editable ." not in proc.stdout


def test_the_setting_is_declared_in_pyproject() -> None:
    """It must be committed, not merely resolvable.

    ``.rhiza/.env`` is gitignored, so a value set only there would work locally and vanish in
    CI -- the same trap that made the doctest scope wrapper necessary. Reading the table
    directly is the point: this asserts *where* the value lives.
    """
    import tomllib

    table = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["rhiza-task"]
    packages = table.get("mkdocs-extra-packages", [])
    assert any("mkdocstrings" in p for p in packages), (
        f"[tool.rhiza-task] mkdocs-extra-packages must name mkdocstrings; found {json.dumps(packages)}"
    )
