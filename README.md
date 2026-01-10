<div align="center">

# <img src="assets/rhiza-logo.svg" alt="Rhiza Logo" width="30" style="vertical-align: middle;"> Rhiza
![GitHub Release](https://img.shields.io/github/v/release/jebel-quant/rhiza?sort=semver&color=2FA4A9&label=rhiza)
![Synced with Rhiza](https://img.shields.io/badge/synced%20with-rhiza-2FA4A9?color=2FA4A9)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python versions](https://img.shields.io/badge/Python-3.11%20•%203.12%20•%203.13%20•%203.14-blue?logo=python)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?logo=ruff)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![CodeFactor](https://www.codefactor.io/repository/github/jebel-quant/rhiza/badge)](https://www.codefactor.io/repository/github/jebel-quant/rhiza)

![Gitlab](https://img.shields.io/badge/GitLab-FC6D26?style=flat&logo=gitlab&logoColor=white)
![Github](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat&logo=linux&logoColor=white)
![MAC OS](https://img.shields.io/badge/macOS-000000?style=flat&logo=apple&logoColor=white)

[![CI](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_ci.yml/badge.svg?event=push)](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_ci.yml)
[![PRE-COMMIT](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_pre-commit.yml/badge.svg?event=push)](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_pre-commit.yml)
[![DEPTRY](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_deptry.yml/badge.svg?event=push)](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_deptry.yml)
[![MARIMO](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_marimo.yml/badge.svg?event=push)](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_marimo.yml)
[![DOCKER](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_docker.yml/badge.svg?event=push)](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_docker.yml)
[![DEVCONTAINER](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_devcontainer.yml/badge.svg?event=push)](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_devcontainer.yml)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jebel-quant/rhiza)

# Strong roots
Creating and maintaining technical harmony across repositories.

Reusable configuration templates for modern Python projects.
Repositories opt into specific templates, allowing controlled flexibility while preserving consistency.
Automated synchronization keeps selected templates applied over time.

![Last Updated](https://img.shields.io/github/last-commit/jebel-quant/rhiza/main?label=Last%20updated&color=blue)

In the original Greek, spelt **ῥίζα**, pronounced *ree-ZAH*, and having the literal meaning **root**.

</div>

## 📑 Table of Contents

- [✨ Features](#-features)
- [🚀 Getting Started](#-getting-started)
- [📋 Available Tasks](#-available-tasks)
- [📊 Marimo Notebooks](#-marimo-notebooks)
- [🧪 Testing](#-testing)
- [🎨 Documentation Customization](#-documentation-customization)
- [📽️ Presentations](#-presentations)
- [📁 Available Templates](#-available-templates)
- [⚙️ Workflow Configuration](#-workflow-configuration)
- [🔒 Security](#-security)
- [♻️ Dependency Management](#-dependency-management)
- [🧩 Bringing Rhiza into an Existing Project](INTEGRATION.md) *(see dedicated guide)*
- [🖥️ Dev Container Compatibility](.devcontainer/README.md) *(see dedicated guide)*
- [🔧 Custom Build Extras](#-custom-build-extras)
- [🚀 Releasing](#-releasing)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)

## ✨ Features

- 🚀 **CI/CD Templates** - Ready-to-use GitHub Actions and GitLab CI workflows
- 🧪 **Testing Framework** - Comprehensive test setup with pytest
- 📚 **Documentation** - Automated documentation generation
- 🔍 **Code Quality** - Linting, formatting, and dependency checking
- 📝 **Editor Configuration** - Cross-platform .editorconfig for consistent coding style
- 📊 **Marimo Integration** - Interactive notebook support

## 🚀 Getting Started

Rhiza is consumed via a dedicated command line tool.
We recommend installing [uv/uvx](https://docs.astral.sh/uv/getting-started/installation/)
and start with

```bash
uvx rhiza --help
```

and

```bash
uvx rhiza welcome
```

```bash
╭───────────────────────────────────────────────────────────────╮
│                                                               │
│  🌿 Welcome to Rhiza v0.8.3                                   │
│                                                               │
╰───────────────────────────────────────────────────────────────╯

Rhiza helps you maintain consistent configuration across multiple
Python projects using reusable templates stored in a central repository.

✨ What Rhiza can do for you:

  • Initialize projects with standard configuration templates
  • Materialize (inject) templates into target repositories
  • Validate template configurations
  • Keep project configurations synchronized

🚀 Getting started:

  1. Initialize a project:
     $ rhiza init

  2. Customize .rhiza/template.yml to match your needs

  3. Materialize templates into your project:
     $ rhiza materialize

📚 Learn more:

  • View all commands:    rhiza --help
  • Project repository:   https://github.com/jebel-quant/rhiza-cli
  • Documentation:        https://jebel-quant.github.io/rhiza-cli/

Happy templating! 🎉
```

**Note:** This repository (`jebel-quant/rhiza`) contains the configuration templates.
The actual command line tool is [rhiza-cli](https://github.com/jebel-quant/rhiza-cli).

## 🧩 Bringing Rhiza into an Existing Project

Rhiza provides reusable configuration templates that you can integrate
into your existing Python projects.
You can choose to adopt all templates or selectively pick the ones that fit your needs.

**📖 [View the complete Integration Guide →](INTEGRATION.md)**

The integration guide covers:
- Prerequisites and preparation
- Quick Start with automated injection
- Manual integration for selective adoption
- Automated sync for continuous updates
- What to expect after integration
- Troubleshooting common issues

## The .rhiza/template.yml file

The `.rhiza/template.yml` file contains the configuration
for the files and folders that you want to apply to your project.

```yaml
template-repository: jebel-quant/rhiza
template-branch: main
include:
- .github/workflows
- tests
- book
- presentation
- .rhiza
- .editorconfig
- .gitignore
- .pre-commit-config.yaml
- Makefile
- ruff.toml
exclude:
- .github/workflows/rhiza_docker.yml
```

The `template-repository` and `template-branch` fields specify the repository
and branch to pull templates from.
Of course, you can use your own fork of Rhiza, or a different template repository entirely to customize.

In the example above we include all files and folders from the `.github/workflows` directory,
the `tests` directory. Behind the scenes a sparse git checkout is performed to extract the files and folders.
It is possible to specify multiple template repositories.

The `exclude` field allows you to exclude files and folders from the template checkout.
This is useful if you want to customize the template checkout without modifying the original template.

The file is created automatically when you run `rhiza init` and can be modified manually afterwards.

## 📋 Available Tasks

The `Makefile` provides a convenient way to run common development tasks.
Rather than having just one Makefile we have multiple Makefiles for different purposes.
The Makefile on the root level is the central entry point for all tasks.
The actual list of possible targets depends on the installed templates.

Run `make help` to see all available targets:

```makefile
  ____  _     _
 |  _ \| |__ (_)______ _
 | |_) | '_ \| |_  / _\`|
 |  _ <| | | | |/ / (_| |
 |_| \_\_| |_|_/___\__,_|
 
Usage:
  make <target>

Targets:

Meta

Bootstrap
  install-uv            ensure uv/uvx is installed
  install-extras        run custom build script (if exists)
  install               install
  sync                  sync with template repository as defined in .github/template.yml
  validate              validate project structure against template repository as defined in .github/template.yml
  clean                 Clean project artifacts and stale local branches

Tools

Quality and Formatting
  deptry                Run deptry
  fmt                   check the pre-commit hooks and the linting

Releasing and Versioning
  bump                  bump version
  release               create tag and push to remote with prompts
  post-release          perform post-release tasks

Meta
  help                  Display this help message
  customisations        list available customisation scripts
  update-readme         update README.md with current Makefile help output
  version-matrix        Emit the list of supported Python versions from pyproject.toml

Development and Testing
  test                  run all tests
  benchmark             run performance benchmarks

Documentation
  docs                  create documentation with pdoc
  book                  compile the companion book

Marimo
  marimo                fire up Marimo server
  marimushka            export Marimo notebooks to HTML
  marimo-deptry         Run deptry on Marimo notebooks

Presentation
  presentation          generate presentation slides from PRESENTATION.md using Marp
  presentation-pdf      generate PDF presentation from PRESENTATION.md using Marp
  presentation-serve    serve presentation interactively with Marp

Customisations
  install-extras        run custom build script (if exists)
  post-release          perform post-release tasks

Agentic Workflows
  copilot               open interactive prompt for copilot
  analyse-repo          run the analyser agent to update REPOSITORY_ANALYSIS.md
  summarize-changes     summarize changes since the most recent release/tag
  install-copilot       checks for copilot and prompts to install

GitHub Helpers
  gh-install            check for gh cli existence and install extensions
  view-prs              list open pull requests
  view-issues           list open issues
  failed-workflows      list recent failing workflow runs
  whoami                check github auth status

```

The [Makefile](Makefile) provides organized targets for bootstrapping, development, testing, and documentation tasks.

> **Note:** The help output above is automatically generated from the Makefile.
> When you modify Makefile targets or descriptions, run `make update-readme` to update this section,
> or the pre-commit hook will update it automatically when you commit changes to the Makefile.

## 📊 Marimo Notebooks

This project supports [Marimo](book/marimo/README.md) notebooks.

## 🧪 Testing

### Running Tests

Run the test suite using:

```bash
make test
```

**📖 [View the complete Test Suite Guide →](tests/test_rhiza/README.md)**

The test suite includes:
- Git-based workflow validation (version bumping, releasing)
- Project structure checks
- Makefile target validation
- Documentation testing (README code examples, docstrings)
- Development tool fixtures

## 🎨 Documentation Customization

You can customize the look and feel of your documentation by providing your own templates.
[Documentation](book/README.md)

## 📽️ Presentations

Create beautiful presentation slides from Markdown using [Marp](https://marp.app/).

**📖 [View the complete Presentation Guide →](presentation/README.md)**

### Quick Start

```bash
# Generate HTML presentation
make presentation

# Generate PDF presentation  
make presentation-pdf

# Serve interactively with live reload
make presentation-serve
```

The presentation system:
- Converts `PRESENTATION.md` to HTML and PDF slides
- Supports custom themes and styling
- Provides live reload during editing
- Automatically installs Marp CLI if needed

Edit `PRESENTATION.md` in the repository root to create your presentation content. See the [presentation guide](presentation/README.md) for detailed documentation on Marp syntax, styling, and advanced features.

## 📁 Available Templates

This repository provides a curated set of reusable configuration templates, organised by purpose.

### 🌱 Core Project Configuration
Foundational files that define project structure, standards, and contribution practices.

- **.python-version** — Specifies the preferred Python version for tools like `uv` and `pyenv`
- **.gitignore** — Sensible defaults for Python projects
- **.editorconfig** — Editor configuration to enforce consistent coding standards
- **ruff.toml** — Configuration for the Ruff linter and formatter
- **pytest.ini** — Configuration for the `pytest` testing framework
- **Makefile** — Simple make targets for common development tasks
- **CODE_OF_CONDUCT.md** — Generic code of conduct for open-source projects
- **CONTRIBUTING.md** — Generic contributing guidelines for open-source projects
- **renovate.json** — Configuration for automatic dependency updates

### 🔧 Developer Experience

Tooling that improves local development, onboarding, and reproducibility.

- **.devcontainer/** — Development container setup (VS Code / Dev Containers)
- **.pre-commit-config.yaml** — Common and useful pre-commit hooks
- **docker/** — Example `Dockerfile` and `.dockerignore`

### 🚀 CI / CD & Automation
Templates related to continuous integration, delivery, and repository automation.

- **.github/** — GitHub Actions workflows, scripts, and repository templates
- **.gitlab/** — GitLab CI/CD workflows (equivalent to GitHub Actions)
  - See [GITLAB_CI.md](GITLAB_CI.md) for GitLab CI/CD setup and usage

## 🖥️ Dev Container Compatibility

This repository includes a template **Dev Container** configuration for seamless development experience in both **VS Code** and **GitHub Codespaces**.

**📖 [View the complete Dev Container Guide →](.devcontainer/README.md)**

The dev container guide covers:
- What's configured in the dev container
- Usage instructions for VS Code and GitHub Codespaces
- Publishing devcontainer images
- SSH agent forwarding setup
- Troubleshooting common issues

## 🔧 Custom Build Extras

The project includes a hook for installing additional system dependencies and custom build steps needed across all build phases.

### Using build-extras.sh

Create a file `.rhiza/scripts/customisations/build-extras.sh` in your repository to install system packages or dependencies (this repository uses a dedicated `customisations` folder for repo-specific scripts):
```bash
#!/bin/bash
set -euo pipefail

# Example: Install graphviz for diagram generation
sudo apt-get update
sudo apt-get install -y graphviz

# Add other custom installation commands here
```

### When it Runs

The `build-extras.sh` script (from `.rhiza/scripts/customisations`) is automatically invoked during:
- `make install` - Initial project setup
- `make test` - Before running tests
- `make book` - Before building documentation
- `make docs` - Before generating API documentation

This ensures custom dependencies are available whenever needed throughout the build lifecycle. The `Makefile` intentionally only checks the `.rhiza/scripts/customisations` folder for repository-specific hooks such as `build-extras.sh` and `post-release.sh`.

### Important: Exclude from Template Updates

If you customize this file, add it to the exclude list in your `action.yml` configuration to prevent it from being overwritten during template updates. Use the `customisations` path to avoid clobbering:
```yaml
exclude: |
  .rhiza/scripts/customisations/build-extras.sh
```


### Common Use Cases

- Installing graphviz for diagram rendering
- Adding LaTeX for mathematical notation
- Installing system libraries for specialized tools
- Setting up additional build dependencies
- Downloading external resources or tools

### Post-release scripts

If you need repository-specific post-release tasks, place a `post-release.sh` script in `.rhiza/scripts/customisations/post-release.sh`. The `Makefile` will only look in the `customisations` folder for that hook.


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

**Python Selection:**
- The `.python-version` file ensures that tools like `uv` and `pyenv` use the correct
Python version for local development.
- This is synchronized with the CI workflows and `pyproject.toml`.

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
