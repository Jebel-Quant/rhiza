"""Tests for the repository-owned `book` target overrides."""

from __future__ import annotations

from tests.util import run_make, strip_ansi


def test_book_target_default_packages_do_not_use_editable_install(logger):
    """The default book target should not request `--with-editable .`."""
    result = run_make(logger, ["book"], dry_run=True)
    output = strip_ansi(result.stdout)

    assert "--with-editable ." not in output
    assert "--with 'mkdocstrings[python]'" in output
