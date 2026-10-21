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

## Consumer setup and publishing

| Setting | Purpose |
| --- | --- |
| `RHIZA_SETUP_ENABLED` variable | Set to `true` to run your `.github/actions/rhiza-setup` action before dependency resolution in supported jobs. |
| `RHIZA_SETUP_CREDENTIALS` secret | Optional opaque credential passed only to that setup action. Omit when using OIDC. |
| `RELEASE_PUBLISHER` variable | Set to `custom` to run your `.github/actions/release-publish` action. Unset or `none` disables package uploads. |
| `RELEASE_PUBLISH_CREDENTIALS` secret | Optional opaque credential passed only to the publishing action. |

Setup receives `purpose` and `credentials` inputs and non-secret variables as JSON in
`RHIZA_SETUP_VARS`. Publishing receives `artifacts-dir`, `tag`, `version`, `credentials`,
and non-secret variables as JSON in `RHIZA_RELEASE_PUBLISH_VARS`. Neither consumer action
is template-owned. Commit them before releasing; publisher code is loaded from the release
tag. Missing configured actions and failed setup/uploads fail closed. Failed publication
leaves the release draft. OIDC callers must grant `id-token: write`.

PyPI is an optional implementation of the same publishing contract. Copy
`examples/publishing/pypi/action.yml` from Rhiza into your publishing action path and select
`custom`. For Trusted Publishing, use the directly triggered release workflow; PyPA does
not support OIDC publishing inside reusable workflows. Reusable callers can pass a PyPI
API token through `RELEASE_PUBLISH_CREDENTIALS` instead. The example rejects private-package
metadata and excludes provenance files from uploads.

**Migration:** implicit PyPI publishing and `RELEASE_PUBLISHER=pypi` have been removed.
Adopt the example and select `custom` before upgrading. Move `PYPI_TOKEN` to
`RELEASE_PUBLISH_CREDENTIALS`; put any custom endpoint configuration inside your own action.
There is no fallback upload destination. Existing `custom` publishers retain their inputs.

For AWS private dependencies, copy `examples/dependency-setup/codeartifact/action.yml`
into your setup action path and set `RHIZA_SETUP_ENABLED=true`. All AWS settings and token
handling live in that consumer action, outside reusable workflows. The former
`CODEARTIFACT_CONSUMPTION_ENABLED` switch is replaced by this generic opt-in.
Setup refuses fork pull requests and `pull_request_target`. Container builds need separate
BuildKit secret forwarding.

See the [extension contract](https://jebel-quant.github.io/rhiza/reference/ARCHITECTURE/#consumer-owned-setup-and-publishing)
for configuration, example requirements, output contracts, and migration details.

## Private dependency secrets in other workflows

`GH_PAT` and `UV_EXTRA_INDEX_URL` are read by the CI, benchmark, CodeQL, marimo, book,
weekly and docker workflows too. The stubs that call those reusable workflows forward each secret by
name rather than with `secrets: inherit`, because GitHub only honours `inherit` when the
caller sits in the same organisation or enterprise as `jebel-quant/rhiza` — from any other
organisation the secrets simply never arrived, and private dependencies failed to install
with `could not read Password for 'https://***@github.com'` (#1689). A secret that is not
defined is forwarded empty and the workflow falls back to `github.token`, so nothing is
required for a project with no private dependencies. Pull requests from forks never receive
secrets at all, so a fork PR that needs a private dependency fails at install; that is
GitHub's rule rather than a rhiza setting.

The docker workflow is the one place the runner's git configuration cannot reach, because
`uv sync` runs inside the image build. It passes both secrets to `docker buildx build` as
BuildKit secrets instead, which exist only for that one instruction and are written into no
layer; a build argument would be readable with `docker history` (#1691). See
`docs/development/DOCKER.md` for building such an image locally.
