# 8. Use Marimo for Interactive Notebooks

Date: 2025-03-01

## Status

Accepted

## Context

Rhiza's documentation system benefits from executable, interactive examples that
demonstrate template features, visualise data, and let users experiment directly
in the browser. Jupyter notebooks are the industry standard for this use case, but
they present challenges in a template context:

- **Diff noise**: Jupyter notebooks are JSON files. Cell outputs, execution counts,
  and metadata are embedded in the file, producing large, hard-to-review diffs when
  notebooks are run and re-committed.
- **State management**: Jupyter's implicit execution order (cells can be run out of
  order) makes notebooks fragile and hard to reproduce reliably.
- **Dependency on Jupyter server**: Running a Jupyter notebook requires starting a
  server process and managing kernel state. This adds complexity to CI pipelines and
  the `make book` build.
- **Static export quality**: Converting Jupyter notebooks to HTML for static
  documentation produces adequate but not polished output.
- **Not reactive**: Jupyter notebooks require manual re-execution when inputs change.

## Decision

We will use [Marimo](https://marimo.io/) as the interactive notebook runtime for
Rhiza's documentation examples and the companion book.

**Key aspects:**

1. **Pure Python files**: Marimo notebooks are valid Python scripts, not JSON. They
   produce clean, reviewable diffs and work naturally with Git.
2. **Reactive execution model**: Marimo re-executes cells automatically when their
   inputs change, eliminating hidden state and ensuring reproducibility.
3. **Static HTML export**: `marimo export html` produces polished standalone HTML
   pages suitable for the companion book.
4. **Development server**: `make marimo` starts the Marimo server for interactive
   development; `make marimushka` exports all notebooks to HTML for the book.
5. **Bundle**: The `marimo` template bundle includes the Makefile targets, requirements
   file, and a starter notebook.
6. **CI validation**: The `rhiza_marimo.yml` GitHub Actions workflow validates that all
   notebooks can be exported without errors.

## Consequences

### Positive

- **Clean version control**: Python-file format produces minimal, meaningful diffs.
  Notebook changes are easy to review in pull requests.
- **Reproducible**: Reactive execution eliminates the "works on my machine" problem
  caused by out-of-order cell execution.
- **Integrated with book**: Marimo HTML exports slot directly into the companion book
  build, giving each notebook a polished presentation page.
- **Modern UX**: Marimo's browser-based interface is fast, responsive, and supports
  Python type annotations and module reloading.
- **CI-friendly**: Notebooks can be validated in CI without a running kernel server.

### Neutral

- **Smaller ecosystem**: Marimo is newer than Jupyter and has a smaller ecosystem of
  extensions and integrations. Most scientific Python libraries work without
  modification, but some Jupyter-specific widgets are not compatible.
- **Learning curve**: Contributors familiar with Jupyter need to learn Marimo's
  reactivity model. The key difference—no hidden state—is generally an improvement but
  requires an adjustment in how notebooks are structured.

### Negative

- **Migration effort**: Existing Jupyter notebooks must be rewritten as Marimo
  notebooks; the formats are not automatically compatible.
- **Maturity**: Marimo's API is still evolving. Minor breaking changes between
  releases may require notebook updates. The `marimo>=0.18.0,<1.0` version constraint
  in `pyproject.toml` limits exposure to breaking changes.
