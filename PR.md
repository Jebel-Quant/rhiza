# Restructure Test Suite for Better Organization and Maintainability

## Summary

This PR restructures the entire rhiza test suite from a flat layout in `tests/test_rhiza/` into a purpose-driven, hierarchical organization under `.rhiza/tests/test_rhiza/`. The new structure improves discoverability, maintainability, and aligns with the project's modular architecture.

## Motivation

The previous flat structure made it difficult to:
- Quickly locate tests by their purpose (API validation vs. integration vs. structure checks)
- Identify which fixtures and helpers were available where
- Maintain test quality and prevent duplication
- Onboard new contributors to the testing strategy

## Changes

### Test Organization

Tests are now organized into 6 purpose-driven categories:

```
.rhiza/tests/test_rhiza/
├── api/          # 15 tests - Makefile dry-run validation
├── deps/         # 4 tests - Dependency health checks (NEW)
├── integration/  # 19 tests - Sandboxed execution
├── structure/    # 5 tests (1 skipped) - Static assertions
├── sync/         # 16 tests (1 skipped) - Template/content validation
└── utils/        # 67 tests - Test infrastructure
```

### New Tests

Added 4 new dependency health checks in `deps/`:
- Validates `requires-python` in `pyproject.toml`
- Checks all requirements files have valid pip specifiers
- Detects duplicate packages across requirements files
- Ensures critical test dependencies are present

### Quality Improvements

Removed 9 low-value tests:
- Trivially-true assertions (type checks, path absolute checks)
- Tests with no meaningful assertions
- Tests that validated external tools (`cat`) rather than rhiza functionality

Strengthened weak tests:
- Added proper assertions to previously incomplete tests
- Improved error messages and failure diagnostics

### Fixture Consolidation

- **Root-level** (`.rhiza/tests/test_rhiza/conftest.py`): `root`, `logger`, `git_repo`, `strip_ansi`
- **API** (`api/conftest.py`): `run_make`, `setup_tmp_makefile`, `SPLIT_MAKEFILES`
- **Sync** (`sync/conftest.py`): `setup_sync_env`
- **Utils** (`utils/conftest.py`): `sys.path` setup for version_matrix imports

Removed duplicate helpers and fixtures across test files.

### Documentation

- Created comprehensive `README.md` in `.rhiza/tests/test_rhiza/` with:
  - Test organization by category
  - Running instructions (all tests, by category, specific files)
  - Available fixtures and their scopes
  - Conventions and best practices
  - Coverage goals

### Configuration Updates

- Updated `pytest.ini` to only discover `.rhiza/tests` (benchmarks remain in `tests/test_rhiza/benchmarks/`)
- Updated `.rhiza/make.d/01-test.mk` to rely on `pytest.ini` testpaths
- Added `.rhiza/tests` to `.pre-commit-config.yaml` bandit exclusions
- Added `# nosec` annotations to test fixtures with shell commands (bandit compliance)

## Testing

All tests pass:
```bash
uv run pytest .rhiza/tests/test_rhiza/ -v
# 126 passed, 2 skipped (for optional src/ directory)
```

Test coverage maintained at previous levels while improving test quality.

## Migration Notes

The migration was completed in 9 sequential phases:
1. Bootstrap infrastructure (conftest.py, __init__.py files, pytest config)
2. Move structure tests
3. Move Makefile API tests
4. Move integration tests
5. Move sync tests
6. Move utility tests
7. Create dependency tests
8. Clean up old directory
9. Quality review

Each phase was verified independently before proceeding to ensure no test failures.

## Breaking Changes

None. The test suite location has changed, but:
- `make test` continues to work as before
- All existing fixtures and helpers are preserved
- Test discovery is automatic via `pytest.ini`
- Benchmarks remain in their original location (`tests/test_rhiza/benchmarks/`)

## Statistics

- **Before:** 131 tests (1 skipped), flat structure in `tests/test_rhiza/`
- **After:** 126 tests (2 skipped), organized structure in `.rhiza/tests/test_rhiza/`
- **Net change:** -5 tests (removed low-value tests, added 4 new dependency tests)
- **Files changed:** 38 files (+1,181 insertions, -638 deletions)

## Future Work

Optional improvements for future consideration:
- Add coverage for `make install` and `make clean` dry-runs
- Add tests for `.rhiza/.env` variable loading
- Profile and optimize slow tests
- Add tests for new Makefile targets as they're added
