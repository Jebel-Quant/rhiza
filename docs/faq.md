# Frequently Asked Questions

Common questions about Rhiza and template-based development.

---

## General Questions

### What is Rhiza?

Rhiza is a **living template system** for Python projects. Unlike traditional project generators (cookiecutter, copier) that create a one-time snapshot, Rhiza maintains a continuous connection to template repositories, allowing you to synchronize updates over time.

**Key difference:**
- **Traditional generators:** Create files once, then you're on your own
- **Rhiza:** Ongoing synchronization with upstream best practices

---

### Who should use Rhiza?

Rhiza is ideal for:

- **Teams** maintaining multiple Python projects
- **Organizations** wanting standardized tooling across repos
- **Individual developers** who want battle-tested configurations
- **Open source maintainers** keeping projects up-to-date

**Not ideal for:**
- Projects with heavily customized build systems
- Non-Python projects (though the concept can be adapted)
- Teams that prefer full control without any template system

---

### What does "Rhiza" mean?

**Rhiza** (ῥίζα) is Ancient Greek for **"root"**, pronounced *ree-ZAH*.

The name reflects:
- Strong foundations for your projects
- Root-level configuration (build, CI, linting)
- Growing and evolving with your codebase

---

### Is Rhiza free?

Yes! Rhiza is **MIT licensed** and completely free to use, modify, and distribute.

The only costs are:
- **GitHub Actions minutes** (free tier usually sufficient)
- **GitHub Advanced Security** (optional, for CodeQL on private repos)

---

## Getting Started

### How do I start using Rhiza?

For new projects:

```bash
git clone https://github.com/jebel-quant/rhiza.git my-project
cd my-project
make install
```

For existing projects:

```bash
cd /path/to/your/project
uvx rhiza init
uvx rhiza materialize
```

See [Quick Start](getting-started/quickstart.md) for details.

---

### What Python versions does Rhiza support?

Rhiza requires **Python 3.11+** and tests against:

- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14

Older Python versions (3.8-3.10) are not supported.

---

### Do I need to install anything globally?

**No!** Rhiza is self-contained:

- `make install` auto-installs `uv` to `./bin/` if needed
- Python is downloaded by `uv` if not present
- All dependencies live in `.venv/`

**No global pollution.** Everything stays in your project directory.

---

### Can I use Rhiza without uv?

Technically yes, but **not recommended**. Rhiza is designed around `uv` for:

- **Speed** — 10-100x faster than pip
- **Reliability** — Reproducible installs via `uv.lock`
- **Simplicity** — Single tool for all Python needs

If you must use `pip`, you'll need to manually implement several features.

---

## Template Synchronization

### How often should I sync templates?

**Recommended schedule:**

- **Automatically:** Weekly via `.github/workflows/rhiza_sync.yml`
- **Manually:** When you see upstream improvements you want
- **Before releases:** Ensure latest security patches

You control the schedule in `.github/workflows/rhiza_sync.yml`:

```yaml
on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
```

---

### Will sync overwrite my customizations?

**No!** Rhiza respects your exclude patterns:

```yaml
# .rhiza/template.yml
exclude: |
  local.mk
  .rhiza/make.d/90-custom.mk
  src/
  tests/
```

Files matching `exclude` patterns are never touched during sync.

---

### What happens during a sync?

```mermaid
flowchart LR
    A[Scheduled Trigger] --> B[Fetch Upstream]
    B --> C[Filter by include/exclude]
    C --> D[Create PR with Changes]
    D --> E[You Review & Merge]
    
    style A fill:#2fa4a9
    style E fill:#4ade80
```

1. **Fetch** upstream templates from configured repository
2. **Filter** using your `include` and `exclude` patterns
3. **Create PR** with proposed changes
4. **You review** and decide what to merge

**You're always in control.**

---

### Can I use a different template repository?

**Absolutely!** Rhiza can sync from any repository:

```yaml
# .rhiza/template.yml
repository: your-org/your-template-repo
ref: main
```

**Common patterns:**

- Fork `jebel-quant/rhiza` for your organization
- Create a completely custom template
- Use different templates for different project types

---

### How do I stop syncing a specific file?

Add it to `exclude` in `.rhiza/template.yml`:

```yaml
exclude: |
  .github/workflows/custom.yml
  local.mk
  some-config.toml
```

Or remove it from `include`:

```yaml
include: |
  .github/workflows/rhiza_*.yml  # Excludes custom.yml
```

---

## Customization

### Can I add custom Make targets?

**Yes!** Create `.rhiza/make.d/50-custom.mk`:

```makefile
##@ Custom Tasks

.PHONY: deploy
deploy: ## Deploy to production
	./scripts/deploy.sh
```

This appears in `make help` and won't be overwritten by sync.

---

### How do I customize pre-commit hooks?

Edit `.pre-commit-config.yaml` and add to exclude list:

```yaml
# .rhiza/template.yml
exclude: |
  .pre-commit-config.yaml
```

Or extend the template:

```yaml
# .pre-commit-config.yaml
repos:
  # Rhiza's hooks
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
  
  # Your custom hooks
  - repo: local
    hooks:
      - id: custom-check
        entry: ./scripts/check.sh
```

---

### Can I use a different linter?

**You can**, but Rhiza is optimized for `ruff`. To use a different linter:

1. **Exclude Rhiza's ruff config:**
   ```yaml
   exclude: |
     ruff.toml
   ```

2. **Add your linter to pyproject.toml:**
   ```toml
   [tool.black]
   line-length = 88
   ```

3. **Update pre-commit hooks:**
   ```yaml
   - repo: https://github.com/psf/black
     hooks:
       - id: black
   ```

---

### How do I add custom CI workflows?

Create `.github/workflows/custom.yml` and exclude from sync:

```yaml
# .rhiza/template.yml
exclude: |
  .github/workflows/custom.yml
```

---

## CI/CD

### Do I have to use GitHub Actions?

**No.** Rhiza also supports GitLab CI (see `.gitlab/`).

For other CI systems:
1. Exclude `.github/workflows/`
2. Use Rhiza's `Makefile` targets in your CI config:

```yaml
# Example: CircleCI
jobs:
  test:
    steps:
      - checkout
      - run: make test
```

---

### How do I publish to PyPI?

Configure **Trusted Publishing** (no tokens needed):

1. Go to PyPI → Your Project → Publishing → Add new publisher
2. Fill in:
   - Owner: `{your-org}`
   - Repository: `{your-repo}`
   - Workflow: `rhiza_release.yml`
   - Environment: `release`

3. Create and push a version tag:
   ```bash
   make bump BUMP=patch
   make release
   ```

See [RELEASING.md](RELEASING.md) for details.

---

### Can I publish to a private PyPI?

**Yes!** Set secrets:

- `PYPI_REPOSITORY_URL` — Your private PyPI URL
- `PYPI_TOKEN` — Authentication token

The release workflow automatically detects and uses them.

---

### Why does CodeQL fail on my private repo?

**CodeQL requires GitHub Advanced Security**, which is:

- ✅ Free for public repositories
- 💰 Requires Enterprise license for private repos

**Solutions:**

1. Enable Advanced Security (if you have Enterprise)
2. Or disable CodeQL: Set variable `CODEQL_ENABLED=false`

---

## Dependencies

### How do I add a dependency?

```bash
uv add requests              # Runtime dependency
uv add --dev pytest-mock     # Development dependency
```

This updates `pyproject.toml` and `uv.lock` automatically.

---

### Why does `make install` fail with "uv.lock out of sync"?

**Cause:** You edited `pyproject.toml` but didn't update the lock file.

**Solution:**

```bash
uv lock       # Update lock file
make install  # Retry
```

Or use `uv add` which handles both steps.

---

### Can I use private packages?

**Yes!** Configure authentication:

**For GitHub Packages:**

```bash
# Set GH_PAT secret in repository settings
```

**For custom index:**

```yaml
# In repository secrets
UV_EXTRA_INDEX_URL: https://username:password@custom.pypi.org/simple
```

See [private-packages.md](private-packages.md) for details.

---

### How do I update all dependencies?

```bash
uv lock --upgrade  # Update all packages
make install       # Sync environment
```

To upgrade one package:

```bash
uv lock --upgrade-package requests
make install
```

---

## Testing

### How do I run tests?

```bash
make test          # All tests
make test-fast     # Skip slow tests
```

For specific tests:

```bash
uv run pytest tests/test_specific.py -v
uv run pytest tests/test_specific.py::test_function -v
```

---

### How do I check test coverage?

```bash
make test  # Generates coverage report

# View HTML report
open _tests/html-coverage/index.html
```

Coverage configuration is in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*"]

[tool.coverage.report]
fail_under = 80
```

---

### Can I use a different test framework?

**Rhiza is designed for pytest**, but you can adapt:

1. Exclude Rhiza's test config:
   ```yaml
   exclude: |
     pytest.ini
     pyproject.toml:[tool.pytest]
   ```

2. Update `Makefile` test target:
   ```makefile
   test:
       unittest discover tests/
   ```

---

## Troubleshooting

### `make` command not found

**macOS:**
```bash
xcode-select --install
```

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential
```

**Windows:**

Use WSL2 (Windows Subsystem for Linux). Native Windows is not supported.

---

### GitHub Actions workflow fails

**Common causes:**

1. **Secrets not configured**
   - Check repository Settings → Secrets
   - Ensure `GH_PAT` or `PAT_TOKEN` is set if needed

2. **Python version mismatch**
   - Update `pyproject.toml` classifiers
   - CI matrix auto-generates from classifiers

3. **Lock file out of sync**
   - Run `uv lock` and commit changes

---

### Sync workflow can't push changes

**Cause:** `PAT_TOKEN` not configured or lacks `workflow` scope.

**Solution:**

1. Create Personal Access Token with `workflow` scope
2. Add as repository secret named `PAT_TOKEN`
3. See [token-setup.md](token-setup.md)

---

### Pre-commit hooks fail

```bash
# Update hooks
uv run pre-commit autoupdate

# Run manually
uv run pre-commit run --all-files

# Skip hooks (emergency only)
git commit --no-verify
```

---

### Documentation build fails

```bash
# Check dependencies
make install

# Build locally
make book

# Check for errors in docs/
```

Common issues:
- Broken markdown links
- Missing image files
- Invalid YAML frontmatter

---

## Best Practices

### Should I commit .venv/?

**No!** The `.venv/` directory should never be committed.

It's already in `.gitignore`:

```gitignore
.venv/
venv/
```

Commit `uv.lock` instead for reproducible environments.

---

### Should I commit uv.lock?

**Yes!** Always commit `uv.lock`:

- Ensures reproducible builds
- Required for CI
- Tracks exact dependency versions

---

### How do I keep my fork in sync with Rhiza?

If you forked Rhiza to create your own template:

```bash
# Add upstream remote
git remote add upstream https://github.com/jebel-quant/rhiza.git

# Fetch upstream changes
git fetch upstream

# Merge or cherry-pick changes
git merge upstream/main
# or
git cherry-pick <commit-hash>
```

---

### What should I exclude from template sync?

**Always exclude:**
- `local.mk` — Your custom make targets
- `src/` — Your source code
- `tests/` — Your tests
- Custom workflows

**Example:**

```yaml
exclude: |
  local.mk
  src/
  tests/
  .rhiza/make.d/90-custom.mk
  .github/workflows/custom.yml
```

---

## Advanced Topics

### Can I use Rhiza with monorepos?

**Yes**, but with caveats:

- Each sub-project can have its own `.rhiza/` config
- Shared tooling goes in root `.rhiza/`
- Use workspace configuration in `pyproject.toml`

See [monorepo example](https://github.com/jebel-quant/rhiza/discussions) (TBD).

---

### How do I create my own template repository?

1. **Fork or clone Rhiza:**
   ```bash
   gh repo fork jebel-quant/rhiza your-org/your-template
   ```

2. **Customize for your needs:**
   - Update CI workflows
   - Adjust linting rules
   - Add company-specific tooling

3. **Point projects to your template:**
   ```yaml
   # .rhiza/template.yml
   repository: your-org/your-template
   ```

---

### Can I sync from multiple templates?

**Not directly**, but you can:

1. **Merge templates manually:**
   ```bash
   uvx rhiza materialize --from org1/template1
   uvx rhiza materialize --from org2/template2 --keep-existing
   ```

2. **Or create a composite template** combining both upstream sources

---

### How do I contribute to Rhiza?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## Platform-Specific

### Does Rhiza work on Windows?

**Windows requires WSL2** (Windows Subsystem for Linux).

Native Windows is **not supported** because:
- Rhiza uses POSIX shell scripts
- `make` on Windows is problematic
- Path handling differs significantly

**Recommended:** Use WSL2 with Ubuntu.

---

### Does Rhiza work on macOS?

**Yes!** macOS is fully supported.

Install prerequisites:

```bash
xcode-select --install  # For make and git
```

Then:

```bash
make install  # Everything else auto-installs
```

---

### Does Rhiza work in Docker?

**Yes!** Use the included dev container:

```bash
# VS Code
code .  # Opens in dev container

# Or Docker directly
docker build -f docker/Dockerfile .
```

See [DOCKER.md](DOCKER.md) for details.

---

## Comparison to Other Tools

### Rhiza vs. Cookiecutter

| Feature | Rhiza | Cookiecutter |
|---------|-------|--------------|
| Initial generation | ✅ | ✅ |
| Ongoing sync | ✅ | ❌ |
| Template updates | Automatic | Manual |
| Customization | Hooks & exclusions | Fork template |
| Language | Python-focused | Any language |

**Use Rhiza when:** You want ongoing synchronization  
**Use Cookiecutter when:** One-time project bootstrap

---

### Rhiza vs. Copier

| Feature | Rhiza | Copier |
|---------|-------|--------|
| Initial generation | ✅ | ✅ |
| Updates | Via sync PR | Manual update |
| Template format | Git repo | Git repo |
| Customization | Exclude patterns | Template variables |

**Rhiza advantage:** Automated CI workflow for syncing  
**Copier advantage:** Better for multi-language projects

---

### Rhiza vs. Poetry

**They're complementary!**

- **Poetry:** Dependency management and packaging
- **Rhiza:** Project structure, CI/CD, and tooling

Rhiza uses `uv` (faster than Poetry) but the concepts are similar.

---

## Getting Help

### Where can I find more documentation?

- [Quick Start](getting-started/quickstart.md)
- [Migration Guide](migration.md)
- [Workflows](WORKFLOWS.md)
- [Customization](CUSTOMIZATION.md)
- [CI/CD](ci-cd.md)

---

### How do I report a bug?

1. Check [existing issues](https://github.com/jebel-quant/rhiza/issues)
2. Create a new issue with:
   - Description of the problem
   - Steps to reproduce
   - Expected vs. actual behavior
   - Output of `make validate`
   - Python version, OS, uv version

---

### How do I request a feature?

Open a [GitHub Discussion](https://github.com/jebel-quant/rhiza/discussions) with:

- **Use case:** What are you trying to achieve?
- **Proposed solution:** How should it work?
- **Alternatives:** What have you tried?

---

### Where can I get support?

- **GitHub Issues:** Bug reports
- **GitHub Discussions:** Questions and ideas
- **Documentation:** Comprehensive guides (you're reading one!)

---

## Still Have Questions?

If your question isn't answered here:

1. **Search the docs:** Use the search box (top right)
2. **Check GitHub Discussions:** Someone may have asked
3. **Open a discussion:** We're happy to help!

**Found an error in this FAQ?** Please [open an issue](https://github.com/jebel-quant/rhiza/issues) or submit a PR.
