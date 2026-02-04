# Answer: How Does Rhiza Parse Bundles from Other Repos?

## Direct Answer

**rhiza-cli uses a standard location convention**: `.rhiza/template-bundles.yml`

Any GitHub repository with this file at this location automatically becomes a template source. No configuration or registration needed!

## The Discovery Mechanism

### 1. User Specifies Repository

```yaml
# User's .rhiza/template.yml
repository: your-org/your-repo  # ANY repository!
ref: main
templates:
  - feature-a
```

### 2. rhiza-cli Auto-Fetches

```
https://raw.githubusercontent.com/your-org/your-repo/main/.rhiza/template-bundles.yml
```

### 3. Parses and Applies

- Reads bundle definitions
- Resolves dependencies
- Expands to file patterns
- Downloads files

## Key Points

✅ **Universal** - Works with ANY GitHub repository
✅ **Standard Location** - Always `.rhiza/template-bundles.yml`
✅ **No Configuration** - No registration needed
✅ **Automatic** - rhiza-cli discovers it
✅ **Public & Private** - Both supported

## Example Repositories

**Official Rhiza:**
```yaml
repository: Jebel-Quant/rhiza
templates: [tests, docker]
```

**Your Custom Templates:**
```yaml
repository: your-org/your-templates
templates: [backend, frontend]
```

**Community Templates:**
```yaml
repository: nodejs/express-templates
templates: [typescript, jest]
```

## Creating Your Own

**3 Simple Steps:**

1. Create `.rhiza/template-bundles.yml`:
   ```yaml
   version: "1.0"
   bundles:
     my-feature:
       description: "My feature"
       files: [src/**, config/**]
   ```

2. Commit and push

3. Done! Users can reference it:
   ```yaml
   repository: your-username/your-repo
   templates: [my-feature]
   ```

## Documentation

- **Quick Answer**: [docs/TEMPLATE_BUNDLE_DISCOVERY.md](docs/TEMPLATE_BUNDLE_DISCOVERY.md)
- **Complete Guide**: [docs/CREATING_TEMPLATE_REPOSITORY.md](docs/CREATING_TEMPLATE_REPOSITORY.md)
- **Quick Reference**: [docs/QUICK_REF_EXTERNAL_TEMPLATES.md](docs/QUICK_REF_EXTERNAL_TEMPLATES.md)
- **Implementation**: [docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md](docs/IMPLEMENTATION_GUIDE_RHIZA_CLI.md)

## Summary

rhiza uses a **standard location convention** to discover template bundles:

- Any repo with `.rhiza/template-bundles.yml` = Template source
- rhiza-cli fetches from standard location automatically
- No special configuration needed
- Works with any GitHub repository (public or private)

**That's how rhiza knows how to parse bundles from other repos!** 🎉
