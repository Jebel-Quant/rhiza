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

![w:200](https://raw.githubusercontent.com/Jebel-Quant/rhiza/main/bundles/book/docs/assets/rhiza-logo.svg)

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
- Docs site with MkDocs + zensical
- API docs with mkdocstrings
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
- Security scanning (CodeQL, Scorecard)

---

## 🎯 Quick Start

### 1. Install the plugin (once)

```text
/plugin marketplace add Jebel-Quant/rhiza-claude
/plugin install rhiza@rhiza-claude
```

### 2. Adopt, in two pull requests

```text
/rhiza:init      # writes .rhiza/template.yml — the pointer. Merge it.
/rhiza:update    # the first sync: the workflows, the Makefile, the rest
```

`/rhiza:init` syncs nothing, so its PR looks almost empty — that is correct.

---

## 🔄 Template Synchronization

Templates stay up-to-date with Rhiza's latest improvements:

### Configuration: `.rhiza/template.yml`

```yaml
repository: "Jebel-Quant/rhiza"
ref: "v1.5.1"

profiles:
  - github-project

exclude: |
  docs/development/DOCKER.md
```

A profile expands to its bundles; `exclude` opts out of individual files.

---

## 🔄 Staying Current

Syncing is a local command, not a scheduled job — nothing needs a write-scoped
token on a timer:

- 🤖 Renovate opens a PR when the template's `ref` has a newer release
- 🔄 `/rhiza:update` applies it: fetch the bundles, three-way merge, open the PR
- 🔍 Only template-owned paths are staged — `.rhiza/template.lock` is the list
- 🎯 `exclude` patterns and local edits both survive
- 📋 `/rhiza:status --check` reports drift without changing anything

---

## 🛠️ Makefile: Your Command Center

```bash
make install      # Setup project with uv
make test         # Run pytest test suite
make fmt          # Run pre-commit hooks
make book         # Build the companion book
make book         # Build companion book
make presentation # Generate slides from PRESENTATION.md
make marimo       # Launch Marimo notebook server
```

**Note**: Releasing is driven by the rhiza-claude `/release` command, which bumps the version, regenerates the changelog, and creates the tag.

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

### Release (via rhiza-claude `/release`)

```text
/release
# → Derives the next version
# → Bumps pyproject.toml
# → Regenerates CHANGELOG.md
# → Creates the git tag locally
```

Pushing the tag triggers the release workflow. Releasing is not a `make` target.

### Check Status

```bash
make workflow-status
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

### Your own targets, in `local.mk`

The `Makefile` is template-owned and `-include`s `local.mk`, which no sync
touches. An explicit rule beats its `%:` catch-all, so shadowing extends a task:

```makefile
# local.mk — committed
install: $(UVX)
	@sudo apt-get update && sudo apt-get install -y graphviz
	@$(UVX) $(RHIZA_TASK) install

train-model: ## Train the ML model
	@uv run python scripts/train.py
```

Settings go in `pyproject.toml`'s `[tool.rhiza-task]` table.

---

## 🎨 Documentation Customization

### The docs site (MkDocs + zensical)

Override anything from the base config in your own `mkdocs.yml`:

```yaml
INHERIT: docs/mkdocs-base.yml

theme:
  logo: assets/my-logo.png
```

API pages come from mkdocstrings; extra packages go in the
`mkdocs-extra-packages` setting.

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
- 📝 **Documentation**: Auto-generated with `make book`

---

## 🙏 Acknowledgments

### Built With

- **GitHub Actions** — CI/CD automation
- **UV** — Fast Python package management
- **Ruff** — Fast Python linting
- **Pytest** — Testing framework
- **Marimo** — Interactive notebooks
- **Marp** — This presentation!
- **MkDocs + zensical** — The docs site
- **mkdocstrings** — API documentation

---

## 💡 Getting Started Today

### Three Simple Steps

1. **Install**: `/plugin install rhiza@rhiza-claude` in Claude Code
2. **Point**: `/rhiza:init` writes `.rhiza/template.yml` — review and merge
3. **Sync**: `/rhiza:update` brings the template content in

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
# Setup (in Claude Code)
# /rhiza:init                  # become rhiza-managed
# /rhiza:update                # sync the template content

# Development
make install                   # Install dependencies
make test                      # Run tests
make fmt                       # Format & lint

# Documentation
make book                      # Companion book
make book                      # Companion book
make presentation              # Generate slides

# Release (driven by the rhiza-claude /release command)
make workflow-status          # Show recent runs for the release workflow

# Notebooks
make marimo                    # Interactive notebooks
```

---

<!-- _class: lead -->

# Ready to Root Your Project?

**Get Started**: [github.com/jebel-quant/rhiza](https://github.com/jebel-quant/rhiza)

![w:300](https://raw.githubusercontent.com/Jebel-Quant/rhiza/main/bundles/book/docs/assets/rhiza-logo.svg)

