"""Tests for the Marimo notebook Makefile targets and their resilience.

Mirrors test_presentation_targets.py: the marimo bundle ships make targets
(marimo, marimo-validate) in .rhiza/make.d/marimo.mk, and this exercises them
end-to-end against a synced repo rather than relying solely on static
bundle-content checks.
"""

import shutil
import subprocess  # nosec

import pytest

MAKE = shutil.which("make") or "/usr/bin/make"


@pytest.fixture
def marimo_makefile(git_repo):
    """Return the marimo.mk path or skip tests if missing."""
    makefile = git_repo / ".rhiza" / "make.d" / "marimo.mk"
    if not makefile.exists():
        pytest.skip("marimo.mk not found, skipping test")
    return makefile


def test_marimo_targets_defined(git_repo, marimo_makefile):
    """Marimo targets must be defined and parseable even without a notebook folder.

    Both targets guard internally on MARIMO_FOLDER existing, so a dry-run (-n)
    verifies make can resolve them (and their 'install' prerequisite) without
    starting a server or running notebooks.
    """
    for target in ["marimo", "marimo-validate"]:
        result = subprocess.run([MAKE, "-n", target], cwd=git_repo, capture_output=True, text=True)  # nosec
        assert "no rule to make target" not in result.stderr.lower(), (
            f"Target {target} should be defined in .rhiza/make.d/marimo.mk"
        )
        assert result.returncode == 0, f"Dry-run of {target} failed: {result.stderr}"


def test_marimo_phony_targets(marimo_makefile):
    """marimo.mk must declare the expected phony targets."""
    content = marimo_makefile.read_text()

    phony_targets = [line.strip() for line in content.splitlines() if line.startswith(".PHONY:")]
    assert phony_targets, "expected at least one .PHONY declaration in marimo.mk"

    all_targets = set()
    for phony_line in phony_targets:
        all_targets.update(phony_line.split(":")[1].strip().split())

    expected_targets = {"marimo", "marimo-validate"}
    assert expected_targets.issubset(all_targets), (
        f"Expected phony targets to include {expected_targets}, got {all_targets}"
    )


def test_marimo_targets_depend_on_install(marimo_makefile):
    """Both targets must depend on 'install' so the venv is ready before use."""
    content = marimo_makefile.read_text()
    assert "marimo: install" in content, "marimo should declare 'install' as a prerequisite"
    assert "marimo-validate: install" in content, "marimo-validate should declare 'install' as a prerequisite"


def test_marimo_recipes_drive_marimo_cli(marimo_makefile):
    """The recipes must launch the Marimo editor and validate notebooks under MARIMO_FOLDER."""
    content = marimo_makefile.read_text()
    assert "MARIMO_FOLDER" in content, "marimo.mk should reference the configurable MARIMO_FOLDER"
    assert "marimo edit" in content, "marimo target should launch the editor via 'marimo edit'"
    assert "Validating" in content, "marimo-validate should report on notebook validation"
