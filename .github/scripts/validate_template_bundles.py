#!/usr/bin/env python3
"""
Validate that all files and folders referenced in template-bundles.yml exist.

This script:
1. Parses .rhiza/template-bundles.yml
2. Extracts all file paths from each bundle
3. Checks if each path exists in the repository
4. Reports any missing files/folders and exits with error code if any are missing
"""

import sys
from pathlib import Path

import yaml


def main():
    """Main validation logic."""
    # Path to the template bundles file
    bundles_file = Path(".rhiza/template-bundles.yml")

    if not bundles_file.exists():
        print(f"❌ ERROR: {bundles_file} does not exist!")
        sys.exit(1)

    print(f"📋 Validating file paths in {bundles_file}...")
    print()

    # Load the YAML file
    with open(bundles_file) as f:
        data = yaml.safe_load(f)

    if not data or "bundles" not in data:
        print("❌ ERROR: Invalid template-bundles.yml format - missing 'bundles' key")
        sys.exit(1)

    bundles = data["bundles"]
    all_missing = []
    total_files = 0

    # Check each bundle
    for bundle_name, bundle_config in bundles.items():
        if "files" not in bundle_config:
            continue

        files = bundle_config["files"]
        missing_in_bundle = []

        for file_path in files:
            total_files += 1
            path = Path(file_path)

            if not path.exists():
                missing_in_bundle.append(file_path)
                all_missing.append((bundle_name, file_path))

        if missing_in_bundle:
            print(f"❌ Bundle '{bundle_name}' has {len(missing_in_bundle)} missing path(s):")
            for missing in missing_in_bundle:
                print(f"   - {missing}")
            print()

    # Report results
    print("=" * 70)
    print(f"Total files/folders checked: {total_files}")
    print(f"Missing files/folders: {len(all_missing)}")
    print("=" * 70)

    if all_missing:
        print()
        print("❌ VALIDATION FAILED")
        print()
        print("The following files/folders are referenced in template-bundles.yml")
        print("but do not exist in the repository:")
        print()
        for bundle_name, file_path in all_missing:
            print(f"  [{bundle_name}] {file_path}")
        print()
        sys.exit(1)
    else:
        print()
        print("✅ VALIDATION PASSED")
        print("All files and folders referenced in template-bundles.yml exist!")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
