"""Unit tests for link_dogfood.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_module(root: Path):
    """Load ``utils/link_dogfood.py`` as an importable module."""
    module_path = root / "utils" / "link_dogfood.py"
    spec = importlib.util.spec_from_file_location("link_dogfood", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_link_one_keeps_original_file_when_temp_symlink_creation_fails(root, tmp_path, monkeypatch) -> None:
    """A failed temporary symlink creation should not delete the original file."""
    module = _load_module(root)
    rel = "file.txt"
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    link = tmp_path / rel
    link.write_text("original", encoding="utf-8")

    def _raise_symlink(self: Path, target: str, target_is_directory: bool = False) -> None:
        """Stand-in for ``Path.symlink_to`` that always fails."""
        raise OSError("boom")

    monkeypatch.setattr(Path, "symlink_to", _raise_symlink)

    with pytest.raises(OSError, match="boom"):
        module._link_one(tmp_path, rel, source)

    assert link.exists()
    assert not link.is_symlink()
    assert link.read_text(encoding="utf-8") == "original"


def test_classify_dogfood_skips_without_reading_mismatched_sizes(root, tmp_path, monkeypatch) -> None:
    """Owners with non-matching sizes should be skipped before byte reads."""
    module = _load_module(root)
    rel = "file.txt"
    root_file = tmp_path / rel
    root_file.write_text("abc", encoding="utf-8")
    owner = tmp_path / "owner.txt"
    owner.write_text("different-size", encoding="utf-8")
    index = {rel: [owner]}

    def _fail_read_bytes(self: Path) -> bytes:
        """Stand-in for ``Path.read_bytes`` that must never be invoked here."""
        msg = "read_bytes should not be called for mismatched file sizes"
        raise AssertionError(msg)

    monkeypatch.setattr(Path, "read_bytes", _fail_read_bytes)

    assert module._classify_dogfood(tmp_path, rel, index) == ("skip", None)


def test_relink_check_mode_reports_pending_and_exits_nonzero(root, tmp_path) -> None:
    """Check mode should accumulate pending links and exit non-zero when any are pending."""
    module = _load_module(root)

    rel_pending = "pending.txt"
    rel_unchanged = "unchanged.txt"

    # dst_pending is a real file (not a symlink) with the same content as src_pending —
    # it looks like an unlinked dogfood copy and should be flagged as pending.
    src_pending = tmp_path / "src_pending.txt"
    src_pending.write_text("pending-source", encoding="utf-8")
    dst_pending = tmp_path / rel_pending
    dst_pending.write_text("pending-source", encoding="utf-8")

    # dst_unchanged is already a correct *relative* symlink pointing at src_unchanged —
    # _link_is_current requires a relative target, so symlink_to must receive a str.
    src_unchanged = tmp_path / "src_unchanged.txt"
    src_unchanged.write_text("unchanged-source", encoding="utf-8")
    dst_unchanged = tmp_path / rel_unchanged
    dst_unchanged.symlink_to("src_unchanged.txt")  # relative symlink

    index = {
        rel_pending: [src_pending],
        rel_unchanged: [src_unchanged],
    }

    rc = module.relink(tmp_path, index, check=True)
    assert rc != 0
