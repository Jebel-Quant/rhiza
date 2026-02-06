# Template Bundle System - Implementation Status

## Overview

The template bundle system allows users to select high-level feature bundles (e.g., `tests`, `docker`, `marimo`) instead of manually specifying file paths. This is a **two-repository** effort:

1. **rhiza repository** (this repo) - Template definitions ✅ COMPLETE
2. **rhiza-cli repository** - Implementation code ⏳ PENDING

## Two-Phase Implementation

```
┌─────────────────────────────────────┐
│ PHASE 1: Template Repository        │
│ (This PR in rhiza repo)             │
│                                     │
│ ✅ Define template bundles          │
│ ✅ Create documentation             │
│ ✅ Add validation scripts           │
│ ✅ Provide specifications           │
│                                     │
│ STATUS: COMPLETE                    │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ PHASE 2: CLI Implementation         │
│ (Separate PR in rhiza-cli repo)     │
│                                     │
│ ⏳ Implement bundle parsing          │
│ ⏳ Implement dependency resolution   │
│ ⏳ Implement file expansion          │
│ ⏳ Add tests and integration         │
│                                     │
│ STATUS: NOT YET STARTED             │
└─────────────────────────────────────┘
```

## Phase 1: Template Repository (✅ COMPLETE)

### What Was Done in This PR

#### 1. Template Bundle Definitions (✅ Complete)

**File**: `.rhiza/template-bundles.yml`

Defines 10 bundles covering ~100 files:
- ✅ `core` - Core infrastructure (auto-included)
- ✅ `legal` - LICENSE, CONTRIBUTING, CODE_OF_CONDUCT
- ✅ `tests` - Testing infrastructure (pytest, coverage, CI)
- ✅ `benchmarks` - Performance benchmarking
- ✅ `docker` - Docker containerization
- ✅ `marimo` - Interactive notebooks
- ✅ `book` - Documentation generation
- ✅ `devcontainer` - VS Code DevContainer
- ✅ `gitlab` - GitLab CI/CD
- ✅ `presentation` - Presentation slides

#### 2. User Documentation (✅ Complete)

- ✅ `README.md` - Updated with template system overview
- ✅ `TEMPLATE_SYSTEM_SUMMARY.md` - Quick reference for users
- ✅ `TEMPLATE_BUNDLES_DESIGN.md` - Complete design specification
- ✅ `TEMPLATE_BUNDLES_VISUALIZATION.md` - Visual diagrams
- ✅ `docs/MIGRATION_TEMPLATE_BUNDLES.md` - Migration guide for existing users
- ✅ `docs/CREATING_TEMPLATE_REPOSITORY.md` - Guide for creating other template repos
- ✅ `docs/TEMPLATE_BUNDLE_DISCOVERY.md` - How discovery works
- ✅ `docs/QUICK_REF_EXTERNAL_TEMPLATES.md` - Quick reference card
- ✅ `ANSWER_EXTERNAL_TEMPLATES.md` - Direct answers to common questions

#### 3. Example Template Configuration (✅ Complete)

**File**: `.rhiza/templates/template.yml`

Pre-configured template with:
- ✅ All available bundles listed with descriptions
- ✅ Common bundles enabled by default
- ✅ Examples of template-based, path-based, and hybrid approaches
- ✅ IDE-friendly comments for autocomplete

#### 4. Validation Infrastructure (✅ Complete)

**File**: `.rhiza/scripts/validate_template_bundles.py`

- ✅ Validates bundle structure
- ✅ Checks for circular dependencies
- ✅ Validates file references
- ✅ Checks metadata consistency
- ✅ Integrated into CI workflow

**File**: `tests/test_rhiza/test_template_bundles.py`

- ✅ Tests bundle structure
- ✅ Tests dependency declarations
- ✅ Tests file list completeness

**File**: `.github/workflows/rhiza_ci.yml`

- ✅ Added validation step to CI
- ✅ Runs on every commit

#### 5. Developer Documentation (✅ Complete)

**File**: `docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md`

Complete specification for rhiza-cli developers including:
- ✅ Discovery mechanism
- ✅ Parsing algorithm
- ✅ Dependency resolution
- ✅ File expansion
- ✅ Error handling
- ✅ Code examples (Python)
- ✅ Test cases
- ✅ Edge cases

## Phase 2: CLI Implementation (⏳ PENDING)

### What Needs to Be Done in rhiza-cli

#### 1. Bundle Discovery (⏳ Not Started)

**Location**: rhiza-cli repository

Implement code to:
- [ ] Parse `templates:` field from user's `.rhiza/template.yml`
- [ ] Fetch `.rhiza/template-bundles.yml` from specified repository
- [ ] Handle different refs (tags, branches, commits)
- [ ] Handle private repositories (authentication)
- [ ] Handle missing bundle definitions (fallback to path-based)
- [ ] Cache downloaded bundle definitions

**Expected API**:
```python
def fetch_template_bundles(repo: str, ref: str) -> dict:
    """
    Fetch template-bundles.yml from repository.
    
    Args:
        repo: Repository in format "owner/repo"
        ref: Git ref (tag, branch, or commit SHA)
    
    Returns:
        Parsed bundle definitions
    
    Raises:
        TemplateNotFoundError: If .rhiza/template-bundles.yml doesn't exist
        InvalidBundleError: If bundle definition is invalid
    """
```

#### 2. Bundle Parsing (⏳ Not Started)

**Location**: rhiza-cli repository

Implement code to:
- [ ] Parse YAML structure
- [ ] Validate schema version
- [ ] Validate bundle structure
- [ ] Extract bundle metadata
- [ ] Handle malformed YAML gracefully

**Expected API**:
```python
def parse_bundle_definitions(yaml_content: str) -> BundleRegistry:
    """
    Parse template-bundles.yml content.
    
    Args:
        yaml_content: Raw YAML content
    
    Returns:
        BundleRegistry object with all bundles
    
    Raises:
        InvalidSchemaError: If schema version is unsupported
        ParseError: If YAML is malformed
    """
```

#### 3. Dependency Resolution (⏳ Not Started)

**Location**: rhiza-cli repository

Implement code to:
- [ ] Resolve `requires` dependencies transitively
- [ ] Detect circular dependencies
- [ ] Handle missing dependencies
- [ ] Respect `recommends` (warnings, not errors)
- [ ] Auto-include `required: true` bundles (like `core`)

**Expected API**:
```python
def resolve_dependencies(
    bundles: BundleRegistry,
    selected: List[str]
) -> List[str]:
    """
    Resolve bundle dependencies.
    
    Args:
        bundles: Available bundles
        selected: User-selected bundle names
    
    Returns:
        Complete list of bundles including dependencies
    
    Raises:
        MissingDependencyError: If required dependency doesn't exist
        CircularDependencyError: If circular dependency detected
    """
```

#### 4. File Expansion (⏳ Not Started)

**Location**: rhiza-cli repository

Implement code to:
- [ ] Expand bundle names to file patterns
- [ ] Handle glob patterns (`**`, `*`)
- [ ] Merge with existing include/exclude patterns
- [ ] Remove duplicates
- [ ] Preserve user's include/exclude overrides

**Expected API**:
```python
def expand_bundles_to_files(
    bundles: BundleRegistry,
    selected: List[str]
) -> List[str]:
    """
    Expand bundle names to file patterns.
    
    Args:
        bundles: Available bundles
        selected: Resolved bundle names (after dependency resolution)
    
    Returns:
        List of file patterns to include
    """
```

#### 5. Integration (⏳ Not Started)

**Location**: rhiza-cli repository

Integrate with existing rhiza-cli:
- [ ] Update argument parser to recognize `templates:` field
- [ ] Combine template-based and path-based approaches
- [ ] Update file download logic
- [ ] Update status messages (show which bundles are being applied)
- [ ] Update error messages

#### 6. Testing (⏳ Not Started)

**Location**: rhiza-cli repository

Create comprehensive tests:
- [ ] Unit tests for bundle parsing
- [ ] Unit tests for dependency resolution
- [ ] Unit tests for file expansion
- [ ] Integration tests with real repositories
- [ ] Integration tests with multiple repositories
- [ ] Error case tests
- [ ] Edge case tests

**Test Coverage Needed**:
- Valid bundle definitions
- Invalid bundle definitions
- Missing bundle definitions (fallback)
- Circular dependencies
- Missing dependencies
- Glob pattern expansion
- Include/exclude merging
- Private repositories
- Network errors
- Caching behavior

## Timeline and Dependencies

### Critical Path

```
rhiza Repository (✅ COMPLETE)
    ↓
rhiza-cli: Bundle Discovery (⏳)
    ↓
rhiza-cli: Bundle Parsing (⏳)
    ↓
rhiza-cli: Dependency Resolution (⏳)
    ↓
rhiza-cli: File Expansion (⏳)
    ↓
rhiza-cli: Integration (⏳)
    ↓
rhiza-cli: Testing (⏳)
    ↓
FEATURE COMPLETE
```

### Estimated Effort (rhiza-cli Implementation)

- **Bundle Discovery**: 2-3 days
- **Bundle Parsing**: 1-2 days
- **Dependency Resolution**: 2-3 days
- **File Expansion**: 1-2 days
- **Integration**: 2-3 days
- **Testing**: 3-4 days

**Total**: ~11-17 days of development effort

## How to Use Right Now

### Current State (After This PR)

Users **CANNOT** use template bundles yet because rhiza-cli doesn't support them.

However, template repository creators CAN:
1. ✅ Create `.rhiza/template-bundles.yml` in their repositories
2. ✅ Validate their bundles using `.rhiza/scripts/validate_template_bundles.py`
3. ✅ Document their bundles for future use
4. ✅ Prepare for when rhiza-cli adds support

### Future State (After rhiza-cli Implementation)

Users WILL BE ABLE TO:
```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main

templates:
  - legal      # LICENSE, CONTRIBUTING, CODE_OF_CONDUCT
  - tests      # Testing infrastructure
  - docker     # Docker containerization
  - marimo     # Interactive notebooks
```

Instead of:
```yaml
# Old path-based approach
include: |
  LICENSE
  CONTRIBUTING.md
  CODE_OF_CONDUCT.md
  pytest.ini
  tests/**
  .github/workflows/rhiza_ci.yml
  docker/Dockerfile
  .rhiza/make.d/07-docker.mk
  # ... 50+ more lines
```

## Next Steps

### For rhiza Repository (This Repo)

✅ **COMPLETE** - No further action needed in this repository for basic functionality.

Future enhancements could include:
- Adding more bundles as rhiza grows
- Refining existing bundle definitions
- Adding more examples and documentation

### For rhiza-cli Repository

⏳ **ACTION REQUIRED** - Implementation needed:

1. **Immediate**: Create feature branch in rhiza-cli
2. **Step 1**: Implement bundle discovery
3. **Step 2**: Implement bundle parsing
4. **Step 3**: Implement dependency resolution
5. **Step 4**: Implement file expansion
6. **Step 5**: Integrate with existing CLI
7. **Step 6**: Add comprehensive tests
8. **Step 7**: Update rhiza-cli documentation
9. **Step 8**: Release new rhiza-cli version

### For Documentation

- [ ] Link to rhiza-cli PR when implementation starts
- [ ] Update this status document when implementation progresses
- [ ] Create migration guide for rhiza-cli updates

## References

- **Specifications**: [docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md](docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md)
- **Bundle Definitions**: [.rhiza/template-bundles.yml](.rhiza/template-bundles.yml)
- **Design Document**: [TEMPLATE_BUNDLES_DESIGN.md](TEMPLATE_BUNDLES_DESIGN.md)
- **Repository Separation**: [REPOSITORY_SEPARATION.md](REPOSITORY_SEPARATION.md)
