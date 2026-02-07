# Migration Guide

Step-by-step guide for adding Rhiza to existing Python projects.

---

## Overview

Migrating an existing project to Rhiza allows you to benefit from:

- :material-sync: Continuous template synchronization
- :material-test-tube: Pre-configured testing infrastructure  
- :material-rocket-launch: GitHub Actions CI/CD workflows
- :material-cog: Standardized development tooling
- :material-book-open-variant: Documentation generation

This guide walks through the migration process, handling conflicts, and best practices.

---

## Pre-Migration Checklist

Before starting, ensure your project meets these requirements:

- [ ] **Python 3.11+** — Rhiza requires Python 3.11 or newer
- [ ] **Git repository** — Project must be version controlled
- [ ] **Clean working tree** — Commit or stash all changes
- [ ] **Backup** — Create a backup branch: `git checkout -b pre-rhiza-backup`
- [ ] **Review dependencies** — Understand your current dependencies
- [ ] **Test suite** — Have a working test suite (or plan to create one)

---

## Migration Strategies

Choose the strategy that fits your project:

### Strategy 1: Gradual Integration (Recommended)

Integrate Rhiza incrementally, adopting one feature at a time.

**Best for:**
- Large existing codebases
- Projects with extensive customizations
- Teams that need time to adapt

**Timeline:** 1-2 weeks

---

### Strategy 2: Full Migration

Replace your entire configuration with Rhiza templates.

**Best for:**
- Newer projects
- Projects with minimal customization
- Starting fresh after tech debt cleanup

**Timeline:** 1-2 days

---

### Strategy 3: Selective Adoption

Cherry-pick specific Rhiza features without full integration.

**Best for:**
- Projects with strong existing conventions
- Wanting specific features (e.g., just CI workflows)
- Testing Rhiza before full commitment

**Timeline:** 1 day

---

## Step-by-Step Migration

### Step 1: Initialize Rhiza

Navigate to your project and initialize Rhiza configuration:

```bash
cd /path/to/your/project
uvx rhiza init
```

This creates:
- `.rhiza/` directory with configuration
- `.rhiza/template.yml` with default settings

**Output:**
```
✓ Created .rhiza/template.yml
✓ Initialized Rhiza configuration
```

---

### Step 2: Review Template Configuration

Edit `.rhiza/template.yml` to select which templates to sync:

```yaml
repository: Jebel-Quant/rhiza
ref: main

include: |
  .github/workflows/*.yml
  .pre-commit-config.yaml
  ruff.toml
  pytest.ini
  Makefile

exclude: |
  .rhiza/make.d/90-custom.mk
  local.mk
```

**Key Decisions:**

| Template | Include if... | Skip if... |
|----------|---------------|------------|
| `.github/workflows/` | You want GitHub Actions CI/CD | You use GitLab CI or other CI |
| `Makefile` | You want standardized make targets | You have custom build system |
| `ruff.toml` | You want consistent linting | You use different linters |
| `.pre-commit-config.yaml` | You want pre-commit hooks | You have existing hooks |
| `pytest.ini` | You use pytest | You use different test framework |

---

### Step 3: Preview Changes

Before applying templates, preview what will change:

```bash
uvx rhiza materialize --dry-run
```

**Example output:**
```
Preview of changes:

  ADD    .github/workflows/rhiza_ci.yml
  ADD    .github/workflows/rhiza_release.yml
  UPDATE Makefile
  UPDATE pyproject.toml
  SKIP   local.mk (excluded)
  
Changes would affect 15 files.
Run without --dry-run to apply.
```

**Review each change carefully!**

---

### Step 4: Handle Existing Files

Rhiza will detect conflicts with existing files. Choose your strategy:

#### Option A: Interactive Mode (Recommended)

Rhiza prompts for each conflict:

```bash
uvx rhiza materialize
```

**Prompt example:**
```
Conflict: pyproject.toml exists

Options:
  [k] Keep local version
  [r] Replace with template
  [m] Merge manually  
  [d] Show diff
  [a] Abort

Your choice:
```

**Recommendations:**

| File | Recommended Action |
|------|-------------------|
| `pyproject.toml` | Merge manually — preserve your metadata |
| `Makefile` | Merge manually — preserve custom targets |
| `.gitignore` | Merge manually — combine both |
| `pytest.ini` | Replace — adopt Rhiza defaults |
| `ruff.toml` | Replace — adopt Rhiza defaults |

#### Option B: Keep Existing

Preserve all existing files and only add new ones:

```bash
uvx rhiza materialize --keep-existing
```

Then manually merge desired changes:

```bash
git diff .rhiza/cache/Makefile Makefile
```

#### Option C: Force Replace

Replace all files without prompting (⚠️ Use with caution):

```bash
uvx rhiza materialize --force
```

---

### Step 5: Merge Critical Files

#### Merging pyproject.toml

**Your existing file:**
```toml
[project]
name = "my-project"
version = "1.0.0"
description = "My awesome project"
dependencies = ["requests", "pandas"]
```

**Rhiza template:**
```toml
[project]
requires-python = ">=3.11"

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Merged result:**
```toml
[project]
name = "my-project"
version = "1.0.0"
description = "My awesome project"
requires-python = ">=3.11"
dependencies = ["requests", "pandas"]

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

#### Merging Makefile

Add Rhiza's `include` statement to your existing Makefile:

**Your existing Makefile:**
```makefile
.PHONY: test
test:
	pytest tests/

.PHONY: deploy
deploy:
	./scripts/deploy.sh
```

**After adding Rhiza:**
```makefile
include .rhiza/rhiza.mk

# Your custom targets
.PHONY: deploy
deploy:
	./scripts/deploy.sh
```

This preserves your custom targets while gaining Rhiza's 40+ targets.

---

### Step 6: Update Dependencies

Sync your environment with the new configuration:

```bash
make install
```

This:
1. Installs `uv` if not present
2. Creates/updates `.venv`
3. Installs all dependencies from `pyproject.toml`
4. Sets up pre-commit hooks

**Troubleshooting:**

If `make install` fails:

```bash
# Check uv is accessible
which uv || make install-uv

# Manually sync
uv sync

# Verify
uv pip list
```

---

### Step 7: Migrate Tests

If you have existing tests, ensure they work with Rhiza's pytest configuration:

#### Update Test Structure

Rhiza expects:
```
tests/
├── conftest.py
├── test_mymodule/
│   ├── test_feature1.py
│   └── test_feature2.py
└── integration/
    └── test_integration.py
```

#### Run Tests

```bash
make test
```

If tests fail, check:

1. **Import paths** — Ensure `src/` is on `PYTHONPATH`
2. **Fixtures** — Move to `conftest.py`
3. **Coverage** — Update coverage settings in `pyproject.toml`

---

### Step 8: Configure CI/CD

If you have existing CI, decide how to handle it:

#### Option A: Replace with Rhiza Workflows

```bash
# Remove old CI config
rm -rf .github/workflows/*.yml  # or .gitlab-ci.yml

# Materialize Rhiza workflows
uvx rhiza materialize --force .github/workflows/
```

#### Option B: Keep Existing CI

Exclude Rhiza workflows:

```yaml
# .rhiza/template.yml
exclude: |
  .github/workflows/*
```

#### Option C: Hybrid Approach

Use Rhiza workflows for testing, keep custom workflows for deployment:

```yaml
# .rhiza/template.yml
include: |
  .github/workflows/rhiza_ci.yml
  .github/workflows/rhiza_security.yml

exclude: |
  .github/workflows/deploy.yml  # Keep your custom workflow
```

---

### Step 9: Commit Changes

Review and commit the migration:

```bash
# Review all changes
git status
git diff

# Stage changes
git add .

# Commit
git commit -m "chore: migrate to Rhiza template system

- Initialize Rhiza configuration
- Integrate CI/CD workflows
- Adopt standardized linting and testing
- Preserve existing custom configuration"

# Push
git push origin main
```

---

### Step 10: Verify Migration

Ensure everything works:

```bash
# Format code
make fmt

# Run tests
make test

# Check dependencies
make deptry

# Validate configuration
make validate

# Build documentation (if applicable)
make book
```

**Expected output:**
```
✓ Code formatted
✓ All tests passed
✓ No dependency issues
✓ Configuration valid
✓ Documentation built
```

---

## Handling Common Conflicts

### Conflict: Different Linter

**Scenario:** You use `black` and `flake8`, Rhiza uses `ruff`.

**Solution:** Migrate to `ruff` (recommended):

```bash
# Remove old config
rm .flake8 pyproject.toml:[tool.black]

# Install ruff via Rhiza
make install

# Format code
make fmt
```

Or keep your linters:

```yaml
# .rhiza/template.yml
exclude: |
  ruff.toml
  pyproject.toml:[tool.ruff]
```

---

### Conflict: Custom Make Targets

**Scenario:** You have a `Makefile` with custom targets.

**Solution:** Create `local.mk` for custom targets:

**local.mk:**
```makefile
.PHONY: custom-deploy
custom-deploy: ## Deploy to production
	./scripts/deploy.sh

.PHONY: custom-train
custom-train: ## Train ML model
	python scripts/train.py
```

**Makefile:**
```makefile
include .rhiza/rhiza.mk
-include local.mk  # Optional custom targets
```

Add to exclude list:

```yaml
# .rhiza/template.yml
exclude: |
  local.mk
```

---

### Conflict: Existing CI Matrix

**Scenario:** You test on Python 3.9, 3.10; Rhiza uses 3.11+.

**Solution:** Update `pyproject.toml`:

```toml
[project]
requires-python = ">=3.9"

classifiers = [
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
```

The CI matrix auto-generates from these classifiers.

---

### Conflict: Private Packages

**Scenario:** You use private packages from GitHub or custom index.

**Solution:** Configure authentication secrets:

1. **For GitHub packages:**
   ```bash
   # Set GH_PAT secret in repository settings
   # See: docs/token-setup.md
   ```

2. **For custom index:**
   ```yaml
   # .rhiza/template.yml or repository secrets
   UV_EXTRA_INDEX_URL: https://username:password@custom.pypi.org/simple
   ```

See [private-packages.md](private-packages.md) for details.

---

## Customizing After Migration

### Add Custom Pre-commit Hooks

Edit `.pre-commit-config.yaml`:

```yaml
repos:
  # Rhiza's hooks
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.7
    hooks:
      - id: ruff
      - id: ruff-format
  
  # Your custom hooks
  - repo: local
    hooks:
      - id: custom-check
        name: Custom validation
        entry: ./scripts/validate.sh
        language: script
```

---

### Add Custom Makefile Targets

Create `.rhiza/make.d/50-custom.mk`:

```makefile
##@ Custom Tasks

.PHONY: analyze
analyze: ## Run custom analysis
	@echo "Running analysis..."
	@uv run python scripts/analyze.py

.PHONY: backup
backup: ## Backup data
	@./scripts/backup.sh
```

These appear in `make help`.

---

### Add Custom CI Workflow

Create `.github/workflows/custom.yml`:

```yaml
name: Custom Workflow

on:
  push:
    branches: [ main ]

jobs:
  custom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - run: make custom-target
```

Exclude from template sync:

```yaml
# .rhiza/template.yml
exclude: |
  .github/workflows/custom.yml
```

---

## Rollback Plan

If migration causes issues, you can rollback:

### Full Rollback

```bash
# Return to pre-migration state
git reset --hard pre-rhiza-backup

# Or revert the migration commit
git revert <commit-hash>
```

### Partial Rollback

```bash
# Remove Rhiza
rm -rf .rhiza/

# Restore specific files
git checkout HEAD~1 -- Makefile
git checkout HEAD~1 -- pyproject.toml

# Remove Rhiza from template.yml
rm .rhiza/template.yml
```

---

## Migration Checklist

Use this checklist to track your migration progress:

- [ ] **Pre-migration**
  - [ ] Python 3.11+ verified
  - [ ] Clean working tree
  - [ ] Backup branch created
  - [ ] Existing tests pass

- [ ] **Initialization**
  - [ ] `uvx rhiza init` executed
  - [ ] `.rhiza/template.yml` configured
  - [ ] Preview changes reviewed

- [ ] **File Migration**
  - [ ] `pyproject.toml` merged
  - [ ] `Makefile` integrated
  - [ ] `.gitignore` merged
  - [ ] CI workflows added

- [ ] **Environment**
  - [ ] `make install` successful
  - [ ] Dependencies installed
  - [ ] Pre-commit hooks set up

- [ ] **Testing**
  - [ ] Tests migrated/updated
  - [ ] `make test` passes
  - [ ] Coverage configured

- [ ] **CI/CD**
  - [ ] Workflows triggered
  - [ ] All checks passing
  - [ ] Secrets configured (if needed)

- [ ] **Documentation**
  - [ ] README updated
  - [ ] Migration documented
  - [ ] Team notified

- [ ] **Verification**
  - [ ] `make fmt` works
  - [ ] `make test` passes
  - [ ] `make validate` passes
  - [ ] CI pipeline green

---

## Post-Migration

### Enable Template Sync

Keep your project up-to-date with upstream Rhiza:

```bash
# Manual sync
make sync

# Or enable automatic weekly sync
# (already configured in .github/workflows/rhiza_sync.yml)
```

### Configure Secrets

If using private packages or custom features:

1. Set `GH_PAT` for private GitHub packages
2. Set `PAT_TOKEN` for workflow modifications
3. See [token-setup.md](token-setup.md)

### Update Team

Communicate changes to your team:

- New `make` targets available
- Pre-commit hooks now active
- CI/CD workflows updated
- Documentation generated automatically

---

## FAQ

### Do I need to migrate everything at once?

No! Use Strategy 1 (Gradual Integration) to adopt Rhiza incrementally.

### Will migration break my existing code?

No. Rhiza only adds configuration and tooling. Your source code remains unchanged.

### Can I keep my existing CI/CD?

Yes. Exclude `.github/workflows/` from `.rhiza/template.yml`.

### What if I want to customize Rhiza templates?

Use hooks in `.rhiza/make.d/` and exclude customized files from syncing.

### Can I migrate back?

Yes. Create a backup branch before migration for easy rollback.

### Do I need to use uv?

Rhiza strongly recommends `uv` for its speed and reliability, but technically you can use `pip` if needed.

---

## Troubleshooting

### Make install fails

**Solution:**
```bash
# Install uv manually
curl -LsSf https://astral.sh/uv/install.sh | sh

# Retry
make install
```

### Tests fail after migration

**Solution:**
1. Check import paths
2. Verify dependencies installed: `uv pip list`
3. Update `PYTHONPATH` if needed: `export PYTHONPATH=src:$PYTHONPATH`

### CI workflow fails

**Solution:**
1. Check Python version compatibility
2. Verify secrets are configured
3. Review workflow logs in GitHub Actions

### Conflicts during materialize

**Solution:**
```bash
# Preview changes
uvx rhiza materialize --dry-run

# Keep existing and merge manually
uvx rhiza materialize --keep-existing
git diff .rhiza/cache/<file> <file>
```

---

## Next Steps

After successful migration:

1. **Read [WORKFLOWS.md](WORKFLOWS.md)** — Learn day-to-day development workflows
2. **Read [CUSTOMIZATION.md](CUSTOMIZATION.md)** — Customize Rhiza for your needs
3. **Set up [token-setup.md](token-setup.md)** — Configure secrets for private packages
4. **Enable [ci-cd.md](ci-cd.md)** — Understand your new CI/CD pipelines
5. **Configure [RELEASING.md](RELEASING.md)** — Set up release automation

---

## Related Documentation

- [Quick Start](getting-started/quickstart.md) — New project setup
- [First Sync](getting-started/first-sync.md) — Understanding template sync
- [Customization](CUSTOMIZATION.md) — Advanced customization
- [CI/CD](ci-cd.md) — Workflow documentation
- [FAQ](faq.md) — Frequently asked questions

---

## Getting Help

If you encounter issues during migration:

1. **Check logs:** Review `make` output and CI logs
2. **Validate config:** Run `make validate`
3. **Search issues:** Check [GitHub Issues](https://github.com/jebel-quant/rhiza/issues)
4. **Ask for help:** Open a new issue with details

Include in your issue:
- Migration strategy used
- Error messages
- Output of `make validate`
- Python version: `python --version`
- uv version: `uv --version`
