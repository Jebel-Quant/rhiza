# Rhiza Technical Analysis

**Repository**: Rhiza - Living Template Framework for Python Projects
**Analysis Date**: 2026-01-18
**Version**: 0.6.0
**Author**: Thomas Schmelzer / Jebel-Quant

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Purpose and Philosophy](#project-purpose-and-philosophy)
3. [Repository Structure](#repository-structure)
4. [Architecture Deep Dive](#architecture-deep-dive)
5. [Technology Stack](#technology-stack)
6. [CI/CD Pipeline Analysis](#cicd-pipeline-analysis)
7. [Testing Strategy](#testing-strategy)
8. [Security Measures](#security-measures)
9. [Configuration Management](#configuration-management)
10. [Developer Experience](#developer-experience)
11. [Design Patterns and Decisions](#design-patterns-and-decisions)
12. [Extension Points](#extension-points)

---

## Executive Summary

Rhiza is a sophisticated **living template framework** that solves the problem of configuration drift across Python projects. Unlike traditional generators (cookiecutter, copier) that produce static snapshots, Rhiza provides continuously-synchronized configuration templates that evolve with best practices.

**Core Value Proposition**: Projects using Rhiza can selectively synchronize updates from the upstream template over time, benefiting from improvements to CI/CD workflows, linting rules, and development tooling without manual maintenance.

**Key Metrics**:
- 14 GitHub Actions workflows
- 40+ Makefile targets
- 15 test files with 2,299 lines of test code
- 90% coverage threshold enforced
- Python 3.11-3.14 support

---

## Project Purpose and Philosophy

### The Problem

Traditional project templates suffer from **configuration drift**:
1. Generate project from template (one-time operation)
2. Template improves over time with new best practices
3. Downstream projects become outdated
4. Manual effort required to backport improvements
5. Teams diverge in tooling and quality standards

### The Solution

Rhiza implements a **living template** pattern:

```
Upstream Template (Rhiza) ──sync──> Downstream Project A
                          ──sync──> Downstream Project B
                          ──sync──> Downstream Project C
```

**Selective Synchronization**: Projects control what syncs via `.rhiza/template.yml`:
```yaml
repository: Jebel-Quant/rhiza
ref: main
include:
  - .github/workflows/*.yml
  - .pre-commit-config.yaml
  - ruff.toml
exclude:
  - .rhiza/scripts/customisations/*
```

**Customization Without Conflict**: The double-colon hook system allows projects to extend behavior without modifying synced files.

---

## Repository Structure

```
rhiza/
├── .rhiza/                      # Core infrastructure (synced to downstream)
│   ├── rhiza.mk                 # Main Makefile (274 lines)
│   ├── make.d/                  # Modular extensions (00-99 numeric prefixes)
│   ├── scripts/                 # Shell scripts (POSIX-compliant)
│   ├── utils/                   # Python utilities
│   ├── requirements/            # Development dependencies
│   ├── template.yml             # Sync configuration
│   ├── .cfg.toml               # Bumpversion configuration
│   └── .env                     # Environment variables
│
├── .github/                     # GitHub Actions
│   ├── workflows/               # 14 workflow files
│   ├── github.mk                # GitHub helper commands
│   └── agents/                  # AI agent integrations
│
├── .gitlab/                     # GitLab CI/CD (feature parity)
│   └── workflows/
│
├── src/hello/                   # Minimal example package
│   ├── __init__.py
│   └── hello.py                 # Test module (15 lines)
│
├── tests/test_rhiza/            # Comprehensive test suite
│   ├── conftest.py              # Fixtures & mocks
│   ├── test_makefile.py         # Dry-run target validation
│   ├── test_release_script.py   # Release workflow tests
│   ├── test_structure.py        # Project structure validation
│   ├── test_readme.py           # README code testing
│   └── benchmarks/              # Performance tests
│
├── book/                        # Documentation generation
│   ├── marimo/                  # Interactive notebooks
│   ├── pdoc-templates/          # API doc templates
│   └── book.mk                  # Documentation targets
│
├── docker/                      # Container configuration
│   ├── Dockerfile               # Production image
│   └── docker.mk                # Docker targets
│
├── docs/                        # Additional documentation
│   ├── ARCHITECTURE.md          # Mermaid diagrams
│   ├── GLOSSARY.md             # Terminology
│   ├── CUSTOMIZATION.md        # Extension guide
│   ├── QUICK_REFERENCE.md      # Command reference
│   └── RELEASING.md            # Release process
│
├── Makefile                     # Root (9 lines, thin wrapper)
├── pyproject.toml               # Project metadata
├── ruff.toml                    # Linter configuration (124 lines)
├── pytest.ini                   # Test configuration
├── .pre-commit-config.yaml      # Git hooks (10 checks)
└── uv.lock                      # Reproducible dependency lock
```

---

## Architecture Deep Dive

### Makefile Hierarchical System

The build system uses a layered architecture:

```
Makefile (9 lines)
  │
  └─> include .rhiza/rhiza.mk (274 lines)
        │
        ├─> include .rhiza/make.d/*.mk (auto-loaded by number)
        │     ├─> 00-19: Configuration files
        │     ├─> 20-79: Task definitions
        │     └─> 80-99: Hook implementations
        │
        ├─> -include tests/tests.mk
        ├─> -include book/book.mk
        ├─> -include presentation/presentation.mk
        ├─> -include docker/docker.mk
        ├─> -include .github/github.mk
        └─> -include local.mk (optional, not synced)
```

**Design Benefits**:
1. **Root Makefile stays minimal**: Never conflicts during sync
2. **Core logic is separated**: Easy to maintain and understand
3. **Extensions auto-load**: Numeric prefixes control order
4. **Local customization preserved**: `local.mk` never synced

### Double-Colon Hook System

Rhiza uses GNU Make's double-colon targets for extensibility:

```makefile
# In .rhiza/rhiza.mk (core definition)
pre-install:: ; @:
post-install:: ; @:

install:: pre-install
    @echo "Installing dependencies..."
    uv sync --all-extras --all-groups --frozen
install:: post-install

# In downstream project's .rhiza/make.d/80-hooks.mk
post-install::
    @echo "Running custom post-install steps..."
    ./scripts/setup-database.sh
```

**Available Hooks**:
| Hook | Triggered |
|------|-----------|
| `pre-install::` / `post-install::` | Before/after dependency installation |
| `pre-sync::` / `post-sync::` | Before/after template synchronization |
| `pre-validate::` / `post-validate::` | Before/after project validation |
| `pre-release::` / `post-release::` | Before/after release creation |
| `pre-bump::` / `post-bump::` | Before/after version bumping |

### Python Execution Model

All Python execution routes through `uv`:

```makefile
# Direct execution
uv run pytest tests/

# Tool execution (ephemeral)
uvx ruff check src/

# Script execution
uv run python -m hello
```

**Benefits**:
- No activation of virtual environments required
- Consistent behavior across CI and local development
- Fast execution (uv is 10-100x faster than pip)

---

## Technology Stack

### Core Tools

| Tool | Purpose | Version |
|------|---------|---------|
| **Python** | Language runtime | 3.11, 3.12, 3.13, 3.14 |
| **uv** | Package management | Latest |
| **Hatch** | Build backend | Latest |
| **Ruff** | Linting & formatting | 0.14.x |
| **pytest** | Testing framework | Latest |
| **mypy** | Static type checking | Latest |

### CI/CD Tools

| Tool | Purpose |
|------|---------|
| **GitHub Actions** | Primary CI/CD platform |
| **GitLab CI** | Alternative CI/CD (feature parity) |
| **Renovate** | Automated dependency updates |
| **CodeQL** | Semantic code analysis |
| **actionlint** | GitHub Actions linting |

### Code Quality Tools

| Tool | Purpose |
|------|---------|
| **ruff** | Linting (15+ rule sets) and formatting |
| **mypy** | Static type checking (strict mode) |
| **deptry** | Dependency hygiene |
| **bandit** | Security scanning |
| **pip-audit** | Vulnerability detection |
| **pre-commit** | Git hooks framework |

### Documentation Tools

| Tool | Purpose |
|------|---------|
| **pdoc** | API documentation from docstrings |
| **minibook** | Companion documentation generation |
| **Marimo** | Interactive reactive notebooks |
| **Marp** | Markdown-based presentations |

---

## CI/CD Pipeline Analysis

### Workflow Inventory

Rhiza includes 14 GitHub Actions workflows:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `rhiza_ci.yml` | Push, PR | Multi-Python testing (3.11-3.14) |
| `rhiza_release.yml` | Tag `v*` | Multi-phase release pipeline |
| `rhiza_security.yml` | Schedule, Push | pip-audit + bandit |
| `rhiza_codeql.yml` | Schedule, Push | CodeQL analysis |
| `rhiza_mypy.yml` | Push, PR | Static type checking |
| `rhiza_deptry.yml` | Push, PR | Dependency validation |
| `rhiza_pre-commit.yml` | PR | Pre-commit hook validation |
| `rhiza_validate.yml` | Push, PR | Project structure validation |
| `rhiza_sync.yml` | Manual | Template synchronization |
| `rhiza_benchmarks.yml` | Push, PR | Performance regression detection |
| `rhiza_book.yml` | Push | Documentation + coverage reports |
| `rhiza_marimo.yml` | Push, PR | Notebook validation |
| `rhiza_docker.yml` | Push, PR | Docker image building |
| `rhiza_devcontainer.yml` | Push, PR | Dev container validation |

### Dynamic Version Matrix

The CI workflow dynamically generates its Python version matrix:

```yaml
generate-matrix:
  runs-on: ubuntu-latest
  outputs:
    python-versions: ${{ steps.set-matrix.outputs.python-versions }}
  steps:
    - uses: actions/checkout@v4
    - run: |
        matrix=$(make -f .rhiza/rhiza.mk -s version-matrix)
        echo "python-versions=$matrix" >> "$GITHUB_OUTPUT"

test:
  needs: generate-matrix
  strategy:
    matrix:
      python-version: ${{ fromJson(needs.generate-matrix.outputs.python-versions) }}
```

**Source of Truth**: `pyproject.toml` contains `requires-python = ">=3.11"`, which `version_matrix.py` parses to generate `["3.11", "3.12", "3.13", "3.14"]`.

### Release Pipeline

The release workflow implements a multi-phase pipeline:

```
Tag Push (v*.*.*)
    │
    ├─> Phase 1: Validate
    │     └─> Check version consistency
    │
    ├─> Phase 2: Build
    │     └─> Build wheel and sdist
    │
    ├─> Phase 3: Draft Release
    │     └─> Create GitHub release (draft)
    │
    ├─> Phase 4: Publish PyPI (conditional)
    │     └─> OIDC trusted publishing
    │
    ├─> Phase 5: Publish DevContainer (optional)
    │     └─> Push to ghcr.io
    │
    └─> Phase 6: Finalize
          └─> Mark release as non-draft
```

**Security Features**:
- OIDC authentication (no stored PyPI tokens)
- SLSA provenance attestations
- Conditional skip for private packages
- Minimal permissions model

---

## Testing Strategy

### Test Categories

| Category | Files | Purpose |
|----------|-------|---------|
| **Makefile Tests** | `test_makefile.py`, `test_makefile_api.py` | Validate make targets via dry-run |
| **Structure Tests** | `test_structure.py` | Ensure project layout consistency |
| **Script Tests** | `test_release_script.py` | Validate shell script behavior |
| **Documentation Tests** | `test_readme.py`, `test_docstrings.py` | Execute code examples |
| **Utility Tests** | `test_version_matrix.py` | Unit test Python utilities |
| **Benchmark Tests** | `benchmarks/` | Performance regression detection |

### Innovative Testing Techniques

**1. Dry-Run Makefile Testing**

```python
def test_install_target(capsys):
    """Test that 'make install' target is defined and runnable."""
    result = subprocess.run(
        ["make", "-n", "install"],  # -n = dry-run
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
```

**2. README Code Block Execution**

```python
def test_readme_code_examples():
    """Execute Python code blocks from README.md."""
    readme = Path("README.md").read_text()
    for block in extract_python_blocks(readme):
        exec(block)  # Validates documentation accuracy
```

**3. Git Repository Sandbox Fixture**

```python
@pytest.fixture
def git_repo(tmp_path):
    """Create isolated git repo for testing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo)
    # ... setup mock uv and make scripts
    return repo
```

### Coverage Requirements

- **Threshold**: 90% minimum (`--cov-fail-under=90`)
- **Reports**: HTML, JSON, terminal
- **Publishing**: GitHub Pages via `make book`

---

## Security Measures

### Multi-Layer Security

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Code Analysis                                      │
│  ├─ CodeQL (semantic analysis)                              │
│  ├─ Bandit (security patterns)                              │
│  └─ Ruff (bug detection rules)                              │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Dependency Security                                │
│  ├─ pip-audit (vulnerability scanning)                      │
│  ├─ deptry (dependency hygiene)                             │
│  └─ Renovate (automated updates)                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Supply Chain Security                              │
│  ├─ OIDC trusted publishing (no stored credentials)         │
│  ├─ SLSA provenance attestations                            │
│  ├─ SBOM generation capability                              │
│  └─ uv.lock (reproducible builds)                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: CI/CD Security                                     │
│  ├─ Minimal permissions model                               │
│  ├─ actionlint + shellcheck validation                      │
│  └─ Full workflow linting                                   │
└─────────────────────────────────────────────────────────────┘
```

### OIDC Trusted Publishing

PyPI publishing uses OpenID Connect instead of stored tokens:

```yaml
publish-pypi:
  permissions:
    id-token: write  # OIDC token generation
  steps:
    - uses: pypa/gh-action-pypi-publish@release/v1
      # No PYPI_TOKEN needed - GitHub OIDC authenticates directly
```

---

## Configuration Management

### Configuration Files Overview

| File | Lines | Purpose |
|------|-------|---------|
| `pyproject.toml` | ~100 | Project metadata, dependencies, tool configs |
| `ruff.toml` | 124 | Linter/formatter rules (15+ rule sets) |
| `.pre-commit-config.yaml` | 67 | 10 pre-commit hooks |
| `.editorconfig` | 44 | Editor settings (indent, line endings) |
| `pytest.ini` | 15 | Test runner configuration |
| `.rhiza/.cfg.toml` | ~30 | Bumpversion configuration |
| `renovate.json` | ~10 | Dependency update bot |

### Ruff Configuration Highlights

```toml
[lint]
select = [
    "D",     # pydocstyle (Google-style docstrings)
    "E", "W", "F",  # pycodestyle, pyflakes
    "I",     # isort (import sorting)
    "N",     # pep8-naming
    "UP",    # pyupgrade (modern Python syntax)
    "B",     # flake8-bugbear
    "C4",    # flake8-comprehensions
    "PT",    # pytest-style
    "TRY",   # tryceratops (exception handling)
    "ICN",   # import conventions
    "RUF",   # Ruff-specific rules
]

line-length = 120
target-version = "py311"

[lint.pydocstyle]
convention = "google"
```

### Pre-commit Hooks

| Hook | Source | Purpose |
|------|--------|---------|
| check-toml | pre-commit-hooks | TOML validation |
| check-yaml | pre-commit-hooks | YAML validation |
| ruff | ruff-pre-commit | Linting with autofix |
| ruff-format | ruff-pre-commit | Code formatting |
| markdownlint | markdownlint-cli2 | Markdown style |
| check-renovate | python-jsonschema | Renovate schema |
| check-github-workflows | python-jsonschema | GH Actions schema |
| actionlint | actionlint | GH Actions linting |
| validate-pyproject | validate-pyproject | pyproject.toml schema |
| bandit | bandit | Security checking |

---

## Developer Experience

### Quick Start

```bash
# One command setup
make install

# See all available targets
make help
```

### Target Categories

| Category | Targets | Purpose |
|----------|---------|---------|
| **Bootstrap** | `install-uv`, `install`, `clean` | Environment setup |
| **Quality** | `fmt`, `deptry`, `mypy` | Code quality |
| **Testing** | `test`, `benchmark` | Test execution |
| **Releasing** | `bump`, `release` | Version management |
| **Documentation** | `docs`, `book` | Doc generation |
| **Docker** | `docker-build`, `docker-run` | Container operations |
| **GitHub** | `view-prs`, `view-issues` | GitHub helpers |
| **Rhiza** | `sync`, `validate`, `readme` | Template management |

### Local Customization

Projects can extend without modifying synced files:

```makefile
# local.mk (never synced)
.PHONY: deploy
deploy:
    @echo "Deploying to production..."
    kubectl apply -f k8s/
```

```makefile
# .rhiza/make.d/80-hooks.mk (synced but designed for extension)
post-install::
    @echo "Installing dev database..."
    docker-compose up -d postgres
```

---

## Design Patterns and Decisions

### 1. Convention Over Configuration

Default behaviors work out-of-the-box:
- Python version from `.python-version`
- Dependencies from `pyproject.toml`
- Virtual environment in `.venv`

### 2. Single Source of Truth

- **Python versions**: `pyproject.toml` `requires-python`
- **Project version**: `pyproject.toml` `version`
- **Dependencies**: `uv.lock` (generated from `pyproject.toml`)

### 3. Fail-Fast Philosophy

```makefile
SHELL := /bin/bash -o pipefail
```

```shell
#!/bin/sh
set -eu  # Exit on error, undefined variables
```

### 4. Explicit Over Implicit

- All uv commands specify `--all-extras --all-groups`
- Workflows declare minimal permissions explicitly
- Configuration files are comprehensive, not minimal

### 5. Graceful Degradation

```makefile
-include local.mk  # Optional, doesn't fail if missing
```

```yaml
if: ${{ hashFiles('dist/*') != '' }}  # Skip if no artifacts
```

---

## Extension Points

### For Downstream Projects

1. **Hook Implementation** (`.rhiza/make.d/80-*.mk`)
   ```makefile
   post-install::
       ./scripts/setup-local-db.sh
   ```

2. **Local Targets** (`local.mk`)
   ```makefile
   deploy: build
       kubectl apply -f k8s/
   ```

3. **Sync Configuration** (`.rhiza/template.yml`)
   ```yaml
   exclude:
     - .github/workflows/custom_*.yml
   ```

4. **Environment Variables** (`.rhiza/.env`)
   ```bash
   CUSTOM_SCRIPTS_FOLDER=./scripts
   ```

### For Template Maintainers

1. **New Workflows**: Add to `.github/workflows/rhiza_*.yml`
2. **New Make Targets**: Add to `.rhiza/make.d/20-*.mk`
3. **New Hooks**: Define in `.rhiza/rhiza.mk`
4. **New Scripts**: Add to `.rhiza/scripts/`

---

## Conclusion

Rhiza represents a mature, well-architected solution to the configuration drift problem in Python project management. Its key innovations:

1. **Living Templates**: Continuous synchronization vs. one-shot generation
2. **Double-Colon Hooks**: Extension without override
3. **Dynamic CI Matrix**: Single source of truth for Python versions
4. **Multi-Layer Security**: OIDC, SLSA, CodeQL, bandit, pip-audit
5. **Comprehensive Testing**: Dry-run validation, README testing, sandboxed fixtures

The architecture balances flexibility with standardization, allowing teams to benefit from shared best practices while maintaining project-specific customizations.
