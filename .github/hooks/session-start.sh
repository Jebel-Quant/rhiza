#!/bin/bash
set -euo pipefail

# Session Start Hook
# Validates that the environment is correctly set up before the agent begins work.

echo "[copilot-hook] Validating environment..."

# Verify uv is available
if ! command -v uv >/dev/null 2>&1 && [ ! -x "./bin/uv" ]; then
    echo "[copilot-hook] ERROR: uv not found. Run 'make install' to set up the environment."
    exit 1
fi

# Verify virtual environment exists
if [ ! -d ".venv" ]; then
    echo "[copilot-hook] ERROR: .venv not found. Run 'make install' to set up the environment."
    exit 1
fi

echo "[copilot-hook] Environment validated successfully."
