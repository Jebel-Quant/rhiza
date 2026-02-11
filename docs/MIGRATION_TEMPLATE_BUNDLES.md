# Migration Guide: Path-Based to Template-Based Configuration

This guide helps you migrate from path-based template configuration to the new template-based approach.

## Overview

Rhiza now supports a **template-centric** approach where you select feature bundles instead of listing individual file paths. This simplifies configuration and ensures you get all related files automatically.

## Quick Comparison

### Before (Path-Based)
```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main

include: |
  .rhiza/make.d/01-test.mk
  .rhiza/requirements/tests.txt
  pytest.ini
  tests/**
  .github/workflows/rhiza_ci.yml
  .github/workflows/rhiza_benchmarks.yml
  docker/Dockerfile
  .rhiza/make.d/07-docker.mk
  .github/workflows/rhiza_docker.yml
  book/marimo/**
  .rhiza/make.d/03-marimo.mk
  .github/workflows/rhiza_marimo.yml
```

### After (Template-Based)
```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main

templates:
  - tests
  - docker
  - marimo
```

## Migration Steps

### Step 1: Review Available Templates

See which template bundles are available:

```bash
# View the template bundles definition
cat .rhiza/template-bundles.yml

# Or read the documentation
cat TEMPLATE_SYSTEM_SUMMARY.md
```

Available templates:
- `tests` - Testing infrastructure
- `docker` - Docker containerization
- `marimo` - Interactive notebooks
- `book` - Documentation generation
- `devcontainer` - VS Code DevContainer
- `gitlab` - GitLab CI/CD
- `presentation` - Presentations

### Step 2: Map Your Current Includes to Templates

Review your current `.rhiza/template.yml` and identify which templates cover your included files:

| Current Include Pattern | Template Bundle |
|------------------------|-----------------|
| `pytest.ini`, `tests/**`, `.github/workflows/rhiza_ci.yml` | `tests` |
| `docker/Dockerfile`, `.rhiza/make.d/07-docker.mk` | `docker` |
| `book/marimo/**`, `.rhiza/make.d/03-marimo.mk` | `marimo` |
| `.rhiza/make.d/02-book.mk`, `.github/workflows/rhiza_book.yml` | `book` |
| `.devcontainer/**` | `devcontainer` |
| `.gitlab-ci.yml`, `.gitlab/**` | `gitlab` |

### Step 3: Update Your Configuration

Edit `.rhiza/template.yml`:

```yaml
repository: Jebel-Quant/rhiza
ref: main

# New template-based approach
templates:
  - tests
  - docker
  - marimo

# Optional: Keep path-based excludes if needed
exclude: |
  .rhiza/scripts/customisations/*
```

### Step 4: Test the Migration

Run materialize to see what would be synced:

```bash
uvx rhiza materialize --dry-run
```

Or simply materialize and review the changes:

```bash
uvx rhiza materialize
git status
git diff
```

### Step 5: Commit the Changes

If everything looks good, commit your updated configuration:

```bash
git add .rhiza/template.yml
git commit -m "chore: migrate to template-based configuration"
```

## Hybrid Approach

You can use **both** templates and path-based includes/excludes together:

```yaml
repository: Jebel-Quant/rhiza
ref: main

# Use templates for common bundles
templates:
  - tests
  - docker

# Add specific files not covered by templates
include: |
  custom/special-file.yml

# Exclude specific files from templates
exclude: |
  tests/specific-test-to-skip.py
  .rhiza/scripts/customisations/*
```

This is useful when:
- You need additional files not in any template
- You want to exclude specific files from a template bundle

## Template Dependencies

Some templates automatically include others:

- **`book`** → automatically includes `tests` (required dependency)
- **`book`** → works better with `marimo` (recommended)

Example:
```yaml
templates:
  - book  # Automatically includes tests
  - marimo  # Recommended for book
```

## Common Migration Scenarios

### Scenario 1: Minimal Testing Project

**Before:**
```yaml
include: |
  pytest.ini
  tests/**
  .github/workflows/rhiza_ci.yml
```

**After:**
```yaml
templates:
  - tests
```

### Scenario 2: Docker Service

**Before:**
```yaml
include: |
  docker/Dockerfile
  .rhiza/make.d/07-docker.mk
  pytest.ini
  tests/**
```

**After:**
```yaml
templates:
  - tests
  - docker
```

### Scenario 3: Data Science Project

**Before:**
```yaml
include: |
  pytest.ini
  tests/**
  book/marimo/**
  .rhiza/make.d/02-book.mk
  .rhiza/make.d/03-marimo.mk
```

**After:**
```yaml
templates:
  - book  # Auto-includes tests
  - marimo
```

### Scenario 4: Full-Featured Project

**Before:**
```yaml
include: |
  pytest.ini
  tests/**
  docker/**
  book/**
  .devcontainer/**
  .rhiza/make.d/*.mk
  .github/workflows/*.yml
```

**After:**
```yaml
templates:
  - tests
  - docker
  - marimo
  - book
  - devcontainer
```

## Troubleshooting

### "Template not found" error

Make sure you're using a version of rhiza-cli that supports template bundles:

```bash
uvx rhiza --version
# Template bundle support planned for rhiza-cli v0.9.0+
```

**Note**: Template bundle support in rhiza-cli is currently in development. This migration guide assumes rhiza-cli has been updated to support the `templates:` field. Check the rhiza-cli release notes for availability.

### Missing files after migration

Check if you had custom includes that aren't covered by templates. You can add them:

```yaml
templates:
  - tests
  - docker

include: |
  custom/my-file.yml
```

### Too many files synced

Use excludes to skip specific files:

```yaml
templates:
  - tests

exclude: |
  tests/integration/**  # Skip integration tests
```

## Backward Compatibility

The template-based approach is **fully backward compatible**:

- Old path-based configurations continue to work
- You can migrate gradually
- Templates and path-based includes can be mixed

No action is required to maintain existing configurations.

## Getting Help

- See [TEMPLATE_SYSTEM_SUMMARY.md](TEMPLATE_SYSTEM_SUMMARY.md) for complete template documentation
- See [TEMPLATE_BUNDLES_DESIGN.md](TEMPLATE_BUNDLES_DESIGN.md) for technical details
- View [.rhiza/template-bundles.yml](.rhiza/template-bundles.yml) for the complete bundle definitions

## Next Steps

After migrating:

1. **Test your project** - Run tests and builds to ensure everything works
2. **Update documentation** - If you have docs mentioning template.yml, update them
3. **Share with team** - Let your team know about the simpler configuration
4. **Enable auto-sync** - Set up the SYNC workflow for automatic template updates
