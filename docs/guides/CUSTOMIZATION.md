# Customization Guide

This guide covers how to extend and adapt Rhiza-based projects without breaking template sync.

## Safe Extension Points

Rhiza provides four extension mechanisms that survive every `/rhiza:update`. **Never edit template-managed files** — `.rhiza/`, the workflow stubs, and (since the make layer retired) the `Makefile` itself are overwritten on the next sync. `check-managed-files` refuses a commit that touches one, so this is enforced rather than merely advised.

| Extension point | Where to add | Committed? | Use for |
|-----------------|--------------|------------|---------|
| `local.mk` | Project root | Yes | Your own make targets, and extending a template task |
| `local-setup.sh` | Project root | Yes | Native binaries the project needs before any gate runs |
| `[tool.rhiza-task]` | `pyproject.toml` | Yes | Settings — `source-folder`, `coverage-fail-under`, … |
| `pyproject.toml` | Project root | Yes | Dependencies, scripts, tool configuration |
| `.rhiza/.env` | Project root | No (gitignored) | Per-developer setting overrides |

### `local.mk` — the project's own targets

The `Makefile` is template-owned and `-include`s `local.mk`, which no sync touches. It is deliberately **not** gitignored: commit it, because anything CI invokes has to be in the repository.

```makefile
# local.mk — committed
train-model: ## Train the ML model
	@uv run python scripts/train.py
```

Targets carrying a `##` comment are listed by `make help` under *Repo-owned targets*, so they stay discoverable next to the template's tasks.

## 🛠️ Extending a Template Task

The `pre-install::` / `post-install::` hooks the synced make layer anchored are **gone**: the tasks live in the pinned `rhiza-task` CLI, which knows nothing about make targets. The replacement is to **shadow** the target from `local.mk` — an explicit rule always beats the shim's `%:` catch-all, so the rule can call the task and then do the extra work.

```makefile
# local.mk
report: $(UVX)
	@$(UVX) $(RHIZA_TASK) test
	@./scripts/publish-test-report.sh
```

`RHIZA_TASK` and `UVX` are defined by the `Makefile` above the `-include`, so a shadowing rule runs the same pinned CLI the rest of the project does — and naming `$(UVX)` as a prerequisite keeps the bootstrap that installs `uv` on a runner without one.

**Shadowing only reaches a task that make resolves.** An explicit rule wins when you type its name, or when another make rule names it as a prerequisite. It does not win when the CLI reaches the task internally: `test` needs `install`, but the shim forwards the goal `test` to `rhiza-task`, which resolves `install` in its own task graph — no make rule of that name is consulted. And CI never invokes make at all; every workflow calls `uvx "$RHIZA_TASK" <gate>` directly.

So shadowing adds work around a task **you invoke**. Work that has to happen before every gate belongs in the setup hook.

## 🧰 Installing System Dependencies

A project may need a native binary before any gate can run — graphviz for a docs plugin, `libpq` for psycopg, pandoc, an ODBC driver. Put it in an executable `local-setup.sh` at the repository root:

```bash
#!/usr/bin/env bash
set -euo pipefail

if ! command -v dot >/dev/null 2>&1; then
    echo "Installing graphviz..."
    sudo apt-get update && sudo apt-get install -y graphviz
fi
```

```bash
chmod +x local-setup.sh
```

Every language layer's `install` runs it first, and `install` is the prerequisite of essentially every gate — so this one file covers a local `make test`, GitHub Actions, GitLab CI and the devcontainer, with no workflow edit anywhere. Commit it: `core` leaves it un-ignored for the same reason it leaves `local.mk` un-ignored — anything CI invokes has to be in the repository.

Three things worth knowing:

- **Guard the expensive part yourself**, as above. The hook runs on every fresh CI job and on every local invocation of a gate.
- **A non-executable hook fails**, with a `chmod +x` hint — a provisioning step someone wrote and believed was running is exactly what must not pass quietly. Having no hook at all simply succeeds, so a project that needs nothing pays nothing, `--strict` runs included.
- **It is a shell script rather than a list of package names**, because a list cannot survive contact with more than one package manager — `graphviz` is spelled the same on apt and brew, `libgl1-mesa-glx` is not — and cannot express "download this tarball" at all. The script puts platform detection with the people who know which platforms they build on.

> Releasing is not a `make` target at all. Releases are driven by the rhiza-claude
> `/rhiza:release` command, which bumps the version, regenerates `CHANGELOG.md`, and
> creates the tag locally; pushing the tag triggers the release workflow.

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

Settings belong to the task runner, not to the `Makefile` — which is template-owned, so an assignment there would not survive a sync. `rhiza-task` resolves each one through five layers, later winning over earlier: its defaults, `.rhiza/.env`, `pyproject.toml`, the environment, then CLI flags.

### Project-wide configuration

A `[tool.rhiza-task]` table in `pyproject.toml`, typed by TOML rather than parsed out of strings:

```toml
[tool.rhiza-task]
source-folder = "src/my_package"
coverage-fail-under = 80
```

`uvx rhiza-task print coverage-fail-under` shows what a setting currently resolves to, which is the quickest way to tell whether an override is being read at all. A project with no Python manifest uses `.rhiza/.env`, or exports `RHIZA_*` from `local.mk` for anything that must be committed.

### Per-developer configuration

`.rhiza/.env` is gitignored and read as layer 2, so it is the place for values that should not travel with the repository.

### On-Demand Configuration

Environment variables outrank both files, so a one-off looks like:

```bash
RHIZA_COVERAGE_FAIL_UNDER=80 make test
```

## 🎨 Documentation Customization

You can customize the API documentation and companion book.

### Project Logo

The API documentation can show a logo in the sidebar. Set it in `mkdocs.yml`:

```yaml
theme:
  logo: assets/my-custom-logo.png
```

### Custom Templates

You can customise the look and feel of the documentation site by overriding MkDocs Material theme settings in `mkdocs.yml` (or `mkdocs-base.yml` if you use the split config approach). See the [MkDocs Material documentation](https://squidfunk.github.io/mkdocs-material/customization/) for available options.

For more details on customizing the documentation, see [docs/BOOK.md](BOOK.md).

## 📖 Complete Documentation

For detailed information about extending the task layer — adding targets, shadowing a task, and where settings live — see [Makefile Customisation](../../README.md#makefile-customisation).

For a tutorial walkthrough of these extension points — including the rule about template-managed files, the exclude mechanism, and forking the template for your organisation — see [rhiza-education Lesson 10: Customising Safely](https://github.com/Jebel-Quant/rhiza-education/blob/main/lessons/10-customizing-safely.md).
