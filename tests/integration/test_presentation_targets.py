"""Tests for the Marp presentation Makefile targets and their resilience.

Mirrors test_book_targets.py: the presentation bundle ships make targets
(presentation, presentation-pdf, presentation-serve) in
.rhiza/make.d/presentation.mk, and this exercises them end-to-end against a
synced repo rather than relying solely on static bundle-content checks.
"""

import shutil
import subprocess  # nosec

import pytest

MAKE = shutil.which("make") or "/usr/bin/make"


@pytest.fixture
def presentation_makefile(git_repo):
    """Return the presentation.mk path or skip tests if missing."""
    makefile = git_repo / ".rhiza" / "make.d" / "presentation.mk"
    if not makefile.exists():
        pytest.skip("presentation.mk not found, skipping test")
    return makefile


def test_presentation_targets_defined(git_repo, presentation_makefile):
    """Presentation targets must be defined and parseable even without PRESENTATION.md.

    The targets are double-colon rules with no prerequisites, so a dry-run (-n)
    verifies make can resolve them without invoking Marp or needing the source.
    """
    # No PRESENTATION.md is created; the targets must still resolve.
    assert not (git_repo / "PRESENTATION.md").exists()

    for target in ["presentation", "presentation-pdf", "presentation-serve"]:
        result = subprocess.run([MAKE, "-n", target], cwd=git_repo, capture_output=True, text=True)  # nosec
        assert "no rule to make target" not in result.stderr.lower(), (
            f"Target {target} should be defined in .rhiza/make.d/presentation.mk"
        )
        assert result.returncode == 0, f"Dry-run of {target} failed: {result.stderr}"


def test_presentation_phony_targets(presentation_makefile):
    """presentation.mk must declare the expected phony targets."""
    content = presentation_makefile.read_text()

    phony_targets = [line.strip() for line in content.splitlines() if line.startswith(".PHONY:")]
    assert phony_targets, "expected at least one .PHONY declaration in presentation.mk"

    all_targets = set()
    for phony_line in phony_targets:
        all_targets.update(phony_line.split(":")[1].strip().split())

    expected_targets = {"presentation", "presentation-pdf", "presentation-serve"}
    assert expected_targets.issubset(all_targets), (
        f"Expected phony targets to include {expected_targets}, got {all_targets}"
    )


def test_presentation_double_colon_rules(presentation_makefile):
    """presentation.mk must define each target as a '::' rule for hook chaining."""
    content = presentation_makefile.read_text()
    for target in ["presentation", "presentation-pdf", "presentation-serve"]:
        assert f"{target}::" in content, f"presentation.mk should define '{target}' as a '::' (double-colon) rule"


def test_presentation_invokes_marp(presentation_makefile):
    """The recipes must drive Marp against PRESENTATION.md (the bundle's source file)."""
    content = presentation_makefile.read_text()
    assert "marp PRESENTATION.md" in content, "presentation target should render PRESENTATION.md via Marp"
    assert "presentation.html" in content, "presentation target should emit presentation.html"
    assert "presentation.pdf" in content, "presentation-pdf target should emit presentation.pdf"
