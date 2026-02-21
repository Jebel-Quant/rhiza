# Repository Analysis Journal

This document contains ongoing technical analysis of the Rhiza repository.

---

## 2026-02-21 — Initial Analysis Entry

### Summary

Rhiza is a mature, well-architected Python template system that has evolved significantly beyond its roadmap's stated v0.7.5 version. The repository is currently at **v0.8.1-rc.2** (per `pyproject.toml`), though the roadmap still references v0.7.5 as "Current Version". The project demonstrates production-grade engineering practices with comprehensive CI/CD, extensive documentation (25+ docs files, 9 ADRs), modular architecture, and a sophisticated template bundle system supporting 13 distinct feature sets.

The codebase shows evidence of significant recent work, with a complete repository scaffold added in commit `e972047` containing 190+ files and 24,714+ line additions. This represents a substantial implementation of the roadmap's planned features, though documentation has not been updated to reflect this progress.

### Strengths

**Architecture & Design**
- **Separation of concerns**: Clean split between `rhiza` (template repository) and `rhiza-cli` (CLI tool), documented in ADR-0005
- **Modular Makefile system**: Well-structured with 18 distinct `.mk` modules in `.rhiza/make.d/`, each focused on specific functionality (ADR-0004)
- **Template bundle abstraction**: Sophisticated bundle system defined in `.rhiza/template-bundles.yml` with 13 bundles (core, github, tests, marimo, book, docker, devcontainer, gitlab, presentation, lfs, legal, renovate, gh-aw) supporting dependency declarations and standalone flags
- **Dual CI/CD support**: Feature parity between GitHub Actions (16 workflows) and GitLab CI (8 workflows) as documented in ADR-0007

**Developer Experience**
- **Comprehensive tooling**: 60+ Makefile targets covering installation, testing, quality, documentation, releases, agentic workflows, and more
- **Modern Python stack**: uv for package management (ADR-0002), ruff for linting/formatting (ADR-0003), Python 3.11-3.14 support
- **Rich documentation**: 25 documentation files in `docs/`, 9 Architecture Decision Records, separate guides for book building, Docker, DevContainer, LFS, presentations, security testing, shell scripts, etc.
- **Interactive development**: Marimo notebooks for exploration (ADR-0008), DevContainer configuration, pre-commit hooks (ADR-0009)

**Quality & Testing**
- **Extensive test infrastructure**: 30+ test modules across `.rhiza/tests/` covering API tests, integration tests, security patterns, stress tests, structure validation, sync validation, etc.
- **Security focus**: CodeQL workflow, security testing documentation, secret scanning configuration, security patterns tests
- **Multiple validation layers**: Pre-commit hooks, deptry dependency checking, benchmark suite, property-based tests
- **Test categorization**: Separate directories for benchmarks, property tests, stress tests with dedicated READMEs

**Maintainability**
- **Technical debt tracking**: Comprehensive `docs/TECHNICAL_DEBT.md` with prioritized items (11 tracked items across Critical/High/Medium/Low)
- **Roadmap planning**: Detailed `ROADMAP.md` with quarterly release timeline through v1.0.0 and beyond
- **Changelog guidance**: `docs/CHANGELOG_GUIDE.md` with PR categorization strategy
- **TODO tracking**: `make todos` target for scanning TODO/FIXME/HACK comments

**Advanced Features**
- **GitHub Agentic Workflows (gh-aw)**: Full integration with AI-driven automation (documented in 636-line `docs/GH_AW.md`), including 10+ Makefile targets and 3 starter workflows
- **Presentation support**: Marp-based slide generation with dedicated targets
- **Git LFS integration**: Complete LFS support with installation, tracking, and status targets
- **Renovate integration**: Automated dependency updates with template sync support

### Weaknesses

**Documentation Drift**
- **Version mismatch**: `ROADMAP.md` states "Current Version: 0.7.5" but `pyproject.toml` shows "0.8.1-rc.2" — documentation is 1-2 versions behind actual implementation
- **Status accuracy**: Many features listed as "In Progress" or "Planned" in the roadmap appear to be completed based on codebase evidence (e.g., TODO tracking via `make todos` exists, GitHub project board documentation exists, changelog automation is implemented)
- **Last updated dates**: Several docs show "Last Updated: February 2026" but recent commit history shows only 2 commits since 2024-01-01, suggesting either stale dates or shallow git history

**Commit History Concerns**
- **Grafted repository**: The git history shows a grafted commit (`e972047 (grafted)`), indicating the repository history has been rewritten or truncated
- **Massive single commit**: The most recent commit adds 190 files with 24,714 insertions in a single commit, suggesting either:
  - A repository reconstruction/migration event
  - Bulk template materialization from upstream
  - Loss of granular commit history
- **Limited historical context**: Only 2 commits visible in the working tree, making it difficult to trace the evolution of features or understand when specific implementations occurred

**Clarity & Organization**
- **Bundle dependency complexity**: The template bundle system is powerful but complex — understanding which bundles require others (e.g., `book` requires `tests`) requires reading the YAML definition file
- **Makefile target proliferation**: 60+ targets is comprehensive but potentially overwhelming — grouping is good but discoverability could be improved
- **Multiple configuration files**: `.rhiza/.cfg.toml`, `.rhiza/.env`, `pyproject.toml`, `renovate.json`, `ruff.toml`, `pytest.ini` — configuration is distributed across many files

**Missing Elements**
- **No actual Python package code**: The repository is purely templates and configuration — there's no `src/` or package code, which is correct for a template repo but may confuse users expecting installable code
- **Changelog file**: No `CHANGELOG.md` or `CHANGES.md` file present despite `CHANGELOG_GUIDE.md` documentation — users must rely on GitHub releases
- **Project board**: `docs/PROJECT_BOARD.md` provides guidance but there's no evidence of an actual linked GitHub Project

### Risks / Technical Debt

**Critical**
1. **Roadmap desynchronization**: The roadmap is significantly out of date (v0.7.5 vs. v0.8.1-rc.2 reality). Users may question which features are actually available. **Action needed**: Update roadmap to reflect current state, move completed items to "Completed" section.

2. **Git history integrity**: The grafted repository and single massive commit raise questions about:
   - Reproducibility of historical states
   - Ability to bisect bugs
   - Understanding feature evolution
   - Trust in version history

**High**
3. **Template bundle documentation gap**: While `.rhiza/template-bundles.yml` is well-structured, there's no comprehensive user-facing guide explaining:
   - How bundles interact
   - What happens when you enable conflicting bundles
   - Migration paths when adding/removing bundles

4. **Test execution evidence**: While extensive test infrastructure exists (30+ test files), there's no visible evidence in the recent commits of test execution, coverage reports, or CI passing. The shallow git history makes it impossible to verify if tests are actually running and passing.

5. **Version number semantics**: The project is at `v0.8.1-rc.2` (release candidate 2) but there's no documentation about:
   - What issues were found in rc.1
   - What the criteria are for promoting to v0.8.1 stable
   - Whether rc versions are safe for production use

**Medium**
6. **Agentic workflow maturity**: The gh-aw integration is extensive (636-line doc, 10+ targets) but marked as experimental in places. The roadmap doesn't mention agentic workflows at all, suggesting this is a newer feature without clear stability guarantees.

7. **Multi-platform support**: Documentation references Linux, macOS, and DevContainer environments, but there's no explicit testing matrix or platform-specific guidance for Windows users.

8. **Dependency version bounds**: `pyproject.toml` shows no `dependencies = []` (zero runtime dependencies) but extensive dev dependencies with upper bounds (`<1.0`, `<3.0`, etc.). While conservative, this may cause conflicts in downstream projects with different version constraints.

**Low**
9. **Presentation feature adoption**: The presentation bundle exists with full Marp support, but it's unclear how many users actually need slide generation in a template system — this may be feature creep.

10. **GitLab parity maintenance**: Supporting both GitHub Actions and GitLab CI doubles the maintenance burden. The roadmap doesn't mention GitLab, suggesting it may be a recent addition without clear long-term support commitment.

### Score

**7.5/10** — Solid, well-engineered repository with notable concerns

**Rationale:**
- **+3 points**: Excellent architecture, modularity, and separation of concerns (ADRs, bundles, Makefile modules)
- **+2 points**: Comprehensive documentation and developer tooling
- **+1.5 points**: Modern Python practices (uv, ruff, type checking, security focus)
- **+1 point**: Advanced features (agentic workflows, dual CI/CD, LFS, presentations)
- **-0.5 points**: Documentation drift (version mismatch, roadmap staleness)
- **-1 point**: Git history concerns (grafted repo, massive single commit, shallow history)
- **-0.5 points**: Complexity (60+ targets, 13 bundles, distributed config)

**Not rated higher (8-9) because:**
- Cannot verify test execution or CI health due to shallow git history
- Significant version/documentation desynchronization
- Unclear release candidate status and stability guarantees
- Git history integrity questions

**Not rated lower (6) because:**
- Core architecture is sound and well-documented via ADRs
- Feature set is comprehensive and cohesive
- Modern tooling and practices are evident
- Technical debt is tracked and categorized

**Recommendation**: Update the roadmap immediately to reflect the actual v0.8.1-rc.2 state, clarify the release candidate status, and consider adding a CHANGELOG.md file for better version transparency. The repository is production-capable but needs documentation to catch up with implementation.

