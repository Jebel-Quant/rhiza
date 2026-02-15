#!/bin/bash
set -euo pipefail

# Session Start Hook
# Validates that the environment is correctly set up before the agent begins work.
# The virtual environment should already be activated via copilot-setup-steps.yml.
#
# Usage: session-start.sh [--dry-run]
#   --dry-run: Show what would be validated without actually checking

DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
    echo "[copilot-hook] 🔍 DRY RUN MODE - No actual validation will be performed"
fi

echo "[copilot-hook] Validating environment..."

# Verify uv is available
if [ "$DRY_RUN" = true ]; then
    echo "[copilot-hook] [DRY-RUN] Would check: uv command availability"
elif ! command -v uv >/dev/null 2>&1 && [ ! -x "./bin/uv" ]; then
    echo "[copilot-hook] ❌ ERROR: uv not found"
    echo "[copilot-hook] 💡 Remediation: Run 'make install' to set up the environment"
    echo "[copilot-hook] 💡 Alternative: Ensure uv is in PATH or ./bin/uv exists"
    exit 1
else
    echo "[copilot-hook] ✓ uv is available"
fi

# Verify virtual environment exists
if [ "$DRY_RUN" = true ]; then
    echo "[copilot-hook] [DRY-RUN] Would check: .venv directory existence"
elif [ ! -d ".venv" ]; then
    echo "[copilot-hook] ❌ ERROR: .venv not found"
    echo "[copilot-hook] 💡 Remediation: Run 'make install' to create the virtual environment"
    echo "[copilot-hook] 💡 Details: The .venv directory should contain Python dependencies"
    exit 1
else
    echo "[copilot-hook] ✓ Virtual environment exists"
fi

# Verify virtual environment is on PATH (activated via copilot-setup-steps.yml)
if [ "$DRY_RUN" = true ]; then
    echo "[copilot-hook] [DRY-RUN] Would check: Python is from .venv"
elif ! command -v python >/dev/null 2>&1 || [[ "$(command -v python)" != *".venv"* ]]; then
    echo "[copilot-hook] ⚠️  WARNING: .venv/bin is not on PATH"
    echo "[copilot-hook] 💡 Note: The agent may not use the correct Python version"
    echo "[copilot-hook] 💡 Remediation: Ensure .venv/bin is added to PATH before running the agent"
else
    echo "[copilot-hook] ✓ Virtual environment is activated"
fi

if [ "$DRY_RUN" = true ]; then
    echo "[copilot-hook] 🔍 DRY RUN COMPLETE - No changes made"
else
    echo "[copilot-hook] ✅ Environment validated successfully"
fi
