"""Pytest configuration for benchmark tests.

Provides fixtures needed for benchmarking tests.
"""

import pathlib

import pytest


@pytest.fixture(scope="session")
def root():
    """Return the repository root directory as a pathlib.Path."""
    return pathlib.Path(__file__).parent.parent.parent
