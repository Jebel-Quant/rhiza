"""Tests for Marimo notebooks in the book/marimo directory."""

import subprocess
from pathlib import Path

import pytest

MARIMO_FOLDER = Path("book/marimo")


def get_notebooks():
    """Discover all Marimo notebooks in the book/marimo directory."""
    if not MARIMO_FOLDER.exists():
        return []
    return list(MARIMO_FOLDER.glob("*.py"))


@pytest.mark.parametrize("notebook_path", get_notebooks(), ids=lambda p: p.name)
def test_notebook_execution(notebook_path):
    """Test if a Marimo notebook can be executed without errors.

    We use 'marimo export html' which executes the notebook cells and
    reports if any cells failed.
    """
    # Use uvx to run marimo to ensure it's available and has dependencies
    # We use --sandbox to ensure it runs in an isolated environment with its own dependencies
    # specified in the notebook's script metadata.
    cmd = [
        "./bin/uvx",
        "marimo",
        "export",
        "html",
        "--sandbox",
        str(notebook_path),
        "-o",
        "/dev/null",  # We don't need the actual HTML output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Marimo export html might return 0 even if cells fail, but it prints an error message.
    # However, with recent versions, it might return a non-zero exit code if cells fail.
    # We check both the return code and the stderr/stdout for failure messages.

    assert result.returncode == 0, f"Marimo export failed for {notebook_path.name}:\n{result.stderr}"

    # Check for failure messages in output
    failure_keywords = ["some cells failed to execute", "cells failed to execute", "MarimoExceptionRaisedError"]
    for keyword in failure_keywords:
        assert keyword not in result.stderr, f"Notebook {notebook_path.name} had cell failures:\n{result.stderr}"
        assert keyword not in result.stdout, f"Notebook {notebook_path.name} had cell failures:\n{result.stdout}"
