# 9. Use Pre-commit Hooks for Automated Code Quality Enforcement

Date: 2024-04-01

## Status

Accepted

## Context

Code quality tools (linters, formatters, security scanners) are most valuable when they
run consistently and automatically. Relying on developers to remember to run `make fmt`
before every commit leads to:

- Style violations slipping into the repository and requiring separate clean-up commits.
- CI failures on trivial issues (missing newlines, import order) that block PRs
  unnecessarily.
- Inconsistent enforcement—some contributors run the tools, others do not.
- Review overhead as reviewers catch style issues that tooling should have caught.

The alternative—running all quality checks only in CI—creates a slow feedback loop.
Developers learn about formatting issues only after pushing a commit and waiting for
CI to complete.

## Decision

We will use [pre-commit](https://pre-commit.com/) to run code quality hooks automatically
on every commit, enforcing standards at the point of authorship.

**Key aspects:**

1. **Configuration file**: All hooks are defined in `.pre-commit-config.yaml` in the
   project root.
2. **Core hooks**: The standard configuration includes:
   - `check-toml`, `check-yaml` — syntax validation for TOML and YAML files
   - `ruff` — Python linting with auto-fix
   - `ruff-format` — Python formatting
   - `markdownlint` — Markdown style enforcement
   - `check-jsonschema` — schema validation for configuration files
   - `actionlint` — GitHub Actions workflow syntax validation
   - `validate-pyproject` — `pyproject.toml` schema validation
   - `bandit` — Python security scanning
   - `uv-lock` — ensures `uv.lock` is up-to-date
   - `rhiza-hooks` — custom Rhiza-specific checks (workflow naming, Makefile targets,
     Python version consistency)
3. **Installation**: `make install` installs pre-commit hooks via `uv run pre-commit install`.
4. **CI enforcement**: The `rhiza_pre-commit.yml` GitHub Actions workflow runs all hooks
   in CI to catch any commits that bypassed local hooks.
5. **Auto-fix in CI**: The CI workflow applies auto-fixes and commits them back,
   reducing friction for contributors who forget to run hooks locally.

## Consequences

### Positive

- **Shift-left quality**: Issues are caught at commit time, before they enter the
  repository and slow down CI.
- **Consistent enforcement**: Every contributor gets the same checks regardless of their
  local tooling setup.
- **Reduced review noise**: Reviewers spend time on logic, not style. Automated tools
  handle formatting and trivial issues.
- **Self-updating**: `pre-commit autoupdate` (run periodically) keeps hook versions
  current. Renovate can automate this.
- **Extensible**: New tools are added by appending to `.pre-commit-config.yaml` with no
  change to the Makefile.

### Neutral

- **Slower commits**: Running all hooks on every commit adds latency. For large
  codebases this can be several seconds. Pre-commit only runs hooks on changed files,
  keeping this manageable.
- **Occasional bypasses needed**: Urgent fixes sometimes require `git commit --no-verify`
  to skip hooks. This is an escape hatch, not a workflow pattern.

### Negative

- **Bootstrap dependency**: Pre-commit must be installed for hooks to run. If a
  contributor skips `make install`, they will not have hooks. The CI enforcement
  provides a backstop in this case.
- **Hook version drift**: Hook repositories release new versions independently. Outdated
  hooks may fail with newer tool versions. Regular `pre-commit autoupdate` runs
  (automated via Renovate) mitigate this.
