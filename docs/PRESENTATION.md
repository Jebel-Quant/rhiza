---
marp: true
theme: default
paginate: true
backgroundColor: #fff
color: #2c3e50
style: |
  section {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
  h1 {
    color: #2FA4A9;
  }
  h2 {
    color: #2FA4A9;
  }
  code {
    background: #f5f5f5;
  }
  .columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }
---

<!-- _class: lead -->
# 🌱 Rhiza

**Reusable Configuration Templates for Modern Python Projects**

![w:200](assets/rhiza-logo.svg)

*ῥίζα (ree-ZAH) — Ancient Greek for "root"*

---

## 🤔 The Problem

Setting up a new Python project is time-consuming:

- ⚙️ Configuring CI/CD pipelines
- 🧪 Setting up testing frameworks
- 📝 Creating linting and formatting rules
- 📚 Configuring documentation generation
- 🔧 Establishing development workflows
- 🐳 Setting up dev containers

**Result**: Hours of configuration before writing actual code

---

## 💡 The Solution: Rhiza

A curated collection of **battle-tested templates** that:

✅ Save time on project setup
✅ Enforce best practices
✅ Maintain consistency across projects
✅ Stay up-to-date automatically
✅ Support multiple Python versions (3.11-3.14)

---

## ✨ Key Features

<div class="columns">
<div>

### 🚀 Automation
- GitHub Actions workflows
- Pre-commit hooks
- Automated releases
- Version bumping

### 🧪 Testing
- pytest configuration
- CI test matrix
- Code coverage
- Documentation tests

</div>
<div>

### 📚 Documentation
- API docs with pdoc
- Companion book with minibook
- Presentation slides with Marp
- Interactive notebooks

### 🔧 Developer Experience
- Dev containers
- VS Code integration
- GitHub Codespaces ready
- SSH agent forwarding

</div>
</div>

---

## 📁 Available Templates

### 🌱 Core Project Configuration
- `.gitignore` — Python project defaults
- `.editorconfig` — Consistent coding standards
- `ruff.toml` — Linting and formatting
- `pytest.ini` — Testing framework
- `Makefile` — Common development tasks
- `CODE_OF_CONDUCT.md` & `CONTRIBUTING.md`

---

## 📁 Available Templates (cont.)

### 🔧 Developer Experience
- `.devcontainer/` — VS Code dev containers
- `.pre-commit-config.yaml` — Pre-commit hooks
- `docker/` — Dockerfile templates

### 🚀 CI/CD & Automation
- `.github/workflows/` — GitHub Actions
- Automated testing & releases
- Documentation generation
- Template synchronization

---

## 🎯 Quick Start

### 1. Automated Injection (Recommended)

```bash
cd /path/to/your/project
uvx rhiza .
```

This creates `.github/template.yml` and syncs templates automatically.

### 2. Manual Integration

```bash
# Clone Rhiza
git clone https://github.com/jebel-quant/rhiza.git /tmp/rhiza

# Copy sync mechanism
cp /tmp/rhiza/.github/template.yml .github/
cp /tmp/rhiza/.rhiza/scripts/sync.sh .rhiza/scripts/

# Sync templates
./.rhiza/scripts/sync.sh
```

---

## 🔄 Template Synchronization

Templates stay up-to-date with Rhiza's latest improvements:

### Configuration: `.github/template.yml`

```yaml
repository: Jebel-Quant/rhiza
ref: v0.7.1

include: |
  .github/workflows/*.yml
  .pre-commit-config.yaml
  ruff.toml
  pytest.ini

exclude: |
  .rhiza/scripts/customisations/*
```

---

## 🔄 Automated Sync Workflow

The `sync.yml` workflow keeps your project current:

- 📅 Runs weekly (configurable)
- 🔄 Fetches latest templates from Rhiza
- 🔍 Applies only included files
- 🎯 Respects exclude patterns
- 📝 Creates pull request with changes
- 🤖 Fully automated

**Manual trigger**: GitHub Actions → "Sync Templates" → "Run workflow"

---

## 🛠️ Makefile: Your Command Center

```bash
make install      # Setup project with uv
make test         # Run pytest test suite
make fmt          # Run pre-commit hooks
make docs         # Generate API documentation
make book         # Build companion book
make presentation # Generate slides from PRESENTATION.md
make marimo       # Launch Marimo notebook server
make bump         # Interactive version bump
make release      # Tag and release
```

**Tip**: Run `make help` to see all available targets

---

## 📊 Marimo Integration

[Marimo](https://marimo.io/) — Modern interactive Python notebooks

```bash
make marimo  # Start notebook server
```

### Features
- 🔄 Reactive execution
- 🐍 Pure Python (no JSON)
- 📦 Self-contained dependencies
- 🎨 Built-in visualizations
- 💻 VS Code extension support

Notebooks stored in `docs/notebooks/` with inline dependency management.

---

## 🚀 Release Workflow

### One-Step Publish (Recommended)

```bash
make publish
# → Bumps version + creates tag + pushes
# → Triggers release workflow
```

### Two-Step Process

```bash
# 1. Bump version
make bump
# → Interactive prompts for patch/minor/major
# → Updates pyproject.toml
# → Commits and pushes changes

# 2. Create release
make release
# → Creates git tag
# → Pushes tag to GitHub
# → Triggers release workflow
```

### Check Status

```bash
make release-status
# → Shows workflow run history
# → Shows latest release details
```

### Release Automation
✅ Builds Python package
✅ Creates GitHub release
✅ Publishes to PyPI (if public)
✅ Publishes devcontainer image (optional)

---

## 🐳 Dev Container Features

### What You Get

- 🐍 Python 3.14 runtime
- ⚡ UV package manager
- 🔧 All project dependencies
- 🧪 Pre-commit hooks
- 📊 Marimo integration
- 🔐 SSH agent forwarding
- 🚀 Port 8080 forwarding

### Usage

**VS Code**: Reopen in Container
**Codespaces**: Create codespace on GitHub

---

## 🔧 Customization

### Build Extras

Create `.rhiza/scripts/customisations/build-extras.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Install system dependencies
sudo apt-get update
sudo apt-get install -y graphviz

# Your custom setup here
```

Runs during: `make install`, `make test`, `make book`, `make docs`

---

## 🎨 Documentation Customization

### API Documentation (pdoc)

```bash
mkdir -p book/pdoc-templates
# Add custom Jinja2 templates
```

### Companion Book (minibook)

```bash
mkdir -p book/minibook-templates
# Create custom.html.jinja2
```

### Presentations (Marp)

Edit `PRESENTATION.md` and run:
```bash
make presentation      # Generate HTML
make presentation-pdf  # Generate PDF
make presentation-serve # Interactive preview
```

---

## ⚙️ Configuration Variables

Control Python versions via repository variables:

### `PYTHON_MAX_VERSION`
- Default: `'3.14'`
- Tests on 3.11, 3.12, 3.13, 3.14
- Set to `'3.13'` to exclude 3.14

### `PYTHON_DEFAULT_VERSION`
- Default: `'3.14'`
- Used in release, pre-commit, book workflows
- Set to `'3.12'` for compatibility

**Set in**: Repository Settings → Secrets and variables → Actions → Variables

---

## 🔍 Code Quality Tools

### Pre-commit Hooks
- ✅ YAML validation
- ✅ TOML validation
- ✅ Markdown formatting
- ✅ Trailing whitespace
- ✅ End-of-file fixes
- ✅ GitHub workflow validation

### Ruff
- Fast Python linter
- Replaces flake8, isort, pydocstyle
- Auto-fixing capabilities
- Extensive rule selection

---

## 🧪 Testing Philosophy

### What Gets Tested

- 📝 README code blocks
- 🔧 Shell scripts (bump, release)
- 🎯 Makefile targets
- 📁 Repository structure
- 📊 Marimo notebooks

### Test Command

```bash
make test
```

Runs `pytest` with coverage reporting and HTML output.

---

## 🌐 CI/CD Workflows

### 10 Automated Workflows

1. **CI** — Test matrix across Python versions
2. **PRE-COMMIT** — Validate code quality
3. **DEPTRY** — Check dependency usage
4. **BOOK** — Build documentation
5. **MARIMO** — Validate notebooks
6. **DOCKER** — Build and publish images
7. **DEVCONTAINER** — Validate dev environment
8. **RELEASE** — Automated releases
9. **SYNC** — Template synchronization
10. **RHIZA** — Self-injection test

---

## 📦 Package Publishing

### PyPI Publication

Automatic if configured as **Trusted Publisher**:

1. Register package on PyPI
2. Add GitHub Actions as trusted publisher
3. Release workflow publishes automatically

### Private Packages

Add to `pyproject.toml`:
```toml
classifiers = [
    "Private :: Do Not Upload",
]
```

---

## 🎯 Real-World Usage

### Perfect For:

- 🆕 New Python projects
- 🔄 Standardizing existing projects
- 👥 Team templates
- 📚 Educational projects
- 🏢 Corporate standards

### Not Ideal For:

- ❌ Non-Python projects
- ❌ Projects requiring exotic configurations
- ❌ One-off scripts

---

## 🏗️ Architecture Decisions

### Why Makefile?

- ✅ Universal (no language-specific tools)
- ✅ Self-documenting
- ✅ Easy to extend
- ✅ Works everywhere

### Why UV?

- ⚡ 10-100x faster than pip
- 📦 Handles entire Python ecosystem
- 🔒 Lock files for reproducibility
- 🎯 Single tool for everything

---

## 🤝 Contributing

### How to Contribute

1. 🍴 Fork the repository
2. 🌿 Create feature branch
3. ✍️ Make your changes
4. ✅ Run `make test` and `make fmt`
5. 📤 Submit pull request

### What to Contribute

- 🆕 New templates
- 🐛 Bug fixes
- 📚 Documentation improvements
- 💡 Feature suggestions

---

## 📈 Project Stats

- 🐍 **Python Versions**: 3.11, 3.12, 3.13, 3.14
- 📄 **License**: MIT
- 🏷️ **Current Version**: 0.3.0
- 🔧 **Templates**: 20+ configuration files
- 🤖 **Workflows**: 10 GitHub Actions
- ⭐ **Badge**: ![Created with Rhiza](https://img.shields.io/badge/synced%20with-rhiza-2FA4A9)

---

## 🔗 Useful Links

- 📖 **Repository**: [github.com/jebel-quant/rhiza](https://github.com/jebel-quant/rhiza)
- 📚 **Issues**: [github.com/jebel-quant/rhiza/issues](https://github.com/jebel-quant/rhiza/issues)
- 🚀 **Codespaces**: [Open in GitHub Codespaces](https://codespaces.new/jebel-quant/rhiza)
- 📝 **Documentation**: Auto-generated with `make docs`

---

## 🙏 Acknowledgments

### Built With

- **GitHub Actions** — CI/CD automation
- **UV** — Fast Python package management
- **Ruff** — Fast Python linting
- **Pytest** — Testing framework
- **Marimo** — Interactive notebooks
- **Marp** — This presentation!
- **pdoc** — API documentation
- **minibook** — Companion book

---

## 💡 Getting Started Today

### Three Simple Steps

1. **Try it**: `uvx rhiza .` in your project
2. **Review**: Check the generated `.github/template.yml`
3. **Sync**: Run `./.rhiza/scripts/sync.sh`

### Or Explore First

```bash
# Open in Codespaces
# → Click "Create codespace on main"

# Or clone locally
git clone https://github.com/jebel-quant/rhiza.git
cd rhiza
make install
make test
```

---

<!-- _class: lead -->

# 🎉 Thank You!

## Questions?

**Rhiza** — Your foundation for modern Python projects

*From the Greek ῥίζα (root) — because every great project needs strong roots*

---

## 📋 Quick Reference Card

```bash
# Setup
uvx rhiza .                    # Auto-inject Rhiza

# Development
make install                   # Install dependencies
make test                      # Run tests
make fmt                       # Format & lint

# Documentation
make docs                      # API documentation
make book                      # Companion book
make presentation              # Generate slides

# Release
make bump                      # Bump version
make release                   # Create release

# Notebooks
make marimo                    # Interactive notebooks
```

---

<!-- _class: lead -->

# Ready to Root Your Project?

**Get Started**: [github.com/jebel-quant/rhiza](https://github.com/jebel-quant/rhiza)

![w:300](assets/rhiza-logo.svg)
