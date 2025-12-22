# Performance Benchmarks

This directory contains performance benchmarks.

## Overview

The benchmarks test the performance of key operations:

- **Database Operations** (`test_db_operations.py`)
  - Insert operations (single and bulk)
  - Select queries (all and filtered)
  - Complex cross-table queries
  - Date range queries

- **I/O Operations** (`test_io_operations.py`)
  - CSV export and import
  - Parquet export and import
  - DataFrame conversions

- **Utility Functions** (`test_utils.py`)
  - Month code conversions
  - Futures code parsing

## Running Benchmarks

### Install Dependencies

First, ensure the development dependencies are installed:

```bash
make install
```

### Run All Benchmarks

```bash
uv run pytest tests/benchmarks/ --benchmark-only --benchmark-json=tests/benchmarks/benchmarks.json
uv run tests/benchmarks/analyze_benchmarks.py

```

### Run Specific Benchmark Categories

Database operations only:
```bash
uv run pytest tests/benchmarks/test_db_operations.py --benchmark-only
```

I/O operations only:
```bash
uv run pytest tests/benchmarks/test_io_operations.py --benchmark-only
```

Utility functions only:
```bash
uv run pytest tests/benchmarks/test_utils.py --benchmark-only
```

### Generate Benchmark Report

Save benchmark results to a file:
```bash
uv run pytest tests/benchmarks/ --benchmark-only --benchmark-save=baseline
```

### HTML Report

Generate an HTML report with graphs:
```bash
uv run pytest tests/benchmarks/ --benchmark-only --benchmark-histogram
```

## Benchmark Configuration

The benchmarks use `pytest-benchmark` with the following features:

- **Automatic calibration**: Each benchmark runs multiple iterations to get accurate timing
- **Statistical analysis**: Reports min, max, mean, median, and standard deviation
- **Warmup rounds**: Ensures JIT compilation and caching don't affect results
- **Memory cleanup**: Tests clean up after themselves to avoid interference

## Understanding Results

Benchmark output includes:

- **Name**: Test function name
- **Min**: Fastest execution time
- **Max**: Slowest execution time
- **Mean**: Average execution time
- **StdDev**: Standard deviation (lower = more consistent)
- **Median**: Middle value (useful when outliers exist)
- **IQR**: Interquartile range (measure of variance)
- **Outliers**: Number of outlier measurements
- **Rounds**: Number of times the benchmark was run

## Performance Targets

These are rough guidelines, not strict requirements:

| Operation | Target (approx) |
|-----------|----------------|
| Single insert | < 1ms |
| Bulk insert (100) | < 50ms |
| Select all (100) | < 10ms |
| Filtered select | < 15ms |
| CSV export (100) | < 50ms |
| Parquet export (100) | < 30ms |
| CSV import (100) | < 50ms |
| Parquet import (100) | < 30ms |
| Month code conversion | < 0.01ms |

Actual performance depends on hardware and database state.

## Adding New Benchmarks

To add a new benchmark:

1. Create a test function with the `benchmark` fixture
2. Use `benchmark()` to wrap the operation being tested
3. Include setup code outside the benchmark call
4. Add cleanup code if needed (within the benchmarked function)
5. Add assertions to verify correctness

Example:

```python
def test_my_operation(self, benchmark, db):
    """Benchmark my operation."""
    # Setup (not benchmarked)
    data = setup_test_data()

    # Define operation to benchmark
    def operation():
        result = db.my_operation(data)
        # Cleanup if needed
        db.cleanup()
        return result

    # Run benchmark
    result = benchmark(operation)

    # Verify correctness
    assert result is not None
```

## CI Integration

Benchmarks can be integrated into CI/CD:

- Run benchmarks on every PR to detect performance regressions
- Compare against baseline to flag significant changes
- Set performance budgets as test gates

## Tips for Accurate Benchmarks

1. **Close background applications** that might interfere
2. **Run multiple times** and look for consistency
3. **Use realistic data sizes** that match production usage
4. **Warm up databases** before critical benchmarks
5. **Monitor system resources** during benchmark runs
6. **Compare relative performance**, not absolute times
