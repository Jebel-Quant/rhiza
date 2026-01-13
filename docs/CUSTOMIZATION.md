# Customization Guide

This guide covers advanced customization options for Rhiza-based projects.

## 🔧 Custom Build Extras

The project includes a hook for installing additional system dependencies and custom build steps needed across all build phases.

### Using build-extras.sh

Create a file `.rhiza/scripts/customisations/build-extras.sh` in your repository to install system packages or dependencies.

> **Note:** This repository uses a dedicated `customisations` folder for repo-specific scripts to avoid conflicts with template updates.

```bash
#!/bin/bash
set -euo pipefail

# Example: Install graphviz for diagram generation
sudo apt-get update
sudo apt-get install -y graphviz

# Add other custom installation commands here
```

### When it Runs

The `build-extras.sh` script (from `.rhiza/scripts/customisations`) is automatically invoked during:
- `make install` - Initial project setup
- `make test` - Before running tests
- `make book` - Before building documentation
- `make docs` - Before generating API documentation

This ensures custom dependencies are available whenever needed throughout the build lifecycle. The `Makefile` intentionally only checks the `.rhiza/scripts/customisations` folder for repository-specific hooks such as `build-extras.sh` and `post-release.sh`.

### Important: Exclude from Template Updates

If you customize this file, add it to the exclude list in your `action.yml` configuration to prevent it from being overwritten during template updates. Use the `customisations` path to avoid clobbering:

```yaml
exclude: |
  .rhiza/scripts/customisations/build-extras.sh
```

### Common Use Cases

- Installing graphviz for diagram rendering
- Adding LaTeX for mathematical notation
- Installing system libraries for specialized tools
- Setting up additional build dependencies
- Downloading external resources or tools

### Post-release scripts

If you need repository-specific post-release tasks, place a `post-release.sh` script in `.rhiza/scripts/customisations/post-release.sh`. The `Makefile` will only look in the `customisations` folder for that hook.

## 🛠️ Makefile Architecture & Extension

For detailed information about extending and customizing the Makefile system, see [.rhiza/make.d/README.md](../.rhiza/make.d/README.md).

### Quick Reference

**Extension Points (Hooks):**
- `pre-install / post-install`
- `pre-sync / post-sync`
- `pre-validate / post-validate`
- `pre-release / post-release`
- `pre-bump / post-bump`

**Example: Adding a post-install step**

Create `.rhiza/make.d/99-setup.mk`:

```makefile
post-install::
	@echo "Installing specialized dependencies..."
	@pip install some-private-lib
```

See the [Makefile Cookbook](../.rhiza/make.d/README.md) for more recipes and patterns.
