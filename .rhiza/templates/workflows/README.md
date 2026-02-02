# Workflow Templates

This directory contains example GitHub Actions workflow templates that can be used as references or copied into your project.

## Available Templates

### example-ci-with-private-packages.yml

A complete example of a CI workflow configured to access private GitHub packages.

**Use cases:**
- Your project depends on private Python packages hosted on GitHub
- You need to install dependencies from private repositories during CI/CD
- You want to see a working example of Git PAT configuration

**Setup required:**
1. Create a Personal Access Token (PAT) with `repo` scope
2. Add it as a repository secret named `GH_PAT`
3. See [../docs/PRIVATE_PACKAGES.md](../docs/PRIVATE_PACKAGES.md) for detailed instructions

**Usage:**
```bash
# Copy to your project's .github/workflows/ directory
cp .rhiza/templates/workflows/example-ci-with-private-packages.yml .github/workflows/ci.yml

# Edit as needed for your project
```

## Related Documentation

- [PRIVATE_PACKAGES.md](../docs/PRIVATE_PACKAGES.md) - Complete guide to private GitHub packages
- [TOKEN_SETUP.md](../docs/TOKEN_SETUP.md) - PAT_TOKEN setup for workflow synchronization
- [CONFIG.md](../docs/CONFIG.md) - General repository configuration
