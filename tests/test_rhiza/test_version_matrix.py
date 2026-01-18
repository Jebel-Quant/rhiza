"""Tests for version_matrix.py utility.

Tests cover version parsing, specifier validation, and edge cases
for malformed inputs. Includes property-based tests using hypothesis.
"""

import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Add the utils directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".rhiza" / "utils"))

from version_matrix import (
    CANDIDATES,
    PyProjectError,
    RhizaError,
    VersionSpecifierError,
    parse_version,
    satisfies,
    supported_versions,
)


class TestExceptionHierarchy:
    """Test custom exception class hierarchy."""

    def test_version_specifier_error_inherits_from_rhiza_error(self):
        """VersionSpecifierError should inherit from RhizaError."""
        assert issubclass(VersionSpecifierError, RhizaError)

    def test_pyproject_error_inherits_from_rhiza_error(self):
        """PyProjectError should inherit from RhizaError."""
        assert issubclass(PyProjectError, RhizaError)

    def test_rhiza_error_inherits_from_exception(self):
        """RhizaError should inherit from Exception."""
        assert issubclass(RhizaError, Exception)

    def test_can_catch_all_rhiza_errors(self):
        """All custom exceptions should be catchable as RhizaError."""
        with pytest.raises(RhizaError):
            raise VersionSpecifierError("test")

        with pytest.raises(RhizaError):
            raise PyProjectError("test")


class TestParseVersion:
    """Tests for parse_version function."""

    def test_simple_version(self):
        """Parse simple version strings."""
        assert parse_version("3.11") == (3, 11)
        assert parse_version("3.12") == (3, 12)
        assert parse_version("3.14") == (3, 14)

    def test_three_part_version(self):
        """Parse three-part version strings."""
        assert parse_version("3.11.0") == (3, 11, 0)
        assert parse_version("3.12.5") == (3, 12, 5)

    def test_version_with_rc_suffix(self):
        """Parse version with release candidate suffix."""
        assert parse_version("3.11.0rc1") == (3, 11, 0)
        assert parse_version("3.14.0a1") == (3, 14, 0)
        assert parse_version("3.13.0b2") == (3, 13, 0)

    def test_single_component_version(self):
        """Parse single component version."""
        assert parse_version("3") == (3,)

    def test_many_component_version(self):
        """Parse version with many components."""
        assert parse_version("1.2.3.4.5") == (1, 2, 3, 4, 5)

    def test_malformed_version_no_numeric_prefix(self):
        """Raise VersionSpecifierError for non-numeric component."""
        with pytest.raises(VersionSpecifierError) as exc_info:
            parse_version("abc.11")
        assert "abc" in str(exc_info.value)
        assert "expected a numeric prefix" in str(exc_info.value)

    def test_malformed_version_empty_component(self):
        """Raise VersionSpecifierError for empty component."""
        with pytest.raises(VersionSpecifierError) as exc_info:
            parse_version("3..11")
        assert "expected a numeric prefix" in str(exc_info.value)

    def test_malformed_version_letter_only(self):
        """Raise VersionSpecifierError for letter-only version."""
        with pytest.raises(VersionSpecifierError) as exc_info:
            parse_version("x.y.z")
        assert "Invalid version component" in str(exc_info.value)

    def test_empty_string(self):
        """Raise VersionSpecifierError for empty string."""
        with pytest.raises(VersionSpecifierError):
            parse_version("")

    def test_whitespace_version(self):
        """Raise VersionSpecifierError for whitespace-only version."""
        with pytest.raises(VersionSpecifierError):
            parse_version("   ")


class TestSatisfies:
    """Tests for satisfies function."""

    def test_greater_than_or_equal(self):
        """Test >= operator."""
        assert satisfies("3.11", ">=3.11") is True
        assert satisfies("3.12", ">=3.11") is True
        assert satisfies("3.10", ">=3.11") is False

    def test_less_than_or_equal(self):
        """Test <= operator."""
        assert satisfies("3.11", "<=3.11") is True
        assert satisfies("3.10", "<=3.11") is True
        assert satisfies("3.12", "<=3.11") is False

    def test_greater_than(self):
        """Test > operator."""
        assert satisfies("3.12", ">3.11") is True
        assert satisfies("3.11", ">3.11") is False
        assert satisfies("3.10", ">3.11") is False

    def test_less_than(self):
        """Test < operator."""
        assert satisfies("3.10", "<3.11") is True
        assert satisfies("3.11", "<3.11") is False
        assert satisfies("3.12", "<3.11") is False

    def test_equal(self):
        """Test == operator."""
        assert satisfies("3.11", "==3.11") is True
        assert satisfies("3.12", "==3.11") is False

    def test_not_equal(self):
        """Test != operator."""
        assert satisfies("3.12", "!=3.11") is True
        assert satisfies("3.11", "!=3.11") is False

    def test_implicit_equality(self):
        """Test version without operator implies equality."""
        assert satisfies("3.11", "3.11") is True
        assert satisfies("3.12", "3.11") is False

    def test_compound_specifier(self):
        """Test comma-separated specifiers."""
        assert satisfies("3.11", ">=3.11,<3.14") is True
        assert satisfies("3.12", ">=3.11,<3.14") is True
        assert satisfies("3.14", ">=3.11,<3.14") is False
        assert satisfies("3.10", ">=3.11,<3.14") is False

    def test_specifier_with_whitespace(self):
        """Test specifiers with whitespace."""
        assert satisfies("3.11", ">= 3.11") is True
        assert satisfies("3.11", ">=3.11, <3.14") is True

    def test_invalid_specifier_format(self):
        """Raise VersionSpecifierError for invalid specifier."""
        with pytest.raises(VersionSpecifierError) as exc_info:
            satisfies("3.11", "~=3.11")
        assert "Invalid specifier" in str(exc_info.value)
        assert "~=3.11" in str(exc_info.value)

    def test_invalid_specifier_garbage(self):
        """Raise VersionSpecifierError for garbage input."""
        with pytest.raises(VersionSpecifierError) as exc_info:
            satisfies("3.11", "foobar")
        assert "Invalid specifier" in str(exc_info.value)

    def test_invalid_specifier_operator_only(self):
        """Raise VersionSpecifierError for operator without version."""
        with pytest.raises(VersionSpecifierError) as exc_info:
            satisfies("3.11", ">=")
        assert "Invalid specifier" in str(exc_info.value)


class TestSupportedVersions:
    """Tests for supported_versions function."""

    def test_returns_list_of_versions(self):
        """supported_versions returns a list of version strings."""
        versions = supported_versions()
        assert isinstance(versions, list)
        assert all(isinstance(v, str) for v in versions)

    def test_versions_are_subset_of_candidates(self):
        """Returned versions should be from the CANDIDATES list."""
        versions = supported_versions()
        assert all(v in CANDIDATES for v in versions)

    def test_missing_requires_python(self, tmp_path, monkeypatch):
        """Raise PyProjectError when requires-python is missing."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\n')

        # Patch PYPROJECT to point to our temp file
        monkeypatch.setattr("version_matrix.PYPROJECT", pyproject)

        with pytest.raises(PyProjectError) as exc_info:
            supported_versions()
        assert "missing 'project.requires-python'" in str(exc_info.value)

    def test_no_matching_versions(self, tmp_path, monkeypatch):
        """Raise PyProjectError when no candidates match specifier."""
        pyproject = tmp_path / "pyproject.toml"
        # Require Python 2.7 which no candidate satisfies
        pyproject.write_text('[project]\nname = "test"\nrequires-python = ">=2.7,<3.0"\n')

        monkeypatch.setattr("version_matrix.PYPROJECT", pyproject)

        with pytest.raises(PyProjectError) as exc_info:
            supported_versions()
        assert "no supported Python versions match" in str(exc_info.value)
        # Error message should include evaluated candidates
        assert "Evaluated candidates" in str(exc_info.value)
        assert "3.11" in str(exc_info.value)

    def test_filters_versions_correctly(self, tmp_path, monkeypatch):
        """Correctly filter versions based on specifier."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nrequires-python = ">=3.12"\n')

        monkeypatch.setattr("version_matrix.PYPROJECT", pyproject)

        versions = supported_versions()
        assert "3.11" not in versions
        assert "3.12" in versions
        assert "3.13" in versions
        assert "3.14" in versions


class TestEdgeCases:
    """Additional edge case tests."""

    def test_version_comparison_tuple_length_mismatch(self):
        """Version tuples of different lengths use Python tuple comparison.

        Note: Python tuple comparison treats (3, 11) < (3, 11, 0) because
        the shorter tuple is exhausted first. This is intentional behavior
        of the simple implementation.
        """
        # (3, 11) < (3, 11, 0) in Python tuple comparison
        assert satisfies("3.11", ">=3.11.0") is False
        # (3, 11, 0) >= (3, 11) is True
        assert satisfies("3.11.0", ">=3.11") is True

    def test_leading_zeros_in_version(self):
        """Leading zeros are stripped when parsing."""
        assert parse_version("03.011") == (3, 11)

    def test_very_large_version_numbers(self):
        """Handle large version numbers."""
        assert parse_version("999.999.999") == (999, 999, 999)
        assert satisfies("999.999", ">=3.11") is True

    def test_specifier_with_multiple_commas(self):
        """Handle multiple constraints."""
        assert satisfies("3.12", ">=3.11,<3.14,!=3.13") is True
        assert satisfies("3.13", ">=3.11,<3.14,!=3.13") is False


# =============================================================================
# Property-based tests using Hypothesis
# =============================================================================

# Custom strategies for generating version-like data
version_component = st.integers(min_value=0, max_value=999)
version_tuple = st.tuples(version_component, version_component).map(lambda t: t) | st.tuples(
    version_component, version_component, version_component
).map(lambda t: t)


def tuple_to_version_str(t: tuple[int, ...]) -> str:
    """Convert a version tuple to a version string."""
    return ".".join(str(x) for x in t)


# Strategy for valid version strings (2 or 3 components)
valid_version_str = version_tuple.map(tuple_to_version_str)


class TestParseVersionProperties:
    """Property-based tests for parse_version function."""

    @given(components=st.lists(version_component, min_size=1, max_size=5))
    def test_output_length_equals_component_count(self, components: list[int]):
        """Parsing a valid version string produces a tuple with the same number of components."""
        version_str = ".".join(str(c) for c in components)
        result = parse_version(version_str)
        assert len(result) == len(components)

    @given(components=st.lists(version_component, min_size=1, max_size=5))
    def test_all_output_elements_are_non_negative_integers(self, components: list[int]):
        """All elements in the parsed tuple are non-negative integers."""
        version_str = ".".join(str(c) for c in components)
        result = parse_version(version_str)
        assert all(isinstance(x, int) and x >= 0 for x in result)

    @given(components=st.lists(version_component, min_size=1, max_size=5))
    def test_roundtrip_preserves_values(self, components: list[int]):
        """Parsing a version string and converting back gives the same values."""
        version_str = ".".join(str(c) for c in components)
        result = parse_version(version_str)
        # The values should match (leading zeros are stripped by int())
        assert result == tuple(components)

    @given(components=st.lists(version_component, min_size=1, max_size=5))
    def test_parsing_is_idempotent(self, components: list[int]):
        """Parsing, converting to string, and parsing again gives the same result."""
        version_str = ".".join(str(c) for c in components)
        first_parse = parse_version(version_str)
        reconstructed = ".".join(str(x) for x in first_parse)
        second_parse = parse_version(reconstructed)
        assert first_parse == second_parse

    @given(
        components=st.lists(version_component, min_size=1, max_size=3),
        suffix=st.sampled_from(["", "rc1", "a1", "b2", "alpha", "beta", "dev1"]),
    )
    def test_suffix_is_stripped_from_last_component(self, components: list[int], suffix: str):
        """Suffixes on the last component are stripped, keeping the numeric prefix."""
        parts = [str(c) for c in components]
        parts[-1] = parts[-1] + suffix  # Add suffix to last component
        version_str = ".".join(parts)
        result = parse_version(version_str)
        # The numeric values should be preserved
        assert result == tuple(components)

    @given(garbage=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    def test_non_numeric_prefix_raises_error(self, garbage: str):
        """Version components without numeric prefix raise VersionSpecifierError."""
        with pytest.raises(VersionSpecifierError):
            parse_version(garbage)


class TestSatisfiesProperties:
    """Property-based tests for satisfies function."""

    @given(v=valid_version_str)
    def test_reflexivity_equality(self, v: str):
        """A version always satisfies equality with itself."""
        assert satisfies(v, f"=={v}") is True

    @given(v=valid_version_str)
    def test_reflexivity_greater_or_equal(self, v: str):
        """A version always satisfies >= itself."""
        assert satisfies(v, f">={v}") is True

    @given(v=valid_version_str)
    def test_reflexivity_less_or_equal(self, v: str):
        """A version always satisfies <= itself."""
        assert satisfies(v, f"<={v}") is True

    @given(v=valid_version_str)
    def test_strict_inequality_never_satisfied_by_self(self, v: str):
        """A version never satisfies strict inequality with itself."""
        assert satisfies(v, f">{v}") is False
        assert satisfies(v, f"<{v}") is False

    @given(v=valid_version_str)
    def test_not_equal_to_self_is_false(self, v: str):
        """A version never satisfies != itself."""
        assert satisfies(v, f"!={v}") is False

    @given(v=valid_version_str, s=valid_version_str)
    def test_greater_equal_opposite_of_less_than(self, v: str, s: str):
        """V >= s is equivalent to not (v < s)."""
        assert satisfies(v, f">={s}") == (not satisfies(v, f"<{s}"))

    @given(v=valid_version_str, s=valid_version_str)
    def test_less_equal_opposite_of_greater_than(self, v: str, s: str):
        """V <= s is equivalent to not (v > s)."""
        assert satisfies(v, f"<={s}") == (not satisfies(v, f">{s}"))

    @given(v=valid_version_str, s=valid_version_str)
    def test_equal_opposite_of_not_equal(self, v: str, s: str):
        """V == s is equivalent to not (v != s)."""
        assert satisfies(v, f"=={s}") == (not satisfies(v, f"!={s}"))

    @given(v=valid_version_str, s=valid_version_str)
    def test_trichotomy(self, v: str, s: str):
        """Exactly one of <, ==, > holds for any two versions."""
        lt = satisfies(v, f"<{s}")
        eq = satisfies(v, f"=={s}")
        gt = satisfies(v, f">{s}")
        assert sum([lt, eq, gt]) == 1

    @given(v=valid_version_str, s1=valid_version_str, s2=valid_version_str)
    def test_conjunction_of_constraints(self, v: str, s1: str, s2: str):
        """Comma-separated constraints are a conjunction (AND)."""
        combined = satisfies(v, f">={s1},<={s2}")
        separate = satisfies(v, f">={s1}") and satisfies(v, f"<={s2}")
        assert combined == separate

    @given(
        major=st.integers(min_value=0, max_value=99),
        minor=st.integers(min_value=0, max_value=99),
    )
    def test_ordering_consistency(self, major: int, minor: int):
        """If v1 < v2, then satisfies reflects this ordering correctly."""
        v1 = f"{major}.{minor}"
        v2 = f"{major}.{minor + 1}"
        # v1 < v2 should always hold
        assert satisfies(v1, f"<{v2}") is True
        assert satisfies(v2, f">{v1}") is True
        assert satisfies(v1, f"<={v2}") is True
        assert satisfies(v2, f">={v1}") is True

    @given(v=valid_version_str, s=valid_version_str)
    @settings(max_examples=50)
    def test_whitespace_tolerance(self, v: str, s: str):
        """Whitespace around operators doesn't affect the result."""
        assert satisfies(v, f">={s}") == satisfies(v, f">= {s}")
        assert satisfies(v, f"<={s}") == satisfies(v, f"<= {s}")
