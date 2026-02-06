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

## ⚠️ NEXT AGENT: Start with Phase 4

**Agent instructions:**

1. **Move `tests/test_rhiza/test_release_script.py` → `.rhiza/tests/test_rhiza/integration/test_release.py`**
   - Uses `git_repo` fixture from root conftest — no changes needed
   - Use `git mv` to preserve history

2. **Move `tests/test_rhiza/test_book.py` → `.rhiza/tests/test_rhiza/integration/test_book_targets.py`**
   - Uses `git_repo` fixture — no changes needed
   - Use `git mv` to preserve history

3. **Move `tests/test_rhiza/test_marimushka_target.py` → `.rhiza/tests/test_rhiza/integration/test_marimushka.py`**
   - Uses `git_repo` fixture — no changes needed
   - Use `git mv` to preserve history

4. **Move `tests/test_rhiza/test_notebooks.py` → `.rhiza/tests/test_rhiza/integration/test_notebook_execution.py`**
   - **Improvement:** Add a standalone test function that fails or skips explicitly when no notebooks are discovered, so silent no-ops are surfaced:
     ```python
     def test_notebooks_discovered():
         """At least one notebook should be discovered for parametrized tests to run."""
         if not NOTEBOOK_PATHS:
             pytest.skip("No Marimo notebooks found — check MARIMO_FOLDER in .rhiza/.env")
     ```
   - Use `git mv` to preserve history

5. **Verify:**
   - `uv run pytest .rhiza/tests/test_rhiza/integration/ -v` — all pass or skip
   - `uv run pytest -q` — total count correct
   - `make fmt` — clean

**Acceptance criteria:**
- All integration tests pass from new location
- Originals removed from `tests/test_rhiza/`
- Notebook discovery guard test added
- Changes committed with descriptive message

---

## Phase 4: Move Integration Tests → `integration/`

**Goal:** Move tests requiring sandboxed git repos or subprocess execution.

**Agent instructions:**

1. **Create `.rhiza/tests/test_rhiza/api/conftest.py`** with shared fixtures:
   - Extract the `setup_tmp_makefile` autouse fixture from `test_makefile.py`
   - Extract the `SPLIT_MAKEFILES` constant from `test_makefile.py`
   - Include a local `run_make` function (or import from parent conftest — agent's choice, but avoid duplication)
   - The `setup_gh_makefile` fixture from `test_makefile_gh.py` is similar to `setup_tmp_makefile` but copies `.rhiza/.env` directly. Consolidate: make `setup_tmp_makefile` also copy the real `.env` if it exists (or parameterise it), so a single fixture serves all three test files.

2. **Move `tests/test_rhiza/test_makefile.py` → `.rhiza/tests/test_rhiza/api/test_makefile_targets.py`**
   - Remove the local `run_make`, `strip_ansi`, `setup_rhiza_git_repo`, `setup_tmp_makefile`, `SPLIT_MAKEFILES` — all now in conftest
   - Import what's needed: `from ..conftest import strip_ansi, setup_rhiza_git_repo`
   - Keep test classes: `TestMakefile`, `TestMakefileRootFixture`, `TestMakeBump`

3. **Move `tests/test_rhiza/test_makefile_api.py` → `.rhiza/tests/test_rhiza/api/test_makefile_api.py`**
   - Remove the local `run_make`
   - Keep the `setup_api_env` fixture (it's meaningfully different — full project copy vs minimal)
   - Keep all test functions

4. **Move `tests/test_rhiza/test_makefile_gh.py` → `.rhiza/tests/test_rhiza/api/test_github_targets.py`**
   - Remove the local `run_make` and `setup_gh_makefile` (now handled by shared conftest)

5. **Verify:**
   - `uv run pytest .rhiza/tests/test_rhiza/api/ -v` — all pass
   - `uv run pytest -q` — total count correct

**Acceptance criteria:**
- No duplicate `run_make`, `strip_ansi`, or `setup_rhiza_git_repo` across api test files
- All API tests pass from new location
- Originals removed from `tests/test_rhiza/`

---

## Phase 4: Move Integration Tests → `integration/`

**Goal:** Move tests requiring sandboxed git repos or subprocess execution.

**Agent instructions:**

1. **Move `tests/test_rhiza/test_release_script.py` → `.rhiza/tests/test_rhiza/integration/test_release.py`**
   - Uses `git_repo` fixture from root conftest — no changes needed

2. **Move `tests/test_rhiza/test_book.py` → `.rhiza/tests/test_rhiza/integration/test_book_targets.py`**
   - Uses `git_repo` fixture — no changes needed

3. **Move `tests/test_rhiza/test_marimushka_target.py` → `.rhiza/tests/test_rhiza/integration/test_marimushka.py`**
   - Uses `git_repo` fixture — no changes needed

4. **Move `tests/test_rhiza/test_notebooks.py` → `.rhiza/tests/test_rhiza/integration/test_notebook_execution.py`**
   - **Improvement:** Add a standalone test function that fails or skips explicitly when no notebooks are discovered, so silent no-ops are surfaced:
     ```python
     def test_notebooks_discovered():
         """At least one notebook should be discovered for parametrized tests to run."""
         if not NOTEBOOK_PATHS:
             pytest.skip("No Marimo notebooks found — check MARIMO_FOLDER in .rhiza/.env")
     ```

5. **Verify:**
   - `uv run pytest .rhiza/tests/test_rhiza/integration/ -v` — all pass or skip
   - `uv run pytest -q` — total count correct

**Acceptance criteria:**
- All integration tests pass from new location
- Originals removed
- Notebook discovery guard test added

---

## Phase 5: Move Sync Tests → `sync/`

**Goal:** Move template sync, versioning, and content validation tests.

**Agent instructions:**

1. **Create `.rhiza/tests/test_rhiza/sync/conftest.py`**
   - Extract the `setup_tmp_makefile` fixture from `test_rhiza_workflows.py` — it's different from the api one (creates `template.yml`, `pyproject.toml`, runs `setup_rhiza_git_repo`, creates `src/` and `tests/` dirs)
   - Keep it as a separate fixture (e.g. `setup_sync_env`) to avoid confusion with the api version

2. **Move `tests/test_rhiza/test_rhiza_workflows.py` → `.rhiza/tests/test_rhiza/sync/test_rhiza_version.py`**
   - Currently imports `from .conftest import run_make, setup_rhiza_git_repo, strip_ansi` — update to `from ..conftest import ...`
   - Remove the local `setup_tmp_makefile` fixture (now in `sync/conftest.py`)
   - Keep classes: `TestRhizaVersion`, `TestSummariseSync`, `TestWorkflowSync`

3. **Move `tests/test_rhiza/test_readme.py` → `.rhiza/tests/test_rhiza/sync/test_readme_validation.py`**
   - No changes needed

4. **Move `tests/test_rhiza/test_docstrings.py` → `.rhiza/tests/test_rhiza/sync/test_docstrings.py`**
   - No changes needed

5. **Verify:**
   - `uv run pytest .rhiza/tests/test_rhiza/sync/ -v` — all pass or skip
   - `uv run pytest -q` — total count correct

**Acceptance criteria:**
- All sync tests pass from new location
- `from .conftest` imports updated to `from ..conftest`
- Originals removed

---

## Phase 6: Move Utility Tests → `utils/`

**Goal:** Move tests for utilities and test infrastructure.

**Agent instructions:**

1. **Move `tests/test_rhiza/test_git_repo_fixture.py` → `.rhiza/tests/test_rhiza/utils/test_git_repo_fixture.py`**
   - No changes needed

2. **Move `tests/test_rhiza/test_version_matrix.py` → `.rhiza/tests/test_rhiza/utils/test_version_matrix.py`**
   - **Improvement:** Move the `sys.path.insert()` hack into `.rhiza/tests/test_rhiza/utils/conftest.py`:
     ```python
     import sys
     from pathlib import Path
     sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "utils"))
     ```
   - Remove the `sys.path.insert` from the test file itself

3. **Verify:**
   - `uv run pytest .rhiza/tests/test_rhiza/utils/ -v` — all pass
   - `uv run pytest -q` — total count correct

**Acceptance criteria:**
- All utility tests pass from new location
- `sys.path` manipulation in conftest, not test file
- Originals removed

---

## Phase 7: Create Dependency Tests → `deps/`

**Goal:** Add meaningful dependency validation tests (new tests, not moved).

**Agent instructions:**

1. **Create `.rhiza/tests/test_rhiza/deps/test_dependency_health.py`** with:
   - `test_pyproject_has_requires_python` — `pyproject.toml` has `requires-python` under `[project]`
   - `test_requirements_files_are_valid_pip_specifiers` — each line in `.rhiza/requirements/*.txt` (ignoring comments/blanks) is a parseable requirement specifier
   - `test_no_duplicate_packages_across_requirements` — no package appears in more than one requirements file
   - `test_dotenv_in_test_requirements` — `python-dotenv` is listed in `tests.txt` (the test suite depends on it)

2. **These complement (not duplicate) the `structure/test_requirements.py` tests** — structure tests check that files exist, deps tests check that content is valid.

3. **Verify:**
   - `uv run pytest .rhiza/tests/test_rhiza/deps/ -v` — all pass

**Acceptance criteria:**
- `deps/test_dependency_health.py` exists and passes
- Tests validate content, not just existence

---

## Phase 8: Clean Up and Final Verification

**Goal:** Remove the old `tests/test_rhiza/` directory (except benchmarks), update docs, verify everything.

**Agent instructions:**

1. **Verify `tests/test_rhiza/` is empty of test files**
   - At this point only `__init__.py`, `conftest.py`, `README.md`, and `benchmarks/` should remain
   - Remove `__init__.py`, `conftest.py`, `README.md` (they've been copied/moved to `.rhiza/tests/`)
   - Keep `benchmarks/` in place (or move to `tests/benchmarks/` if it's not already there)

2. **Update `pytest.ini` `testpaths`** — remove `tests` if it only contains benchmarks (and benchmarks are run via a separate `make benchmark` target, not `make test`). Or keep it if benchmarks should be discoverable.

3. **Update `.rhiza/tests/test_rhiza/README.md`**
   - Update the "Test Organization" section with the new folder layout
   - Update example commands to reference `.rhiza/tests/`

4. **Run full verification:**
   ```bash
   uv run pytest .rhiza/tests/test_rhiza/ -v --tb=short   # all pass
   make fmt                                                  # formatting clean
   make test                                                 # full project suite works
   ```

**Acceptance criteria:**
- No `test_*.py` files in `tests/test_rhiza/` (only benchmarks remain under `tests/`)
- Full suite passes from `.rhiza/tests/`
- `make fmt` and `make test` pass
- README updated

---

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
