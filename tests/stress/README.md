# Stress Tests

This directory contains stress tests for the Rhiza project, exercising the system under load to verify correctness and performance.

## Tests (`test_stress.py`)

- **test_concurrent_computations**: Run 100 Fibonacci calculations concurrently via a thread pool
- **test_rapid_task_submission**: Submit 200 tasks rapidly and assert completion under 5 seconds
- **test_large_list_processing**: Chained transforms on a 100k-element list
- **test_set_operations**: Union, intersection, and difference on 50k-element sets
- **test_large_file_operations**: Write a ~10 MB file and read it 10 times

## Running Stress Tests

```bash
# Run all stress tests
make stress

# Run with verbose output
pytest -m stress -v

# Run without stress tests
make test
```

## Guidelines for Adding New Stress Tests

1. Mark the test class or function with `@pytest.mark.stress`
2. Use temporary files/directories that clean up automatically
3. Include assertions to verify correctness, not just completion
4. Keep tests fast enough to run regularly (< 5 seconds per test preferred)
