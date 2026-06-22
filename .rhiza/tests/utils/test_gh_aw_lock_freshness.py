"""Unit tests for gh_aw_lock_freshness.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_MD = "---\non: {}\n---\n\n# Title\n\nBody text here.\n"


def _load_module(root: Path) -> ModuleType:
    """Import the repo's gh_aw_lock_freshness.py utility as a standalone module."""
    module_path = root / ".rhiza" / "utils" / "gh_aw_lock_freshness.py"
    spec = importlib.util.spec_from_file_location("gh_aw_lock_freshness", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["gh_aw_lock_freshness"] = module
    spec.loader.exec_module(module)
    return module


def _write_workflow(workflows: Path, name: str, md_text: str, body_hash: str | None) -> None:
    """Write a .md source and (optionally) a matching .lock.yml stub into a dir."""
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / f"{name}.md").write_text(md_text)
    if body_hash is not None:
        (workflows / f"{name}.lock.yml").write_text(f'# gh-aw-metadata: {{"body_hash":"{body_hash}"}}\njobs: {{}}\n')


def test_source_body_hash_ignores_frontmatter(root: Path) -> None:
    """The body hash depends only on the markdown body, not the frontmatter."""
    module = _load_module(root)
    a = module.source_body_hash("---\non: {}\n---\n\nSame body.\n")
    b = module.source_body_hash("---\non: {push: {}}\n---\nSame body.")
    assert a is not None
    assert a == b


def test_source_body_hash_returns_none_without_frontmatter(root: Path) -> None:
    """Markdown without a frontmatter fence yields no body hash."""
    module = _load_module(root)
    assert module.source_body_hash("# Just a heading\n") is None


def test_embedded_body_hash_reads_metadata_header(root: Path) -> None:
    """The embedded hash is parsed from the gh-aw-metadata header line."""
    module = _load_module(root)
    lock = '# gh-aw-metadata: {"schema_version":"v4","body_hash":"abc123"}\njobs: {}\n'
    assert module.embedded_body_hash(lock) == "abc123"


def test_embedded_body_hash_returns_none_when_absent(root: Path) -> None:
    """A lock file without a metadata header yields no embedded hash."""
    module = _load_module(root)
    assert module.embedded_body_hash("jobs: {}\n") is None


def test_check_freshness_passes_for_matching_hash(root: Path, tmp_path: Path) -> None:
    """A source whose body matches its lock's embedded hash is reported fresh."""
    module = _load_module(root)
    workflows = tmp_path / ".github" / "workflows"
    _write_workflow(workflows, "demo", _MD, module.source_body_hash(_MD))
    assert module.check_freshness(tmp_path) == []


def test_check_freshness_flags_stale_body(root: Path, tmp_path: Path) -> None:
    """A source edited since its last compile is flagged as stale."""
    module = _load_module(root)
    workflows = tmp_path / ".github" / "workflows"
    _write_workflow(workflows, "demo", _MD, "0" * 64)
    problems = module.check_freshness(tmp_path)
    assert len(problems) == 1
    assert "demo.md" in problems[0]


def test_check_freshness_flags_missing_lock(root: Path, tmp_path: Path) -> None:
    """A source without any compiled lock file is flagged."""
    module = _load_module(root)
    workflows = tmp_path / ".github" / "workflows"
    _write_workflow(workflows, "demo", _MD, body_hash=None)
    problems = module.check_freshness(tmp_path)
    assert len(problems) == 1
    assert "demo.lock.yml" in problems[0]


def test_check_freshness_empty_without_sources(root: Path, tmp_path: Path) -> None:
    """A repo with no agentic sources reports no problems (graceful no-op)."""
    module = _load_module(root)
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    assert module.check_freshness(tmp_path) == []


def test_repo_lock_files_are_fresh(root: Path) -> None:
    """The committed lock files in this repository must be up to date."""
    module = _load_module(root)
    assert module.check_freshness(root) == []


def test_main_returns_one_and_reports_fix_on_stale(root: Path, tmp_path: Path, capsys) -> None:
    """main() exits non-zero and prints the fix command when a lock is stale."""
    module = _load_module(root)
    workflows = tmp_path / ".github" / "workflows"
    _write_workflow(workflows, "demo", _MD, "0" * 64)
    assert module.main([str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "stale" in out.lower()
    assert "make gh-aw-compile" in out


def test_main_returns_zero_when_fresh(root: Path, tmp_path: Path, capsys) -> None:
    """main() exits zero and prints an OK message when everything is fresh."""
    module = _load_module(root)
    workflows = tmp_path / ".github" / "workflows"
    _write_workflow(workflows, "demo", _MD, module.source_body_hash(_MD))
    assert module.main([str(tmp_path)]) == 0
    assert "[OK]" in capsys.readouterr().out
