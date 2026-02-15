"""Stress tests for concurrent operations.

This module contains stress tests that exercise concurrent and parallel operations,
ensuring the system behaves correctly under concurrent load.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest


@pytest.mark.stress
class TestConcurrentOperationsStress:
    """Stress tests for concurrent operations."""

    def test_concurrent_computations(self):
        """Stress test: Run many computations concurrently."""

        def compute_fibonacci(n):
            """Compute nth Fibonacci number iteratively."""
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(n - 1):
                a, b = b, a + b
            return b

        # Run many Fibonacci calculations concurrently
        num_tasks = 100
        fib_n = 25

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(compute_fibonacci, fib_n) for _ in range(num_tasks)]
            results = [future.result() for future in as_completed(futures)]

        assert len(results) == num_tasks
        assert all(r == compute_fibonacci(fib_n) for r in results)

    def test_concurrent_list_operations(self):
        """Stress test: Concurrent list operations."""

        def process_list(list_id):
            """Process a list by creating, sorting, and summing it."""
            data = list(range(1000, 0, -1))
            sorted_data = sorted(data)
            result = sum(sorted_data)
            return list_id, result

        num_tasks = 50
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_list, i) for i in range(num_tasks)]
            results = dict(future.result() for future in as_completed(futures))

        assert len(results) == num_tasks
        expected_sum = sum(range(1, 1001))
        assert all(v == expected_sum for v in results.values())

    def test_concurrent_dictionary_operations(self):
        """Stress test: Concurrent dictionary operations."""

        def process_dict(dict_id):
            """Process a dictionary by creating, updating, and summing values."""
            data = {f"key_{i}": i for i in range(100)}
            # Update values
            for key in data:
                data[key] *= 2
            return dict_id, sum(data.values())

        num_tasks = 50
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_dict, i) for i in range(num_tasks)]
            results = dict(future.result() for future in as_completed(futures))

        assert len(results) == num_tasks
        expected_sum = sum(range(100)) * 2
        assert all(v == expected_sum for v in results.values())

    def test_concurrent_string_operations(self):
        """Stress test: Concurrent string operations."""

        def process_strings(string_id):
            """Process strings with various operations."""
            base = f"test_string_{string_id}"
            # Create many variations
            variations = [
                base.upper(),
                base.lower(),
                base.replace("_", "-"),
                base * 10,
            ]
            return string_id, len("".join(variations))

        num_tasks = 100
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_strings, i) for i in range(num_tasks)]
            results = dict(future.result() for future in as_completed(futures))

        assert len(results) == num_tasks
        # All results should be positive lengths
        assert all(v > 0 for v in results.values())

    def test_rapid_task_submission(self):
        """Stress test: Submit many tasks rapidly."""
        task_count = 200

        def simple_task(task_id):
            """Simple task that returns its ID."""
            return task_id * 2

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(simple_task, i) for i in range(task_count)]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()

        assert len(results) == task_count
        assert sorted(results) == [i * 2 for i in range(task_count)]
        # Ensure it completes in reasonable time (less than 5 seconds)
        assert end_time - start_time < 5.0
