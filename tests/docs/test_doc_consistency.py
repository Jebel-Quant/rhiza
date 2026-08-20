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

import functools
import os
import re
import subprocess  # nosec B404
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
# rendered by Marp from the repository root (see rhiza-task's `presentation` task).
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


def _load_profile_names() -> list[str]:
    """Return all profile names defined in template-bundles.yml."""
    config = yaml.safe_load(_TEMPLATE_BUNDLES.read_text(encoding="utf-8"))
    return sorted(config["profiles"])


_README = _ROOT / "README.md"

# First-column backtick-wrapped token of a markdown table row, e.g. ``| `core` | ... |``.
_TABLE_FIRST_COL_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|", re.MULTILINE)


def _readme_section(start: str, *, until: str) -> str:
    """Return the slice of README.md from heading ``start`` up to the next heading ``until``."""
    text = _README.read_text(encoding="utf-8")
    begin = text.index(start)
    end = text.index(until, begin + len(start))
    return text[begin:end]


def _readme_bundle_names() -> set[str]:
    """Return the bundle names listed in README.md's 'Available Template Bundles' tables."""
    section = _readme_section("### Available Template Bundles", until="\n## ")
    return set(_TABLE_FIRST_COL_RE.findall(section))


def _readme_profile_names() -> set[str]:
    """Return the profile names listed in README.md's 'Profiles' table."""
    section = _readme_section("### Profiles", until="### Available Template Bundles")
    return set(_TABLE_FIRST_COL_RE.findall(section))


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


_BUNDLE_TAXONOMY = _ROOT / "docs" / "reference" / "BUNDLE_TAXONOMY.md"


class TestBundleTaxonomyDoc:
    """Verify the bundle-taxonomy reference page tracks the authoritative bundle list."""

    @pytest.mark.parametrize("bundle_name", _load_bundle_names())
    def test_bundle_documented_in_taxonomy(self, bundle_name: str) -> None:
        """Every bundle defined in template-bundles.yml must appear in BUNDLE_TAXONOMY.md."""
        taxonomy = _BUNDLE_TAXONOMY.read_text(encoding="utf-8")
        assert f"`{bundle_name}`" in taxonomy, (
            f"bundle '{bundle_name}' is defined in .rhiza/template-bundles.yml but not documented in "
            "docs/reference/BUNDLE_TAXONOMY.md"
        )

    @pytest.mark.parametrize("profile_name", _load_profile_names())
    def test_profile_documented_in_taxonomy(self, profile_name: str) -> None:
        """Every profile defined in template-bundles.yml must appear in BUNDLE_TAXONOMY.md."""
        taxonomy = _BUNDLE_TAXONOMY.read_text(encoding="utf-8")
        assert f"`{profile_name}`" in taxonomy, (
            f"profile '{profile_name}' is defined in .rhiza/template-bundles.yml but not documented in "
            "docs/reference/BUNDLE_TAXONOMY.md"
        )


class TestReadmeBundleList:
    """Verify the README's bundle/profile tables track the authoritative template-bundles.yml."""

    @pytest.mark.parametrize("bundle_name", _load_bundle_names())
    def test_bundle_listed_in_readme(self, bundle_name: str) -> None:
        """Every bundle in template-bundles.yml must appear in the README's bundle tables."""
        assert bundle_name in _readme_bundle_names(), (
            f"bundle '{bundle_name}' is defined in .rhiza/template-bundles.yml but is not listed in "
            "README.md's 'Available Template Bundles' tables"
        )

    def test_readme_lists_no_unknown_bundles(self) -> None:
        """The README's bundle tables must not list bundles absent from template-bundles.yml."""
        extra = _readme_bundle_names() - set(_load_bundle_names())
        assert not extra, (
            f"README.md's bundle tables list {sorted(extra)}, which is not defined in .rhiza/template-bundles.yml"
        )

    @pytest.mark.parametrize("profile_name", _load_profile_names())
    def test_profile_listed_in_readme(self, profile_name: str) -> None:
        """Every profile in template-bundles.yml must appear in the README's profiles table."""
        assert profile_name in _readme_profile_names(), (
            f"profile '{profile_name}' is defined in .rhiza/template-bundles.yml but is not listed in "
            "README.md's 'Profiles' table"
        )

    def test_readme_lists_no_unknown_profiles(self) -> None:
        """The README's profiles table must not list profiles absent from template-bundles.yml."""
        extra = _readme_profile_names() - set(_load_profile_names())
        assert not extra, (
            f"README.md's profiles table lists {sorted(extra)}, which is not defined in .rhiza/template-bundles.yml"
        )

    def test_readme_tables_were_parsed(self) -> None:
        """Guard against the README table scanner silently collecting nothing."""
        assert len(_readme_bundle_names()) > 5, "expected README to list multiple bundles"
        assert len(_readme_profile_names()) > 1, "expected README to list multiple profiles"


# The root Makefile and `local.mk`: this repo runs on the rhiza-task shim, so there is no
# `.rhiza/rhiza.mk` and no `.rhiza/make.d/` here. The Makefile is the shim verbatim and
# defines only `help`, so `local.mk` is where every target this repo owns actually lives --
# omit it and `make e2e` in the docs reads as drift. The gates a doc may legitimately
# mention come from the CLI instead -- see :func:`_defined_make_targets`.
_MAKE_SOURCES = ("Makefile", "local.mk")

_TARGET_DEF_RE = re.compile(r"^([A-Za-z0-9_.-]+(?:\s+[A-Za-z0-9_.-]+)*)\s*::?(?!=)", re.MULTILINE)
_MAKE_MENTION_RE = re.compile(r"\bmake\s+([a-z][A-Za-z0-9_-]*)")
_CODE_REGION_RE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)

_BUNDLE_COUNT_RE = re.compile(r"\b\d+\s+(?:\w+\s+){0,2}bundles\b", re.IGNORECASE)
_STAMP_RE = re.compile(r"^\s*\*{0,2}Last Updated", re.MULTILINE | re.IGNORECASE)

# Markdown files exempt from prose-drift gates: generated or historical records.
_PROSE_GATE_EXEMPT = {"CHANGELOG.md"}


@functools.lru_cache(maxsize=1)
def _cli_task_names() -> frozenset[str]:
    """Return every task the pinned rhiza-task CLI can run in this repository.

    The shim's ``%:`` catch-all forwards any unmatched target to the CLI, so these are as
    much "make targets" as an explicit rule is -- ``make test`` works because ``test`` is a
    task, not because anything in the Makefile mentions it.

    Read from the CLI rather than listed here, and *in this repository* rather than
    generically: the task set is layer-dependent, so a hand-written list would drift on the
    next rhiza-task release.

    Returns:
        The task names, or an empty set if the CLI cannot be reached.
    """
    match = re.search(r"^RHIZA_TASK \?= (\S+)", (_ROOT / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        return frozenset()
    proc = subprocess.run(  # nosec B603
        ["uvx", match.group(1), "list"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return frozenset()
    return frozenset(m.group(1) for m in re.finditer(r"^\s(\S+)\s{2,}\S", proc.stdout, re.MULTILINE))


def _defined_make_targets() -> set[str]:
    """Return every target ``make`` can resolve: explicit rules plus CLI tasks.

    Both halves are needed and neither is sufficient. The root Makefile holds only ``help``
    and ``local.mk`` this repo's mother-repo-only targets; every gate a doc mentions --
    ``test``, ``fmt``, ``typecheck`` -- is a task the shim forwards to. Checking the files
    alone would fail every such mention; checking the CLI alone would miss ``make e2e``.
    """
    targets: set[str] = set(_cli_task_names())
    sources = [_ROOT / s for s in _MAKE_SOURCES]
    # The bundles' own `.rhiza/make.d/*.mk` used to be scanned alongside, because rhiza
    # documented what it *ships* and not only what it runs: `make paper` and `make view-prs`
    # were real for a consumer while unknown to the CLI. rhiza-task 0.3.0 closed that gap by
    # taking over the last five fragments, so the CLI is once again the complete answer and
    # the two sources have converged.
    sources += sorted((_ROOT / "bundles").glob("*/Makefile"))
    for source in sources:
        if not source.is_file():
            continue
        for match in _TARGET_DEF_RE.finditer(source.read_text(encoding="utf-8")):
            targets.update(name for name in match.group(1).split() if not name.startswith("."))
    return targets


def _make_mention_cases() -> list[tuple[str, str]]:
    """Collect (label, target) for every `make <target>` mention in CLAUDE.md and README.md code."""
    cases: list[tuple[str, str]] = []
    for doc in ("CLAUDE.md", "README.md"):
        text = (_ROOT / doc).read_text(encoding="utf-8")
        for region in _CODE_REGION_RE.findall(text):
            for match in _MAKE_MENTION_RE.finditer(region):
                cases.append((f"{doc}: make {match.group(1)}", match.group(1)))
    return sorted(set(cases))


class TestProseDrift:
    """Verify that documentation prose cannot drift from the repository state."""

    @pytest.mark.parametrize(("label", "target"), _make_mention_cases(), ids=[c[0] for c in _make_mention_cases()])
    def test_mentioned_make_targets_exist(self, label: str, target: str) -> None:
        """Every `make <target>` mentioned in CLAUDE.md/README.md code must be a real target."""
        assert target in _defined_make_targets(), (
            f"{label}: target is not defined in the Makefile and is not a task of the pinned CLI"
        )

    @pytest.mark.parametrize(
        "md_file",
        [p for p in _markdown_files() if p.name not in _PROSE_GATE_EXEMPT],
        ids=lambda p: str(p.relative_to(_ROOT)),
    )
    def test_no_hardcoded_bundle_counts(self, md_file: Path) -> None:
        """Docs must not hard-code the bundle count; template-bundles.yml is authoritative."""
        hits = _BUNDLE_COUNT_RE.findall(md_file.read_text(encoding="utf-8", errors="replace"))
        assert not hits, f"hard-coded bundle count {hits} — refer to .rhiza/template-bundles.yml instead"

    @pytest.mark.parametrize(
        "md_file",
        [p for p in _markdown_files() if p.name not in _PROSE_GATE_EXEMPT],
        ids=lambda p: str(p.relative_to(_ROOT)),
    )
    def test_no_last_updated_stamps(self, md_file: Path) -> None:
        """Docs must not carry manual 'Last Updated' stamps; git history answers that question."""
        assert not _STAMP_RE.search(md_file.read_text(encoding="utf-8", errors="replace")), (
            "manual 'Last Updated' stamp found — these drift silently; rely on git history instead"
        )

    def test_make_mentions_were_collected(self) -> None:
        """Guard against the make-mention scanner silently collecting nothing."""
        assert len(_make_mention_cases()) > 10, "expected CLAUDE.md/README.md to mention make targets"


# Tools whose presence in the toolchain is worth keeping the docs honest about. Each is
# either invoked somewhere in _INVOCATION_SOURCES or it is not; the test below derives
# which, rather than hard-coding a "retired" list that would drift in its own right.
_WATCHED_TOOLS = (
    "pip-audit",
    "bandit",
    "semgrep",
    "deptry",
    "interrogate",
    "govulncheck",
    "cargo-machete",
)

# Where a tool would be invoked from: this repo's Makefile and every CI workflow, here and
# in the bundles it ships. The bundles' `.rhiza/make.d/*.mk` were a source until rhiza-task
# 0.3.0 took over the last five; a tool a *task* invokes is rhiza-task's to document.
_INVOCATION_SOURCES = (
    *(_ROOT / s for s in _MAKE_SOURCES),
    *sorted(_ROOT.glob(".github/workflows/*.yml")),
    *sorted(_ROOT.glob("bundles/*/.github/workflows/*.yml")),
    *sorted(_ROOT.glob("bundles/*/.gitlab/**/*.yml")),
    *sorted(_ROOT.glob("bundles/*/.gitlab-ci.yml")),
)

# Prose files exempt from the claim gate. CHANGELOG.md records what *was* true, and the
# e2e suite's docstrings name pip-audit as the analogue of govulncheck/cargo-deny — both
# describe history or comparison rather than claiming the tool runs.
_CLAIM_GATE_EXEMPT = {"CHANGELOG.md"}


@functools.lru_cache(maxsize=1)
def _cli_task_sources() -> str:
    """Return the concatenated source of the pinned CLI's task modules.

    Most of the watched tools moved *into* rhiza-task when the gate fragments retired: bandit,
    mypy, ty, deptry, interrogate, pytest and the rest are named in its task bodies
    (``uvx("bandit", ...)``, ``uv_run("mypy", ...)``) rather than in a ``.mk`` recipe. Scanning
    only the fragments would therefore report them as *not invoked* and fail every document that
    mentions them -- which is the opposite of the truth, and would invite deleting accurate prose
    to get a green suite.

    Read from the installed package rather than listed here, because this class's whole design is
    that the invoked set is derived: adding a tool to a task must re-permit its mentions in the
    same commit, with no list to update.

    Returns:
        The concatenated text, or an empty string if the CLI cannot be located.
    """
    match = re.search(r"^RHIZA_TASK \?= (\S+)", (_ROOT / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        return ""
    name, _, version = match.group(1).partition("@")
    requirement = f"{name}=={version}" if version else name
    proc = subprocess.run(  # nosec B603
        [
            "uv",
            "run",
            "--quiet",
            "--no-project",
            "--with",
            requirement,
            "python",
            "-c",
            "import pathlib, rhiza_task;"
            "print('\\n'.join(p.read_text() for p in pathlib.Path(rhiza_task.__file__).parent.rglob('*.py')))",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else ""


def _invoked_tools() -> set[str]:
    """Return the watched tools that something in the product actually invokes.

    Three places now, where there used to be two: the make fragments and workflows still in the
    tree, and the task bodies of the pinned CLI that replaced most of those fragments.
    """
    haystack = "\n".join(
        path.read_text(encoding="utf-8", errors="replace") for path in _INVOCATION_SOURCES if path.is_file()
    )
    haystack += "\n" + _cli_task_sources()
    return {tool for tool in _WATCHED_TOOLS if tool in haystack}


def _prose_files() -> list[Path]:
    """Return the documentation files whose claims about the toolchain are gated."""
    return [p for p in _markdown_files() if p.name not in _CLAIM_GATE_EXEMPT] + sorted(_ROOT.glob("docs/paper/*.tex"))


class TestToolClaims:
    """Documentation must not credit the project with a tool nothing runs.

    `make security` dropped pip-audit, and a test pins the removal — but nine documents
    went on describing it, including a self-attestation against the CII best-practices
    standard and the published paper (#1506). Docstring coverage and markdownlint both
    stayed green throughout: neither asks whether a claim is *true*. This does.

    The invoked set is derived rather than declared, so reinstating a tool in a workflow
    re-permits every mention of it in the same commit.
    """

    @pytest.mark.parametrize(
        "doc",
        _prose_files(),
        ids=lambda p: str(p.relative_to(_ROOT)),
    )
    def test_docs_only_claim_tools_that_run(self, doc: Path) -> None:
        """No prose may name a watched tool that no make fragment or workflow invokes."""
        invoked = _invoked_tools()
        text = doc.read_text(encoding="utf-8", errors="replace")
        claimed_but_absent = [t for t in _WATCHED_TOOLS if t not in invoked and t in text]
        assert not claimed_but_absent, (
            f"{doc.relative_to(_ROOT)} names {claimed_but_absent}, which nothing in this "
            f"repository invokes. Either wire the tool up or drop the claim (#1506)."
        )

    def test_the_invocation_scan_found_something(self) -> None:
        """Positive control: an empty invoked set would make the gate above vacuous."""
        invoked = _invoked_tools()
        assert {"bandit", "deptry"} <= invoked, (
            f"expected bandit and deptry to be detected as invoked; got {sorted(invoked)}. "
            "The invocation scan is probably looking in the wrong places."
        )

    def test_pip_audit_is_the_known_absent_case(self) -> None:
        """pip-audit is deliberately not wired up; this pins the fact the gate depends on."""
        assert "pip-audit" not in _invoked_tools(), (
            "pip-audit is invoked again — that is fine, but this test and the docs that "
            "were pruned in #1506 should be revisited together."
        )
