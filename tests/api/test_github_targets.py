"""Tests for the GitHub Makefile targets using safe dry-runs.

These tests validate that the .github/github.mk targets are correctly exposed
and emit the expected commands without actually executing them.
"""

from __future__ import annotations

import sys

import pytest

# setup_tmp_makefile (autouse) comes from the api/ conftest; run_make is a shared
# helper imported directly from test_utils.
from tests.util import run_make

# The gh helper targets are POSIX shell recipes driven through `make`; they don't
# run under Windows' make/shell, so skip the module there (matches the repo's
# other make/POSIX-shell tests, e.g. test_ci_workflow).
pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="exercises POSIX make + gh targets via a shell; unsupported on Windows",
)

# Every GitHub helper target defined in github.mk. `github.mk` is one of the five fragments that
# survive the rhiza-task migration -- rhiza-task has no task for any of these, and `github` is in
# the `github-project` profile, so retiring it would take `make view-prs` from consumers on the
# flagship profile (Jebel-Quant/rhiza-task#20).
_GH_TARGETS = (
    "gh-install",
    "view-prs",
    "view-issues",
    "failed-workflows",
    "whoami",
    "workflow-status",
    "latest-release",
)

# Map each target to a substring that must appear in its dry-run output, proving
# the recipe emits the intended command rather than merely parsing. Under `make -n`
# even @-prefixed recipe lines are printed, so the command text is observable.
_TARGET_COMMANDS = (
    ("gh-install", "command -v gh"),
    ("view-prs", "gh pr list"),
    ("view-issues", "gh issue list"),
    ("failed-workflows", "gh run list"),
    ("whoami", "gh auth status"),
    ("workflow-status", "gh workflow list"),
    ("latest-release", "gh release view"),
)


def test_gh_targets_exist(logger):
    """Verify that every GitHub target resolves.

    Asserted by resolution rather than by appearing in ``make help``, which is what this checked
    before. Under the shim ``help`` runs the CLI's own ``list``, and the CLI knows nothing about
    the fragments the shim ``-include``s -- so these targets work while being absent from help.
    That discoverability gap is real and recorded in Jebel-Quant/rhiza-task#20; it is not this
    test's subject, and asserting on help output would fail for a reason unrelated to gh.
    """
    for target in _GH_TARGETS:
        result = run_make(logger, [target], check=False)
        assert result.returncode == 0, f"`make {target}` did not resolve: {result.stderr}"
        assert "no rule to make target" not in result.stderr.lower(), (
            f"{target} is not defined -- github.mk should still be included by the shim"
        )


@pytest.mark.parametrize(("target", "expected_command"), _TARGET_COMMANDS)
def test_gh_target_emits_command(logger, target, expected_command):
    """Verify each GitHub target dry-runs cleanly and emits its expected command."""
    result = run_make(logger, [target])
    assert result.returncode == 0
    assert expected_command in result.stdout, (
        f"Target {target} did not emit expected command {expected_command!r}; got:\n{result.stdout}"
    )
