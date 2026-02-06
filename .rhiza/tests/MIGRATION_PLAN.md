# Rhiza Test Migration Plan

## Overview

Migrate and restructure the rhiza test suite from the flat layout in `tests/test_rhiza/` into a purpose-driven folder structure under `.rhiza/tests/test_rhiza/`. The empty target subdirectories (`api/`, `deps/`, `integration/`, `structure/`, `sync/`, `utils/`) already exist under `.rhiza/tests/test_rhiza/`.

Work is divided into sequential phases — complete and verify each before starting the next.

**Source (current, working):** `tests/test_rhiza/` — 14 test files, 131 passing, 1 skipped
**Target:** `.rhiza/tests/test_rhiza/` — empty subdirectory scaffolding already in place

---

## Current State

All tests pass from their current location:
```
uv run pytest tests/test_rhiza/ -q
# 131 passed, 1 skipped (test_docstrings — no src/ dir), 1 warning
```

### Source Files
| File | What it tests | Target folder |
|------|--------------|---------------|
| `conftest.py` | Fixtures: `root`, `logger`, `git_repo`; helpers: `strip_ansi`, `run_make`, `setup_rhiza_git_repo`; mock scripts | root conftest |
| `__init__.py` | Package marker | root |
| `README.md` | Test suite documentation | root |
| `test_structure.py` | Repo root has expected dirs/files | `structure/` |
| `test_requirements_folder.py` | `.rhiza/requirements/` exists with expected files | `structure/` |
| `test_makefile.py` | Core Makefile targets (dry-run, variables, flags) | `api/` |
| `test_makefile_api.py` | Makefile API (delegation, extension, hooks, overrides) | `api/` |
| `test_makefile_gh.py` | GitHub Makefile targets (dry-run) | `api/` |
| `test_book.py` | Book-related Makefile targets in sandboxed git | `integration/` |
| `test_release_script.py` | `release.sh` in sandboxed git repo | `integration/` |
| `test_marimushka_target.py` | Marimushka target in sandboxed env | `integration/` |
| `test_notebooks.py` | Marimo notebooks execute without errors | `integration/` |
| `test_docstrings.py` | Doctests across all source modules | `sync/` |
| `test_readme.py` | README code blocks execute and match results | `sync/` |
| `test_rhiza_workflows.py` | `.rhiza-version`, sync, validate, summarise-sync | `sync/` |
| `test_git_repo_fixture.py` | Validates the `git_repo` fixture itself | `utils/` |
| `test_version_matrix.py` | `version_matrix.py` utility (pure unit tests) | `utils/` |

### Target Folder Purposes
| Folder | Purpose |
|--------|---------|
| `structure/` | Static assertions about file/directory presence — no subprocess calls |
| `api/` | Makefile target validation via `make -n` dry-runs |
| `integration/` | Tests that need a sandboxed git repo or subprocess execution |
| `sync/` | Tests for template sync, workflows, versioning, and content validation |
| `utils/` | Tests for utility code and test infrastructure (fixtures) |
| `deps/` | Dependency validation (requirements file content, pyproject validity) |

### Known Issues in Existing Tests
These do NOT block the migration but should be addressed in the final quality phase:

- `test_structure.py`: Uses `warnings.warn()` instead of `assert` — tests never fail
- `test_structure.py`: `test_root_resolves_correctly_from_nested_location` checks for old path `tests/test_rhiza/conftest.py` — update after move
- `test_makefile.py`: `test_test_target_dry_run` has an empty assertion comment
- `test_makefile.py`: Duplicates `strip_ansi`, `run_make`, `setup_rhiza_git_repo` from conftest
- `test_makefile_api.py`: Duplicates `run_make`
- `test_makefile_gh.py`: Duplicates `run_make`
- `test_rhiza_workflows.py`: Imports from `.conftest` — needs update after move
- `test_version_matrix.py`: Uses `sys.path.insert()` hack at module level
- `test_makefile_api.py`: `test_hooks_flow` has no meaningful assertions

---

## Phase 1: Bootstrap the Target — `conftest.py`, `__init__.py`, pytest config ✅ COMPLETED

**Goal:** Set up `.rhiza/tests/test_rhiza/` as a working pytest root with the shared fixtures, `__init__.py` files in each subdirectory, and pytest configured to discover both locations.

**Completion Summary:**
- Created `.rhiza/tests/test_rhiza/conftest.py` with updated `root` fixture (4 levels up)
- Created `.rhiza/tests/test_rhiza/__init__.py`
- Created `__init__.py` in all 6 subdirectories with appropriate docstrings
- Updated `pytest.ini` with `testpaths = .rhiza/tests tests`
- Added `# nosec` annotations to conftest.py to suppress bandit warnings on test fixtures
- Verified: `.rhiza/tests/` collects 0 tests (expected), `tests/test_rhiza/` still passes 131 tests

**Committed:** `06dc0fddb2c23a8c0ff504bfdedc646f6a4d326a`

---

## Phase 2: Move Structure Tests → `structure/` ✅ COMPLETED

**Goal:** Move static file/directory assertion tests into `.rhiza/tests/test_rhiza/structure/`.

**Completion Summary:**
- Moved `test_structure.py` → `structure/test_project_layout.py`
- Moved `test_requirements_folder.py` → `structure/test_requirements.py`
- Updated `test_root_resolves_correctly_from_nested_location` to check `.rhiza/tests/test_rhiza/conftest.py`
- Converted `warnings.warn()` to proper assertions with `pytest.skip()` for optional items
- Added `ClassVar` annotation for `EXPECTED_REQUIREMENTS_FILES`
- Verified: 9 passed, 1 skipped (src/ directory is optional)

**Committed:** `fee1d1e`

---

## ⚠️ NEXT AGENT: Start with Phase 3

**Agent instructions:**

1. **Copy `tests/test_rhiza/conftest.py` → `.rhiza/tests/test_rhiza/conftest.py`**
   - Keep all fixtures and helpers as-is
   - Update the `root` fixture path calculation. Currently:
     ```python
     return pathlib.Path(__file__).parent.parent.parent
     ```
     The new location is `.rhiza/tests/test_rhiza/conftest.py`, so the repo root is now **four** levels up:
     ```python
     return pathlib.Path(__file__).parent.parent.parent.parent
     ```
   - Keep `strip_ansi`, `run_make`, `setup_rhiza_git_repo`, mock scripts, `root`, `logger`, `git_repo` exactly as-is (except the path fix above).

2. **Copy `tests/test_rhiza/__init__.py` → `.rhiza/tests/test_rhiza/__init__.py`**

3. **Create `__init__.py` in each subdirectory** (all under `.rhiza/tests/test_rhiza/`):

   | File | Docstring |
   |------|-----------|
   | `structure/__init__.py` | `"""Structure tests — static assertions about file and directory presence."""` |
   | `api/__init__.py` | `"""API tests — Makefile target validation via dry-runs."""` |
   | `integration/__init__.py` | `"""Integration tests — sandboxed git repos and subprocess execution."""` |
   | `sync/__init__.py` | `"""Sync tests — template sync, workflows, versioning, and content validation."""` |
   | `utils/__init__.py` | `"""Utility tests — test infrastructure and helper utilities."""` |
   | `deps/__init__.py` | `"""Dependency tests — requirements file content and pyproject validation."""` |

4. **Update `pytest.ini`** — add `testpaths` so pytest discovers both locations:
   ```ini
   testpaths = .rhiza/tests tests
   ```

5. **Verify:**
   - `uv run pytest .rhiza/tests/ --co -q` — should collect 0 tests (no test files yet, just infra)
   - `uv run pytest tests/test_rhiza/ -q` — existing 131 tests still pass
   - `uv run pytest -q` — both locations discovered, 131 pass

**Acceptance criteria:**
- `.rhiza/tests/test_rhiza/conftest.py` exists with corrected `root` path
- All 6 subdirectories have `__init__.py`
- `pytest.ini` has `testpaths`
- Existing tests in `tests/test_rhiza/` unaffected

---

## Phase 3: Move Makefile API Tests → `api/` ✅ COMPLETED

**Goal:** Move Makefile dry-run and API tests, deduplicating helpers.

**Completion Summary:**
- Created `.rhiza/tests/test_rhiza/api/conftest.py` with shared fixtures:
  - `setup_tmp_makefile` (autouse): Consolidates Makefile and split file setup
  - `run_make`: Shared helper for executing make commands with dry-run support
  - `setup_rhiza_git_repo`: Initialize git repo configured as rhiza origin
  - `SPLIT_MAKEFILES`: Centralized list of split Makefile paths
- Moved `test_makefile.py` → `api/test_makefile_targets.py` (removed duplicates)
- Moved `test_makefile_api.py` → `api/test_makefile_api.py` (added logger params to all tests)
- Moved `test_makefile_gh.py` → `api/test_github_targets.py` (removed duplicates)
- Deduplication:
  - Removed duplicate `run_make`, `strip_ansi`, `setup_rhiza_git_repo` helpers
  - Removed duplicate `setup_gh_makefile` fixture (consolidated into `setup_tmp_makefile`)
  - All test files now import shared helpers from conftest modules
- All 33 API tests passing in new location
- Code formatted and linted (make fmt passes)

**Committed:** `8502870`

---

## Phase 4: Move Integration Tests → `integration/` ✅ COMPLETED

**Goal:** Move tests requiring sandboxed git repos or subprocess execution.

**Completion Summary:**
- Moved `test_release_script.py` → `integration/test_release.py`
- Moved `test_book.py` → `integration/test_book_targets.py`
- Moved `test_marimushka_target.py` → `integration/test_marimushka.py`
- Moved `test_notebooks.py` → `integration/test_notebook_execution.py`
- Added `test_notebooks_discovered()` guard test to surface when no notebooks found
- Added `# nosec` annotations to all subprocess calls for bandit compliance
- All files moved with `git mv` to preserve history
- All 19 integration tests passing in new location
- Total of 61 tests passing (1 skipped for optional src/ directory)

**Committed:** `9a3124f`

---

## Phase 5: Move Sync Tests → `sync/` ✅ COMPLETED

**Goal:** Move template sync, versioning, and content validation tests.

**Completion Summary:**
- Created `sync/conftest.py` with `setup_sync_env` fixture for template sync tests
- Moved `test_rhiza_workflows.py` → `sync/test_rhiza_version.py` with updated imports
- Moved `test_readme.py` → `sync/test_readme_validation.py`
- Moved `test_docstrings.py` → `sync/test_docstrings.py`
- Added `# nosec` annotations to subprocess calls for bandit compliance
- Updated `.pre-commit-config.yaml` to exclude `.rhiza/tests` from bandit scanning
- All 20 sync tests passing (1 skipped for optional src/ directory)
- Total of 81 tests passing in `.rhiza/tests/test_rhiza/` (2 skipped)

**Committed:** `e3ff597`

---

## Phase 6: Move Utility Tests → `utils/` ✅ COMPLETED

**Goal:** Move tests for utilities and test infrastructure.

**Completion Summary:**
- Created `utils/conftest.py` with sys.path setup for version_matrix imports
- Moved `test_git_repo_fixture.py` → `utils/test_git_repo_fixture.py` (no changes)
- Moved `test_version_matrix.py` → `utils/test_version_matrix.py`
  - Removed `sys.path.insert()` hack from test file (now in conftest.py)
- Removed old `conftest.py`, `__init__.py`, `README.md` from `tests/test_rhiza/`
- Updated `.rhiza/make.d/01-test.mk` to rely on `pytest.ini` `testpaths` instead of explicit folder
- Fixed test assertion in `test_makefile_targets.py` to check for `.venv/bin/python -m pytest` instead of `pytest tests`
- All 131 tests passing (2 skipped for optional src/ directory)

**Committed:** `9451ab0`

---

## Phase 7: Create Dependency Tests → `deps/` ✅ COMPLETED

**Goal:** Add meaningful dependency validation tests (new tests, not moved).

**Completion Summary:**
- Created `deps/test_dependency_health.py` with 4 new tests:
  - `test_pyproject_has_requires_python` — validates `requires-python` in `[project]` section
  - `test_requirements_files_are_valid_pip_specifiers` — checks all requirement lines are parseable
  - `test_no_duplicate_packages_across_requirements` — detects duplicate packages (allows intentional duplicates like `python-dotenv`)
  - `test_dotenv_in_test_requirements` — ensures `python-dotenv` is in `tests.txt`
- Fixed f-string nesting for Python 3.11 compatibility
- All 135 tests passing (2 skipped for optional src/ directory)

**Committed:** `05f7b87`

---

## Phase 8: Clean Up Old Directory and Finalize ✅ COMPLETED

**Goal:** Remove the old `tests/test_rhiza/` directory (except benchmarks), update docs, verify everything.

**Completion Summary:**
- Removed `__pycache__/` from `tests/test_rhiza/` (only `benchmarks/` remains)
- Updated `pytest.ini` to only discover tests in `.rhiza/tests` (benchmarks excluded from test discovery)
- Created comprehensive `README.md` in `.rhiza/tests/test_rhiza/` documenting:
  - Test organization by category
  - Running tests (all, by category, specific files)
  - Available fixtures (root-level and category-specific)
  - Conventions and best practices
  - Coverage goals
- Full verification passed:
  - `uv run pytest .rhiza/tests/test_rhiza/ -v --tb=short` — 135 passed, 2 skipped
  - `make fmt` — clean
  - `make test` — 135 passed, 2 skipped
- Benchmarks remain in `tests/test_rhiza/benchmarks/` (run via `make benchmark`)

**Committed:** `5bcd536`

---

## ⚠️ NEXT AGENT: Start with Phase 9

**Goal:** Quality review — remove low-value tests, strengthen weak ones.

## Phase 9: Quality Review — Remove Low-Value Tests, Strengthen Weak Ones

**Goal:** Review all migrated tests for quality. Remove tests that exist "for the sake of testing". Strengthen weak assertions.

**Agent instructions:**

1. **Remove low-value tests:**
   - `test_root_returns_pathlib_path` — trivially true, remove
   - `test_root_is_absolute_path` — trivially true, remove
   - `test_root_can_locate_github_scripts` — duplicates structure tests, remove
   - `test_makefile_is_readable` — if it exists, it's readable, remove
   - `test_bash_blocks_are_non_empty` — bash blocks could be intentionally empty, remove

2. **Strengthen weak tests:**
   - `test_test_target_dry_run`: fill in the empty assertion (`# Check for uv command with the configured path`) or remove
   - `test_hooks_flow`: has no meaningful assertions — add assertions or remove
   - `test_makefile_has_uv_variables`: too vague — either assert specific variable names or remove
   - `test_workflow_version_reading_pattern` and `test_workflow_version_fallback_pattern`: these test `cat`, not rhiza — remove or replace with tests that validate the actual workflow YAML references the right version

3. **Add missing coverage (if time permits):**
   - Test that `make install` dry-run emits expected commands
   - Test that `make clean` dry-run emits expected cleanup commands
   - Test that `.rhiza/.env` variables are correctly loaded by Makefile (e.g. `print-SOURCE_FOLDER`)

4. **Verify:**
   - `uv run pytest .rhiza/tests/test_rhiza/ -v --tb=short` — all pass
   - `make fmt` — clean

**Acceptance criteria:**
- No trivially-true tests remain
- No tests with empty/missing assertion blocks
- Each test file has a clear docstring
- All tests pass

---

## Final Directory Structure

```
.rhiza/tests/test_rhiza/
├── __init__.py
├── conftest.py              # Core fixtures: root, logger, git_repo
│                            # Helpers: strip_ansi, run_make, setup_rhiza_git_repo
│                            # Mock scripts: MOCK_UV_SCRIPT, MOCK_MAKE_SCRIPT
├── README.md
├── api/
│   ├── __init__.py
│   ├── conftest.py          # setup_tmp_makefile fixture, SPLIT_MAKEFILES
│   ├── test_makefile_targets.py
│   ├── test_makefile_api.py
│   └── test_github_targets.py
├── deps/
│   ├── __init__.py
│   └── test_dependency_health.py
├── integration/
│   ├── __init__.py
│   ├── test_release.py
│   ├── test_book_targets.py
│   ├── test_marimushka.py
│   └── test_notebook_execution.py
├── structure/
│   ├── __init__.py
│   ├── test_project_layout.py
│   └── test_requirements.py
├── sync/
│   ├── __init__.py
│   ├── conftest.py          # setup_sync_env fixture
│   ├── test_rhiza_version.py
│   ├── test_readme_validation.py
│   └── test_docstrings.py
└── utils/
    ├── __init__.py
    ├── conftest.py          # sys.path setup for version_matrix
    ├── test_git_repo_fixture.py
    └── test_version_matrix.py
```

---

## Notes for Agents

- **Always verify after each phase:** `uv run pytest .rhiza/tests/test_rhiza/ -v --tb=short`
- **Do NOT skip or combine phases** — each builds on the previous.
- **Use `git mv`** when moving files to preserve history.
- **Fixture scopes must be preserved** — `root` and `logger` are session-scoped.
- **Import convention:** use relative imports within the test package (e.g., `from ..conftest import strip_ansi`).
- **Run `make fmt` after each phase** to keep formatting consistent.
- **The old `tests/test_rhiza/` tests must keep passing** until the corresponding files are moved in each phase. Never have the same test in both locations simultaneously (move, don't copy).
