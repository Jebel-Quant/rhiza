# User Tests

This directory is reserved for your project's tests. Add your test files here following pytest conventions:

- Test files should be named `test_*.py` or `*_test.py`
- Test functions should be named `test_*`
- Organize tests in subdirectories as needed

## Running Your Tests

```bash
# Run all your tests
make test

# Run specific tests
pytest tests/test_mymodule.py -v

# Run with coverage
pytest tests/ --cov=src
```

## Rhiza Framework Tests

Rhiza's own framework tests are located in `.rhiza/tests/` to keep them separate from your project tests. You can run them with:

```bash
make rhiza-test
```

For more information, see `docs/TESTS.md`.
