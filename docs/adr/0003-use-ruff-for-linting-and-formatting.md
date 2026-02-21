# 3. Use Ruff for Linting and Formatting

Date: 2024-06-01

## Status

Accepted

## Context

Python projects traditionally require multiple separate tools to cover code quality
concerns: `flake8` (or `pylint`) for style and error checking, `black` for formatting,
`isort` for import sorting, and `pyupgrade` for modernising syntax. Running these tools
individually involves:

- Managing multiple tool configurations spread across different files
- Coordinating tool versions to avoid conflicting opinions on style
- Longer CI run times as each tool makes a separate pass over the codebase
- Pre-commit configuration referencing four or more distinct hooks

As a template system that downstream projects adopt wholesale, Rhiza must keep its
development toolchain simple, fast, and easy for contributors to reason about.
Configuration complexity in Rhiza becomes configuration complexity for every project
that syncs from it.

## Decision

We will use [Ruff](https://github.com/astral-sh/ruff) as the single tool for Python
linting and formatting, replacing `flake8`, `black`, `isort`, and `pyupgrade`.

**Key aspects:**

1. **Single binary**: Ruff is a single executable, installable via `uv` alongside other
   development dependencies.
2. **Configuration**: All Ruff configuration lives in a single `ruff.toml` file in the
   project root.
3. **Two modes**: `ruff check` for linting (with `--fix` for auto-fixing) and
   `ruff format` for formatting.
4. **Pre-commit integration**: The `.pre-commit-config.yaml` uses the official
   `ruff-pre-commit` hooks, replacing multiple legacy hooks.
5. **Rule selection**: We enable a curated set of rule prefixes (`E`, `F`, `I`, `UP`,
   `B`, `SIM`) that replicate the coverage of the replaced tools.
6. **Formatting target**: Ruff format targets the Python version specified in
   `pyproject.toml` (`requires-python`).

The `make fmt` target runs:

```bash
uv run ruff format .
uv run ruff check --fix .
```

## Consequences

### Positive

- **Speed**: Ruff is written in Rust and is typically 10–100× faster than the Python
  tools it replaces, making `make fmt` near-instant even on large codebases.
- **Single configuration file**: `ruff.toml` replaces `.flake8`, `pyproject.toml`
  black/isort sections, and other scattered tool configs.
- **Fewer dependencies**: One tool instead of four reduces the dependency surface area.
- **Consistent output**: A single tool with a unified opinion eliminates conflicts
  between formatters and linters (e.g., black and isort disagreeing on trailing commas).
- **Active development**: Ruff is under active development and rapidly adds support for
  new rules and capabilities.

### Neutral

- **Rule differences**: Some flake8 plugins have no direct Ruff equivalent. Teams must
  evaluate whether missing rules are critical to their workflow.
- **Formatting choices**: Ruff format follows Black's style. Teams that prefer different
  formatting conventions may need to configure overrides.

### Negative

- **Single vendor**: Ruff is maintained by Astral. The tool is open source (MIT licence),
  which provides continuity guarantees, but project momentum is tied to one organisation.
- **Learning curve**: Teams migrating from established tools need to learn Ruff's rule
  codes and configuration syntax.
