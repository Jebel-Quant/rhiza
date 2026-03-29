# GitHub Actions

This directory contains GitHub Actions workflows and supporting configuration.

## GitHub Token

Workflows that create pull requests (e.g. `sync.yml`) require a token with write access. Set the `GH_TOKEN` secret in your repository settings to a Personal Access Token or a GitHub App token with `contents: write` and `pull-requests: write` permissions.
