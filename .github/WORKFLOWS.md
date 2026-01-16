# GitHub Actions Workflows

This document describes all GitHub Actions workflows in this repository.

---

## Quick Reference

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [CI](#ci) | Push/PR to main | Run tests on multiple Python versions |
| [Pre-commit](#pre-commit) | Push/PR to main | Code quality and formatting checks |
| [Deptry](#deptry) | Push/PR to main | Detect missing/obsolete dependencies |
| [CodeQL](#codeql) | Push/PR/Weekly | Security vulnerability scanning |
| [Docker](#docker) | Push/PR to main | Lint and validate Dockerfile |
| [Devcontainer](#devcontainer) | Changes to .devcontainer/ | Validate devcontainer builds |
| [Marimo](#marimo) | Push/PR to main | Execute and validate notebooks |
| [Book](#book) | Push to main | Build and deploy documentation |
| [Validate](#validate) | Push/PR to main | Validate rhiza configuration |
| [Sync](#sync) | Weekly/Manual | Synchronize with template repository |
| [Release](#release) | Tag push (v*) | Build, publish, and release |

---

## Workflow Details

### CI

**File:** `rhiza_ci.yml`
**Name:** (RHIZA) CI

**Purpose:** Run the test suite across multiple Python versions to ensure compatibility.

**Triggers:**
- Push to `main` or `master`
- Pull requests to `main` or `master`

**How it works:**
1. Generates Python version matrix dynamically from `pyproject.toml`
2. Runs `make test` for each Python version in parallel
3. Uses `fail-fast: false` to report all failures

**Permissions:** `contents: read`

---

### Pre-commit

**File:** `rhiza_pre-commit.yml`
**Name:** (RHIZA) PRE-COMMIT

**Purpose:** Run pre-commit hooks to ensure code quality and consistency.

**Triggers:**
- Push to `main` or `master`
- Pull requests to `main` or `master`

**How it works:**
- Executes `make fmt` which runs ruff format and ruff check

**Permissions:** `contents: read`

---

### Deptry

**File:** `rhiza_deptry.yml`
**Name:** (RHIZA) DEPTRY

**Purpose:** Identify missing and obsolete dependencies in the project.

**Triggers:**
- Push to `main` or `master`
- Pull requests to `main` or `master`

**How it works:**
- Runs in a uv container (`ghcr.io/astral-sh/uv:0.9.26-python3.12-trixie`)
- Executes `make deptry` to check dependency hygiene

**Permissions:** `contents: read`

---

### CodeQL

**File:** `rhiza_codeql.yml`
**Name:** (RHIZA) CODEQL

**Purpose:** Perform security vulnerability scanning using GitHub's CodeQL analysis.

**Triggers:**
- Push to `main` or `master`
- Pull requests to `main` or `master`
- Weekly schedule (Mondays at 01:27 UTC)

**How it works:**
- Analyzes Python code and GitHub Actions workflows
- Uses `fail-fast: false` to report all language findings
- Only runs on public repositories

**Permissions:** `security-events: write`, `packages: read`, `actions: read`, `contents: read`

**Languages analyzed:**
- `actions` (GitHub Actions workflows)
- `python`

---

### Docker

**File:** `rhiza_docker.yml`
**Name:** (RHIZA) DOCKER

**Purpose:** Lint Dockerfile with hadolint and validate the image builds successfully.

**Triggers:**
- Push to `main` or `master`
- Pull requests to `main` or `master`

**How it works:**
1. Checks if `docker/Dockerfile` exists (skips gracefully if not)
2. Lints with hadolint
3. Builds image with Docker Buildx (validation only, not pushed)
4. Uses Python version from `.python-version`

**Permissions:** `contents: read`

---

### Devcontainer

**File:** `rhiza_devcontainer.yml`
**Name:** (RHIZA) DEVCONTAINER

**Purpose:** Validate that the devcontainer image builds successfully.

**Triggers:**
- Push to any branch when `.devcontainer/` files change
- Pull requests to `main`/`master` when `.devcontainer/` files change
- Changes to this workflow file

**How it works:**
1. Checks if `.devcontainer/devcontainer.json` exists
2. Builds devcontainer image (validation only, `push: never`)
3. Image tag format: `{branch}-{commit-sha}`

**Permissions:** `contents: read`, `packages: write`

**Note:** Actual publishing happens during releases via `rhiza_release.yml` when `PUBLISH_DEVCONTAINER` variable is `true`.

---

### Marimo

**File:** `rhiza_marimo.yml`
**Name:** (RHIZA) MARIMO

**Purpose:** Discover and execute all Marimo notebooks to ensure they are reproducible.

**Triggers:**
- Push to `main` or `master`
- Pull requests to `main` or `master`

**How it works:**
1. Discovers all `.py` notebooks in `book/marimo/`
2. Creates a dynamic matrix for parallel execution
3. Runs each notebook in a fresh ephemeral environment via `uvx uv run`
4. Uses `fail-fast: false` to report all failing notebooks

**Permissions:** `contents: read`

---

### Book

**File:** `rhiza_book.yml`
**Name:** (RHIZA) BOOK

**Purpose:** Build and deploy comprehensive documentation to GitHub Pages.

**Triggers:**
- Push to `main` or `master`

**How it works:**
1. Syncs virtual environment
2. Runs `make book` to generate documentation
3. Uploads to GitHub Pages artifact
4. Deploys to GitHub Pages (unless fork or `PUBLISH_COMPANION_BOOK` is `false`)

**Permissions:** `contents: read`, `pages: write`, `id-token: write`

**Environment:** `github-pages`

**Components built:**
- API documentation (pdoc)
- Test coverage reports
- Marimo notebooks (HTML export)

---

### Validate

**File:** `rhiza_validate.yml`
**Name:** (RHIZA) VALIDATE

**Purpose:** Validate project structure against template repository configuration.

**Triggers:**
- Push to `main` or `master`
- Pull requests to `main` or `master`

**How it works:**
- Runs in a uv container
- Executes `uvx rhiza validate .`
- Skipped for the rhiza repository itself (has no template.yml)

**Permissions:** `contents: read`

---

### Sync

**File:** `rhiza_sync.yml`
**Name:** (RHIZA) SYNC

**Purpose:** Synchronize the repository with its upstream template.

**Triggers:**
- Manual dispatch (workflow_dispatch)
- Weekly schedule (Mondays at 00:00 UTC)

**How it works:**
1. Runs `uvx rhiza materialize --force .`
2. Commits changes if detected
3. Creates a pull request with the updates
4. Skipped for the rhiza repository itself

**Permissions:** `contents: write`, `pull-requests: write`

**Required secrets:**
- `PAT_TOKEN` - Personal Access Token with `workflow` scope (required if sync modifies workflow files)

**Inputs:**
- `create-pr` (boolean, default: true) - Whether to create a pull request

---

### Release

**File:** `rhiza_release.yml`
**Name:** (RHIZA) RELEASE

**Purpose:** Automated release pipeline for Python packages with optional devcontainer publishing.

**Triggers:**
- Push of tags matching `v*` (e.g., `v1.2.3`)

**Pipeline phases:**
1. **Validate Tag** - Check tag format, ensure release doesn't already exist
2. **Build** - Build Python package with Hatch (if `[build-system]` defined)
3. **Generate SBOM** - Create Software Bill of Materials (SPDX and CycloneDX formats)
4. **Draft Release** - Create draft GitHub release with SBOM artifacts
5. **Publish to PyPI** - Publish using OIDC trusted publishing
6. **Publish Devcontainer** - Build and push devcontainer image (conditional)
7. **Finalize Release** - Publish the GitHub release with links

**Permissions:** `contents: write`, `id-token: write`, `packages: write`

**Environment:** `release`

**PyPI Publishing:**
- Uses OIDC Trusted Publishing (no stored credentials needed)
- Skipped if no `dist/` artifacts or `Private :: Do Not Upload` classifier present
- For custom feeds: use `PYPI_REPOSITORY_URL` variable and `PYPI_TOKEN` secret

**Devcontainer Publishing:**
- Only when `PUBLISH_DEVCONTAINER` variable is `true`
- Requires `.devcontainer/` directory
- Registry defaults to `ghcr.io` (override with `DEVCONTAINER_REGISTRY` variable)

**To trigger:**
```bash
git tag v1.2.3
git push origin v1.2.3
```

---

## Required Configuration

### Repository Secrets

| Secret | Required For | Description |
|--------|--------------|-------------|
| `PAT_TOKEN` | Sync workflow | Personal Access Token with `workflow` scope |
| `PYPI_TOKEN` | Release (custom feeds) | Token for custom PyPI feed authentication |

### Repository Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `PUBLISH_COMPANION_BOOK` | Book | Set to `true` to deploy docs (default: deploy) |
| `PUBLISH_DEVCONTAINER` | Release, Devcontainer | Set to `true` to publish devcontainer images |
| `DEVCONTAINER_REGISTRY` | Release, Devcontainer | Container registry (default: `ghcr.io`) |
| `DEVCONTAINER_IMAGE_NAME` | Release, Devcontainer | Custom image name component |
| `PYPI_REPOSITORY_URL` | Release | Custom PyPI feed URL |

---

## Workflow Dependencies

```
CI ──────────────────────────────────────────────────────────> Tests pass
Pre-commit ──────────────────────────────────────────────────> Code quality
Deptry ──────────────────────────────────────────────────────> Dependency health
CodeQL ──────────────────────────────────────────────────────> Security scan
Docker ──────────────────────────────────────────────────────> Dockerfile valid
Devcontainer ────────────────────────────────────────────────> Devcontainer valid
Marimo ──────────────────────────────────────────────────────> Notebooks valid
Book ────────────────────────────────────────────────────────> Docs deployed
Validate ────────────────────────────────────────────────────> Template config valid
Sync ────────────────────────────────────────────────────────> PR with updates
Release: Tag → Build → Draft → PyPI → Devcontainer → Finalize
```

---

## Tool Versions

All workflows use consistent tool versions:
- **uv:** 0.9.26
- **Python:** Dynamically from `pyproject.toml` (CI) or `.python-version` (others)
- **Checkout action:** v6
- **Setup-uv action:** v7
