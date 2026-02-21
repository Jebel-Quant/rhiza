"""Blueprint property-based tests for downstream repositories.

This module contains example property-based tests using Hypothesis.
It intentionally exercises generic Python behaviour (e.g. list sorting)
rather than any Rhiza-specific logic, and serves as a **starting-point
blueprint** for downstream projects.

The Rhiza project's own tests live in ``.rhiza/tests/``.

Uses Hypothesis to generate test cases that verify behaviour across a
wide range of inputs.
"""

from __future__ import annotations

import itertools
from collections import Counter

import pytest
from hypothesis import given
from hypothesis import strategies as st


@pytest.mark.property
@given(st.lists(st.integers() | st.floats(allow_nan=False, allow_infinity=False)))
def test_sort_correctness_using_properties(lst):
    """Verify that sorted() correctly orders lists and preserves all elements."""
    result = sorted(lst)
    # Use Counter to ensure multiplicities (duplicates) are preserved
    assert Counter(lst) == Counter(result)
    assert all(a <= b for a, b in itertools.pairwise(result))
