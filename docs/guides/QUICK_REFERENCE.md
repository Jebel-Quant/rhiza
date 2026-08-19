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
| `make release-status` | Show release workflow status and latest release |

> Releasing is driven by the rhiza-claude `/release` command, which derives the next version, bumps `pyproject.toml`, regenerates `CHANGELOG.md`, and creates the git tag locally. Pushing that tag triggers the release workflow.

## Code Quality

| Command | Description |
|---------|-------------|
| `make fmt` | Format + lint with auto-fix |
| `make deps` | Check for unused/missing dependencies |
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
Makefile              # repo-owned shim, generated once by `rhiza-task shim`
local.mk              # optional, gitignored: personal one-off targets
pyproject.toml        # [tool.rhiza-task] settings live here
.rhiza/
├── template.yml      # Sync configuration
├── semgrep.yml       # Static-analysis rules
└── .env              # optional, gitignored: developer-local settings
```

## Extending a Task

There are no hook targets. `pre-install::`/`post-install::` belonged to the synced make layer;
the CLI knows nothing about make targets. Shadow the task instead — an explicit rule beats the
shim's `%:` catch-all:

```makefile
install:
	@$(UVX) $(RHIZA_TASK) install
	@./scripts/fetch-fixtures.sh
```

That works for any task, runs in a defined order, and needs no anchor to have been declared in
advance.

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
