"""Tests for shell completion scripts.

This file and its associated tests flow down via a SYNC action from the
jebel-quant/rhiza repository (https://github.com/jebel-quant/rhiza).

Validates that the shell completion scripts for bash and zsh:
- Exist in the expected location
- Have non-trivial content (not empty stubs)
- Reference key make targets that all Rhiza-based projects expose
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def completions_dir(root: Path) -> Path:
    """Return the path to the shell completions directory."""
    d = root / ".rhiza" / "completions"
    if not d.is_dir():
        pytest.skip(".rhiza/completions directory not found — completions bundle not synced")
    return d


class TestBashCompletion:
    """Tests for the bash shell completion script."""

    def test_bash_completion_exists(self, completions_dir: Path) -> None:
        """rhiza-completion.bash must exist in the completions directory."""
        bash_comp = completions_dir / "rhiza-completion.bash"
        assert bash_comp.exists(), f"rhiza-completion.bash not found in {completions_dir}"

    def test_bash_completion_is_non_empty(self, completions_dir: Path) -> None:
        """rhiza-completion.bash must have at least 5 lines of content."""
        bash_comp = completions_dir / "rhiza-completion.bash"
        if not bash_comp.exists():
            pytest.skip("rhiza-completion.bash not found")
        lines = [ln for ln in bash_comp.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) >= 5, f"bash completion has too few non-blank lines: {len(lines)}"

    def test_bash_completion_invokes_make_for_target_discovery(self, completions_dir: Path) -> None:
        """Bash completion must invoke make to dynamically discover targets."""
        bash_comp = completions_dir / "rhiza-completion.bash"
        if not bash_comp.exists():
            pytest.skip("rhiza-completion.bash not found")
        content = bash_comp.read_text(encoding="utf-8")
        assert "make" in content, "bash completion should invoke 'make' to discover targets dynamically"

    def test_bash_completion_registers_with_complete_builtin(self, completions_dir: Path) -> None:
        """Bash completion must register via the 'complete' builtin for shell integration."""
        bash_comp = completions_dir / "rhiza-completion.bash"
        if not bash_comp.exists():
            pytest.skip("rhiza-completion.bash not found")
        content = bash_comp.read_text(encoding="utf-8")
        assert "complete " in content, "bash completion must call 'complete' to register itself with the shell"

    def test_bash_completion_has_shebang_or_function(self, completions_dir: Path) -> None:
        """Bash completion should use a bash function or shebang for proper shell integration."""
        bash_comp = completions_dir / "rhiza-completion.bash"
        if not bash_comp.exists():
            pytest.skip("rhiza-completion.bash not found")
        content = bash_comp.read_text(encoding="utf-8")
        has_shebang = content.startswith("#!")
        has_function = "function " in content or "() {" in content or "complete " in content
        assert has_shebang or has_function, (
            "bash completion should have a shebang line, function definition, or 'complete' call"
        )


class TestZshCompletion:
    """Tests for the zsh shell completion script."""

    def test_zsh_completion_exists(self, completions_dir: Path) -> None:
        """rhiza-completion.zsh must exist in the completions directory."""
        zsh_comp = completions_dir / "rhiza-completion.zsh"
        assert zsh_comp.exists(), f"rhiza-completion.zsh not found in {completions_dir}"

    def test_zsh_completion_is_non_empty(self, completions_dir: Path) -> None:
        """rhiza-completion.zsh must have at least 5 lines of content."""
        zsh_comp = completions_dir / "rhiza-completion.zsh"
        if not zsh_comp.exists():
            pytest.skip("rhiza-completion.zsh not found")
        lines = [ln for ln in zsh_comp.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) >= 5, f"zsh completion has too few non-blank lines: {len(lines)}"

    def test_zsh_completion_invokes_make_for_target_discovery(self, completions_dir: Path) -> None:
        """Zsh completion must invoke make to dynamically discover targets."""
        zsh_comp = completions_dir / "rhiza-completion.zsh"
        if not zsh_comp.exists():
            pytest.skip("rhiza-completion.zsh not found")
        content = zsh_comp.read_text(encoding="utf-8")
        assert "make" in content, "zsh completion should invoke 'make' to discover targets dynamically"

    def test_zsh_completion_has_compdef_or_compadd(self, completions_dir: Path) -> None:
        """Zsh completion must use zsh completion primitives (compdef or compadd)."""
        zsh_comp = completions_dir / "rhiza-completion.zsh"
        if not zsh_comp.exists():
            pytest.skip("rhiza-completion.zsh not found")
        content = zsh_comp.read_text(encoding="utf-8")
        has_zsh_primitives = "compdef" in content or "compadd" in content or "_arguments" in content
        assert has_zsh_primitives, (
            "zsh completion should use zsh completion primitives (compdef, compadd, or _arguments)"
        )


class TestCompletionsReadme:
    """The completions directory must have a README explaining installation."""

    def test_readme_exists(self, completions_dir: Path) -> None:
        """A README must be present in the completions directory."""
        readme = completions_dir / "README.md"
        assert readme.exists(), "README.md not found in .rhiza/completions/"

    def test_readme_mentions_source_or_install(self, completions_dir: Path) -> None:
        """README should explain how to source or install the completion scripts."""
        readme = completions_dir / "README.md"
        if not readme.exists():
            pytest.skip("README.md not found in completions dir")
        content = readme.read_text(encoding="utf-8").lower()
        assert any(w in content for w in ("source", "install", "load", "add")), (
            "completions README should explain how to source/install the scripts"
        )
