# GitHub Configuration

This directory contains GitHub-specific configuration files and workflows for the Rhiza project.

## Contents

- `workflows/`: GitHub Actions workflow definitions for CI/CD, documentation, and maintenance.
- `dependabot.yml`: Configuration for Dependabot to keep dependencies up to date.

## Workflows

The project uses GitHub Actions for:
- **CI**: Continuous Integration running tests across multiple Python versions.
- **Pre-commit**: Running linting and formatting checks.
- **Deptry**: Checking for dependency issues.
- **Book**: Building and deploying the companion book.
- **Marimo**: Exporting interactive notebooks to HTML.
- **Release**: Automating the release process and publishing to PyPI/GitHub Releases.
- **Sync**: Synchronizing the repository with its template.
- **Validate**: Validating project structure and configuration.
- **Docker**: Building and pushing Docker images.
- **Devcontainer**: Building and testing the Dev Container.
- **CodeQL**: Static analysis for security vulnerabilities.
