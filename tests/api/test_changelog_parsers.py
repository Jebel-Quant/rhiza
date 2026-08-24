r"""cliff.toml's skip rules must drop machine commits without eating real ones.

Every rule in ``commit_parsers`` is matched by git-cliff against the **whole commit
message**, subject and body together. That is easy to forget when writing one, and the
consequence is the quietest kind of failure this repo keeps finding: the commit is not
reported as skipped, it simply never appears, and the changelog understates what shipped.

It has now happened twice, to two different rules:

* A bare ``bump`` alternative ate every ``chore(deps): bump <dependency>``. The rhiza-hooks
  v1.2.0 bump (#1487) vanished from v1.3.2's notes that way, and had been vanishing for a
  while unnoticed.
* ``.*\\[skip ci\\].*`` ate ``feat: give the paper branch a README`` (#1626) out of v1.6.0's
  notes, because its body quoted the *format* of another commit's message -- one backticked
  ``[skip ci]`` twenty lines below the subject.

So these tests run the rules the way git-cliff does -- over a full message -- and assert
both directions for each: the machine commit the rule exists for is dropped, and a commit
that merely mentions the marker in prose survives. Asserting only the first is what let both
regressions through.

The rules are read from ``cliff.toml`` rather than restated here, so a rewritten pattern is
tested rather than a copy of the old one.

One consequence of anchoring to the subject is worth knowing before writing a commit *about*
the marker: a subject containing it is still skipped, correctly, so such a commit has to name
the marker in its body instead. The fix that introduced these tests was itself dropped from
the release notes once for exactly that reason.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

# A commit whose body quotes another commit's message. This is not a contrived case: it is
# what #1626 did, and the shape any commit takes when it documents what a publish step
# writes.
_MENTIONS_IN_BODY = """feat: give the paper branch a README explaining what it is

Provenance goes in the commit message, which is only written when there is
something to commit: `Update the compiled paper from <sha> [skip ci]`.
"""

# What the rule is actually for: a machine-written commit carrying the marker in its subject.
_MARKER_IN_SUBJECT = "chore: update CHANGELOG.md for v0.18.9 [skip ci]"

# A Dependabot subject, which the `bump` rule must not swallow.
_DEPENDENCY_BUMP = "chore(deps): bump rhiza-hooks from 1.1.0 to 1.2.0"

# The release flow's own commits, which the release rules exist to drop.
_RELEASE_COMMIT = "chore: release v1.6.0"


@pytest.fixture(scope="module")
def skip_patterns() -> list[str]:
    """Return every ``commit_parsers`` pattern marked ``skip``.

    Returns:
        The regexes, as written in cliff.toml.
    """
    config = tomllib.loads((_ROOT / "cliff.toml").read_text(encoding="utf-8"))
    parsers = config["git"]["commit_parsers"]
    return [p["message"] for p in parsers if p.get("skip") and "message" in p]


def _skipped(message: str, patterns: list[str]) -> bool:
    """Return whether any skip rule matches a full commit message.

    Args:
        message: The complete commit message, subject and body.
        patterns: The skip regexes.

    Returns:
        True when git-cliff would drop the commit.
    """
    # `search`, not `match`: git-cliff's regexes are unanchored, which is the whole reason a
    # body mention could match a rule intended for a subject.
    return any(re.search(pattern, message) for pattern in patterns)


def test_the_scan_finds_the_skip_rules(skip_patterns: list[str]) -> None:
    """Positive control: no rules would make every assertion below vacuous."""
    assert len(skip_patterns) >= 4, (
        f"found only {len(skip_patterns)} skip rule(s) in cliff.toml: {skip_patterns}. The "
        f"marker rule and the three release-flow rules alone are more than that, so this is "
        f"reading the wrong table."
    )


def test_a_marker_in_the_subject_is_dropped(skip_patterns: list[str]) -> None:
    """The rule must still do its job: machine commits stay out of the changelog."""
    assert _skipped(_MARKER_IN_SUBJECT, skip_patterns), (
        f"no skip rule matches {_MARKER_IN_SUBJECT!r}. Anchoring the marker rule to the "
        f"subject must not stop it matching a subject."
    )


def test_a_marker_mentioned_in_the_body_survives(skip_patterns: list[str]) -> None:
    """A commit that *talks about* the marker is a real change and must be reported.

    This is #1626. The subject is a plain `feat:`; the body quotes another commit's message.
    Under the unanchored rule the whole feature disappeared from the release notes.
    """
    assert not _skipped(_MENTIONS_IN_BODY, skip_patterns), (
        "a skip rule matches a commit that only mentions `[skip ci]` in its body, so the "
        "feature it describes will be missing from the changelog with nothing reporting it "
        "(#1626). Anchor the rule to the subject line."
    )


def test_a_dependency_bump_survives(skip_patterns: list[str]) -> None:
    """The other half of the same lesson, kept as a regression test.

    A bare `bump` alternative in the release rules ate every `chore(deps): bump ...`, and
    #1487 vanished from v1.3.2's notes. The rules name `release` and `bump version`
    explicitly for this reason.
    """
    assert not _skipped(_DEPENDENCY_BUMP, skip_patterns), (
        f"a skip rule matches {_DEPENDENCY_BUMP!r}. Dependency bumps are user-facing signal "
        f"and belong in the Dependencies section."
    )


def test_the_release_commit_is_dropped(skip_patterns: list[str]) -> None:
    """`chore: release vX.Y.Z` is bookkeeping and must not appear in its own notes."""
    assert _skipped(_RELEASE_COMMIT, skip_patterns), (
        f"no skip rule matches {_RELEASE_COMMIT!r}, so every release's notes would open with the commit that cut them."
    )
