"""core must ship no ``.rhiza/.env``.

The rest of this module tested that file's *precedence* — that a value in it overrode
``rhiza.mk``'s ``?=`` default, and that an exported ``RHIZA_CI_OS_MATRIX`` survived a populated
file. Both were assertions about make's variable rules, read out of ``make -n`` output, and
``rhiza.mk`` no longer exists: the CLI resolves settings through six explicit layers instead,
tested in rhiza-task where that code lives.

What is left is the invariant that made those tests necessary in the first place, and it belongs
to the *bundle* rather than to make: a template-owned assignment outranks an exported environment
variable, so shipping any ``.rhiza/.env`` at all takes those variables out of a caller's reach.
That is the mechanism of #1545, and a file that ships no values cannot repeat it.
"""

from __future__ import annotations

from pathlib import Path


class TestCoreShipsNoEnvFile:
    """Pin the absence, so it cannot creep back."""

    def test_core_ships_no_env_file_at_all(self, root: Path):
        """Core must ship no `.rhiza/.env`, which is what makes #1545 unrepeatable.

        This replaces an assertion that the shipped file merely left
        RHIZA_CI_OS_MATRIX unset. Checking one line inside the file treated the
        pinning as the bug; the bug was that a *template-owned* makefile fragment
        could name any variable at all, because a makefile assignment outranks an
        exported environment variable and so removes it from the workflow's reach.
        The two values it did carry — SOURCE_FOLDER, MARIMO_FOLDER — were identical
        to rhiza.mk's `?=` defaults, so deleting the file changed no resolved value
        and removed the only mechanism by which a synced file could shadow a caller.

        Asserted against the bundle source, so the failure names the cause directly
        if someone reinstates the file. A *consumer's own* .rhiza/.env stays
        supported: rhiza.mk still `-include`s it, and the two tests above pin that a
        present file does not break the matrix hand-off.
        """
        shipped = root / "bundles" / "core" / ".rhiza" / ".env"
        assert not shipped.exists(), (
            f"{shipped} must not exist: a template-owned assignment outranks the export "
            f"rhiza_ci.yml uses to select the matrix per caller (#1526, #1545). Project "
            f"settings belong in a [tool.rhiza-task] table in pyproject.toml."
        )
