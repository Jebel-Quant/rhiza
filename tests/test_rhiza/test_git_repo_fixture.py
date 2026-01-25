"""Tests for the git_repo pytest fixture that creates a mock Git repository.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

This module validates the temporary repository structure, git initialization,
mocked tool executables, environment variables, and basic git configuration the
fixture is expected to provide for integration-style tests.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import MOCK_UV_SCRIPT

# Get absolute path for git to avoid S607 warnings
GIT = shutil.which("git") or "/usr/bin/git"


class TestGitRepoFixture:
    """Tests for the git_repo fixture that sets up a mock git repository.

    Uses a class-scoped shared repo since all tests are read-only inspections.
    """

    @pytest.fixture(scope="class")
    def _shared_git_repo(self, request, root, tmp_path_factory):
        """Create a git repo once for the entire test class (read-only tests only)."""
        tmp_path = tmp_path_factory.mktemp("git_repo")
        remote_dir = tmp_path / "remote.git"
        local_dir = tmp_path / "local"

        # 1. Create bare remote
        remote_dir.mkdir()
        subprocess.run([GIT, "init", "--bare", str(remote_dir)], check=True, capture_output=True)
        subprocess.run([GIT, "symbolic-ref", "HEAD", "refs/heads/master"], cwd=remote_dir, check=True)

        # 2. Clone to local
        subprocess.run([GIT, "clone", str(remote_dir), str(local_dir)], check=True, capture_output=True)

        # Ensure local default branch is 'master'
        subprocess.run([GIT, "checkout", "-b", "master"], cwd=local_dir, check=True, capture_output=True)

        # Create pyproject.toml
        (local_dir / "pyproject.toml").write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')

        # Create dummy uv.lock
        (local_dir / "uv.lock").write_text("")

        # Create bin/uv mock
        bin_dir = local_dir / "bin"
        bin_dir.mkdir()
        uv_path = bin_dir / "uv"
        uv_path.write_text(MOCK_UV_SCRIPT)
        uv_path.chmod(0o755)

        # Copy scripts and core Rhiza Makefiles
        shutil.copytree(root / ".rhiza", local_dir / ".rhiza")
        shutil.copy(root / "Makefile", local_dir / "Makefile")

        tests_src = root / "tests"
        if tests_src.is_dir():
            shutil.copytree(tests_src, local_dir / "tests", dirs_exist_ok=True)

        book_src = root / "book"
        if book_src.is_dir():
            shutil.copytree(book_src, local_dir / "book", dirs_exist_ok=True)

        # Commit and push initial state
        subprocess.run([GIT, "config", "user.email", "test@example.com"], cwd=local_dir, check=True)
        subprocess.run([GIT, "config", "user.name", "Test User"], cwd=local_dir, check=True)
        subprocess.run([GIT, "add", "."], cwd=local_dir, check=True)
        subprocess.run([GIT, "commit", "-m", "Initial commit"], cwd=local_dir, check=True, capture_output=True)
        subprocess.run([GIT, "push", "origin", "master"], cwd=local_dir, check=True, capture_output=True)

        return local_dir

    @pytest.fixture
    def git_repo(self, _shared_git_repo, monkeypatch):
        """Function-scoped fixture that reuses shared repo but sets up environment per-test."""
        local_dir = _shared_git_repo
        bin_dir = local_dir / "bin"

        # Use monkeypatch for per-test chdir and PATH modification
        monkeypatch.chdir(local_dir)
        monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")

        return local_dir

    def test_git_repo_creates_temporary_directory(self, git_repo):
        """Git repo fixture should create a temporary directory."""
        assert git_repo.exists()
        assert git_repo.is_dir()

    def test_git_repo_contains_pyproject_toml(self, git_repo):
        """Git repo should contain a pyproject.toml file."""
        pyproject = git_repo / "pyproject.toml"
        assert pyproject.exists()
        content = pyproject.read_text()
        assert 'name = "test-project"' in content
        assert 'version = "0.1.0"' in content

    def test_git_repo_contains_uv_lock(self, git_repo):
        """Git repo should contain a uv.lock file."""
        assert (git_repo / "uv.lock").exists()

    def test_git_repo_has_bin_directory_with_mocks(self, git_repo):
        """Git repo should have bin directory with mock tools."""
        bin_dir = git_repo / "bin"
        assert bin_dir.exists()
        assert (bin_dir / "uv").exists()

    def test_git_repo_mock_tools_are_executable(self, git_repo):
        """Mock tools should be executable."""
        for tool in ["uv"]:
            tool_path = git_repo / "bin" / tool
            assert os.access(tool_path, os.X_OK), f"{tool} is not executable"

    def test_git_repo_has_github_scripts_directory(self, git_repo):
        """Git repo should have .github/rhiza/scripts directory."""
        scripts_dir = git_repo / ".rhiza" / "scripts"
        assert scripts_dir.exists()
        assert (scripts_dir / "release.sh").exists()

    def test_git_repo_scripts_are_executable(self, git_repo):
        """GitHub scripts should be executable."""
        for script in ["release.sh"]:
            script_path = git_repo / ".rhiza" / "scripts" / script
            assert os.access(script_path, os.X_OK), f"{script} is not executable"

    def test_git_repo_is_initialized(self, git_repo):
        """Git repo should be properly initialized."""
        result = subprocess.run(
            [GIT, "rev-parse", "--git-dir"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert ".git" in result.stdout

    def test_git_repo_has_master_branch(self, git_repo):
        """Git repo should be on master branch."""
        result = subprocess.run(
            [GIT, "branch", "--show-current"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "master"

    def test_git_repo_has_initial_commit(self, git_repo):
        """Git repo should have an initial commit."""
        result = subprocess.run(
            [GIT, "log", "--oneline"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Initial commit" in result.stdout

    def test_git_repo_has_remote_configured(self, git_repo):
        """Git repo should have origin remote configured."""
        result = subprocess.run(
            [GIT, "remote", "-v"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "origin" in result.stdout

    def test_git_repo_user_config_is_set(self, git_repo):
        """Git repo should have user.email and user.name configured."""
        email = subprocess.check_output(
            [GIT, "config", "user.email"],
            cwd=git_repo,
            text=True,
        ).strip()
        name = subprocess.check_output(
            [GIT, "config", "user.name"],
            cwd=git_repo,
            text=True,
        ).strip()
        assert email == "test@example.com"
        assert name == "Test User"

    def test_git_repo_working_tree_is_clean(self, git_repo):
        """Git repo should start with a clean working tree."""
        result = subprocess.run(
            [GIT, "status", "--porcelain"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_git_repo_changes_current_directory(self, git_repo):
        """Git repo fixture should change to the temporary directory."""
        current_dir = Path.cwd()
        assert current_dir == git_repo

    def test_git_repo_modifies_path_environment(self, git_repo):
        """Git repo fixture should prepend bin directory to PATH."""
        path_env = os.environ.get("PATH", "")
        bin_dir = str(git_repo / "bin")
        assert bin_dir in path_env
        assert path_env.startswith(bin_dir)
