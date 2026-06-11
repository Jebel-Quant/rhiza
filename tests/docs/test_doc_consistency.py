"""Tests that documentation stays consistent with the repository state.

Two gated invariants:

1. Every relative markdown link (and image) resolves to an existing file or
   directory — either in this repository's layout or in the downstream layout
   produced by syncing bundles (each ``bundles/<name>/`` directory maps onto
   the downstream repository root).
2. Every bundle defined in ``.rhiza/template-bundles.yml`` is documented in
   CLAUDE.md, so the bundle overview cannot silently drift as bundles are
   added or renamed.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLES_DIR = _ROOT / "bundles"
_TEMPLATE_BUNDLES = _ROOT / ".rhiza" / "template-bundles.yml"

_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".idea",
    ".ruff_cache",
    ".pytest_cache",
    ".benchmarks",
    "__pycache__",
    "node_modules",
    "_tests",
}

# Link targets that are intentionally unresolvable (e.g. placeholders inside
# document templates that downstream authors are expected to replace).
_PLACEHOLDER_TARGETS = {"XXXX-title.md"}

# Templates that are copied elsewhere before use: deployment-relative file
# path -> directory its links actually resolve from. PRESENTATION.md is
# rendered by Marp from the repository root (see .rhiza/make.d/presentation.mk).
_DEPLOYED_DIR_OVERRIDES = {
    Path("docs/development/PRESENTATION.md"): Path(),
}

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def _markdown_files() -> list[Path]:
    """Return all markdown files in the repository outside excluded directories."""
    return sorted(
        path for path in _ROOT.rglob("*.md") if not _EXCLUDED_DIRS.intersection(path.relative_to(_ROOT).parts)
    )


def _deployment_rel_path(md_file: Path) -> Path:
    """Return the file's path relative to its deployment root.

    Files under bundles/<name>/ are synced to the downstream repository root,
    so their deployment path drops the leading bundles/<name>/ prefix. All
    other files deploy where they live.
    """
    rel = md_file.relative_to(_ROOT)
    if rel.parts[0] == "bundles" and len(rel.parts) > 2:
        return Path(*rel.parts[2:])
    return rel


def _normalised_target(rel_dir: Path, target: str) -> Path | None:
    """Resolve a link target against its file's directory, relative to the deployment root.

    Returns None when the target escapes the deployment root (such links can
    never resolve in a downstream repository).
    """
    path = target.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return None
    candidate = path.lstrip("/") if path.startswith("/") else os.path.normpath(str(rel_dir / path))
    if candidate.startswith(".."):
        return None
    return Path(candidate)


def _relative_link_cases() -> list[tuple[str, Path, str]]:
    """Collect (label, markdown file, link target) for every relative link."""
    cases: list[tuple[str, Path, str]] = []
    for md_file in _markdown_files():
        text = md_file.read_text(encoding="utf-8", errors="replace")
        text = _FENCED_CODE_RE.sub("", text)
        text = _INLINE_CODE_RE.sub("", text)
        text = _HTML_COMMENT_RE.sub("", text)
        for match in _LINK_RE.finditer(text):
            target = match.group(1)
            if _SCHEME_RE.match(target) or target.startswith(("#", "<")):
                continue
            if target.split("#", 1)[0] in _PLACEHOLDER_TARGETS:
                continue
            label = f"{md_file.relative_to(_ROOT)} -> {target}"
            cases.append((label, md_file, target))
    return cases


_LINK_CASES = _relative_link_cases()


def _load_bundle_names() -> list[str]:
    """Return all bundle names defined in template-bundles.yml."""
    config = yaml.safe_load(_TEMPLATE_BUNDLES.read_text(encoding="utf-8"))
    return sorted(config["bundles"])


class TestMarkdownLinks:
    """Verify that every relative markdown link points at something that exists."""

    @pytest.mark.parametrize(
        ("label", "md_file", "target"),
        _LINK_CASES,
        ids=[case[0] for case in _LINK_CASES],
    )
    def test_relative_link_resolves(self, label: str, md_file: Path, target: str) -> None:
        """Each relative link must resolve in the repo or in any bundle's downstream layout."""
        rel = _deployment_rel_path(md_file)
        rel_dir = _DEPLOYED_DIR_OVERRIDES.get(rel, rel.parent)
        resolved = _normalised_target(rel_dir, target)
        assert resolved is not None, f"{label}: link escapes the repository root"

        roots = [_ROOT, *(d for d in sorted(_BUNDLES_DIR.iterdir()) if d.is_dir())]
        assert any((root / resolved).exists() for root in roots), (
            f"{label}: target does not exist in this repository or in any bundle's downstream layout"
        )

    def test_links_were_collected(self) -> None:
        """Guard against the link scanner silently collecting nothing."""
        assert len(_LINK_CASES) > 50, "expected to find a substantial number of relative links"


class TestBundleDocumentation:
    """Verify that the bundle documentation tracks the authoritative bundle list."""

    @pytest.mark.parametrize("bundle_name", _load_bundle_names())
    def test_bundle_documented_in_claude_md(self, bundle_name: str) -> None:
        """Every bundle defined in template-bundles.yml must be mentioned in CLAUDE.md."""
        claude_md = (_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        assert f"`{bundle_name}`" in claude_md, (
            f"bundle '{bundle_name}' is defined in .rhiza/template-bundles.yml but not documented in CLAUDE.md"
        )
