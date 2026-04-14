# GitLab CI/CD Workflows for Rhiza

This directory contains GitLab CI/CD workflow configurations that mirror the functionality of the GitHub Actions workflows in `.github/workflows/`.

## Structure

```
.gitlab/
├── workflows/
│   ├── rhiza_ci.yml           # Continuous Integration - Python matrix testing
│   ├── rhiza_quality.yml      # Quality checks (deptry, pre-commit, docs coverage, link check)
│   ├── rhiza_semgrep.yml      # Semgrep static analysis with local numpy rules
│   ├── rhiza_marimo.yml       # Marimo notebook execution and artefact publishing
│   ├── rhiza_book.yml         # Documentation building (GitLab Pages)
│   ├── rhiza_sync.yml         # Template synchronization
│   └── rhiza_release.yml      # Release workflow
├── template/                  # GitLab CI job templates
│   └── marimo_job_template.yml.jinja
└── README.md                  # This file

.gitlab-ci.yml                 # Main GitLab CI configuration (includes all workflows)
```

## Workflows

### 1. CI (`rhiza_ci.yml`)
**Purpose:** Run tests on multiple Python versions to ensure compatibility.

**Trigger:**
- On push to any branch
- On merge requests to main/master

**Key Features:**
- Dynamic Python version matrix generation
- Tests on Python 3.11, 3.12, 3.13
- Git LFS support
- UV package manager for dependency management

**Equivalent GitHub Action:** `.github/workflows/rhiza_ci.yml`

---

### 2. Validate (`rhiza_validate.yml`)
**Purpose:** Validate Rhiza configuration against template, run security scans and type checking.

**Trigger:**
- On push to any branch
- On merge requests to main/master
- `pip-audit` job only runs on scheduled pipelines

**Key Features:**
- Runs `make validate`, which fires the full hook chain (`pre-validate`, `rhiza-test`, `uvx rhiza validate .`, `post-validate`)
- Skips validation in the rhiza repository itself (handled internally by `make validate`)
- Runs `make security` (pip-audit + bandit) on push/MR
- Runs `uvx pip-audit` on scheduled pipelines for dependency vulnerability scanning
- Runs `make typecheck` (ty type checker) on push/MR

**Equivalent GitHub Action:** `.github/workflows/rhiza_validate.yml`

---

### 3. Quality (`rhiza_quality.yml`)
**Purpose:** Run quality checks including dependency validation, pre-commit hooks, documentation coverage, and link checking.

**Trigger:**
- On push to any branch
- On merge requests to main/master

**Key Features:**
- Dependency checking with deptry (`make deptry`)
- Pre-commit hooks for code formatting and linting (`make fmt`)
- Documentation coverage validation (`make docs-coverage`)
- Link checking on README.md with lychee

**Equivalent GitHub Action:** `.github/workflows/rhiza_quality.yml`

---

### 4. Semgrep (`rhiza_semgrep.yml`)
**Purpose:** Run static analysis using Semgrep with local rules to detect common bugs and security issues.

**Trigger:**
- On push to any branch
- On merge requests to main/master

**Key Features:**
- Runs `make semgrep` using `.rhiza/semgrep.yml` local rules
- Skips if `SOURCE_FOLDER` is not found

**Equivalent GitHub Action:** `.github/workflows/rhiza_semgrep.yml`

---

### 5. License (`rhiza_license.yml`)
**Purpose:** Check that no copyleft-licensed dependencies (GPL, LGPL, AGPL) have been introduced via transitive updates.

**Trigger:**
- On push to any branch
- On merge requests to main/master

**Key Features:**
- Runs `make license` to fail on forbidden licenses
- Generates `LICENSES.md` markdown report of all dependency licenses
- Publishes `LICENSES.md` as a GitLab CI artifact (retained 30 days)

**Equivalent GitHub Action:** `.github/workflows/rhiza_validate.yml` (license job)

---

### 6. Marimo (`rhiza_marimo.yml`)
**Purpose:** Discover and execute all Marimo notebooks in the repository, publishing results as artefacts.

**Trigger:**
- On push to main/master branch
- On merge requests to main/master

**Key Features:**
- Discovers notebooks dynamically from `MARIMO_FOLDER` (default: `marimo`)
- Runs each notebook sequentially with `uvx uv run`
- `fail-fast: false` equivalent — all notebooks are attempted even if one fails
- Publishes `results/` as GitLab CI artefacts (retained for 1 week)
- Git LFS support

**Equivalent GitHub Action:** `.github/workflows/rhiza_marimo.yml`

---

### 7. Book (`rhiza_book.yml`)
**Purpose:** Build and deploy documentation to GitLab Pages.

**Trigger:**
- On push to main/master branch

**Key Features:**
- Combines API docs, test coverage, and notebooks
- Deploys to GitLab Pages
- Controlled by `PUBLISH_COMPANION_BOOK` variable

**Equivalent GitHub Action:** `.github/workflows/rhiza_book.yml`

**GitLab-specific:** Outputs to `public/` directory for GitLab Pages.

---

### 8. Sync (`rhiza_sync.yml`)
**Purpose:** Synchronize repository with its template.

**Trigger:**
- Scheduled (can be set in GitLab)
- Manual trigger
- Web pipeline trigger

**Key Features:**
- Template materialization with rhiza
- Automatic branch creation
- Manual merge request creation

**Equivalent GitHub Action:** `.github/workflows/rhiza_sync.yml`

**GitLab-specific:** Requires Project/Group Access Token (PAT_TOKEN) for workflow modifications.

---

### 9. Release (`rhiza_release.yml`)
**Purpose:** Create releases and publish packages to PyPI.

**Trigger:**
- On version tags (e.g., `v1.2.3`)

**Key Features:**
- Version validation
- Python package building with Hatch
- PyPI publishing with twine
- GitLab release creation

**Equivalent GitHub Action:** `.github/workflows/rhiza_release.yml`

**GitLab-specific:**
- Uses GitLab Releases API instead of GitHub Releases
- Uses PYPI_TOKEN instead of OIDC Trusted Publishing

---

## Key Differences from GitHub Actions

For a detailed side-by-side syntax comparison and per-feature breakdown, see [COMPARISON.md](COMPARISON.md).

---

## Configuration Variables

These variables can be set in GitLab CI/CD settings (Settings > CI/CD > Variables):

| Variable | Default | Description |
|----------|---------|-------------|
| `UV_EXTRA_INDEX_URL` | `""` | Extra index URL for UV package manager |
| `PYPI_REPOSITORY_URL` | `""` | Custom PyPI repository URL (empty = pypi.org) |
| `PYPI_TOKEN` | N/A | **Secret** - PyPI authentication token |
| `PUBLISH_COMPANION_BOOK` | `true` | Whether to publish documentation |
| `CREATE_MR` | `true` | Whether to create merge request on sync |
| `PAT_TOKEN` | N/A | **Secret** - Project/Group Access Token for sync |

### Setting Variables

1. Navigate to your GitLab project
2. Go to **Settings > CI/CD > Variables**
3. Click **Add variable**
4. Enter the variable name and value
5. Mark as **Protected** for production variables
6. Mark as **Masked** for sensitive values

---

## Testing GitLab CI Locally

You can validate the GitLab CI configuration syntax using:

```bash
# Install GitLab CI Lint tool
curl --header "PRIVATE-TOKEN: <your_access_token>" \
  "https://gitlab.com/api/v4/projects/<project_id>/ci/lint" \
  --data-urlencode "content@.gitlab-ci.yml"
```

Or use the GitLab UI:
1. Go to **CI/CD > Pipelines**
2. Click **CI Lint** button (or go to `/ci/lint`)
3. Paste your `.gitlab-ci.yml` content
4. Click **Validate**

---

## Migration Checklist

When migrating from GitHub Actions to GitLab CI:

- [ ] Set required CI/CD variables (especially secrets like `PYPI_TOKEN`)
- [ ] Configure Project/Group Access Token for `PAT_TOKEN` (if using sync)
- [ ] Enable GitLab Pages in project settings (if using book)
- [ ] Configure scheduled pipelines for sync workflow
- [ ] Update any repository-specific configurations
- [ ] Test each workflow individually
- [ ] Verify release workflow with a test tag
- [ ] Update documentation links

---

## Troubleshooting

### Common Issues

1. **Pipeline fails with "permission denied"**
   - Check if required variables are set
   - Verify token permissions

2. **Pages deployment doesn't work**
   - Ensure job is named `pages`
   - Verify artifacts are in `public/` directory
   - Check if GitLab Pages is enabled

3. **Matrix jobs don't run in parallel**
   - GitLab CI has limitations on dynamic matrices
   - Consider using child pipelines for true parallelism

4. **Release workflow fails**
   - Verify `PYPI_TOKEN` is set
   - Check tag format (must start with `v`)
   - Ensure version in pyproject.toml matches tag

---

## Support

For issues specific to:
- **GitLab CI syntax:** Refer to [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- **Rhiza workflows:** See main repository README
- **Workflow behavior:** Compare with corresponding GitHub Actions workflows

---

## Contributing

When adding or modifying workflows:

1. Update both `.gitlab/workflows/*.yml` and `.github/workflows/*.yml`
2. Keep feature parity between GitHub Actions and GitLab CI
3. Document any platform-specific differences
4. Test changes in a fork before merging
5. Update this README with new workflows or variables

---

## License

These workflows are part of the jebel-quant/rhiza repository and follow the same license.
