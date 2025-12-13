# 🛠️ Rhiza

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python versions](https://img.shields.io/badge/Python-3.11%20•%203.12%20•%203.13%20•%203.14-blue?logo=python)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?logo=ruff)](https://github.com/astral-sh/ruff)

[![CI Status](https://github.com/jebel-quant/rhiza/workflows/CI/badge.svg)](https://github.com/jebel-quant/rhiza/actions)
[![Pre-commit](https://github.com/jebel-quant/rhiza/workflows/PRE-COMMIT/badge.svg)](https://github.com/jebel-quant/rhiza/actions?query=workflow%3APRE-COMMIT)
[![Deptry](https://github.com/jebel-quant/rhiza/workflows/DEPTRY/badge.svg)](https://github.com/jebel-quant/rhiza/actions?query=workflow%3ADEPTRY)
[![Book](https://github.com/jebel-quant/rhiza/workflows/BOOK/badge.svg)](https://github.com/jebel-quant/rhiza/actions?query=workflow%3ABOOK)
[![Marimo](https://github.com/jebel-quant/rhiza/workflows/Marimo/badge.svg)](https://github.com/jebel-quant/rhiza/actions?query=workflow%3AMarimo)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jebel-quant/rhiza)

A collection of reusable configuration templates
for modern Python projects.
Save time and maintain consistency across your projects
with these pre-configured templates.

![Last Updated](https://img.shields.io/github/last-commit/jebel-quant/rhiza/main?label=Last%20updated&color=blue)

## ✨ Features

- 🚀 **CI/CD Templates** - Ready-to-use GitHub Actions and GitLab CI workflows
- 🧪 **Testing Framework** - Comprehensive test setup with pytest
- 📚 **Documentation** - Automated documentation generation
- 🔍 **Code Quality** - Linting, formatting, and dependency checking
- 📝 **Editor Configuration** - Cross-platform .editorconfig for consistent coding style
- 📊 **Marimo Integration** - Interactive notebook support

## 🚀 Getting Started

Start by cloning the repository:

```bash
# Clone the repository
git clone https://github.com/jebel-quant/rhiza.git
cd rhiza
```

The project uses a [Makefile](Makefile) as the primary entry point for all tasks.
It relies on [uv and uvx](https://github.com/astral-sh/uv) for fast Python package management.

Install all dependencies using:

```bash
make install
```

This will:
- Install `uv` and `uvx` into the `bin/` directory
- Create a Python virtual environment in `.venv/`
- Install all project dependencies from `pyproject.toml`

Both the `.venv` and `bin` directories are listed in `.gitignore`.

## 📋 Available Tasks

Run `make help` to see all available targets:

```makefile
Usage:
  make <target>

Targets:

Bootstrap
  install-uv       ensure uv/uvx is installed
  install-extras   run custom build script (if exists)
  install          install
  clean            clean

Development and Testing
  test             run all tests
  marimo           fire up Marimo server
  marimushka       export Marimo notebooks to HTML
  deptry           run deptry if pyproject.toml exists

Documentation
  docs             create documentation with pdoc
  book             compile the companion book
  fmt              check the pre-commit hooks and the linting
  all              Run everything

Releasing and Versioning
  bump             bump version
  release          create tag and push to remote with prompts
  post-release     perform post-release tasks

Meta
  sync             sync with template repository as defined in .github/template.yml
  help             Display this help message
  customisations   list available customisation scripts
  update-readme    update README.md with current Makefile help output
```

The [Makefile](Makefile) provides organized targets for bootstrapping, development, testing, and documentation tasks.

> **Note:** The help output above is automatically generated from the Makefile.
> When you modify Makefile targets or descriptions, run `make update-readme` to update this section,
> or the pre-commit hook will update it automatically when you commit changes to the Makefile.

## 📊 Marimo Notebooks

This project supports [Marimo](https://marimo.io/) notebooks. You can run the Marimo server using:

```bash
make marimo
```

### Configuration

To ensure Marimo can import the local package (`src/config`), the following configuration is added to `pyproject.toml`:

```toml
[tool.marimo.runtime]
pythonpath = ["src"]
```

### Dependency Management

Marimo notebooks can define their own dependencies using inline script metadata. This allows notebooks to be self-contained and reproducible.

To use the current package (`rhiza`) within a notebook, you can define it as a dependency and point `uv` to the local path. Add the following block at the top of your `.py` notebook file:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas",
#     "rhiza",
# ]
#
# [tool.uv.sources]
# rhiza = { path = "../.." }
# ///
```

Adjust the `path` in `[tool.uv.sources]` relative to the notebook's location.

## Testing your documentation

Any README.md file will be scanned for Python code blocks.
If any are found, they will be tested in [test_readme.py](tests/test_config_templates/test_readme.py).

```python
# Some generic Python code block
import math
print("Hello, World!")
print(1 + 1)
print(round(math.pi, 2))
print(round(math.cos(math.pi/4.0), 2))
```

For each code block, we define a block of expected output.
If the output matches the expected output, a [test](tests/test_config_templates/test_readme.py) passes,
Otherwise, it fails.

```result
Hello, World!
2
3.14
0.71
```

## 📁 Available Templates

This repository includes the following configuration templates:

- **ruff.toml** - Configuration for the Ruff linter and formatter
- **pytest.ini** - Configuration for the pytest testing framework
- **.devcontainer/** - Development container configuration
- **.github/** - GitHub Actions, scripts and workflow templates
- **Makefile** - Simple make commands for common operations

## ⚙️ Workflow Configuration

The GitHub Actions workflows can be customized using repository variables:

### Python Version Control

Control which Python versions are used in your workflows:

- **`PYTHON_MAX_VERSION`** - Maximum Python version for CI testing matrix
  - Default: `'3.14'` (tests on 3.11, 3.12, 3.13, 3.14)
  - Set to `'3.13'` to test on 3.11, 3.12, 3.13 only
  - Set to `'3.12'` to test on 3.11, 3.12 only
  - Set to `'3.11'` to test on 3.11 only

- **`PYTHON_DEFAULT_VERSION`** - Default Python version for release, pre-commit, book, and marimo workflows
  - Default: `'3.14'`
  - Set to `'3.12'` or `'3.13'` if dependencies are not compatible with newer versions

**To set these variables:**

1. Go to your repository Settings → Secrets and variables → Actions → Variables tab
2. Click "New repository variable"
3. Add `PYTHON_MAX_VERSION` and/or `PYTHON_DEFAULT_VERSION` with your desired values

## 🧩 Usage Examples

You can inject the templates into your project
using one of the methods described below.

### Manual Copy

Copy the desired configuration files to your project:

```bash
# Example: Copy GitHub workflow files
mkdir -p .github/workflows
cp rhiza/.github/workflows/ci.yml .github/workflows/
```

### Using Jebel Quant's [Sync Template Action](https://github.com/marketplace/actions/sync-template)

You can automatically sync these configuration
templates into your GitHub repositories using
the Jebel Quant action:

```yaml
name: Sync Templates

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday at midnight
  workflow_dispatch:     # Allow manual triggering

permissions:
  contents: write
  pull-requests: write

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Sync Template
        id: sync
        uses: jebel-quant/sync_template@v0.3.1
        with:
          token: ${{ secrets.PAT_TOKEN }}
          source: ".github/template.yml"
          branch: "template-updates"
          commit-message: "chore: sync template files"
```

This workflow will:

1. Download the latest templates based on your template.yml configuration
2. Copy them to your project
3. Create a pull request with the changes (if any)

**Note:** You need to create a `.github/template.yml` file in your repository that specifies
which templates to sync. This file should list the configuration files you want to include from this repository.
Example template.yml:

```yaml
template-repository: "jebel-quant/rhiza"
template-branch: "main"
include: |
    .github
    tests
    .editorconfig
    .gitignore
    .pre-commit-config.yaml
    CODE_OF_CONDUCT.md
    CONTRIBUTING.md
    Makefile
    ruff.toml
```

## 🖥️ Dev Container Compatibility

This repository includes a
template **Dev Container** configuration
for seamless development experience in
both **VS Code** and **GitHub Codespaces**.

### What's Configured

The `.devcontainer` setup provides:

- 🐍 **Python 3.14** runtime environment
- 🔧 **UV Package Manager** - Fast Python package installer and resolver
- ⚡ **Makefile** - For running project workflows
- 🧪 **Pre-commit Hooks** - Automated code quality checks
- 📊 **Marimo Integration** - Interactive notebook support with VS Code extension
- 🔍 **Python Development Tools** - Pylance, Python extension, and optimized settings
- 🚀 **Port Forwarding** - Port 8080 for development servers
- 🔐 **SSH Agent Forwarding** - Full Git functionality with your host SSH keys

### Usage

#### In VS Code

1. Install the "Dev Containers" extension
2. Open the repository in VS Code
3. Click "Reopen in Container" when prompted
4. The environment will automatically set up with all dependencies

#### In GitHub Codespaces

1. Navigate to the repository on GitHub
2. Click the green "Code" button
3. Select "Codespaces" tab
4. Click "Create codespace on main" (or your branch)
5. Your development environment will be ready in minutes

The dev container automatically runs the initialization script that:

- Installs UV package manager
- Configures the Python virtual environment
- Installs project dependencies
- Sets up pre-commit hooks

### Publishing Devcontainer Images

The repository includes workflows for building and publishing devcontainer images:

#### CI Validation

The **DEVCONTAINER** workflow automatically validates that your devcontainer builds successfully:
- Triggers on changes to `.devcontainer/**` files or the workflow itself
- Builds the image without publishing (`push: never`)
- Works on pushes to any branch and pull requests
- Gracefully skips if no `.devcontainer/devcontainer.json` exists

### VS Code Dev Container SSH Agent Forwarding

Dev containers launched locally via VS code
are configured with SSH agent forwarding
to enable seamless Git operations:

- **Mounts your SSH directory** - Your `~/.ssh` folder is mounted into the container
- **Forwards SSH agent** - Your host's SSH agent is available inside the container
- **Enables Git operations** - Push, pull, and clone using your existing SSH keys
- **Works transparently** - No additional setup required in VS Code dev containers

### Troubleshooting

Common issues and solutions when using this configuration template.

---

#### SSH authentication fails on macOS when using devcontainer

**Symptom**: When building or using the devcontainer on macOS, Git operations (pull, push, clone) fail with SSH authentication errors, even though your SSH keys work fine on the host.

**Cause**: macOS SSH config often includes `UseKeychain yes`, which is a macOS-specific directive. When the devcontainer mounts your `~/.ssh` directory, other platforms (Linux containers) don't recognize this directive and fail to parse the SSH config.

**Solution**: Add `IgnoreUnknown UseKeychain` to the top of your `~/.ssh/config` file on your Mac:

```ssh-config
# At the top of ~/.ssh/config
IgnoreUnknown UseKeychain

Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_rsa
```

This tells SSH clients on non-macOS platforms to ignore the `UseKeychain` directive instead of failing.

**Reference**: [Stack Overflow solution](https://stackoverflow.com/questions/75613632/trying-to-ssh-to-my-server-from-the-terminal-ends-with-error-line-x-bad-configu/75616369#75616369)


## 🔧 Custom Build Extras

The project includes a hook for installing additional system dependencies and custom build steps needed across all build phases.

### Using build-extras.sh

Create a file `.github/scripts/customisations/build-extras.sh` in your repository to install system packages or dependencies (this repository uses a dedicated `customisations` folder for repo-specific scripts):
```bash
#!/bin/bash
set -euo pipefail

# Example: Install graphviz for diagram generation
sudo apt-get update
sudo apt-get install -y graphviz

# Add other custom installation commands here
```

### When it Runs

The `build-extras.sh` script (from `.github/scripts/customisations`) is automatically invoked during:
- `make install` - Initial project setup
- `make test` - Before running tests
- `make book` - Before building documentation
- `make docs` - Before generating API documentation

This ensures custom dependencies are available whenever needed throughout the build lifecycle. The `Makefile` intentionally only checks the `.github/scripts/customisations` folder for repository-specific hooks such as `build-extras.sh` and `post-release.sh`.

### Important: Exclude from Template Updates

If you customize this file, add it to the exclude list in your `action.yml` configuration to prevent it from being overwritten during template updates. Use the `customisations` path to avoid clobbering:
```yaml
exclude: |
  .github/scripts/customisations/build-extras.sh
```


### Common Use Cases

- Installing graphviz for diagram rendering
- Adding LaTeX for mathematical notation
- Installing system libraries for specialized tools
- Setting up additional build dependencies
- Downloading external resources or tools

### Post-release scripts

If you need repository-specific post-release tasks, place a `post-release.sh` script in `.github/scripts/customisations/post-release.sh`. The `Makefile` will only look in the `customisations` folder for that hook.


## 🚀 Releasing

This template includes a robust release workflow that handles version bumping, tagging, and publishing.

### The Release Process

The release process consists of two interactive steps: **Bump** and **Release**.

#### 1. Bump Version

First, update the version in `pyproject.toml`:

```bash
make bump
```

This command will interactively guide you through:
1. Selecting a bump type (patch, minor, major) or entering a specific version
2. Warning you if you're not on the default branch
3. Showing the current and new version
4. Prompting whether to commit the changes
5. Prompting whether to push the changes

The script ensures safety by:
- Checking for uncommitted changes before bumping
- Validating that the tag doesn't already exist
- Verifying the version format

#### 2. Release

Once the version is bumped and committed, run the release command:

```bash
make release
```

This command will interactively guide you through:
1. Checking if your branch is up-to-date with the remote
2. If your local branch is ahead, showing the unpushed commits and prompting you to push them
3. Creating a git tag (e.g., `v1.2.4`)
4. Pushing the tag to the remote, which triggers the GitHub Actions release workflow

The script provides safety checks by:
- Warning if you're not on the default branch
- Verifying no uncommitted changes exist
- Checking if the tag already exists locally or on remote
- Showing the number of commits since the last tag

### What Happens After Release

The release workflow (`.github/workflows/release.yml`) triggers on the tag push and:

1.  **Validates** - Checks the tag format and ensures no duplicate releases
2.  **Builds** - Builds the Python package (if `pyproject.toml` exists)
3.  **Drafts** - Creates a draft GitHub release with artifacts
4.  **PyPI** - Publishes to PyPI (if not marked private)
5.  **Devcontainer** - Publishes devcontainer image (if `PUBLISH_DEVCONTAINER=true`)
6.  **Finalizes** - Publishes the GitHub release with links to PyPI and container images

### Configuration Options

**Python Version Configuration:**
- Set repository variable `PYTHON_MAX_VERSION` to control maximum Python version in CI tests
  - Options: `'3.11'`, `'3.12'`, `'3.13'`, or `'3.14'` (default)
  - Example: Set to `'3.13'` to test on Python 3.11, 3.12, and 3.13 only
- Set repository variable `PYTHON_DEFAULT_VERSION` to control default Python version in workflows
  - Options: `'3.11'`, `'3.12'`, `'3.13'`, or `'3.14'` (default)
  - Example: Set to `'3.12'` if dependencies are not compatible with Python 3.14
  - Used in release, pre-commit, book, and marimo workflows

**PyPI Publishing:**
- Automatic if package is registered as a Trusted Publisher
- Use `PYPI_REPOSITORY_URL` and `PYPI_TOKEN` for custom feeds
- Mark as private with `Private :: Do Not Upload` in `pyproject.toml`

**Devcontainer Publishing:**
- Set repository variable `PUBLISH_DEVCONTAINER=true` to enable
- Override registry with `DEVCONTAINER_REGISTRY` variable (defaults to ghcr.io)
- Requires `.devcontainer/devcontainer.json` to exist
- Image published as `{registry}/{owner}/{repository}/devcontainer:vX.Y.Z`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [GitHub Actions](https://github.com/features/actions) - For CI/CD capabilities
- [Marimo](https://marimo.io/) - For interactive notebooks
- [UV](https://github.com/astral-sh/uv) - For fast Python package operations
