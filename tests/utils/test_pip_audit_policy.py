"""Unit tests for .rhiza/utils/pip_audit_policy.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace


def _load_module(root: Path):
    module_path = root / ".rhiza" / "utils" / "pip_audit_policy.py"
    spec = importlib.util.spec_from_file_location("pip_audit_policy", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["pip_audit_policy"] = module
    spec.loader.exec_module(module)
    return module


def test_vuln_ids_deduplicates_primary_id(root) -> None:
    """The primary vulnerability ID should not be duplicated when also present as an alias."""
    module = _load_module(root)
    vuln = {"id": "CVE-2024-0001", "aliases": ["GHSA-aaaa", "CVE-2024-0001"]}

    assert module._vuln_ids(vuln) == "CVE-2024-0001, GHSA-aaaa"


def test_main_returns_zero_for_tooling_only_vulns(root, monkeypatch) -> None:
    """Tooling-only vulnerabilities should warn but not fail."""
    module = _load_module(root)
    payload = json.dumps(
        {
            "dependencies": [
                {
                    "name": "pip",
                    "version": "24.0",
                    "vulns": [{"id": "PYSEC-1", "aliases": []}],
                }
            ]
        }
    )

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout=payload, stderr=""),
    )
    monkeypatch.setattr(module.sys, "argv", ["pip_audit_policy.py"])

    assert module.main() == 0


def test_main_returns_one_for_runtime_vulns(root, monkeypatch) -> None:
    """Runtime dependency vulnerabilities should fail."""
    module = _load_module(root)
    payload = json.dumps(
        {
            "dependencies": [
                {
                    "name": "requests",
                    "version": "1.0",
                    "vulns": [{"id": "PYSEC-2", "aliases": ["CVE-2024-9999"]}],
                }
            ]
        }
    )

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout=payload, stderr=""),
    )
    monkeypatch.setattr(module.sys, "argv", ["pip_audit_policy.py"])

    assert module.main() == 1
