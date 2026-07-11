"""Completeness gate tying every declared bundle to a behavioural test.

100% docstring/line coverage proves the Python utilities are exercised, but says
nothing about the *templates*: a new bundle can be added to
``.rhiza/template-bundles.yml`` and shipped without any test that exercises the
Makefile targets, workflow stubs, or files it contributes. This module closes
that gap.

For every bundle declared in ``template-bundles.yml`` we require either:

1. a behavioural test under ``.rhiza/tests/`` or ``tests/`` that references the
   bundle by name (a quoted string, a ``bundles/<name>`` path, or a
   ``test_<name>`` / ``<name>_targets`` test module), or
2. an explicit entry in ``_EXEMPT`` with a documented reason (for static
   file-only bundles that have no behaviour to drive — their content is already
   guarded by the bundle content-validity and byte-identity sync tests).

The generic tests that enumerate *all* bundles from the YAML (sync, schema,
matrix, ...) are deliberately excluded from the scan: they would make every
bundle look "covered" and defeat the gate.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATE_BUNDLES = _ROOT / ".rhiza" / "template-bundles.yml"

# Test modules that iterate the full bundle list from template-bundles.yml. They
# touch every bundle generically, so a mention here is not evidence of a
# *behavioural* test and must not count as coverage.
_GENERIC_TESTS = {
    "test_template_bundles.py",
    "test_template_bundles_schema.py",
    "test_bundle_rhiza_sync.py",
    "test_bundle_sync.py",
    "test_bundle_matrix.py",
    "test_bundle_combinations.py",
    "test_bundle_content_validity.py",
    "test_bundle_claude_commands_sync.py",
    "test_doc_consistency.py",
    "test_bundle_test_coverage.py",  # this module
}

# Bundles with no behavioural surface to exercise: they contribute only static
# files (no make targets, no workflow logic). Their content is already verified
# by test_bundle_content_validity.py and the byte-identity sync tests, so a
# dedicated behavioural test would have nothing to assert. Keyed to the reason.
_EXEMPT: dict[str, str] = {
    "claude": "Static .claude/commands/*.md slash-command prose; no make targets or "
    "workflows to drive. Byte-identity with the dogfooded copies is guarded by "
    "test_bundle_claude_commands_sync.py (a generic module).",
    "legal": "Static community files (LICENSE, CODE_OF_CONDUCT, ...); no targets "
    "or workflows. Content is guarded by the bundle content-validity tests.",
    "renovate": "Static renovate.json config; validated by the 'Validate Renovate "
    "Config' pre-commit hook and the bundle content-validity tests, no behaviour to drive.",
    "vscode": "Static .vscode/extensions.json and settings.json; no targets or "
    "workflows. Covered by TestVscodeBundleSync in test_bundle_combinations.py "
    "(a generic test module) and the bundle content-validity tests.",
}


def _bundle_names() -> list[str]:
    """Return every bundle name declared in template-bundles.yml."""
    config = yaml.safe_load(_TEMPLATE_BUNDLES.read_text(encoding="utf-8"))
    return sorted(config["bundles"])


def _behavioural_test_files() -> list[Path]:
    """Return every non-generic test file under .rhiza/tests/ and tests/."""
    files: list[Path] = []
    for base in (".rhiza/tests", "tests"):
        for path in sorted((_ROOT / base).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            if path.name in _GENERIC_TESTS:
                continue
            files.append(path)
    return files


# Read behavioural test files lazily and cache their text for repeated scans.
_TEST_SOURCES: dict[Path, str] = {}


def _test_sources() -> dict[Path, str]:
    """Return cached behavioural test sources, loading them on first use."""
    if not _TEST_SOURCES:
        _TEST_SOURCES.update(
            {
                p: p.read_text(encoding="utf-8", errors="replace")
                for p in _behavioural_test_files()
            }
        )
    return _TEST_SOURCES


def _bundle_patterns(bundle: str) -> list[str]:
    """Return the regex fragments that count as a behavioural reference to ``bundle``."""
    name = re.escape(bundle)
    snake = re.escape(bundle.replace("-", "_"))
    return [
        rf"""["']{name}["']""",  # quoted bundle name
        rf"/{name}[/.\"']",  # path component, e.g. bundles/<name>/...
        rf"bundles/{name}\b",
        rf"{snake}_targets",  # e.g. docker_targets
        rf"test_{snake}\b",  # e.g. test_lfs
    ]


def _covering_tests(bundle: str) -> list[str]:
    """Return the behavioural test files that reference ``bundle``, if any."""
    patterns = [re.compile(p) for p in _bundle_patterns(bundle)]
    return [
        path.relative_to(_ROOT).as_posix()
        for path, text in _test_sources().items()
        if any(p.search(text) for p in patterns)
    ]


_BUNDLE_NAMES = _bundle_names()


class TestBundleTestCoverage:
    """Every declared bundle must have a behavioural test or a documented exemption."""

    @pytest.mark.parametrize("bundle", _BUNDLE_NAMES)
    def test_bundle_has_behavioural_test(self, bundle: str) -> None:
        """A bundle is covered by a behavioural test, or is explicitly exempt."""
        if bundle in _EXEMPT:
            return
        covering = _covering_tests(bundle)
        assert covering, (
            f"bundle '{bundle}' is declared in .rhiza/template-bundles.yml but no behavioural "
            f"test under .rhiza/tests/ or tests/ references it. Add a test that exercises the "
            f"bundle's targets/workflows/files, or add '{bundle}' to _EXEMPT in this module with a reason."
        )

    @pytest.mark.parametrize("bundle", sorted(_EXEMPT))
    def test_exemptions_are_real_bundles(self, bundle: str) -> None:
        """Every _EXEMPT key must name a bundle that actually exists (no stale exemptions)."""
        assert bundle in _BUNDLE_NAMES, (
            f"_EXEMPT lists '{bundle}', which is not a bundle in .rhiza/template-bundles.yml — remove the stale entry"
        )

    @pytest.mark.parametrize("bundle", sorted(_EXEMPT))
    def test_exemptions_are_still_untested(self, bundle: str) -> None:
        """An exempt bundle that has since gained a behavioural test must leave _EXEMPT."""
        covering = _covering_tests(bundle)
        assert not covering, (
            f"bundle '{bundle}' is in _EXEMPT but is now referenced by {covering}. "
            "Remove it from _EXEMPT so the bundle is gated by its real test."
        )

    def test_scanner_finds_known_coverage(self) -> None:
        """Guard against a scanner regression silently reporting everything as uncovered."""
        for bundle in ("docker", "marimo", "book", "paper", "lfs"):
            assert _covering_tests(bundle), (
                f"scanner found no behavioural test for '{bundle}', which has a known integration "
                "test — the coverage scan is broken"
            )
