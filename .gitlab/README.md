# GitLab CI/CD Configuration

This directory contains the GitLab CI/CD configuration for the rhiza project.

## Structure

```
.gitlab/
├── scripts -> ../.github/rhiza/scripts  # Symbolic link to shared scripts
├── utils -> ../.github/rhiza/utils      # Symbolic link to shared utilities
└── README.md                             # This file
```

## Purpose

This setup enables the reuse of scripts and utilities between GitHub Actions and GitLab CI/CD:

- **scripts/**: Contains shell scripts for building documentation, bumping versions, releases, etc.
  - `book.sh` - Build combined documentation
  - `bump.sh` - Version bumping
  - `release.sh` - Release management
  - `marimushka.sh` - Marimo notebook processing
  - `update-readme-help.sh` - Update README with Makefile help

- **utils/**: Contains Python utilities for version management
  - `version_matrix.py` - Generate Python version matrix for CI
  - `version_max.py` - Get maximum supported Python version

## Symbolic Links

The symbolic links in this directory point to the shared scripts and utilities in `.github/rhiza/`.
This approach allows us to:

1. Maintain a single source of truth for reusable scripts
2. Reduce code duplication across CI/CD platforms
3. Ensure consistency between GitHub Actions and GitLab CI/CD workflows
4. Make updates in one place that benefit both platforms

## Usage in GitLab CI

The `.gitlab-ci.yml` file at the root of the repository references these scripts and utilities:

```yaml
# Example usage in .gitlab-ci.yml
script:
  - python .gitlab/utils/version_max.py
  - sh .gitlab/scripts/book.sh
```

## Maintenance

When updating scripts:

1. Edit the original files in `.github/rhiza/scripts/` or `.github/rhiza/utils/`
2. Changes will automatically be reflected in `.gitlab/` due to symbolic links
3. Test changes in both GitHub Actions and GitLab CI/CD workflows

## See Also

- `.gitlab-ci.yml` - Main GitLab CI/CD configuration
- `.github/workflows/` - GitHub Actions workflows
- `.github/rhiza/` - Shared scripts and utilities
- `Makefile` - Local development tasks
