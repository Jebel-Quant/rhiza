# Repository Separation: rhiza vs rhiza-cli

## Question: Why isn't most of this PR in rhiza-cli?

**Short Answer**: This PR is correctly focused on the **template repository** side (rhiza). The actual implementation code WILL BE in rhiza-cli. This PR provides the template definitions and specifications that rhiza-cli will consume.

## Understanding the Separation

### Two Repositories, Two Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│ rhiza Repository (Template Repository)                          │
│ • Defines what templates are available                          │
│ • Provides template files and structure                         │
│ • Documents how to use rhiza as a template source              │
│ • Documents how to create other template repositories          │
└─────────────────────────────────────────────────────────────────┘
                              ↓ consumed by ↓
┌─────────────────────────────────────────────────────────────────┐
│ rhiza-cli Repository (CLI Tool Implementation)                  │
│ • Implements code to fetch and parse template-bundles.yml       │
│ • Implements dependency resolution                              │
│ • Implements file downloading and application                   │
│ • Contains all the parsing/discovery logic                      │
└─────────────────────────────────────────────────────────────────┘
```

## What Belongs Where

### ✅ IN THIS REPO (rhiza - Template Repository)

**Files That BELONG Here:**

1. **`.rhiza/template-bundles.yml`**
   - Defines what bundles are available in the rhiza template
   - Example: `tests`, `docker`, `marimo`, `book`, etc.
   - This is the DATA that rhiza-cli will consume

2. **`.rhiza/templates/template.yml`**
   - Template file for users to copy
   - Shows examples of using templates

3. **Template Files Themselves**
   - All the actual `.mk` files, workflows, configs, etc.
   - These are what users get when they select bundles

4. **User-Facing Documentation**
   - `README.md` - How to use rhiza as a template
   - `TEMPLATE_SYSTEM_SUMMARY.md` - Overview of available bundles
   - `docs/CREATING_TEMPLATE_REPOSITORY.md` - How to create other template repos
   - `docs/TEMPLATE_BUNDLE_DISCOVERY.md` - How the discovery works (user perspective)

5. **Validation for This Repository**
   - `.rhiza/scripts/validate_template_bundles.py` - Validates rhiza's own bundles
   - `tests/test_rhiza/test_template_bundles.py` - Tests for rhiza's bundles

**Current Status**: ✅ **All correctly in this PR**

### ❌ SHOULD BE IN rhiza-cli (CLI Tool Repository)

**Files/Code That Belong There:**

1. **Implementation Code** (NOT in this PR, TO BE IMPLEMENTED in rhiza-cli):
   ```python
   # In rhiza-cli repository
   def fetch_template_bundles(repo, ref):
       """Fetch template-bundles.yml from any repository"""
       url = f"https://raw.githubusercontent.com/{repo}/{ref}/.rhiza/template-bundles.yml"
       # Implementation code...
   
   def resolve_dependencies(bundles, selected):
       """Resolve bundle dependencies"""
       # Implementation code...
   
   def expand_bundles_to_files(bundles, selected):
       """Expand bundle names to file patterns"""
       # Implementation code...
   ```

2. **Implementation Tests** (NOT in this PR, TO BE IMPLEMENTED in rhiza-cli):
   ```python
   # In rhiza-cli repository
   def test_fetch_template_bundles():
       """Test fetching bundles from GitHub"""
       # Test code...
   
   def test_resolve_dependencies():
       """Test dependency resolution"""
       # Test code...
   ```

3. **CLI Integration** (NOT in this PR, TO BE IMPLEMENTED in rhiza-cli):
   - Argument parsing for `templates:` field
   - Integration with existing include/exclude logic
   - Error handling and user feedback

**Current Status**: ⏳ **NOT YET IMPLEMENTED** - Waiting for rhiza-cli team

### 🤔 AMBIGUOUS: Could Be in Either Repo

**`docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md`**
- Currently in rhiza repository as a SPECIFICATION
- Acts as a design document and implementation guide
- Could be moved to rhiza-cli when implementation starts
- For now, serves as a bridge document

**Recommendation**: Keep in rhiza during design phase, copy/move to rhiza-cli when implementation begins.

## Why This Split Makes Sense

### 1. Separation of Concerns

```
Template Repository (rhiza):          CLI Tool (rhiza-cli):
┌──────────────────┐                 ┌────────────────────┐
│ WHAT templates   │  ───────────→  │ HOW to fetch and   │
│ are available    │                 │ apply templates    │
└──────────────────┘                 └────────────────────┘
```

### 2. Multiple Template Repositories

rhiza-cli needs to work with ANY template repository, not just `Jebel-Quant/rhiza`:

```
rhiza-cli
    ↓ fetches from
    ├─→ Jebel-Quant/rhiza (.rhiza/template-bundles.yml)
    ├─→ acme-corp/acme-templates (.rhiza/template-bundles.yml)
    ├─→ nodejs/nodejs-templates (.rhiza/template-bundles.yml)
    └─→ ANY repository with .rhiza/template-bundles.yml
```

### 3. Versioning Independence

- rhiza repository can add/modify bundles without changing rhiza-cli
- rhiza-cli can improve parsing logic without changing template repositories
- Multiple template repositories can evolve independently

## Current Implementation Status

### ✅ COMPLETE: Template Repository Side (This PR)

- [x] Template bundle definitions (`.rhiza/template-bundles.yml`)
- [x] Documentation for users
- [x] Documentation for other template repository creators
- [x] Example template file
- [x] Validation scripts for rhiza's bundles
- [x] Tests for rhiza's bundle structure

### ⏳ PENDING: CLI Tool Side (rhiza-cli repository)

- [ ] Parse `templates:` field from user's `.rhiza/template.yml`
- [ ] Fetch `.rhiza/template-bundles.yml` from specified repository
- [ ] Parse bundle definitions
- [ ] Resolve dependencies (handle `requires` and `recommends`)
- [ ] Expand bundle names to file patterns
- [ ] Integrate with existing include/exclude logic
- [ ] Handle errors (missing bundles, circular dependencies, etc.)
- [ ] Add tests for all parsing/discovery logic
- [ ] Update rhiza-cli documentation

## For rhiza-cli Developers

When implementing this feature in rhiza-cli:

1. **Start with** `docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md` in this repository
   - It provides the complete specification
   - Shows expected behavior and edge cases
   - Includes code examples

2. **Reference** the schema in `.rhiza/template-bundles.yml`
   - Understand the structure you'll be parsing
   - Test against real bundles from rhiza repository

3. **Test with multiple repositories**
   - Test with `Jebel-Quant/rhiza` (official)
   - Create a test repository with bundles
   - Test error handling with repositories that don't have bundles

4. **Consider copying/moving**
   - `docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md` → rhiza-cli repo
   - Keep it updated as implementation details change

## Summary

| Aspect | rhiza Repository | rhiza-cli Repository |
|--------|------------------|----------------------|
| **Purpose** | Template definitions | Template consumption |
| **Contains** | Data + Specs | Code + Tests |
| **Defines** | WHAT bundles exist | HOW to use bundles |
| **Status** | ✅ Complete (this PR) | ⏳ Pending implementation |

**This PR is correctly focused on the template repository side.** The implementation will happen in rhiza-cli, which will consume these template definitions.

## Related Documentation

- **In This Repo**:
  - [TEMPLATE_SYSTEM_SUMMARY.md](TEMPLATE_SYSTEM_SUMMARY.md) - Overview of template system
  - [docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md](docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md) - Specification for rhiza-cli
  - [docs/CREATING_TEMPLATE_REPOSITORY.md](docs/CREATING_TEMPLATE_REPOSITORY.md) - How to create template repos
  - [docs/TEMPLATE_BUNDLE_DISCOVERY.md](docs/TEMPLATE_BUNDLE_DISCOVERY.md) - How discovery works

- **To Be Created in rhiza-cli**:
  - Implementation code for bundle parsing
  - Implementation code for dependency resolution
  - Integration tests
  - CLI interface updates
