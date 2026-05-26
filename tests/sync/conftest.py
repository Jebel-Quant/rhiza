"""Pytest configuration for downstream-sync integration tests.

Security Notes:
- S101 (assert usage): Asserts are appropriate in test code for validating conditions
"""

import pathlib

import pytest


@pytest.fixture(scope="session")
def root() -> pathlib.Path:
    """Return the repository root directory."""
    return pathlib.Path(__file__).parent.parent.parent
