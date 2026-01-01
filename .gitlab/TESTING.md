# GitLab CI/CD Testing Guide

This document provides instructions for testing the GitLab CI/CD workflows.

## Prerequisites

1. A GitLab account (gitlab.com or self-hosted)
2. A GitLab repository (can be a mirror/fork of the GitHub repository)
3. Access to GitLab CI/CD settings

## Testing Approach

Since this is the rhiza repository itself, comprehensive testing requires:
1. Creating a test project/fork in GitLab
2. Configuring CI/CD variables
3. Triggering each workflow type

## Quick Validation

### 1. YAML Syntax Validation

All workflow files have been validated for YAML syntax:

```bash
# Validate all YAML files
for file in .gitlab-ci.yml .gitlab/workflows/*.yml; do
    python3 -c "import yaml; yaml.safe_load(open('$file'))" && \
    echo "✅ $file is valid YAML"
done
```

**Result:** All 8 files (1 main + 7 workflows) are valid YAML.

### 2. GitLab CI Lint

You can validate the configuration using GitLab's CI Lint tool:

**Option A: Web UI**
1. Go to your GitLab project
2. Navigate to **CI/CD > Pipelines**
3. Click **CI Lint** button (or visit `/-/ci/lint`)
4. Paste the contents of `.gitlab-ci.yml`
5. Click **Validate**

**Option B: API** (requires GitLab access token)
```bash
curl --header "PRIVATE-TOKEN: <your_token>" \
  "https://gitlab.com/api/v4/projects/<project_id>/ci/lint" \
  --form "content=@.gitlab-ci.yml"
```

## Workflow-Specific Testing

### 1. CI Workflow (`rhiza_ci.yml`)

**Test trigger:** Push to any branch or create merge request

**Expected behavior:**
- Generates Python version matrix (3.11, 3.12, 3.13)
- Runs tests in parallel for each Python version
- Uses UV for dependency management
- Supports Git LFS

**Manual test:**
```bash
# Push to a test branch
git checkout -b test-gitlab-ci
git push origin test-gitlab-ci
```

**Success criteria:**
- Pipeline shows 3 test jobs (one per Python version)
- All tests pass
- Git LFS files are downloaded correctly

---

### 2. Validate Workflow (`rhiza_validate.yml`)

**Test trigger:** Push to any branch or create merge request

**Expected behavior:**
- Skips in the rhiza repository itself
- Runs `rhiza validate .` in downstream projects

**Manual test:**
This workflow is designed for repositories that use rhiza as a template, not for rhiza itself.

**Success criteria:**
- Job skips in rhiza repository
- Would run and validate in downstream projects

---

### 3. Deptry Workflow (`rhiza_deptry.yml`)

**Test trigger:** Push to any branch or create merge request

**Expected behavior:**
- Checks for missing/obsolete dependencies
- Automatically detects source folder (`src/` or `.`)
- Reports unused dependencies

**Manual test:**
```bash
# Run deptry locally
uvx deptry src/
```

**Success criteria:**
- Dependency check completes
- No critical dependency issues found

---

### 4. Pre-commit Workflow (`rhiza_pre-commit.yml`)

**Test trigger:** Push to any branch or create merge request

**Expected behavior:**
- Runs all pre-commit hooks
- Checks code formatting, linting, etc.

**Manual test:**
```bash
# Run pre-commit locally
uv run pre-commit run --all-files
```

**Success criteria:**
- All pre-commit checks pass
- No formatting or linting issues

---

### 5. Book Workflow (`rhiza_book.yml`)

**Test trigger:** Push to `main` or `master` branch

**Expected behavior:**
- Builds comprehensive documentation
- Combines API docs, tests, coverage, notebooks
- Deploys to GitLab Pages (public/ directory)

**Manual test:**
```bash
# Build book locally
make book
ls -la _book/
```

**Success criteria:**
- Documentation builds successfully
- GitLab Pages deployment succeeds
- Pages are accessible at `https://<username>.gitlab.io/<project>/`

**Configuration needed:**
- Enable GitLab Pages in project settings
- Set `PUBLISH_COMPANION_BOOK=true` (default)

---

### 6. Sync Workflow (`rhiza_sync.yml`)

**Test trigger:** Manual pipeline, scheduled pipeline, or web trigger

**Expected behavior:**
- Syncs repository with template
- Creates a new branch
- Commits changes
- Optionally creates merge request

**Manual test:**
```bash
# Trigger manually from GitLab UI
# CI/CD > Pipelines > Run pipeline
```

**Success criteria:**
- Template synchronization completes
- New branch created if changes detected
- No changes if already in sync

**Configuration needed:**
- Set `PAT_TOKEN` for workflow modifications
- Set `CREATE_MR=true` to auto-create merge requests

---

### 7. Release Workflow (`rhiza_release.yml`)

**Test trigger:** Push a version tag (e.g., `v1.0.0`)

**Expected behavior:**
- Validates tag format
- Builds Python package
- Creates GitLab release
- Publishes to PyPI (if configured)
- Publishes devcontainer (if configured)
- Finalizes release with links

**Manual test:**
```bash
# Create and push a test tag
git tag v0.0.1-test
git push origin v0.0.1-test
```

**Success criteria:**
- Version matches pyproject.toml
- Package builds successfully
- GitLab release created
- PyPI upload succeeds (if PYPI_TOKEN set)
- Devcontainer publishes (if PUBLISH_DEVCONTAINER=true)

**Configuration needed:**
- Set `PYPI_TOKEN` for PyPI publishing
- Set `PUBLISH_DEVCONTAINER=true` for devcontainer
- Optionally set `PYPI_REPOSITORY_URL` for custom feed

---

## Required CI/CD Variables

Set these in GitLab project settings (Settings > CI/CD > Variables):

### Secrets (Protected & Masked)
- `PYPI_TOKEN` - PyPI authentication token (for releases)
- `PAT_TOKEN` - Project/Group Access Token (for sync workflow)

### Configuration Variables
- `UV_EXTRA_INDEX_URL` - Extra index URL for UV (optional)
- `PYPI_REPOSITORY_URL` - Custom PyPI URL (optional)
- `PUBLISH_COMPANION_BOOK` - Publish documentation (default: true)
- `CREATE_MR` - Auto-create merge requests (default: true)

## Complete Testing Checklist

- [x] Validate YAML syntax for all workflow files
- [ ] Set up test GitLab repository
- [ ] Configure required CI/CD variables
- [ ] Test CI workflow (push to branch)
- [ ] Test Validate workflow (in downstream project)
- [ ] Test Deptry workflow
- [ ] Test Pre-commit workflow
- [ ] Test Book workflow (push to main)
- [ ] Test Sync workflow (manual trigger)
- [ ] Test Release workflow (push version tag)
- [ ] Verify GitLab Pages deployment
- [ ] Verify container registry images
- [ ] Verify PyPI package upload (test PyPI)

## Known Limitations

1. **Dynamic Matrix:** GitLab CI has limited support for dynamic parallel matrices. Where dynamic matrices are needed, consider generating jobs via child pipelines or iterate within a job.

2. **Merge Request Creation:** The Sync workflow doesn't automatically create merge requests via the API (would require additional setup with GitLab CLI or API calls).

3. **OIDC Publishing:** GitLab CI doesn't support OIDC-based PyPI publishing like GitHub Actions. Token-based authentication is used instead.

4. **Devcontainer CLI:** Requires Node.js and devcontainer CLI installation in the job, which adds overhead.

## Troubleshooting

### Pipeline doesn't start
- Check if `.gitlab-ci.yml` is in the root directory
- Verify YAML syntax is valid
- Check pipeline rules match the trigger condition

### Permission errors
- Ensure required variables are set
- Check if tokens have correct scopes
- Verify project permissions

### GitLab Pages not deploying
- Ensure job is named `pages`
- Verify artifacts are in `public/` directory
- Check if GitLab Pages is enabled in project settings
- Ensure pipeline runs on default branch

## Next Steps

1. **Create test repository:** Fork or mirror rhiza to GitLab
2. **Configure variables:** Set all required CI/CD variables
3. **Test incrementally:** Test each workflow type individually
4. **Document issues:** Report any platform-specific issues
5. **Iterate:** Fix issues and retest

## Support

- **GitLab CI/CD Docs:** https://docs.gitlab.com/ee/ci/
- **GitLab API Docs:** https://docs.gitlab.com/ee/api/
- **Rhiza Repository:** https://github.com/jebel-quant/rhiza
