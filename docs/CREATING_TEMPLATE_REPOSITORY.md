# Creating Your Own Template Repository

This guide explains how to create a custom template repository that can be used with rhiza-cli, allowing other projects to consume your templates just like they consume templates from `Jebel-Quant/rhiza`.

## Overview

Any GitHub repository can become a rhiza template source by:
1. Creating a `.rhiza/template-bundles.yml` file that defines template bundles
2. Following the template bundle schema
3. Organizing your files in a way that makes sense for your templates

## Quick Start

### 1. Create Template Bundle Definition

Create `.rhiza/template-bundles.yml` in your repository:

```yaml
# .rhiza/template-bundles.yml
version: "1.0"

bundles:
  # Define your bundles here
  my-feature:
    description: "My awesome feature bundle"
    standalone: true
    requires: []
    files:
      - path/to/feature/**
      - config/feature.yml
      - .github/workflows/feature.yml
```

### 2. Users Can Reference Your Repository

Users can now use your repository as a template source in their `.rhiza/template.yml`:

```yaml
# In user's project: .rhiza/template.yml
repository: your-org/your-template-repo
ref: main

templates:
  - my-feature
```

### 3. rhiza-cli Discovery Process

When a user runs rhiza-cli:

1. **Parse user config**: Reads `.rhiza/template.yml` to get `repository` and `templates`
2. **Fetch bundle definition**: Downloads `.rhiza/template-bundles.yml` from your repo:
   ```
   https://raw.githubusercontent.com/your-org/your-template-repo/main/.rhiza/template-bundles.yml
   ```
3. **Resolve dependencies**: Expands selected templates to include required bundles
4. **Expand to files**: Converts bundle names to file patterns
5. **Download files**: Fetches and applies files to user's project

## Template Bundle Schema

### Required Fields

```yaml
version: "1.0"  # Schema version (currently only 1.0)

bundles:
  bundle-name:
    description: "Human-readable description"
    standalone: true | false  # Can be used independently?
    files:
      - list/of/file/patterns
```

### Optional Fields

```yaml
bundles:
  bundle-name:
    description: "..."
    standalone: false
    
    # Required dependencies (must be included)
    requires:
      - other-bundle
    
    # Recommended bundles (suggested but not required)
    recommends:
      - suggested-bundle
    
    # File patterns (supports globs)
    files:
      - path/to/file.txt
      - directory/**
      - config/*.yml
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version (use "1.0") |
| `bundles` | object | Yes | Map of bundle definitions |
| `description` | string | Yes | Human-readable description of the bundle |
| `standalone` | boolean | Yes | Whether bundle can be used independently |
| `files` | array | Yes | List of file patterns to include |
| `requires` | array | No | Bundle names that must be included |
| `recommends` | array | No | Bundle names that are suggested |
| `required` | boolean | No | Whether bundle is always included (for core bundles) |

## Example: Creating a Custom Template Repository

### Scenario: Node.js Template Repository

Let's create a template repository for Node.js projects with various features:

#### Repository Structure

```
my-nodejs-templates/
├── .rhiza/
│   └── template-bundles.yml     # Bundle definitions
├── configs/
│   ├── eslint.config.js
│   ├── prettier.config.js
│   └── tsconfig.json
├── workflows/
│   ├── .github/
│   │   └── workflows/
│   │       ├── ci.yml
│   │       └── deploy.yml
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── scripts/
    ├── build.sh
    └── test.sh
```

#### Bundle Definition

```yaml
# .rhiza/template-bundles.yml
version: "1.0"

bundles:
  # Core bundle - always included
  core:
    description: "Core Node.js project files"
    required: true
    standalone: true
    files:
      - package.json
      - .gitignore
      - .nvmrc
      - README.md
  
  # TypeScript bundle
  typescript:
    description: "TypeScript configuration and tooling"
    standalone: true
    requires: []
    files:
      - configs/tsconfig.json
      - scripts/build-ts.sh
  
  # Linting bundle
  linting:
    description: "ESLint and Prettier configuration"
    standalone: true
    requires: []
    files:
      - configs/eslint.config.js
      - configs/prettier.config.js
      - .eslintignore
      - .prettierignore
  
  # Testing bundle
  testing:
    description: "Jest testing setup"
    standalone: true
    requires: []
    files:
      - jest.config.js
      - tests/**
      - scripts/test.sh
      - workflows/.github/workflows/ci.yml
  
  # Docker bundle
  docker:
    description: "Docker containerization"
    standalone: true
    requires: []
    recommends:
      - testing
    files:
      - docker/Dockerfile
      - docker/docker-compose.yml
      - docker/.dockerignore
      - workflows/.github/workflows/deploy.yml
  
  # Full stack bundle - combines multiple features
  fullstack:
    description: "Complete full-stack setup"
    standalone: false
    requires:
      - typescript
      - linting
      - testing
      - docker
    files:
      - scripts/start-dev.sh

# Optional: Example configurations
examples:
  minimal:
    description: "Minimal Node.js project"
    templates:
      - typescript
      - linting
  
  production:
    description: "Production-ready Node.js service"
    templates:
      - fullstack

# Optional: Metadata
metadata:
  total_bundles: 6
  repository_type: "nodejs-templates"
  maintained_by: "your-team"
```

### Using the Custom Repository

Users would configure their project to use your templates:

```yaml
# User's .rhiza/template.yml
repository: your-org/my-nodejs-templates
ref: main

templates:
  - typescript
  - linting
  - testing
  - docker
```

## Best Practices

### 1. Bundle Granularity

**Good**: Fine-grained bundles that can be mixed and matched
```yaml
bundles:
  typescript: { ... }
  jest: { ... }
  eslint: { ... }
```

**Avoid**: Monolithic bundles that include everything
```yaml
bundles:
  everything: { ... }  # Too broad
```

### 2. Clear Dependencies

**Good**: Explicit dependencies
```yaml
bundles:
  testing:
    requires: [typescript]  # Clear dependency
```

**Avoid**: Implicit assumptions
```yaml
bundles:
  testing:
    files:
      - tests/**  # Assumes TypeScript exists but doesn't declare it
```

### 3. Use Glob Patterns Wisely

**Good**: Specific patterns
```yaml
files:
  - src/**/*.ts
  - tests/**/*.test.ts
  - config/*.json
```

**Avoid**: Overly broad patterns
```yaml
files:
  - "**/*"  # Too broad, includes everything
```

### 4. Document Your Bundles

Include clear descriptions and examples:

```yaml
bundles:
  typescript:
    description: |
      TypeScript configuration with strict mode enabled.
      Includes tsconfig.json, build scripts, and type definitions.
      Requires Node.js 18+.
    standalone: true
    files: [...]
```

### 5. Version Your Template Repository

Use git tags to version your template repository:

```bash
git tag -a v1.0.0 -m "Initial template release"
git push origin v1.0.0
```

Users can pin to specific versions:

```yaml
repository: your-org/my-nodejs-templates
ref: v1.0.0  # Pin to specific version
```

## Validation

### Validate Your Bundle Definition

Use the rhiza validation script to check your bundle definition:

```bash
# Clone rhiza repo for validation tool
git clone https://github.com/Jebel-Quant/rhiza.git
cd rhiza

# Validate your template-bundles.yml
python .rhiza/scripts/validate_template_bundles.py /path/to/your/.rhiza/template-bundles.yml
```

### Common Validation Errors

1. **Missing required fields**
   ```
   Error: Bundle 'my-bundle' missing 'description'
   ```
   Solution: Add description to all bundles

2. **Invalid dependencies**
   ```
   Error: Bundle 'feature' requires non-existent bundle 'missing-bundle'
   ```
   Solution: Ensure all required/recommended bundles exist

3. **Circular dependencies**
   ```
   Error: Circular dependency detected: bundle-a → bundle-b → bundle-a
   ```
   Solution: Remove circular dependency chain

## Testing Your Template Repository

### 1. Create a Test Project

```bash
mkdir test-project
cd test-project
```

### 2. Create Template Configuration

```yaml
# .rhiza/template.yml
repository: your-org/your-template-repo
ref: main

templates:
  - your-bundle
```

### 3. Run rhiza-cli (when available)

```bash
rhiza sync
```

### 4. Verify Files

Check that expected files were downloaded:

```bash
ls -la
# Verify your template files are present
```

## Advanced Features

### Conditional Bundles

Use `recommends` for optional features:

```yaml
bundles:
  api:
    description: "REST API setup"
    recommends:
      - documentation  # Suggested but not required
      - testing       # Suggested but not required
```

### Bundle Metadata

Add metadata for tooling:

```yaml
metadata:
  total_bundles: 10
  language: "nodejs"
  framework: "express"
  maintained_by: "platform-team"
  
  file_counts:
    typescript: "~15 files"
    testing: "~20 files"
```

### Private Repositories

For private template repositories, users need GitHub authentication:

```yaml
# User's .rhiza/template.yml
repository: your-org/private-templates  # Private repo
ref: main

# User must have GITHUB_TOKEN environment variable set
templates:
  - secure-bundle
```

## Migration from Path-Based to Bundle-Based

If you already have a template repository using path-based includes, you can add bundle support while maintaining backward compatibility:

```yaml
# Users can still use old path-based approach
include: |
  src/**
  config/**

# OR use new bundle-based approach
templates:
  - myfeature

# OR mix both
templates:
  - myfeature
include: |
  custom/special-file.txt
```

## Schema Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-02 | Initial schema with bundles, dependencies, and file patterns |

Future versions may add:
- Conditional includes based on project type
- Template variables/parameters
- Multi-repository template composition

## Example Template Repositories

### Official Rhiza Templates
- **Repository**: `Jebel-Quant/rhiza`
- **Bundles**: tests, docker, marimo, book, devcontainer, gitlab, presentation
- **Use case**: Python projects with scientific computing, documentation, and CI/CD

### Community Examples

Create your own and share them! Good use cases:
- Language-specific templates (Node.js, Rust, Go, etc.)
- Framework templates (Django, Rails, Express, etc.)
- Infrastructure templates (Terraform, Kubernetes, etc.)
- Organization standards (corporate CI/CD, security policies, etc.)

## Support and Questions

- **Schema Questions**: See [docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md](IMPLEMENTATION_GUIDE_RHIZA_CLI.md)
- **Examples**: See `.rhiza/template-bundles.yml` in the rhiza repository
- **Validation**: Use `.rhiza/scripts/validate_template_bundles.py`

## Summary

Creating a template repository is simple:

1. ✅ Create `.rhiza/template-bundles.yml` in your repo
2. ✅ Define bundles with descriptions and file patterns
3. ✅ Specify dependencies using `requires` and `recommends`
4. ✅ Validate using the rhiza validation script
5. ✅ Users reference your repo in their `.rhiza/template.yml`
6. ✅ rhiza-cli automatically discovers and uses your bundles

Your template repository becomes a reusable source of project scaffolding that teams can consume declaratively!
