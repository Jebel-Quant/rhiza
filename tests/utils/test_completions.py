"""Tests for the shell completion scripts in .rhiza/completions/.

Gates two invariants:

1. Both completion scripts are syntactically valid for their target shell
   (bash -n / zsh -n), so a broken edit cannot ship.
2. The bash completion's cache helper behaves correctly: stale when the cache
   file is missing, fresh after writing, stale again after a makefile source
   changes.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - invoking known shells on repo-controlled files
import time
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_COMPLETIONS = _ROOT / ".rhiza" / "completions"


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, capturing output."""
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kwargs)  # nosec B603


class TestCompletionScripts:
    """Syntax and cache behaviour of the shell completion scripts."""

    @pytest.mark.parametrize(
        ("shell", "script"),
        [("bash", "rhiza-completion.bash"), ("zsh", "rhiza-completion.zsh")],
    )
    def test_script_syntax_is_valid(self, shell: str, script: str) -> None:
        """Each completion script must pass its shell's no-exec syntax check."""
        if shutil.which(shell) is None:
            pytest.skip(f"{shell} not available")
        result = _run([shell, "-n", str(_COMPLETIONS / script)])
        assert result.returncode == 0, f"{script} failed {shell} -n: {result.stderr}"

    def test_bash_cache_staleness_lifecycle(self, tmp_path: Path) -> None:
        """The cache helper reports stale on miss, fresh after write, stale after edit."""
        if shutil.which("bash") is None:
            pytest.skip("bash not available")
        (tmp_path / "Makefile").write_text("all:\n\ttrue\n")
        script = f"""
        source "{_COMPLETIONS / "rhiza-completion.bash"}"
        cd "{tmp_path}"
        cache="{tmp_path}/cache-file"
        _rhiza_make_cache_stale "$cache" && echo "miss:stale" || echo "miss:fresh"
        echo targets > "$cache"
        _rhiza_make_cache_stale "$cache" && echo "written:stale" || echo "written:fresh"
        """
        result = _run(["bash", "-c", script])
        assert "miss:stale" in result.stdout
        assert "written:fresh" in result.stdout

        # A makefile edit after the cache write must invalidate it. mtimes are
        # second-granular under macOS bash, so push the Makefile clearly ahead.
        cache = tmp_path / "cache-file"
        cache.write_text("targets\n")
        future = time.time() + 5
        os.utime(tmp_path / "Makefile", (future, future))
        result = _run(
            [
                "bash",
                "-c",
                f'source "{_COMPLETIONS / "rhiza-completion.bash"}"; cd "{tmp_path}"; '
                f'_rhiza_make_cache_stale "{cache}" && echo "edited:stale" || echo "edited:fresh"',
            ],
        )
        assert "edited:stale" in result.stdout
