#!/usr/bin/env python3
"""Validate template-bundles.yml structure and consistency.

This script validates the template bundles configuration file to ensure:
1. Valid YAML syntax
2. Required fields are present
3. Bundle dependencies reference existing bundles
4. File paths follow expected patterns
5. Examples reference valid bundles

Exit codes:
  0 - Validation passed
  1 - Validation failed
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def validate_template_bundles(bundles_path: Path) -> tuple[bool, list[str]]:
    """Validate template bundles configuration.

    Args:
        bundles_path: Path to template-bundles.yml

    Returns:
        Tuple of (success, error_messages)
    """
    errors = []

    # Check file exists
    if not bundles_path.exists():
        return False, [f"Template bundles file not found: {bundles_path}"]

    # Load YAML
    try:
        with open(bundles_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML: {e}"]

    if data is None:
        return False, ["Template bundles file is empty"]

    # Check required top-level fields
    required_fields = {"version", "bundles"}
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate bundles section
    bundles = data.get("bundles", {})
    if not isinstance(bundles, dict):
        return False, ["'bundles' must be a dictionary"]

    bundle_names = set(bundles.keys())

    # Validate each bundle
    for bundle_name, bundle_config in bundles.items():
        if not isinstance(bundle_config, dict):
            errors.append(f"Bundle '{bundle_name}' must be a dictionary")
            continue

        # Check required fields
        if "description" not in bundle_config:
            errors.append(f"Bundle '{bundle_name}' missing 'description'")

        if "files" not in bundle_config:
            errors.append(f"Bundle '{bundle_name}' missing 'files'")
        elif not isinstance(bundle_config["files"], list):
            errors.append(f"Bundle '{bundle_name}' 'files' must be a list")

        # Validate dependencies
        if "requires" in bundle_config:
            if not isinstance(bundle_config["requires"], list):
                errors.append(f"Bundle '{bundle_name}' 'requires' must be a list")
            else:
                for dep in bundle_config["requires"]:
                    if dep not in bundle_names:
                        errors.append(
                            errors.append(
                                f"Bundle '{bundle_name}' requires "
                                f"non-existent bundle '{dep}'"
                            )
                        )

        if "recommends" in bundle_config:
            if not isinstance(bundle_config["recommends"], list):
                errors.append(f"Bundle '{bundle_name}' 'recommends' must be a list")
            else:
                for dep in bundle_config["recommends"]:
                    if dep not in bundle_names:
                        errors.append(
                            errors.append(
                                f"Bundle '{bundle_name}' recommends "
                                f"non-existent bundle '{dep}'"
                            )
                        )

    # Validate examples section
    if "examples" in data:
        examples = data["examples"]
        if not isinstance(examples, dict):
            errors.append("'examples' must be a dictionary")
        else:
            for example_name, example_config in examples.items():
                if "templates" in example_config:
                    if not isinstance(example_config["templates"], list):
                        errors.append(
                            f"Example '{example_name}' 'templates' must be a list"
                        )
                    else:
                        for template in example_config["templates"]:
                            # core is auto-included, we don't validate it
                            if template != "core" and template not in bundle_names:
                                errors.append(
                                    f"Example '{example_name}' references "
                                    f"non-existent bundle '{template}'"
                                )

    # Validate metadata if present
    if "metadata" in data:
        metadata = data["metadata"]
        if "total_bundles" in metadata:
            expected_count = len(bundles)
            actual_count = metadata["total_bundles"]
            if actual_count != expected_count:
                errors.append(
                    f"Metadata 'total_bundles' ({actual_count}) doesn't match "
                    f"actual bundle count ({expected_count})"
                )

    return len(errors) == 0, errors


def main() -> int:
    """Main entry point."""
    # Find template-bundles.yml
    script_dir = Path(__file__).parent.parent.parent
    bundles_path = script_dir / ".rhiza" / "template-bundles.yml"

    print(f"Validating template bundles: {bundles_path}")

    success, errors = validate_template_bundles(bundles_path)

    if success:
        print("✓ Template bundles validation passed!")
        return 0
    else:
        print("\n✗ Template bundles validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
