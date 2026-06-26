# Rhiza Quick Reference Card

A concise reference for common Rhiza operations.

## Essential Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies and set up environment |
| `make test` | Run pytest with coverage |
| `make fmt` | Format and lint code with ruff |
| `make doctor` | Validate required tools and versions (start here when something is wrong) |
| `make help` | Show all available targets |

## Version & Release

| Command | Description |
|---------|-------------|
| `make release` | Bump version, create tag and push to trigger the release workflow (prompts for major/minor/patch) |
| `make bump` | Bump version only, without releasing (prompts for major/minor/patch) |
| `make bump BUMP=patch` | Bump patch version directly |
| `make bump BUMP=minor` | Bump minor version directly |
| `make bump BUMP=major` | Bump major version directly |
| `make release-status` | Show release workflow status and latest release |

## Code Quality

| Command | Description |
|---------|-------------|
| `make fmt` | Format + lint with auto-fix |
| `make deptry` | Check for unused/missing dependencies |
| `make pre-commit` | Run all pre-commit hooks |

## Template Sync

| Command | Description |
|---------|-------------|
| `make sync` | Sync templates from upstream Rhiza |
| `make validate` | Validate project structure against `.rhiza/template.yml` |

### `.rhiza/template.yml` — profile-based (recommended)

```yaml
repository: Jebel-Quant/rhiza
ref: v0.14.0

profiles:
  - github-project   # or: local, gitlab-project
```

### `.rhiza/template.yml` — bundle-based (advanced)

```yaml
repository: Jebel-Quant/rhiza
ref: v0.14.0

templates:
  - core
  - tests
  - github
  - github-tests
```

## Running Tests

```bash
# All tests
make test

# Specific file
uv run pytest tests/path/to/test.py -v

# Specific test function
uv run pytest tests/path/to/test.py::test_name -v

# With output
uv run pytest -v -s
```

## Directory Structure

```text
.rhiza/
├── rhiza.mk          # Core Makefile logic
├── make.d/           # Modular extensions (auto-loaded)
│   ├── 00-19*.mk     # Configuration
│   ├── 20-79*.mk     # Task definitions
│   └── 80-99*.mk     # Hook implementations
├── utils/            # Python utilities
└── template.yml      # Sync configuration
```

## Hook Targets

Extend these with `::` syntax in `local.mk` or `.rhiza/make.d/`:

| Hook | When it runs |
|------|--------------|
| `pre-install::` | Before dependency installation |
| `post-install::` | After dependency installation |
| `pre-sync::` | Before template sync |
| `post-sync::` | After template sync |
| `pre-validate::` | Before project validation |
| `post-validate::` | After project validation |
| `pre-release::` | Before release creation |
| `post-release::` | After release creation |
| `pre-bump::` | Before version bump |
| `post-bump::` | After version bump |

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, version — must have `[project]` (name, version, description, readme, requires-python) and `[dependency-groups]` |
| `uv.lock` | Locked dependency versions |
| `.python-version` | Default Python version — single line, e.g. `3.13` |
| `.rhiza/template.yml` | Sync configuration (repository, ref, profiles/bundles) |
| `ruff.toml` | Linter/formatter configuration |
| `local.mk` | Local Makefile customizations (not synced, auto-loaded) |

## Python Execution

Always use `uv` for Python operations:

```bash
uv run python script.py    # Run Python script
uv run pytest              # Run tests
uv build                   # Build distribution packages
```

## Version Format

- Source of truth: `version` field in `pyproject.toml`
- Git tags: `v` prefix (e.g., `v1.2.3`)
- Semantic versioning: `MAJOR.MINOR.PATCH`

## CI Workflows

| Workflow | Trigger |
|----------|---------|
| CI | Push, Pull Request |
| Release | Tag `v*` |
| Security | Schedule, Push |
| Sync | Manual |

## Common Patterns

### Add a custom make target

Add to your root `Makefile` (above the `include .rhiza/rhiza.mk` line):
```makefile
##@ Custom Tasks
my-target: ## My custom task
	@echo "Custom target"
```

### Extend a hook (root Makefile)

Add above the `include` line in your root `Makefile`:
```makefile
post-install::
	@echo "Additional setup after install"
```

### Extend a hook (local only)

Add to `local.mk` (not committed, not synced):
```makefile
post-install::
	@echo "Local developer setup"
```

### Skip CI on commit

```bash
git commit -m "docs: update readme [skip ci]"
```
