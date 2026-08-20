"""Tests for the Makefile targets and help output using safe dry-runs.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

These tests validate that the Makefile exposes expected targets and emits
the correct commands without actually executing them, by invoking `make -n`
(dry-run). We also pass `-s` to reduce noise in CI logs. This approach keeps
tests fast, portable, and free of side effects like network or environment
changes.
"""

from __future__ import annotations

import re
from pathlib import Path


def assert_uvx_command_uses_version(output: str, tmp_path, command_fragment: str):
    """Assert uvx command uses .python-version when present, else fallback checks."""
    python_version_file = tmp_path / ".python-version"
    if python_version_file.exists():
        python_version = python_version_file.read_text().strip()
        assert f"uvx -p {python_version} {command_fragment}" in output
    else:
        assert "uvx -p" in output
        assert command_fragment in output


# ``TestMakefile`` lived here: 27 dry-run assertions over the gate recipes in ``python.mk``,
# ``quality.mk``, ``test.mk``, ``book.mk``, ``bootstrap.mk`` and ``doctor.mk`` -- that ``fmt`` ran
# prek, that ``typecheck`` invoked both checkers, that ``test`` passed the coverage flags, and so
# on. Those fragments retired to rhiza-task, so there is no recipe left to dry-run: every one of
# those targets is now a task the shim forwards to, and ``make -n test`` prints one line.
#
# The assertions are not simply dropped. rhiza-task carries its own suite for the recipes, and
# ``tests/e2e/`` runs each layer's gates against an assembled project for real -- which is a
# stronger check than a dry run ever was, since it catches wrong flags rather than only wrong
# text. What remains here is the part that is *this repo's* business: what its own front door
# must be.


class TestMakefileRootFixture:
    """What this repo's own root Makefile must be, now that ``core`` ships it.

    Every other test in this module runs against a tmp_path assembled from ``bundles/``, so
    they assert what a *consumer* receives. These assert what the *mother repo* runs -- and
    the two answers converged again when the front door went back into the template: the
    root file is a dogfood symlink, so there is one copy and both questions have one answer.

    The assertion that used to live here grepped the Makefile and its ``.rhiza/make.d``
    fragments for ``install:``/``fmt:``/``test:``/``deps:``. That cannot survive the shim and
    should not: the whole point is that those names are *not* in the file any more -- a `%:`
    catch-all forwards them to the CLI. Grepping for target names would have to be deleted
    or weakened on every migration; asserting the forwarding contract holds instead.
    """

    def test_makefile_is_a_dogfood_symlink_into_core(self, root: Path) -> None:
        """The root Makefile must be a symlink into ``bundles/core/``.

        It was deliberately a real file for as long as ``uvx rhiza-task shim`` printed it: a
        link would then have shipped the mother repo's own front door, which at the time
        carried its ``e2e``/``sync-self`` targets. Those live in ``local.mk`` now and
        :meth:`test_makefile_carries_no_repo_owned_rule` keeps them there, so the exception
        had nothing left to protect -- and a real copy of a template file is drift waiting to
        happen, which is the whole reason for the dogfood invariant.
        """
        makefile = root / "Makefile"
        assert makefile.is_file(), "the root Makefile is missing"
        assert makefile.is_symlink(), (
            "the root Makefile is a real file again -- `core` owns the front door, so a copy "
            "here can diverge from what consumers receive (run `make sync-self`)"
        )
        assert makefile.resolve() == (root / "bundles" / "core" / "Makefile").resolve(), (
            "the root Makefile points somewhere other than bundles/core/Makefile"
        )

    def test_makefile_forwards_unknown_targets_to_a_pinned_cli(self, root: Path) -> None:
        """The shim's contract: a catch-all rule, a pinned version, and no gate recipes."""
        content = (root / "Makefile").read_text(encoding="utf-8")

        assert re.search(r"^RHIZA_TASK \?= rhiza-task@\d+\.\d+\.\d+", content, re.MULTILINE), (
            "the shim must pin rhiza-task to an exact version: an unpinned CLI is a gate that moves under you"
        )
        assert re.search(r"^%:", content, re.MULTILINE), "without the `%:` catch-all no gate resolves at all"

    def test_makefile_puts_the_bootstrapped_uv_on_path(self, root: Path) -> None:
        """The shim must export PATH, or every gate fails on a runner without uv.

        The shim through 0.3.0 deliberately omitted this ("no PATH export") and reached the
        CLI by absolute path. That is enough to *start* it and not enough to let it work:
        rhiza-task's task bodies shell out to bare ``uv``/``uvx``, so the first gate dies
        with ``FileNotFoundError: 'uvx'``. 0.3.1 ships the export, so this is no longer a
        mother-repo addition -- but it is still the line whose loss makes the branch
        unmergeable, which is what this test exists to catch, whoever owns it.

        Pinned because it is load-bearing for a *required* check. The ``pre-commit`` job runs
        ``make fmt`` with no ``astral-sh/setup-uv`` step, and ``Pre-commit hooks`` is required
        in ``.github/rulesets/main-branch-protection.json`` — so losing this line makes the
        branch unmergeable, which is exactly what happened on the first push of the migration.

        Asserted as a prepend, not merely a mention: appending leaves a runner with an older
        uv earlier on PATH resolving differently from a bare one, which would quietly make
        ``RHIZA_TASK`` no longer the whole version contract. See Jebel-Quant/rhiza-task#19.
        """
        content = (root / "Makefile").read_text(encoding="utf-8")
        assert re.search(r"^export PATH := \$\(INSTALL_DIR\):\$\(PATH\)", content, re.MULTILINE), (
            "the Makefile must prepend $(INSTALL_DIR) to PATH, or a runner without uv fails "
            "every gate once the shim has bootstrapped it (rhiza-task#19)"
        )

    def test_local_mk_keeps_the_mother_repo_only_targets(self, root: Path) -> None:
        """The targets rehomed from the retired .rhiza/make.d/bundles.mk.

        They live in ``local.mk``, which the Makefile ``-include``s, so the front door can be
        a template-owned file with nothing repo-specific in it -- see
        :meth:`test_makefile_carries_no_repo_owned_rule`. That separation is now load-bearing
        rather than tidy: the Makefile is synced, so anything put in it is lost at the next
        ``/rhiza:update``, and ``make e2e`` is what rhiza_e2e.yml runs in all three language
        jobs.
        """
        content = (root / "local.mk").read_text(encoding="utf-8")
        for target in ("explain-bundles", "sync-self", "sync-self-check", "e2e"):
            assert re.search(rf"^{re.escape(target)}:", content, re.MULTILINE), (
                f"`{target}` must be an explicit rule -- the `%:` catch-all would otherwise "
                f"forward it to the CLI, which has no such task"
            )

    def test_local_mk_is_committed(self, root: Path) -> None:
        """``local.mk`` must not be ignored here, or CI loses ``make e2e`` silently.

        ``bundles/core/.gitignore`` deliberately leaves it committable (#1574), and this is the
        case that forced it: with the ``Makefile`` synced, ``local.mk`` is the *only* place a
        repo-owned target can live, so ignoring it would leave a consumer nowhere to put one.
        A rule re-added there would not fail anything either: the file stays on disk, so every
        local run keeps working, and only a fresh CI checkout finds no rule to make target `e2e`.
        """
        assert (root / "local.mk").is_file()
        ignored = (root / ".gitignore").read_text(encoding="utf-8")
        assert not re.search(r"^local\.mk$", ignored, re.MULTILINE), (
            "local.mk carries this repo's own targets and must stay committed -- "
            "rhiza_e2e.yml runs `make e2e` in all three language jobs"
        )

    def test_makefile_carries_no_repo_owned_rule(self, root: Path) -> None:
        """The Makefile must define nothing beyond the shim's own rules.

        This is what makes a version bump an overwrite rather than a merge: sync, and nothing
        repo-specific is lost because nothing repo-specific is there. The moment a target is
        appended below the shim again, the next ``/rhiza:update`` silently drops it -- and
        since the file became template-owned, that is a sync away rather than a deliberate
        regeneration.

        Checked by name rather than by diffing against anything: there is nothing left to
        diff against. While ``rhiza-task shim`` printed this file, the honest comparison was
        against the *published* CLI's output -- and this repo ran a hand-carried variant of
        it (the ``UV`` alias, ``FORCE``, the ``help`` extension), so the diff was noise. One
        template-owned copy replaces both the generator and the fork of it.
        """
        content = (root / "Makefile").read_text(encoding="utf-8")
        defined = {
            match.group(1)
            for match in re.finditer(r"^([^\s:#=]+)\s*::?(?!=)", content, re.MULTILINE)
            if not match.group(1).startswith(".")
        }
        assert defined <= {"help", "$(UVX)", "$(UV)", "FORCE", "local.mk", "Makefile", "%"}, (
            f"the root Makefile has grown repo-owned rules ({sorted(defined)}) -- they belong "
            f"in local.mk, or a rhiza-task bump regenerating this file will drop them"
        )
