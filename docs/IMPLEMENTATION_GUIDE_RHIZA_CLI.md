# Implementation Guide for rhiza-cli Team

This document provides guidance for the rhiza-cli team to implement template bundle support.

## Overview

Template repositories (including `Jebel-Quant/rhiza` and any custom template repositories) can define template bundles in `.rhiza/template-bundles.yml`. This document explains how rhiza-cli should discover and process these bundles from ANY repository.

## Template Bundle Discovery

### How It Works

rhiza-cli discovers template bundles using a standard location convention:

1. **User specifies repository** in their `.rhiza/template.yml`:
   ```yaml
   repository: Jebel-Quant/rhiza  # OR any other repository
   ref: main
   templates:
     - tests
     - docker
   ```

2. **rhiza-cli fetches bundle definition** from that repository:
   ```
   https://raw.githubusercontent.com/{repository}/{ref}/.rhiza/template-bundles.yml
   ```

3. **Any repository can be a template source** if it has `.rhiza/template-bundles.yml`

### Multi-Repository Support

This design enables:
- ✅ Official rhiza templates from `Jebel-Quant/rhiza`
- ✅ Custom organizational templates from `your-org/your-templates`
- ✅ Language-specific templates from `nodejs/nodejs-templates`
- ✅ Framework templates from `django/django-templates`
- ✅ Any public or private GitHub repository

## Template Bundle File Location

**Standard Location**: `.rhiza/template-bundles.yml` (in ANY template repository)

**Format**: YAML with the following structure:

```yaml
version: "1.0"

bundles:
  tests:
    description: "Testing infrastructure..."
    standalone: true
    requires: []
    files:
      - pytest.ini
      - tests/**
      - .github/workflows/rhiza_ci.yml
      # ... more files
  
  book:
    description: "Documentation generation..."
    standalone: false
    requires:
      - tests
    recommends:
      - marimo
    files:
      - .rhiza/make.d/02-book.mk
      # ... more files
```

## User Configuration

Users will configure templates in `.rhiza/template.yml`:

```yaml
repository: Jebel-Quant/rhiza
ref: main

# New template-based approach
templates:
  - tests
  - docker
  - marimo

# Can be combined with path-based approach
include: |
  custom/my-file.yml

exclude: |
  tests/skip-this.py
```

## Implementation Steps

### 1. Parse User Configuration

Read `.rhiza/template.yml` from the user's project:

```python
def parse_user_config(config_path: Path) -> dict:
    """Parse user's template.yml configuration."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    return {
        'repository': config.get('repository'),
        'ref': config.get('ref', 'main'),
        'templates': config.get('templates', []),
        'include': config.get('include', ''),
        'exclude': config.get('exclude', ''),
    }
```

### 2. Fetch Template Bundles

Download `template-bundles.yml` from the upstream repository:

```python
def fetch_template_bundles(repository: str, ref: str) -> dict:
    """Fetch template bundles from upstream repository."""
    url = f"https://raw.githubusercontent.com/{repository}/{ref}/.rhiza/template-bundles.yml"
    response = requests.get(url)
    response.raise_for_status()
    return yaml.safe_load(response.text)
```

### 3. Resolve Dependencies

Expand template selections to include dependencies:

```python
def resolve_dependencies(
    selected_templates: list[str],
    bundles: dict
) -> list[str]:
    """Resolve template dependencies recursively."""
    resolved = set()
    to_process = set(selected_templates)
    
    while to_process:
        template = to_process.pop()
        if template in resolved:
            continue
            
        resolved.add(template)
        
        bundle = bundles.get(template, {})
        requires = bundle.get('requires', [])
        to_process.update(requires)
    
    return list(resolved)
```

### 4. Expand Templates to File Patterns

Convert template names to file patterns:

```python
def expand_templates(
    templates: list[str],
    bundles: dict
) -> list[str]:
    """Expand templates to file patterns."""
    file_patterns = []
    
    # Always include core
    if 'core' not in templates:
        templates = ['core'] + templates
    
    # Resolve dependencies
    resolved = resolve_dependencies(templates, bundles['bundles'])
    
    # Collect all file patterns
    for template in resolved:
        bundle = bundles['bundles'].get(template, {})
        file_patterns.extend(bundle.get('files', []))
    
    return file_patterns
```

### 5. Merge with Include/Exclude

Combine template files with user's include/exclude patterns:

```python
def merge_patterns(
    template_files: list[str],
    user_include: str,
    user_exclude: str
) -> tuple[list[str], list[str]]:
    """Merge template files with user includes/excludes."""
    # Parse user patterns
    include_patterns = [p.strip() for p in user_include.split('\n') if p.strip()]
    exclude_patterns = [p.strip() for p in user_exclude.split('\n') if p.strip()]
    
    # Combine
    all_includes = template_files + include_patterns
    
    return all_includes, exclude_patterns
```

### 6. Complete Flow

Put it all together:

```python
def materialize(project_path: Path):
    """Materialize templates into project."""
    # 1. Parse user config
    config = parse_user_config(project_path / '.rhiza' / 'template.yml')
    
    # 2. Fetch template bundles if templates are specified
    if config['templates']:
        bundles = fetch_template_bundles(config['repository'], config['ref'])
        
        # 3. Expand templates to files
        template_files = expand_templates(config['templates'], bundles)
    else:
        template_files = []
    
    # 4. Merge with include/exclude
    includes, excludes = merge_patterns(
        template_files,
        config['include'],
        config['exclude']
    )
    
    # 5. Download and apply files (existing logic)
    download_and_apply_files(
        repository=config['repository'],
        ref=config['ref'],
        includes=includes,
        excludes=excludes
    )
```

## Supporting Custom Template Repositories

### Discovery Mechanism

rhiza-cli MUST support ANY repository as a template source, not just `Jebel-Quant/rhiza`:

```python
def fetch_template_bundles(repository: str, ref: str) -> dict | None:
    """Fetch template bundles from any repository.
    
    Args:
        repository: GitHub repository (e.g., "your-org/your-templates")
        ref: Git ref (branch, tag, or commit)
    
    Returns:
        Dictionary with bundle definitions, or None if not found
    """
    url = f"https://raw.githubusercontent.com/{repository}/{ref}/.rhiza/template-bundles.yml"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return yaml.safe_load(response.text)
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            # Repository doesn't have template bundles - fall back to path-based
            return None
        raise
```

### Fallback Behavior

If `.rhiza/template-bundles.yml` doesn't exist:

1. **No templates specified**: Use existing path-based include/exclude logic
2. **Templates specified but no bundle file**: Error with helpful message:
   ```
   Error: Repository 'your-org/your-repo' does not have template bundles defined.
   
   To use template bundles, the repository must have:
     .rhiza/template-bundles.yml
   
   See documentation: docs/CREATING_TEMPLATE_REPOSITORY.md
   
   Alternatively, use path-based configuration:
     include: |
       path/to/files
   ```

### Example: Using Custom Template Repository

User configuration for a Node.js template repository:

```yaml
# .rhiza/template.yml
repository: nodejs-templates/express-starter
ref: v2.0.0

templates:
  - typescript
  - testing
  - docker
```

rhiza-cli will:
1. Fetch `https://raw.githubusercontent.com/nodejs-templates/express-starter/v2.0.0/.rhiza/template-bundles.yml`
2. Resolve dependencies
3. Download files from that repository

### Private Repositories

Support private repositories using GitHub authentication:

```python
def fetch_template_bundles(
    repository: str, 
    ref: str,
    github_token: str | None = None
) -> dict | None:
    """Fetch template bundles with optional authentication."""
    url = f"https://raw.githubusercontent.com/{repository}/{ref}/.rhiza/template-bundles.yml"
    
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return yaml.safe_load(response.text)
```

Users can provide authentication:
```bash
# Via environment variable
export GITHUB_TOKEN=ghp_xxxxx
rhiza sync

# Or via CLI flag
rhiza sync --github-token ghp_xxxxx
```

## Validation and Error Handling

### Bundle Validation

Validate fetched bundle definitions before use:

```python
def validate_bundle_definition(bundles: dict) -> list[str]:
    """Validate bundle definition structure.
    
    Returns list of validation errors (empty if valid).
    """
    errors = []
    
    # Check version
    if 'version' not in bundles:
        errors.append("Missing 'version' field")
    
    # Check bundles
    if 'bundles' not in bundles:
        errors.append("Missing 'bundles' field")
        return errors
    
    # Validate each bundle
    bundle_names = set(bundles['bundles'].keys())
    for name, bundle in bundles['bundles'].items():
        if 'description' not in bundle:
            errors.append(f"Bundle '{name}' missing 'description'")
        
        if 'files' not in bundle:
            errors.append(f"Bundle '{name}' missing 'files'")
        
        # Validate dependencies
        for dep in bundle.get('requires', []):
            if dep not in bundle_names:
                errors.append(f"Bundle '{name}' requires non-existent bundle '{dep}'")
        
        for dep in bundle.get('recommends', []):
            if dep not in bundle_names:
                errors.append(f"Bundle '{name}' recommends non-existent bundle '{dep}'")
    
    return errors
```

### Error Messages

Provide clear error messages:

```python
# Unknown template
Error: Template 'unknown-bundle' not found in repository 'your-org/your-repo'

Available templates:
  - typescript
  - testing
  - docker

# Circular dependency
Error: Circular dependency detected: bundle-a → bundle-b → bundle-a

# Invalid bundle definition
Error: Invalid bundle definition in 'your-org/your-repo':
  - Bundle 'testing' missing 'description'
  - Bundle 'docker' requires non-existent bundle 'missing'
```

## Testing Template Resolution

### Unit Tests

```python
def test_resolve_dependencies():
    """Test dependency resolution."""
    bundles = {
        'bundles': {
            'a': {'requires': []},
            'b': {'requires': ['a']},
            'c': {'requires': ['b']},
        }
    }
    
    # Should resolve c → b → a
    result = resolve_dependencies(['c'], bundles)
    assert set(result) == {'a', 'b', 'c'}

def test_custom_repository():
    """Test using custom template repository."""
    config = {
        'repository': 'custom-org/custom-templates',
        'ref': 'v1.0.0',
        'templates': ['feature-a', 'feature-b']
    }
    
    # Mock fetch_template_bundles to return custom bundles
    # ... test that custom repository bundles are used
```

## Documentation References

For users creating custom template repositories:
- See [docs/CREATING_TEMPLATE_REPOSITORY.md](CREATING_TEMPLATE_REPOSITORY.md)

For bundle schema details:
- See [.rhiza/template-bundles.yml](.rhiza/template-bundles.yml)

For validation:
- Use [.rhiza/scripts/validate_template_bundles.py](.rhiza/scripts/validate_template_bundles.py)

        ref=config['ref'],
        includes=includes,
        excludes=excludes,
        dest=project_path
    )
```

## Validation

Validate the template bundles file:

```python
def validate_template_bundles(bundles: dict) -> list[str]:
    """Validate template bundles structure."""
    errors = []
    
    # Check required fields
    if 'version' not in bundles:
        errors.append("Missing 'version' field")
    
    if 'bundles' not in bundles:
        errors.append("Missing 'bundles' field")
        return errors
    
    bundle_names = set(bundles['bundles'].keys())
    
    # Validate each bundle
    for name, bundle in bundles['bundles'].items():
        if 'description' not in bundle:
            errors.append(f"Bundle '{name}' missing description")
        
        if 'files' not in bundle:
            errors.append(f"Bundle '{name}' missing files")
        
        # Check dependencies exist
        for dep in bundle.get('requires', []):
            if dep not in bundle_names:
                errors.append(f"Bundle '{name}' requires non-existent '{dep}'")
    
    return errors
```

## CLI Commands

### New Commands

Add a command to list available templates:

```bash
$ uvx rhiza list-templates
Available templates:

  tests          - Testing infrastructure with pytest, coverage, and benchmarks
  docker         - Docker containerization support
  marimo         - Interactive Marimo notebooks
  book           - Documentation generation (requires: tests)
  devcontainer   - VS Code DevContainer configuration
  gitlab         - GitLab CI/CD pipelines
  presentation   - Presentation building
```

### Modified Commands

Update existing commands to support templates:

```bash
# Init with templates
$ uvx rhiza init --templates tests,docker

# Materialize with dry-run
$ uvx rhiza materialize --dry-run
Would include files from templates: tests, docker
  - pytest.ini
  - tests/**
  - docker/Dockerfile
  - .rhiza/make.d/01-test.mk
  - .rhiza/make.d/07-docker.mk
  ...
```

## Error Handling

### Template Not Found

```python
if template not in bundles['bundles']:
    raise ValueError(
        f"Template '{template}' not found. "
        f"Available: {', '.join(bundles['bundles'].keys())}"
    )
```

### Circular Dependencies

```python
def check_circular_dependencies(bundles: dict) -> list[str]:
    """Check for circular dependencies."""
    errors = []
    
    for name in bundles['bundles']:
        visited = set()
        stack = [name]
        
        while stack:
            current = stack.pop()
            if current in visited:
                errors.append(f"Circular dependency detected: {name}")
                break
            
            visited.add(current)
            bundle = bundles['bundles'].get(current, {})
            stack.extend(bundle.get('requires', []))
    
    return errors
```

## Testing

### Unit Tests

```python
def test_resolve_dependencies():
    bundles = {
        'bundles': {
            'tests': {'requires': []},
            'book': {'requires': ['tests']},
        }
    }
    
    result = resolve_dependencies(['book'], bundles['bundles'])
    assert set(result) == {'tests', 'book'}

def test_expand_templates():
    bundles = {
        'bundles': {
            'core': {'files': ['Makefile'], 'required': True},
            'tests': {'files': ['pytest.ini'], 'requires': []},
        }
    }
    
    result = expand_templates(['tests'], bundles)
    assert 'Makefile' in result  # core auto-included
    assert 'pytest.ini' in result
```

### Integration Tests

```python
def test_materialize_with_templates(tmp_path):
    # Create user config
    config = {
        'repository': 'Jebel-Quant/rhiza',
        'ref': 'main',
        'templates': ['tests', 'docker']
    }
    
    # Run materialize
    materialize(tmp_path)
    
    # Check files exist
    assert (tmp_path / 'pytest.ini').exists()
    assert (tmp_path / 'docker' / 'Dockerfile').exists()
```

## Backward Compatibility

Ensure existing path-based configurations continue to work:

```python
def materialize(project_path: Path):
    config = parse_user_config(project_path / '.rhiza' / 'template.yml')
    
    # Support both templates and path-based
    if config['templates']:
        # New template-based approach
        bundles = fetch_template_bundles(config['repository'], config['ref'])
        template_files = expand_templates(config['templates'], bundles)
    else:
        # Old path-based approach
        template_files = []
    
    # Both approaches can be combined
    includes, excludes = merge_patterns(
        template_files,
        config['include'],
        config['exclude']
    )
    
    # ... rest of materialize logic
```

## Version Requirements

- Minimum rhiza-cli version: **0.9.0** (planned)
- Template bundles version: **1.0**

## References

- Template bundles definition: `.rhiza/template-bundles.yml` in template repo
- Design document: `TEMPLATE_BUNDLES_DESIGN.md`
- Migration guide: `docs/MIGRATION_TEMPLATE_BUNDLES.md`
- Validation script: `.rhiza/scripts/validate_template_bundles.py`

## Questions?

Contact the rhiza template repository maintainers or open an issue at:
https://github.com/Jebel-Quant/rhiza/issues
