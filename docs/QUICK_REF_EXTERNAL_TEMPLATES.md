# Quick Reference: Using Other Repos as Templates

## The Answer

**Question**: How does rhiza know how to parse bundles from other repos?

**Answer**: rhiza-cli uses a **standard location convention**:
```
.rhiza/template-bundles.yml
```

Any repository with this file becomes a template source!

## How It Works

### 1. Create Template Bundle File

In your repository, create `.rhiza/template-bundles.yml`:

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

### 2. Users Reference Your Repo

Users add your repository to their `.rhiza/template.yml`:

```yaml
repository: your-org/your-repo  # Your repository!
ref: main

templates:
  - my-feature
```

### 3. rhiza-cli Auto-Discovers

rhiza-cli automatically:
1. Fetches: `https://raw.githubusercontent.com/your-org/your-repo/main/.rhiza/template-bundles.yml`
2. Parses bundles
3. Expands to files
4. Downloads and applies

**No configuration needed!**

## Key Points

✅ **Universal**: Works with ANY GitHub repository
✅ **Standard Location**: Always `.rhiza/template-bundles.yml`
✅ **No Registration**: No need to register your repository
✅ **Auto-Discovery**: rhiza-cli finds it automatically
✅ **Version Pinning**: Use branches, tags, or commits
✅ **Public & Private**: Supports both (with GitHub token for private)

## Examples

### Official Rhiza Templates
```yaml
repository: Jebel-Quant/rhiza
templates: [tests, docker]
```

### Your Custom Templates
```yaml
repository: acme-corp/acme-templates
templates: [backend, frontend]
```

### Community Templates
```yaml
repository: nodejs/express-templates
templates: [typescript, testing]
```

## More Information

- **Full Guide**: [docs/CREATING_TEMPLATE_REPOSITORY.md](docs/CREATING_TEMPLATE_REPOSITORY.md)
- **How Discovery Works**: [docs/TEMPLATE_BUNDLE_DISCOVERY.md](docs/TEMPLATE_BUNDLE_DISCOVERY.md)
- **Implementation**: [docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md](docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md)

## Summary

Creating a template repository is simple:

1. Add `.rhiza/template-bundles.yml` to your repo
2. Define your bundles
3. Users reference your repo in their config
4. Done! rhiza-cli handles the rest

**That's it!** The standard location convention makes any repository discoverable.
