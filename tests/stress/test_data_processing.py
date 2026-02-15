"""Stress tests for data processing operations.

This module contains stress tests that exercise data processing and manipulation
operations under load, testing the system's ability to handle large datasets
and intensive computations.
"""

from __future__ import annotations

import pytest


@pytest.mark.stress
class TestDataProcessingStress:
    """Stress tests for data processing operations."""

    def test_large_list_processing(self):
        """Stress test: Process large lists."""
        # Create a large list
        size = 100_000
        data = list(range(size))

        # Perform various operations
        doubled = [x * 2 for x in data]
        filtered = [x for x in doubled if x % 3 == 0]
        summed = sum(filtered)

        assert len(doubled) == size
        assert len(filtered) > 0
        assert summed > 0

    def test_nested_list_operations(self):
        """Stress test: Process nested lists."""
        # Create nested lists
        size = 100
        nested = [[i * j for j in range(size)] for i in range(size)]

        # Flatten and process
        flattened = [item for sublist in nested for item in sublist]
        total = sum(flattened)

        assert len(flattened) == size * size
        assert total > 0

    def test_dict_comprehensions(self):
        """Stress test: Create and process large dictionaries."""
        size = 50_000
        # Create dictionary
        data = {f"key_{i}": i * 2 for i in range(size)}

        # Process dictionary
        filtered = {k: v for k, v in data.items() if v % 4 == 0}
        values_sum = sum(filtered.values())

        assert len(data) == size
        assert len(filtered) > 0
        assert values_sum > 0

    def test_set_operations(self):
        """Stress test: Set operations on large datasets."""
        size = 50_000
        set1 = set(range(0, size, 2))  # Even numbers
        set2 = set(range(0, size, 3))  # Multiples of 3

        # Perform set operations
        union = set1 | set2
        intersection = set1 & set2
        difference = set1 - set2

        assert len(set1) == size // 2
        assert len(set2) > 0
        assert len(union) > len(set1)
        assert len(intersection) > 0
        assert len(difference) > 0

    def test_string_manipulation(self):
        """Stress test: String manipulation operations."""
        # Create many strings
        num_strings = 10_000
        strings = [f"test_string_{i}" for i in range(num_strings)]

        # Perform various string operations
        upper = [s.upper() for s in strings]
        joined = "-".join(strings[:1000])  # Join subset to avoid memory issues
        split = joined.split("-")

        assert len(upper) == num_strings
        assert len(joined) > num_strings
        assert len(split) == 1000  # Splitting by "-" should give us back 1000 strings

    def test_sorting_large_lists(self):
        """Stress test: Sort large lists with different data types."""
        size = 50_000

        # Sort integers
        int_list = list(range(size, 0, -1))
        sorted_ints = sorted(int_list)
        assert sorted_ints[0] == 1
        assert sorted_ints[-1] == size

        # Sort strings
        str_list = [f"item_{i:06d}" for i in range(size, 0, -1)]
        sorted_strs = sorted(str_list)
        assert sorted_strs[0] == "item_000001"
        assert sorted_strs[-1] == f"item_{size:06d}"

    def test_filtering_operations(self):
        """Stress test: Filter large datasets with complex conditions."""
        size = 100_000
        data = list(range(size))

        # Apply multiple filters
        filtered1 = [x for x in data if x % 2 == 0]
        filtered2 = [x for x in filtered1 if x % 3 == 0]
        filtered3 = [x for x in filtered2 if x % 5 == 0]

        assert len(filtered1) == size // 2
        assert len(filtered2) < len(filtered1)
        assert len(filtered3) < len(filtered2)
        assert all(x % 30 == 0 for x in filtered3)

    def test_aggregation_operations(self):
        """Stress test: Aggregate large datasets."""
        size = 50_000
        data = list(range(1, size + 1))

        # Perform various aggregations
        total = sum(data)
        maximum = max(data)
        minimum = min(data)
        average = total / len(data)

        assert total == (size * (size + 1)) // 2  # Sum formula
        assert maximum == size
        assert minimum == 1
        assert average == (size + 1) / 2
