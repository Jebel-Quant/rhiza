"""Gate SECURITY.md's "Security Measures" claims against repository reality.

SECURITY.md once claimed GPG-signed releases while no workflow implemented
signing (#1157) — the same prose-drift class that ``TestProseDrift`` catches
for make targets, but outside its scope. These tests bind every bold claim
bullet under "## Security Measures" to a concrete piece of evidence (a
workflow step, hook, or config file), in both directions:

1. every mapped claim's evidence must exist in the repository, and
2. every claim bullet in SECURITY.md must be mapped — adding a new measure
   to the prose without wiring up its evidence fails loudly here.
"""

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    """Return the text of a repository file, or an empty string if absent."""
    path = _ROOT / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _make_fragments_text() -> str:
    """Return the concatenated text of all .rhiza/make.d fragments."""
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted((_ROOT / ".rhiza" / "make.d").glob("*.mk")))


# Claim (the bold lead of a bullet under "## Security Measures") -> a predicate
# proving the repository actually implements it.
_CLAIM_EVIDENCE = {
    "CodeQL": lambda: (_ROOT / ".github" / "workflows" / "rhiza_codeql.yml").is_file(),
    "Bandit": lambda: "bandit" in _read(".pre-commit-config.yaml"),
    "pip-audit": lambda: "pip-audit" in _make_fragments_text(),
    "Secret Scanning": lambda: (_ROOT / ".github" / "secret_scanning.yml").is_file(),
    "SLSA Provenance": lambda: "attest-build-provenance" in _read(".github/workflows/rhiza_release.yml"),
    "Locked Dependencies": lambda: (_ROOT / "uv.lock").is_file(),
    "Dependabot": lambda: (_ROOT / ".github" / "dependabot.yml").is_file(),
    "Renovate": lambda: (_ROOT / "renovate.json").is_file(),
    "OIDC Publishing": lambda: "id-token: write" in _read(".github/workflows/rhiza_release.yml"),
    "SBOM Attestations": lambda: "cyclonedx" in _read(".github/workflows/rhiza_release.yml").lower(),
    "Tag Protection": lambda: "Validate Tag" in _read(".github/workflows/rhiza_release.yml"),
}

_CLAIM_BULLET = re.compile(r"^- \*\*(?P<claim>[^*]+)\*\*:", re.MULTILINE)


def _security_measures_claims() -> list[str]:
    """Extract the bold claim bullets from SECURITY.md's Security Measures section."""
    text = _read("SECURITY.md")
    match = re.search(r"^## Security Measures$(?P<section>.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert match, "SECURITY.md has no '## Security Measures' section — update this test's parser"
    return _CLAIM_BULLET.findall(match.group("section"))


def test_claims_were_collected():
    """Sanity check: the parser finds a plausible number of claims."""
    assert len(_security_measures_claims()) >= 5, f"unexpectedly few claims parsed: {_security_measures_claims()}"


@pytest.mark.parametrize("claim", sorted(_CLAIM_EVIDENCE), ids=str)
def test_claimed_measure_is_implemented(claim: str):
    """Every mapped security-measure claim must have its evidence in the repository."""
    assert _CLAIM_EVIDENCE[claim](), (
        f"SECURITY.md claims '{claim}' but its evidence is missing — either implement the "
        "measure or remove/correct the claim (see #1157 for the GPG precedent)."
    )


def test_every_claim_in_security_md_is_mapped():
    """Every claim bullet in SECURITY.md must have an evidence mapping in this test.

    This forces new prose claims to arrive with verifiable evidence, and flags
    stale mappings when claims are removed from the document.
    """
    documented = set(_security_measures_claims())
    mapped = set(_CLAIM_EVIDENCE)
    unmapped = documented - mapped
    stale = mapped - documented
    assert not unmapped, f"SECURITY.md claims without an evidence mapping in _CLAIM_EVIDENCE: {sorted(unmapped)}"
    assert not stale, f"_CLAIM_EVIDENCE entries no longer claimed in SECURITY.md: {sorted(stale)}"
