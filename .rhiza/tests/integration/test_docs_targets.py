"""Tests for docs.mk Makefile targets and the MKDOCS_EXTRA_PACKAGES variable."""

import shutil
import subprocess  # nosec

import pytest

MAKE = shutil.which("make") or "/usr/bin/make"


@pytest.fixture
def docs_makefile(git_repo):
    """Return the docs.mk path or skip tests if missing."""
    makefile = git_repo / ".rhiza" / "make.d" / "docs.mk"
    if not makefile.exists():
        pytest.skip("docs.mk not found, skipping test")
    return makefile


def test_mkdocs_extra_packages_variable_defined(docs_makefile):
    """Test that MKDOCS_EXTRA_PACKAGES is declared with a default-empty value."""
    content = docs_makefile.read_text()
    assert "MKDOCS_EXTRA_PACKAGES ?=" in content, "docs.mk should declare MKDOCS_EXTRA_PACKAGES with a ?= default"


def test_mkdocs_extra_packages_used_in_build(docs_makefile):
    """Test that MKDOCS_EXTRA_PACKAGES is spliced into the mkdocs-build uvx command."""
    content = docs_makefile.read_text()
    # The variable must appear on the same line as 'mkdocs build'
    build_lines = [line for line in content.splitlines() if "mkdocs build" in line]
    assert build_lines, "docs.mk should contain a 'mkdocs build' invocation"
    assert any("$(MKDOCS_EXTRA_PACKAGES)" in line for line in build_lines), (
        "mkdocs build line should include $(MKDOCS_EXTRA_PACKAGES)"
    )


def test_mkdocs_extra_packages_used_in_serve(docs_makefile):
    """Test that MKDOCS_EXTRA_PACKAGES is spliced into the mkdocs-serve uvx command."""
    content = docs_makefile.read_text()
    serve_lines = [line for line in content.splitlines() if "mkdocs serve" in line]
    assert serve_lines, "docs.mk should contain a 'mkdocs serve' invocation"
    assert any("$(MKDOCS_EXTRA_PACKAGES)" in line for line in serve_lines), (
        "mkdocs serve line should include $(MKDOCS_EXTRA_PACKAGES)"
    )


def test_mkdocs_build_dry_run_with_extra_package(git_repo, docs_makefile):
    """Test that passing MKDOCS_EXTRA_PACKAGES on the command line is accepted by make."""
    result = subprocess.run(  # nosec
        [MAKE, "-n", "mkdocs-build", "MKDOCS_EXTRA_PACKAGES=--with mkdocs-graphviz"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )
    assert "no rule to make target" not in result.stderr.lower(), "mkdocs-build should be a defined target"
    assert result.returncode == 0, f"Dry-run failed: {result.stderr}"
    # The extra package flag should appear in the dry-run output
    assert "mkdocs-graphviz" in result.stdout, "MKDOCS_EXTRA_PACKAGES value should be visible in the dry-run command"
