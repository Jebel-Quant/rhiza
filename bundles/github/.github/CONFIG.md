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
| `GH_PAT` | Git authentication for installing private dependencies during the release build. |
| `UV_EXTRA_INDEX_URL` | Extra package index URL (with credentials) for private dependencies. |

`GITHUB_TOKEN` is provided automatically by GitHub Actions and needs no configuration.

## How the workflows are pinned

Every third-party action in these workflows is pinned to a **commit SHA**, with the tag it
corresponds to in a trailing comment:

```yaml
- uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0
```

A tag is a moving reference: whoever owns the action can repoint `v6.1.0` at a different
commit, and every repository using it runs the new code without a diff anywhere. A SHA cannot
move. This is also what OpenSSF Scorecard's Pinned-Dependencies check looks for, so a synced
repository scores on it without doing anything.

Keeping them current is a bot's job. Rhiza itself uses Renovate and Dependabot; the `renovate`
bundle ships a config with the `github-actions` manager enabled, and the `github` bundle ships
a `dependabot.yml` that covers `.github/workflows`. Either updates the SHA and the comment
together — you need only review and merge.

References to rhiza's own reusable workflows are the deliberate exception:

```yaml
uses: jebel-quant/rhiza/.github/workflows/rhiza_ci.yml@v1.5.1
```

That tag is the *template version* this repository is synced to, not a dependency to bump.
`/rhiza:update` rewrites it when you move to a new release, so a bot bumping it would put
your workflows ahead of the template they came from.

## What these workflows deliberately do not do

They contain no runner-hardening or egress-monitoring step, even though rhiza's own workflows
open every job with `step-security/harden-runner`. Adding a third-party agent that watches a
runner and reports its network activity to a third-party service is a decision for the people
who own the repository and answer for its compliance — not one a configuration template makes
on their behalf. Nothing in the release pipeline needs it to cut a release.

If you want it, add the step to each job; `exclude:` in `.rhiza/template.yml` keeps your copy
across syncs. Note that the workflows delegating to rhiza's reusable workflows — CI, book,
docker, marimo, paper — already run hardened jobs, because those jobs are rhiza's.
