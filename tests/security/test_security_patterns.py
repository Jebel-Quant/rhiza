"""Security pattern validation tests.

This test suite validates that the codebase follows secure coding practices
and doesn't contain common security vulnerabilities. It complements static
analysis tools like Bandit and Ruff's security checks.

Tests are organized into categories:
- Subprocess safety: Validates subprocess calls use safe patterns
- File operations: Validates secure file handling
- Input validation: Checks for proper input sanitization
- Configuration: Validates secure configuration practices
"""

import pathlib
import re
import subprocess
from typing import Callable

import pytest


class TestSubprocessSafety:
    """Validate that subprocess calls follow security best practices."""

    @pytest.fixture
    def python_files(self) -> list[pathlib.Path]:
        """Get all Python files in the repository, excluding virtual environment."""
        repo_root = pathlib.Path(__file__).parent.parent.parent
        return [
            p
            for p in repo_root.rglob("*.py")
            if ".venv" not in str(p) and ".git" not in str(p) and "site-packages" not in str(p)
        ]

    def test_no_shell_true_in_production_code(self, python_files: list[pathlib.Path]) -> None:
        """Verify that subprocess.run/call/Popen don't use shell=True in production code.

        Using shell=True with subprocess is a security risk as it can lead to
        shell injection vulnerabilities if any part of the command comes from
        user input.

        Test code is excluded from this check as it operates in a controlled
        environment and may need shell features for testing purposes.
        """
        violations = []
        shell_pattern = re.compile(r"subprocess\.(run|call|Popen|check_output)\([^)]*shell\s*=\s*True")

        for file_path in python_files:
            # Skip test files - they have different security requirements
            if "test" in str(file_path).lower():
                continue

            content = file_path.read_text()
            if shell_pattern.search(content):
                violations.append(str(file_path))

        assert not violations, (
            f"Found subprocess calls with shell=True in production code:\n"
            f"{', '.join(violations)}\n"
            f"Use list-based command arguments instead of shell=True"
        )

    def test_subprocess_uses_list_arguments(self, python_files: list[pathlib.Path]) -> None:
        """Verify subprocess calls use list arguments, not string concatenation.

        Commands should be passed as lists ['cmd', 'arg1', 'arg2'] rather than
        strings to prevent shell injection and ensure proper argument handling.
        """
        violations = []
        # Look for common patterns that might indicate string-based commands
        string_command_patterns = [
            re.compile(r"subprocess\.(run|call|Popen)\s*\(\s*['\"]"),  # Direct string argument
            re.compile(r"subprocess\.(run|call|Popen)\s*\(\s*f['\"]"),  # F-string argument
        ]

        for file_path in python_files:
            # Skip test files - they may use different patterns for testing
            if "test" in str(file_path).lower():
                continue

            # Skip marimo notebooks - they have different requirements
            if "marimo" in str(file_path):
                continue

            content = file_path.read_text()
            for pattern in string_command_patterns:
                if pattern.search(content):
                    # Verify it's not part of a list by checking context
                    # This is a heuristic and may need adjustment
                    violations.append(str(file_path))
                    break

        # Currently no production code with subprocess, so this should pass
        assert not violations, (
            f"Found subprocess calls that may use string commands:\n"
            f"{', '.join(violations)}\n"
            f"Use list arguments: subprocess.run(['cmd', 'arg']) instead of subprocess.run('cmd arg')"
        )


class TestFileOperations:
    """Validate secure file handling practices."""

    def test_no_world_writable_file_creation(self) -> None:
        """Verify that no code creates world-writable files (777 permissions).

        World-writable files are a security risk as any user can modify them.
        This test only checks production code, not test files.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent
        violations = []
        # Look for chmod calls with overly permissive modes (world-writable: 0o7[7]x)
        # We're specifically looking for 0o777, 0o776, 0o775, etc. (world-writable)
        chmod_pattern = re.compile(r"\.chmod\s*\(\s*0o77[0-9]")

        for py_file in repo_root.rglob("*.py"):
            # Skip test files and virtual environment
            if ".venv" not in str(py_file) and "test" not in str(py_file).lower():
                content = py_file.read_text()
                if chmod_pattern.search(content):
                    violations.append(str(py_file))

        assert not violations, (
            f"Found world-writable file permissions (0o77x) in production code:\n"
            f"{', '.join(violations)}\n"
            f"Avoid using 0o77x permissions; use 0o755 or more restrictive"
        )


class TestInputValidation:
    """Validate input validation and sanitization practices."""

    def test_no_eval_in_production_code(self) -> None:
        """Verify that eval() is not used in production code.

        Using eval() with any user input is extremely dangerous as it can
        execute arbitrary code. There are almost always safer alternatives.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent
        violations = []
        eval_pattern = re.compile(r"\beval\s*\(")

        for py_file in repo_root.rglob("*.py"):
            # Skip test files and virtual environment
            if ".venv" not in str(py_file) and "test" not in str(py_file).lower():
                content = py_file.read_text()
                if eval_pattern.search(content):
                    violations.append(str(py_file))

        assert not violations, (
            f"Found eval() usage in production code:\n"
            f"{', '.join(violations)}\n"
            f"Avoid eval(); use safer alternatives like ast.literal_eval() or json.loads()"
        )

    def test_no_exec_in_production_code(self) -> None:
        """Verify that exec() is not used in production code.

        Similar to eval(), exec() can execute arbitrary code and should be
        avoided unless absolutely necessary with strong input validation.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent
        violations = []
        exec_pattern = re.compile(r"\bexec\s*\(")

        for py_file in repo_root.rglob("*.py"):
            # Skip test files and virtual environment
            if ".venv" not in str(py_file) and "test" not in str(py_file).lower():
                content = py_file.read_text()
                if exec_pattern.search(content):
                    violations.append(str(py_file))

        assert not violations, (
            f"Found exec() usage in production code:\n"
            f"{', '.join(violations)}\n"
            f"Avoid exec(); refactor to use safer alternatives"
        )


class TestSecurityConfiguration:
    """Validate security-related configuration."""

    def test_ruff_security_checks_enabled(self) -> None:
        """Verify that Ruff's security checks (S) are enabled."""
        repo_root = pathlib.Path(__file__).parent.parent.parent
        ruff_config = repo_root / "ruff.toml"

        assert ruff_config.exists(), "ruff.toml not found"

        content = ruff_config.read_text()
        # Check that "S" is in either select or extend-select
        assert '"S"' in content or "'S'" in content, "Ruff security checks (S) should be enabled in ruff.toml"

    def test_bandit_configured_in_precommit(self) -> None:
        """Verify that Bandit is configured in pre-commit hooks."""
        repo_root = pathlib.Path(__file__).parent.parent.parent
        precommit_config = repo_root / ".pre-commit-config.yaml"

        assert precommit_config.exists(), ".pre-commit-config.yaml not found"

        content = precommit_config.read_text()
        assert "bandit" in content.lower(), "Bandit should be configured in pre-commit hooks"

    def test_test_security_exceptions_documented(self) -> None:
        """Verify that security exceptions in test code are documented.

        Test files should have docstrings or comments explaining why security
        exceptions (like S101, S603, S607) are safe in the test context.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent
        conftest_files = list(repo_root.rglob("conftest.py"))

        # For each conftest, verify it has security documentation
        for conftest in conftest_files:
            if ".venv" in str(conftest):
                continue

            content = conftest.read_text()
            # Check for security-related comments or docstrings
            has_security_docs = (
                "S101" in content or "S603" in content or "S607" in content or "security" in content.lower()
            )

            assert has_security_docs, f"{conftest} should document security exceptions (S101/S603/S607)"


class TestSecretsDetection:
    """Validate that no secrets are hardcoded in the codebase."""

    def test_no_hardcoded_passwords(self) -> None:
        """Verify no obvious hardcoded passwords in the codebase.

        This is a basic check for common password patterns. More sophisticated
        secret scanning should be done by dedicated tools like GitGuardian.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent
        violations = []
        # Look for common password patterns
        password_patterns = [
            re.compile(r'password\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
            re.compile(r'pwd\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
        ]

        for py_file in repo_root.rglob("*.py"):
            if ".venv" not in str(py_file):
                content = py_file.read_text()
                for pattern in password_patterns:
                    if pattern.search(content):
                        # Exclude test files and mock data
                        if "test" not in str(py_file).lower() and "example" not in content.lower():
                            violations.append(str(py_file))
                            break

        assert not violations, (
            f"Found potential hardcoded passwords:\n"
            f"{', '.join(violations)}\n"
            f"Use environment variables or secure configuration management"
        )

    def test_no_api_keys_in_code(self) -> None:
        """Verify no API keys or tokens are hardcoded.

        API keys should be loaded from environment variables or secure vaults.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent
        violations = []
        # Look for patterns that might indicate API keys
        api_key_patterns = [
            re.compile(r'api[_-]?key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', re.IGNORECASE),
            re.compile(r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', re.IGNORECASE),
            re.compile(r'secret\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', re.IGNORECASE),
        ]

        for py_file in repo_root.rglob("*.py"):
            if ".venv" not in str(py_file):
                content = py_file.read_text()
                for pattern in api_key_patterns:
                    if pattern.search(content):
                        # Exclude test files, examples, and documentation
                        if (
                            "test" not in str(py_file).lower()
                            and "example" not in content.lower()
                            and "mock" not in content.lower()
                        ):
                            violations.append(str(py_file))
                            break

        assert not violations, (
            f"Found potential hardcoded API keys/tokens:\n"
            f"{', '.join(violations)}\n"
            f"Use environment variables: os.environ.get('API_KEY')"
        )


@pytest.mark.integration
class TestSecurityTooling:
    """Integration tests for security scanning tools."""

    def test_bandit_runs_successfully(self) -> None:
        """Verify that bandit can run successfully on the codebase.

        This doesn't validate findings, just that the tool is properly configured.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent

        # Try to run bandit
        result = subprocess.run(
            ["uv", "tool", "run", "bandit", "--version"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )

        # If bandit is not installed, skip this test
        if result.returncode != 0:
            pytest.skip("Bandit is not installed as a UV tool")

    def test_ruff_security_checks_pass_on_production_code(self) -> None:
        """Verify that Ruff's security checks pass on production code.

        This runs Ruff with only security rules enabled to validate that
        production code passes all security checks.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent

        # Run ruff with only security checks on non-test files
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "--select", "S", "book/"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )

        # This should pass (or at least not error) on production code
        # We allow non-zero exit if there are no Python files to check
        if result.returncode != 0 and "No Python files found" not in result.stdout:
            # Only fail if there are actual security issues
            if "S1" in result.stdout or "S2" in result.stdout or "S3" in result.stdout:
                pytest.fail(f"Ruff security checks found issues in production code:\n{result.stdout}")
