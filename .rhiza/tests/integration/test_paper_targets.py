"""Tests for the LaTeX paper Makefile targets and their resilience.

Mirrors test_presentation_targets.py: the paper bundle ships make targets
(paper, paper-clean) in .rhiza/make.d/paper.mk, and this exercises them
end-to-end against a synced repo rather than relying solely on static
bundle-content checks.
"""

import shutil
import subprocess  # nosec

import pytest

MAKE = shutil.which("make") or "/usr/bin/make"


@pytest.fixture
def paper_makefile(git_repo):
    """Return the paper.mk path or skip tests if missing."""
    makefile = git_repo / ".rhiza" / "make.d" / "paper.mk"
    if not makefile.exists():
        pytest.skip("paper.mk not found, skipping test")
    return makefile


def test_paper_targets_defined(git_repo, paper_makefile):
    """Paper targets must be defined and parseable even without a docs/paper folder.

    The targets are double-colon rules with no prerequisites, so a dry-run (-n)
    verifies make can resolve them without invoking latexmk or needing sources.
    """
    assert not (git_repo / "docs" / "paper").exists()

    for target in ["paper", "paper-clean"]:
        result = subprocess.run([MAKE, "-n", target], cwd=git_repo, capture_output=True, text=True)  # nosec
        assert "no rule to make target" not in result.stderr.lower(), (
            f"Target {target} should be defined in .rhiza/make.d/paper.mk"
        )
        assert result.returncode == 0, f"Dry-run of {target} failed: {result.stderr}"


def test_paper_phony_targets(paper_makefile):
    """paper.mk must declare the expected phony targets."""
    content = paper_makefile.read_text()

    phony_targets = [line.strip() for line in content.splitlines() if line.startswith(".PHONY:")]
    assert phony_targets, "expected at least one .PHONY declaration in paper.mk"

    all_targets = set()
    for phony_line in phony_targets:
        all_targets.update(phony_line.split(":")[1].strip().split())

    expected_targets = {"paper", "paper-clean"}
    assert expected_targets.issubset(all_targets), (
        f"Expected phony targets to include {expected_targets}, got {all_targets}"
    )


def test_paper_double_colon_rules(paper_makefile):
    """paper.mk must define each target as a '::' rule for hook chaining."""
    content = paper_makefile.read_text()
    for target in ["paper", "paper-clean"]:
        assert f"{target}::" in content, f"paper.mk should define '{target}' as a '::' (double-colon) rule"


def test_paper_invokes_latexmk(paper_makefile):
    """The recipes must drive latexmk against the configured paper directory."""
    content = paper_makefile.read_text()
    assert "PAPER_DIR" in content, "paper.mk should expose a configurable PAPER_DIR"
    assert "latexmk -pdf" in content, "paper target should compile PDFs via latexmk"
    assert "latexmk -C" in content, "paper-clean target should remove artifacts via 'latexmk -C'"
