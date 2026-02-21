# Rhiza Documentation

**Rhiza** is a collection of reusable configuration templates for modern Python projects.
Save time and maintain consistency across your projects with pre-configured, living templates that evolve alongside your codebase.

> In the original Greek, spelt **ῥίζα**, pronounced *ree-ZAH*, and having the literal meaning **root**.

## What is Rhiza?

Unlike traditional one-shot project templates (like cookiecutter or copier), Rhiza provides **living templates** that support continuous synchronisation. When best practices evolve, you can selectively pull template updates into your project through automated workflows — no manual tracking of upstream changes required.

Rhiza has two components:

- **[rhiza](https://github.com/jebel-quant/rhiza)** — the *template content*: curated configuration files, Makefile modules, CI/CD workflows, and tooling.
- **[rhiza-cli](https://pypi.org/project/rhiza-cli/)** — the *CLI engine*: a separate package (run via `uvx`) providing `init`, `materialize`, `bump`, and `release` commands.

## Quick Start

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialise Rhiza configuration
uvx rhiza init

# Review .rhiza/template.yml, then apply the templates
uvx rhiza materialize
```

See the [Quick Reference](QUICK_REFERENCE.md) for a concise command overview, or the [Demo](DEMO.md) for a hands-on walkthrough.

## Explore the Documentation

| Section | Description |
|---------|-------------|
| [Quick Reference](QUICK_REFERENCE.md) | Common commands and tasks at a glance |
| [Architecture](ARCHITECTURE.md) | System diagrams and component overview |
| [Customization](CUSTOMIZATION.md) | Adapting Rhiza to your project's needs |
| [Extending Rhiza](EXTENDING_RHIZA.md) | Adding custom templates and hooks |
| [Dependencies](DEPENDENCIES.md) | Dependency management with uv and deptry |
| [Docker](DOCKER.md) | Containerisation support |
| [Dev Container](DEVCONTAINER.md) | VS Code / GitHub Codespaces setup |
| [Marimo](MARIMO.md) | Interactive notebook integration |
| [Security](SECURITY.md) | Security policy and reporting |
| [Glossary](GLOSSARY.md) | Key terms and concepts |
| [ADR Overview](adr/README.md) | Architecture Decision Records |
