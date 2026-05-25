"""Pytest configuration for bundle integration tests.

Security Notes:
- S101 (assert usage): Asserts are appropriate in test code for validating conditions
- S603 (subprocess without shell=True): All subprocess calls use lists of known commands,
  not user input, making them safe from shell injection
- S607 (subprocess with partial path): Using commands from PATH is acceptable in test fixtures
  as the test environment is controlled
"""

import pathlib

import pytest


@pytest.fixture(scope="session")
def root() -> pathlib.Path:
    """Return the repository root directory."""
    return pathlib.Path(__file__).parent.parent.parent
