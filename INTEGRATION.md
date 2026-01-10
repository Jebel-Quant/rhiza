# 🧩 Bringing Rhiza into an Existing Project

Rhiza provides reusable configuration templates that you can integrate into your existing Python projects.
You can choose to adopt all templates or selectively pick the ones that fit your needs.

## Prerequisites

Before integrating Rhiza into your existing project:

- **Python 3.11+** - Ensure your project supports Python 3.11 or newer
- **Git** - Your project should be a Git repository
- **Backup** - Consider committing any uncommitted changes before integration
- **Review** - Review the [Available Templates](README.md#-available-templates) section to understand what could be added

## Quick Start: Automated Injection

The fastest way to integrate Rhiza is by following the steps below:

```bash
# Navigate to your repository
cd /path/to/your/project

# Initialize configuration templates
uvx rhiza init
```

This will:
- ✅ Create a default template configuration (`.github/template.yml`)

Then, update the generated `.github/template.yml` file with your chosen templates that you can find from [Available Templates](README.md#-available-templates).

You will then need to run the following, to inject templates into your repository:

```bash
# Inject templates into your repository
uvx rhiza materialize
```

**Options:**
- `--branch <branch>` - Use a specific rhiza branch (default: main)
- `--help` - Show detailed usage information

**Example with branch option:**
```bash
# Use a development branch
uvx rhiza materialize --branch develop
```

## Method 1: Manual Integration (Selective Adoption)

This approach is ideal if you want to cherry-pick specific templates or customize them before integration.

### Step 1: Clone Rhiza

First, clone the Rhiza repository to a temporary location:

```bash
# Clone to a temporary directory
cd /tmp
git clone https://github.com/jebel-quant/rhiza.git
```

### Step 2: Copy Desired Templates

Navigate to your project and copy the configuration files you need:

```bash
# Navigate to your project
cd /path/to/your/project

# We recommend working on a fresh branch
git checkout -b rhiza

# Ensure required directories exist
mkdir -p .github/workflows
mkdir -p .rhiza/scripts

# Copy the template configuration
cp /tmp/rhiza/.github/template.yml .github/template.yml

# Copy the sync helper script
cp /tmp/rhiza/.rhiza/scripts/sync.sh .rhiza/scripts
```

At this stage:

  - ❌ No templates are copied yet
  - ❌ No existing files are modified
  - ✅ Only the sync mechanism is installed
  - ⚠️ **Do not merge this branch yet.**

### Step 3: Perform the first sync

Run the sync script to apply the templates defined in '.github/template.yml'

```bash
./.rhiza/scripts/sync.sh
```

This will:

  - Fetch the selected templates from the Rhiza repository
  - Apply them locally according to your include/exclude rules
  - Stage or commit the resulting changes on the current branch

Review the changes carefully:

```bash
git status
git diff
```

If happy with the suggested changes push them

```bash
git add .
git commit -m "Integrate Rhiza templates"
git push -u origin rhiza
```

## Method 2: Automated Sync (Continuous Updates)

This approach keeps your project's configuration in sync with Rhiza's latest templates while giving you control over which files are applied.

Prerequisites:

  - A .github/template.yml file exists, defining **which templates to include or exclude**.
  - The first manual sync (./.rhiza/scripts/sync.sh) has been performed.
  - The .github/workflows/sync.yml workflow is present in your repository.

The workflow can run:

  **On a schedule** — e.g., weekly updates
  **Manually** — via the GitHub Actions "Run workflow" button

⚠️ .github/template.yml remains the **source of truth**. All automated updates are driven by its include/exclude rules.

### Step 1: Configure GitHub Token

If you want the sync workflow to trigger other workflows (e.g. to create pull requests), create a Personal Access Token (PAT):

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with `repo` and `workflow` scopes
3. Add it as a repository secret named `PAT_TOKEN`
4. Update the workflow to use `token: ${{ secrets.PAT_TOKEN }}`

### Step 2: Run Initial Sync (again)

You can trigger the sync workflow manually:

1. Go to your repository's "Actions" tab
2. Select the "Sync Templates" workflow
3. Click "Run workflow"
4. Review and merge the resulting pull request

The workflow will:
- Download the latest templates from Rhiza
- Copy them to your project based on your `template.yml` configuration
- Create a pull request with the changes (if any)
- Automatically run weekly to keep your templates up to date

## What to Expect After Integration

After integrating Rhiza, your project will have:

- **Automated CI/CD** - GitHub Actions workflows for testing, linting, and releases
- **Code Quality Tools** - Pre-commit hooks, ruff formatting, and pytest configuration
- **Task Automation** - Makefile with common development tasks (`make test`, `make fmt`, etc.)
- **Dev Container** - Optional VS Code/Codespaces development environment
- **Documentation** - Templates for automated documentation generation

## Next Steps

1. **Test the integration** - Run `make test` to ensure tests pass
2. **Run pre-commit** - Execute `make fmt` to verify code quality checks
3. **Review workflows** - Check GitHub Actions tabs to see workflows in action
4. **Customize** - Adjust templates to match your project's specific needs
5. **Update documentation** - Add project-specific instructions to your README

## Troubleshooting

**Issue: Makefile targets conflict with existing scripts**
- Solution: Review the Makefile and merge targets with your existing build scripts, or rename conflicting targets

**Issue: Pre-commit hooks fail on existing code**
- Solution: Run `make fmt` to fix formatting issues, or temporarily exclude certain files in `.pre-commit-config.yaml`

**Issue: GitHub Actions workflows fail**
- Solution: Check Python version compatibility and adjust `PYTHON_MAX_VERSION` repository variable if needed

**Issue: Dev container fails to build**
- Solution: Review `.devcontainer/devcontainer.json` and ensure all dependencies are available for your project
