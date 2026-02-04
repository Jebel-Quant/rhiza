# Template-Centric Include/Exclude System Design

## Executive Summary

This document outlines the design for a template-centric include/exclude system for Rhiza, allowing users to select feature bundles instead of manually listing file paths.

**Current State:**
```yaml
include: |
  docker/Dockerfile
  .rhiza/make.d/07-docker.mk
  .github/workflows/rhiza_docker.yml
```

**Desired State:**
```yaml
templates:
  - docker
  - book  
  - tests
  - marimo
```

---

## 1. File Mapping Analysis

Based on repository analysis, here are the identified template bundles and their associated files:

### Template Bundle Definitions

#### 1. **core** (Always included)
Core infrastructure files that every Rhiza-based project needs.

**Files:**
- `.rhiza/rhiza.mk` - Main Makefile logic
- `.rhiza/.cfg.toml` - Rhiza configuration
- `.rhiza/.env` - Environment variables
- `.rhiza/.gitignore` - Rhiza-specific ignores
- `.rhiza/.rhiza-version` - Version tracking
- `.rhiza/make.d/00-custom-env.mk` - Custom environment variables
- `.rhiza/make.d/05-github.mk` - GitHub helper targets
- `.rhiza/make.d/06-agentic.mk` - Agentic development targets
- `.rhiza/make.d/08-docs.mk` - Documentation generation (pdoc)
- `.rhiza/scripts/**` - Core utility scripts
- `.rhiza/utils/**` - Python utility tools
- `.rhiza/docs/**` - Documentation
- `Makefile` - Root Makefile
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `.editorconfig` - Editor configuration
- `.gitignore` - Git ignore patterns
- `.python-version` - Python version specification
- `ruff.toml` - Ruff linter configuration
- `renovate.json` - Renovate dependency updates
- `pyproject.toml` - Python project metadata
- `LICENSE` - License file
- `README.md` - Main README
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Code of conduct
- `SECURITY.md` - Security policy
- `.github/workflows/rhiza_validate.yml` - Basic validation workflow
- `.github/workflows/rhiza_sync.yml` - Template sync workflow
- `.github/workflows/rhiza_pre-commit.yml` - Pre-commit validation
- `.github/workflows/rhiza_deptry.yml` - Dependency analysis
- `.github/actions/configure-git-auth/**` - Git auth action

**File Count:** ~25-30 files  
**Dependencies:** None  
**Standalone:** Required for all projects

---

#### 2. **tests**
Testing infrastructure with pytest, coverage reporting, and benchmarks.

**Files:**
- `.rhiza/make.d/01-test.mk` - Test targets (test, coverage, benchmarks)
- `.rhiza/requirements/tests.txt` - Test dependencies (pytest, coverage, etc.)
- `pytest.ini` - Pytest configuration
- `tests/**` - All test files and infrastructure
  - `tests/test_rhiza/` - Test suite directory
  - `tests/test_rhiza/conftest.py` - Pytest fixtures
  - `tests/test_rhiza/benchmarks/` - Benchmark infrastructure
  - `tests/test_rhiza/test_*.py` - All test files

**GitHub Workflows:**
- `.github/workflows/rhiza_ci.yml` - Main CI with tests
- `.github/workflows/rhiza_benchmarks.yml` - Benchmark tests
- `.github/workflows/rhiza_mypy.yml` - Type checking
- `.github/workflows/rhiza_security.yml` - Security scanning
- `.github/workflows/rhiza_codeql.yml` - CodeQL analysis

**GitLab Workflows:**
- `.gitlab/workflows/rhiza_ci.yml` - GitLab CI

**File Count:** ~30+ files  
**Dependencies:** None  
**Standalone:** Yes

---

#### 3. **docker**
Docker containerization support for building and running Docker images.

**Files:**
- `.rhiza/make.d/07-docker.mk` - Docker build/run/clean targets
- `docker/Dockerfile` - Main Dockerfile
- `docker/Dockerfile.dockerignore` - Docker ignore patterns
- `docs/DOCKER.md` - Docker documentation

**GitHub Workflows:**
- `.github/workflows/rhiza_docker.yml` - Docker lint and build validation

**File Count:** ~5 files  
**Dependencies:** None  
**Standalone:** Yes

---

#### 4. **marimo**
Interactive Marimo notebooks for data exploration and documentation.

**Files:**
- `.rhiza/make.d/03-marimo.mk` - Marimo server and validation targets
- `.rhiza/requirements/marimo.txt` - Marimo dependencies
- `book/marimo/` - Marimo notebooks directory
  - `book/marimo/notebooks/rhiza.py` - Example notebook
- `docs/MARIMO.md` - Marimo documentation

**GitHub Workflows:**
- `.github/workflows/rhiza_marimo.yml` - Notebook validation

**GitLab Templates:**
- `.gitlab/template/marimo_job_template.yml.jinja` - GitLab Marimo job template

**File Count:** ~6 files  
**Dependencies:** None (but book template can optionally include marimo outputs)  
**Standalone:** Yes

---

#### 5. **book**
Comprehensive documentation book generation combining API docs, test reports, coverage, and notebooks.

**Files:**
- `.rhiza/make.d/02-book.mk` - Book building targets
- `.rhiza/templates/minibook/custom.html.jinja2` - Custom book template
- `docs/BOOK.md` - Book documentation

**GitHub Workflows:**
- `.github/workflows/rhiza_book.yml` - Book building and GitHub Pages deployment

**GitLab Workflows:**
- `.gitlab/workflows/rhiza_book.yml` - GitLab book deployment

**File Count:** ~5 files  
**Dependencies:** 
- **Required:** `tests` (for coverage and test reports)
- **Optional:** `marimo` (for notebook exports)
- Uses `core` docs targets (pdoc)

**Standalone:** No - requires tests template

**Note:** The book template aggregates outputs from:
- API documentation (pdoc - from core)
- Test coverage reports (from tests)
- Test HTML reports (from tests)
- Marimo notebook exports (from marimo - optional)

---

#### 6. **devcontainer**
VS Code DevContainer configuration for consistent development environments.

**Files:**
- `.devcontainer/devcontainer.json` - DevContainer configuration
- `.devcontainer/bootstrap.sh` - DevContainer initialization script
- `docs/DEVCONTAINER.md` - DevContainer documentation

**GitHub Workflows:**
- `.github/workflows/rhiza_devcontainer.yml` - DevContainer build validation

**File Count:** ~3-4 files  
**Dependencies:** None  
**Standalone:** Yes

---

#### 7. **gitlab**
GitLab CI/CD pipeline configuration.

**Files:**
- `.gitlab-ci.yml` - Main GitLab CI configuration (includes workflow files)
- `.gitlab/workflows/**` - All GitLab workflow files:
  - `rhiza_book.yml`
  - `rhiza_ci.yml`
  - `rhiza_deptry.yml`
  - `rhiza_pre-commit.yml`
  - `rhiza_release.yml`
  - `rhiza_renovate.yml`
  - `rhiza_sync.yml`
  - `rhiza_validate.yml`
- `.gitlab/template/**` - GitLab job templates
- `.gitlab/*.md` - GitLab-specific documentation (COMPARISON.md, README.md, SUMMARY.md, TESTING.md)

**File Count:** ~15 files  
**Dependencies:** 
- Some workflows reference other templates (tests, book) but can work independently
- If `book` template is selected, GitLab includes book workflow
- If `tests` template is selected, GitLab includes CI workflow

**Standalone:** Yes (but enhanced with other templates)

---

#### 8. **github** (Implicit - always included with core)
GitHub Actions workflows and GitHub-specific configurations.

**Note:** This is partially included in `core` and partially distributed across feature templates. We may not need this as a separate user-selectable template since:
- Core GitHub workflows (validate, sync, pre-commit, deptry) are in `core`
- Feature-specific workflows (docker, book, marimo, devcontainer, tests) are in their respective templates

**Files in core:**
- `.github/workflows/rhiza_validate.yml`
- `.github/workflows/rhiza_sync.yml`
- `.github/workflows/rhiza_pre-commit.yml`
- `.github/workflows/rhiza_deptry.yml`
- `.github/workflows/rhiza_release.yml`
- `.github/dependabot.yml`
- `.github/copilot-instructions.md`
- `.github/agents/**`

**Files distributed to feature templates:**
- Docker workflows → `docker` template
- Book workflows → `book` template
- Marimo workflows → `marimo` template
- DevContainer workflows → `devcontainer` template
- Test workflows → `tests` template

---

## 2. Proposed Structure

### 2.1 Template Bundle Manifest

Create a new file: `.rhiza/template-bundles.yml` (or embed in existing config)

```yaml
# Template Bundle Definitions
# This file defines which files belong to each template bundle

bundles:
  core:
    description: "Core Rhiza infrastructure (always included)"
    required: true
    files:
      - .rhiza/rhiza.mk
      - .rhiza/.cfg.toml
      - .rhiza/.env
      - .rhiza/.gitignore
      - .rhiza/.rhiza-version
      - .rhiza/make.d/00-custom-env.mk
      - .rhiza/make.d/05-github.mk
      - .rhiza/make.d/06-agentic.mk
      - .rhiza/make.d/08-docs.mk
      - .rhiza/scripts/**
      - .rhiza/utils/**
      - .rhiza/docs/**
      - Makefile
      - .pre-commit-config.yaml
      - .editorconfig
      - .gitignore
      - .python-version
      - ruff.toml
      - renovate.json
      - pyproject.toml
      - LICENSE
      - README.md
      - CONTRIBUTING.md
      - CODE_OF_CONDUCT.md
      - SECURITY.md
      - .github/workflows/rhiza_validate.yml
      - .github/workflows/rhiza_sync.yml
      - .github/workflows/rhiza_pre-commit.yml
      - .github/workflows/rhiza_deptry.yml
      - .github/workflows/rhiza_release.yml
      - .github/actions/configure-git-auth/**
      - .github/dependabot.yml
      - .github/copilot-instructions.md
      - .github/agents/**

  tests:
    description: "Testing infrastructure with pytest, coverage, and benchmarks"
    requires: []
    files:
      - .rhiza/make.d/01-test.mk
      - .rhiza/requirements/tests.txt
      - pytest.ini
      - tests/**
      - .github/workflows/rhiza_ci.yml
      - .github/workflows/rhiza_benchmarks.yml
      - .github/workflows/rhiza_mypy.yml
      - .github/workflows/rhiza_security.yml
      - .github/workflows/rhiza_codeql.yml
      - .gitlab/workflows/rhiza_ci.yml

  docker:
    description: "Docker containerization support"
    requires: []
    files:
      - .rhiza/make.d/07-docker.mk
      - docker/Dockerfile
      - docker/Dockerfile.dockerignore
      - docs/DOCKER.md
      - .github/workflows/rhiza_docker.yml

  marimo:
    description: "Interactive Marimo notebooks"
    requires: []
    files:
      - .rhiza/make.d/03-marimo.mk
      - .rhiza/requirements/marimo.txt
      - book/marimo/**
      - docs/MARIMO.md
      - .github/workflows/rhiza_marimo.yml
      - .gitlab/template/marimo_job_template.yml.jinja

  book:
    description: "Documentation book generation (API docs, coverage, test reports, notebooks)"
    requires: ["tests"]  # Book needs tests for coverage/reports
    recommends: ["marimo"]  # Book works better with marimo notebooks
    files:
      - .rhiza/make.d/02-book.mk
      - .rhiza/templates/minibook/**
      - docs/BOOK.md
      - .github/workflows/rhiza_book.yml
      - .gitlab/workflows/rhiza_book.yml

  devcontainer:
    description: "VS Code DevContainer configuration"
    requires: []
    files:
      - .devcontainer/**
      - docs/DEVCONTAINER.md
      - .github/workflows/rhiza_devcontainer.yml

  gitlab:
    description: "GitLab CI/CD pipeline configuration"
    requires: []
    files:
      - .gitlab-ci.yml
      - .gitlab/workflows/**
      - .gitlab/template/**
      - .gitlab/*.md
```

### 2.2 User Configuration

**Option A: New `templates` field in `.rhiza/template.yml`**

```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main

# Template bundles to include (new feature)
templates:
  - tests
  - docker
  - book
  - marimo

# Traditional path-based includes (backward compatible)
include: |
  .github/workflows/rhiza_custom.yml
  
# Traditional path-based excludes (backward compatible)
exclude: |
  .rhiza/make.d/20-custom.mk
  tests/test_custom.py
```

**Option B: Separate configuration file**

```yaml
# .rhiza/templates.yml (new file)
bundles:
  - tests
  - docker
  - book
  - marimo
```

**Recommendation:** Option A (extend existing template.yml) for simplicity and backward compatibility.

---

## 3. Implementation Location

### Where should template bundle definitions live?

**Option 1: In the template repository (this repo - `jebel-quant/rhiza`)**

**Files:**
- `.rhiza/template-bundles.yml` - Bundle definitions
- Or embed in existing `.rhiza/.cfg.toml`

**Pros:**
- ✅ Centralized in template source
- ✅ Template maintainer controls bundle definitions
- ✅ Easy to update bundles as template evolves
- ✅ Users get latest bundle definitions when syncing
- ✅ One source of truth

**Cons:**
- ❌ rhiza-cli needs to fetch bundle definitions from remote repo
- ❌ Slightly more complex: need to fetch before materializing

---

**Option 2: In rhiza-cli repository**

**Files:**
- Hardcoded in Python code or as a bundled YAML file

**Pros:**
- ✅ rhiza-cli has immediate access
- ✅ No network fetch needed
- ✅ Simpler initial implementation

**Cons:**
- ❌ Bundle definitions are decoupled from template repo
- ❌ rhiza-cli version must match template repo version
- ❌ Users might have outdated bundle definitions
- ❌ Template repo changes require rhiza-cli updates
- ❌ Two sources of truth that can drift

---

**Option 3: Hybrid Approach**

**Files:**
- Default bundles in rhiza-cli (fallback)
- Optional bundle definitions in template repo (`.rhiza/template-bundles.yml`)

**Pros:**
- ✅ Works offline with defaults
- ✅ Can be customized per template repo
- ✅ Template repos can define their own bundles
- ✅ Graceful degradation

**Cons:**
- ❌ More complex implementation
- ❌ Potential for confusion about which definitions apply

---

**Recommendation:** **Option 1 (Template Repository)** 

**Rationale:**
1. **Single Source of Truth:** Bundle definitions should live with the files they reference
2. **Template Flexibility:** Different template repos can define different bundles
3. **Automatic Updates:** When template repo evolves, bundle definitions evolve with it
4. **Customization:** Organizations can fork Rhiza and define custom bundles

**Implementation in rhiza-cli:**
```python
# When user runs: uvx rhiza materialize

# 1. Read .rhiza/template.yml from user's project
config = read_template_config(".rhiza/template.yml")

# 2. Fetch bundle definitions from upstream template repo
bundles = fetch_bundle_definitions(
    repo=config.repository,
    ref=config.ref,
    path=".rhiza/template-bundles.yml"
)

# 3. Resolve user's selected templates to file paths
files_to_include = resolve_templates(
    user_templates=config.templates,
    bundle_definitions=bundles
)

# 4. Merge with traditional include/exclude patterns
final_includes = files_to_include + config.include
final_excludes = config.exclude

# 5. Materialize files
materialize(repo, ref, final_includes, final_excludes)
```

---

## 4. Backward Compatibility Strategy

### Approach: Additive Enhancement

The template system should support BOTH the new template-based approach AND the existing path-based approach simultaneously.

**Key Principles:**
1. ✅ Existing `include:` and `exclude:` patterns continue to work unchanged
2. ✅ New `templates:` field is optional
3. ✅ Both can be used together (templates expanded, then include/exclude applied)
4. ✅ No breaking changes to existing projects

**Migration Path:**

**Phase 1: Both approaches work**
```yaml
# .rhiza/template.yml

# Legacy approach (still works)
include: |
  .github/workflows/rhiza_custom.yml
  custom/special-file.txt

# New approach (optional)
templates:
  - tests
  - docker

# Excludes work for both
exclude: |
  .rhiza/make.d/99-local-override.mk
```

**Execution order:**
1. Resolve `templates:` to file paths
2. Add `include:` patterns
3. Subtract `exclude:` patterns
4. Materialize final file set

**Phase 2: Gradual Migration** (future)
- Documentation encourages template-based approach for common patterns
- Users can migrate at their own pace
- Legacy path-based approach remains supported indefinitely

**Phase 3: Optional Warnings** (far future)
- rhiza-cli could optionally suggest template equivalents for common path patterns
- Example: "Detected docker/Dockerfile in include - consider using 'templates: [docker]'"

---

## 5. Advanced Features (Future Enhancements)

### 5.1 Template Dependencies (Auto-include)

If user selects `book` template, automatically include `tests` (required dependency):

```yaml
templates:
  - book  # Automatically includes 'tests' as dependency
```

rhiza-cli would:
1. Read `book` template definition
2. See `requires: ["tests"]`
3. Automatically add `tests` to the inclusion list
4. Warn user: "Template 'book' requires 'tests' - adding automatically"

### 5.2 Template Recommendations (Warnings)

If user selects `book` without `marimo`:

```
⚠️  Warning: Template 'book' recommends 'marimo' for best experience
   Add to your template.yml:
   
   templates:
     - book
     - marimo  # Recommended
```

### 5.3 Template Conflicts (Detection)

If bundles have conflicting files:

```yaml
# Example: Two templates trying to provide different pytest.ini files
bundles:
  tests:
    files:
      - pytest.ini  # Version A
  
  custom-tests:
    files:
      - pytest.ini  # Version B - CONFLICT!
```

rhiza-cli would:
1. Detect the conflict
2. Warn user
3. Let last-selected template win (or prompt for choice)

### 5.4 Custom Bundle Definitions

Organizations could define custom bundles in their forks:

```yaml
# .rhiza/template-bundles.yml in organization's fork

bundles:
  # ... standard bundles ...
  
  acme-corp-standard:
    description: "ACME Corp standard Python project setup"
    requires: ["tests", "docker"]
    files:
      - .acme/corporate-policy.md
      - .acme/compliance-check.sh
```

### 5.5 Template Profiles

Pre-defined combinations for common project types:

```yaml
# .rhiza/template.yml

# Instead of listing individual templates
profile: data-science  # Includes: tests, marimo, book

# Equivalent to:
# templates:
#   - tests
#   - marimo
#   - book
```

---

## 6. Minimal Implementation Approach

### MVP (Minimum Viable Product)

**Scope:**
1. Define template bundles in `.rhiza/template-bundles.yml` in this repo
2. Add `templates:` field to `.rhiza/template.yml` (user config)
3. Implement bundle resolution in rhiza-cli:
   - Fetch bundle definitions from upstream
   - Expand templates to file paths
   - Merge with existing include/exclude
4. Maintain 100% backward compatibility

**What to build:**

**File 1: `.rhiza/template-bundles.yml` (in this repo)**
```yaml
version: 1
bundles:
  core: { description: "...", required: true, files: [...] }
  tests: { description: "...", files: [...] }
  docker: { description: "...", files: [...] }
  marimo: { description: "...", files: [...] }
  book: { description: "...", requires: ["tests"], files: [...] }
  devcontainer: { description: "...", files: [...] }
  gitlab: { description: "...", files: [...] }
```

**File 2: Updated user template config (example)**
```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main

templates:
  - tests
  - docker

include: |
  # Still works for custom files

exclude: |
  # Still works
```

**File 3: rhiza-cli changes** (pseudo-code)
```python
def materialize():
    # 1. Load user config
    user_config = load_yaml(".rhiza/template.yml")
    
    # 2. Fetch bundle definitions from template repo
    bundle_defs = fetch_from_github(
        repo=user_config.repository,
        ref=user_config.ref,
        path=".rhiza/template-bundles.yml"
    )
    
    # 3. Resolve templates to files
    template_files = []
    if "templates" in user_config:
        for template_name in user_config.templates:
            bundle = bundle_defs.bundles[template_name]
            
            # Auto-include dependencies
            if "requires" in bundle:
                for dep in bundle.requires:
                    template_files.extend(bundle_defs.bundles[dep].files)
            
            template_files.extend(bundle.files)
    
    # 4. Combine with legacy include patterns
    all_includes = template_files + parse_patterns(user_config.get("include", ""))
    
    # 5. Apply excludes
    excludes = parse_patterns(user_config.get("exclude", ""))
    
    # 6. Materialize
    sync_files(repo, ref, includes=all_includes, excludes=excludes)
```

**Testing:**
1. Test with new template-based config
2. Test with legacy path-based config
3. Test with both combined
4. Test dependency resolution (book → tests)
5. Test with custom template repo (fork)

---

## 7. File Count and Bundle Relationships

| Bundle        | Files | Requires  | Recommends | Type       |
|---------------|-------|-----------|------------|------------|
| core          | ~30   | -         | -          | Required   |
| tests         | ~30   | -         | -          | Standalone |
| docker        | ~5    | -         | -          | Standalone |
| marimo        | ~6    | -         | -          | Standalone |
| book          | ~5    | tests     | marimo     | Composite  |
| devcontainer  | ~4    | -         | -          | Standalone |
| gitlab        | ~15   | -         | -          | Standalone |

**Total unique files in repository:** ~95 files

**Bundle dependency graph:**
```
core (required)
  |
  ├── tests (standalone)
  |     └── book (requires tests, recommends marimo)
  |
  ├── docker (standalone)
  ├── marimo (standalone)
  ├── devcontainer (standalone)
  └── gitlab (standalone)
```

---

## 8. Example Configurations

### Example 1: Minimal Python Project
```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main

templates:
  - tests

# Result: core (auto) + tests = ~60 files
```

### Example 2: Docker-based Microservice
```yaml
templates:
  - tests
  - docker

# Result: core + tests + docker = ~65 files
```

### Example 3: Data Science Project
```yaml
templates:
  - tests
  - marimo
  - book

# Result: core + tests + marimo + book = ~71 files
# Note: book auto-includes tests (dependency)
```

### Example 4: Full-Featured Project
```yaml
templates:
  - tests
  - docker
  - marimo
  - book
  - devcontainer

# Result: core + all features = ~75 files
```

### Example 5: GitLab-focused Project
```yaml
templates:
  - tests
  - docker
  - gitlab  # GitLab CI instead of GitHub Actions

# Result: core + tests + docker + gitlab = ~80 files
```

### Example 6: Hybrid (Templates + Custom Paths)
```yaml
templates:
  - tests
  - docker

include: |
  scripts/custom-deploy.sh
  .github/workflows/custom-workflow.yml

exclude: |
  tests/test_benchmarks/**  # Don't need benchmarks
```

---

## 9. Documentation Updates Needed

When implementing this feature, update:

1. **README.md** - Add template-based example in Quick Start
2. **docs/CUSTOMIZATION.md** - Document template system
3. **docs/QUICK_REFERENCE.md** - Add template bundle reference table
4. **.rhiza/template-bundles.yml** - New file with bundle definitions
5. **rhiza-cli docs** - Update materialize command documentation

---

## 10. Decision Summary

### ✅ Recommendations

1. **Define bundles in template repository** (`.rhiza/template-bundles.yml`)
2. **Extend existing `.rhiza/template.yml`** with new `templates:` field
3. **Maintain full backward compatibility** with path-based approach
4. **Implement auto-dependency resolution** (e.g., book → tests)
5. **Start with MVP**: 7 bundles (core, tests, docker, marimo, book, devcontainer, gitlab)

### 📋 Implementation Checklist

- [ ] Create `.rhiza/template-bundles.yml` with bundle definitions
- [ ] Update rhiza-cli to support `templates:` field in config
- [ ] Implement bundle resolution logic
- [ ] Implement dependency resolution (requires, recommends)
- [ ] Add tests for template system
- [ ] Update documentation
- [ ] Test backward compatibility
- [ ] Release rhiza-cli update
- [ ] Update rhiza template repository

---

## Appendix: Complete Bundle Definitions

See the detailed file mappings in the main sections above for the complete list of files in each bundle.
