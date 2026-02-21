# Rhiza Repository Exploration Summary

**Date**: 2026-02-21  
**Repository**: `/home/runner/work/rhiza/rhiza`  
**Version**: 0.8.1-rc.2

---

## Executive Summary

**Rhiza** is a sophisticated **living template system** for Python projects that differs fundamentally from traditional one-time project generators (cookiecutter, copier). Instead of generating a snapshot, Rhiza enables **continuous synchronization** of configuration files, CI/CD workflows, and development tooling across the lifecycle of a project.

**Key Innovation**: Projects maintain a `.rhiza/template.yml` file that defines which template bundles to sync, and automated workflows (GitHub Actions, GitLab CI) can continuously pull updates from the template repository, creating pull requests for review.

---

## 1. Overall Project Structure

### Core Components

```
rhiza/
├── .rhiza/                          # Template infrastructure (core system)
│   ├── make.d/                      # Modular Makefile includes (15+ modules)
│   │   ├── bootstrap.mk             # Dependency installation (uv, gh)
│   │   ├── quality.mk               # Linting, formatting (ruff, deptry)
│   │   ├── test.mk                  # Testing (pytest, coverage, hypothesis)
│   │   ├── book.mk                  # Documentation book generation
│   │   ├── marimo.mk                # Marimo notebook support
│   │   ├── docker.mk                # Container support
│   │   ├── github.mk                # GitHub CLI helpers
│   │   ├── gh-aw.mk                 # GitHub Agentic Workflows
│   │   ├── agentic.mk               # AI copilot integration
│   │   └── releasing.mk             # Version bumping and release
│   ├── requirements/                # Dependency lock files
│   │   ├── docs.txt                 # pdoc, mkdocs
│   │   ├── marimo.txt               # Marimo notebooks
│   │   ├── tests.txt                # pytest, hypothesis, coverage
│   │   └── tools.txt                # ruff, deptry, bandit
│   ├── tests/                       # Template system tests (70+ files)
│   │   ├── api/                     # Makefile target API tests
│   │   ├── integration/             # Book, LFS, notebook tests
│   │   ├── structure/               # Layout, bundle validation
│   │   ├── security/                # Security pattern tests
│   │   ├── stress/                  # Performance tests
│   │   └── sync/                    # README, docstring validation
│   ├── docs/                        # Template documentation
│   ├── templates/                   # Minibook templates
│   ├── rhiza.mk                     # Core Makefile logic
│   ├── template-bundles.yml         # Bundle definitions (12 bundles)
│   └── .rhiza-version               # Template version (0.11.0)
│
├── .github/workflows/               # GitHub Actions CI/CD
│   ├── rhiza_ci.yml                 # Multi-version Python tests
│   ├── rhiza_sync.yml               # Template synchronization
│   ├── rhiza_validate.yml           # Structure validation
│   ├── rhiza_pre-commit.yml         # Code quality checks
│   ├── rhiza_deptry.yml             # Dependency analysis
│   ├── rhiza_release.yml            # Automated releases
│   ├── adr-create.md                # ADR creation workflow (Agentic)
│   └── ...
│
├── .gitlab/                         # GitLab CI/CD (feature parity)
│   ├── workflows/                   # GitLab workflow components
│   └── .gitlab-ci.yml               # Main pipeline definition
│
├── docs/                            # User-facing documentation
│   ├── adr/                         # Architecture Decision Records
│   │   ├── 0000-adr-template.md     # ADR template
│   │   ├── 0001-use-architecture-decision-records.md
│   │   └── README.md                # ADR index and guide
│   ├── ARCHITECTURE.md              # System architecture
│   ├── CUSTOMIZATION.md             # Customization guide
│   ├── TECHNICAL_DEBT.md            # Known limitations
│   ├── TESTS.md                     # Testing guide
│   ├── BOOK.md                      # Documentation book info
│   ├── MARIMO.md                    # Marimo notebook guide
│   ├── GLOSSARY.md                  # Terminology
│   └── mkdocs.yml                   # MkDocs config
│
├── book/                            # Documentation generation
│   └── marimo/notebooks/            # Interactive notebooks
│       └── rhiza.py                 # Example notebook
│
├── tests/                           # Project-level tests (5 files)
│   ├── property/                    # Property-based tests
│   ├── benchmarks/                  # Performance benchmarks
│   └── stress/                      # Stress tests
│
├── Makefile                         # Main entry point (40+ targets)
├── pyproject.toml                   # Python project metadata
├── ruff.toml                        # Linter configuration
├── .pre-commit-config.yaml          # Pre-commit hooks
├── .python-version                  # Python version (3.12)
├── README.md                        # Main documentation
├── ROADMAP.md                       # Future plans
├── REPOSITORY_ANALYSIS.md           # Ongoing analysis journal
└── CONTRIBUTING.md                  # Contribution guide
```

### Architecture Highlights

1. **Two-Component Design**:
   - **rhiza** (this repo): Template content (Makefiles, workflows, configs)
   - **rhiza-cli** (separate PyPI package): CLI tool (`uvx rhiza init/materialize`)

2. **Modular Makefile System**: 15+ `.mk` modules with extension hooks for customization

3. **Template Bundles**: Pre-configured sets of related files (12 bundles: core, tests, github, docker, marimo, book, etc.)

4. **Dual CI/CD**: Full feature parity between GitHub Actions and GitLab CI

5. **AI-Powered Workflows**: GitHub Agentic Workflows for ADR creation, repo analysis, change summarization

---

## 2. Architecture Decision Records (ADRs)

### Location and Structure

- **Directory**: `docs/adr/`
- **Files**:
  - `0000-adr-template.md` — Template for new ADRs
  - `0001-use-architecture-decision-records.md` — Meta-ADR documenting the ADR system
  - `README.md` — Index, creation guide, resources

### ADR Format

Each ADR follows a consistent structure:

```markdown
# [NUMBER]. [TITLE]

Date: YYYY-MM-DD

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXXX]

## Context
What is the issue motivating this decision?

## Decision
What is the change being proposed/implemented?

## Consequences
What becomes easier or more difficult?
```

### Key Characteristics

1. **Sequential Numbering**: 4-digit format (`0001`, `0002`, etc.)
2. **Naming Convention**: `XXXX-title-with-hyphens.md`
3. **Immutability**: Once accepted, ADRs are not modified; superseded by new ADRs
4. **Index Table**: `README.md` maintains searchable table:

   ```markdown
   | Number | Title | Status | Date |
   |--------|-------|--------|------|
   | [0001](0001-use-architecture-decision-records.md) | Use Architecture Decision Records | Accepted | 2026-01-01 |
   ```

### ADR Creation Workflow

**Option 1: AI-Assisted (Recommended)**

```bash
make adr
```

This triggers `.github/workflows/adr-create.md` (GitHub Agentic Workflow):
1. Prompts for ADR title and optional context
2. Determines next sequential number
3. Researches and generates comprehensive ADR content
4. Creates filename slug from title
5. Fills all template sections with substantive detail
6. Updates ADR index in `README.md`
7. Creates branch `adr/XXXX-slug`
8. Opens pull request with labels `documentation`, `adr`

**Workflow Details** (`.github/workflows/adr-create.md`):
- **Engine**: GitHub Copilot
- **Inputs**: `title` (required), `context` (optional)
- **Timeout**: 10 minutes
- **Tools**: GitHub repos, pull_requests
- **Process**: 
  - Reads current ADR index
  - Generates 3-5 paragraph Context section
  - Creates comprehensive Decision section
  - Documents Positive/Neutral/Negative consequences (2-4 bullets each)
  - Uses current date (YYYY-MM-DD)
  - Sets status to "Proposed"

**Option 2: Manual Creation**

```bash
cp docs/adr/0000-adr-template.md docs/adr/0002-example-decision.md
# Edit file manually
# Update docs/adr/README.md index
# Submit pull request
```

### ADR-Worthy Decisions

The ADR system documents:
- Project structure or organization changes
- Technology/tool adoption or removal
- Significant workflow or process changes
- Design patterns or architectural approaches
- Build, test, or deployment strategy changes

### Resources

- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's ADR article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

---

## 3. Documentation Structure (book/ Directory)

### Purpose

Rhiza generates a comprehensive **companion book** combining:
- API documentation (from source code via pdoc)
- Marimo interactive notebooks (exported to HTML)
- Test coverage reports
- Project documentation pages

### Directory Structure

```
book/
└── marimo/
    └── notebooks/
        └── rhiza.py              # Interactive Marimo notebook
```

**Note**: The `book/` directory is minimal in the template repository. Downstream projects using Rhiza will have richer content.

### Building the Book

```bash
make book
```

**Process** (defined in `.rhiza/make.d/book.mk`):

1. **Export Marimo Notebooks**: Converts `.py` notebooks to HTML
2. **Generate API Docs**: Uses `pdoc` to document source code
3. **Aggregate Sections**: Combines:
   - About section (project README)
   - API documentation
   - Notebooks
   - Coverage reports (if tests configured)
   - Additional documentation
4. **Create Minibook**: Uses Jinja2 template to generate unified book
5. **Output**: `_book/index.html` and assets

### Customization Options

#### 1. API Documentation (pdoc)

Create custom Jinja2 templates:

```bash
mkdir -p book/pdoc-templates
# Add module.html.jinja2, etc.
```

See [pdoc documentation](https://pdoc.dev/docs/pdoc.html#templates).

#### 2. Project Logo

Set `LOGO_FILE` variable in `Makefile` or `local.mk`:

```makefile
# Default: assets/rhiza-logo.svg
LOGO_FILE := assets/my-company-logo.png

# Disable logo:
LOGO_FILE :=
```

#### 3. Minibook Template

Create custom book template:

```bash
mkdir -p book/minibook-templates
# Create custom.html.jinja2
```

Default template: `.rhiza/templates/minibook/custom.html.jinja2`

### Related Documentation

- `docs/BOOK.md` — Detailed book generation guide
- `docs/MARIMO.md` — Marimo notebook integration
- `.rhiza/make.d/book.mk` — Build logic (52 lines of shell aggregation)
- `.rhiza/make.d/docs.mk` — API documentation generation

### MkDocs Integration

Rhiza also uses **MkDocs Material** for structured documentation:

**Config**: `docs/mkdocs.yml`

Features:
- Dark/light mode toggle
- Code syntax highlighting
- Mermaid diagram support
- Search functionality
- Navigation tabs

**Navigation**:
```yaml
nav:
  - Home: index.md
  - Architecture: ARCHITECTURE.md
  - Quick Reference: QUICK_REFERENCE.md
  - Customization: CUSTOMIZATION.md
  - Dependencies: DEPENDENCIES.md
  # ... etc
```

---

## 4. What Rhiza Does (Framework Purpose)

### Core Problem

Traditional project templates (cookiecutter, copier) create a **one-time snapshot**:
- Generate files at project start
- Configuration **drifts** as best practices evolve
- Manual effort required to track and apply upstream changes
- No automated way to stay current

### Rhiza's Solution: Living Templates

**Continuous Synchronization**: Projects stay aligned with evolving best practices through automated workflows.

### Key Features

#### 1. Template Synchronization

Projects define `.rhiza/template.yml`:

```yaml
repository: Jebel-Quant/rhiza
ref: v0.7.1                    # Version tag (auto-updated by Renovate)

templates:
  - core                       # Core infrastructure
  - tests                      # Testing framework
  - github                     # GitHub Actions
  - docker                     # Containerization
```

Commands:
- `uvx rhiza init` — Initialize configuration
- `uvx rhiza materialize` — Apply template updates
- Automated sync via `.github/workflows/rhiza_sync.yml`

#### 2. Template Bundles (12 Available)

| Bundle | Description | Requires | Standalone |
|--------|-------------|----------|------------|
| `core` | Core infrastructure (Makefile, linting, docs) | — | ✅ |
| `tests` | Testing (pytest, coverage, hypothesis) | — | ✅ |
| `github` | GitHub Actions workflows | `core` | ✅ |
| `gitlab` | GitLab CI/CD | `core` | ✅ |
| `docker` | Docker containerization | — | ✅ |
| `devcontainer` | VS Code Dev Container | — | ✅ |
| `marimo` | Interactive notebooks | — | ✅ |
| `book` | Documentation book generation | `tests` | ❌ |
| `presentation` | Marp presentation building | — | ✅ |
| `lfs` | Git Large File Storage | — | ✅ |
| `legal` | LICENSE, CODE_OF_CONDUCT, CONTRIBUTING | — | ✅ |
| `renovate` | Automated dependency updates | — | ✅ |
| `gh-aw` | GitHub Agentic Workflows | `github` | ✅ |

Full bundle definitions: `.rhiza/template-bundles.yml`

#### 3. Makefile Task Automation

**40+ Available Targets** (run `make help`):

**Rhiza Workflows**:
- `make sync` — Sync with template repository
- `make validate` — Validate project structure
- `make readme` — Update README with Makefile help

**Development**:
- `make install` — Install dependencies (via uv)
- `make test` — Run test suite with coverage
- `make fmt` — Format and lint code (ruff, pre-commit)
- `make todos` — Scan for TODO/FIXME/HACK comments

**Documentation**:
- `make docs` — Generate API docs (pdoc)
- `make book` — Build companion book
- `make marimo` — Start Marimo notebook server

**Releasing**:
- `make bump` — Bump version
- `make release` — Create tag and push

**Docker**:
- `make docker-build` — Build Docker image
- `make docker-run` — Run container

**GitHub Helpers**:
- `make view-prs` — List open pull requests
- `make view-issues` — List open issues
- `make failed-workflows` — Show failing workflow runs

**Agentic Workflows** (AI-powered):
- `make adr` — Create Architecture Decision Record
- `make analyse-repo` — Update repository analysis
- `make summarise-changes` — Summarize changes since last release

#### 4. CI/CD Automation

**GitHub Actions** (`.github/workflows/`):
- `rhiza_ci.yml` — Tests across Python 3.11-3.14
- `rhiza_sync.yml` — Automated template sync (creates PRs)
- `rhiza_validate.yml` — Structure validation
- `rhiza_pre-commit.yml` — Code quality checks
- `rhiza_deptry.yml` — Dependency analysis
- `rhiza_release.yml` — Automated releases
- `adr-create.md` — ADR creation (Agentic Workflow)

**GitLab CI** (`.gitlab/`):
- Feature parity with GitHub Actions
- 4-stage pipeline: `.pre`, `build`, `test`, `deploy`

#### 5. Code Quality Tools

- **Linting**: Ruff (extremely fast Python linter/formatter)
- **Type Checking**: mypy (optional)
- **Dependency Checking**: deptry (finds unused/missing dependencies)
- **Security**: bandit (security pattern scanning)
- **Pre-commit**: Automated hooks for formatting, linting

#### 6. Development Environment

- **Dev Container**: VS Code/Codespaces ready (`.devcontainer/`)
- **UV**: Fast Python package manager (replaces pip, poetry, pipenv)
- **Python Versions**: 3.11, 3.12, 3.13, 3.14 supported
- **Editor Config**: Cross-platform style consistency

### Use Cases

1. **Maintain Consistency**: Keep CI/CD, linting, and tooling aligned across multiple projects
2. **Adopt Best Practices**: Continuously benefit from upstream improvements
3. **Reduce Boilerplate**: Template bundles provide complete, tested configurations
4. **Custom Templates**: Fork Rhiza to create organization-specific templates
5. **Living Documentation**: ADRs, technical debt tracking, roadmaps

### Who Benefits

- **Teams**: Standardize tooling across organization
- **Solo Developers**: Reduce setup time for new projects
- **Open Source Maintainers**: Keep multiple repos in sync
- **Organizations**: Create custom template forks with company standards

---

## 5. ADR Templates and Examples

### Template File: `docs/adr/0000-adr-template.md`

```markdown
# [NUMBER]. [TITLE]

Date: [YYYY-MM-DD]

## Status

[Proposed | Accepted | Deprecated | Superseded by [ADR-XXXX](XXXX-title.md)]

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?
```

### Example ADR: `0001-use-architecture-decision-records.md`

**Title**: 1. Use Architecture Decision Records  
**Date**: 2026-01-01  
**Status**: Accepted  

**Context** (excerpt):
> As the Rhiza project grows and evolves, we need a systematic way to document important architectural and design decisions. Team members (both current and future) need to understand:
> - Why certain approaches were chosen over alternatives
> - What constraints or requirements influenced past decisions
> - The expected consequences of architectural choices
> - The historical context behind the current system design

**Decision** (key aspects):
1. **Location**: `docs/adr/` directory
2. **Format**: Template defined in `0000-adr-template.md`
3. **Naming**: `XXXX-title-with-hyphens.md` with 4-digit numbering
4. **Index**: `docs/adr/README.md` maintains table
5. **Immutability**: Accepted ADRs not modified; supersede with new ADRs
6. **Review**: Discussed before marking "Accepted"

**Consequences**:
- ✅ **Positive**: Knowledge preservation, better onboarding, reduced debate, audit trail
- ⚖️ **Neutral**: Process overhead, learning curve
- ❌ **Negative**: Initial setup time, index maintenance

### AI-Assisted Workflow (`.github/workflows/adr-create.md`)

**Inputs**:
- `title` (required): "Use PostgreSQL for data storage"
- `context` (optional): "Current YAML storage doesn't scale..."

**Workflow Steps**:

1. **Determine Number**: Read `docs/adr/README.md` index, increment highest number
2. **Create Slug**: "use-postgresql-for-data-storage"
3. **Generate Content**:
   - **Context**: 3-5 paragraphs researching the problem
   - **Decision**: 2-4 paragraphs detailing approach
   - **Consequences**: 
     - Positive: 2-4 benefits
     - Neutral: 2-4 trade-offs
     - Negative: 2-4 costs
4. **Create File**: `docs/adr/0002-use-postgresql-for-data-storage.md`
5. **Update Index**: Add row to README table
6. **Create PR**: Branch `adr/0002-use-postgresql-for-data-storage`, labels `documentation`, `adr`

**Example Output Structure**:

```markdown
# 2. Use PostgreSQL for Data Storage

Date: 2026-02-21

## Status

Proposed

## Context

Rhiza currently stores all configuration data in YAML files. As the system grows...
[AI generates 3-5 paragraphs based on research and provided context]

## Decision

We will adopt PostgreSQL as the primary data store for Rhiza configuration data...
[AI generates detailed decision with technical specifics]

## Consequences

### Positive

- **Improved query capabilities**: PostgreSQL enables complex queries...
- **Better concurrency**: ACID transactions prevent data corruption...
- **Scalability**: Can handle larger datasets...

### Neutral

- **Operational complexity**: Requires PostgreSQL installation...
- **Learning curve**: Team needs to learn SQL...

### Negative

- **Migration effort**: Existing YAML data must be migrated...
- **Infrastructure dependency**: Requires database server...
```

---

## Additional Resources

### Key Documentation Files

- `README.md` — Main project documentation
- `CONTRIBUTING.md` — Contribution guidelines
- `ROADMAP.md` — Future plans (v0.8-v1.0)
- `REPOSITORY_ANALYSIS.md` — Ongoing technical analysis journal (1000+ lines)
- `docs/ARCHITECTURE.md` — System architecture
- `docs/CUSTOMIZATION.md` — Customization guide
- `docs/TECHNICAL_DEBT.md` — Known limitations
- `docs/GLOSSARY.md` — Terminology reference
- `docs/QUICK_REFERENCE.md` — Command cheat sheet

### Learning Resources

- **[rhiza-education](https://github.com/Jebel-Quant/rhiza-education)** — 12-lesson tutorial covering:
  - Lessons 1-5: CI/CD concepts, UV, Python conventions
  - Lessons 6-8: Rhiza init, materialization, sync lifecycle
  - Lessons 9-12: Renovate, customization, advanced topics

### External Links

- **rhiza-cli**: [PyPI package](https://pypi.org/project/rhiza-cli/) (CLI tool)
- **GitHub**: [Jebel-Quant/rhiza](https://github.com/jebel-quant/rhiza)
- **Issues**: [GitHub Issues](https://github.com/jebel-quant/rhiza/issues)

---

## Quick Reference: Common Tasks

```bash
# Initialize Rhiza in your project
cd /path/to/your/project
uvx rhiza init
uvx rhiza materialize

# Create a new ADR (AI-assisted)
make adr

# Run tests
make test

# Format and lint code
make fmt

# Generate documentation
make docs      # API documentation
make book      # Companion book

# Start Marimo notebook server
make marimo

# Sync with template updates
make sync

# Release workflow
make bump      # Bump version
make release   # Create tag and push

# View GitHub status
make view-prs           # Open pull requests
make view-issues        # Open issues
make failed-workflows   # Recent failures

# Repository analysis
make analyse-repo       # Update REPOSITORY_ANALYSIS.md
make summarise-changes  # Summarize changes since last release
```

---

## Repository Statistics

- **Version**: 0.8.1-rc.2 (Rhiza CLI: 0.11.0)
- **Python Support**: 3.11, 3.12, 3.13, 3.14
- **Makefile Targets**: 40+
- **Template Bundles**: 12
- **GitHub Workflows**: 15+
- **GitLab Workflows**: Feature parity
- **ADRs**: 1 (system is new, more expected)
- **Documentation Files**: 25+
- **Test Files**: 75+ (`.rhiza/tests/` + `tests/`)
- **Lines in REPOSITORY_ANALYSIS.md**: 1007

---

## Current Assessment (from REPOSITORY_ANALYSIS.md)

**Score**: 7/10 — Solid, production-ready template system

**Strengths**:
- Exceptional modular Makefile architecture
- Comprehensive dual CI/CD (GitHub + GitLab)
- Strong testing infrastructure
- Innovative book compilation system
- Security scanning and code quality enforcement

**Areas for Improvement**:
- Hypothesis testing infrastructure underutilized (1 example test)
- Overlapping test directory structure (tests/ vs .rhiza/tests/)
- Shell complexity in Makefiles increases maintenance burden
- Book system may be over-engineered for current content volume

**Next Version Focus (v0.8.0)**: Quality & Maintainability
- TODO/FIXME tracking
- Technical debt documentation
- Enhanced changelog automation
- GitHub project board integration

---

## Conclusion

Rhiza is a **mature, well-architected living template system** that solves the configuration drift problem inherent in one-time project generators. Its modular design, dual CI/CD support, and AI-powered workflows (like ADR creation) demonstrate thoughtful engineering.

The **ADR system** is well-implemented with:
- Clear template and format
- AI-assisted creation workflow
- Index maintenance
- Comprehensive example (ADR-0001)

The **documentation structure** combines:
- MkDocs for structured documentation
- pdoc for API documentation
- Marimo notebooks for interactive examples
- Minibook generation for unified output

For teams looking to standardize tooling across multiple Python projects while maintaining the ability to evolve with best practices, Rhiza provides a robust foundation.

---

**Generated**: 2026-02-21  
**For**: Repository exploration and ADR creation context
