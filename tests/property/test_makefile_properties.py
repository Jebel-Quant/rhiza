"""Property-based tests for Makefile targets and operations.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

Uses Hypothesis to generate test cases that verify Makefile behavior with various inputs.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

@pytest.mark.property
@given(st.lists(st.integers() | st.floats(allow_nan=False, allow_infinity=False)))
def test_sort_correctness_using_properties(lst):
    result = sorted(lst)
    assert set(lst) == set(result)
    assert all(a <= b for a, b in zip(result, result[1:]))
