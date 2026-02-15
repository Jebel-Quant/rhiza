"""Stress tests for file operations.

This module contains stress tests that exercise file I/O operations under load,
simulating scenarios where the system needs to handle many file operations
concurrently or in rapid succession.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.mark.stress
class TestFileOperationsStress:
    """Stress tests for file operations."""

    def test_many_file_reads(self):
        """Stress test: Read many files repeatedly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create test files
            num_files = 100
            for i in range(num_files):
                file_path = tmppath / f"test_{i}.txt"
                file_path.write_text(f"Content {i}" * 100)

            # Read all files multiple times
            iterations = 50
            for _ in range(iterations):
                for i in range(num_files):
                    file_path = tmppath / f"test_{i}.txt"
                    content = file_path.read_text()
                    assert len(content) > 0

    def test_many_file_writes(self):
        """Stress test: Write many files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            num_files = 500
            for i in range(num_files):
                file_path = tmppath / f"test_{i}.txt"
                file_path.write_text(f"Content for file {i}")
                assert file_path.exists()

    def test_rapid_file_creation_deletion(self):
        """Stress test: Rapidly create and delete files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            iterations = 100
            for i in range(iterations):
                file_path = tmppath / f"temp_{i}.txt"
                # Create
                file_path.write_text(f"Temporary content {i}")
                assert file_path.exists()
                # Delete
                file_path.unlink()
                assert not file_path.exists()

    def test_large_file_operations(self):
        """Stress test: Handle large file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create a large file (approximately 10MB of text)
            large_content = "x" * (10 * 1024 * 1024)
            file_path = tmppath / "large_file.txt"
            file_path.write_text(large_content)

            # Read it back multiple times
            for _ in range(10):
                content = file_path.read_text()
                assert len(content) == len(large_content)

    def test_nested_directory_operations(self):
        """Stress test: Create and manage nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            depth = 10
            num_files_per_level = 5

            # Create nested structure
            current = tmppath
            for level in range(depth):
                current = current / f"level_{level}"
                current.mkdir()
                for i in range(num_files_per_level):
                    file_path = current / f"file_{i}.txt"
                    file_path.write_text(f"Level {level}, File {i}")

            # Verify structure
            current = tmppath
            for level in range(depth):
                current = current / f"level_{level}"
                assert current.exists()
                for i in range(num_files_per_level):
                    file_path = current / f"file_{i}.txt"
                    assert file_path.exists()
