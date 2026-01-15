# Customization Guide

This guide covers advanced customization options for Rhiza-based projects.

## 🛠️ Makefile Hooks & Extensions

Rhiza uses a modular Makefile system with extension points (hooks) that let you customize workflows without modifying core files.

### Available Hooks

You can hook into standard workflows using double-colon syntax (`::`) in `.rhiza/make.d/` files:

- `pre-install / post-install` - Runs around `make install`
- `pre-sync / post-sync` - Runs around repository synchronization
- `pre-validate / post-validate` - Runs around validation checks
- `pre-release / post-release` - Runs around release process
- `pre-bump / post-bump` - Runs around version bumping

### Example: Installing System Dependencies

Create `.rhiza/make.d/20-dependencies.mk`:

```makefile
pre-install::
	@if ! command -v dot >/dev/null 2>&1; then \
		echo "Installing graphviz..."; \
		sudo apt-get update && sudo apt-get install -y graphviz; \
	fi
```

This hook runs automatically before `make install`, ensuring graphviz is available.

### Example: Post-Release Tasks

Create `.rhiza/make.d/90-hooks.mk`:

```makefile
post-release::
	@echo "Running post-release tasks..."
	@./scripts/notify-team.sh
	@./scripts/update-changelog.sh
```

This runs automatically after `make release` completes.

### Example: Custom Build Steps

Create `.rhiza/make.d/50-custom.mk`:

```makefile
post-install::
	@echo "Installing specialized dependencies..."
	@pip install some-private-lib
	
##@ Custom Tasks
train-model: ## Train the ML model
	@uv run python scripts/train.py
```

### Ordering

Files in `.rhiza/make.d/` are loaded alphabetically. Use numeric prefixes to control order:

- `00-19`: Configuration & Variables
- `20-79`: Custom Tasks & Rules
- `80-99`: Hooks & Lifecycle logic

### Excluding from Template Updates

If you add custom `.mk` files, add them to the exclude list in your `.rhiza/template.yml`:

```yaml
exclude: |
  .rhiza/make.d/20-dependencies.mk
  .rhiza/make.d/90-hooks.mk
```

## 📖 Complete Documentation

For detailed information about extending and customizing the Makefile system, see [.rhiza/make.d/README.md](../.rhiza/make.d/README.md).
