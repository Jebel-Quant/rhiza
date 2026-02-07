# Network Connectivity Tests

This module contains tests that verify network connectivity to essential services
required for a healthy rhiza-based repository.

## Purpose

These tests are designed to be run as part of CI/CD workflows to quickly diagnose
connectivity issues. They help answer the question: "Can this environment reach
all the services it needs?"

## Services Tested

By default, the following services are tested:

| Service | URL | Purpose |
|---------|-----|---------|
| GitHub API | `https://api.github.com` | Repository operations, releases |
| PyPI | `https://pypi.org` | Package downloads |
| GitHub Container Registry | `https://ghcr.io` | Container images |
| GitHub Raw Content | `https://raw.githubusercontent.com` | Raw file access |

## Configuration

Services can be configured via:

1. **Environment variable**: Set `RHIZA_NETWORK_ENDPOINTS` as a comma-separated list of URLs
2. **pytest markers**: Skip specific service checks with `@pytest.mark.skip`
3. **conftest.py**: Override the `network_endpoints` fixture

### Custom Endpoints

Add custom endpoints via environment variable:

```bash
export RHIZA_NETWORK_ENDPOINTS="https://api.github.com,https://pypi.org,https://custom.internal.service"
```

## Running Tests

```bash
# Run all network tests
pytest .rhiza/tests/network/ -v

# Run with timeout adjustment
pytest .rhiza/tests/network/ -v --network-timeout=10

# Skip network tests (useful for offline development)
pytest -m "not network"
```

## Usage in Workflows

```yaml
- name: Network connectivity check
  run: |
    make test PYTEST_ARGS=".rhiza/tests/network/ -v"
```

## Markers

- `@pytest.mark.network` - Applied to all network tests (can be used to skip/select)
- `@pytest.mark.slow` - Applied to tests that may take longer due to network latency
