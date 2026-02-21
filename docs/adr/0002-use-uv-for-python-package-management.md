# 2. Use uv for Python Package and Environment Management

Date: 2024-09-01

## Status

Accepted

## Context

Rhiza needs a reliable, fast, and consistent tool for managing Python environments and
dependencies across local development, CI/CD pipelines, and DevContainer setups. The
traditional Python toolchain (pip + venv, or pip-tools) presents several challenges:

- **Fragmentation**: Different tools handle different concerns—`pip` for installation,
  `venv` for environments, `pip-tools` for lock files, `pyenv` for Python versions. Each
  has its own configuration and mental model.
- **Speed**: `pip` resolution and installation can be slow, especially in CI where
  dependencies are installed from scratch on every run.
- **Reproducibility**: Without lock files, builds can diverge. With `requirements.txt`
  lock files, the workflow is verbose and error-prone.
- **Python version management**: Installing the correct Python version requires a
  separate tool (`pyenv`, `asdf`, or system packages), adding complexity to onboarding.

As a template system, Rhiza must bootstrap with minimal prerequisites and operate
reliably across many different downstream projects and environments. Every extra tool
in the prerequisite chain is a potential friction point for users adopting Rhiza.

## Decision

We will use [uv](https://github.com/astral-sh/uv) as the single tool for Python version
management, virtual environment creation, and dependency installation.

**Key aspects:**

1. **Single binary**: `uv` is a single self-contained binary written in Rust, installable
   via a one-line `curl` command. No Python required to install it.
2. **Python version management**: `uv` reads `.python-version` and automatically downloads
   and installs the correct Python version when needed.
3. **Virtualenv creation**: `uv venv` creates a virtual environment using the managed
   Python version.
4. **Dependency installation**: `uv sync` installs dependencies from `pyproject.toml`
   using a lock file (`uv.lock`) for reproducible builds.
5. **Script execution**: `uv run <command>` ensures commands run inside the correct
   environment without requiring manual activation.
6. **Bootstrap location**: `uv` is installed to `./bin/uv` when not found in PATH,
   keeping the repository self-contained.

The Makefile bootstrap sequence becomes:

```makefile
make install   # installs uv, Python, venv, and all dependencies
```

## Consequences

### Positive

- **Single source of truth for Python**: The `.python-version` file controls the Python
  version; `uv` reads it automatically with no extra configuration.
- **Dramatically faster CI**: `uv` dependency resolution and installation is typically
  10–100× faster than `pip`, reducing CI run times.
- **Reproducible builds**: `uv.lock` captures the exact resolved dependency graph,
  ensuring identical environments across machines and over time.
- **Simplified onboarding**: New contributors run `make install` and everything—Python,
  venv, and dependencies—is set up automatically.
- **No manual venv activation**: `uv run` and Makefile targets handle environment
  activation transparently.
- **Renovate integration**: The `uv-pre-commit` hook and `uv.lock` file integrate with
  Renovate for automated dependency update PRs.

### Neutral

- **New tool**: Contributors unfamiliar with `uv` need to learn a new command. However,
  the Makefile abstracts most `uv` invocations, so direct `uv` knowledge is rarely needed.
- **Lock file**: `uv.lock` must be committed and kept up-to-date. This is enforced via
  a pre-commit hook.

### Negative

- **Dependency on Astral**: `uv` is maintained by Astral, a private company. If
  development stops, we would need to migrate. The tool is open source (MIT licence)
  which mitigates this risk.
- **Rust toolchain not required**: `uv` ships as a pre-built binary, so no Rust
  installation is needed. However, building from source requires Rust.
