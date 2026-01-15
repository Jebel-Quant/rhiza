<div align="center">

# <img src="assets/rhiza-logo.svg" alt="Rhiza Logo" width="30" style="vertical-align: middle;"> Rhiza 
![GitHub Release](https://img.shields.io/github/v/release/jebel-quant/rhiza?sort=semver&color=2FA4A9&label=rhiza)
![Synced with Rhiza](https://img.shields.io/badge/synced%20with-rhiza-2FA4A9?color=2FA4A9)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python versions](https://img.shields.io/badge/Python-3.11%20•%203.12%20•%203.13%20•%203.14-blue?logo=python)](https://www.python.org/)
[![CI](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_ci.yml/badge.svg?event=push)](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_ci.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?logo=ruff)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![CodeFactor](https://www.codefactor.io/repository/github/jebel-quant/rhiza/badge)](https://www.codefactor.io/repository/github/jebel-quant/rhiza)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jebel-quant/rhiza)

# Strong roots
Creating and maintaining technical harmony across repositories.

A collection of reusable configuration templates
for modern Python projects.
Save time and maintain consistency across your projects
with these pre-configured templates.

![Last Updated](https://img.shields.io/github/last-commit/jebel-quant/rhiza/main?label=Last%20updated&color=blue)

In the original Greek, spelt **ῥίζα**, pronounced *ree-ZAH*, and having the literal meaning **root**.

</div>

## 🌟 Why Rhiza?

**Unlike traditional project templates** (like cookiecutter or copier) that generate a one-time snapshot of configuration files, **Rhiza provides living templates** that evolve with your project. Classic templates help you start a project, but once generated, your configuration drifts away from the template as best practices change. Rhiza takes a different approach: it enables **continuous synchronization**, allowing you to selectively pull template updates into your project over time through automated workflows. This means you can benefit from improvements to CI/CD workflows, linting rules, and development tooling without manually tracking upstream changes. Think of it as keeping your project's foundation fresh and aligned with modern practices, while maintaining full control over what gets updated.

### How It Works

Rhiza uses a simple configuration file (`.rhiza/template.yml`) to control which templates sync to your project:

```yaml
# .rhiza/template.yml
repository: Jebel-Quant/rhiza
ref: main

include: |
  .github/workflows/*.yml
  .pre-commit-config.yaml
  ruff.toml
  pytest.ini
  Makefile

exclude: |
  .rhiza/scripts/customisations/*
```

**What you're seeing:**
- **`repository`** - The upstream template source (**can be any repository, not just Rhiza!**)
- **`ref`** - Which branch/tag to sync from (usually `main`)
- **`include`** - File patterns to pull from the template (CI workflows, linting configs, etc.)
- **`exclude`** - Paths to skip, protecting your customisations

When you run `uvx rhiza materialize` or trigger the automated sync workflow, Rhiza fetches only the files matching your `include` patterns, skips anything in `exclude`, and creates a clean diff for you to review. You stay in control of what updates and when.

**💡 Pro Tip:** While you can use `Jebel-Quant/rhiza` directly, **we recommend creating your own template repository** using GitHub's "Use this template" button. This gives you a clean copy to customise for your organisation's specific needs and constraints—adjusting CI workflows, coding standards, or tooling choices—while still benefiting from Rhiza's sync mechanism. Your template repo becomes your team's source of truth, and you can selectively pull updates from upstream Rhiza when desired.

## 📚 Table of Contents

- [Why Rhiza?](#-why-rhiza)
- [Quick Start](#-quick-start)
- [What You Get](#-what-you-get)
- [Integration Guide](#-integration-guide)
- [Available Tasks](#-available-tasks)
- [Advanced Topics](#-advanced-topics)
- [CI/CD Support](#-cicd-support)
- [Contributing to Rhiza](#-contributing-to-rhiza)

## 🚀 Quick Start

### For New Projects

Create a new project with Rhiza templates:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialise Rhiza configuration
uvx rhiza init

# Edit .rhiza/template.yml to select desired templates
# Then materialize the templates
uvx rhiza materialize
```

### For Existing Projects

Integrate Rhiza into an existing Python project:

```bash
# Navigate to your repository
cd /path/to/your/project

# Initialise and configure
uvx rhiza init

# Review and edit .rhiza/template.yml
# Then apply templates
uvx rhiza materialize
```

See the [Integration Guide](#-integration-guide) for detailed instructions and options.

### For Contributing to Rhiza

If you want to develop Rhiza itself:

```bash
# Clone the repository
git clone https://github.com/jebel-quant/rhiza.git
cd rhiza

# Install dependencies
make install
```

## ✨ What You Get

### Core Features

- 🚀 **CI/CD Templates** - Ready-to-use GitHub Actions and GitLab CI workflows
- 🧪 **Testing Framework** - Comprehensive test setup with pytest
- 📚 **Documentation** - Automated documentation generation with pdoc and companion books
- 🔍 **Code Quality** - Linting with ruff, formatting, and dependency checking with deptry
- 📝 **Editor Configuration** - Cross-platform .editorconfig for consistent coding style
- 📊 **Marimo Integration** - Interactive notebook support for documentation and exploration
- 🎤 **Presentations** - Generate slides from Markdown using Marp
- 🐳 **Containerization** - Docker and Dev Container configurations

### Available Templates

This repository provides a curated set of reusable configuration templates:

#### 🌱 Core Project Configuration
- **.gitignore** - Sensible defaults for Python projects
- **.editorconfig** - Editor configuration to enforce consistent coding standards
- **ruff.toml** - Configuration for the Ruff linter and formatter
- **pytest.ini** - Configuration for the `pytest` testing framework
- **Makefile** - Task automation for common development workflows
- **CODE_OF_CONDUCT.md** - Code of conduct for open-source projects
- **CONTRIBUTING.md** - Contributing guidelines

#### 🔧 Developer Experience
- **.devcontainer/** - Development container setup (VS Code / Dev Containers)
- **.pre-commit-config.yaml** - Pre-commit hooks for code quality
- **docker/** - Example `Dockerfile` and `.dockerignore`

#### 🚀 CI/CD & Automation
- **.github/** - GitHub Actions workflows, scripts, and repository templates
- **.gitlab/** - GitLab CI/CD workflows (see [.gitlab/README.md](.gitlab/README.md))

## 🧩 Integration Guide

Rhiza provides reusable configuration templates that you can integrate into your existing Python projects.

### Prerequisites

- **Python 3.11+** - Ensure your project supports Python 3.11 or newer
- **Git** - Your project should be a Git repository
- **Backup** - Consider committing any uncommitted changes before integration

### Automated Integration (Recommended)

The fastest way to integrate Rhiza:

```bash
# Navigate to your repository
cd /path/to/your/project

# Initialise configuration templates
uvx rhiza init

# Edit .rhiza/template.yml to select desired templates
# Then materialize the templates
uvx rhiza materialize
```

**Options:**
- `--branch <branch>` - Use a specific rhiza branch (default: main)
- `--help` - Show detailed usage information

### Manual Integration (Selective Adoption)

For cherry-picking specific templates or customising before integration:

1. **Clone Rhiza** to a temporary location:
   ```bash
   cd /tmp
   git clone https://github.com/jebel-quant/rhiza.git
   ```

2. **Copy desired templates** to your project:
   ```bash
   cd /path/to/your/project
   git checkout -b rhiza
   mkdir -p .github/workflows .rhiza/scripts
   cp /tmp/rhiza/.rhiza/template.yml .rhiza/template.yml
   cp /tmp/rhiza/.rhiza/scripts/sync.sh .rhiza/scripts
   ```

3. **Run the sync script**:
   ```bash
   ./.rhiza/scripts/sync.sh
   git status
   git diff  # Review changes
   ```

4. **Commit and push** if satisfied with the changes

### Automated Sync (Continuous Updates)

Keep your templates up-to-date with automated sync workflows:

- Configure `.rhiza/template.yml` to define which templates to include/exclude
- The `.github/workflows/sync.yml` workflow runs on schedule or manually
- Creates pull requests with template updates

For GitHub Token configuration and details, see the [GitHub Actions documentation](.github/README.md).

### What to Expect After Integration

- **Automated CI/CD** - GitHub Actions workflows for testing, linting, and releases
- **Code Quality Tools** - Pre-commit hooks, ruff formatting, and pytest configuration
- **Task Automation** - Makefile with common development tasks
- **Dev Container** - Optional VS Code/Codespaces environment
- **Documentation** - Automated documentation generation

### Troubleshooting Integration

- **Makefile conflicts**: Merge targets with existing build scripts
- **Pre-commit failures**: Run `make fmt` to fix formatting issues
- **Workflow failures**: Check Python version in `.python-version` and `pyproject.toml`
- **Dev container issues**: See [.devcontainer/README.md](.devcontainer/README.md)

## 📋 Available Tasks

The project uses a [Makefile](Makefile) as the primary entry point for all tasks, powered by [uv](https://github.com/astral-sh/uv) for fast Python package management.

### Key Commands

```bash
make install         # Install dependencies and setup environment
make test            # Run test suite with coverage
make fmt             # Format and lint code
make sync            # Sync with template repository
make release         # Create and publish a new release
make marimo          # Start Marimo notebook server
make book            # Build documentation
```

Run `make help` for a complete list of 40+ available targets.

<details>
<summary>Show all available targets</summary>

```makefile
  ____  _     _
 |  _ \| |__ (_)______ _
 | |_) | '_ \| |_  / _\`|
 |  _ <| | | | |/ / (_| |
 |_| \_\_| |_|_/___\__,_|

Usage:
  make <target>

Targets:

Rhiza Workflows
  sync                  sync with template repository as defined in .rhiza/template.yml
  validate              validate project structure against template repository as defined in .rhiza/template.yml
  readme                update README.md with current Makefile help output

Bootstrap
  install-uv            ensure uv/uvx is installed
  install               install
  clean                 Clean project artifacts and stale local branches

Quality and Formatting
  deptry                Run deptry
  fmt                   check the pre-commit hooks and the linting

Releasing and Versioning
  bump                  bump version
  release               create tag and push to remote with prompts

Meta
  help                  Display this help message
  version-matrix        Emit the list of supported Python versions from pyproject.toml

Development and Testing
  test                  run all tests
  benchmark             run performance benchmarks

Documentation
  docs                  create documentation with pdoc
  book                  compile the companion book

Marimo Notebooks
  marimo-validate       validate all Marimo notebooks can run
  marimo                fire up Marimo server
  marimushka            export Marimo notebooks to HTML

Presentation
  presentation          generate presentation slides from PRESENTATION.md using Marp
  presentation-pdf      generate PDF presentation from PRESENTATION.md using Marp
  presentation-serve    serve presentation interactively with Marp

Docker
  docker-build          build Docker image 
  docker-run            run the Docker container
  docker-clean          remove Docker image

Agentic Workflows
  copilot               open interactive prompt for copilot
  analyse-repo          run the analyser agent to update REPOSITORY_ANALYSIS.md
  summarise-changes     summarise changes since the most recent release/tag
  install-copilot       checks for copilot and prompts to install

GitHub Helpers
  gh-install            check for gh cli existence and install extensions
  view-prs              list open pull requests
  view-issues           list open issues
  failed-workflows      list recent failing workflow runs
  whoami                check github auth status

Custom Tasks
  hello-rhiza           a custom greeting task
  post-install          run custom logic after core install

```

</details>

> **Note:** The help output is automatically generated from the Makefile.
> When you modify Makefile targets, run `make readme` to update this section,
> or the pre-commit hook will update it automatically.

## 🎯 Advanced Topics

### Marimo Notebooks

This project supports [Marimo](https://marimo.io/) notebooks for interactive documentation and exploration.

```bash
make marimo  # Start Marimo server
```

For configuration details including dependency management and pythonpath setup, see the [Marimo documentation](https://marimo.io/).

### Presentations

Generate presentation slides using [Marp](https://marp.app/):

```bash
make presentation        # Generate HTML slides
make presentation-pdf    # Generate PDF slides
make presentation-serve  # Serve with live reload
```

For detailed information about creating and customising presentations, see [presentation/README.md](presentation/README.md).

### Testing Documentation

README code blocks are automatically tested. See [tests/test_config_templates/test_readme.py](tests/test_config_templates/test_readme.py) for details.

```python
# Example code block
import math
print("Hello, World!")
print(1 + 1)
print(round(math.pi, 2))
print(round(math.cos(math.pi/4.0), 2))
```

```result
Hello, World!
2
3.14
0.71
```

### Documentation Customisation

For information on customising the look and feel of your documentation, see [book/README.md](book/README.md).

### Python Version Management

The `.python-version` file specifies the default Python version for local development. Tools like `uv` and `pyenv` automatically use this version. Simply update this file to change your local Python version.

### Makefile Customisation

Rhiza uses a modular Makefile system with extension points (hooks) for customisation. See [.rhiza/make.d/README.md](.rhiza/make.d/README.md) for the complete guide including:
- Extension points and hooks
- Custom target creation
- Module ordering conventions

### Custom Build Scripts

For system dependencies and custom build steps, see [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md).

### Release Management

For information on versioning, tagging, and publishing releases, see [docs/RELEASING.md](docs/RELEASING.md).

### Dev Container

This repository includes a template Dev Container configuration for seamless development in VS Code and GitHub Codespaces. See [.devcontainer/README.md](.devcontainer/README.md) for setup, configuration, and troubleshooting.

## 🔄 CI/CD Support

### GitHub Actions

The `.github/` directory contains comprehensive GitHub Actions workflows for:
- CI testing across multiple Python versions
- Pre-commit checks and code quality
- Dependency checking with deptry
- Documentation building
- Docker and devcontainer validation
- Release automation
- Template synchronization

### GitLab CI/CD

Rhiza provides GitLab CI/CD workflow configurations with feature parity to GitHub Actions. The `.gitlab/` directory includes workflows for CI, validation, dependency checking, documentation, sync, and releases.

**Quick setup:**
```bash
cp -r .gitlab/ /path/to/your/project/
cp .gitlab-ci.yml /path/to/your/project/
```

For complete GitLab setup instructions, configuration variables, and troubleshooting, see **[.gitlab/README.md](.gitlab/README.md)**.

## 🛠️ Contributing to Rhiza

Contributions are welcome! To contribute to Rhiza itself (not using Rhiza in your project):

1. Fork the repository
2. Clone and setup:
   ```bash
   git clone https://github.com/your-username/rhiza.git
   cd rhiza
   make install
   ```
3. Create your feature branch (`git checkout -b feature/amazing-feature`)
4. Make your changes and test (`make test && make fmt`)
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [GitHub Actions](https://github.com/features/actions) - For CI/CD capabilities
- [Marimo](https://marimo.io/) - For interactive notebooks
- [UV](https://github.com/astral-sh/uv) - For fast Python package operations
- [Ruff](https://github.com/astral-sh/ruff) - For Python linting and formatting
- [Marp](https://marp.app/) - For presentation generation
