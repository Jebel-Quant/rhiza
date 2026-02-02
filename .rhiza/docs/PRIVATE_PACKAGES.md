# Using Private GitHub Packages

This document explains how to configure your project to use private GitHub packages from the same organization as dependencies.

## Quick Start

If you're using Rhiza's template workflows, you need to configure a Personal Access Token (PAT) for cross-repository access. All Rhiza workflows use `secrets.PRIVATE_REPO_TOKEN` to access private repositories.

**Setup Steps:**

1. Create a Personal Access Token (PAT) with `repo` scope (see instructions below)
2. Add it as a repository secret named `PRIVATE_REPO_TOKEN`
3. Add your private package to `pyproject.toml`:

```toml
[tool.uv.sources]
my-package = { git = "https://github.com/jebel-quant/my-package.git", rev = "v1.0.0" }
```

The workflows will handle authentication automatically using your `PRIVATE_REPO_TOKEN`.

## Detailed Guide

### Problem

When your project depends on private GitHub repositories, you need to authenticate to access them. SSH keys work locally but are complex to set up in CI/CD environments. HTTPS with tokens is simpler and more secure for automated workflows.

## Solution

Use HTTPS URLs with token authentication instead of SSH for git dependencies.

### 1. Configure Dependencies in pyproject.toml

Instead of using SSH URLs like `git@github.com:org/repo.git`, use HTTPS URLs:

```toml
[tool.uv.sources]
my-package = { git = "https://github.com/jebel-quant/my-package.git", rev = "v1.0.0" }
another-package = { git = "https://github.com/jebel-quant/another-package.git", tag = "v2.0.0" }
```

**Key points:**
- Use `https://github.com/` instead of `git@github.com:`
- Specify version using `rev`, `tag`, or `branch` parameter
- No token is included in the URL itself (git config handles authentication)

### 2. Git Authentication in CI

**All Rhiza workflows require a Personal Access Token (PAT) for private package access.** 

You need to:

1. **Create a PAT** with `repo` scope or fine-grained token with read access to your private repositories
2. **Add it as a repository secret** named `PRIVATE_REPO_TOKEN` in your repository settings
3. **Workflows will automatically use it** - all Rhiza workflows are configured to use `secrets.PRIVATE_REPO_TOKEN`

You can verify the configuration in any Rhiza workflow file (e.g., `.github/workflows/rhiza_ci.yml`):

```yaml
- name: Configure git auth for private packages
  uses: ./.github/actions/configure-git-auth
  with:
    token: ${{ secrets.PRIVATE_REPO_TOKEN }}
```

Or for container-based workflows:

```yaml
- name: Configure git auth for private packages
  run: |
    git config --global url."https://${{ secrets.PRIVATE_REPO_TOKEN }}@github.com/".insteadOf "https://github.com/"
```

**For custom workflows** (not synced from Rhiza), add the git authentication step yourself:

```yaml
- name: Configure git auth for private packages
  run: |
    git config --global url."https://${{ secrets.PRIVATE_REPO_TOKEN }}@github.com/".insteadOf "https://github.com/"
```

This configuration tells git to automatically inject your PAT into all HTTPS GitHub URLs.

### 3. Using the Composite Action (Custom Workflows)

For custom workflows, you can use Rhiza's composite action instead of inline commands:

```yaml
- name: Configure git auth for private packages
  uses: ./.github/actions/configure-git-auth
  with:
    token: ${{ secrets.PRIVATE_REPO_TOKEN }}
```

This is cleaner and more maintainable than inline git config commands.

### 4. Complete Workflow Example

Here's a complete example of a GitHub Actions workflow that uses private packages:

```yaml
name: CI with Private Packages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          version: "0.9.28"

      - name: Configure git auth for private packages
        run: |
          git config --global url."https://${{ secrets.PRIVATE_REPO_TOKEN }}@github.com/".insteadOf "https://github.com/"

      - name: Install dependencies
        run: |
          uv sync --frozen

      - name: Run tests
        run: |
          uv run pytest
```

## Token Scopes

### Creating a Personal Access Token (PAT)

Since the default `GITHUB_TOKEN` only has access to the current repository, you need to create a Personal Access Token with cross-repository access:

**Steps to create a PAT:**

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a descriptive name (e.g., "Private Package Access for [repo-name]")
4. Set expiration (recommended: 90 days or less for better security; you can set up automatic token rotation)
5. Select scopes:
   - ✅ `repo` (Full control of private repositories)
6. Click "Generate token"
7. Copy the token immediately (you won't be able to see it again)

**Add the token to your repository:**

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PRIVATE_REPO_TOKEN`
4. Value: Paste your PAT
5. Click "Add secret"

### Alternative: Fine-grained Personal Access Token

For better security, you can use a fine-grained token:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Fill in token details:
   - Name: "Private Package Access for [repo-name]"
   - Expiration: Your preference
   - Resource owner: Select the organization
   - Repository access: Choose "Only select repositories" and select the private packages you need
4. Repository permissions:
   - ✅ Contents: Read-only
5. Generate token and add it to your repository secrets as `PRIVATE_REPO_TOKEN`

### Why not use GITHUB_TOKEN?

The automatic `GITHUB_TOKEN` provided by GitHub Actions:
- ❌ Only has read access to the current repository
- ❌ Cannot access other repositories, even in the same organization
- ❌ Will fail when trying to clone private dependencies

For private package dependencies, you **must** use a PAT with cross-repository access.

## Local Development

For local development, you have several options:

### Option 1: Use GitHub CLI (Recommended)

```bash
# Install gh CLI
brew install gh  # macOS
# or: apt install gh  # Ubuntu/Debian

# Authenticate
gh auth login

# Configure git
gh auth setup-git
```

The GitHub CLI automatically handles git authentication for private repositories.

### Option 2: Use Personal Access Token

```bash
# Create a PAT with 'repo' scope at:
# https://github.com/settings/tokens

# Configure git
git config --global url."https://YOUR_TOKEN@github.com/".insteadOf "https://github.com/"
```

**Security Note:** Be careful not to commit this configuration. It's better to use `gh` CLI or SSH keys for local development.

### Option 3: Use SSH (Local Only)

For local development, you can continue using SSH:

```toml
[tool.uv.sources]
my-package = { git = "ssh://git@github.com/jebel-quant/my-package.git", rev = "v1.0.0" }
```

However, this won't work in CI without additional SSH key setup.

## Troubleshooting

### Error: "fatal: could not read Username"

This means git cannot find authentication credentials. Ensure:
1. The git config step runs **before** `uv sync`
2. The token has proper permissions
3. The repository URL uses HTTPS format

### Error: "Repository not found" or "403 Forbidden"

This means the token doesn't have access to the repository. Check:
1. The repository is in the same organization (for `GITHUB_TOKEN`)
2. Or use a PAT with `repo` scope (for different organizations)
3. The token hasn't expired

### Error: "Couldn't resolve host 'github.com'"

This is a network issue, not authentication. Check your network connection.

## Best Practices

1. **Use HTTPS URLs** in `pyproject.toml` for better CI/CD compatibility
2. **Rely on `GITHUB_TOKEN`** for same-org packages (automatic and secure)
3. **Pin versions** using `rev`, `tag`, or specific commit SHA for reproducibility
4. **Use `gh` CLI** for local development (easier than managing tokens)
5. **Keep tokens secure** - never commit them to the repository

## Related Documentation

- [TOKEN_SETUP.md](TOKEN_SETUP.md) - Setting up Personal Access Tokens
- [GitHub Actions: Automatic token authentication](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [uv: Git dependencies](https://docs.astral.sh/uv/concepts/dependencies/#git-dependencies)
