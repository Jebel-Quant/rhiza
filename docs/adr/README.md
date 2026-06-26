# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Rhiza project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## ADR Format

Each ADR follows a consistent format:

- **Title and Number**: Sequential numbering with descriptive title
- **Date**: When the decision was made
- **Status**: Current state (Proposed, Accepted, Deprecated, Superseded)
- **Context**: The issue or situation that motivates the decision
- **Decision**: The change or approach being taken
- **Consequences**: What becomes easier or harder as a result

## ADR Index

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0001](0001-use-architecture-decision-records.md) | Use Architecture Decision Records | Accepted | 2026-01-01 |
| [0002](0002-use-uv-for-python-package-management.md) | Use uv for Python Package and Environment Management | Accepted | 2024-09-01 |
| [0003](0003-use-ruff-for-linting-and-formatting.md) | Use Ruff for Linting and Formatting | Accepted | 2024-06-01 |
| [0004](0004-adopt-modular-makefile-architecture.md) | Adopt a Modular Makefile Architecture | Accepted | 2024-03-01 |
| [0005](0005-separate-rhiza-template-from-cli.md) | Separate rhiza Template Repository from rhiza-cli | Accepted | 2024-05-01 |
| [0006](0006-organise-templates-into-bundles.md) | Organise Templates into Bundles | Accepted | 2025-01-01 |
| [0007](0007-support-dual-cicd-github-and-gitlab.md) | Support Dual CI/CD with GitHub Actions and GitLab CI | Accepted | 2024-08-01 |
| [0008](0008-use-marimo-for-interactive-notebooks.md) | Use Marimo for Interactive Notebooks | Accepted | 2025-03-01 |
| [0009](0009-use-pre-commit-hooks-for-code-quality.md) | Use Pre-commit Hooks for Automated Code Quality Enforcement | Accepted | 2024-04-01 |
| [0010](0010-layered-bundle-profile-model.md) | Introduce a Layered Bundle and Profile Model | Accepted | 2026-05-02 |

## Creating a New ADR

To create an ADR manually:

1. Copy an existing ADR in this directory as a starting point
2. Use the next available 4-digit number (e.g., 0011, 0012)
3. Fill in all sections with relevant information
4. Update this README to add your ADR to the index
5. Submit via pull request for review

## Resources

- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's article on ADRs](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
