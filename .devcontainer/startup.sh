#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${script_dir}/bootstrap.sh"

echo "🚀 Generic Python .devcontainer environment ready!"
echo "🔧 Pre-commit hooks installed for code quality, run 'make fmt' for formatting and linting!"
echo "📓 Marimo installed for notebook editing!"

uv run marimo --yes edit --host=localhost --port=8080 --headless --no-token || echo '⚠️ Marimo failed to start'"
