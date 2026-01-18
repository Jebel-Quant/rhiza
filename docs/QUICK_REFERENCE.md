# Quick Reference

Essential commands for working with Rhiza projects.

---

## Top 10 Commands

| # | Command | What it does |
|---|---------|--------------|
| 1 | `make install` | Set up environment (installs uv, creates .venv, installs deps) |
| 2 | `make test` | Run test suite with pytest |
| 3 | `make fmt` | Format code and run linting (ruff + pre-commit) |
| 4 | `make help` | Show all available targets (40+) |
| 5 | `make sync` | Pull updates from template repository |
| 6 | `make bump` | Interactively bump version (major/minor/patch) |
| 7 | `make release` | Create git tag and push to trigger release |
| 8 | `make deptry` | Check for missing/unused dependencies |
| 9 | `make clean` | Remove artifacts and prune stale branches |
| 10 | `make validate` | Check if project matches template (dry-run sync) |

---

## Daily Workflow

```bash
# Start of day
make install          # Ensure environment is up to date

# Development cycle
# ... edit code ...
make test             # Verify changes work
make fmt              # Format before commit

# Before PR
make deptry           # Check dependencies
make validate         # Ensure template compliance
```

---

## Running Tests

```bash
make test                                    # Run all tests
uv run pytest tests/path/to/test.py         # Run specific file
uv run pytest tests/path/to/test.py::func   # Run specific test
uv run pytest -k "keyword"                  # Run tests matching keyword
uv run pytest -x                            # Stop on first failure
uv run pytest --lf                          # Run last failed tests
```

---

## Version & Release

```bash
make bump             # Bump version (interactive prompt)
make release          # Create tag and push

# Manual version check
uv version --short    # Show current version
```

---

## Template Sync

```bash
make sync             # Pull updates from template
make validate         # Check for drift (no changes)

# Direct CLI
uvx rhiza materialize .   # Apply template
uvx rhiza validate .      # Validate only
```

---

## Documentation

```bash
make book             # Build documentation site
make docs             # Generate API docs (pdoc)
make marimo           # Start Marimo notebook server
```

---

## Docker

```bash
make docker-build     # Build Docker image
make docker-run       # Run container
make docker-clean     # Remove image
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Stale dependencies | `make clean && make install` |
| Formatting failures | `make fmt` (auto-fixes most issues) |
| Pre-commit hook fails | `uvx pre-commit run --all-files` |
| Template out of sync | `make sync` |
| Unknown Python version | Check `.python-version` file |

---

## Key Files

| File | Purpose |
|------|---------|
| `Makefile` | Entry point for all commands |
| `pyproject.toml` | Project config, dependencies, version |
| `.python-version` | Default Python version |
| `uv.lock` | Locked dependency versions |
| `.rhiza/template.yml` | Template sync configuration |
| `ruff.toml` | Linting and formatting rules |

---

## Environment Variables

```bash
# Set Python version (overrides .python-version)
PYTHON_VERSION=3.13 make install

# Custom virtual environment path
VENV=.venv-custom make install

# Skip PATH modification
UV_NO_MODIFY_PATH=1
```

---

## Getting Help

```bash
make help             # List all targets
cat .rhiza/make.d/README.md   # Makefile extension guide
cat docs/architecture.md      # System architecture
cat docs/glossary.md          # Term definitions
```
