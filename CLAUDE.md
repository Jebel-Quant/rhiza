# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Rhiza is a collection of reusable configuration templates for modern Python projects. Unlike traditional templates (cookiecutter, copier), Rhiza provides "living templates" that enable continuous synchronization of best practices across projects via `.rhiza/template.yml` configuration.

## Essential Commands

```bash
make install     # Install uv, create .venv, install all dependencies
make test        # Run pytest with coverage
make fmt         # Format (ruff format) and lint (ruff check --fix)
make deptry      # Check for missing/unused dependencies
make help        # Display all 40+ available targets
```

### Running a Single Test

```bash
uv run pytest tests/test_rhiza/test_readme.py -v           # Run specific test file
uv run pytest tests/test_rhiza/test_readme.py::test_name   # Run specific test function
```

## Architecture

### Makefile System

The Makefile is hierarchical and modular:

- `Makefile` - Minimal entry point (8 lines), includes `.rhiza/rhiza.mk`
- `.rhiza/rhiza.mk` - Core logic and orchestration
- `.rhiza/make.d/*.mk` - Auto-loaded extensions (numeric prefixes control load order: 00-19 config, 20-79 tasks, 80-99 hooks)
- `local.mk` - Developer-local extensions (not committed)

**Hook System** (double-colon targets): `pre-install::`, `post-install::`, `pre-sync::`, `post-sync::`, `pre-validate::`, `post-validate::`, `pre-release::`, `post-release::`, `pre-bump::`, `post-bump::`

### All Python Execution Through uv

All commands use `uv run` for Python execution and `uvx` for external tools. Never call Python directly.

### Test Organization

Tests in `tests/test_rhiza/`:
- `conftest.py` - Fixtures including `git_repo` for sandboxed git testing and mock `uv`/`make` scripts
- `test_readme.py` - Validates code blocks in README.md actually work
- `test_makefile.py` - Validates Makefile targets
- `test_release_script.py` - Tests release workflow

## Code Style

- **Ruff** enforces: D (pydocstyle/Google convention), E, F, I (isort), N, W, UP
- **Line length**: 120 characters
- **Docstrings**: Required for modules, classes, functions, magic methods (Google style)
- **Quotes**: Double quotes for strings

## Key Conventions

1. **Makefile-first**: All operations go through Makefile targets
2. **Version source of truth**: `pyproject.toml` version field only
3. **Custom tasks**: Add to `.rhiza/make.d/` (not core files) to preserve sync compatibility
4. **Template sync**: `.rhiza/template.yml` defines include/exclude patterns for upstream sync
