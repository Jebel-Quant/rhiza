"""Tests for the README that hold whatever the project is written in.

This file and its associated tests flow down via a SYNC action from the
jebel-quant/rhiza repository (https://github.com/jebel-quant/rhiza).

Owned by ``core`` because none of it is language-specific: every synced README documents
its gates in ``bash`` fences — ``make install``, ``make test``, ``make all`` — and a
fence with a syntax error is broken the same way in a Rust, Go or Python project. Before
this split (#1472) all of it lived in the ``tests`` bundle, which requires
``python-core``, so a Rust or Go repo had no README coverage at all.

The Python-block half stays behind in ``tests`` as ``test_readme_validation.py``: it
executes ``python`` fences and diffs them against a ``result`` block, which only means
something where the project *is* Python.

The fence flags themselves live in :mod:`rhiza_test._fences`, shared with
``test_readme_validation.py``. They were duplicated across the two modules while the
suite was copied per-bundle; packaging gave them one home.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404
from pathlib import Path

import pytest
from rhiza_test._fences import SKIP_FLAG, should_skip

# Bash code blocks — captures optional flags (e.g. "+RHIZA_SKIP") and the code body.
BASH_BLOCK = re.compile(r"```bash([^\n]*)\n(.*?)```", re.DOTALL)

# Bash executable used for syntax checking; `bash -n` parses without executing.
BASH = "bash"

# Box-drawing characters mean the fence is a directory tree, not runnable shell.
_TREE_MARKERS = ("├──", "└──", "│")


class TestReadmeExists:
    """The README has to be there and be readable before anything else applies."""

    def test_readme_file_exists_at_root(self, root: Path) -> None:
        """README.md should exist at repository root."""
        readme = root / "README.md"
        assert readme.exists(), "README.md not found at project root"
        assert readme.is_file(), "README.md is not a regular file"

    def test_readme_is_readable(self, root: Path) -> None:
        """README.md should be readable with UTF-8 encoding and non-empty."""
        content = (root / "README.md").read_text(encoding="utf-8")
        assert content.strip(), "README.md is empty"


class TestReadmeBashFragments:
    """Bash fences must parse, in any language's project.

    Only ``bash -n`` — the blocks are parsed, never executed. A README's shell examples
    are usually destructive-adjacent (`make clean`, `git push`) and running them is not
    what this is for; a fence that cannot even parse is a documentation bug regardless.
    """

    def test_bash_blocks_basic_syntax(self, root: Path, logger) -> None:
        """Every non-skipped bash block should parse under `bash -n`."""
        content = (root / "README.md").read_text(encoding="utf-8")
        bash_blocks = BASH_BLOCK.findall(content)

        logger.info("Found %d bash code block(s) in README", len(bash_blocks))

        for i, (flags, code) in enumerate(bash_blocks):
            if should_skip(flags):
                logger.info("Skipping bash block %d (%s flag)", i, SKIP_FLAG)
                continue

            if any(marker in code for marker in _TREE_MARKERS):
                logger.info("Skipping bash block %d (directory tree representation)", i)
                continue

            # A block that is only comments has nothing to parse and no way to be wrong.
            lines = [line.strip() for line in code.split("\n") if line.strip()]
            if not [line for line in lines if not line.startswith("#")]:
                logger.info("Skipping bash block %d (only comments)", i)
                continue

            logger.debug("Checking bash block %d:\n%s", i, code)

            result = subprocess.run(  # nosec B603 B607 - `bash -n` parses without executing
                [BASH, "-n"],
                input=code,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                pytest.fail(f"Bash block {i} has syntax errors:\nCode:\n{code}\nError:\n{result.stderr}")


class TestSkipFlag:
    """Tests for the +RHIZA_SKIP flag that excludes an individual fence."""

    def test_should_skip_returns_true_for_skip_flag(self) -> None:
        """+RHIZA_SKIP in flags string should cause _should_skip to return True."""
        assert should_skip(" +RHIZA_SKIP") is True
        assert should_skip("+RHIZA_SKIP") is True
        assert should_skip(" +RHIZA_SKIP other-flag") is True

    def test_should_skip_returns_false_without_flag(self) -> None:
        """Absence of +RHIZA_SKIP should cause _should_skip to return False."""
        assert should_skip("") is False
        assert should_skip(" ") is False
        assert should_skip("other-flag") is False

    def test_bash_block_with_skip_flag_is_excluded(self, tmp_path: Path) -> None:
        """A ```bash +RHIZA_SKIP block should not be syntax-checked."""
        readme = tmp_path / "README.md"
        readme.write_text(
            "```bash +RHIZA_SKIP\nnot-valid-bash @@@@\n```\n```bash\necho hello\n```\n",
            encoding="utf-8",
        )
        all_blocks = BASH_BLOCK.findall(readme.read_text(encoding="utf-8"))
        assert len(all_blocks) == 2
        checked = [code for flags, code in all_blocks if not should_skip(flags)]
        assert len(checked) == 1
        assert "not-valid-bash" not in checked[0]
