"""Stress tests for file system operations.

Tests file system operations under heavy load to verify stability
and proper resource cleanup.
"""

from __future__ import annotations

import concurrent.futures
import tempfile
from pathlib import Path

import pytest


@pytest.mark.stress
def test_rapid_file_creation_deletion(stress_iterations: int):
    """Test rapid file creation and deletion cycles.
    
    Verifies that rapid file operations don't leak file handles or
    cause file system issues.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        results = []
        
        for i in range(stress_iterations):
            test_file = tmp_path / f"test_{i}.txt"
            try:
                # Create file
                test_file.write_text(f"Test content {i}")
                assert test_file.exists()
                
                # Delete file
                test_file.unlink()
                assert not test_file.exists()
                
                results.append(True)
            except Exception:
                results.append(False)
        
        success_rate = sum(results) / len(results)
        assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_concurrent_file_operations(concurrent_workers: int):
    """Test concurrent file creation and deletion.
    
    Verifies that concurrent file operations in separate directories
    don't cause conflicts.
    """
    
    def file_operation_sequence(worker_id: int):
        """Create and delete files in a worker-specific directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            for i in range(10):
                test_file = tmp_path / f"worker_{worker_id}_file_{i}.txt"
                test_file.write_text(f"Worker {worker_id}, file {i}")
                content = test_file.read_text()
                test_file.unlink()
                if content != f"Worker {worker_id}, file {i}":
                    return False
            return True
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(file_operation_sequence, i) for i in range(concurrent_workers)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_directory_traversal_stress(root: Path, stress_iterations: int):
    """Test repeated directory traversal operations.
    
    Verifies that repeated directory walks don't cause issues or
    degraded performance.
    """
    results = []
    
    for _ in range(stress_iterations):
        try:
            # Walk the repository directory
            file_count = sum(1 for _ in root.rglob("*.py"))
            # Verify we found at least some Python files
            results.append(file_count > 0)
        except Exception:
            results.append(False)
    
    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_bulk_file_existence_checks(concurrent_workers: int):
    """Test bulk file existence checking under concurrent load.
    
    Verifies that many concurrent file existence checks don't cause
    file system issues.
    """
    
    def check_files(file_paths: list[Path]):
        """Check existence of multiple files."""
        try:
            results = [path.exists() for path in file_paths]
            # All checked files should either exist or not (no errors)
            return len(results) == len(file_paths)
        except Exception:
            return False
    
    # Create a list of important project files to check
    test_files = [
        Path(".rhiza/rhiza.mk"),
        Path("Makefile"),
        Path("pyproject.toml"),
        Path("README.md"),
        Path(".python-version"),
        Path(".gitignore"),
    ]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(check_files, test_files) for _ in range(concurrent_workers * 10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_large_file_operations(stress_iterations: int):
    """Test operations with larger files.
    
    Verifies that operations with larger files (simulating template content)
    work correctly under repeated execution.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        results = []
        
        # Create content simulating a larger template file (~1MB)
        large_content = "# Template content\n" * 50000
        
        for i in range(stress_iterations // 10):  # Reduce iterations for large files
            test_file = tmp_path / f"large_file_{i}.txt"
            try:
                # Write large file
                test_file.write_text(large_content)
                
                # Read and verify
                content = test_file.read_text()
                assert len(content) == len(large_content)
                
                # Delete
                test_file.unlink()
                
                results.append(True)
            except Exception:
                results.append(False)
        
        success_rate = sum(results) / len(results)
        assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"
