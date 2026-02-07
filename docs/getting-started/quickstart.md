# Quick Start

Get up and running with Rhiza in 5 minutes.

---

## Prerequisites

Before you begin, ensure you have:

- **Git** for version control
- **Linux, macOS, or WSL2** (Windows native not supported)

!!! success "No Python or uv Installation Needed"
    Rhiza is **self-contained**. When you run `make install`, it automatically:
    
    - Installs `uv` to `./bin/` (if not in PATH)
    - Downloads Python via uv (no system Python needed)
    - Creates a project-local virtual environment
    
    Everything stays within your project directory.

---

## For New Projects

Start a fresh Python project with Rhiza templates:

=== "Using make (Recommended)"
    ```bash
    # Clone Rhiza
    git clone https://github.com/jebel-quant/rhiza.git my-project
    cd my-project
    
    # Auto-installs uv, Python, and all dependencies
    make install
    
    # Run tests to verify setup
    make test
    ```

=== "Using uvx (Global uv)"
    ```bash
    # If you have uv installed globally
    cd /path/to/your/project
    uvx rhiza init
    uvx rhiza materialize
    make install
    ```

---

## For Existing Projects

Integrate Rhiza into an existing Python codebase:

```bash
cd /path/to/existing/project
uvx rhiza init
# Edit .rhiza/template.yml to configure which files to sync
uvx rhiza materialize
```

!!! warning "Existing Files"
    Rhiza will prompt before overwriting existing files. Review changes carefully before proceeding.

---

## What Happens Next?

After running `rhiza materialize`, your project will have:

### :material-hammer-wrench: Development Tools

- **Makefile** with 40+ targets for common tasks
- **Pre-commit hooks** configured with ruff, mypy, and more
- **pyproject.toml** with modern Python tooling configured

### :material-test-tube: Testing Infrastructure

- **pytest** configuration with coverage tracking
- **Benchmark suite** for performance testing
- **CI matrix** testing across Python 3.11, 3.12, 3.13, and 3.14

### :material-rocket-launch: CI/CD Pipelines

- **GitHub Actions** workflows for:
    - Testing on every push
    - Automated releases
    - Documentation publishing
- **GitLab CI** configuration (optional)

### :material-dev-to: Development Environment

- **Dev container** for VS Code and GitHub Codespaces
- **Docker** configuration for containerized development
- Consistent environment across your team

### :material-book-open-variant: Documentation

- **pdoc** API documentation setup
- **MkDocs Material** theme configured
- **Marimo** notebooks for interactive documentation

---

## Next Steps

!!! success "You're Ready!"
    Your project is now set up with modern Python best practices.

<div class="grid cards" markdown>

- :material-tools: [**Learn the Workflow**](../WORKFLOWS.md)
    
    Discover common development tasks

- :material-puzzle: [**Customize Templates**](../CUSTOMIZATION.md)
    
    Adapt Rhiza to your needs

- :material-file-document: [**Command Reference**](../QUICK_REFERENCE.md)
    
    Explore all available commands

- :material-update: [**Stay Synchronized**](first-sync.md)
    
    Keep your project templates up to date

</div>

---

## Common Commands

Once set up, use these commands in your daily workflow:

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make test` | Run tests with coverage |
| `make fmt` | Format code with ruff |
| `make lint` | Check code quality |
| `make docs` | Build documentation |
| `make clean` | Clean build artifacts |

!!! tip "See All Commands"
    Run `make help` to see all available targets.

---

## Troubleshooting

### uv or Python not found

Run `make install` to auto-install everything:
```bash
make install
```

This installs `uv` to `./bin/` and creates `.venv/` with the correct Python version.

### Windows users

Rhiza requires **WSL2** (Windows Subsystem for Linux):

1. Install WSL2: [Microsoft's WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install)
2. Open WSL2 terminal
3. Clone Rhiza and run `make install`

!!! warning "Native Windows Not Supported"
    Rhiza uses POSIX shell scripts (`sh`) that require a Unix-like environment.

### Conflicts with existing files

Review the conflicts and choose whether to:
- Keep your existing files
- Replace with Rhiza templates
- Merge changes manually

---

## Getting Help

- :material-chat: [GitHub Discussions](https://github.com/jebel-quant/rhiza/discussions)
- :material-bug: [Report Issues](https://github.com/jebel-quant/rhiza/issues)
- :material-book: [Full Documentation](../index.md)
