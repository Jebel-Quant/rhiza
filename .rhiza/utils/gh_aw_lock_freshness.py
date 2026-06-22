"""Compiler-free freshness check for gh-aw agentic workflow lock files.

GitHub Agentic Workflow sources live as ``.github/workflows/*.md`` files that
compile to ``.lock.yml`` artifacts via ``gh aw compile``. Every generated
``.lock.yml`` embeds a ``# gh-aw-metadata:`` header recording the SHA-256
``body_hash`` of its source's markdown body.

This module verifies, without requiring the ``gh-aw`` CLI extension, that each
source has a compiled lock file and that the embedded ``body_hash`` matches the
current source. It catches the common drift case: a ``.md`` prompt body edited
without recompiling. The authoritative full check (which additionally covers
frontmatter and pinned-action drift) remains ``gh aw compile`` followed by a
``git diff``, which ``make gh-aw-validate`` runs when the extension is available.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

_METADATA_PREFIX = "# gh-aw-metadata:"
_FIX_HINT = "Run 'make gh-aw-compile' and commit the regenerated .lock.yml files."
# Capture the markdown body that follows the leading YAML frontmatter block.
_FRONTMATTER_RE = re.compile(r"^---\r?\n.*?\r?\n---\r?\n?(.*)$", re.DOTALL)


def iter_agentic_sources(workflows_dir: Path) -> list[Path]:
    """Return agentic-workflow markdown sources under a workflows directory.

    A source is any ``*.md`` file that begins with a ``---`` YAML frontmatter
    fence, matching the gh-aw convention.

    Args:
        workflows_dir: The ``.github/workflows`` directory to scan.

    Returns:
        Sorted list of agentic-workflow ``.md`` source paths (empty if the
        directory does not exist).
    """
    if not workflows_dir.is_dir():
        return []
    return [md for md in sorted(workflows_dir.glob("*.md")) if md.read_text(encoding="utf-8").startswith("---")]


def source_body_hash(md_text: str) -> str | None:
    """Return the SHA-256 of the markdown body that follows the frontmatter.

    The body is everything after the closing ``---`` fence, stripped of leading
    and trailing whitespace — the same normalisation gh-aw applies before
    hashing.

    Args:
        md_text: Full text of an agentic-workflow ``.md`` source.

    Returns:
        Hex SHA-256 digest of the stripped body, or ``None`` when no closing
        frontmatter fence is present.
    """
    match = _FRONTMATTER_RE.match(md_text)
    if match is None:
        return None
    return hashlib.sha256(match.group(1).strip().encode("utf-8")).hexdigest()


def embedded_body_hash(lock_text: str) -> str | None:
    """Return the ``body_hash`` recorded in a lock file's gh-aw metadata header.

    Args:
        lock_text: Full text of a generated ``.lock.yml`` file.

    Returns:
        The embedded hex digest, or ``None`` when the metadata header or the
        ``body_hash`` field is absent or unparseable.
    """
    for line in lock_text.splitlines()[:5]:
        if line.startswith(_METADATA_PREFIX):
            try:
                data: object = json.loads(line[len(_METADATA_PREFIX) :].strip())
            except json.JSONDecodeError:
                return None
            if isinstance(data, dict):
                value = data.get("body_hash")
                return value if isinstance(value, str) else None
            return None
    return None


def check_freshness(repo_root: Path) -> list[str]:
    """Return freshness problems for every agentic workflow lock file.

    Args:
        repo_root: Repository root that contains ``.github/workflows``.

    Returns:
        Human-readable problem descriptions; empty when every source has a
        compiled lock file whose embedded body hash matches the source (also
        empty when there are no agentic sources).
    """
    problems: list[str] = []
    workflows_dir = repo_root / ".github" / "workflows"
    for md in iter_agentic_sources(workflows_dir):
        lock = md.with_suffix(".lock.yml")
        if not lock.exists():
            problems.append(f"{md.name}: no compiled {lock.name} found")
            continue
        expected = embedded_body_hash(lock.read_text(encoding="utf-8"))
        if expected is None:
            problems.append(f"{lock.name}: missing or invalid '{_METADATA_PREFIX}' metadata header")
            continue
        if expected != source_body_hash(md.read_text(encoding="utf-8")):
            problems.append(f"{md.name}: body changed since last compile ({lock.name} is stale)")
    return problems


def main(argv: list[str] | None = None) -> int:
    """Check lock-file freshness and report problems to stdout.

    Args:
        argv: Optional argument list; the first value, if present, is the
            repository root to check (defaults to the current directory).

    Returns:
        ``0`` when all lock files are fresh, ``1`` otherwise.
    """
    args = sys.argv[1:] if argv is None else argv
    repo_root = Path(args[0]) if args else Path.cwd()
    problems = check_freshness(repo_root)
    if not problems:
        print("[OK] All agentic workflow lock files are up to date.")
        return 0
    print("[ERROR] Agentic workflow lock files are stale relative to their .md sources:")
    for problem in problems:
        print(f"  - {problem}")
    print(_FIX_HINT)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
