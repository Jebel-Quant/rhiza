"""Pytest configuration for stress tests.

Provides fixtures and utilities specific to stress testing scenarios.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def stress_iterations():
    """Return the number of iterations for stress tests.

    Default is 100 iterations. Can be overridden via pytest.ini or command line.
    """
    return 100


@pytest.fixture
def concurrent_workers():
    """Return the number of concurrent workers for stress tests.

    Default is 10 workers. Can be overridden for more aggressive testing.
    """
    return 10
