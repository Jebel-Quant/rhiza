# GitHub Actions Configuration

This document describes the secrets used by the Rhiza-provided GitHub Actions workflows
(`.github/workflows/rhiza_*.yml`) and how to configure them.

## PAT_TOKEN

Some workflows may need to push changes to files under `.github/workflows/`. The
automatic `github.token` **cannot** do that — GitHub rejects such pushes unless
the token carries the `workflow` scope. If you need it, create a Personal Access
Token (PAT) with the `workflow` scope and store it as a repository secret named
`PAT_TOKEN`.

If `PAT_TOKEN` is not configured, workflows fall back to `github.token`.

### Creating the token

**Fine-grained PAT** (recommended):

1. Go to **Settings → Developer settings → Fine-grained tokens → Generate new token**
   (<https://github.com/settings/personal-access-tokens/new>).
2. Restrict **Repository access** to the repository (or repositories) using Rhiza.
3. Under **Repository permissions**, grant:
   - **Contents**: Read and write
   - **Workflows**: Read and write
   - **Pull requests**: Read and write (needed for the scheduled sync-PR mode)
4. Generate the token and copy it.

**Classic PAT** (alternative):

1. Go to **Settings → Developer settings → Tokens (classic) → Generate new token**.
2. Select the `repo` and `workflow` scopes.
3. Generate the token and copy it.

### Storing the secret

In the repository that consumes Rhiza:

1. Go to **Settings → Secrets and variables → Actions → New repository secret**.
2. Name: `PAT_TOKEN`
3. Value: the token created above.

Or with the GitHub CLI:

```bash
gh secret set PAT_TOKEN
```

A PAT expires; when sync pushes start failing with a `refusing to allow ... workflow` error,
regenerate the token and update the secret.

## Release workflow secrets (optional)

The release workflow (`.github/workflows/rhiza_release.yml`) supports additional secrets, all
optional depending on which release features you use:

| Secret | Purpose |
| --- | --- |
| `PYPI_TOKEN` | Publish the built package to PyPI. Not needed when using trusted publishing (OIDC). |
| `RELEASE_PUBLISH_CREDENTIALS` | Optional credentials input for a repository-owned custom publisher. Not needed when the extension uses OIDC. |
| `GH_PAT` | Git authentication for installing private dependencies during the release build. |
| `UV_EXTRA_INDEX_URL` | Extra package index URL (with credentials) for private dependencies. |

`GITHUB_TOKEN` is provided automatically by GitHub Actions and needs no configuration.

## Release publisher selection

Set the Actions **variable** `RELEASE_PUBLISHER` to choose package deployment:

| Value | Behaviour |
| --- | --- |
| Unset or `pypi` | Existing PyPI Trusted Publishing. `PYPI_REPOSITORY_URL` (variable) and `PYPI_TOKEN` (secret) still support PyPI-compatible custom endpoints. |
| `custom` | Run your repository-owned composite action at `.github/actions/release-publish/action.yml` (or `action.yaml`). No fallback to public PyPI. |
| `none` | Skip package publishing, retaining the other release outputs. |

Rhiza never syncs the custom action path. Commit the action before tagging the release;
it runs from that release revision with the `release` environment, `contents: read` and
`id-token: write`. It receives `artifacts-dir` (absolute path to the downloaded build
artifacts), `tag`, `version` (tag without `v`) and the optional `credentials` input.
It owns provider login, tool setup and upload, and must fail on unsuccessful publication.
Use the existing distributions rather than rebuilding them; the directory can also
contain provenance files.

For OIDC-capable feeds, obtain and immediately mask short-lived credentials in this
action. Otherwise, supply the optional `RELEASE_PUBLISH_CREDENTIALS` secret in the
format your action expects. Only that explicit secret is forwarded to the extension.
An optional `artifact-url` output supplies a public HTTPS artifact link for release notes;
omit it for private destinations and never include credentials or signed access tokens.

The private-package classifier still suppresses built-in PyPI uploads; `custom`
explicitly permits private distributions. Invalid modes, missing custom actions and
missing expected distributions fail closed. Failed required uploads prevent release
finalization. Conda recipes are generated only after successful public PyPI publication
with no `PYPI_REPOSITORY_URL` override.

This is a GitHub publishing extension, not private dependency-consumption setup or a
GitLab feature. See the
[publisher contract](https://jebel-quant.github.io/rhiza/reference/ARCHITECTURE/#repository-owned-publishing-action)
for details.
