"""Pytest configuration for stress tests.

Provides fixtures and utilities specific to stress testing scenarios.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser):
    """Add custom command-line options for stress tests."""
    parser.addoption(
        "--iterations",
        action="store",
        default=100,
        type=int,
        help="Number of iterations for stress tests (default: 100)",
    )
    parser.addoption(
        "--workers",
        action="store",
        default=10,
        type=int,
        help="Number of concurrent workers for stress tests (default: 10)",
    )


@pytest.fixture
def stress_iterations(request):
    """Return the number of iterations for stress tests.

    Default is 100 iterations. Can be overridden via --iterations command line option.
    """
    return request.config.getoption("--iterations")


@pytest.fixture
def concurrent_workers(request):
    """Return the number of concurrent workers for stress tests.

    Default is 10 workers. Can be overridden via --workers command line option.
    """
    return request.config.getoption("--workers")
