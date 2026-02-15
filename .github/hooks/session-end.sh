#!/bin/bash
set -euo pipefail

# Session End Hook
# Runs quality gates after the agent finishes work.
#
# Usage: session-end.sh [--dry-run]
#   --dry-run: Show what quality gates would run without actually executing them

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
    echo "[copilot-hook] 🔍 DRY RUN MODE - No quality gates will be executed"
fi

echo "[copilot-hook] Running post-work quality gates..."

# Format code
echo "[copilot-hook] Formatting code..."
if [ "$DRY_RUN" = true ]; then
    echo "[copilot-hook] [DRY-RUN] Would run: make fmt"
elif ! make fmt; then
    echo "[copilot-hook] ❌ ERROR: Formatting check failed"
    echo "[copilot-hook] 💡 Remediation: Review the formatting errors above"
    echo "[copilot-hook] 💡 Common fixes:"
    echo "[copilot-hook]    - Run 'make fmt' locally to see detailed errors"
    echo "[copilot-hook]    - Check for syntax errors in modified files"
    echo "[copilot-hook]    - Ensure all files follow project style guidelines"
    exit 1
else
    echo "[copilot-hook] ✓ Code formatting passed"
fi

# Run tests
echo "[copilot-hook] Running tests..."
if [ "$DRY_RUN" = true ]; then
    echo "[copilot-hook] [DRY-RUN] Would run: make test"
elif ! make test; then
    echo "[copilot-hook] ❌ ERROR: Tests failed"
    echo "[copilot-hook] 💡 Remediation: Review the test failures above"
    echo "[copilot-hook] 💡 Common fixes:"
    echo "[copilot-hook]    - Run 'make test' locally to see detailed output"
    echo "[copilot-hook]    - Check if new code broke existing functionality"
    echo "[copilot-hook]    - Verify test assertions match expected behavior"
    echo "[copilot-hook]    - Review test logs in _tests/ directory"
    exit 1
else
    echo "[copilot-hook] ✓ Tests passed"
fi

if [ "$DRY_RUN" = true ]; then
    echo "[copilot-hook] 🔍 DRY RUN COMPLETE - No changes made"
else
    echo "[copilot-hook] ✅ All quality gates passed"
fi
