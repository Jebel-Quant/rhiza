# .rhiza

This directory contains the core configuration, templates, and automation logic for the Rhiza project.
It is the "brain" of the repository's maintenance system.

## 📁 Directory Structure

- **[docs/](docs/)**: Detailed documentation regarding Rhiza configuration and setup.
  - `CONFIG.md`: Guide to configuring the sync mechanism.
  - `TOKEN_SETUP.md`: Instructions for setting up GitHub/GitLab tokens for automation.
- **[make.d/](make.d/)**: A "Makefile Cookbook" for repository-specific build logic. Files here are automatically included in the main `Makefile`.
- **[requirements/](requirements/)**: Modular development dependencies (tests, docs, tools, etc.).
- **[scripts/](scripts/)**: Automation scripts used by Makefile targets (e.g., `release.sh`).
- **[utils/](utils/)**: Helper utilities and python scripts for repository maintenance.
- **`rhiza.mk`**: The core Makefile module that implements the Rhiza synchronization and validation logic.

## 🛠 Core Concepts

### Template Synchronization
Rhiza allows repositories to stay in sync with a central "template" (often this repository itself). The configuration for this is typically found in `.rhiza/template.yml` at the project root (though it can be customized).

### Modular Makefile
The main `Makefile` at the root is designed to be lean, importing logic from:
1. `rhiza.mk` (core logic)
2. Files in `make.d/` (custom/extended logic)

## 🚀 Common Tasks

If you are working within this directory, you are likely maintaining the Rhiza ecosystem. Common commands include:

```bash
make sync      # Sync the project with the template
make validate  # Check if the project structure matches the template
make help      # See all available automation targets
```

For more information on how to customize Rhiza for your own project, see [docs/CUSTOMIZATION.md](../docs/CUSTOMIZATION.md).
