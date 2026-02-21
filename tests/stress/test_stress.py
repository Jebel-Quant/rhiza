"""Stress tests for rhiza.

Examples covering concurrent operations, data processing, and file I/O under load.
"""

from __future__ import annotations

import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest


@pytest.mark.stress
class TestStress:
    """Stress tests covering concurrent operations, data processing, and file I/O."""

    def test_concurrent_computations(self):
        """Run many Fibonacci calculations concurrently."""

        def compute_fibonacci(n):
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(n - 1):
                a, b = b, a + b
            return b

        num_tasks = 100
        fib_n = 25
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(compute_fibonacci, fib_n) for _ in range(num_tasks)]
            results = [f.result() for f in as_completed(futures)]

        assert len(results) == num_tasks
        assert all(r == compute_fibonacci(fib_n) for r in results)

    def test_rapid_task_submission(self):
        """Submit many tasks rapidly and verify throughput."""
        task_count = 200

        start = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(lambda i=i: i * 2, i) for i in range(task_count)]
            results = [f.result() for f in as_completed(futures)]
        elapsed = time.time() - start

        assert len(results) == task_count
        assert sorted(results) == [i * 2 for i in range(task_count)]
        assert elapsed < 5.0

    def test_large_list_processing(self):
        """Process a large list with chained transformations."""
        size = 100_000
        data = list(range(size))
        doubled = [x * 2 for x in data]
        filtered = [x for x in doubled if x % 3 == 0]
        summed = sum(filtered)

        assert len(doubled) == size
        assert len(filtered) > 0
        assert summed > 0

    def test_set_operations(self):
        """Perform set operations on large datasets."""
        size = 50_000
        set1 = set(range(0, size, 2))
        set2 = set(range(0, size, 3))

        union = set1 | set2
        intersection = set1 & set2
        difference = set1 - set2

        assert len(union) > len(set1)
        assert len(intersection) > 0
        assert len(difference) > 0

    def test_large_file_operations(self):
        """Write and repeatedly read a large file (~10 MB)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            large_content = "x" * (10 * 1024 * 1024)
            file_path = Path(tmpdir) / "large_file.txt"
            file_path.write_text(large_content)

            for _ in range(10):
                content = file_path.read_text()
                assert len(content) == len(large_content)
