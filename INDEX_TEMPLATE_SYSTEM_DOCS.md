# Template System Documentation Index

This document provides an organized index to all template system documentation.

## ⚠️ Important: Repository Separation

**"Why isn't most of this PR in rhiza-cli?"** 

→ **[WHY_NOT_IN_RHIZA_CLI.md](WHY_NOT_IN_RHIZA_CLI.md)** - Direct answer to this question ⭐ **NEW**

**This PR is for the rhiza repository (template definitions).** The actual CLI implementation will be in the separate rhiza-cli repository.

- **[REPOSITORY_SEPARATION.md](REPOSITORY_SEPARATION.md)** - Explains what belongs in which repository ⭐ **NEW**
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Current status and what's pending ⭐ **NEW**

## Quick Start

**New to template bundles?** Start here:

1. **[docs/TEMPLATE_BUNDLE_DISCOVERY.md](docs/TEMPLATE_BUNDLE_DISCOVERY.md)** - How rhiza discovers and parses bundles from any repository ⭐ **NEW**
2. **[TEMPLATE_SYSTEM_SUMMARY.md](TEMPLATE_SYSTEM_SUMMARY.md)** - Quick overview of the template system
3. **[README.md](README.md#-template-bundles)** - Template bundles section in main README

## For Users

**Using templates in your project:**

- **[README.md](README.md)** - Main documentation with template bundle usage examples
- **[TEMPLATE_SYSTEM_SUMMARY.md](TEMPLATE_SYSTEM_SUMMARY.md)** - Complete template system overview
- **[docs/MIGRATION_TEMPLATE_BUNDLES.md](docs/MIGRATION_TEMPLATE_BUNDLES.md)** - Migrating from path-based to template-based configuration
- **[.rhiza/templates/template.yml](.rhiza/templates/template.yml)** - Template configuration file with autocomplete comments

## For Template Creators

**Creating your own template repository:**

- **[docs/CREATING_TEMPLATE_REPOSITORY.md](docs/CREATING_TEMPLATE_REPOSITORY.md)** - Complete guide to creating custom template repositories ⭐ **NEW**
- **[docs/TEMPLATE_BUNDLE_DISCOVERY.md](docs/TEMPLATE_BUNDLE_DISCOVERY.md)** - How discovery works (important for understanding) ⭐ **NEW**
- **[.rhiza/template-bundles.yml](.rhiza/template-bundles.yml)** - Reference implementation of bundle definitions
- **[.rhiza/scripts/validate_template_bundles.py](.rhiza/scripts/validate_template_bundles.py)** - Validation tool for bundle definitions

## For rhiza-cli Developers

**Implementing template bundle support:**

- **[docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md](docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md)** - Complete implementation guide with code examples (Updated)
- **[docs/TEMPLATE_BUNDLE_DISCOVERY.md](docs/TEMPLATE_BUNDLE_DISCOVERY.md)** - Discovery mechanism details ⭐ **NEW**
- **[TEMPLATE_BUNDLES_DESIGN.md](TEMPLATE_BUNDLES_DESIGN.md)** - Design document with technical details
- **[tests/test_rhiza/test_template_bundles.py](tests/test_rhiza/test_template_bundles.py)** - Test examples

## Common Questions

### Why isn't most of this PR in rhiza-cli?

→ See **[REPOSITORY_SEPARATION.md](REPOSITORY_SEPARATION.md)** ⭐ **NEW**

**TL;DR**: This PR correctly focuses on template definitions (rhiza repo). Implementation code will be in rhiza-cli repo.

### What's the current implementation status?

→ See **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** ⭐ **NEW**

**TL;DR**: Template definitions ✅ complete. CLI implementation ⏳ pending in rhiza-cli repo.

### How does rhiza know how to parse bundles from other repos?

→ See **[docs/TEMPLATE_BUNDLE_DISCOVERY.md](docs/TEMPLATE_BUNDLE_DISCOVERY.md)** ⭐

**TL;DR**: rhiza-cli looks for `.rhiza/template-bundles.yml` at a standard location in ANY repository you specify.

### How do I create my own template repository?

→ See **[docs/CREATING_TEMPLATE_REPOSITORY.md](docs/CREATING_TEMPLATE_REPOSITORY.md)** ⭐

**TL;DR**: Create `.rhiza/template-bundles.yml` in your repository defining your bundles.

---

*Last updated: 2025-02-04*
