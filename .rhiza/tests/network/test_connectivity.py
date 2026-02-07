"""Network connectivity tests for essential services.

These tests verify that the environment can reach all services required
for a healthy rhiza-based repository workflow.
"""

from __future__ import annotations

import socket
import ssl
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest

if TYPE_CHECKING:
    from .conftest import ServiceEndpoint


def _check_dns_resolution(hostname: str) -> tuple[bool, str]:
    """Check if a hostname can be resolved via DNS.

    Args:
        hostname: The hostname to resolve.

    Returns:
        A tuple of (success, message).
    """
    try:
        socket.gethostbyname(hostname)
    except socket.gaierror as e:
        return False, f"DNS resolution failed for {hostname}: {e}"
    else:
        return True, f"DNS resolution successful for {hostname}"


def _check_tcp_connection(hostname: str, port: int, timeout: float) -> tuple[bool, str]:
    """Check if a TCP connection can be established.

    Args:
        hostname: The hostname to connect to.
        port: The port to connect to.
        timeout: Connection timeout in seconds.

    Returns:
        A tuple of (success, message).
    """
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True, f"TCP connection successful to {hostname}:{port}"
    except OSError as e:
        return False, f"TCP connection failed to {hostname}:{port}: {e}"


def _check_tls_handshake(hostname: str, port: int, timeout: float) -> tuple[bool, str]:
    """Check if a TLS handshake can be completed.

    Args:
        hostname: The hostname to connect to.
        port: The port to connect to.
        timeout: Connection timeout in seconds.

    Returns:
        A tuple of (success, message).
    """
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                return (
                    True,
                    f"TLS handshake successful to {hostname}:{port} (cert subject: {cert.get('subject', 'N/A')})",
                )
    except ssl.SSLError as e:
        return False, f"TLS handshake failed to {hostname}:{port}: {e}"
    except OSError as e:
        return False, f"Connection failed during TLS handshake to {hostname}:{port}: {e}"


@pytest.mark.network
class TestDNSResolution:
    """Test DNS resolution for all configured endpoints."""

    def test_dns_resolution(
        self,
        network_endpoints: tuple[ServiceEndpoint, ...],
    ) -> None:
        """Verify DNS resolution works for all service endpoints."""
        failures = []

        for endpoint in network_endpoints:
            parsed = urlparse(endpoint.url)
            hostname = parsed.hostname
            if hostname:
                success, message = _check_dns_resolution(hostname)
                if not success:
                    failures.append(f"{endpoint.name}: {message}")

        if failures:
            pytest.fail("DNS resolution failures:\n" + "\n".join(failures))


@pytest.mark.network
class TestTCPConnectivity:
    """Test TCP connectivity to all configured endpoints."""

    def test_tcp_connectivity(
        self,
        network_endpoints: tuple[ServiceEndpoint, ...],
        network_timeout: float,
    ) -> None:
        """Verify TCP connections can be established to all service endpoints."""
        failures = []

        for endpoint in network_endpoints:
            parsed = urlparse(endpoint.url)
            hostname = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)

            if hostname:
                success, message = _check_tcp_connection(hostname, port, network_timeout)
                if not success:
                    failures.append(f"{endpoint.name}: {message}")

        if failures:
            pytest.fail("TCP connectivity failures:\n" + "\n".join(failures))


@pytest.mark.network
class TestTLSHandshake:
    """Test TLS handshake for HTTPS endpoints."""

    def test_tls_handshake(
        self,
        network_endpoints: tuple[ServiceEndpoint, ...],
        network_timeout: float,
    ) -> None:
        """Verify TLS handshakes succeed for all HTTPS endpoints."""
        failures = []

        for endpoint in network_endpoints:
            parsed = urlparse(endpoint.url)
            if parsed.scheme != "https":
                continue

            hostname = parsed.hostname
            port = parsed.port or 443

            if hostname:
                success, message = _check_tls_handshake(hostname, port, network_timeout)
                if not success:
                    failures.append(f"{endpoint.name}: {message}")

        if failures:
            pytest.fail("TLS handshake failures:\n" + "\n".join(failures))


@pytest.mark.network
class TestHTTPConnectivity:
    """Test HTTP-level connectivity to all configured endpoints."""

    @pytest.fixture(scope="class")
    def http_client(self, network_timeout: float):
        """Create an HTTP client for testing."""
        # Use httpx if available, fall back to urllib
        try:
            import httpx

            with httpx.Client(timeout=network_timeout, follow_redirects=True) as client:
                yield client
        except ImportError:
            # Fallback to a simple wrapper around urllib
            yield None

    def test_http_connectivity(
        self,
        network_endpoints: tuple[ServiceEndpoint, ...],
        http_client,
        network_timeout: float,
    ) -> None:
        """Verify HTTP requests succeed to all service endpoints."""
        failures = []
        successes = []

        for endpoint in network_endpoints:
            try:
                if http_client is not None:
                    # Use httpx
                    response = http_client.get(endpoint.url)
                    status_code = response.status_code
                else:
                    # Fallback to urllib
                    import urllib.request

                    req = urllib.request.Request(endpoint.url, method="GET")
                    req.add_header("User-Agent", "rhiza-network-test/1.0")
                    try:
                        with urllib.request.urlopen(req, timeout=network_timeout) as resp:
                            status_code = resp.status
                    except urllib.error.HTTPError as e:
                        status_code = e.code

                if status_code in endpoint.expected_status_codes:
                    successes.append(f"{endpoint.name}: HTTP {status_code} (expected)")
                else:
                    failures.append(
                        f"{endpoint.name}: HTTP {status_code} (expected one of {endpoint.expected_status_codes})"
                    )

            except Exception as e:
                failures.append(f"{endpoint.name}: {type(e).__name__}: {e}")

        # Log successes for debugging
        if successes:
            print("\nSuccessful connections:")
            for s in successes:
                print(f"  ✓ {s}")

        if failures:
            pytest.fail("HTTP connectivity failures:\n" + "\n".join(failures))


@pytest.mark.network
@pytest.mark.slow
class TestServiceSpecific:
    """Service-specific connectivity tests with deeper validation."""

    def test_github_api_rate_limit(self, network_timeout: float) -> None:
        """Verify GitHub API is accessible and check rate limit status."""
        try:
            import httpx

            with httpx.Client(timeout=network_timeout) as client:
                response = client.get("https://api.github.com/rate_limit")
                assert response.status_code == 200, f"GitHub API returned {response.status_code}"

                data = response.json()
                core_limit = data.get("resources", {}).get("core", {})
                remaining = core_limit.get("remaining", 0)
                limit = core_limit.get("limit", 0)

                print(f"\nGitHub API rate limit: {remaining}/{limit} remaining")

                # Warn if rate limit is low (but don't fail)
                if remaining < 10:
                    pytest.skip(f"GitHub API rate limit is very low: {remaining}/{limit}")

        except ImportError:
            pytest.skip("httpx not installed - skipping detailed API test")

    def test_pypi_package_lookup(self, network_timeout: float) -> None:
        """Verify PyPI can look up a common package (pip)."""
        try:
            import httpx

            with httpx.Client(timeout=network_timeout) as client:
                response = client.get("https://pypi.org/pypi/pip/json")
                assert response.status_code == 200, f"PyPI returned {response.status_code}"

                data = response.json()
                version = data.get("info", {}).get("version", "unknown")
                print(f"\nPyPI connectivity verified (pip version: {version})")

        except ImportError:
            pytest.skip("httpx not installed - skipping detailed PyPI test")
