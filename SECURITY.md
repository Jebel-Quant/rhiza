# Security Policy

## Supported Versions

We actively maintain security updates for the following versions of Rhiza:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

We take the security of Rhiza seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **GitHub Security Advisories** (Preferred)
   - Navigate to the [Security tab](https://github.com/Jebel-Quant/rhiza/security/advisories) of this repository
   - Click "Report a vulnerability"
   - Provide detailed information about the vulnerability

2. **Email**
   - Contact the maintainers directly through GitHub
   - Include "SECURITY" in the subject line
   - Provide detailed information about the vulnerability

### What to Include

When reporting a vulnerability, please include:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested fixes or mitigations (if available)
- Your contact information for follow-up questions

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Updates**: We will send you regular updates about our progress
- **Timeline**: We aim to resolve critical vulnerabilities within 7 days
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Measures

### Automated Security Scanning

This repository uses automated security scanning tools:

- **CodeQL Analysis**: Automated code scanning for security vulnerabilities
- **Dependency Scanning**: Regular checks for vulnerable dependencies via Renovate
- **Pre-commit Hooks**: Security checks run automatically before each commit

### Security Best Practices

When contributing to Rhiza:

- Never commit secrets, API keys, or credentials
- Follow secure coding practices as outlined in our [Contributing Guide](CONTRIBUTING.md)
- Keep dependencies up to date
- Run `make fmt` to ensure code meets our security standards

### Workflow Security

The GitHub Actions workflows in this repository follow security best practices:

- Minimal permissions granted to workflows
- Secrets managed through GitHub's encrypted secrets
- Pull request workflows run with limited permissions
- Regular updates to GitHub Actions via Renovate

## Disclosure Policy

When a security vulnerability is confirmed:

1. We will create a security advisory on GitHub
2. We will develop and test a fix
3. We will release a patch version with the fix
4. We will publish the security advisory with details
5. We will credit the reporter (if desired)

## Security Updates

Security updates are released as patch versions (e.g., 0.3.1) and are clearly marked in:

- GitHub Releases
- CHANGELOG (if applicable)
- Security Advisories

Users are encouraged to update to the latest version to receive security fixes.

## Questions

If you have questions about this security policy, please open a discussion in the repository or contact the maintainers.
