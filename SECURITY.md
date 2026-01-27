# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.6.x   | :white_check_mark: |
| < 0.6   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please report security vulnerabilities through one of these channels:

1. **GitHub Security Advisories (Preferred)**
   - Navigate to the [Security tab](https://github.com/Jebel-Quant/rhiza/security/advisories)
   - Click "Report a vulnerability"
   - Fill out the form with details about the vulnerability

2. **Private Disclosure**
   - Open a [private security advisory](https://github.com/Jebel-Quant/rhiza/security/advisories/new)

### What to Include

Please include the following information in your report:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Affected versions** of Rhiza
- **Potential impact** of the vulnerability
- **Suggested fix** (if you have one)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Assessment**: We will assess the vulnerability and determine its severity
- **Updates**: We will keep you informed of our progress
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

### Scope

This security policy applies to:

- The Rhiza repository and its templates
- GitHub Actions workflows provided by Rhiza
- Shell scripts in `.rhiza/scripts/`
- Python utilities in `.rhiza/utils/`

### Out of Scope

The following are not considered security vulnerabilities:

- Vulnerabilities in dependencies (report these to the respective projects)
- Issues in projects that use Rhiza templates (report these to those projects)
- Denial of service through resource exhaustion in CI workflows
- Security issues requiring physical access to a machine

## Security Best Practices

When using Rhiza templates, we recommend:

1. **Review workflow permissions** - Ensure workflows use minimal required permissions
2. **Pin action versions** - Use specific versions rather than floating tags
3. **Use Trusted Publishing** - For PyPI releases, use OIDC instead of stored tokens
4. **Enable branch protection** - Require PR reviews for changes to main branch
5. **Rotate secrets regularly** - Update PAT tokens and other secrets periodically

## Security Features

Rhiza includes several security features:

- **CodeQL Analysis** - Automated security scanning for Python and GitHub Actions
- **Minimal Permissions** - Workflows default to `contents: read`
- **OIDC Authentication** - Trusted publishing to PyPI without stored credentials
- **Dependency Locking** - `uv.lock` ensures reproducible builds
- **Pre-commit Hooks** - Automated checks for common security issues
