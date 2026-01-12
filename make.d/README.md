# Makefile Extensions (`make.d/`)

This directory contains repository-specific Makefile modules. Files in this directory are automatically included by the root `Makefile` in lexicographical order.

## How to use

1.  Create a file with a `.mk` extension (e.g., `make.d/50-data-science.mk`).
2.  Use double digits at the start of the filename to control the order of inclusion if needed.
3.  Add your custom targets and variables.

## Comparison: `make.d/` vs `local.mk`

| Feature | `make.d/*.mk` | `local.mk` |
| :--- | :--- | :--- |
| **Persistence** | Committed to the repository | Local to your machine (git-ignored) |
| **Purpose** | Project-specific shared tasks | Personal developer preferences/secrets |
| **Inclusion** | Included after core API | Included after `make.d/*.mk` |

## Example: Adding a hook

You can use core Rhiza hooks to inject logic into standard workflows:

```makefile
pre-sync::
	@echo "Checking for uncommitted changes before sync..."
```
