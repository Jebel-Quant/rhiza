# Testing Guide

Comprehensive guide to testing in Rhiza-based projects.

---

## Running Tests

### Quick Start

The simplest way to run all tests:

```bash
make test
```

This will:

- Run the full pytest suite
- Generate coverage reports
- Create HTML test and coverage reports
- Display summary results

### Running Specific Tests

=== "Single File"
    ```bash
    # Run tests in a specific file
    uv run pytest tests/path/to/test_example.py -v
    ```

=== "Single Test Function"
    ```bash
    # Run a specific test function
    uv run pytest tests/path/to/test_example.py::test_specific_function -v
    ```

=== "Pattern Matching"
    ```bash
    # Run tests matching a keyword
    uv run pytest -k "test_name_pattern" -v
    ```

### Useful pytest Options

| Flag | Purpose |
|------|---------|
| `-v` | Verbose output (show individual test names) |
| `-s` | Show print statements and stdout |
| `-x` | Stop on first failure |
| `--lf` | Run last failed tests only |
| `--ff` | Run failed tests first, then the rest |
| `--maxfail=N` | Stop after N failures |
| `--pdb` | Drop into debugger on failure |

**Example:**

```bash
# Stop on first failure with output
uv run pytest -xvs
```

---

## Test Structure

Rhiza projects follow pytest's standard test organization:

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── test_rhiza/          # Unit tests
│   ├── test_core.py
│   ├── test_config.py
│   └── test_utils.py
├── benchmarks/          # Performance tests
│   └── test_benchmark.py
└── integration/         # Integration tests (if applicable)
    └── test_workflow.py
```

### Test Discovery

pytest automatically discovers tests following these conventions:

- Files named `test_*.py` or `*_test.py`
- Functions named `test_*`
- Classes named `Test*` with methods named `test_*`

---

## Writing Tests

### Basic Test

```python
def test_example():
    """Test example function."""
    result = my_function(42)
    assert result == 84
```

### Using Fixtures

Fixtures provide reusable test data and setup:

```python
import pytest

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value", "number": 42}

def test_with_fixture(sample_data):
    """Test using fixture data."""
    assert sample_data["key"] == "value"
    assert sample_data["number"] == 42
```

### Parameterized Tests

Test multiple inputs efficiently:

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    """Test doubling function with multiple inputs."""
    assert double(input) == expected
```

### Exception Testing

Verify that code raises expected exceptions:

```python
import pytest

def test_raises_exception():
    """Test that invalid input raises ValueError."""
    with pytest.raises(ValueError, match="Invalid input"):
        process_data("invalid")
```

---

## Coverage

Coverage reports show which code is executed during tests.

### Viewing Coverage

After running `make test`, view the interactive HTML report:

```bash
# Open in browser
open _tests/html-coverage/index.html
```

Or check the terminal summary for a quick overview.

### Coverage Targets

Rhiza projects aim for:

- **Overall coverage:** ≥ 80%
- **Critical modules:** ≥ 90%
- **Utilities:** 100% (where feasible)

### Coverage Configuration

Coverage is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=src",
    "--cov-report=html:_tests/html-coverage",
    "--cov-report=term-missing",
]
```

!!! tip "Missing Coverage"
    The `term-missing` report shows exactly which lines aren't covered,
    making it easy to identify gaps.

---

## CI Matrix Testing

Tests run automatically across multiple Python versions in CI:

- **Python 3.11** - Minimum supported version
- **Python 3.12** - Current stable
- **Python 3.13** - Latest stable
- **Python 3.14** - Upcoming release

This ensures compatibility across all supported versions.

### CI Configuration

See [`.github/workflows/rhiza_ci.yml`](../.github/workflows/rhiza_ci.yml) for the full CI matrix configuration.

---

## Test Categories

### Unit Tests

Fast, isolated tests of individual functions/classes:

```python
def test_parse_config():
    """Test configuration parsing."""
    config = parse_config({"key": "value"})
    assert config.key == "value"
```

### Integration Tests

Tests that verify components work together:

```python
def test_full_workflow():
    """Test complete workflow integration."""
    result = initialize_project()
    assert result.status == "success"
    assert result.files_created > 0
```

### Performance Tests

See [Benchmarks](BENCHMARK.md) for performance testing details.

---

## Best Practices

### ✅ Do

- Write descriptive test names: `test_parse_yaml_with_comments()`
- Use fixtures for shared setup
- Test edge cases and error conditions
- Keep tests fast (< 1 second per test)
- Use parameterized tests for similar test cases
- Document complex test scenarios

### ❌ Don't

- Write tests that depend on each other
- Use hard-coded file paths (use `tmp_path` fixture)
- Test external services without mocking
- Ignore failing tests
- Skip test coverage for "trivial" code

---

## Debugging Failed Tests

### View Detailed Output

```bash
# Show full diff on assertion failures
uv run pytest -vv

# Show print statements
uv run pytest -s
```

### Use the Debugger

```bash
# Drop into pdb on failure
uv run pytest --pdb

# Or add breakpoint in code
def test_example():
    result = complex_function()
    breakpoint()  # Execution pauses here
    assert result == expected
```

### Run Only Failed Tests

```bash
# Re-run only failed tests from last run
uv run pytest --lf -v
```

---

## Continuous Integration

Tests run automatically on:

- **Pull Requests** — Every commit
- **Push to main** — After merges
- **Scheduled** — Nightly builds (optional)

Failed tests block merging, ensuring code quality.

---

## Learn More

- [pytest Documentation](https://docs.pytest.org/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest Parametrize](https://docs.pytest.org/en/stable/parametrize.html)
- [Coverage.py](https://coverage.readthedocs.io/)

---

*Happy testing! 🧪*