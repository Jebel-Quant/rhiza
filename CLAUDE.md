# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Rhiza is a **living template system** for modern Python projects. Unlike traditional one-time templates (cookiecutter, copier), Rhiza enables continuous synchronisation of configuration and best practices across repositories. Projects define which templates to sync via `.rhiza/template.yml`.

This repository is the template source itself, not a typical application codebase. It contains configuration templates, CI/CD workflows, and build tooling that flow to downstream projects.

## Essential Commands

```bash
make install         # Install uv, create .venv, install all dependencies
make test            # Run pytest with coverage
make fmt             # Format and lint with ruff (runs pre-commit hooks)
make deptry          # Check for missing/unused dependencies
```

### Running Specific Tests

```bash
pytest tests/test_rhiza/test_makefile.py -v     # Run a specific test file
pytest tests/test_rhiza/ -k "test_bump" -v      # Run tests matching pattern
```

### Other Useful Commands

```bash
make help            # Show all 40+ available targets
make marimo          # Start interactive Marimo notebook server
make book            # Build documentation
make docs            # Generate API docs with pdoc
make bump            # Bump version interactively
make release         # Create tag and push (triggers CI release)
```

## Architecture

### Makefile System

The build system uses a modular Makefile architecture:

- **`Makefile`** - Thin wrapper that includes `.rhiza/rhiza.mk`
- **`.rhiza/rhiza.mk`** - Core targets (template-managed, do not modify directly)
- **`.rhiza/make.d/*.mk`** - Custom extensions loaded alphabetically
- **`local.mk`** - Machine-specific overrides (not committed)

Custom targets use numeric prefixes to control load order:
- `00-19`: Configuration/Variables
- `20-79`: Custom tasks
- `80-99`: Hooks/Lifecycle

Hooks use double-colon syntax (`::`) to extend workflows:
```makefile
post-install::
    @echo "Custom post-install logic"
```

Available hooks: `pre/post-install`, `pre/post-sync`, `pre/post-validate`, `pre/post-release`, `pre/post-bump`

### Project Structure

```
.rhiza/           # Core Rhiza engine
  rhiza.mk        # Main Makefile API (template-managed)
  make.d/         # Custom Makefile extensions
  requirements/   # Tool-specific dependencies (tests.txt, docs.txt, etc.)
  scripts/        # Utility scripts (release.sh)
tests/test_rhiza/ # Test suite
book/             # Documentation and Marimo notebooks
docker/           # Container configuration
.github/          # GitHub Actions workflows (11 workflows)
.gitlab/          # GitLab CI configuration (feature parity)
```

### Test Infrastructure

Tests validate template infrastructure:
- `conftest.py` - Fixtures: `root` (project path), `logger`, `git_repo` (mock git environment)
- `test_makefile.py` - Validates Makefile targets
- `test_release_script.py` - Tests release automation
- `test_readme.py` - Executes code blocks from README
- `test_notebooks.py` - Validates Marimo notebooks

The `git_repo` fixture creates a complete mock git environment with fake `uv` and `make` binaries for testing git workflows.

## Code Style

- **Language**: UK English spelling (colour, organisation, synchronise)
- **Python**: 3.11+ (3.12 default), formatted by ruff
- **Line length**: 120 characters
- **Docstrings**: Google style
- **Quotes**: Double quotes

Ruff rules: D (docstrings), E/W (PEP 8), F (pyflakes), I (isort), N (naming), UP (pyupgrade)

## Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies |
| `.python-version` | Default Python version (3.12) |
| `ruff.toml` | Linter/formatter configuration |
| `pytest.ini` | Test configuration (live logs enabled) |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `.rhiza/template.yml` | Template sync configuration (downstream projects) |

## CI/CD

GitHub Actions workflows in `.github/workflows/`:
- `rhiza_ci.yml` - Multi-version Python testing (3.11, 3.12, 3.13, 3.14)
- `rhiza_release.yml` - Tag-triggered PyPI publishing
- `rhiza_sync.yml` - Template synchronisation PRs
- `rhiza_pre-commit.yml` - Pre-commit validation
- `rhiza_deptry.yml` - Dependency checking

Releases are git tag-based (`v*.*`). Use `make release` for interactive release workflow.
