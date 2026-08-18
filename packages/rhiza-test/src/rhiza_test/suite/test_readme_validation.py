"""Tests for executable Python examples in the README.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

This module extracts Python code and expected result blocks from README.md,
executes the code, and verifies the output matches the documented result.

The language-neutral half — that the README exists, and that its ``bash`` fences
parse — moved to ``core``'s ``test_readme.py`` in #1472, so a Rust or Go project gets it
too. What stays here only means something where the project itself is Python: running a
``python`` fence and diffing it against the following ``result`` block.

The fence flags live in :mod:`rhiza_test._fences`, shared with that module. They were
duplicated while the suite was copied per-bundle; packaging gave them one home.
"""

import re
import subprocess  # nosec B404
import sys

import pytest
from rhiza_test._fences import SKIP_FLAG, should_skip

# Regex for Python code blocks — captures optional flags (e.g. "+RHIZA_SKIP") and the code body.
CODE_BLOCK = re.compile(r"```python([^\n]*)\n(.*?)```", re.DOTALL)

RESULT = re.compile(r"```result\n(.*?)```", re.DOTALL)


def test_readme_runs(logger, root):
    """Execute README code blocks and compare output to documented results."""
    readme = root / "README.md"
    logger.info("Reading README from %s", readme)
    readme_text = readme.read_text(encoding="utf-8")
    all_code_blocks = CODE_BLOCK.findall(readme_text)
    result_blocks = RESULT.findall(readme_text)

    code_blocks = []
    for i, (flags, code) in enumerate(all_code_blocks):
        if should_skip(flags):
            logger.info("Skipping Python code block %d (%s flag)", i, SKIP_FLAG)
        else:
            code_blocks.append(code)

    logger.info(
        "Found %d code block(s) (%d skipped) and %d result block(s) in README",
        len(all_code_blocks),
        len(all_code_blocks) - len(code_blocks),
        len(result_blocks),
    )

    code = "".join(code_blocks)  # merged code
    expected = "".join(result_blocks)  # merged results

    # Trust boundary: we execute Python snippets sourced from README.md in this repo.
    # The README is part of the trusted repository content and reviewed in PRs.
    logger.debug("Executing README code via %s -c ...", sys.executable)
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=root)  # nosec

    stdout = result.stdout
    logger.debug("Execution finished with return code %d", result.returncode)
    if result.stderr:
        logger.debug("Stderr from README code:\n%s", result.stderr)
    logger.debug("Stdout from README code:\n%s", stdout)

    assert result.returncode == 0, f"README code exited with {result.returncode}. Stderr:\n{result.stderr}"
    logger.info("README code executed successfully; comparing output to expected result")
    assert stdout.strip() == expected.strip()
    logger.info("README code output matches expected result")


class TestReadmeTestEdgeCases:
    """Edge cases for README code block testing."""

    def test_readme_code_is_syntactically_valid(self, root):
        """Python code blocks in README should be syntactically valid (skipped blocks are excluded)."""
        readme = root / "README.md"
        content = readme.read_text(encoding="utf-8")
        all_code_blocks = CODE_BLOCK.findall(content)

        for i, (flags, code) in enumerate(all_code_blocks):
            if should_skip(flags):
                continue
            try:
                compile(code, f"<readme_block_{i}>", "exec")
            except SyntaxError as e:
                pytest.fail(f"Code block {i} has syntax error: {e}")


class TestSkipFlag:
    """Tests for the +RHIZA_SKIP flag as it applies to Python fences."""

    # should_skip's own behaviour is covered once, in test_readme.py, next to the
    # language-neutral half. What is specific here is that a flagged *python* fence
    # is kept out of the list this module executes.

    def test_python_block_with_skip_flag_is_excluded(self, tmp_path):
        """A ```python +RHIZA_SKIP block should not appear in the list of blocks to execute."""
        readme = tmp_path / "README.md"
        readme.write_text(
            '```python +RHIZA_SKIP\nraise RuntimeError("should not run")\n```\n'
            "```python\nprint('hello')\n```\n"
            "```result\nhello\n```\n",
            encoding="utf-8",
        )
        content = readme.read_text(encoding="utf-8")
        all_blocks = CODE_BLOCK.findall(content)
        assert len(all_blocks) == 2
        executed = [code for flags, code in all_blocks if not should_skip(flags)]
        assert len(executed) == 1
        assert "raise RuntimeError" not in executed[0]
