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
    """What this repo's own root Makefile must be, now that it is the rhiza-task shim.

    Every other test in this module runs against a tmp_path assembled from ``bundles/``, so
    they assert what a *consumer* receives. These two assert what the *mother repo* runs,
    and the two answers deliberately differ: rhiza migrated to the shim first so the
    dogfooding proves it before any consumer is affected.

    The assertion that used to live here grepped the Makefile and its ``.rhiza/make.d``
    fragments for ``install:``/``fmt:``/``test:``/``deps:``. That cannot survive the shim and
    should not: the whole point is that those names are *not* in the file any more -- a `%:`
    catch-all forwards them to the CLI. Grepping for target names would have to be deleted
    or weakened on every migration; asserting the forwarding contract holds instead.
    """

    def test_makefile_exists_at_root(self, root: Path) -> None:
        """Makefile should exist at repository root, and be a real file, not a symlink.

        It stopped being a dogfood symlink into ``bundles/core/`` when it became the shim:
        it now carries this repo's own ``e2e``/``sync-self`` targets, which must not ship.
        """
        makefile = root / "Makefile"
        assert makefile.is_file()
        assert not makefile.is_symlink(), (
            "the root Makefile is repo-owned now -- a symlink into bundles/core/ would ship "
            "rhiza's own mother-repo targets to every consumer"
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

        The shipped shim deliberately omits this ("no PATH export") and reaches the CLI by
        absolute path. That is enough to *start* it and not enough to let it work:
        rhiza-task's task bodies shell out to bare ``uv``/``uvx``, so the first gate dies
        with ``FileNotFoundError: 'uvx'``.

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

    def test_makefile_keeps_the_mother_repo_only_targets(self, root: Path) -> None:
        """The five targets rehomed from the retired .rhiza/make.d/bundles.mk.

        They live in the Makefile rather than ``local.mk`` because ``local.mk`` is
        gitignored and CI invokes two of them -- ``make e2e`` from rhiza_e2e.yml and
        ``make gitlab-docker-test`` from rhiza_weekly.yml.
        """
        content = (root / "Makefile").read_text(encoding="utf-8")
        for target in ("explain-bundles", "sync-self", "sync-self-check", "e2e", "gitlab-docker-test"):
            assert re.search(rf"^{re.escape(target)}:", content, re.MULTILINE), (
                f"`{target}` must be an explicit rule -- the `%:` catch-all would otherwise "
                f"forward it to the CLI, which has no such task"
            )
