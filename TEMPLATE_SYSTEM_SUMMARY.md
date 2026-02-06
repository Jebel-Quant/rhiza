# Template-Centric System Implementation Summary

## Quick Overview

This document summarizes the analysis and design for implementing a template-centric include/exclude system for Rhiza.

---

## What Was Analyzed

The Rhiza repository was comprehensively analyzed to:
1. Identify all files associated with each feature (docker, book, tests, marimo, etc.)
2. Understand dependency relationships between features
3. Design a minimal implementation approach
4. Ensure backward compatibility with existing path-based configuration

---

## Key Findings

### Repository Structure is Ideal for Template Bundles

The repository contains **~95 files** organized into **8 distinct feature bundles**:

| Bundle       | Files | Standalone? | Dependencies        |
|--------------|-------|-------------|---------------------|
| core         | ~30   | Required    | -                   |
| tests        | ~30   | Yes         | -                   |
| docker       | ~5    | Yes         | -                   |
| marimo       | ~6    | Yes         | -                   |
| book         | ~5    | No          | Requires: tests, Recommends: marimo |
| devcontainer | ~4    | Yes         | -                   |
| gitlab       | ~15   | Yes         | -                   |
| presentation | ~2    | Yes         | -                   |

### Clear File Boundaries

Each feature has well-defined components:
- **Make targets**: `.rhiza/make.d/NN-feature.mk`
- **Workflows**: `.github/workflows/rhiza_feature.yml` and/or `.gitlab/workflows/rhiza_feature.yml`
- **Configuration**: Feature-specific files (Dockerfile, pytest.ini, devcontainer.json, etc.)
- **Documentation**: `docs/FEATURE.md`
- **Dependencies**: `.rhiza/requirements/feature.txt`

### Dependency Relationships

```
core (always included)
  |
  ├── tests ────┐
  |             ├── book (requires tests, recommends marimo)
  ├── marimo ───┘
  |
  ├── docker
  ├── devcontainer
  ├── gitlab
  └── presentation
```

---

## What Was Created

### 1. Design Document: `TEMPLATE_BUNDLES_DESIGN.md`

A comprehensive 400+ line design document covering:
- ✅ Complete file mappings for all 8 bundles
- ✅ Bundle dependency graph
- ✅ Implementation location recommendation (template repo)
- ✅ Backward compatibility strategy
- ✅ Example configurations
- ✅ MVP implementation checklist
- ✅ Future enhancement ideas

### 2. Bundle Definition File: `.rhiza/template-bundles.yml`

A concrete YAML file defining:
- ✅ All 8 template bundles with file lists
- ✅ Dependency relationships (requires, recommends)
- ✅ Standalone vs composite bundles
- ✅ Example configurations
- ✅ Metadata and version tracking

### 3. Analysis Entry: `REPOSITORY_ANALYSIS.md`

Added journal entry documenting:
- ✅ Repository structure assessment
- ✅ Strengths of current organization
- ✅ Weaknesses and gaps
- ✅ Implementation risks
- ✅ Template bundle readiness score: 8/10

---

## Recommended Approach

### Current State
```yaml
# .rhiza/template.yml
include: |
  docker/Dockerfile
  .rhiza/make.d/07-docker.mk
  .github/workflows/rhiza_docker.yml
  docs/DOCKER.md
```

### Desired State
```yaml
# .rhiza/template.yml
templates:
  - docker  # Automatically includes all 5 docker-related files
  - tests
  - book    # Automatically includes 'tests' (required dependency)
```

### Backward Compatible
```yaml
# Both work together!
templates:
  - docker
  - tests

include: |
  scripts/custom-file.sh  # Still works

exclude: |
  tests/benchmarks/**  # Still works
```

---

## Implementation Plan

### Phase 1: Define (This Repository) ✅ DONE

1. ✅ Create `.rhiza/template-bundles.yml` with bundle definitions
2. ✅ Document in `TEMPLATE_BUNDLES_DESIGN.md`
3. ⬜ Add template examples to README.md

### Phase 2: Implement (rhiza-cli)

1. Add `templates:` field support to config parser
2. Implement bundle resolution:
   ```python
   # Fetch bundle definitions from upstream
   bundles = fetch_from_github(
       repo="Jebel-Quant/rhiza",
       ref="main",
       path=".rhiza/template-bundles.yml"
   )
   
   # Resolve templates to file paths
   files = resolve_bundles(user_templates, bundles)
   
   # Merge with include/exclude
   materialize(files + include - exclude)
   ```
3. Implement dependency resolution (auto-include required templates)
4. Add `uvx rhiza list-templates` command
5. Maintain backward compatibility

### Phase 3: Test

1. Template-only config
2. Legacy path-only config
3. Hybrid config (both methods)
4. Dependency auto-resolution
5. Forked template repos with custom bundles

### Phase 4: Document

1. Update README with template examples
2. Update CUSTOMIZATION.md with bundle reference
3. Add template quick reference table
4. Update rhiza-cli documentation

---

## Implementation Location Decision

### ✅ Recommended: Template Repository

**Store bundle definitions in `.rhiza/template-bundles.yml` in this repo**

**Pros:**
- ✅ Single source of truth with the files themselves
- ✅ Template repos can customize bundles
- ✅ Evolves automatically with template updates
- ✅ Supports forked template repos with custom bundles
- ✅ No version coupling issues

**Cons:**
- ⚠️ rhiza-cli must fetch from remote (network dependency)
- ⚠️ Slightly more complex implementation

**Implementation:**
```python
# rhiza-cli fetches bundle definitions from upstream
bundles = fetch_template_bundles(
    repo=user_config.repository,
    ref=user_config.ref
)
```

### ❌ Alternative: rhiza-cli Hardcoded

**Store bundle definitions in rhiza-cli code**

**Pros:**
- ✅ No network fetch needed
- ✅ Simpler initial implementation

**Cons:**
- ❌ Version coupling (cli version must match template version)
- ❌ Cannot customize bundles per template repo
- ❌ Updates require cli release
- ❌ Two sources of truth that can drift

---

## Example Configurations

### Minimal Python Project
```yaml
templates:
  - tests
# Result: core + tests = ~60 files
```

### Docker Microservice
```yaml
templates:
  - tests
  - docker
# Result: core + tests + docker = ~65 files
```

### Data Science Project
```yaml
templates:
  - tests
  - marimo
  - book  # Auto-includes 'tests' (dependency)
# Result: core + tests + marimo + book = ~71 files
```

### Full-Featured Project
```yaml
templates:
  - tests
  - docker
  - marimo
  - book
  - devcontainer
# Result: core + all features = ~75 files
```

### GitLab-Focused
```yaml
templates:
  - tests
  - docker
  - gitlab  # GitLab CI instead of GitHub Actions
# Result: core + tests + docker + gitlab = ~80 files
```

### Hybrid Approach
```yaml
templates:
  - tests
  - docker

include: |
  scripts/custom-deploy.sh

exclude: |
  tests/benchmarks/**  # Don't need benchmarks
```

---

## Backward Compatibility

### Strategy: Additive Enhancement

- ✅ Existing `include:` patterns continue to work
- ✅ Existing `exclude:` patterns continue to work
- ✅ New `templates:` field is optional
- ✅ Both approaches can be used together
- ✅ No breaking changes
- ✅ Migration is opt-in

### Resolution Order

1. Expand `templates:` to file paths
2. Add `include:` patterns
3. Remove `exclude:` patterns
4. Materialize final file set

---

## Key Benefits

### For Users

- 🎯 **Simpler Configuration**: Select `docker` instead of listing 5 files
- 🔒 **Completeness**: Never forget a required file (workflow, docs, etc.)
- 🔗 **Automatic Dependencies**: Selecting `book` auto-includes `tests`
- 📚 **Discovery**: `uvx rhiza list-templates` shows available bundles
- 🛡️ **Validation**: CLI can warn about missing dependencies

### For Maintainers

- 📝 **Documentation**: Bundles are self-documenting
- 🧪 **Testing**: Can validate bundle completeness
- 🔄 **Evolution**: Add files to bundles without user config changes
- 🍴 **Forks**: Organizations can define custom bundles

---

## Next Steps

1. **Review** `.rhiza/template-bundles.yml` for accuracy
2. **Implement** bundle resolution in rhiza-cli
3. **Test** thoroughly (template-only, legacy, hybrid, dependencies, forks)
4. **Document** in README and CUSTOMIZATION.md
5. **Release** as opt-in feature in rhiza-cli

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `TEMPLATE_BUNDLES_DESIGN.md` | Comprehensive design document | ✅ Created |
| `.rhiza/template-bundles.yml` | Bundle definitions (YAML) | ✅ Created |
| `REPOSITORY_ANALYSIS.md` | Analysis entry appended | ✅ Updated |
| `TEMPLATE_SYSTEM_SUMMARY.md` | This summary document | ✅ Created |

---

## Questions Answered

### 1. What files are associated with each template?

✅ Answered in `TEMPLATE_BUNDLES_DESIGN.md` sections 1.1-1.8 and `.rhiza/template-bundles.yml`

### 2. What's the best structure for defining bundles?

✅ YAML file with bundles containing:
- `description`
- `standalone` (boolean)
- `requires` (list of required bundles)
- `recommends` (list of recommended bundles)
- `files` (list of file patterns)

### 3. Where should mapping be defined?

✅ **In this template repository** (`.rhiza/template-bundles.yml`)
- Evolves with template
- Supports forked repos
- Single source of truth

### 4. How to maintain backward compatibility?

✅ **Additive approach**:
- Keep `include:` and `exclude:` working
- Add new `templates:` field (optional)
- Both can be used together
- Resolution: templates → include → exclude

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Version coupling (cli ↔ template) | Medium | Bundle schema versioning, graceful degradation |
| Template drift | Low | Automated testing in rhiza-cli |
| User confusion | Low | Clear documentation, good examples |
| Network dependency | Low | Caching, offline fallback |
| Breaking changes | None | Backward compatible by design |

---

## Success Metrics

How to measure if implementation is successful:

1. ✅ Users can select templates instead of listing files
2. ✅ Dependencies auto-resolve (book includes tests)
3. ✅ Legacy configs continue working
4. ✅ `uvx rhiza list-templates` command works
5. ✅ Forked repos can define custom bundles
6. ✅ Documentation is clear and includes examples
7. ✅ Tests cover all scenarios (template-only, legacy, hybrid)

---

*For detailed technical design, see `TEMPLATE_BUNDLES_DESIGN.md`*  
*For bundle definitions, see `.rhiza/template-bundles.yml`*  
*For repository analysis, see `REPOSITORY_ANALYSIS.md` (2025-02-04 entry)*
