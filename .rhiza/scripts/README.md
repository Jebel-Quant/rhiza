# Scripts

This directory contains automation scripts used by Makefile targets.

---

## Available Scripts

### release.sh

**Purpose:** Create a git tag and push to remote to trigger the release workflow.

**Usage:**
```bash
# Via Makefile (recommended)
make release

# Direct invocation
./.rhiza/scripts/release.sh

# Show help
./.rhiza/scripts/release.sh --help
```

**What it does:**

1. **Validates environment**
   - Checks `pyproject.toml` exists
   - Verifies `uv` is available

2. **Pre-flight checks**
   - Warns if not on default branch
   - Verifies no uncommitted changes
   - Ensures branch is up-to-date with remote
   - Checks if tag already exists (local and remote)

3. **Creates tag**
   - Reads version from `pyproject.toml` via `uv version --short`
   - Creates tag in format `v{version}` (e.g., `v0.6.0`)
   - Uses GPG signing if configured, otherwise annotated tag

4. **Pushes tag**
   - Shows commits since last tag
   - Pushes tag to origin
   - Displays link to GitHub Actions

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Success or user abort |
| 1 | Error (missing file, uncommitted changes, etc.) |

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `UV_BIN` | `./bin/uv` | Path to uv binary |

**Safety features:**

- Prompts for confirmation at each step
- Refuses to run with uncommitted changes
- Warns when not on default branch
- Detects diverged branches
- Prevents duplicate tag creation

---

## Script Conventions

All scripts in this directory follow these conventions:

### Shell Compatibility

- POSIX `/bin/sh` compatible (no bash-specific features)
- `set -e` for fail-on-error behavior
- Works on Linux, macOS, and WSL

### Color Output

Scripts use ANSI color codes for clarity:

| Color | Meaning |
|-------|---------|
| 🔵 Blue | Informational messages |
| 🟢 Green | Success messages |
| 🟡 Yellow | Warnings and prompts |
| 🔴 Red | Error messages |

### User Interaction

- Interactive prompts use `[y/N]` format (default No)
- All destructive actions require confirmation
- `Ctrl+C` safely aborts at any point

### Error Handling

- Clear error messages with `[ERROR]` prefix
- Helpful suggestions for resolution
- Non-zero exit codes on failure

---

## Adding New Scripts

To add a new script:

1. **Create the script** in this directory:
   ```bash
   touch .rhiza/scripts/my-script.sh
   chmod +x .rhiza/scripts/my-script.sh
   ```

2. **Follow the template:**
   ```sh
   #!/bin/sh
   # Description of what this script does
   # - Key feature 1
   # - Key feature 2

   set -e

   # Colors
   BLUE="\033[36m"
   RED="\033[31m"
   GREEN="\033[32m"
   YELLOW="\033[33m"
   RESET="\033[0m"

   # Help function
   show_usage() {
     printf "Usage: %s [OPTIONS]\n" "$0"
     # ... options ...
   }

   # Parse arguments
   while [ $# -gt 0 ]; do
     case "$1" in
       -h|--help) show_usage; exit 0 ;;
       *) printf "%b[ERROR] Unknown: %s%b\n" "$RED" "$1" "$RESET"; exit 1 ;;
     esac
   done

   # Main logic
   main() {
     printf "%b[INFO] Starting...%b\n" "$BLUE" "$RESET"
     # ... implementation ...
     printf "%b[SUCCESS] Done!%b\n" "$GREEN" "$RESET"
   }

   main
   ```

3. **Add Makefile target** in `.rhiza/make.d/`:
   ```makefile
   # .rhiza/make.d/50-custom.mk
   my-task: ## Description of my task
   	@/bin/sh ".rhiza/scripts/my-script.sh"
   ```

4. **Document here** by adding a section to this README.

---

## Customization Directory

For project-specific scripts that shouldn't be synced from the template, create:

```
.rhiza/scripts/customisations/
```

This directory is typically excluded in `template.yml`:

```yaml
exclude: |
  .rhiza/scripts/customisations/*
```

---

## Related Documentation

- [docs/architecture.md](../../docs/architecture.md) - Release pipeline flow
- [docs/glossary.md](../../docs/glossary.md) - Term definitions
- [docs/RELEASING.md](../../docs/RELEASING.md) - Release process guide
- [.rhiza/make.d/README.md](../make.d/README.md) - Makefile extension guide
