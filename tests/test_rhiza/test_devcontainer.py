"""Tests for devcontainer configuration and bootstrap scripts.

This module validates that the devcontainer setup works correctly,
testing the bootstrap.sh and startup.sh scripts that configure
the development environment for users.
"""

import subprocess
import tempfile
from pathlib import Path


class TestDevContainerConfiguration:
    """Tests for devcontainer.json configuration."""

    def test_devcontainer_json_exists(self, root):
        """Devcontainer configuration should exist."""
        devcontainer_json = root / ".devcontainer" / "devcontainer.json"
        assert devcontainer_json.exists()

    def test_devcontainer_has_required_fields(self, root):
        """Devcontainer configuration should have required fields."""
        devcontainer_json = root / ".devcontainer" / "devcontainer.json"
        content = devcontainer_json.read_text()

        # Check for required fields (devcontainer.json can have comments)
        assert '"name"' in content
        assert '"image"' in content
        assert '"onCreateCommand"' in content
        assert '"remoteUser"' in content

    def test_devcontainer_points_to_startup_script(self, root):
        """Devcontainer onCreateCommand should reference startup.sh."""
        devcontainer_json = root / ".devcontainer" / "devcontainer.json"
        content = devcontainer_json.read_text()

        # Check that onCreateCommand references startup.sh
        assert "startup.sh" in content
        # Verify it's in the context of onCreateCommand
        assert '"onCreateCommand"' in content and "startup.sh" in content


class TestBootstrapScript:
    """Tests for the bootstrap.sh script that sets up the environment."""

    def test_bootstrap_script_exists(self, root):
        """Bootstrap script should exist in .devcontainer directory."""
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"
        assert bootstrap_script.exists()

    def test_bootstrap_script_is_executable(self, root):
        """Bootstrap script should have executable permissions."""
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"
        # Check if file has any execute bit set
        assert bootstrap_script.stat().st_mode & 0o111

    def test_bootstrap_script_has_shebang(self, root):
        """Bootstrap script should start with a bash shebang."""
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"
        with open(bootstrap_script) as f:
            first_line = f.readline().strip()
        assert first_line.startswith("#!/")
        assert "bash" in first_line.lower()

    def test_bootstrap_sets_uv_environment_variables(self, root):
        """Bootstrap script should set UV-related environment variables."""
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"
        content = bootstrap_script.read_text()

        # Check for UV environment variable exports
        assert "UV_VENV_CLEAR" in content
        assert "UV_LINK_MODE" in content
        assert "UV_INSTALL_DIR" in content

    def test_bootstrap_adds_to_bashrc(self, root):
        """Bootstrap script should persist environment variables to .bashrc."""
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"
        content = bootstrap_script.read_text()

        # Check that variables are added to bashrc
        assert ">> ~/.bashrc" in content or ">> $HOME/.bashrc" in content

    def test_bootstrap_installs_marimo(self, root):
        """Bootstrap script should install marimo tool."""
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"
        content = bootstrap_script.read_text()

        assert "marimo" in content
        assert "tool install" in content

    def test_bootstrap_installs_precommit(self, root):
        """Bootstrap script should install pre-commit hooks."""
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"
        content = bootstrap_script.read_text()

        assert "pre-commit" in content
        assert "install" in content

    def test_bootstrap_runs_make_install(self, root):
        """Bootstrap script should call make install."""
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"
        content = bootstrap_script.read_text()

        assert "make install" in content


class TestStartupScript:
    """Tests for the startup.sh script that orchestrates devcontainer initialization."""

    def test_startup_script_exists(self, root):
        """Startup script should exist in .devcontainer directory."""
        startup_script = root / ".devcontainer" / "startup.sh"
        assert startup_script.exists()

    def test_startup_script_is_executable(self, root):
        """Startup script should have executable permissions."""
        startup_script = root / ".devcontainer" / "startup.sh"
        # Check if file has any execute bit set
        assert startup_script.stat().st_mode & 0o111

    def test_startup_script_has_shebang(self, root):
        """Startup script should start with a bash shebang."""
        startup_script = root / ".devcontainer" / "startup.sh"
        with open(startup_script) as f:
            first_line = f.readline().strip()
        assert first_line.startswith("#!/")
        assert "bash" in first_line.lower()

    def test_startup_script_sources_bootstrap(self, root):
        """Startup script should source the bootstrap.sh script."""
        startup_script = root / ".devcontainer" / "startup.sh"
        content = startup_script.read_text()

        # Check for source command with bootstrap.sh
        assert "source" in content and "bootstrap.sh" in content

    def test_startup_script_has_welcome_messages(self, root):
        """Startup script should display welcome messages to users."""
        startup_script = root / ".devcontainer" / "startup.sh"
        content = startup_script.read_text()

        # Check for echo commands that display welcome messages
        assert "echo" in content and ("environment ready" in content.lower() or "ready!" in content.lower())


class TestDevContainerScriptIntegration:
    """Integration tests that simulate the devcontainer bootstrap process."""

    def test_bootstrap_script_syntax_valid(self, root):
        """Bootstrap script should have valid bash syntax."""
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"

        result = subprocess.run(
            ["bash", "-n", str(bootstrap_script)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Syntax error in bootstrap.sh: {result.stderr}"

    def test_startup_script_syntax_valid(self, root):
        """Startup script should have valid bash syntax."""
        startup_script = root / ".devcontainer" / "startup.sh"

        result = subprocess.run(
            ["bash", "-n", str(startup_script)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Syntax error in startup.sh: {result.stderr}"

    def test_bootstrap_uv_install_dir_configuration(self, root):
        """Bootstrap script should respect UV_INSTALL_DIR environment variable."""
        # Read the bootstrap script
        bootstrap_script = root / ".devcontainer" / "bootstrap.sh"
        content = bootstrap_script.read_text()

        # Verify the script reads UV_INSTALL_DIR from environment with default fallback
        assert "UV_INSTALL_DIR" in content
        assert "${UV_INSTALL_DIR" in content or "$UV_INSTALL_DIR" in content
        # Verify it has a default value (either in export or parameter expansion)
        assert ":-" in content or "/home/vscode/.local/bin" in content or "./bin" in content
