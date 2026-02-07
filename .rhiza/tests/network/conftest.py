"""Pytest configuration for network connectivity tests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for network tests."""
    config.addinivalue_line("markers", "network: marks tests as network tests (may be skipped offline)")
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options for network tests."""
    parser.addoption(
        "--network-timeout",
        action="store",
        default=5.0,
        type=float,
        help="Timeout in seconds for network connectivity tests (default: 5.0)",
    )
    parser.addoption(
        "--skip-network",
        action="store_true",
        default=False,
        help="Skip all network connectivity tests",
    )


@dataclass(frozen=True)
class ServiceEndpoint:
    """Represents a service endpoint to test connectivity against."""

    name: str
    url: str
    expected_status_codes: tuple[int, ...] = (200, 301, 302, 403, 404)
    description: str = ""

    def __str__(self) -> str:
        """String representation for logging purposes."""
        return f"{self.name} ({self.url})"


# Default endpoints that rhiza-based projects typically need
DEFAULT_ENDPOINTS: tuple[ServiceEndpoint, ...] = (
    ServiceEndpoint(
        name="GitHub API",
        url="https://api.github.com",
        expected_status_codes=(200,),
        description="GitHub REST API - required for repository operations",
    ),
    ServiceEndpoint(
        name="PyPI",
        url="https://pypi.org/simple/",
        expected_status_codes=(200,),
        description="Python Package Index - required for package downloads",
    ),
    ServiceEndpoint(
        name="GitHub Container Registry",
        url="https://ghcr.io/v2/",
        expected_status_codes=(200, 401),  # 401 is expected without auth
        description="GitHub Container Registry - required for container images",
    ),
    ServiceEndpoint(
        name="GitHub Raw Content",
        url="https://raw.githubusercontent.com",
        expected_status_codes=(200, 400),  # 400 without a path is expected
        description="GitHub raw content delivery - required for raw file access",
    ),
)


def _parse_custom_endpoints() -> tuple[ServiceEndpoint, ...]:
    """Parse custom endpoints from environment variable."""
    env_endpoints = os.environ.get("RHIZA_NETWORK_ENDPOINTS", "")
    if not env_endpoints:
        return ()

    custom = []
    for url in env_endpoints.split(","):
        url = url.strip()
        if url:
            # Extract a name from the URL
            name = url.replace("https://", "").replace("http://", "").split("/")[0]
            custom.append(ServiceEndpoint(name=f"Custom: {name}", url=url))
    return tuple(custom)


@pytest.fixture(scope="session")
def network_timeout(request: pytest.FixtureRequest) -> float:
    """Get the network timeout from command-line options."""
    return request.config.getoption("--network-timeout")


@pytest.fixture(scope="session")
def network_endpoints() -> tuple[ServiceEndpoint, ...]:
    """Get all service endpoints to test.

    Override this fixture in your conftest.py to customize endpoints.
    """
    custom = _parse_custom_endpoints()
    if custom:
        return custom  # If custom endpoints are specified, use only those
    return DEFAULT_ENDPOINTS


@pytest.fixture(autouse=True)
def skip_network_if_requested(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Skip network tests if --skip-network is passed."""
    if request.config.getoption("--skip-network"):
        if request.node.get_closest_marker("network"):
            pytest.skip("Skipping network test (--skip-network specified)")
    return
