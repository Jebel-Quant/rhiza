"""Tests for the JSON Schema that validates .rhiza/template-bundles.yml.

The schema is enforced at commit time by the ``check-jsonschema`` pre-commit hook.
These tests guard the schema file and its wiring so the enforcement cannot silently
disappear, and confirm the live bundle definitions still satisfy its core rules.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA = _ROOT / ".rhiza" / "template-bundles.schema.json"
_BUNDLES = _ROOT / ".rhiza" / "template-bundles.yml"


def test_schema_file_is_valid_json() -> None:
    """The template-bundles schema must exist and be parseable JSON Schema."""
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    assert schema.get("$schema"), "schema must declare a $schema dialect"
    assert "bundles" in schema["properties"], "schema must describe the 'bundles' mapping"
    assert "bundles" in schema.get("required", []), "'bundles' must be a required top-level key"


def test_precommit_wires_the_schema() -> None:
    """The check-jsonschema hook must reference the schema so enforcement stays active."""
    config = (_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "template-bundles.schema.json" in config, (
        "pre-commit config must wire check-jsonschema to template-bundles.schema.json"
    )


def test_live_bundles_satisfy_required_schema_rules() -> None:
    """The shipped template-bundles.yml must satisfy the schema's required structure."""
    data = yaml.safe_load(_BUNDLES.read_text(encoding="utf-8"))

    bundles = data["bundles"]
    assert bundles, "at least one bundle must be defined"
    for name, spec in bundles.items():
        description = spec.get("description")
        assert isinstance(description, str), f"bundle {name!r} description must be a string"
        assert description, f"bundle {name!r} must have a non-empty description"
        for key in ("requires", "recommends"):
            if key in spec:
                assert isinstance(spec[key], list), f"bundle {name!r} {key} must be a list"

    for name, spec in data.get("profiles", {}).items():
        description = spec.get("description")
        assert isinstance(description, str), f"profile {name!r} description must be a string"
        assert description, f"profile {name!r} must have a non-empty description"
        profile_bundles = spec.get("bundles")
        assert isinstance(profile_bundles, list), f"profile {name!r} bundles must be a list"
        assert profile_bundles, f"profile {name!r} must list at least one bundle"
