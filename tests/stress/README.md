# Stress Tests

This directory contains stress and load tests for the Rhiza project. These tests exercise the system under high load to ensure it behaves correctly under stress conditions.

## Test Categories

### File Operations (`test_file_operations.py`)
Tests that stress file I/O operations:
- **test_many_file_reads**: Read many files repeatedly
- **test_many_file_writes**: Write many files
- **test_rapid_file_creation_deletion**: Rapidly create and delete files
- **test_large_file_operations**: Handle large file content (10MB+)
- **test_nested_directory_operations**: Create and manage nested directories

### Concurrent Operations (`test_concurrent_operations.py`)
Tests that exercise concurrent and parallel operations:
- **test_concurrent_computations**: Run computations concurrently
- **test_concurrent_list_operations**: Concurrent list processing
- **test_concurrent_dictionary_operations**: Concurrent dictionary operations
- **test_concurrent_string_operations**: Concurrent string operations
- **test_rapid_task_submission**: Submit many tasks rapidly

### Data Processing (`test_data_processing.py`)
Tests that exercise data processing and manipulation:
- **test_large_list_processing**: Process large lists (100k+ elements)
- **test_nested_list_operations**: Process nested list structures
- **test_dict_comprehensions**: Create and process large dictionaries
- **test_set_operations**: Set operations on large datasets
- **test_string_manipulation**: String manipulation operations
- **test_sorting_large_lists**: Sort large lists with different data types
- **test_filtering_operations**: Filter large datasets with complex conditions
- **test_aggregation_operations**: Aggregate large datasets

## Running Stress Tests

### Run all stress tests:
```bash
pytest -m stress
```

### Run stress tests with verbose output:
```bash
pytest -m stress -v
```

### Run stress tests from a specific file:
```bash
pytest tests/stress/test_file_operations.py -v
```

### Skip stress tests (run only regular tests):
```bash
pytest -m "not stress"
```

### Run regular tests by default:
```bash
make test  # This ignores benchmarks but may include stress tests depending on config
```

## Test Characteristics

- All tests are marked with the `@pytest.mark.stress` decorator
- Tests are designed to be deterministic and reproducible
- Tests use temporary directories and clean up after themselves
- Tests validate both correctness and performance under load
- Tests are independent and can be run in any order

## Guidelines for Adding New Stress Tests

When adding new stress tests:

1. Mark the test class or function with `@pytest.mark.stress`
2. Use temporary files/directories that clean up automatically
3. Test realistic scenarios that could occur in production
4. Include assertions to verify correctness, not just completion
5. Document what the test is stressing and why it matters
6. Keep tests fast enough to run regularly (< 5 seconds per test preferred)

## CI/CD Integration

Stress tests can be:
- Run on every commit to catch performance regressions early
- Run separately on a schedule (e.g., nightly) to save CI time
- Excluded from quick pre-commit checks using `-m "not stress"`

To configure this in CI, use pytest markers in your workflow:
```yaml
# Run only stress tests
pytest -m stress

# Run without stress tests
pytest -m "not stress"
```
