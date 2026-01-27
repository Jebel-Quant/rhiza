# Migration Guide

How to migrate existing Python projects to use Rhiza templates.

---

## Overview

This guide covers migrating a legacy Python project to Rhiza's living templates system. The migration process is designed to be incremental—you can adopt as much or as little as you need.

---

## Prerequisites

Before starting:

- [ ] Python 3.11+ installed
- [ ] Git repository initialized
- [ ] Backup or commit any uncommitted changes
- [ ] Review your current project structure

---

## Migration Paths

### Path A: Full Adoption (Recommended)

Adopt the complete Rhiza template including CI/CD, tooling, and project structure.

### Path B: Selective Adoption

Cherry-pick specific components (e.g., only CI workflows or only linting config).

### Path C: Template Fork

Fork Rhiza and customize for your organization's standards.

---

## Full Adoption Guide

### Step 1: Initialize Rhiza

```bash
cd /path/to/your/project

# Initialize Rhiza configuration
uvx rhiza init

# This creates:
# - .rhiza/template.yml (sync configuration)
# - Basic directory structure
```

### Step 2: Review template.yml

Edit `.rhiza/template.yml` to control what gets synced:

```yaml
repository: Jebel-Quant/rhiza
ref: main

include: |
  .github/workflows/*.yml
  .pre-commit-config.yaml
  ruff.toml
  pytest.ini
  Makefile
  .rhiza/rhiza.mk
  .editorconfig

exclude: |
  # Protect your customizations
  .rhiza/make.d/*
  pyproject.toml          # Keep your own
  README.md               # Keep your own
```

### Step 3: Materialize Templates

```bash
# Apply templates (creates/overwrites files)
uvx rhiza materialize

# Review changes
git status
git diff
```

### Step 4: Resolve Conflicts

Common conflicts and resolutions:

#### Makefile Conflicts

If you have an existing Makefile:

```bash
# Option 1: Rename yours and include it
mv Makefile Makefile.legacy
# Then in .rhiza/make.d/99-legacy.mk:
# include Makefile.legacy

# Option 2: Merge targets manually
# Copy your targets to .rhiza/make.d/50-custom.mk
```

#### pyproject.toml Conflicts

Rhiza doesn't sync `pyproject.toml` by default. Ensure yours has:

```toml
[project]
name = "your-project"
version = "1.0.0"
requires-python = ">=3.11"

# Add if missing
[dependency-groups]
dev = [
    # your dev dependencies
]
```

#### CI Workflow Conflicts

If you have existing `.github/workflows/`:

```yaml
# In template.yml, exclude specific workflows:
exclude: |
  .github/workflows/my-custom-workflow.yml
```

### Step 5: Install and Verify

```bash
# Install dependencies
make install

# Run tests
make test

# Check formatting
make fmt

# Verify dependencies
make deptry
```

### Step 6: Commit Migration

```bash
git add -A
git commit -m "chore: Migrate to Rhiza templates"
```

---

## Selective Adoption Guide

### CI/CD Only

To adopt only GitHub Actions workflows:

```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main

include: |
  .github/workflows/*.yml

exclude: |
  # Everything else excluded by default
```

### Linting Only

To adopt only code quality tools:

```yaml
# .rhiza/template.yml
include: |
  ruff.toml
  .pre-commit-config.yaml
  .editorconfig
```

### Makefile Only

To adopt only the Makefile system:

```yaml
# .rhiza/template.yml
include: |
  Makefile
  .rhiza/rhiza.mk
  .rhiza/make.d/README.md
```

---

## Common Migration Tasks

### Migrating from setup.py to pyproject.toml

```toml
# pyproject.toml
[project]
name = "your-package"
version = "1.0.0"
description = "Your description"
requires-python = ">=3.11"
dependencies = [
    # Move from install_requires
]

[dependency-groups]
dev = [
    "pytest>=7.0",
    # Move from extras_require["dev"]
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Migrating from requirements.txt

```bash
# Convert requirements.txt to pyproject.toml
# Option 1: Manual (recommended for cleanup)
# Copy dependencies to pyproject.toml [project.dependencies]

# Option 2: Keep requirements.txt for legacy support
# Place in .rhiza/requirements/ and they'll be installed
mkdir -p .rhiza/requirements
mv requirements.txt .rhiza/requirements/legacy.txt
```

### Migrating from tox to Makefile

| tox command | Rhiza equivalent |
|-------------|------------------|
| `tox` | `make test` |
| `tox -e lint` | `make fmt` |
| `tox -e docs` | `make docs` |
| `tox -e py311` | `PYTHON_VERSION=3.11 make test` |

### Migrating from Black/isort to Ruff

Ruff replaces both Black and isort. Remove from your config:

```bash
# Remove old configs
rm -f .black .isort.cfg pyproject.toml[tool.black] pyproject.toml[tool.isort]

# Ruff config is in ruff.toml (synced from template)
```

### Migrating from pip/pip-tools to uv

| pip command | uv equivalent |
|-------------|---------------|
| `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| `pip install -e .` | `uv pip install -e .` |
| `pip-compile` | `uv lock` |
| `pip-sync` | `uv sync` |

---

## Post-Migration Checklist

### Immediate

- [ ] `make install` succeeds
- [ ] `make test` passes
- [ ] `make fmt` passes
- [ ] `make deptry` passes
- [ ] CI workflows run successfully

### Short-term

- [ ] Update README.md with new commands
- [ ] Remove obsolete config files (setup.py, tox.ini, .black, etc.)
- [ ] Configure branch protection for main branch
- [ ] Set up required secrets (PAT_TOKEN for sync workflow)

### Long-term

- [ ] Enable scheduled sync workflow
- [ ] Configure Renovate for dependency updates
- [ ] Set up GitHub Pages for documentation
- [ ] Configure release workflow secrets

---

## Troubleshooting

### "Command not found: make"

Install make:
```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install build-essential

# Windows (use WSL or)
choco install make
```

### "uv: command not found"

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or let Rhiza install it
make install-uv
```

### Pre-commit hook failures

```bash
# Auto-fix most issues
make fmt

# If still failing, check specific hook
uvx pre-commit run <hook-id> --all-files
```

### Python version mismatch

```bash
# Check required version
cat .python-version

# Install with uv
uv python install 3.12

# Or specify version
PYTHON_VERSION=3.12 make install
```

### Import errors after migration

```bash
# Reinstall in development mode
uv pip install -e .

# Or full reinstall
make clean
make install
```

---

## Rollback

If you need to undo the migration:

```bash
# Revert all changes
git checkout .

# Or revert specific files
git checkout HEAD -- Makefile ruff.toml

# Remove Rhiza directory
rm -rf .rhiza
```

---

## Getting Help

- Check [docs/glossary.md](glossary.md) for term definitions
- Review [docs/architecture.md](architecture.md) for system design
- See [docs/QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands
- Open an issue at https://github.com/Jebel-Quant/rhiza/issues
