# Repository Analysis Journal

This document contains dated architectural and technical reviews of the rhiza repository.

---

## 2026-03-10 — Analysis Entry

### Summary
Rhiza is a **living template framework** for Python projects, providing synchronizable configuration templates via Make-based automation. The repository is **mature and well-engineered**, with comprehensive CI/CD (20 workflows), extensive documentation (7200+ lines across 22 MD files), modular Makefile architecture (18 `.mk` modules), and 29 test files organized into 7 categories. Version 0.8.7 represents a stable foundation with active development (826+ commits). The project demonstrates strong DevOps practices, clear separation of concerns, and thoughtful extensibility mechanisms.

### Strengths

- **Modular Architecture**: Clean separation via `.rhiza/make.d/*.mk` modules (18 files: bootstrap.mk, test.mk, github.mk, etc.) allows incremental feature adoption without coupling
- **Comprehensive Testing**: 29 test files across 7 categories (structure, api, integration, sync, deps, stress, utils) with clear separation between static validation and subprocess-based integration tests
- **Rich Documentation**: 22 markdown files (ARCHITECTURE.md, TECHNICAL_DEBT.md, TESTS.md, etc.) provide deep context; TECHNICAL_DEBT.md tracks 11 known issues with priority/effort estimates
- **Bundle System**: `template-bundles.yml` defines 13 semantic bundles (core, github, tests, marimo, book, docker, devcontainer, etc.) with dependency declarations, enabling composable project setups
- **Multi-Platform CI**: Full feature parity across GitHub Actions (16 workflows) and GitLab CI (8 workflows in `.gitlab/`), demonstrating platform independence
- **Hooks & Extensibility**: Double-colon Make targets (`pre-install::`, `post-sync::`) enable safe downstream customization without breaking template sync
- **Zero Runtime Dependencies**: `pyproject.toml` declares `dependencies = []`, making this a pure configuration/tooling framework
- **Automated Quality Gates**: `.github/hooks/session-{start,end}.sh` enforce environment validation and quality checks for GitHub Copilot sessions
- **Agentic Workflows**: Early adoption of GitHub Agentic Workflows with 3 starter templates (daily-repo-status, ci-doctor, issue-triage) and validation workflow
- **Renovate Integration**: Sophisticated `renovate.json` with custom regex managers for template versioning, enabling automated updates of `ref:` field in downstream projects
- **Version Matrix Testing**: Dynamic Python version matrix generation from `pyproject.toml` classifiers (3.11-3.14) in CI workflow

### Weaknesses

- **No Source Code**: Project contains templates and tests but **no `src/` directory** — legitimate for a template repo, but reduces code coverage meaningfulness (coverage tracks test execution, not template usage)
- **Test Execution Blocked**: `make test` fails with "Permission denied and could not request permission from user" — indicates environment issue or permission constraints during analysis
- **Missing Lock Files**: No `.lock.yml` files found despite gh-aw workflows (adr-create.md, ci-doctor.md) existing — suggests workflows not yet compiled or feature incomplete
- **Python Version Mismatch**: `.python-version` specifies `3.12`, but `pyproject.toml` claims support for 3.11-3.14 — actual runtime untested on non-3.12 versions in this environment
- **No Scripts Directory**: `.rhiza/scripts/` is empty except `__pycache__` — suggests migration away from scripts to Make targets, but may leave dead references
- **Roadmap Staleness**: ROADMAP.md references "Current Version: 0.8.1-rc.2" but `pyproject.toml` shows `0.8.7` — documentation lags reality by ~6 minor versions
- **Bootstrap Documentation Gap**: `.devcontainer/bootstrap.sh` referenced in custom instructions but not verified to exist in repository scan
- **No Benchmark Results**: `tests/benchmarks/` exists but no committed baseline results visible — performance regression detection requires manual interpretation
- **Template Validation Incomplete**: TECHNICAL_DEBT.md item #8 acknowledges "Limited validation of custom templates before sync" as medium-priority debt

### Risks / Technical Debt

- **Conflict Resolution**: TECHNICAL_DEBT.md item #1 (Critical) — Manual 3-way merge required when template updates conflict with local changes; no automatic resolution strategy
- **Performance at Scale**: Item #3 (High) — Sync operations slow for large repos; no incremental sync or caching layer implemented
- **Test Coverage Gap**: Item #2 (High) — "Limited test coverage for template synchronization edge cases" — core functionality undertested despite 29 test files
- **Complexity Growth**: 20 GitHub workflows (2056 total lines) + 18 Makefile modules creates high cognitive load for contributors; no architectural diagrams beyond docs/ARCHITECTURE.md
- **gh-aw Maturity**: Agentic workflows (adr-create.md, ci-doctor.md, issue-triage.md) lack `.lock.yml` counterparts — feature may be experimental/incomplete
- **Dependency Upper Bounds**: TECHNICAL_DEBT.md item #7 notes some dependencies lack upper bounds (e.g., `marimo>=0.18.0,<1.0` is good, but pattern not universal)
- **Private Package Assumption**: `.github/actions/configure-git-auth` and `UV_EXTRA_INDEX_URL` secret suggest reliance on private PyPI packages — may break in forks or public use
- **Hook Documentation Scattered**: Hooks mentioned in Makefile, docs/ARCHITECTURE.md, and `.rhiza/make.d/README.md` but no single source of truth for all available hooks
- **No Public Release Artifacts**: Classifier "Private :: Do Not Upload" prevents PyPI publication — downstream adoption requires git-based sync, increasing coupling

### Score

**8/10** — Solid, production-grade template framework with minor maintenance gaps.

**Rationale**:
- **+3**: Excellent modular architecture, comprehensive documentation, extensibility design
- **+2**: Strong CI/CD coverage (multi-platform, matrix testing), automated quality gates
- **+2**: Thoughtful DevOps practices (Renovate, session hooks, bundle system)
- **+1**: Active development (recent commits), transparent technical debt tracking
- **-1**: Test execution issues, missing lock files, documentation staleness
- **-1**: No actual source code to validate claims (legitimate for templates, but reduces verifiability)

**Context**: This is a **configuration/template repository**, not a library. Scoring adjusted for domain — it excels at what it aims to be (a living template system), but lacks traditional library artifacts (src/, published packages, API docs).

