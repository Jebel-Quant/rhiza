# GitLab CI/CD Integration

This repository includes GitLab CI/CD workflows that mirror all GitHub Actions functionality.

## Quick Start

1. **Mirror to GitLab:** Create a GitLab repository (mirror or fork)
2. **Configure Variables:** Set required CI/CD variables (see below)
3. **Push Code:** The `.gitlab-ci.yml` will automatically trigger pipelines

## File Structure

```
.gitlab-ci.yml              # Main GitLab CI configuration
.gitlab/
├── README.md               # Comprehensive documentation
├── TESTING.md              # Testing guide
└── workflows/              # Individual workflow definitions
    ├── rhiza_ci.yml
    ├── rhiza_devcontainer.yml
    ├── rhiza_marimo.yml
    ├── rhiza_validate.yml
    ├── rhiza_deptry.yml
    ├── rhiza_docker.yml
    ├── rhiza_pre-commit.yml
    ├── rhiza_book.yml
    ├── rhiza_sync.yml
    └── rhiza_release.yml
```

## Workflow Equivalents

| GitHub Actions | GitLab CI | Purpose |
|----------------|-----------|---------|
| `rhiza_ci.yml` | `rhiza_ci.yml` | Python matrix testing |
| `rhiza_devcontainer.yml` | `rhiza_devcontainer.yml` | Devcontainer build |
| `rhiza_marimo.yml` | `rhiza_marimo.yml` | Notebook testing |
| `rhiza_validate.yml` | `rhiza_validate.yml` | Config validation |
| `rhiza_deptry.yml` | `rhiza_deptry.yml` | Dependency check |
| `rhiza_docker.yml` | `rhiza_docker.yml` | Docker lint/build |
| `rhiza_pre-commit.yml` | `rhiza_pre-commit.yml` | Code quality |
| `rhiza_book.yml` | `rhiza_book.yml` | Documentation |
| `rhiza_sync.yml` | `rhiza_sync.yml` | Template sync |
| `rhiza_release.yml` | `rhiza_release.yml` | Release pipeline |

## Required Configuration

### Secrets (Protected & Masked)
Set in **Settings > CI/CD > Variables**:

- `PYPI_TOKEN` - For PyPI publishing (releases)
- `PAT_TOKEN` - For workflow modifications (sync)

### Optional Variables
- `UV_EXTRA_INDEX_URL` - Extra package index
- `DEVCONTAINER_REGISTRY` - Container registry (default: registry.gitlab.com)
- `PUBLISH_DEVCONTAINER` - Publish devcontainer (default: false)
- `PYPI_REPOSITORY_URL` - Custom PyPI URL
- `PUBLISH_COMPANION_BOOK` - Publish docs (default: true)

## Key Differences from GitHub Actions

1. **Pages:** Uses `public/` directory instead of `_book/`
2. **Authentication:** Token-based instead of OIDC
3. **Matrix:** Limited dynamic matrix support (notebooks run sequentially)
4. **Triggers:** Uses `rules:` instead of `on:`
5. **Registry:** GitLab Container Registry by default

## Documentation

- **Full Documentation:** [.gitlab/README.md](.gitlab/README.md)
- **Testing Guide:** [.gitlab/TESTING.md](.gitlab/TESTING.md)
- **GitLab CI Docs:** https://docs.gitlab.com/ee/ci/

## Validation

All YAML files have been validated:

```bash
# Validate syntax
for file in .gitlab-ci.yml .gitlab/workflows/*.yml; do
    python3 -c "import yaml; yaml.safe_load(open('$file'))"
done
```

Result: ✅ All 11 files are valid YAML

## Testing

See [.gitlab/TESTING.md](.gitlab/TESTING.md) for:
- Workflow-specific testing instructions
- Configuration requirements
- Troubleshooting guide
- Complete testing checklist

## Support

- Issues specific to GitLab CI: See [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- Rhiza-specific issues: See main [README.md](README.md)
- Platform differences: See [.gitlab/README.md](.gitlab/README.md)

## Contributing

When modifying workflows:
1. Update both GitHub Actions and GitLab CI versions
2. Maintain feature parity between platforms
3. Test in a fork/mirror before merging
4. Document platform-specific differences

## License

Same license as the main repository.
