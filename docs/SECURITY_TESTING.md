# Security Testing Guide

This document describes the security testing approach for the Rhiza project, including the tools used, testing strategies, and how to interpret and address security findings.

## Overview

Security is a critical aspect of the Rhiza template system. We employ a defense-in-depth approach with multiple layers of security validation:

1. **Static Application Security Testing (SAST)** - Automated code analysis
2. **Security Test Suite** - Custom tests validating security patterns
3. **Dependency Scanning** - Vulnerability checks in dependencies
4. **Pre-commit Hooks** - Prevention at commit time

## Security Testing Tools

### Bandit

[Bandit](https://github.com/PyCQA/bandit) is a security linter specifically designed for Python. It scans code for common security issues.

**Configuration**: Configured in `.pre-commit-config.yaml` and `pyproject.toml`

**What it checks**:
- Subprocess calls with shell injection risks
- Weak cryptographic practices
- Hardcoded passwords and secrets
- Insecure deserialization
- SQL injection vulnerabilities

**Running Bandit**:
```bash
# Run via pre-commit
pre-commit run bandit --all-files

# Or directly with uv
uv tool run bandit -r . -c pyproject.toml
```

### Ruff Security Checks (S)

[Ruff](https://github.com/astral-sh/ruff) includes the flake8-bandit security ruleset (S rules) for finding security issues.

**Configuration**: Enabled in `ruff.toml` via the `"S"` rule set

**What it checks**:
- S1xx: Assert and exec/eval usage
- S2xx: Insecure functions (pickle, marshal, etc.)
- S3xx: Injection vulnerabilities
- S4xx: Cryptographic issues
- S5xx: YAML/XML security issues
- S6xx: Miscellaneous security issues

**Running Ruff Security Checks**:
```bash
# Check all files
make fmt

# Check only security rules
uv run ruff check --select S .

# Check production code only
uv run ruff check --select S book/
```

### Custom Security Test Suite

Located in `.rhiza/tests/security/test_security_patterns.py`, this suite validates that security tooling is properly configured. 

**Important**: This test suite does NOT duplicate security checks already performed by pre-commit hooks (Bandit, Ruff). The actual security scanning happens automatically via pre-commit.

**What it tests**:
- **Configuration validation**: Verifies Ruff S-rules and Bandit are enabled in configs
- **Documentation validation**: Ensures security exceptions (S101/S603/S607) are documented in test files
- **Custom patterns**: File permission checks (world-writable files) not covered by Bandit

**What Bandit/Ruff already handle** (not duplicated in tests):
- Subprocess safety (shell=True detection, command injection)
- Input validation (eval/exec usage)
- Hardcoded secrets (passwords, API keys)
- And many other security patterns

**Running Security Tests**:
```bash
# Run all 4 security configuration tests
uv run pytest .rhiza/tests/security/

# Run specific test class
uv run pytest .rhiza/tests/security/test_security_patterns.py::TestSecurityConfiguration

# Run with verbose output
uv run pytest .rhiza/tests/security/ -v
```

## Security Exceptions in Test Code

Test code has different security requirements than production code. The following security rules are disabled for test files:

### S101 - Assert Statements

**Why it's disabled**: Asserts are the standard way to validate conditions in pytest tests. They provide clear failure messages and are expected in test code.

**Example**:
```python
def test_something():
    result = do_something()
    assert result == expected  # S101 - OK in tests
```

### S603 - Subprocess Without shell=False

**Why it's disabled**: Tests need to call git, make, and other CLI tools via subprocess. Since test code controls all inputs and runs in a controlled environment, this is safe.

**Example**:
```python
subprocess.run(["git", "status"], check=True)  # S603 - OK in tests with list args
```

### S607 - Subprocess with Partial Path

**Why it's disabled**: Tests use standard development tools (git, make) available on PATH. The test environment is controlled and these are required dependencies.

**Example**:
```python
# S607 - OK in tests for required dev tools
subprocess.run(["git", "init"], check=True)
```

**Important**: Even in test code, we still follow security best practices:
- Use list-based arguments (not strings) for subprocess calls
- Never use `shell=True`
- Document security exceptions with `# nosec` comments
- Add explanatory comments in conftest.py and test utility files

## SAST Baseline

The SAST baseline captures the security state of production code and ensures no security regressions.

### Generating the Baseline

```bash
# Install bandit as a UV tool
uv tool install bandit

# Generate baseline for production code (excluding tests)
uv tool run bandit -r book/ .rhiza/scripts/ -f json -o .bandit-baseline.json

# Or generate text report
uv tool run bandit -r book/ .rhiza/scripts/ -f txt -o .bandit-baseline.txt
```

### Interpreting the Baseline

The baseline should show **zero security findings** in production code:
- `book/` - Marimo notebooks
- Any future production Python modules

Test code (`.rhiza/tests/`, `tests/`) is excluded from the baseline as it has different security requirements.

### Updating the Baseline

The baseline should be updated when:
1. New production code is added
2. Security findings are fixed
3. Legitimate new security exceptions are added

```bash
# Re-generate after changes
uv tool run bandit -r book/ -f json -o .bandit-baseline.json

# Commit the updated baseline
git add .bandit-baseline.json
git commit -m "Update SAST baseline"
```

## Security Testing Workflow

### During Development

1. **Pre-commit hooks** run automatically on `git commit`:
   - Ruff checks (including security rules)
   - Bandit scans

2. **Manual testing** before committing:
   ```bash
   # Run all tests including security tests
   make test

   # Run only security tests
   uv run pytest .rhiza/tests/security/
   ```

### During Code Review

1. Review any `# nosec` comments to ensure they're justified
2. Check that security exceptions in test code are documented
3. Verify new subprocess calls use list-based arguments
4. Ensure no secrets are hardcoded

### In CI/CD

1. **GitHub Actions** runs on every PR:
   - Full test suite (includes security tests)
   - Ruff checks (includes security rules)
   - Pre-commit hooks validation

2. **CodeQL** scans for security vulnerabilities:
   - Configured in `.github/workflows/codeql.yml`
   - Runs on push to main and on PRs

## Common Security Issues and Solutions

### Issue: Subprocess with shell=True

**Problem**:
```python
# BAD - vulnerable to shell injection
subprocess.run(f"git {user_input}", shell=True)
```

**Solution**:
```python
# GOOD - uses list arguments, safe from injection
subprocess.run(["git", "status"], check=True)
```

### Issue: Hardcoded Secrets

**Problem**:
```python
# BAD - API key in code
api_key = "sk_live_abc123..."
```

**Solution**:
```python
# GOOD - load from environment
import os
api_key = os.environ.get("API_KEY")
```

### Issue: Using eval() or exec()

**Problem**:
```python
# BAD - executes arbitrary code
result = eval(user_input)
```

**Solution**:
```python
# GOOD - safe alternatives
import json
result = json.loads(user_input)  # For JSON data

import ast
result = ast.literal_eval(user_input)  # For Python literals
```

### Issue: World-writable Files

**Problem**:
```python
# BAD - file can be modified by any user
file.chmod(0o777)
```

**Solution**:
```python
# GOOD - owner can write, others can read/execute
file.chmod(0o755)

# BETTER - only owner can access
file.chmod(0o700)
```

## Responding to Security Findings

### 1. Analyze the Finding

- **Understand the issue**: Read the rule description and example
- **Assess the risk**: Is this a real vulnerability or a false positive?
- **Check the context**: Is this in test code where different rules apply?

### 2. Fix or Justify

**If it's a real issue**:
- Fix the code to use secure patterns
- Add a test to prevent regression
- Update the SAST baseline

**If it's a false positive**:
- Document why it's safe with a comment
- Add `# nosec <code>` to suppress the warning
- Consider if the code can be refactored to avoid the pattern

### 3. Document the Decision

Add inline comments explaining security decisions:
```python
# Using subprocess with git is safe here because:
# 1. git is a required development dependency
# 2. all arguments are from trusted sources (configuration files)
# 3. we use list-based arguments, not shell strings
subprocess.run(["git", "status"], check=True)  # nosec B603, B607
```

## Security Testing Checklist

Before merging any PR with code changes:

- [ ] All security configuration tests pass (`pytest .rhiza/tests/security/`)
- [ ] Pre-commit hooks pass (includes Bandit and Ruff security checks)
- [ ] No new security findings from Bandit in pre-commit
- [ ] No new security findings from Ruff (`make fmt`)
- [ ] Any `# nosec` comments are documented and justified
- [ ] No hardcoded secrets in the code
- [ ] SAST baseline is updated if production code changed

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Common web security risks
- [Bandit Documentation](https://bandit.readthedocs.io/) - Bandit rule reference
- [Ruff Security Rules](https://docs.astral.sh/ruff/rules/#flake8-bandit-s) - Ruff S-rules reference
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [CWE Database](https://cwe.mitre.org/) - Common Weakness Enumeration

## Contact

For security vulnerabilities, please see [SECURITY.md](SECURITY.md) for our responsible disclosure process.
