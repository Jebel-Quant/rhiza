# Advanced Usage Patterns

This document covers advanced usage patterns for Rhiza, including monorepo support and complex customization scenarios.

---

## Monorepo Patterns

Rhiza can be adapted to work in monorepo contexts. This section describes recommended patterns and considerations.

### Architecture Options

#### Option A: Root-Level Template (Recommended)

Use a single `.rhiza/template.yml` at the monorepo root with shared configuration:

```
monorepo/
├── .rhiza/
│   ├── template.yml          # Single source of truth
│   ├── rhiza.mk              # Core Makefile (synced)
│   └── make.d/
│       └── 50-monorepo.mk    # Monorepo coordination tasks
├── pyproject.toml            # Root project metadata (optional)
├── Makefile                  # Entry point
├── packages/
│   ├── package-a/
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   └── tests/
│   └── package-b/
│       ├── pyproject.toml
│       ├── src/
│       └── tests/
└── shared/
    └── common-lib/
```

**Pros:**
- Single template synchronization point
- Unified CI/CD workflows
- Consistent tooling across all packages
- Simpler maintenance

**Cons:**
- All packages share the same configuration
- Less flexibility for package-specific workflows

#### Option B: Hybrid Approach

Combine root-level Rhiza with package-specific customizations:

```
monorepo/
├── .rhiza/template.yml       # Shared infrastructure
├── Makefile                  # Root coordination
├── packages/
│   ├── package-a/
│   │   ├── Makefile          # Package-specific (includes root)
│   │   └── local.mk          # Package overrides
│   └── package-b/
│       ├── Makefile
│       └── local.mk
```

---

### Monorepo Makefile Extensions

Create `.rhiza/make.d/50-monorepo.mk` for package coordination:

```makefile
##@ Monorepo Tasks

PACKAGES := $(wildcard packages/*)

.PHONY: test-all sync-all install-all lint-all

test-all: ## Run tests across all packages
	@for pkg in $(PACKAGES); do \
		if [ -f "$$pkg/Makefile" ]; then \
			echo "Testing $$pkg..."; \
			$(MAKE) -C "$$pkg" test || exit 1; \
		fi; \
	done

install-all: ## Install all packages in editable mode
	@for pkg in $(PACKAGES); do \
		if [ -f "$$pkg/pyproject.toml" ]; then \
			echo "Installing $$pkg..."; \
			uv pip install -e "$$pkg"; \
		fi; \
	done

lint-all: ## Lint all packages
	@for pkg in $(PACKAGES); do \
		if [ -f "$$pkg/pyproject.toml" ]; then \
			echo "Linting $$pkg..."; \
			uv run ruff check "$$pkg/src"; \
		fi; \
	done

validate-all: ## Validate all packages
	@for pkg in $(PACKAGES); do \
		echo "Validating $$pkg..."; \
		$(MAKE) -C "$$pkg" validate 2>/dev/null || true; \
	done
```

### Using Hooks for Monorepo Setup

Leverage hooks to coordinate package installation:

```makefile
# .rhiza/make.d/90-hooks.mk

post-install::
	@echo "Installing monorepo packages in editable mode..."
	@for pkg in packages/*/; do \
		if [ -f "$$pkg/pyproject.toml" ]; then \
			echo "  → $$pkg"; \
			uv pip install -e "$$pkg" --quiet; \
		fi; \
	done

post-sync::
	@echo "Propagating sync to packages..."
	@for pkg in packages/*/; do \
		if [ -f "$$pkg/.rhiza/template.yml" ]; then \
			$(MAKE) -C "$$pkg" sync; \
		fi; \
	done
```

---

### CI/CD for Monorepos

#### Dynamic Package Matrix

Modify CI workflow to discover and test packages dynamically:

```yaml
# .github/workflows/rhiza_ci.yml (customized)
jobs:
  discover:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.find.outputs.packages }}
    steps:
      - uses: actions/checkout@v6
      - id: find
        run: |
          PACKAGES=$(find packages -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | jq -R -s -c 'split("\n")[:-1]')
          echo "packages=$PACKAGES" >> $GITHUB_OUTPUT

  test:
    needs: discover
    strategy:
      matrix:
        package: ${{ fromJson(needs.discover.outputs.packages) }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
      - run: |
          cd packages/${{ matrix.package }}
          make test
```

#### Selective Testing

Only test packages that changed:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.filter.outputs.changes }}
    steps:
      - uses: actions/checkout@v6
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            package-a:
              - 'packages/package-a/**'
            package-b:
              - 'packages/package-b/**'
```

---

### uv Workspaces Integration

For Python 3.11+ projects, leverage uv workspaces for unified dependency management:

```toml
# pyproject.toml (root)
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
package-a = { workspace = true }
package-b = { workspace = true }
```

This allows:
- Shared lock file (`uv.lock`) across all packages
- Cross-package imports during development
- Unified dependency resolution

---

### Package-Specific Makefiles

Each package can have its own Makefile that inherits from root:

```makefile
# packages/package-a/Makefile

# Inherit root configuration
ROOT_DIR := ../..
include $(ROOT_DIR)/.rhiza/rhiza.mk

# Package-specific overrides
PACKAGE_NAME := package-a
SRC_DIR := src/$(PACKAGE_NAME)

# Override test target for this package
test:
	@uv run pytest tests/ -v

# Package-specific targets
.PHONY: build-docs
build-docs: ## Build package documentation
	@uv run pdoc $(SRC_DIR) -o docs/api
```

---

### Template Configuration for Monorepos

Customize `.rhiza/template.yml` to exclude package-specific files:

```yaml
repository: YourOrg/rhiza-template
ref: main

include: |
  .github/workflows/*.yml
  .pre-commit-config.yaml
  ruff.toml
  pytest.ini
  .rhiza/rhiza.mk

exclude: |
  # Protect package-specific configurations
  packages/*/pyproject.toml
  packages/*/Makefile
  packages/*/.rhiza/*

  # Protect monorepo customizations
  .rhiza/make.d/*
  .github/workflows/custom_*.yml
```

---

### Versioning Strategies

#### Independent Versioning

Each package maintains its own version:

```makefile
# .rhiza/make.d/50-monorepo.mk

bump-package: ## Bump version for a specific package (PACKAGE=name)
ifndef PACKAGE
	$(error PACKAGE is required. Usage: make bump-package PACKAGE=package-a TYPE=patch)
endif
	@cd packages/$(PACKAGE) && $(MAKE) bump TYPE=$(TYPE)

release-package: ## Release a specific package
ifndef PACKAGE
	$(error PACKAGE is required)
endif
	@cd packages/$(PACKAGE) && $(MAKE) release
```

#### Synchronized Versioning

All packages share the same version:

```makefile
# .rhiza/make.d/50-monorepo.mk

MONOREPO_VERSION := $(shell cat VERSION)

bump-all: ## Bump version for all packages
	@echo "$(MONOREPO_VERSION)" > VERSION
	@for pkg in packages/*/; do \
		if [ -f "$$pkg/pyproject.toml" ]; then \
			cd "$$pkg" && uv version $(MONOREPO_VERSION); \
		fi; \
	done

release-all: ## Release all packages with same version
	@for pkg in packages/*/; do \
		if [ -f "$$pkg/pyproject.toml" ]; then \
			echo "Releasing $$pkg @ $(MONOREPO_VERSION)"; \
			cd "$$pkg" && $(MAKE) release; \
		fi; \
	done
```

---

### Best Practices

1. **Start simple**: Begin with root-level Rhiza and add complexity as needed
2. **Use hooks**: Prefer hooks over modifying synced files
3. **Leverage uv workspaces**: For Python projects, uv workspaces simplify dependency management
4. **Selective CI**: Only test changed packages to reduce CI time
5. **Consistent tooling**: Keep ruff.toml, pytest.ini at root level for consistency
6. **Document conventions**: Create a CONTRIBUTING.md explaining monorepo workflows

---

## Custom Template Repositories

### Forking Rhiza for Your Organization

1. Fork `Jebel-Quant/rhiza` to your organization
2. Customize workflows, configs, and scripts
3. Update projects to point to your fork:

```yaml
# .rhiza/template.yml
repository: YourOrg/rhiza-fork
ref: main
```

### Template Layering

Create organization-specific templates that extend Rhiza:

```
your-org/rhiza-base (fork of Jebel-Quant/rhiza)
├── your-org/rhiza-ml (ML-specific extensions)
├── your-org/rhiza-api (API project template)
└── your-org/rhiza-lib (Library template)
```

Each specialized template can:
- Add domain-specific workflows
- Include additional Makefile targets
- Pre-configure relevant dependencies

---

## Troubleshooting

### Sync Conflicts

When template sync conflicts with local changes:

1. Review the sync PR carefully
2. Use `exclude` patterns for files that should never be overwritten
3. Use hooks instead of modifying synced files directly

### Package Discovery Issues

If package discovery fails:

```bash
# Debug package discovery
find packages -maxdepth 1 -mindepth 1 -type d

# Verify Makefile existence
for pkg in packages/*/; do
  echo "$pkg: $(test -f "${pkg}Makefile" && echo 'has Makefile' || echo 'no Makefile')"
done
```

### Dependency Conflicts

For cross-package dependency issues:

```bash
# Check for conflicts
uv pip check

# Regenerate lock file
uv lock --upgrade

# Install with verbose output
uv sync -v
```
