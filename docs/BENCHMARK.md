# Benchmarks

Performance benchmarking for Rhiza-based projects.

---

## Overview

Benchmarks measure the performance of critical code paths to:

- Detect performance regressions
- Compare implementation alternatives
- Validate optimization efforts
- Ensure scalability

---

## Running Benchmarks

### Quick Start

Run all benchmarks with:

```bash
make benchmark
```

This command:

1. Executes all benchmark tests
2. Generates performance metrics
3. Creates interactive HTML reports
4. Saves results to `_benchmarks/`

### Manual Execution

=== "All Benchmarks"
    ```bash
    uv run pytest tests/benchmarks/ --benchmark-only
    ```

=== "Specific Benchmark"
    ```bash
    uv run pytest tests/benchmarks/test_performance.py::test_specific_benchmark
    ```

=== "With Comparisons"
    ```bash
    # Save baseline
    uv run pytest tests/benchmarks/ --benchmark-only --benchmark-save=baseline
    
    # Compare against baseline
    uv run pytest tests/benchmarks/ --benchmark-only --benchmark-compare=baseline
    ```

---

## Viewing Results

Benchmark results are stored in `_benchmarks/`:

| File | Content |
|------|---------|
| `benchmarks.json` | Raw benchmark data (machine-readable) |
| `benchmarks.html` | Interactive HTML report (human-readable) |

### Open HTML Report

```bash
# macOS
open _benchmarks/benchmarks.html

# Linux
xdg-open _benchmarks/benchmarks.html

# Or use VS Code
code _benchmarks/benchmarks.html
```

---

## Writing Benchmarks

Benchmarks use [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) to measure performance.

### Basic Benchmark

```python
def test_function_performance(benchmark):
    """Benchmark example function."""
    result = benchmark(my_function, arg1, arg2)
    assert result is not None
```

### Setup and Teardown

For tests requiring setup/teardown that shouldn't be measured:

```python
def test_with_setup(benchmark):
    """Benchmark with separate setup phase."""
    # Setup (not measured)
    data = generate_test_data()
    
    # Benchmark only the function call
    result = benchmark(process_data, data)
    
    assert len(result) > 0
```

### Advanced: Manual Timing

For more control over what gets measured:

```python
def test_manual_timing(benchmark):
    """Benchmark with manual timing control."""
    data = prepare_data()  # Not measured
    
    @benchmark
    def timed_section():
        """Only this function is timed."""
        return process_data(data)
    
    result = timed_section()
    assert result is not None
```

### Parameterized Benchmarks

Test performance across different input sizes:

```python
import pytest

@pytest.mark.parametrize("size", [100, 1000, 10000])
def test_scaling(benchmark, size):
    """Benchmark function scaling with input size."""
    data = generate_data(size)
    result = benchmark(process_data, data)
    assert len(result) == size
```

---

## Benchmark Configuration

### pytest-benchmark Options

Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--benchmark-autosave",
    "--benchmark-save-data",
]
```

### Common Options

| Option | Purpose |
|--------|---------|
| `--benchmark-only` | Run only benchmarks (skip regular tests) |
| `--benchmark-skip` | Skip benchmarks (run only regular tests) |
| `--benchmark-save=NAME` | Save results with a specific name |
| `--benchmark-compare=NAME` | Compare with saved baseline |
| `--benchmark-autosave` | Automatically save results |
| `--benchmark-min-rounds=N` | Minimum number of rounds (default: 5) |
| `--benchmark-warmup=on` | Enable warmup rounds |

---

## Performance Targets

### Typical Benchmarks

| Operation | Target | Notes |
|-----------|--------|-------|
| Config parsing | < 1ms | Small YAML files |
| Template materialization | < 100ms | Single file |
| Dependency resolution | < 500ms | Typical project |
| Test suite execution | < 5s | Full test suite |

!!! tip "Context Matters"
    Performance targets depend on your specific use case.
    These are general guidelines, not strict requirements.

---

## Interpreting Results

### Sample Output

```
------------------------------------------- benchmark: 3 tests ------------------------------------------
Name (time in ms)              Min       Max      Mean    StdDev    Median     IQR    Outliers     Rounds
-----------------------------------------------------------------------------------------------------------
test_fast_function          0.1234    0.2345    0.1456    0.0123    0.1432  0.0089       2;0        100
test_medium_function        5.4321    6.7890    5.9876    0.2345    5.8765  0.1234       1;1         50
test_slow_function         45.6789   52.1234   48.3456    1.2345   47.9876  0.9876       0;2         20
-----------------------------------------------------------------------------------------------------------
```

### Key Metrics

| Metric | Meaning |
|--------|---------|
| **Min/Max** | Fastest and slowest execution times |
| **Mean** | Average execution time |
| **Median** | Middle value (less affected by outliers) |
| **StdDev** | Standard deviation (consistency measure) |
| **IQR** | Interquartile range (spread of middle 50%) |
| **Outliers** | Unusually fast/slow runs |
| **Rounds** | Number of iterations performed |

!!! success "What to Look For"
    - **Low StdDev** — Consistent performance
    - **Mean ≈ Median** — Few outliers
    - **High Rounds** — More reliable measurements

---

## Regression Detection

### Save Baselines

Before making changes, save a performance baseline:

```bash
uv run pytest tests/benchmarks/ --benchmark-only --benchmark-save=before-optimization
```

### Compare After Changes

After optimization, compare against the baseline:

```bash
uv run pytest tests/benchmarks/ --benchmark-only --benchmark-compare=before-optimization
```

### CI Integration

Benchmarks run automatically in CI pipelines to detect regressions:

- Baseline saved on `main` branch
- Pull requests compared against baseline
- Significant regressions block merging (configurable)

---

## Best Practices

### ✅ Do

- Benchmark realistic workloads
- Use representative data sizes
- Run benchmarks on consistent hardware
- Exclude setup/teardown from timing
- Save baselines before optimizations
- Document performance requirements

### ❌ Don't

- Benchmark trivial operations (< 1μs)
- Include I/O in CPU benchmarks
- Run benchmarks with background tasks
- Compare results across different machines
- Optimize without benchmarking first
- Ignore variance and outliers

---

## Profiling

For detailed performance analysis, use Python's profiling tools:

### cProfile

```bash
# Profile a specific test
python -m cProfile -o profile.stats -m pytest tests/test_example.py

# View results
python -m pstats profile.stats
```

### Line Profiler

```bash
# Install
uv pip install line-profiler

# Decorate function with @profile
@profile
def my_function():
    # ...

# Run with kernprof
kernprof -l -v script.py
```

### Memory Profiling

```bash
# Install
uv pip install memory-profiler

# Decorate function
@profile
def memory_intensive():
    # ...

# Run
python -m memory_profiler script.py
```

---

## Example Benchmark Suite

Here's a complete example benchmark file:

```python
"""Performance benchmarks for core functions."""

import pytest

def test_config_parse_performance(benchmark):
    """Benchmark YAML configuration parsing."""
    yaml_content = """
    key1: value1
    key2: value2
    nested:
        key3: value3
    """
    result = benchmark(parse_yaml, yaml_content)
    assert "key1" in result

@pytest.mark.parametrize("size", [10, 100, 1000])
def test_file_processing_scaling(benchmark, size):
    """Benchmark file processing at different scales."""
    files = [f"file{i}.py" for i in range(size)]
    result = benchmark(process_files, files)
    assert len(result) == size

def test_template_materialization(benchmark):
    """Benchmark template materialization."""
    config = load_test_config()
    result = benchmark(materialize_template, config)
    assert result.success
```

---

## Learn More

- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
- [Python Profilers](https://docs.python.org/3/library/profile.html)
- [Performance Testing Best Practices](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)

---

*Fast code is good code! ⚡*