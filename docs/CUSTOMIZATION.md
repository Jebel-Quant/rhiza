# Customization Guide

This guide covers advanced customization options for Rhiza-based projects.

## 🛠️ Makefile Hooks & Extensions

Rhiza uses a modular Makefile system with extension points (hooks) that let you customize workflows without modifying core files.

**Important**: All customizations should be made in your root `Makefile`, not in `.rhiza/`. The `.rhiza/` directory is template-managed and will be overwritten during sync operations.

### Available Hooks

You can hook into standard workflows using double-colon syntax (`::`) in your root `Makefile`:

- `pre-install / post-install` - Runs around `make install`
- `pre-sync / post-sync` - Runs around repository synchronization
- `pre-validate / post-validate` - Runs around validation checks
- `pre-release / post-release` - Runs around release process
- `pre-bump / post-bump` - Runs around version bumping

### Example: Installing System Dependencies

Add to your root `Makefile` (before the `include .rhiza/rhiza.mk` line):

```makefile
pre-install::
	@if ! command -v dot >/dev/null 2>&1; then \
		echo "Installing graphviz..."; \
		sudo apt-get update && sudo apt-get install -y graphviz; \
	fi
```

This hook runs automatically before `make install`, ensuring graphviz is available.

### Example: Post-Release Tasks

Add to your root `Makefile`:

```makefile
post-release::
	@echo "Running post-release tasks..."
	@./scripts/notify-team.sh
	@./scripts/update-changelog.sh
```

This runs automatically after `make release` completes.

### Example: Custom Build Steps

Add to your root `Makefile`:

```makefile
post-install::
	@echo "Installing specialized dependencies..."
	@uv pip install some-private-lib
	
##@ Custom Tasks
train-model: ## Train the ML model
	@uv run python scripts/train.py
```

## 🔒 CodeQL Configuration

The CodeQL workflow (`.github/workflows/rhiza_codeql.yml`) performs security analysis on your code. However, **CodeQL requires GitHub Advanced Security**, which is:

- ✅ **Available for free** on public repositories
- ⚠️ **Requires GitHub Enterprise license** for private repositories

### Automatic Behavior

By default, the CodeQL workflow:
- **Runs automatically** on public repositories
- **Skips automatically** on private repositories (unless you have Advanced Security)

### Controlling CodeQL

You can override the default behavior using a repository variable:

1. Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
2. Create a new repository variable named `CODEQL_ENABLED`
3. Set the value:
   - `true` - Force CodeQL to run (use if you have Advanced Security on a private repo)
   - `false` - Disable CodeQL entirely (e.g., if it's causing issues)

### For Private Repositories with Advanced Security

If you have a GitHub Enterprise license with Advanced Security enabled:

```bash
# Enable CodeQL for your private repository
gh variable set CODEQL_ENABLED --body "true"
```

### For Users Without Advanced Security

No action needed! The workflow will automatically skip for private repositories. If you want to completely disable it:

```bash
# Disable CodeQL workflow
gh variable set CODEQL_ENABLED --body "false"
```

Or delete the workflow file:

```bash
# Remove CodeQL workflow
git rm .github/workflows/rhiza_codeql.yml
git commit -m "Remove CodeQL workflow"
```

## ⚙️ Configuration Variables

You can configure certain aspects of the Makefile by overriding variables. These can be set in your main `Makefile` (before the `include` line), a `local.mk` file (for local developer overrides), or passed as environment variables / command-line arguments.

### Global Configuration

Add these to your root `Makefile` (before `include .rhiza/rhiza.mk`) or `local.mk`:

```makefile
# Override default Python version
PYTHON_VERSION = 3.12

# Override test coverage threshold (default: 90)
COVERAGE_FAIL_UNDER = 80

# Override the sync schedule (default: weekly on Monday at midnight UTC)
# Uses cron syntax: minute hour day-of-month month day-of-week
RHIZA_SYNC_SCHEDULE = 0 9 * * 1-5  # Weekdays at 9 AM UTC

# Include the Rhiza API (template-managed)
include .rhiza/rhiza.mk
```

### Sync Schedule Override

The `RHIZA_SYNC_SCHEDULE` variable controls the cron schedule for the GitHub Actions sync workflow (`.github/workflows/rhiza_sync.yml`). Since this file is template-managed and overwritten during sync, the schedule is automatically patched after each `make sync` to preserve your custom value.

**Default:** `0 0 * * 1` (weekly on Monday at midnight UTC)

**Examples:**

```makefile
# Daily at 6 AM UTC
RHIZA_SYNC_SCHEDULE = 0 6 * * *

# Weekdays at 9 AM UTC
RHIZA_SYNC_SCHEDULE = 0 9 * * 1-5

# First day of each month at midnight UTC
RHIZA_SYNC_SCHEDULE = 0 0 1 * *

# Every 6 hours
RHIZA_SYNC_SCHEDULE = 0 */6 * * *
```

Set this in your root `Makefile` (before the `include` line) and it will be applied automatically every time `make sync` runs. The override is also visible in the sync output:

```
[INFO] Applied custom sync schedule: 0 9 * * 1-5
```

> **Note:** For GitLab CI, the sync schedule is configured via the GitLab UI (Settings → CI/CD → Pipeline schedules), so this variable only affects GitHub Actions.

### On-Demand Configuration

You can also pass variables directly to `make` for one-off commands:

```bash
# Run tests requiring only 80% coverage
make test COVERAGE_FAIL_UNDER=80
```

## 🎨 Documentation Customization

You can customize the API documentation and companion book.

### Project Logo

The API documentation includes a logo in the sidebar. You can override the default logo (`assets/rhiza-logo.svg`) by setting the `LOGO_FILE` variable in your Makefile or `local.mk`:

```makefile
LOGO_FILE := assets/my-custom-logo.png
```

### Custom Templates

You can customize the look and feel of the API documentation by providing your own Jinja2 templates.
Place your custom templates in the `book/pdoc-templates` directory.

For example, to override the main module template, create `book/pdoc-templates/module.html.jinja2`.

See the [pdoc documentation on templates](https://pdoc.dev/docs/pdoc.html#edit-pdocs-html-template) for full details on how to override specific parts of the documentation.

For more details on customizing the documentation, see [docs/BOOK.md](BOOK.md).

## 📖 Complete Documentation

For detailed information about extending and customizing the Makefile system, see [.rhiza/make.d/README.md](../.rhiza/make.d/README.md).

For a tutorial walkthrough of these extension points — including the rule about template-managed files, the exclude mechanism, and forking the template for your organisation — see [rhiza-education Lesson 10: Customising Safely](https://github.com/Jebel-Quant/rhiza-education/blob/main/lessons/10-customizing-safely.md).
