# 9. Use Pre-commit Hooks for Automated Code Quality Enforcement

Date: 2024-04-01

## Status

Accepted. Amended 2026-08-03: the runner is now
[prek](https://github.com/j178/prek) rather than pre-commit itself — see
**Amendment: prek** at the end of this record. Everything the decision rests on is
unchanged, including `.pre-commit-config.yaml` as the config format.

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
3. **Installation**: `make install` installs the hooks via `uvx prek install`.
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
- **Self-updating**: `prek update` (pre-commit's `autoupdate`) keeps hook versions
  current. Renovate automates it by reading `.pre-commit-config.yaml` directly.
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
  hooks may fail with newer tool versions. Regular `prek update` runs
  (automated via Renovate) mitigate this.

## Amendment: prek (2026-08-03)

The hook *runner* moved from pre-commit to [prek](https://github.com/j178/prek), a Rust
reimplementation that reads the same `.pre-commit-config.yaml`. None of the four
`.pre-commit-config.yaml` files changed, no hook was added or removed, and Renovate keeps
managing hook versions from the same file — so this amends how the decision is executed,
not the decision.

What actually changed:

- `make fmt` runs `uvx prek run --all-files --config .pre-commit-config.yaml`, and
  `make install` runs `uvx prek install`.
- **The `-p $(PYTHON_VERSION)` coupling is gone.** `uvx pre-commit` had to pick an
  interpreter to run pre-commit *itself* on, and a Rust or Go project ships no
  `.python-version` — so the language-neutral half of the template depended on
  `rhiza.mk`'s fallback resolving to a real version. prek is a binary and provisions each
  hook's toolchain itself, so the dependency is removed rather than satisfied.
- CI caches `~/.cache/prek` instead of `~/.cache/pre-commit`; the cache key still hashes
  `.pre-commit-config.yaml`.
- `--config` is passed explicitly. prek otherwise treats every nested
  `.pre-commit-config.yaml` as a separate project — good in a monorepo, wrong in this
  repo, where `bundles/{python,rust,go}-core` ship one each as template content. Without
  the flag, go-core's hooks run `go vet ./...` in a directory with no `go.mod` and fail.

The CI job keeps its id (`pre-commit`) and display name ("Pre-commit hooks"), because
that name is a required status check in `.github/rulesets/main-branch-protection.json`.
Renaming it would leave every PR waiting on a context that never reports.
