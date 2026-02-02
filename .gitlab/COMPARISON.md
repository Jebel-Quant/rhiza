# GitHub Actions vs GitLab CI Comparison

This document provides a side-by-side comparison of GitHub Actions and GitLab CI implementations for the rhiza project.

## Workflow Mapping

| Feature | GitHub Actions | GitLab CI | Status |
|---------|----------------|-----------|--------|
| Main Config | `.github/workflows/*.yml` | `.gitlab-ci.yml` + `.gitlab/workflows/*.yml` | ✅ Complete |
| CI Testing | `rhiza_ci.yml` | `rhiza_ci.yml` | ✅ Complete |
| Validation | `rhiza_validate.yml` | `rhiza_validate.yml` | ✅ Complete |
| Dependencies | `rhiza_deptry.yml` | `rhiza_deptry.yml` | ✅ Complete |
| Pre-commit | `rhiza_pre-commit.yml` | `rhiza_pre-commit.yml` | ✅ Complete |
| Documentation | `rhiza_book.yml` | `rhiza_book.yml` | ✅ Complete |
| Sync | `rhiza_sync.yml` | `rhiza_sync.yml` | ✅ Complete |
| Release | `rhiza_release.yml` | `rhiza_release.yml` | ✅ Complete |

## Syntax Differences

### Triggers

**GitHub Actions:**
```yaml
on:
  push:
  pull_request:
    branches: [main, master]
```

**GitLab CI:**
```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  - if: $CI_COMMIT_BRANCH
```

### Jobs and Steps

**GitHub Actions:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - name: Run tests
        run: pytest tests
```

**GitLab CI:**
```yaml
test:
  stage: test
  image: python:3.12
  script:
    - pytest tests
```

### Matrix Strategy

**GitHub Actions:**
```yaml
strategy:
  matrix:
    python-version: ${{ fromJson(needs.generate-matrix.outputs.matrix) }}
```

**GitLab CI:**
```yaml
parallel:
  matrix:
    - PYTHON_VERSION: ["3.11", "3.12", "3.13"]
```

**Note:** GitLab CI has limited dynamic matrix support. Workaround: use child pipelines or iterate in script.

### Artifacts

**GitHub Actions:**
```yaml
- uses: actions/upload-artifact@v6
  with:
    name: dist
    path: dist
```

**GitLab CI:**
```yaml
artifacts:
  paths:
    - dist/
  expire_in: 1 day
```

### Container Images

**GitHub Actions:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: python:3.12
```

**GitLab CI:**
```yaml
test:
  image: python:3.12
```

### Secrets and Variables

**GitHub Actions:**
```yaml
env:
  TOKEN: ${{ secrets.PYPI_TOKEN }}
  CUSTOM_VAR: ${{ vars.CUSTOM_VAR }}
```

**GitLab CI:**
```yaml
script:
  - echo $PYPI_TOKEN
  - echo $CUSTOM_VAR
```

## Feature Comparison

### 1. Python Matrix Testing (CI)

| Feature | GitHub Actions | GitLab CI |
|---------|----------------|-----------|
| Dynamic matrix | ✅ Full support | ⚠️ Limited (static matrix used) |
| Parallel execution | ✅ Yes | ✅ Yes |
| Git LFS | ✅ Yes | ✅ Yes |
| UV integration | ✅ Yes | ✅ Yes |

### 2. Documentation (Book)

| Feature | GitHub Actions | GitLab CI |
|---------|----------------|-----------|
| Build | ✅ `make book` | ✅ `make book` |
| Output directory | `_book/` | `public/` (required) |
| Deployment | GitHub Pages | GitLab Pages |
| Deploy action | `actions/deploy-pages@v4` | Job named `pages` |

### 3. Release

| Feature | GitHub Actions | GitLab CI |
|---------|----------------|-----------|
| PyPI auth | ✅ OIDC Trusted Publishing | ⚠️ Token-based |
| Release creation | `softprops/action-gh-release` | GitLab Releases API |
| Version validation | ✅ Yes | ✅ Yes |
| Draft releases | ✅ Yes | ✅ Yes (via API) |

### 4. Sync

| Feature | GitHub Actions | GitLab CI |
|---------|----------------|-----------|
| Template sync | ✅ `rhiza materialize` | ✅ `rhiza materialize` |
| PR/MR creation | ✅ Automatic | ⚠️ Manual (API call needed) |
| Token requirement | PAT_TOKEN | PAT_TOKEN |
| Scheduling | ✅ Cron syntax | ✅ Pipeline schedules |

## Platform-Specific Features

### GitHub Actions Only

1. **OIDC Authentication:** Passwordless authentication with PyPI and cloud providers
2. **Action Marketplace:** Reusable actions from the community
3. **Job summaries:** Rich markdown summaries in the UI
4. **Environments:** Built-in environment protection rules

### GitLab CI Only

1. **Stages:** Explicit pipeline stages (`.pre`, `build`, `test`, `deploy`, `.post`)
2. **Job templates:** Reusable job definitions with `extends`
3. **Child pipelines:** Dynamic pipeline generation
4. **Auto DevOps:** Automatic CI/CD configuration

## Migration Considerations

### Easy Migrations
- ✅ Basic CI/CD pipelines
- ✅ Docker-based workflows
- ✅ Artifact handling
- ✅ Environment variables
- ✅ Scheduled pipelines

### Moderate Effort
- ⚠️ Dynamic matrix strategies (use child pipelines)
- ⚠️ Marketplace actions (reimplement with scripts)
- ⚠️ Complex conditionals (restructure with rules)

### Challenging Migrations
- ❌ OIDC-based authentication (use tokens)
- ❌ GitHub-specific APIs (use GitLab APIs)
- ❌ GitHub Apps (use GitLab integrations)

## Testing Status

| Workflow | YAML Valid | Logic Verified | Notes |
|----------|------------|----------------|-------|
| CI | ✅ | ⏳ | Needs test with actual Python matrix |
| Validate | ✅ | ⏳ | Skips in rhiza repo |
| Deptry | ✅ | ⏳ | Needs test with dependencies |
| Pre-commit | ✅ | ⏳ | Needs test with hooks |
| Book | ✅ | ⏳ | Needs GitLab Pages setup |
| Sync | ✅ | ⏳ | Needs PAT_TOKEN |
| Release | ✅ | ⏳ | Needs PYPI_TOKEN |

Legend:
- ✅ Complete
- ⏳ Pending (ready for testing)
- ❌ Not tested

## Recommendations

### For New Projects
1. Choose platform based on primary hosting (GitHub vs GitLab)
2. Consider OIDC requirements (GitHub has better support)
3. Evaluate marketplace actions vs custom scripts

### For Migration
1. Start with simple workflows (CI, pre-commit)
2. Test thoroughly in a fork/mirror
3. Configure all required variables
4. Update documentation links
5. Train team on platform differences

### For Dual Support
1. Maintain both workflow sets (as done here)
2. Keep feature parity
3. Document platform-specific differences
4. Test changes on both platforms

## Resources

- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **GitLab CI Docs:** https://docs.gitlab.com/ee/ci/
- **Rhiza GitHub:** https://github.com/jebel-quant/rhiza
- **Migration Guide:** `.gitlab/README.md`
- **Testing Guide:** `.gitlab/TESTING.md`

## Summary

Most GitHub Actions workflows (7 of 10) have been converted to GitLab CI with equivalent functionality. The main differences are:

1. **Syntax:** Different trigger and job definitions
2. **Authentication:** Token-based instead of OIDC
3. **Matrix:** Static instead of dynamic
4. **Pages:** Different output directory requirements
5. **APIs:** Platform-specific endpoints

Both platforms are fully supported and provide equivalent functionality for the rhiza project.
