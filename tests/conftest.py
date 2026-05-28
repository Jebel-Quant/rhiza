"""Pytest configuration for rhiza tests.

Security Notes:
- S101 (assert usage): Asserts are appropriate in test code for validating conditions
- S603 (subprocess without shell=True): All subprocess calls use lists of known commands,
  not user input, making them safe from shell injection
- S607 (subprocess with partial path): Using commands from PATH is acceptable in test fixtures
  as the test environment is controlled
"""

import logging
import pathlib

import pytest


@pytest.fixture(scope="session")
def logger() -> logging.Logger:
    """Provide a session-scoped logger for tests."""
    return logging.getLogger(__name__)


@pytest.fixture(scope="session")
def root() -> pathlib.Path:
    """Return the repository root directory."""
    return pathlib.Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(root: pathlib.Path) -> pathlib.Path:
    """Return the directory containing test data."""
    return root / "tests" / "resources"
