# Changelog Generation Guide

This document describes how Rhiza generates changelogs and how to enhance them with better PR categorization.

## Current Implementation

Rhiza uses GitHub's built-in release notes generation feature via the `softprops/action-gh-release` action in the release workflow (`.github/workflows/rhiza_release.yml`).

### How It Works

When a release is triggered by pushing a version tag:

```bash
git tag v0.8.0
git push origin v0.8.0
```

The release workflow:
1. Validates the tag format
2. Builds distribution artifacts
3. Creates a draft GitHub release with `generate_release_notes: true`
4. Publishes to PyPI (if applicable)
5. Publishes devcontainer (if configured)
6. Finalizes the release

GitHub automatically generates release notes by:
- Listing all PRs merged since the last release
- Grouping by PR labels
- Including contributor attribution
- Showing full changelog link

## Enhancing Changelog with PR Categorization

To get better-organized changelogs, use GitHub's release notes categories feature.

### 1. Configure Release Categories

Create or update `.github/release.yml` in your repository:

```yaml
# .github/release.yml
changelog:
  exclude:
    labels:
      - ignore-for-release
      - dependencies
      - duplicate
      - question
      - invalid
      - wontfix
    authors:
      - octocat
      - dependabot
      - renovate
  
  categories:
    - title: 🚀 Features
      labels:
        - feature
        - enhancement
    
    - title: 🐛 Bug Fixes
      labels:
        - bug
        - fix
    
    - title: 📚 Documentation
      labels:
        - documentation
        - docs
    
    - title: 🔧 Technical Debt
      labels:
        - technical-debt
        - refactor
        - cleanup
    
    - title: 🏗️ Infrastructure
      labels:
        - ci
        - build
        - infrastructure
    
    - title: ⚡ Performance
      labels:
        - performance
        - optimization
    
    - title: 🧪 Testing
      labels:
        - test
        - testing
    
    - title: 🔒 Security
      labels:
        - security
        - vulnerability
    
    - title: 📦 Dependencies
      labels:
        - dependencies
        - deps
    
    - title: 🔄 Other Changes
      labels:
        - "*"
```

### 2. Label Your Pull Requests

For automatic categorization, ensure PRs are properly labeled:

#### Automation via PR Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Description
<!-- Describe your changes -->

## Type of Change
<!-- Put an 'x' in the boxes that apply -->

- [ ] 🚀 Feature (new functionality)
- [ ] 🐛 Bug fix (fixes an issue)
- [ ] 📚 Documentation (docs only)
- [ ] 🔧 Technical debt (refactoring, cleanup)
- [ ] 🏗️ Infrastructure (CI/CD, build changes)
- [ ] ⚡ Performance (optimization)
- [ ] 🧪 Testing (test changes)
- [ ] 🔒 Security (security improvements)

## Testing
<!-- How was this tested? -->

## Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Changelog updated (if needed)
```

#### Automation via Workflow

Create `.github/workflows/label-pr.yml`:

```yaml
name: Label Pull Request

on:
  pull_request:
    types: [opened, edited, synchronize]

permissions:
  pull-requests: write
  contents: read

jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - name: Label based on branch name
        uses: actions/labeler@v5
        with:
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          configuration-path: .github/labeler.yml
      
      - name: Label based on files changed
        uses: actions/labeler@v5
        with:
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          sync-labels: true
```

Create `.github/labeler.yml`:

```yaml
# .github/labeler.yml
documentation:
  - changed-files:
    - any-glob-to-any-file: 
      - 'docs/**/*'
      - '*.md'
      - 'book/**/*'

test:
  - changed-files:
    - any-glob-to-any-file: 
      - 'tests/**/*'
      - '**/*_test.py'
      - '**/*test_*.py'

ci:
  - changed-files:
    - any-glob-to-any-file:
      - '.github/workflows/**/*'
      - '.gitlab-ci.yml'
      - '.github/actions/**/*'

infrastructure:
  - changed-files:
    - any-glob-to-any-file:
      - 'Makefile'
      - '**/*.mk'
      - 'pyproject.toml'
      - '.pre-commit-config.yaml'

dependencies:
  - changed-files:
    - any-glob-to-any-file:
      - 'pyproject.toml'
      - 'uv.lock'
```

### 3. Manual Categorization

If you prefer manual control, label PRs before merging:

1. Open the PR on GitHub
2. In the right sidebar, click **Labels**
3. Select appropriate category label(s)
4. Multiple labels are fine - PR appears in each category

### 4. Customizing Release Notes

#### Override Auto-generated Notes

When creating a release manually:

1. Go to repository **Releases**
2. Click **Draft a new release**
3. Enter tag name
4. Click **Generate release notes**
5. Edit the generated text as needed
6. Add highlights or breaking changes
7. Publish release

#### Adding Release Highlights

Enhance auto-generated notes with manual highlights:

```markdown
## 🌟 Highlights

This release focuses on maintainability and developer experience:

- Added comprehensive roadmap and technical debt tracking
- New `make todos` command for finding code comments
- GitHub project board setup guide
- Enhanced changelog generation with PR categorization

---

## 🚀 Features
[auto-generated PR list]

## 🐛 Bug Fixes
[auto-generated PR list]

...
```

## Best Practices

### PR Title Conventions

Use clear, descriptive PR titles as they appear directly in the changelog:

- ✅ Good: "Add make todos target for scanning TODO comments"
- ✅ Good: "Fix template sync conflict resolution"
- ❌ Bad: "Update code"
- ❌ Bad: "Fix bug"

### Conventional Commits

Consider using [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add make todos target for scanning TODO comments
fix: resolve template sync conflict issues
docs: add project board setup guide
refactor: simplify changelog generation logic
test: add integration tests for template sync
```

Tools like [semantic-release](https://github.com/semantic-release/semantic-release) can automate versioning based on commit messages.

### Breaking Changes

Clearly mark breaking changes:

```markdown
## ⚠️ Breaking Changes

- **Template Sync**: The `sync` command now requires `template.yml` configuration
  - Migration: Copy `.rhiza/template.yml.example` to `.rhiza/template.yml`
  - See docs/MIGRATION.md for details
```

### Upgrade Instructions

Include upgrade guidance:

```markdown
## 📦 Upgrading

To upgrade to v0.8.0:

```bash
# Update your template reference
sed -i 's/ref: v0.7.5/ref: v0.8.0/' .rhiza/template.yml

# Run sync
make sync
```

See [UPGRADING.md](docs/UPGRADING.md) for detailed instructions.
```

## Advanced: Automated Changelog

For fully automated changelog generation, consider these tools:

### 1. Release Drafter

Automatically drafts release notes as PRs are merged.

Create `.github/workflows/release-drafter.yml`:

```yaml
name: Release Drafter

on:
  push:
    branches:
      - main
  pull_request:
    types: [opened, reopened, synchronize]

permissions:
  contents: read
  pull-requests: read

jobs:
  update_release_draft:
    permissions:
      contents: write
      pull-requests: write
    runs-on: ubuntu-latest
    steps:
      - uses: release-drafter/release-drafter@v6
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Create `.github/release-drafter.yml`:

```yaml
name-template: 'v$RESOLVED_VERSION'
tag-template: 'v$RESOLVED_VERSION'

categories:
  - title: '🚀 Features'
    labels:
      - 'feature'
      - 'enhancement'
  - title: '🐛 Bug Fixes'
    labels:
      - 'bug'
      - 'fix'
  - title: '📚 Documentation'
    labels:
      - 'documentation'
  - title: '🔧 Maintenance'
    labels:
      - 'technical-debt'
      - 'refactor'

version-resolver:
  major:
    labels:
      - 'major'
      - 'breaking'
  minor:
    labels:
      - 'minor'
      - 'feature'
  patch:
    labels:
      - 'patch'
      - 'bug'
      - 'fix'
  default: patch

template: |
  ## Changes

  $CHANGES
```

### 2. Semantic Release

Fully automated versioning and changelog based on commit messages.

```bash
npm install --save-dev semantic-release
```

Configure in `.releaserc.yml`:

```yaml
branches:
  - main
plugins:
  - '@semantic-release/commit-analyzer'
  - '@semantic-release/release-notes-generator'
  - '@semantic-release/changelog'
  - '@semantic-release/github'
  - '@semantic-release/git'
```

## Verification

After implementing changelog enhancements:

1. **Create a test PR** with proper labels
2. **Merge the PR** to main/master branch
3. **Create and push a test tag** (e.g., `v0.8.0-beta.1`)
4. **Check the draft release** on GitHub
5. **Verify categorization** matches your labels
6. **Iterate on configuration** as needed

## Maintenance

### Regular Reviews

- **Monthly**: Review changelog quality and adjust categories
- **Quarterly**: Update labeling rules based on usage patterns
- **Annually**: Refine PR templates and automation

### Metrics to Track

- Percentage of PRs with proper labels
- Time from PR merge to release
- Quality of release notes (team feedback)
- Adoption of categorization system

## Resources

- [GitHub Release Notes Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes)
- [Release Configuration Schema](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes#configuration-options)
- [Release Drafter](https://github.com/release-drafter/release-drafter)
- [Semantic Release](https://semantic-release.gitbook.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Last Updated**: February 2026

For related documentation:
- [ROADMAP.md](../ROADMAP.md) - Project roadmap
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [.github/workflows/rhiza_release.yml](../.github/workflows/rhiza_release.yml) - Release workflow
