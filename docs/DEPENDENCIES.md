# Dependencies

This document explains the purpose of each dependency in the Rhiza project.

---

## Runtime Dependencies

```toml
dependencies = []
```

Rhiza has **zero runtime dependencies**. It's a template repository, not a library to be imported.

---

## Development Dependencies

### pyproject.toml [dependency-groups.dev]

These dependencies are installed via `uv sync` for interactive development:

| Package | Version | Purpose |
|---------|---------|---------|
| `marimo` | >=0.18.0 | Interactive notebook environment for documentation and data exploration |
| `numpy` | >=2.4.0 | Numerical computing library, used in Marimo notebook examples |
| `plotly` | >=6.5.0 | Interactive visualization library for Marimo notebooks |
| `pandas` | >=2.3.3 | Data manipulation library for Marimo notebook examples |

---

## Requirements Files

Dependencies in `.rhiza/requirements/` are installed via `uv pip install -r` during `make install`.

### .rhiza/requirements/tools.txt

Development tools for local workflows:

| Package | Version | Purpose |
|---------|---------|---------|
| `pre-commit` | ==4.5.1 | Git hooks framework for code quality checks |
| `python-dotenv` | ==1.2.1 | Load environment variables from .env files |
| `typer` | ==0.21.1 | CLI framework (temporary, until rhiza-tools is complete) |

### .rhiza/requirements/tests.txt

Testing framework and plugins:

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=8.0 | Testing framework |
| `pytest-cov` | >=6.0 | Coverage reporting plugin |
| `pytest-html` | >=4.0 | HTML test report generation |
| `pytest-mock` | >=3.0 | Mock object fixtures |
| `pytest-benchmark` | >=5.2.3 | Performance benchmarking plugin |
| `pygal` | >=3.1.0 | SVG charting for benchmark reports |

### .rhiza/requirements/docs.txt

Documentation generation:

| Package | Version | Purpose |
|---------|---------|---------|
| `pdoc` | >=16.0.0 | API documentation generator |

### .rhiza/requirements/marimo.txt

Marimo-specific dependencies (may overlap with pyproject.toml):

| Package | Version | Purpose |
|---------|---------|---------|
| `marimo` | >=0.18.0 | Interactive notebook environment |

---

## External Tools (via uvx)

These tools are run in ephemeral environments and don't need installation:

| Tool | Purpose |
|------|---------|
| `ruff` | Linting and formatting |
| `deptry` | Dependency hygiene checking |
| `hatch` | Package building |
| `rhiza` | Template synchronization CLI |
| `syft` | SBOM generation |

---

## CI/CD Tool Versions

Pinned versions used in GitHub Actions workflows:

| Tool | Version | File |
|------|---------|------|
| `uv` | 0.9.26 | All workflows |
| `actions/checkout` | v6 | All workflows |
| `astral-sh/setup-uv` | v7 | All workflows |

---

## Version Constraints Philosophy

### Loose Constraints (>=)

Used for:
- Development dependencies where compatibility is broad
- Dependencies where we want automatic minor/patch updates

Example: `pytest>=8.0`

### Pinned Versions (==)

Used for:
- Tools where exact reproducibility matters
- Dependencies with known breaking changes in minor versions

Example: `pre-commit==4.5.1`

### Upper Bounds (<)

Generally avoided because:
- They cause unnecessary dependency conflicts
- Renovate handles updates automatically
- Tests catch compatibility issues

Exception: Consider adding for dependencies with unstable APIs.

---

## Adding New Dependencies

### To pyproject.toml

```bash
# Add runtime dependency (avoid if possible)
uv add package-name

# Add dev dependency
uv add --group dev package-name
```

### To requirements files

1. Add to appropriate `.rhiza/requirements/*.txt` file
2. Include version constraint
3. Add comment explaining purpose
4. Update this documentation

### Verification

After adding dependencies:

```bash
make install          # Install new dependencies
make deptry           # Verify no missing/unused imports
make test             # Ensure tests pass
```

---

## Dependency Updates

### Automated (Renovate)

Renovate creates PRs for dependency updates:
- **Schedule**: Tuesdays before 10am (Asia/Dubai)
- **Auto-merge**: Patch updates for all dependencies
- **Auto-merge**: Minor updates for dev dependencies and GitHub Actions
- **Dashboard**: See open update PRs in GitHub

### CI Dry-Run Checks

The `rhiza_deps-check.yml` workflow runs weekly (Mondays) to:
- List outdated packages
- Perform dry-run lock upgrades
- Detect resolution conflicts before Renovate runs
- Validate lock file integrity

### Manual

```bash
# Check for updates
uv pip list --outdated

# Update lock file
uv lock --upgrade

# Update specific package
uv lock --upgrade-package pytest

# Dry-run upgrade (see what would change)
uv lock --upgrade --dry-run
```

---

## Security Considerations

1. **Lock files**: `uv.lock` ensures reproducible builds
2. **Renovate**: Automated security updates
3. **Deptry**: Detects unused dependencies (reduce attack surface)
4. **SBOM**: Generated at release for supply chain transparency
