# Rhiza Architecture

This document describes the architecture of Rhiza's "living templates" system, including the template synchronization mechanism, Makefile hierarchy, and extension points.

---

## Overview

Rhiza implements a **living templates** pattern that differs from traditional template generators (cookiecutter, copier). Instead of generating a one-time snapshot, Rhiza enables continuous synchronization between your project and an upstream template repository.

```mermaid
flowchart TB
    subgraph Template["Template Repository (Jebel-Quant/rhiza)"]
        TW[Workflows<br>.yml files]
        TC[Configs<br>ruff.toml, pytest.ini]
        TS[Scripts<br>release.sh]
        TM[Makefile System]
    end

    subgraph Project["Your Project"]
        subgraph Config["Configuration"]
            YAML[".rhiza/template.yml<br>• repository: Jebel-Quant/rhiza<br>• ref: main<br>• include/exclude patterns"]
        end

        SW[Synced Workflows]
        SC[Synced Configs]
        EX[Excluded<br>Custom Files]
        YC[Your Code]
    end

    Template -->|"uvx rhiza materialize<br>(controlled by template.yml)"| Project
    TW -.->|include pattern| SW
    TC -.->|include pattern| SC
    TS -.->|exclude pattern| EX
```

---

## Template Synchronization

### Configuration File: template.yml

Projects using Rhiza define their sync configuration in `.rhiza/template.yml`:

```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza    # Upstream template source
ref: main                         # Branch or tag to sync from

include: |                        # Files to pull from template
  .github/workflows/*.yml
  .pre-commit-config.yaml
  ruff.toml
  pytest.ini
  Makefile

exclude: |                        # Paths to skip (protect customizations)
  .rhiza/scripts/customisations/*
  .rhiza/make.d/50-*.mk
```

### Sync Commands

| Command | Description |
|---------|-------------|
| `make sync` | Pull updates from template repository |
| `make validate` | Check if project matches template (without modifying) |
| `uvx rhiza materialize` | Direct CLI for sync operation |
| `uvx rhiza validate` | Direct CLI for validation |

### Sync Process Flow

```mermaid
flowchart TD
    A[make sync] --> B[pre-sync:: hook]
    B --> C[uvx rhiza materialize --force .]

    subgraph Materialize["Materialize Process"]
        C --> D[Read .rhiza/template.yml]
        D --> E[Fetch files from repository at ref]
        E --> F[Apply include patterns]
        F --> G[Skip exclude patterns]
        G --> H[Write files to project]
    end

    H --> I[post-sync:: hook]

    style B fill:#e1f5fe
    style I fill:#e1f5fe
```

### Automated Sync Workflow

The `rhiza_sync.yml` workflow automates synchronization:

- **Schedule**: Weekly (Mondays at 00:00 UTC)
- **Manual trigger**: Via workflow_dispatch
- **Output**: Creates a pull request with template updates
- **Requirement**: `PAT_TOKEN` secret with `workflow` scope (for modifying workflow files)

---

## Makefile Architecture

### Hierarchy

Rhiza uses a modular Makefile system with clear separation of concerns:

```mermaid
flowchart TD
    subgraph Root["Project Root"]
        MF[Makefile]
    end

    subgraph Core["Core Logic (Synced)"]
        RMK[.rhiza/rhiza.mk]
        TMK[tests/tests.mk]
        BMK[book/book.mk]
        DMK[docker/docker.mk]
        PMK[presentation/presentation.mk]
        GMK[.github/github.mk]
    end

    subgraph Extensions["Custom Extensions (Not Synced)"]
        E1[01-custom-env.mk<br>Variables & Config]
        E2[10-custom-task.mk<br>Custom Tasks]
        E3[90-hooks.mk<br>Hook Implementations]
    end

    subgraph Local["Developer Local"]
        LMK[local.mk<br>Not committed]
    end

    MF -->|include| RMK
    RMK -->|include| TMK
    RMK -->|include| BMK
    RMK -->|include| DMK
    RMK -->|include| PMK
    RMK -->|include| GMK
    RMK -->|"include .rhiza/make.d/*.mk"| Extensions
    MF -->|"-include"| LMK

    style Extensions fill:#fff3e0
    style Local fill:#fce4ec
```

### File Responsibilities

| File | Purpose | Synced? |
|------|---------|---------|
| `Makefile` | Entry point, minimal (~8 lines) | Yes |
| `.rhiza/rhiza.mk` | Core targets (install, sync, release) | Yes |
| `tests/tests.mk` | Test targets | Yes |
| `book/book.mk` | Documentation targets | Yes |
| `.rhiza/make.d/*.mk` | Project-specific extensions | No |
| `local.mk` | Developer-local shortcuts | No (gitignored) |

### Hook System

Rhiza provides double-colon hook targets for customization:

```makefile
# Available hooks (defined in rhiza.mk)
pre-install::   post-install::
pre-sync::      post-sync::
pre-validate::  post-validate::
pre-release::   post-release::
pre-bump::      post-bump::
```

**Usage in .rhiza/make.d/90-hooks.mk:**

```makefile
post-install::
	@echo "Running custom post-install steps..."
	@./scripts/setup-local-config.sh

pre-release::
	@echo "Validating release requirements..."
	@make test
```

### Extension Point Conventions

Files in `.rhiza/make.d/` are loaded alphabetically. Use numeric prefixes:

| Range | Purpose | Example |
|-------|---------|---------|
| 00-19 | Configuration & Variables | `01-custom-env.mk` |
| 20-79 | Custom Tasks & Rules | `50-ml-training.mk` |
| 80-99 | Hooks & Lifecycle Logic | `90-hooks.mk` |

---

## Tool Execution Model

### uv-First Approach

All Python execution flows through `uv`:

```mermaid
flowchart TD
    MT[Makefile Target]

    MT --> UV_RUN[uv run<br>Project venv]
    MT --> UVX[uvx<br>Ephemeral env]
    MT --> UV_PIP[uv pip install<br>Dependencies]

    UV_RUN --> PYTEST[pytest<br>scripts]
    UVX --> RUFF[ruff<br>pre-commit]
    UV_PIP --> VENV[.venv<br>packages]

    style UV_RUN fill:#c8e6c9
    style UVX fill:#bbdefb
    style UV_PIP fill:#fff9c4
```

| Command | Usage |
|---------|-------|
| `uv run` | Execute in project virtual environment |
| `uvx` | Execute in ephemeral environment (external tools) |
| `uv sync` | Install dependencies from lock file |
| `uv pip install` | Install additional packages |

### Environment Variables

```makefile
# Core variables (from rhiza.mk)
INSTALL_DIR ?= ./bin           # Where uv is installed if not in PATH
UV_BIN ?= $(command -v uv)     # Path to uv binary
UVX_BIN ?= $(command -v uvx)   # Path to uvx binary
VENV ?= .venv                  # Virtual environment path
PYTHON_VERSION ?= 3.12         # From .python-version file

# Environment settings
UV_NO_MODIFY_PATH := 1         # Don't modify shell PATH
UV_VENV_CLEAR := 1             # Clear venv before creation
```

---

## Directory Structure

```
project-root/
├── .rhiza/
│   ├── template.yml        # Sync configuration (your project)
│   ├── rhiza.mk            # Core Makefile logic
│   ├── .env                # Environment variables
│   ├── .cfg.toml           # Additional configuration
│   ├── docs/               # Rhiza documentation
│   │   ├── CONFIG.md
│   │   └── TOKEN_SETUP.md
│   ├── make.d/             # Custom Makefile extensions
│   │   ├── 01-custom-env.mk
│   │   ├── 10-custom-task.mk
│   │   └── README.md
│   ├── requirements/       # Additional pip requirements
│   │   ├── tools.txt
│   │   ├── tests.txt
│   │   └── docs.txt
│   ├── scripts/            # Automation scripts
│   │   └── release.sh
│   └── utils/              # Python utilities
│       └── version_matrix.py
├── .github/
│   └── workflows/          # CI/CD workflows (synced)
├── Makefile                # Entry point
├── pyproject.toml          # Project configuration
├── ruff.toml               # Linting configuration (synced)
├── pytest.ini              # Test configuration (synced)
└── .pre-commit-config.yaml # Pre-commit hooks (synced)
```

---

## Release Pipeline

### Version Management

Single source of truth: `pyproject.toml`

```mermaid
flowchart TD
    A[make bump] --> B[pre-bump:: hook]
    B --> C[uvx rhiza tools bump]

    subgraph Bump["Interactive Bump"]
        C --> D[Show current version]
        D --> E[Prompt for bump type<br>major/minor/patch]
        E --> F[Update pyproject.toml]
        F --> G[Update uv.lock]
    end

    G --> H[post-bump:: hook]

    style B fill:#e1f5fe
    style H fill:#e1f5fe
```

### Release Process

```mermaid
flowchart TD
    A[make release] --> B[pre-release:: hook]
    B --> C[.rhiza/scripts/release.sh]

    subgraph Script["Release Script"]
        C --> D[Verify clean working tree]
        D --> E[Check branch up-to-date]
        E --> F[Read version from pyproject.toml]
        F --> G[Prompt for confirmation]
        G --> H[Create git tag]
        H --> I[Push tag to origin]
    end

    I --> J[post-release:: hook]
    J --> K[GitHub Actions Triggered]

    subgraph Actions["rhiza_release.yml"]
        K --> L[Validate tag format]
        L --> M[Build package with hatch]
        M --> N[Create draft release]
        N --> O[Publish to PyPI<br>OIDC]
        N --> P[Publish devcontainer<br>optional]
        O --> Q[Finalize release]
        P --> Q
    end

    style B fill:#e1f5fe
    style J fill:#e1f5fe
    style Actions fill:#f3e5f5
```

---

## Customization Strategies

### 1. Exclude from Sync

Add paths to `template.yml` exclude section:

```yaml
exclude: |
  .rhiza/make.d/*           # All custom make extensions
  .github/workflows/custom_*.yml  # Custom workflows
```

### 2. Use Hooks

Implement pre/post hooks in `.rhiza/make.d/`:

```makefile
# .rhiza/make.d/90-hooks.mk
post-install::
	@pip install -e ./internal-package

pre-release::
	@./scripts/run-integration-tests.sh
```

### 3. Local Extensions

Use `local.mk` for developer-specific shortcuts (not committed):

```makefile
# local.mk
dev-deploy:
	@./scripts/deploy-to-sandbox.sh
```

### 4. Fork the Template

For organization-wide customization:

1. Fork Jebel-Quant/rhiza to your organization
2. Customize workflows, configs, scripts
3. Point your projects to your fork:

```yaml
# .rhiza/template.yml
repository: your-org/rhiza-template
ref: main
```

---

## Security Considerations

1. **Minimal Permissions**: Workflows default to `contents: read`
2. **OIDC Publishing**: PyPI uses trusted publishing, no stored tokens
3. **PAT for Workflows**: Sync requires `PAT_TOKEN` when modifying workflow files
4. **Lock Files**: `uv.lock` ensures reproducible, auditable builds
5. **CodeQL Scanning**: Automated security analysis for Python and Actions
