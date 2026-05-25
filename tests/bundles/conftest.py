"""Pytest configuration for bundle integration tests."""

import pathlib

import pytest


@pytest.fixture(scope="session")
def root() -> pathlib.Path:
    """Return the repository root directory."""
    return pathlib.Path(__file__).parent.parent.parent
