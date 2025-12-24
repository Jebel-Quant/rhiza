<div align="center">

# <img src="assets/rhiza-logo.svg" alt="Rhiza Logo" width="30" style="vertical-align: middle;"> Rhiza

![Created with Rhiza](https://img.shields.io/badge/synced%20with-rhiza-2FA4A9?logoUrl=https://raw.githubusercontent.com/Jebel-Quant/rhiza/main/assets/rhiza-logo.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python versions](https://img.shields.io/badge/Python-3.11%20•%203.12%20•%203.13%20•%203.14-blue?logo=python)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?logo=ruff)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

[![CI](https://github.com/Jebel-Quant/rhiza/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Jebel-Quant/rhiza/actions/workflows/ci.yml)
[![PRE-COMMIT](https://github.com/Jebel-Quant/rhiza/actions/workflows/pre-commit.yml/badge.svg?branch=main)](https://github.com/Jebel-Quant/rhiza/actions/workflows/pre-commit.yml)
[![DEPTRY](https://github.com/Jebel-Quant/rhiza/actions/workflows/deptry.yml/badge.svg?branch=main)](https://github.com/Jebel-Quant/rhiza/actions/workflows/deptry.yml)
[![BOOK](https://github.com/Jebel-Quant/rhiza/actions/workflows/book.yml/badge.svg?branch=main)](https://github.com/Jebel-Quant/rhiza/actions/workflows/book.yml)
[![MARIMO](https://github.com/Jebel-Quant/rhiza/actions/workflows/marimo.yml/badge.svg?branch=main)](https://github.com/Jebel-Quant/rhiza/actions/workflows/marimo.yml)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jebel-quant/rhiza)

A collection of reusable configuration templates
for modern Python projects.
Save time and maintain consistency across your projects
with these pre-configured templates.

![Last Updated](https://img.shields.io/github/last-commit/jebel-quant/rhiza/main?label=Last%20updated&color=blue)

In the original Greek, spelt **ῥίζα**, pronounced *ree-ZAH*, and having the literal meaning **root**.

</div>

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
  install-uv            ensure uv/uvx is installed
  install-extras        run custom build script (if exists)
  install               install
  sync                  sync with template repository as defined in .github/rhiza/template.yml
  validate              validate project structure against template repository as defined in .github/rhiza/template.yml
  clean                 clean

Tools
  marimo                fire up Marimo server

Quality and Formatting
  deptry                run deptry if pyproject.toml exists
  fmt                   check the pre-commit hooks and the linting

Releasing and Versioning
  bump                  bump version
  release               create tag and push to remote with prompts
  post-release          perform post-release tasks

Meta
  help                  Display this help message
  customisations        list available customisation scripts
  update-readme         update README.md with current Makefile help output

Development and Testing
  test                  run all tests
  benchmark             run performance benchmarks

Documentation
  docs                  create documentation with pdoc
  marimushka            export Marimo notebooks to HTML
  book                  compile the companion book

Presentation
  presentation          generate presentation slides from PRESENTATION.md using Marp
  presentation-pdf      generate PDF presentation from PRESENTATION.md using Marp
  presentation-serve    serve presentation interactively with Marp

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

## 🎨 Documentation Customization

You can customize the look and feel of your documentation by providing your own templates.

### API Documentation (pdoc)

The `make docs` command checks for a directory at `book/pdoc-templates`. If found, it uses the templates within that directory to generate the API documentation.

To customize the API docs:
1. Create the directory: `mkdir -p book/pdoc-templates`
2. Add your Jinja2 templates (e.g., `module.html.jinja2`) to this directory.

See the [pdoc documentation](https://pdoc.dev/docs/pdoc.html#templates) for more details on templating.

### Companion Book (minibook)

The `make book` command checks for a template at `book/minibook-templates/custom.html.jinja2`. If found, it uses this template for the minibook generation.

To customize the book:
1. Create the directory: `mkdir -p book/minibook-templates`
2. Create your custom template at `book/minibook-templates/custom.html.jinja2`.

## 📁 Available Templates

This repository provides a curated set of reusable configuration templates, organised by purpose.

### 🌱 Core Project Configuration
Foundational files that define project structure, standards, and contribution practices.

- **.gitignore** — Sensible defaults for Python projects
- **.editorconfig** — Editor configuration to enforce consistent coding standards
- **ruff.toml** — Configuration for the Ruff linter and formatter
- **pytest.ini** — Configuration for the `pytest` testing framework
- **Makefile** — Simple make targets for common development tasks
- **CODE_OF_CONDUCT.md** — Generic code of conduct for open-source projects
- **CONTRIBUTING.md** — Generic contributing guidelines for open-source projects

### 🔧 Developer Experience
Tooling that improves local development, onboarding, and reproducibility.

- **.devcontainer/** — Development container setup (VS Code / Dev Containers)
- **.pre-commit-config.yaml** — Common and useful pre-commit hooks
- **docker/** — Example `Dockerfile` and `.dockerignore`

### 🚀 CI / CD & Automation
Templates related to continuous integration, delivery, and repository automation.

- **.github/** — GitHub Actions workflows, scripts, and repository templates

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

## 🧩 Bringing Rhiza into an Existing Project

Rhiza provides reusable configuration templates that you can integrate into your existing Python projects.
You can choose to adopt all templates or selectively pick the ones that fit your needs.

### Prerequisites

Before integrating Rhiza into your existing project:

- **Python 3.11+** - Ensure your project supports Python 3.11 or newer
- **Git** - Your project should be a Git repository
- **Backup** - Consider committing any uncommitted changes before integration
- **Review** - Review the [Available Templates](#-available-templates) section to understand what could be added

### Quick Start: Automated Injection

The fastest way to integrate Rhiza is using the provided `inject_rhiza.sh` script:

```bash
# Navigate to your repository
cd /path/to/your/project

# Run the injection script
uvx rhiza .
```

This will:
- ✅ Create a default template configuration (`.github/template.yml`)
- ✅ Perform an initial sync of a basic set of templates
- ✅ Provide clear next steps for review and customization

**Options:**
- `--branch <branch>` - Use a specific rhiza branch (default: main)
- `--help` - Show detailed usage information

**Example with branch option:**
```bash
# Use a development branch
uvx --branch develop .
```

### Method 1: Manual Integration (Selective Adoption)

This approach is ideal if you want to cherry-pick specific templates or customize them before integration.

#### Step 1: Clone Rhiza

First, clone the Rhiza repository to a temporary location:

```bash
# Clone to a temporary directory
cd /tmp
git clone https://github.com/jebel-quant/rhiza.git
```

#### Step 2: Copy Desired Templates

Navigate to your project and copy the configuration files you need:

```bash
# Navigate to your project
cd /path/to/your/project

# We recommend working on a fresh branch
git checkout -b rhiza

# Ensure required directories exist
mkdir -p .github/workflows
mkdir -p .github/scripts

# Copy the template configuration
cp /tmp/rhiza/.github/template.yml .github/template.yml

# Copy the sync helper script
cp /tmp/rhiza/.github/scripts/sync.sh .github/scripts
```

At this stage:

  - ❌ No templates are copied yet
  - ❌ No existing files are modified
  - ✅ Only the sync mechanism is installed
  - ⚠️ **Do not merge this branch yet.**

#### Step 3: Perform the first sync

Run the sync script to apply the templates defined in '.github/template.yml'

```bash
./.github/scripts/sync.sh
```

This will:

  - Fetch the selected templates from the Rhiza repository
  - Apply them locally according to your include/exclude rules
  - Stage or commit the resulting changes on the current branch

Review the changes carefully:

```bash
git status
git diff
```

If happy with the suggested changes push them

```bash
git add .
git commit -m "Integrate Rhiza templates"
git push -u origin rhiza
```

### Method 2: Automated Sync (Continuous Updates)

This approach keeps your project’s configuration in sync with Rhiza’s latest templates while giving you control over which files are applied.

Prerequisites:

  - A .github/template.yml file exists, defining **which templates to include or exclude**.
  - The first manual sync (./.github/scripts/sync.sh) has been performed.
  - The .github/workflows/sync.yml workflow is present in your repository.

The workflow can run:

  **On a schedule** — e.g., weekly updates
  **Manually** — via the GitHub Actions “Run workflow” button

⚠️ .github/template.yml remains the **source of truth**. All automated updates are driven by its include/exclude rules.

#### Step 1: Configure GitHub Token

If you want the sync workflow to trigger other workflows (e.g. to create pull requests), create a Personal Access Token (PAT):

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with `repo` and `workflow` scopes
3. Add it as a repository secret named `PAT_TOKEN`
4. Update the workflow to use `token: ${{ secrets.PAT_TOKEN }}`

#### Step 2: Run Initial Sync (again)

You can trigger the sync workflow manually:

1. Go to your repository's "Actions" tab
2. Select the "Sync Templates" workflow
3. Click "Run workflow"
4. Review and merge the resulting pull request

The workflow will:
- Download the latest templates from Rhiza
- Copy them to your project based on your `template.yml` configuration
- Create a pull request with the changes (if any)
- Automatically run weekly to keep your templates up to date

### What to Expect After Integration

After integrating Rhiza, your project will have:

- **Automated CI/CD** - GitHub Actions workflows for testing, linting, and releases
- **Code Quality Tools** - Pre-commit hooks, ruff formatting, and pytest configuration
- **Task Automation** - Makefile with common development tasks (`make test`, `make fmt`, etc.)
- **Dev Container** - Optional VS Code/Codespaces development environment
- **Documentation** - Templates for automated documentation generation

### Next Steps

1. **Test the integration** - Run `make test` to ensure tests pass
2. **Run pre-commit** - Execute `make fmt` to verify code quality checks
3. **Review workflows** - Check GitHub Actions tabs to see workflows in action
4. **Customize** - Adjust templates to match your project's specific needs
5. **Update documentation** - Add project-specific instructions to your README

### Troubleshooting

**Issue: Makefile targets conflict with existing scripts**
- Solution: Review the Makefile and merge targets with your existing build scripts, or rename conflicting targets

**Issue: Pre-commit hooks fail on existing code**
- Solution: Run `make fmt` to fix formatting issues, or temporarily exclude certain files in `.pre-commit-config.yaml`

**Issue: GitHub Actions workflows fail**
- Solution: Check Python version compatibility and adjust `PYTHON_MAX_VERSION` repository variable if needed

**Issue: Dev container fails to build**
- Solution: Review `.devcontainer/devcontainer.json` and ensure all dependencies are available for your project

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
