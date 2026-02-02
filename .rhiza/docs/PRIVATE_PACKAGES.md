# Private GitHub Packages Setup

This document explains how to configure your repository to access private GitHub packages during CI/CD workflows and local development.

## Overview

Some Python packages may be hosted in private GitHub repositories rather than on PyPI. To access these packages during dependency installation, you need to configure Git to authenticate with GitHub using a Personal Access Token (PAT).

## Why is GH_PAT needed?

When installing Python packages that depend on private GitHub repositories, tools like `uv` and `pip` need Git to be able to clone those repositories. The standard approach is to configure Git to use a PAT for authentication with GitHub.

According to GitHub's security best practices:
- Private repositories require authentication for all operations
- A Personal Access Token with appropriate scopes is the recommended method for CI/CD authentication
- The token should be stored as a repository secret and never committed to source code

## Creating a PAT for Private Packages

Follow these steps to create a Personal Access Token with the required scopes:

### 1. Navigate to GitHub Settings

1. Go to [GitHub.com](https://github.com)
2. Click your profile picture (top-right corner)
3. Click **Settings**
4. Scroll down and click **Developer settings** (bottom of left sidebar)
5. Click **Personal access tokens** → **Tokens (classic)**

### 2. Generate a new token

1. Click **Generate new token** → **Generate new token (classic)**
2. Give your token a descriptive name, e.g., `CI Private Packages Access`
3. Set an expiration date (recommended: 90 days or less for security)

### 3. Select the required scopes

**Required scopes for private packages:**
- ✅ `repo` (Full control of private repositories)
  - This automatically includes all repo sub-scopes
  - Allows reading private repository contents

**Optional scopes:**
- `read:packages` (if using GitHub Packages registry)
- `write:packages` (if publishing to GitHub Packages)

### 4. Generate and copy the token

1. Click **Generate token** at the bottom
2. **Important:** Copy the token immediately - you won't be able to see it again!
3. Store it securely (e.g., in a password manager)

### 5. Add the token to repository secrets

1. Navigate to your repository on GitHub
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. Name: `GH_PAT`
6. Value: Paste the token you copied
7. Click **Add secret**

## Configuring Workflows

To use private GitHub packages in your CI/CD workflows, you need to configure Git before running any dependency installation commands.

### Basic Configuration Pattern

Add the following steps to your workflow **before** any `uv install` or `make` commands:

```yaml
steps:
  # 1️⃣ Checkout the code
  - uses: actions/checkout@v6.0.2

  # 2️⃣ Fail early if PAT is missing (optional but recommended)
  - name: Ensure GitHub PAT is configured
    run: |
      if [ -z "${{ secrets.GH_PAT }}" ]; then
        echo "::error::GH_PAT secret is not set!"
        exit 1
      fi

  # 3️⃣ Configure git to use the PAT for all GitHub HTTPS repos
  - name: Configure git for private GitHub repos
    run: |
      git config --global url."https://${{ secrets.GH_PAT }}@github.com/".insteadOf "https://github.com/"

  # 4️⃣ Optional: configure user (only needed if committing in CI)
  - name: Set git user (optional)
    run: |
      git config --local user.name  "github-actions[bot]"
      git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"

  # 5️⃣ Install uv
  - name: Install uv
    uses: astral-sh/setup-uv@v7.2.1
    with:
      version: "0.9.28"

  # 6️⃣ Run your build/install steps
  - name: Install dependencies
    env:
      UV_EXTRA_INDEX_URL: ${{ secrets.UV_EXTRA_INDEX_URL }}
    run: |
      make install
```

### Complete Example: CI Workflow

Here's a complete example of a CI workflow configured for private packages:

```yaml
name: CI with Private Packages

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6.0.2
        with:
          lfs: true

      # Configure Git for private packages
      - name: Configure git for private GitHub repos
        run: |
          git config --global url."https://${{ secrets.GH_PAT }}@github.com/".insteadOf "https://github.com/"

      - name: Install uv
        uses: astral-sh/setup-uv@v7.2.1
        with:
          version: "0.9.28"
          python-version: "3.12"

      - name: Run tests
        env:
          UV_EXTRA_INDEX_URL: ${{ secrets.UV_EXTRA_INDEX_URL }}
        run: |
          make test
```

## Local Development Setup

For local development, you can configure Git to use SSH or a PAT for private repositories.

### Option 1: Using SSH (Recommended for local development)

1. Set up SSH keys with GitHub: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
2. Git will automatically use SSH authentication for private repos

### Option 2: Using PAT for local development

Configure Git to use your PAT globally:

```bash
# Configure git to use PAT for GitHub HTTPS URLs
git config --global url."https://<YOUR_PAT>@github.com/".insteadOf "https://github.com/"
```

**Security Warning:** Be careful when using PATs locally. Consider using credential helpers or SSH instead.

### Option 3: Using Credential Helpers

Use Git credential helpers to store credentials securely:

```bash
# On macOS (uses Keychain)
git config --global credential.helper osxkeychain

# On Linux (uses libsecret)
git config --global credential.helper libsecret

# On Windows (uses Windows Credential Manager)
git config --global credential.helper manager
```

## Specifying Private Packages in pyproject.toml

When your project depends on private GitHub packages, specify them using Git URLs:

```toml
[project]
dependencies = [
    "public-package>=1.0.0",
    "private-package @ git+https://github.com/org/private-repo.git@v1.0.0",
]
```

You can also use SSH URLs for local development:

```toml
[project]
dependencies = [
    "private-package @ git+ssh://git@github.com/org/private-repo.git@v1.0.0",
]
```

## Combining with UV_EXTRA_INDEX_URL

The `GH_PAT` configuration works alongside `UV_EXTRA_INDEX_URL` for custom package indices:

- `GH_PAT`: Authenticates Git operations for packages from private GitHub repositories
- `UV_EXTRA_INDEX_URL`: Provides alternative package indices (e.g., private PyPI servers)

Both can be used together:

```yaml
- name: Configure git for private GitHub repos
  run: |
    git config --global url."https://${{ secrets.GH_PAT }}@github.com/".insteadOf "https://github.com/"

- name: Install dependencies
  env:
    UV_EXTRA_INDEX_URL: ${{ secrets.UV_EXTRA_INDEX_URL }}
  run: |
    make install
```

## Troubleshooting

### Error: "fatal: could not read Username"

This error indicates Git cannot authenticate with the private repository.

**Solution:** Ensure the `GH_PAT` secret is set and has the correct scopes (`repo`).

### Error: "Repository not found"

This can occur if:
- The repository is truly private and the PAT lacks access
- The PAT has been revoked or expired
- The repository name is incorrect

**Solution:** 
1. Verify the repository exists and is accessible with your PAT
2. Check the PAT hasn't expired
3. Regenerate the PAT if necessary

### Error: "Could not find a version that matches"

This may indicate:
- The package version doesn't exist
- The private repository isn't accessible
- Git authentication isn't configured

**Solution:**
1. Verify the package version exists in the repository
2. Check that Git is configured to use the PAT
3. Ensure the PAT has the required scopes

### Workflow succeeds but local install fails

Local development requires separate Git configuration.

**Solution:** Follow the [Local Development Setup](#local-development-setup) section above.

## Security Best Practices

1. **Limit scope:** Only grant the minimum required scopes (`repo` for private packages)
2. **Set expiration:** Use short-lived tokens (30-90 days) and rotate them regularly
3. **Monitor usage:** Regularly review your token usage in GitHub settings
4. **Revoke unused tokens:** Delete tokens that are no longer needed
5. **Use separate tokens:** Don't reuse tokens across multiple projects
6. **Never commit tokens:** Always use secrets for CI/CD
7. **Use SSH locally:** Prefer SSH keys over PATs for local development

## Alternative: GitHub Packages Registry

Instead of Git URLs, you can publish private packages to GitHub Packages and use it as a package index:

```toml
[[tool.uv.index]]
url = "https://pypi.org/simple"

[[tool.uv.index]]
url = "https://<YOUR_PAT>@ghcr.io/org/_/pypi/simple"
name = "github-packages"
```

This approach may be more maintainable for organizations with many private packages.

## Related Documentation

- [TOKEN_SETUP.md](TOKEN_SETUP.md) - Setup for PAT_TOKEN (workflow permissions)
- [CONFIG.md](CONFIG.md) - General repository configuration
- [GitHub: Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [UV Documentation](https://docs.astral.sh/uv/)
