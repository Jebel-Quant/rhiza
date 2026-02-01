"""Tests for book-related Makefile targets and their resilience."""

import shutil
import subprocess

import pytest

MAKE = shutil.which("make") or "/usr/bin/make"


def test_no_book_folder(git_repo):
    """Test that make targets work gracefully when book folder is missing.

    Now that book-related targets are defined in .rhiza/make.d/, they are always
    available but check internally for the existence of the book folder.
    Using dry-run (-n) to test the target logic without actually executing.
    """
    if (git_repo / "book").exists():
        shutil.rmtree(git_repo / "book")
    assert not (git_repo / "book").exists()

    # Targets are now always defined via .rhiza/make.d/
    # Use dry-run to verify they exist and can be parsed
    for target in ["book", "docs", "marimushka"]:
        result = subprocess.run([MAKE, "-n", target], cwd=git_repo, capture_output=True, text=True)
        # Target should exist (not "no rule to make target")
        assert "no rule to make target" not in result.stderr.lower(), (
            f"Target {target} should be defined in .rhiza/make.d/"
        )


def test_book_folder_but_no_mk(git_repo):
    """Test behavior when book folder exists but is empty.

    With the new architecture, targets are always defined in .rhiza/make.d/02-book.mk,
    so they should exist regardless of the book folder contents.
    """
    # ensure book folder exists but is empty
    if (git_repo / "book").exists():
        shutil.rmtree(git_repo / "book")
    # create an empty book folder
    (git_repo / "book").mkdir()

    # assert the book folder exists
    assert (git_repo / "book").exists()
    # assert the git_repo / "book" folder is empty
    assert not list((git_repo / "book").iterdir())

    # Targets are now always defined via .rhiza/make.d/
    # Use dry-run to verify they exist and can be parsed
    for target in ["book", "docs", "marimushka"]:
        result = subprocess.run([MAKE, "-n", target], cwd=git_repo, capture_output=True, text=True)
        # Target should exist (not "no rule to make target")
        assert "no rule to make target" not in result.stderr.lower(), (
            f"Target {target} should be defined in .rhiza/make.d/"
        )


def test_book_folder(git_repo):
    """Test that .rhiza/make.d/02-book.mk defines the expected phony targets."""
    # Check for the new location of book targets
    makefile = git_repo / ".rhiza" / "make.d" / "02-book.mk"
    if not makefile.exists():
        pytest.skip("02-book.mk not found, skipping test")

    content = makefile.read_text()

    # get the list of phony targets from the Makefile
    phony_targets = [line.strip() for line in content.splitlines() if line.startswith(".PHONY:")]
    if not phony_targets:
        pytest.skip("No .PHONY targets found in 02-book.mk")

    # Collect all targets from all .PHONY lines
    all_targets = set()
    for phony_line in phony_targets:
        targets = phony_line.split(":")[1].strip().split()
        all_targets.update(targets)

    expected_targets = {"book", "docs", "marimushka"}
    assert expected_targets.issubset(all_targets), (
        f"Expected phony targets to include {expected_targets}, got {all_targets}"
    )
