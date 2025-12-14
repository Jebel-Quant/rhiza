#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

${UV_BIN:=./bin/uv}
${UVX_BIN:=./bin/uvx}

# Set UV environment variables to avoid prompts and warnings
export UV_VENV_CLEAR=1
export UV_LINK_MODE=copy

# Make UV environment variables persistent for all sessions
echo "export UV_LINK_MODE=copy" >> ~/.bashrc
echo "export UV_VENV_CLEAR=1" >> ~/.bashrc
echo "export PATH=\"$PWD/bin:\$PATH\"" >> ~/.bashrc


make install

# Install Marimo tool for notebook editing
${UV_BIN} tool install marimo 

# Initialize pre-commit hooks if configured
if [ -f .pre-commit-config.yaml ]; then
  # uvx runs tools without requiring them in the project deps
  ${UVX_BIN} pre-commit install
fi
