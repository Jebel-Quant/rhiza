# How Template Bundle Discovery Works

This document explains how rhiza-cli discovers and parses template bundles from ANY repository.

## TL;DR

**Question**: How does rhiza know how to parse a bundle from other repos?

**Answer**: rhiza-cli looks for `.rhiza/template-bundles.yml` at a standard location in ANY repository you specify.

## The Discovery Process

### 1. User Specifies Repository

In their project's `.rhiza/template.yml`:

```yaml
repository: your-org/your-template-repo  # ANY repository
ref: main
templates:
  - my-bundle
```

### 2. rhiza-cli Fetches Bundle Definition

rhiza-cli automatically fetches from the standard location:

```
https://raw.githubusercontent.com/{repository}/{ref}/.rhiza/template-bundles.yml
```

Example:
```
https://raw.githubusercontent.com/your-org/your-template-repo/main/.rhiza/template-bundles.yml
```

### 3. Parses Bundle Structure

rhiza-cli reads the YAML and understands:
- Available bundles
- File patterns for each bundle
- Dependencies between bundles

### 4. Expands to Files

Converts bundle names to actual file patterns and downloads them.

## Standard Location Convention

The key is the **standard location**: `.rhiza/template-bundles.yml`

- ✅ rhiza-cli ALWAYS looks in `.rhiza/template-bundles.yml`
- ✅ Works with ANY repository (yours, official rhiza, community, etc.)
- ✅ No special registration or configuration needed
- ✅ Public or private repositories supported

## Example Flow

### Official Rhiza Repository

```yaml
# User's .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main
templates:
  - tests
  - docker
```

rhiza-cli fetches:
```
https://raw.githubusercontent.com/Jebel-Quant/rhiza/main/.rhiza/template-bundles.yml
```

### Custom Repository

```yaml
# User's .rhiza/template.yml
repository: acme-corp/acme-templates
ref: v2.1.0
templates:
  - backend-api
  - frontend-spa
```

rhiza-cli fetches:
```
https://raw.githubusercontent.com/acme-corp/acme-templates/v2.1.0/.rhiza/template-bundles.yml
```

### Community Repository

```yaml
# User's .rhiza/template.yml
repository: nodejs/express-templates
ref: latest
templates:
  - typescript
  - testing
```

rhiza-cli fetches:
```
https://raw.githubusercontent.com/nodejs/express-templates/latest/.rhiza/template-bundles.yml
```

## What's in the Bundle File?

The `.rhiza/template-bundles.yml` file defines available bundles:

```yaml
version: "1.0"

bundles:
  my-bundle:
    description: "Description of the bundle"
    standalone: true
    files:
      - path/to/file.txt
      - directory/**
      - config/*.yml
```

rhiza-cli reads this to understand:
1. What bundles are available
2. Which files belong to each bundle
3. Dependencies between bundles

## Schema Validation

rhiza-cli validates the fetched bundle definition to ensure it:
- Has required fields (version, bundles, descriptions, files)
- Has valid dependencies
- Follows the schema

If validation fails, you get a clear error message.

## No Configuration Needed

**Important**: You don't need to:
- ❌ Register your repository anywhere
- ❌ Configure rhiza-cli to know about your repository
- ❌ Have special permissions (unless using private repo)
- ❌ Follow a specific repository structure (except for `.rhiza/template-bundles.yml`)

You only need:
- ✅ Create `.rhiza/template-bundles.yml` in your repository
- ✅ Users reference your repository in their `.rhiza/template.yml`

## Making Your Repository a Template Source

Three simple steps:

### Step 1: Create `.rhiza/template-bundles.yml`

```yaml
version: "1.0"

bundles:
  my-feature:
    description: "My awesome feature"
    standalone: true
    files:
      - src/**
      - config/**
```

### Step 2: Commit and Push

```bash
git add .rhiza/template-bundles.yml
git commit -m "Add template bundles"
git push
```

### Step 3: Users Can Reference It

```yaml
# Any user can now use your repository
repository: your-username/your-repo
templates:
  - my-feature
```

Done! rhiza-cli will automatically discover and use your bundles.

## Multiple Template Repositories

Users can use different template repositories for different projects:

**Project A** (Python with official rhiza templates):
```yaml
repository: Jebel-Quant/rhiza
templates: [tests, docker]
```

**Project B** (Node.js with custom templates):
```yaml
repository: my-org/nodejs-templates
templates: [typescript, jest]
```

**Project C** (Go with community templates):
```yaml
repository: golang/go-templates
templates: [modules, testing]
```

Each repository has its own `.rhiza/template-bundles.yml` that rhiza-cli discovers automatically.

## Private Repositories

For private repositories, users provide authentication:

```bash
# Set GitHub token
export GITHUB_TOKEN=ghp_xxxxx

# rhiza-cli uses it to access private repos
rhiza sync
```

rhiza-cli uses the token to fetch:
```
https://raw.githubusercontent.com/private-org/private-templates/main/.rhiza/template-bundles.yml
```

## Fallback Behavior

If `.rhiza/template-bundles.yml` doesn't exist:

1. **No templates specified**: Works normally (path-based include/exclude)
2. **Templates specified**: Error with helpful message:
   ```
   Error: Repository 'your-org/your-repo' does not have template bundles.
   
   To use template bundles, create: .rhiza/template-bundles.yml
   See: docs/CREATING_TEMPLATE_REPOSITORY.md
   ```

## Version Pinning

Users can pin to specific versions:

```yaml
repository: your-org/your-templates
ref: v1.0.0  # Specific version tag
# or
ref: main    # Latest on main branch
# or  
ref: abc123  # Specific commit
```

rhiza-cli fetches from that exact version.

## Summary

**How does rhiza know how to parse bundles from other repos?**

→ It uses a **standard location convention**: `.rhiza/template-bundles.yml`

→ Any repository at that location becomes a template source

→ No special registration or configuration needed

→ rhiza-cli automatically discovers and parses bundles from ANY repository

**Key Points:**

1. **Standard Location**: Always `.rhiza/template-bundles.yml`
2. **Universal**: Works with any GitHub repository
3. **Automatic**: No manual configuration needed
4. **Discoverable**: rhiza-cli fetches and parses automatically
5. **Validated**: Schema validation ensures correctness

## Further Reading

- **Creating Templates**: [CREATING_TEMPLATE_REPOSITORY.md](CREATING_TEMPLATE_REPOSITORY.md)
- **Implementation Details**: [IMPLEMENTATION_GUIDE_RHIZA_CLI.md](IMPLEMENTATION_GUIDE_RHIZA_CLI.md)
- **Bundle Schema**: [../. rhiza/template-bundles.yml](../.rhiza/template-bundles.yml)
- **Validation**: [../.rhiza/scripts/validate_template_bundles.py](../.rhiza/scripts/validate_template_bundles.py)
