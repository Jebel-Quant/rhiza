# GitLab CI/CD Workflows for Rhiza

This directory contains GitLab CI/CD workflow configurations that mirror the functionality of the GitHub Actions workflows in `.github/workflows/`.

## Structure

```
.gitlab/
├── workflows/
│   ├── rhiza_ci.yml           # Continuous Integration - Python matrix testing
│   ├── rhiza_validate.yml     # Rhiza configuration validation
│   ├── rhiza_deptry.yml       # Dependency checking
│   ├── rhiza_pre-commit.yml   # Pre-commit hooks
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
**Purpose:** Validate Rhiza configuration against template.

**Trigger:**
- On push to any branch
- On merge requests to main/master

**Key Features:**
- Skips validation in the rhiza repository itself
- Uses uvx for ephemeral environment

**Equivalent GitHub Action:** `.github/workflows/rhiza_validate.yml`

---

### 3. Deptry (`rhiza_deptry.yml`)
**Purpose:** Check for missing and obsolete dependencies.

**Trigger:**
- On push to any branch
- On merge requests to main/master

**Key Features:**
- Automatic source folder detection
- Identifies unused dependencies

**Equivalent GitHub Action:** `.github/workflows/rhiza_deptry.yml`

---

### 4. Pre-commit (`rhiza_pre-commit.yml`)
**Purpose:** Run pre-commit checks for code quality.

**Trigger:**
- On push to any branch
- On merge requests to main/master

**Key Features:**
- Runs all pre-commit hooks
- UV environment setup

**Equivalent GitHub Action:** `.github/workflows/rhiza_pre-commit.yml`

---

### 5. Book (`rhiza_book.yml`)
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

### 6. Sync (`rhiza_sync.yml`)
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

### 7. Release (`rhiza_release.yml`)
**Purpose:** Create releases and publish packages to PyPI and container registries.

**Trigger:**
- On version tags (e.g., `v1.2.3`)

**Key Features:**
- Version validation
- Python package building with Hatch
- PyPI publishing with twine
- Devcontainer image publishing (conditional)
- GitLab release creation

**Equivalent GitHub Action:** `.github/workflows/rhiza_release.yml`

**GitLab-specific:**
- Uses GitLab Releases API instead of GitHub Releases
- Uses PYPI_TOKEN instead of OIDC Trusted Publishing
- Container registry is GitLab Container Registry by default

---

## Key Differences from GitHub Actions

### 1. **Syntax and Structure**
- **GitHub Actions:** Uses `jobs` and `steps` with `uses` for actions
- **GitLab CI:** Uses `jobs` with `script` and `before_script` sections

### 2. **Triggers**
- **GitHub Actions:** `on: push`, `on: pull_request`
- **GitLab CI:** `rules` with conditions like `if: $CI_PIPELINE_SOURCE == "merge_request_event"`

### 3. **Artifacts and Caching**
- **GitHub Actions:** `actions/upload-artifact@v6`, `actions/download-artifact@v7`
- **GitLab CI:** `artifacts: paths:` and automatic artifact passing between stages

### 4. **Container Images**
- **GitHub Actions:** `runs-on: ubuntu-latest` with `uses: actions/setup-python`
- **GitLab CI:** `image: python:3.12` or specific Docker images

### 5. **Matrix Strategy**
- **GitHub Actions:** Built-in `strategy.matrix` with dynamic values from JSON
- **GitLab CI:** `parallel.matrix` with limited dynamic support (workaround: child pipelines)

### 6. **Pages Deployment**
- **GitHub Actions:** `actions/deploy-pages@v4`
- **GitLab CI:** Job named `pages` with `artifacts: paths: [public]`

### 7. **Secrets and Variables**
- **GitHub Actions:** `secrets.*` and `vars.*`
- **GitLab CI:** `$CI_VARIABLE_NAME` or protected/masked variables

### 8. **Release Management**
- **GitHub Actions:** `softprops/action-gh-release@v2`
- **GitLab CI:** GitLab Releases API with `curl` commands

### 9. **Authentication**
- **GitHub Actions:** OIDC Trusted Publishing for PyPI, `GITHUB_TOKEN` for registry
- **GitLab CI:** Token-based authentication with `PYPI_TOKEN`, `CI_JOB_TOKEN` for registry

### 10. **Conditional Execution**
- **GitHub Actions:** `if:` conditions at job/step level
- **GitLab CI:** `rules:` at job level, `when:` for manual/conditional execution

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
