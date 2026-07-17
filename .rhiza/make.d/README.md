# Makefile Cookbook

This directory (`.rhiza/make.d/`) contains **template-managed build logic**. Files here are synced from the Rhiza template and should not be modified directly.

**For project-specific customizations, use your root `Makefile`** (before the `include .rhiza/rhiza.mk` line).

Use this cookbook to find copy-paste patterns for common development needs.

## 🥘 Recipes

### 1. Add a Simple Task
**Goal**: Run a script with `make train-model`.

Add to your root `Makefile`:
```makefile
##@ Machine Learning
train: ## Train the model using local data
	@echo "Training model..."
	@uv run python scripts/train.py

# Include the Rhiza API (template-managed)
include .rhiza/rhiza.mk
```

### 2. Inject Code into Standard Workflows (Hooks)
**Goal**: Apply task after `make sync`.

Add to your root `Makefile`:
```makefile
post-sync::
	@echo "Applying something..."
```
*Note: Use double-colons (`::`) for hooks to allow accumulation.*

### 3. Define Global Variables
**Goal**: Set a default timeout for all test runs.

Add to your root `Makefile` (before the include line):
```makefile
# Override default timeout (defaults to 60s)
export TEST_TIMEOUT := 120

# Include the Rhiza API (template-managed)
include .rhiza/rhiza.mk
```

### 4. Create a Private Shortcut
**Goal**: Create a command that only exists on my machine (not committed).

Create a `local.mk` in the project root:
```makefile
deploy-dev:
	@./scripts/deploy-to-my-sandbox.sh
```

### 5. Install System Dependencies
**Goal**: Ensure `graphviz` is installed for Marimo notebooks using a hook.

Add to your root `Makefile`:
```makefile
pre-install::
	@if ! command -v dot >/dev/null 2>&1; then \
		echo "Graphviz not found. Installing..."; \
		if command -v brew >/dev/null 2>&1; then \
			brew install graphviz; \
		elif command -v apt-get >/dev/null 2>&1; then \
			sudo apt-get install -y graphviz; \
		else \
			echo "Please install graphviz manually."; \
			exit 1; \
		fi \
	fi
```

---

## ℹ️ Reference

### How the modular Makefile loads

The root `Makefile` is intentionally thin — it only `include`s `.rhiza/rhiza.mk`,
whose **last line** auto-loads every fragment in this directory:

```makefile
# In .rhiza/rhiza.mk (last line)
-include .rhiza/make.d/*.mk
```

Key consequences:

- **Alphabetical load order.** `make` expands the `*.mk` glob alphabetically, so
  fragments are included in filename order (`book.mk`, `bootstrap.mk`,
  `bundles.mk`, …). Don't rely on a later fragment overriding an earlier one — a
  duplicate **single-colon** target across two fragments is a silent
  last-definition-wins bug, and CI fails it (see
  `tests/utils/test_make_structure.py`). Use a hook instead (below).
- **Drop-in extension.** Adding a feature is just dropping a new `.mk` file here;
  there is no include list to maintain.
- **`local.mk`** (project root, not committed) is auto-loaded the same way for
  developer-only shortcuts.

### The hook contract (double-colon targets)

Lifecycle hooks use GNU Make **double-colon** (`::`) rules. Unlike single-colon
targets, a double-colon target **may be defined any number of times**, and make
runs **every** definition in order. That is what lets a fragment, the root
`Makefile`, and a downstream project all attach behaviour to the same lifecycle
point without colliding:

```makefile
# .rhiza/rhiza.mk ships an empty default so the hook always exists:
post-sync:: ; @:

# Your root Makefile adds to it (this does NOT replace the default):
post-sync::
	@echo "Regenerating lockfile after sync..."
	@uv lock
```

Both recipes run on `make sync`. Rules of the road:

- Always use `::` for hooks — a single `:` would trigger the duplicate-target
  gate and silently drop one definition.
- Where to put what:
  - **Project-specific hooks / custom targets** → your root `Makefile`, *above*
    the `include .rhiza/rhiza.mk` line (committed, shared with the team).
  - **Developer-local, throwaway shortcuts** → `local.mk` (not committed).
  - **Never** edit files in `.rhiza/make.d/` directly — they are overwritten on
    the next template sync.

### File Organization
- **`.rhiza/make.d/`**: Template-managed files (do not edit)
- **Root `Makefile`**: Project-specific customizations (variables, hooks, custom targets)
- **`local.mk`**: Developer-local shortcuts (not committed)

### Makefile Files in `.rhiza/make.d/`

| File | Purpose |
|------|---------|
| `book.mk` | Documentation book generation |
| `bootstrap.mk` | Installation and environment setup |
| `bundles.mk` | Bundle inspection (`make explain-bundles`) |
| `custom-env.mk` | Example environment customizations |
| `custom-task.mk` | Example custom tasks |
| `docker.mk` | Docker build and run targets |
| `doctor.mk` | Environment diagnostics (`make doctor`) |
| `github.mk` | GitHub CLI integrations |
| `lfs.mk` | Git LFS management |
| `marimo.mk` | Marimo notebook support |
| `paper.mk` | LaTeX paper compilation |
| `presentation.mk` | Presentation building (Marp) |
| `quality.mk` | Code quality and formatting |
| `test.mk` | Testing infrastructure |

Files prefixed with `custom-` are **examples** showing how to customize Rhiza. Don't edit them directly; instead, add your customizations to the root `Makefile`.

### Naming Conventions

**Targets**: Lowercase with hyphens, verb-noun format
- ✅ `install-uv`, `docker-build`, `view-prs`
- ❌ `installUv`, `docker_build`

**Variables**: SCREAMING_SNAKE_CASE
- ✅ `INSTALL_DIR`, `UV_BIN`, `PYTHON_VERSION`
- ❌ `installDir`, `uvBin`

**Section Headers**: Title Case with `##@`
- `##@ Bootstrap`, `##@ GitHub Helpers`

### Available Hooks
Add these to your root `Makefile` using double-colon syntax (`::`):
- `pre-install` / `post-install`: Runs around `make install`.
- `pre-sync` / `post-sync`: Runs around repository synchronization.
- `pre-validate` / `post-validate`: Runs around validation checks.
