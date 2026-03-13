# `.rhiza/template.yml` Example with `pyproject:` Section

This document shows a fully-annotated example of a downstream project's
`.rhiza/template.yml` using the optional `pyproject:` section introduced by
the `sync-pyproject` feature.

---

## Full Example

```yaml
# .rhiza/template.yml
# ---------------------------------------------------------------
# Which rhiza release to sync against
repository: Jebel-Quant/rhiza
ref: v0.9.0

# Which template bundles to enable
templates:
  - core
  - tests
  - github

# ---------------------------------------------------------------
# Fields rhiza controls in pyproject.toml (all optional)
#
# Only the keys declared here are touched during `make sync-pyproject`.
# Everything else in pyproject.toml (name, version, description, authors,
# keywords, dependencies, [dependency-groups], [project.urls]) is
# preserved unchanged.
# ---------------------------------------------------------------
pyproject:

  # Set [project].requires-python
  requires-python: ">=3.11"

  # Replace [project].classifiers entirely.
  # Rhiza owns this list — it mirrors the requires-python / .python-version
  # support matrix.
  classifiers:
    - "Programming Language :: Python :: 3"
    - "Programming Language :: Python :: 3 :: Only"
    - "Programming Language :: Python :: 3.11"
    - "Programming Language :: Python :: 3.12"
    - "Programming Language :: Python :: 3.13"
    - "Programming Language :: Python :: 3.14"
    - "License :: OSI Approved :: MIT License"
    - "Intended Audience :: Developers"

  # Sync entire [tool.*] subsections from rhiza's own pyproject.toml.
  # Use dotted TOML paths — the entire subtree at that path is replaced.
  tool-sections:
    - tool.deptry.package_module_name_map
```

---

## Supported `pyproject:` Keys

| Key | TOML path patched | Behaviour |
|-----|-------------------|-----------|
| `requires-python` | `[project].requires-python` | Sets the value; no-op if already matching |
| `classifiers` | `[project].classifiers` | Replaces the list entirely |
| `tool-sections` | `[tool.<...>]` (dotted path) | Syncs the subtree from rhiza's own `pyproject.toml` |

---

## Running the Sync

```bash
# Apply changes
make sync-pyproject

# Preview without writing
make sync-pyproject DRY_RUN=1

# CI check — exits non-zero if changes are needed
make sync-pyproject CHECK=1
```

Or call the script directly:

```bash
uv run python .rhiza/utils/sync_pyproject.py
uv run python .rhiza/utils/sync_pyproject.py --dry-run
uv run python .rhiza/utils/sync_pyproject.py --check
```

---

## What is Never Touched

The following fields are **never modified** by `sync-pyproject` unless you
add them to a supported key above:

- `name`
- `version`
- `description`
- `authors`
- `keywords`
- `dependencies`
- `[dependency-groups]`
- `[project.urls]`
- Any `[tool.*]` section not listed under `tool-sections`
