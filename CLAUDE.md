# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Rhiza?

Rhiza is a **collection of reusable configuration templates** for Python projects — not a runtime library. It has no `src/` directory and no runtime dependencies. Its purpose is to provide and continuously synchronize development infrastructure (Makefiles, CI workflows, linting configs, test setups) into downstream projects via the separate `rhiza-cli` tool.

Downstream projects adopt Rhiza by adding a `.rhiza/template.yml` that lists which bundles to sync from this repository.

## Commands

```bash
make install      # Full setup: installs uv, downloads Python 3.13, creates .venv, installs deps
make test         # Run all tests with coverage (90% minimum required)
make fmt          # Run all pre-commit hooks (ruff format/check, markdownlint, bandit, etc.)
make deptry       # Check for unused/missing dependencies
make docs-coverage  # Check docstring coverage (100% required)
make typecheck    # Static type checking with ty
make benchmark    # Performance benchmarks
make hypothesis-test  # Property-based tests only
make stress       # Load/concurrency tests
make security     # pip-audit + bandit security scans
make book         # Build documentation
make marimo       # Start Marimo notebook server
make clean        # Remove build artifacts and stale branches
```

**Running a single test:**
```bash
uv run pytest tests/api/test_makefile_targets.py -v
uv run pytest tests/api/test_makefile_targets.py::TestClass::test_method -v
uv run pytest -m "not stress" tests/   # Exclude stress tests
```

## Command Execution Policy

Follow this order strictly:

1. If a `make` target exists → use `make <target>`
2. No `make` target → use `uv run <command>`
3. Never invoke `.venv/bin/python`, `.venv/bin/pytest`, etc. directly

The virtual environment is managed automatically by `make` and `uv run`. No manual activation is needed.

## Architecture

### Template Bundles

The core abstraction is the **bundle** — a named group of configuration files. The 13 bundles are defined in `.rhiza/template-bundles.yml`:

- `core` (required): Makefiles, linting, base infrastructure
- `tests`: pytest, coverage, type checking
- `github`: GitHub Actions workflows
- `gitlab`: GitLab CI
- `docker`, `devcontainer`: containerisation
- `marimo`: interactive notebooks
- `book`: documentation with pdoc + mkdocs
- `presentation`: Marp slides
- `lfs`, `legal`, `renovate`, `gh-aw`: miscellaneous tooling

### Modular Makefile System

The root `Makefile` is intentionally thin (~10 lines) and only `include`s `.rhiza/rhiza.mk`. That file auto-loads everything in `.rhiza/make.d/*.mk` alphabetically.

Hook targets use double-colon syntax (`pre-install::`, `post-install::`) and can be defined multiple times to chain behaviour. Add project-specific hooks directly in the root `Makefile` above the include line. Developer-local shortcuts go in `local.mk` (not committed).

### Dependency Management

`uv` manages all Python/dependency concerns:
- `.python-version` is the single source of truth for the Python version
- `uv.lock` pins all transitive dependencies — keep it in sync via `uv lock` or `uv sync`
- `uv run` transparently uses the project venv without manual activation

### Code Quality Requirements

- **Ruff** (`ruff.toml`): line length 120, Google-style docstrings, double quotes, rules D/E/F/I/N/W/UP/B/C4/SIM/PT/RUF/S/TRY/ICN
- **Docstring coverage**: 100% (interrogate) — all public functions, classes, and modules require docstrings
- **Test coverage**: 90% minimum
- **Pre-commit hooks**: `make fmt` runs ruff, markdownlint, bandit, actionlint, interrogate, jsonschema, and uv-lock validation

### GitHub Agentic Workflows (gh-aw)

Agentic workflows live in `.github/workflows/` as `.md` source files compiled to `.lock.yml`. **Never edit `.lock.yml` files directly.** After editing any `.md` workflow:

```bash
make gh-aw-compile   # Recompile .md → .lock.yml
```

Always commit both the `.md` and the updated `.lock.yml` together.

### CI/CD

- **GitHub Actions** (primary): `.github/workflows/` — CI, release, docker, CodeQL, weekly, sync
- **GitLab CI** (parallel): `.gitlab-ci.yml` — mirrors GitHub Actions coverage
- Agent environment is pre-configured via `.github/workflows/copilot-setup-steps.yml` (runs before agent starts) and `.github/hooks/hooks.json` (quality gates: `make fmt` + `make test` on session end)
