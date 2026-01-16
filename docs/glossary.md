# Glossary

This glossary defines terms and concepts specific to Rhiza and its template synchronization system.

---

## Core Concepts

### Living Templates

A template system that enables **continuous synchronization** between your project and an upstream template repository. Unlike traditional generators (cookiecutter, copier) that create a one-time snapshot, living templates allow you to pull updates over time while preserving your customizations.

**Related:** [Template Repository](#template-repository), [Sync](#sync)

---

### Template Repository

The upstream repository that serves as the source of truth for configuration files, workflows, and tooling. By default, this is `Jebel-Quant/rhiza`, but you can point to any repository (including your own fork).

**Configuration:**
```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main
```

**Related:** [template.yml](#templateyml)

---

### Sync

The process of pulling updates from a [template repository](#template-repository) into your project. Sync respects include/exclude patterns defined in `template.yml`.

**Commands:**
- `make sync` - Pull updates from template
- `uvx rhiza materialize` - Direct CLI command

**Related:** [Materialize](#materialize), [Validate](#validate)

---

### Materialize

The action of applying template files to your project. Rhiza reads your `template.yml` configuration, fetches matching files from the template repository, and writes them to your project directory.

**Command:** `uvx rhiza materialize --force .`

**Related:** [Sync](#sync)

---

### Validate

Check whether your project's files match the template repository without making changes. Useful for CI pipelines to detect configuration drift.

**Commands:**
- `make validate` - Run validation
- `uvx rhiza validate .` - Direct CLI command

**Related:** [Sync](#sync)

---

## Configuration Files

### template.yml

The configuration file (`.rhiza/template.yml`) that controls template synchronization. Defines what files to sync and what to exclude.

**Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| `repository` | GitHub repository in `owner/repo` format | `Jebel-Quant/rhiza` |
| `ref` | Branch, tag, or commit to sync from | `main`, `v0.6.0` |
| `include` | Glob patterns for files to sync | `*.yml`, `.github/**` |
| `exclude` | Glob patterns for files to skip | `.rhiza/make.d/*` |

**Example:**
```yaml
repository: Jebel-Quant/rhiza
ref: main

include: |
  .github/workflows/*.yml
  ruff.toml
  pytest.ini

exclude: |
  .rhiza/make.d/*
```

---

### rhiza.mk

The core Makefile module (`.rhiza/rhiza.mk`) containing Rhiza's automation logic. Implements targets for sync, validate, install, release, and other common tasks.

**Key targets defined:**
- `sync`, `validate`, `readme`
- `install`, `install-uv`, `clean`
- `bump`, `release`
- `fmt`, `deptry`
- `help`, `version-matrix`

---

### make.d/

The directory (`.rhiza/make.d/`) for project-specific Makefile extensions. Files here are automatically included and are **not synced** from the template, allowing you to add custom targets without conflicts.

**Naming convention:**
| Prefix | Purpose |
|--------|---------|
| 00-19 | Configuration & Variables |
| 20-79 | Custom Tasks & Rules |
| 80-99 | Hooks & Lifecycle Logic |

**Example:** `.rhiza/make.d/50-ml-training.mk`

---

### local.mk

An optional Makefile (`local.mk` in project root) for developer-specific shortcuts. This file is gitignored and never synced, making it ideal for personal convenience targets.

**Example:**
```makefile
# local.mk
dev-deploy:
    @./scripts/deploy-to-my-sandbox.sh
```

---

## Hooks

### Hook Targets

Double-colon Makefile targets that allow you to inject custom logic before or after standard operations. Hooks are defined in `rhiza.mk` and can be extended in `.rhiza/make.d/`.

**Available hooks:**

| Hook | Triggered |
|------|-----------|
| `pre-install::` / `post-install::` | Around `make install` |
| `pre-sync::` / `post-sync::` | Around `make sync` |
| `pre-validate::` / `post-validate::` | Around `make validate` |
| `pre-bump::` / `post-bump::` | Around `make bump` |
| `pre-release::` / `post-release::` | Around `make release` |

**Usage:**
```makefile
# .rhiza/make.d/90-hooks.mk
post-install::
    @echo "Running custom setup..."
    @./scripts/setup-local-config.sh
```

**Note:** Use double-colon (`::`) syntax to allow multiple definitions across files.

---

## Tools

### uv

A fast Python package manager from Astral. Rhiza uses uv exclusively for all Python operations including virtual environment management, dependency installation, and script execution.

**Key commands:**
| Command | Purpose |
|---------|---------|
| `uv sync` | Install dependencies from lock file |
| `uv run` | Execute in project virtual environment |
| `uv pip install` | Install additional packages |
| `uv venv` | Create virtual environment |
| `uv lock` | Generate/update lock file |

**Related:** [uvx](#uvx)

---

### uvx

A command for running Python tools in ephemeral (temporary) environments. Used for external tools that shouldn't pollute your project's virtual environment.

**Examples:**
```bash
uvx ruff check .           # Run ruff without installing
uvx rhiza materialize .    # Run rhiza CLI
uvx pre-commit run         # Run pre-commit hooks
```

**Related:** [uv](#uv)

---

### Deptry

A tool for detecting missing and obsolete dependencies. Rhiza includes deptry in its standard workflow to maintain dependency hygiene.

**Command:** `make deptry`

---

### Hatch

A Python build backend used by the release workflow to build distributable packages (wheels and source distributions).

**Command:** `uvx hatch build`

---

## Workflows

### CI Workflow

The continuous integration workflow (`rhiza_ci.yml`) that runs tests across multiple Python versions. Uses a dynamic matrix generated from `pyproject.toml`.

**Trigger:** Push/PR to main branch

---

### Sync Workflow

The automated synchronization workflow (`rhiza_sync.yml`) that periodically pulls updates from the template repository and creates a pull request.

**Trigger:** Weekly schedule or manual dispatch
**Requirement:** `PAT_TOKEN` secret with `workflow` scope

---

### Release Workflow

The release pipeline (`rhiza_release.yml`) triggered by version tags. Handles building, publishing to PyPI, and creating GitHub releases.

**Trigger:** Push of tags matching `v*`
**Phases:** Validate → Build → Draft → Publish → Finalize

---

## Versioning

### Version Source of Truth

The `version` field in `pyproject.toml` is the single source of truth for the project version. All version operations read from and write to this location.

```toml
[project]
version = "0.6.0"
```

---

### Bump

The process of incrementing the project version. Rhiza provides an interactive bump command that updates `pyproject.toml` and regenerates `uv.lock`.

**Command:** `make bump`

**Bump types:**
- `major` - Breaking changes (1.0.0 → 2.0.0)
- `minor` - New features (1.0.0 → 1.1.0)
- `patch` - Bug fixes (1.0.0 → 1.0.1)

---

### Release

The process of creating a version tag and pushing it to trigger the release workflow.

**Command:** `make release`

**Steps:**
1. Verify clean working tree
2. Confirm version
3. Create git tag (`v{version}`)
4. Push tag to origin

---

## Publishing

### Trusted Publishing (OIDC)

A secure method for publishing to PyPI without storing credentials. Uses GitHub's OpenID Connect (OIDC) tokens to authenticate with PyPI.

**Requirements:**
- Package registered on PyPI as a Trusted Publisher
- `id-token: write` permission in workflow

---

### Private :: Do Not Upload

A PyPI classifier that prevents accidental package publication. When present in `pyproject.toml`, the release workflow skips PyPI upload.

```toml
classifiers = [
    "Private :: Do Not Upload",
]
```

---

## Patterns

### Include Pattern

A glob pattern in `template.yml` specifying files to sync from the template repository.

**Examples:**
```yaml
include: |
  .github/workflows/*.yml    # All workflow files
  *.toml                     # Root-level TOML files
  .rhiza/**                  # Everything in .rhiza
```

---

### Exclude Pattern

A glob pattern in `template.yml` specifying files to skip during sync, protecting your customizations.

**Examples:**
```yaml
exclude: |
  .rhiza/make.d/*            # Custom make extensions
  .github/workflows/custom_* # Custom workflows
```

---

### Configuration Drift

When your project's configuration files diverge from the template repository over time. Rhiza's living templates approach helps prevent drift through regular synchronization.

**Detection:** `make validate`
**Resolution:** `make sync`

---

## Environment

### .python-version

A file containing the default Python version for the project. Read by uv, pyenv, and other tools.

**Example content:** `3.12`

---

### .venv

The default virtual environment directory created by `make install`. Contains installed dependencies isolated from the system Python.

---

### uv.lock

The lock file generated by uv containing exact versions of all dependencies. Ensures reproducible builds across environments.

**Generate:** `uv lock`
**Install from:** `uv sync --frozen`
