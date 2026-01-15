# .rhiza

This directory is the "engine room" of the Rhiza project. It contains the core configuration, modular Makefile system, shared scripts, and development requirements.

## 📁 Directory Structure

### 🤖 `agentic/`
Contains configurations and logic for AI-powered development workflows.
- `agentic.mk`: Makefile targets for GitHub Copilot CLI integration (`make copilot`, `make analyse-repo`).

### 📖 `docs/`
Internal documentation and resources related to the Rhiza system itself.
- `CONFIG.md`: High-level overview of the Rhiza configuration and workflows.
- `TOKEN_SETUP.md`: Guide for setting up PAT tokens for automated synchronization.

### 🛠️ `make.d/`
Modular Makefile extensions. This is the primary place for repository-specific Makefile logic.
- Files here are included in alphabetical order by the main `Makefile`.
- Use numeric prefixes (e.g., `10-custom.mk`, `90-hooks.mk`) to control loading order.
- Supports **Hooks** (using `::` syntax) to inject logic into standard workflows like `post-install` or `pre-sync`.
- See the [Makefile Cookbook](make.d/README.md) for detailed recipes.

### 📦 `requirements/`
Development dependencies organized by purpose, ensuring a lean environment.
- `tests.txt`: Dependencies for pytest and coverage.
- `marimo.txt`: Requirements for running Marimo notebooks.
- `docs.txt`: Tools for API documentation generation (pdoc).
- `tools.txt`: General development utilities (pre-commit, dotenv).
- Automatically installed via `make install`.

### 📜 `scripts/`
Shared utility scripts used across the project and CI/CD pipelines.
- `release.py`: Logic for the interactive `make bump` and `make release` workflows.

### 🧰 `utils/`
Internal Python utilities.
- `version_matrix.py`: Helper script to emit supported Python versions for CI matrix generation.

## 🗝️ Core Files

- **`rhiza.mk`**: The "Stable API" of the project. It defines the core targets (`install`, `test`, `sync`, `validate`, etc.) and is managed by the Rhiza template.
- **`.env`**: Project-wide environment variables (e.g., `MARIMO_FOLDER`, `SOURCE_FOLDER`). This file is used by both the Makefile and Python scripts.

## 🔄 Maintenance & Syncing

Most files in `.rhiza` (except for `.env` and specific files in `make.d/`) are **template-managed**.

### How to Update
To pull the latest improvements from the Rhiza upstream template, run:
```bash
make sync
```

### Customization
- **Do not modify `rhiza.mk` directly**, as your changes will be overwritten during the next sync.
- **Use `make.d/`** for adding new targets or extending existing ones via hooks.
- **Update `.env`** to change project paths or configuration values.
- **Exclusions**: If you must prevent a specific file from being updated, add it to the `exclude` list in your `.rhiza/template.yml` (if applicable).
