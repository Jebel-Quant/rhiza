# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Rhiza?

Rhiza is a **collection of reusable configuration templates** for Python projects — not a runtime library. It has no `src/` directory and no runtime dependencies. Its purpose is to provide and continuously synchronize development infrastructure (Makefiles, CI workflows, linting configs, test setups) into downstream projects via the separate `rhiza-cli` tool.

Downstream projects adopt Rhiza by adding a `.rhiza/template.yml` that lists which bundles to sync from this repository.

## Commands

```bash
make install      # Full setup: installs uv, downloads Python version from .python-version, creates .venv, installs deps
make test         # Run all tests with coverage (90% minimum required)
make fmt          # Run all pre-commit hooks (ruff format/check, markdownlint, bandit, etc.)
make deptry       # Check for unused/missing dependencies
make docs-coverage  # Check docstring coverage with interrogate (100% required)
make typecheck    # Static type checking with pyright
make benchmark    # Performance benchmarks
make hypothesis-test  # Property-based tests only
make stress       # Load/concurrency tests
make security     # pip-audit + bandit security scans
make book         # Build documentation
make marimo       # Start Marimo notebook server
make clean        # Remove build artifacts and stale branches
```

**Running a single test:**
```bash
uv run pytest tests/api/test_makefile_targets.py -v
uv run pytest tests/api/test_makefile_targets.py::TestClass::test_method -v
uv run pytest -m "not stress" tests/   # Exclude stress tests
```

## Command Execution Policy

Follow this order strictly:

1. If a `make` target exists → use `make <target>`
2. No `make` target → use `uv run <command>`
3. Never invoke `.venv/bin/python`, `.venv/bin/pytest`, etc. directly

The virtual environment is managed automatically by `make` and `uv run`. No manual activation is needed.

## Architecture

### Template Bundles

The core abstraction is the **bundle** — a named group of configuration files. All bundles are defined in `.rhiza/template-bundles.yml` (the authoritative list) and fall into three groups:

**Feature bundles** — one per capability:

- `core` (required): Makefiles, linting, base infrastructure
- `tests`: pytest, coverage, type checking
- `benchmarks`: pytest-benchmark infrastructure and reporting
- `github`: GitHub repository configuration (actions, dependabot, core workflows)
- `gitlab`: GitLab CI/CD pipeline configuration and core workflows
- `docker`, `devcontainer`: containerisation
- `vscode`: recommended VS Code extensions and workspace settings for local (non-container) editing
- `claude`: Claude Code slash commands (`/rhiza_quality`, `/rhiza_release`, `/rhiza_update`, `/rhiza_book`) under `.claude/commands/`
- `marimo`: interactive notebooks
- `book`: documentation with [MkDocs](https://www.mkdocs.org/) + [zensical](https://pypi.org/project/zensical/)
- `presentation`: Marp slides
- `paper`: LaTeX paper compilation
- `lfs`, `legal`, `renovate`: miscellaneous tooling

**Platform overlay bundles** — CI workflow stubs that pair a feature with a platform: `github-tests`, `github-book`, `github-marimo`, `github-docker`, `github-devcontainer`, `github-paper`, `github-quality-review`, `gitlab-tests`, `gitlab-book`, `gitlab-marimo`, `gitlab-quality-review`.

**Meta-bundles** — curated compositions of other bundles: `github-project`, `gitlab-project`, `local` (no hosted CI).

### Dogfooding (root files ↔ bundle sources)

Rhiza dogfoods its own templates: the files it ships in `bundles/<name>/...` also live at the repo root so the mother repo runs on its own infrastructure. `bundles/` is the **single source of truth**, and each root dogfood file is a **relative symlink into its owning bundle** (e.g. `.rhiza/rhiza.mk` → `bundles/core/.rhiza/rhiza.mk`). Edit the bundle file; the root reflects it automatically — no second edit. Run `make sync-self` (mother-repo-only, `utils/link_dogfood.py`) to (re)create links after adding a bundle file.

A few files **cannot** be symlinks and stay as **real copies**, kept in sync by tests (`tests/bundles/test_bundle_*_sync.py`) rather than by symlink:

- `.github/*` platform config (Dependabot, release notes, secret scanning, PR template, rulesets) — GitHub reads these blobs directly and does not resolve symlinks. **Live `.github/workflows/*` are also real** (Actions won't run a symlinked workflow) and differ from the bundle stubs by design.
- `.rhiza/.gitignore` (and any `.gitignore`/`.gitattributes`) — git opens these with `O_NOFOLLOW`, so a symlink yields an ELOOP warning and the rules are ignored.

Plus intentional mother-repo overrides that deliberately diverge from their bundle source: `.claude/commands/rhiza_quality.md`, root `.gitignore`, `.pre-commit-config.yaml`, `.python-version`, `SECURITY.md`, `renovate.json`. The exclusion list lives in `utils/link_dogfood.py`. Downstream consumers are unaffected: `rhiza-cli` sparse-checks-out a bundle and dereferences symlinks on copy, so synced projects always receive real files (guarded by `test_no_symlinks_in_*`).

### Modular Makefile System

The root `Makefile` is intentionally thin (~10 lines) and only `include`s `.rhiza/rhiza.mk`. That file auto-loads everything in `.rhiza/make.d/*.mk` alphabetically.

**Each `*.mk` is owned by exactly one bundle** and syncs only when that bundle is adopted — so the file count reflects the bundle model, not accidental sprawl (a project without Docker never receives `docker.mk`). Edit the bundle source (`bundles/<owner>/.rhiza/make.d/<file>`); the root file is a dogfood symlink into it. Mapping:

| `.rhiza/make.d/` file | owner bundle | provides |
| --- | --- | --- |
| `bootstrap.mk` | core | `install`/`uv` bootstrap |
| `doctor.mk` | core | `make doctor` environment checks |
| `quality.mk` | core | `fmt`, lint, pre-commit gates |
| `releasing.mk` | core | `bump`/`release` targets |
| `custom-env.mk` | core | example stub: project variables |
| `custom-task.mk` | core | example stub: project targets/hooks |
| `test.mk` | tests | `test`, coverage, typecheck, stress, mutation |
| `book.mk` | book | `make book` docs build |
| `docker.mk` | docker | container build/run |
| `marimo.mk` | marimo | `make marimo` notebooks |
| `presentation.mk` | presentation | Marp slide build |
| `paper.mk` | paper | LaTeX paper compilation |
| `lfs.mk` | lfs | Git LFS install/track/status |
| `github.mk` | github | GitHub repo/workflow helpers |
| `bundles.mk` | *(mother-repo only — no bundle ships it)* | `explain-bundles`, `sync-self`, `sync-self-check` |

Hook targets use double-colon syntax (`pre-install::`, `post-install::`) and can be defined multiple times to chain behaviour. Add project-specific hooks directly in the root `Makefile` above the include line. Developer-local shortcuts go in `local.mk` (not committed).

### Dependency Management

`uv` manages all Python/dependency concerns:
- `.python-version` is the single source of truth for the Python version
- `uv.lock` pins all transitive dependencies — keep it in sync via `uv lock` or `uv sync`
- `uv run` transparently uses the project venv without manual activation

### Code Quality Requirements

- **Ruff** (`ruff.toml`): see `ruff.toml` for the authoritative and current enabled rule set (rule-prefix reference: https://docs.astral.sh/ruff/rules/)
- **Docstring coverage**: 100% (interrogate) — all public functions, classes, and modules require docstrings
- **Test coverage**: 90% minimum
- **Pre-commit hooks**: `make fmt` runs ruff, markdownlint, bandit, actionlint, interrogate, jsonschema, and uv-lock validation

> **Coverage in this repo (mother-repo specifics).** Rhiza has no `src/` and ships no
> runtime Python, so `make test` prints `Source folder src not found, running tests without
> coverage` and the main `tests/` suite runs *without* a Python coverage number — by design.
> Both that suite and `make rhiza-test` (which runs the shipped `.rhiza/tests/` suite) exercise
> Make targets, YAML, and bundle invariants behaviourally, where there is no Python module to
> cover. (The former suppression/pip-audit utilities that once lived in `.rhiza/utils/` and were
> coverage-gated here have moved into the `rhiza-tools` package, which owns their tests.) So "no
> coverage on `make test`" is expected here and does not mean anything is unmeasured. Downstream
> consumers that adopt the `tests` bundle *do* have a `src/` and get the full 90% `make test` gate.

### CI/CD

This repo runs on **GitHub Actions only**: `.github/workflows/` — CI, release, docker, CodeQL, weekly, sync. There is no root `.gitlab-ci.yml` here.

GitLab support ships as a **template for downstream consumers**, not as active CI in this repo: the `gitlab` bundle (`bundles/gitlab/`) materializes a `.gitlab-ci.yml` plus `.gitlab/` pipelines into projects that adopt the `gitlab-project` profile, mirroring the GitHub Actions coverage there.

Because no GitLab pipeline runs here, `tests/bundles/test_gitlab_ci.py` validates the GitLab templates without a GitLab host: it assembles a `gitlab-project` and (1) checks every container image the pipeline/Dockerfiles reference actually exists on its registry (the guard that catches a retired tag like the removed `uv:*-bookworm`), (2) runs `gitlab-ci-local` (pinned, via `npx`) to resolve every `include:` and validate the merged pipeline against GitLab's JSON schema. A third test actually runs a job in Docker against the pinned `$UV_IMAGE` — it needs Docker and is opt-in: `RHIZA_GITLAB_DOCKER=1 make test` (or run it directly). All three skip cleanly when their dependency (network / Node / Docker) is absent, so `make test` stays green offline.
