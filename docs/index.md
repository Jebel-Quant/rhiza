# Rhiza Documentation

**Rhiza** is a collection of reusable configuration templates for modern Python projects.
Save time and maintain consistency across your projects with pre-configured, living templates that evolve alongside your codebase.

> In the original Greek, spelt **ῥίζα**, pronounced *ree-ZAH*, and having the literal meaning **root**.

## What is Rhiza?

Unlike traditional one-shot project templates (like cookiecutter or copier), Rhiza provides **living templates** that support continuous synchronisation. When best practices evolve, you can selectively pull template updates into your project through automated workflows — no manual tracking of upstream changes required.

Rhiza has two components:

- **[rhiza](https://github.com/jebel-quant/rhiza)** — the *template content*: curated configuration files, Makefile modules, CI/CD workflows, and tooling.
- **[rhiza-cli](https://pypi.org/project/rhiza-cli/)** — the *CLI engine*: a separate package (run via `uvx`) providing `init`, `sync`, `bump`, and `release` commands.

## Quick Start

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialise Rhiza configuration
uvx rhiza init

# Review .rhiza/template.yml, then apply the templates
uvx rhiza sync
```

See the [Quick Reference](guides/QUICK_REFERENCE.md) for a concise command overview, or the [Demo](guides/DEMO.md) for a hands-on walkthrough.

## Explore the Documentation

| Section | Description |
|---------|-------------|
| [Quick Reference](guides/QUICK_REFERENCE.md) | Common commands and tasks at a glance |
| [Architecture](reference/ARCHITECTURE.md) | System diagrams and component overview |
| [Extending Rhiza](guides/EXTENDING_RHIZA.md) | Customising and extending Rhiza for your project |
| [Dependencies](reference/DEPENDENCIES.md) | Dependency management with uv and deptry |
| [Docker](development/DOCKER.md) | Containerisation support |
| [Dev Container](development/DEVCONTAINER.md) | VS Code / GitHub Codespaces setup |
| [Marimo](development/MARIMO.md) | Interactive notebook integration |
| [Glossary](reference/GLOSSARY.md) | Key terms and concepts |
| [ADR Overview](adr/README.md) | Architecture Decision Records |
