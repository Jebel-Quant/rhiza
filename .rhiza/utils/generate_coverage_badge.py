#!/usr/bin/env python3
"""Generate a coverage badge endpoint JSON for shields.io.

This script reads _tests/coverage.json and creates a shields.io endpoint JSON file
at _book/tests/coverage-badge.json.
"""

import json
import sys
from pathlib import Path

import typer
from typer import Option


def get_badge_color(coverage: float) -> str:
    """Determine badge color based on coverage percentage.

    Args:
        coverage: Coverage percentage (0-100)

    Returns:
        str: Color name for shields.io badge
    """
    if coverage >= 90:
        return "brightgreen"
    elif coverage >= 80:
        return "green"
    elif coverage >= 70:
        return "yellowgreen"
    elif coverage >= 60:
        return "yellow"
    elif coverage >= 50:
        return "orange"
    else:
        return "red"


def generate_coverage_badge(
    coverage_json_path: Path = Path("_tests/coverage.json"),
    output_path: Path = Path("_book/tests/coverage-badge.json"),
) -> None:
    """Generate coverage badge JSON from coverage report.

    Args:
        coverage_json_path: Path to the coverage.json file
        output_path: Path where the badge JSON should be written

    Raises:
        SystemExit: If the coverage JSON is invalid or missing required data
    """
    # Check if coverage.json exists
    if not coverage_json_path.exists():
        print(
            f"[WARN] Coverage JSON file not found at {coverage_json_path}, skipping badge generation",
            file=sys.stderr,
        )
        return

    print(f"[INFO] Generating coverage badge from {coverage_json_path}...")

    # Read and parse coverage data
    try:
        with coverage_json_path.open("r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse coverage JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract coverage percentage
    try:
        percent = data["totals"]["percent_covered"]
    except KeyError as e:
        print(f"[ERROR] Missing expected key in coverage JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Round to nearest integer
    coverage = round(percent)

    if not 0 <= coverage <= 100:
        print(f"[ERROR] Coverage percentage {coverage} is out of valid range 0-100", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Coverage: {coverage}%")

    # Determine badge color
    color = get_badge_color(coverage)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate shields.io endpoint JSON
    badge_data = {
        "schemaVersion": 1,
        "label": "coverage",
        "message": f"{coverage}%",
        "color": color,
    }

    with output_path.open("w") as f:
        json.dump(badge_data, f, indent=2)
        f.write("\n")  # Add trailing newline

    print(f"[INFO] Coverage badge JSON generated at {output_path}")


def cli_main(
    coverage_json: Path = Option(
        Path("_tests/coverage.json"),
        "--coverage-json",
        help="Path to coverage.json file",
    ),
    output: Path = Option(
        Path("_book/tests/coverage-badge.json"),
        "--output",
        help="Path to output badge JSON",
    ),
) -> None:
    """Generate coverage badge endpoint JSON for shields.io."""
    try:
        generate_coverage_badge(coverage_json, output)
    except OSError as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app = typer.Typer()
    app.command()(cli_main)
    app()
