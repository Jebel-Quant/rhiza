"""Rhiza - Reusable Configuration Templates for Modern Python Projects.

**Rhiza** is a collection of battle-tested, reusable configuration templates for modern Python projects.
It provides ready-to-use templates for CI/CD, testing, documentation, code quality tools, and more,
helping you bootstrap new projects quickly or bring best practices to existing ones.

## Overview

Rhiza (from the Greek "rhiza" meaning "root") provides the foundational templates you need to:

- 🚀 **Bootstrap projects faster** - Start with production-ready configurations
- 🔄 **Stay up-to-date** - Sync with the latest best practices automatically
- 📊 **Maintain consistency** - Use the same setup across all your projects
- 🧪 **Focus on code** - Spend less time on configuration, more on implementation

## Quick Start

### Installation

The fastest way to integrate Rhiza into a new or existing project:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Run the injection script
uvx rhiza .
```

This command will:
1. Create a template configuration file (`.github/template.yml`)
2. Perform an initial sync of templates
3. Provide next steps for customization

### Using a Different Branch

```bash
# Use a development or feature branch
uvx rhiza --branch develop .
```

## Core Components

### 1. Configuration Templates

Rhiza provides templates organized by purpose:

#### Core Project Configuration
Essential files that define project structure and standards:

- **`.gitignore`** - Sensible defaults for Python projects
- **`.editorconfig`** - Consistent coding standards across editors
- **`ruff.toml`** - Modern Python linter and formatter configuration
- **`pytest.ini`** - Testing framework configuration
- **`Makefile`** - Common development task automation
- **`pyproject.toml`** - Modern Python project metadata
- **`CODE_OF_CONDUCT.md`** - Community guidelines
- **`CONTRIBUTING.md`** - Contribution guidelines

#### Developer Experience
Tools that improve local development:

- **`.devcontainer/`** - VS Code Dev Containers and GitHub Codespaces setup
- **`.pre-commit-config.yaml`** - Automated code quality checks
- **`docker/`** - Example Dockerfile and .dockerignore

#### CI/CD & Automation
Continuous integration and deployment:

- **`.github/workflows/`** - GitHub Actions workflows for:
  - Testing (`ci.yml`)
  - Pre-commit checks (`pre-commit.yml`)
  - Dependency analysis (`deptry.yml`)
  - Documentation generation (`book.yml`, `docs.yml`)
  - Release automation (`release.yml`)
  - Template synchronization (`sync.yml`)
  - Marimo notebook support (`marimo.yml`)

### 2. The Makefile

Rhiza includes a comprehensive [Makefile](https://github.com/Jebel-Quant/rhiza/blob/main/Makefile)
that serves as the primary entry point for all development tasks. Key targets include:

#### Bootstrap Commands
```bash
make install-uv     # Install uv/uvx package manager
make install        # Set up complete development environment
make clean          # Clean build artifacts
```

#### Development Commands
```bash
make test           # Run all tests with pytest
make fmt            # Format code and run pre-commit checks
make deptry         # Analyze dependencies
```

#### Documentation Commands
```bash
make docs           # Generate API documentation with pdoc
make book           # Generate companion documentation
make marimo         # Start Marimo notebook server
```

#### Release Commands
```bash
make bump           # Interactive version bumping
make release        # Create and push release tags
make post-release   # Run post-release tasks
```

#### Maintenance Commands
```bash
make sync           # Sync with Rhiza template repository
make update-readme  # Update README with current Makefile help
```

### 3. Template Synchronization

Rhiza can keep your project's configuration in sync with upstream changes.

#### Configuration File

The `.github/template.yml` file controls which templates are synced:

```yaml
# Template repository configuration
repository: jebel-quant/rhiza
branch: main

# Files to include in sync
include: |
  .github/workflows/ci.yml
  .github/workflows/pre-commit.yml
  .pre-commit-config.yaml
  Makefile
  ruff.toml
  pytest.ini

# Files to exclude (useful for customizations)
exclude: |
  .github/scripts/customisations/
  README.md
```

#### Manual Sync

Run synchronization manually:

```bash
make sync
```

Or using the script directly:

```bash
./.github/scripts/sync.sh
```

#### Automated Sync

The `.github/workflows/sync.yml` workflow can automatically:
- Run on a schedule (e.g., weekly)
- Run manually via GitHub Actions UI
- Create pull requests with template updates

## Integration Guide

### For New Projects

Start a new project with Rhiza templates:

```bash
# Create and navigate to your project
mkdir my-project && cd my-project
git init

# Inject Rhiza templates
uvx rhiza .

# Review and customize
git status
git diff

# Commit when ready
git add .
git commit -m "Initialize project with Rhiza templates"
```

### For Existing Projects

Bring Rhiza into an existing Python project:

```bash
# Create a feature branch
git checkout -b integrate-rhiza

# Inject templates
uvx rhiza .

# Review changes carefully
git status
git diff

# Test the integration
make install
make test
make fmt

# Create a pull request when ready
git add .
git commit -m "Integrate Rhiza configuration templates"
git push -u origin integrate-rhiza
```

### Selective Adoption

You can choose specific templates instead of adopting everything:

1. Clone Rhiza to a temporary location:
   ```bash
   git clone https://github.com/jebel-quant/rhiza.git /tmp/rhiza
   ```

2. Copy only the files you need:
   ```bash
   cp /tmp/rhiza/.github/workflows/ci.yml .github/workflows/
   cp /tmp/rhiza/Makefile .
   cp /tmp/rhiza/ruff.toml .
   ```

3. Customize `.github/template.yml` to include only those files

## Configuration

### Python Version Control

Rhiza workflows support Python 3.11 through 3.14. Control versions using repository variables:

- **`PYTHON_MAX_VERSION`** - Maximum version for CI testing matrix
  - Default: `'3.14'`
  - Set to `'3.11'` to test only on Python 3.11
  - Set to `'3.13'` to test on 3.11, 3.12, and 3.13

- **`PYTHON_DEFAULT_VERSION`** - Default version for single-version workflows
  - Default: `'3.14'`
  - Used in release, pre-commit, book, and marimo workflows

Configure these in: **Repository Settings → Secrets and variables → Actions → Variables**

### Custom Build Dependencies

Add system dependencies needed across all build phases:

1. Create `.github/scripts/customisations/build-extras.sh`:
   ```bash
   #!/bin/bash
   set -euo pipefail

   # Install graphviz for diagram generation
   sudo apt-get update
   sudo apt-get install -y graphviz
   ```

2. Make it executable:
   ```bash
   chmod +x .github/scripts/customisations/build-extras.sh
   ```

3. Exclude from template updates in `.github/template.yml`:
   ```yaml
   exclude: |
     .github/scripts/customisations/
   ```

The script runs automatically during `make install`, `make test`, `make docs`, and `make book`.

### Post-Release Hooks

Add custom post-release tasks:

1. Create `.github/scripts/customisations/post-release.sh`:
   ```bash
   #!/bin/bash
   set -euo pipefail

   echo "Running custom post-release tasks..."
   # Add your custom commands here
   ```

2. Make it executable and exclude from sync as shown above

The script runs automatically after `make release`.

## Development Workflow

### Day-to-Day Development

```bash
# Install/update dependencies
make install

# Run tests as you develop
make test

# Format and lint code
make fmt

# Check dependencies
make deptry

# Update documentation
make docs
make book
```

### Pre-Commit Integration

Rhiza includes pre-commit hooks that run automatically on `git commit`:

- **Ruff** - Linting and formatting
- **Trailing whitespace** - Remove trailing spaces
- **End of file** - Ensure files end with newline
- **YAML/TOML/JSON** - Validate syntax
- **Large files** - Prevent committing large files
- **Deptry** - Check for dependency issues

Install hooks:
```bash
make install  # Installs pre-commit hooks automatically
```

### Release Workflow

Rhiza provides an interactive release process:

1. **Bump the version:**
   ```bash
   make bump
   ```
   - Select bump type (patch/minor/major) or enter specific version
   - Commits the version change
   - Pushes to remote

2. **Create the release:**
   ```bash
   make release
   ```
   - Creates a git tag
   - Pushes the tag to trigger the release workflow
   - GitHub Actions publishes to PyPI (if configured)

The process includes safety checks to prevent mistakes.

## Dev Container Support

### VS Code & GitHub Codespaces

Rhiza templates include a complete `.devcontainer` configuration:

- **Python 3.14** runtime
- **UV Package Manager** pre-installed
- **Makefile** integration
- **Pre-commit hooks** ready to use
- **Marimo extension** for interactive notebooks
- **Port forwarding** for development servers (port 8080)
- **SSH agent forwarding** for Git operations

### Using in VS Code

1. Install the "Dev Containers" extension
2. Open the project folder
3. Click "Reopen in Container"
4. Environment sets up automatically

### Using in GitHub Codespaces

1. Navigate to your repository on GitHub
2. Click "Code" → "Codespaces" → "Create codespace"
3. Your environment is ready in minutes

### SSH Configuration (macOS)

For macOS users, add this to `~/.ssh/config` to avoid SSH issues in containers:

```ssh-config
# At the top of the file
IgnoreUnknown UseKeychain

Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
```

## Testing Documentation

Rhiza includes a unique feature: **executable documentation**.

Code blocks in your `README.md` can be tested automatically:

````markdown
```python
import math
print("Hello, World!")
print(round(math.pi, 2))
```
````

Expected output:

````markdown
```result
Hello, World!
3.14
```
````

The `test_readme.py` test will verify that the code produces the expected output,
ensuring your documentation examples always work.

## Marimo Notebook Integration

Rhiza includes first-class support for [Marimo](https://marimo.io/) notebooks:

### Running Notebooks

```bash
make marimo
```

### Configuration

Add to `pyproject.toml`:

```toml
[tool.marimo.runtime]
pythonpath = ["src"]
```

### Notebook Dependencies

Use inline script metadata to make notebooks self-contained:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas",
#     "your-package",
# ]
#
# [tool.uv.sources]
# your-package = { path = "../.." }
# ///

import marimo as mo
import pandas as pd
import your_package
```

## Documentation Customization

### API Documentation (pdoc)

Customize API docs by creating templates:

1. Create `book/pdoc-templates/` directory
2. Add Jinja2 templates (e.g., `module.html.jinja2`)
3. Run `make docs` to use your templates

See [pdoc templating docs](https://pdoc.dev/docs/pdoc.html#templates).

### Companion Book (minibook)

Customize the companion book:

1. Create `book/minibook-templates/custom.html.jinja2`
2. Run `make book` to use your template

## Examples

### Real-World Projects Using Rhiza

Rhiza templates are used in production by several projects. Here are examples:

- **[Rhiza itself](https://github.com/Jebel-Quant/rhiza)** - A meta example
- Your project could be here!

### Example Template Configuration

Minimal `.github/template.yml`:

```yaml
repository: jebel-quant/rhiza
branch: main
include: |
  Makefile
  ruff.toml
  pytest.ini
  .github/workflows/ci.yml
```

Full-featured configuration:

```yaml
repository: jebel-quant/rhiza
branch: main
include: |
  .github/
  .editorconfig
  .gitignore
  .pre-commit-config.yaml
  Makefile
  ruff.toml
  pytest.ini
exclude: |
  .github/scripts/customisations/
  .github/workflows/release.yml
  README.md
  pyproject.toml
```

## Troubleshooting

### Common Issues

#### Pre-commit hooks fail on existing code

```bash
# Fix formatting issues automatically
make fmt

# Or skip pre-commit temporarily
git commit --no-verify
```

#### GitHub Actions workflows fail

- Check Python version compatibility
- Adjust `PYTHON_MAX_VERSION` repository variable
- Review workflow logs in Actions tab

#### Makefile targets conflict with existing scripts

- Review and merge conflicting targets
- Rename targets in your Makefile
- Selectively exclude Makefile from sync

#### Dev container fails to build

- Check Docker is running
- Review `.devcontainer/devcontainer.json`
- Ensure all dependencies are available

#### Template sync creates merge conflicts

- Review changes carefully before merging
- Use `exclude` in `.github/template.yml` for customized files
- Manually resolve conflicts if needed

### Getting Help

- **Documentation**: [README.md](https://github.com/Jebel-Quant/rhiza/blob/main/README.md)
- **Issues**: [GitHub Issues](https://github.com/Jebel-Quant/rhiza/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Jebel-Quant/rhiza/discussions)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](https://github.com/Jebel-Quant/rhiza/blob/main/CONTRIBUTING.md)
for guidelines.

### Areas for Contribution

- New configuration templates
- Additional CI/CD workflow examples
- Documentation improvements
- Bug fixes and enhancements
- Real-world usage examples

## License

Rhiza is released under the [MIT License](https://github.com/Jebel-Quant/rhiza/blob/main/LICENSE).

## Links

- **Repository**: [https://github.com/Jebel-Quant/rhiza](https://github.com/Jebel-Quant/rhiza)
- **Documentation**: [https://jebel-quant.github.io/rhiza](https://jebel-quant.github.io/rhiza)
- **PyPI**: [https://pypi.org/project/rhiza](https://pypi.org/project/rhiza)
- **Issues**: [https://github.com/Jebel-Quant/rhiza/issues](https://github.com/Jebel-Quant/rhiza/issues)
- **Changelog**: [https://github.com/Jebel-Quant/rhiza/releases](https://github.com/Jebel-Quant/rhiza/releases)

---

*Built with ❤️ by the Jebel Quant team*
"""

from importlib.metadata import version

__version__ = version("rhiza")
__all__ = ["__version__"]
