---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

# :material-sprout: Rhiza

**Reusable Configuration Templates for Modern Python Projects**

Living templates that evolve with your project — not one-time snapshots.

[Get Started](getting-started/quickstart.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/jebel-quant/rhiza){ .md-button }

</div>

---

<div class="grid cards" markdown>

- :material-sync: **Living Templates**

    Stay synchronized with upstream improvements automatically
    
    ---
    
    Unlike one-shot generators, Rhiza templates remain connected to their source

- :material-test-tube: **Testing Ready**

    pytest configuration and coverage out of the box
    
    ---
    
    CI matrix testing across Python 3.11, 3.12, 3.13, and 3.14

- :material-rocket-launch: **CI/CD Workflows**

    GitHub Actions & GitLab CI included
    
    ---
    
    Pre-configured workflows for testing, releasing, and publishing

- :material-book-open-variant: **Documentation**

    pdoc, minibook, and Marimo support
    
    ---
    
    Multiple documentation formats to suit your project's needs

- :material-dev-to: **Dev Containers**

    VS Code and GitHub Codespaces ready
    
    ---
    
    Consistent development environments for your entire team

- :material-package-variant: **Modern Python**

    Built with uv, ruff, and best practices
    
    ---
    
    Blazing-fast dependency management and code quality tools

</div>

---

## Quick Overview

Rhiza provides **reusable configuration templates** that you can sync into your Python projects. Think of it as a living foundation that evolves with the ecosystem.

### For New Projects

```bash
git clone https://github.com/jebel-quant/rhiza.git my-project
cd my-project
make install  # Auto-installs uv, Python, and all dependencies
```

!!! success "Self-Contained Setup"
    No system Python or uv installation needed! `make install` handles everything automatically, installing to `./bin/` and `.venv/` locally.

### For Existing Projects

Rhiza integrates seamlessly with existing codebases:

```bash
cd /path/to/existing/project
# Copy Rhiza's Makefile and .rhiza/ directory
make install  # Auto-installs uv and dependencies
```

---

## What You Get

When you materialize Rhiza templates into your project:

- **40+ Make targets** for common development tasks
- **Pre-commit hooks** configured with ruff, mypy, and more
- **GitHub Actions workflows** for CI/CD
- **Dev container** configuration for consistent environments
- **Testing infrastructure** with pytest and coverage
- **Documentation tools** ready to use

---

## Key Features

### :material-sync-circle: Staying in Sync

Unlike traditional project generators that create files once and walk away, Rhiza maintains a connection to its templates. When best practices evolve or new tools emerge, you can pull in updates.

### :material-cog: Customization

Customize via hooks and overrides without losing the ability to sync:

- Pre/post-materialization hooks
- Template variable overrides
- Selective file exclusion
- Custom jinja2 extensions

### :material-shield-check: Production Ready

Battle-tested in production environments with support for:

- Private package repositories
- Token management
- Security scanning
- Release automation

---

## Learn More

<div class="grid cards" markdown>

- :material-book-open-page-variant: [**Quick Start**](getting-started/quickstart.md)
    
    Get up and running in 5 minutes

- :material-book-alphabet: [**User Guide**](WORKFLOWS.md)
    
    Learn development workflows

- :material-file-document: [**Reference**](QUICK_REFERENCE.md)
    
    Command reference and options

- :material-puzzle: [**Customization**](CUSTOMIZATION.md)
    
    Adapt Rhiza to your needs

</div>
