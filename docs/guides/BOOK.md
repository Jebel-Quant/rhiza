# Book (Documentation Site)

The Rhiza documentation site — referred to as the **book** — is built with [MkDocs](https://www.mkdocs.org/) using the [Material theme](https://squidfunk.github.io/mkdocs-material/). This page explains how to customise its look and feel.

## Building and Serving

```bash
# Build the full book (runs tests, exports notebooks, then builds MkDocs)
make book

# Serve the docs locally with live reload (useful while editing)
make serve

# Build only the MkDocs site (skips test reports and notebooks)
make book
```

The built site is written to `_book/` by default. To change the output directory:

```makefile
# In your root Makefile or local.mk
BOOK_OUTPUT := _site
```

## Configuration

The MkDocs configuration lives in `mkdocs.yml` at the root of the repository. Key settings:

| Setting | Description |
|---------|-------------|
| `site_name` | The title shown in the browser tab and header |
| `site_url` | Canonical URL for the deployed site |
| `docs_dir` | Source directory for Markdown files (default: `docs`) |
| `site_dir` | Build output for `mkdocs-build` (default: `_mkdocs`) |
| `theme.name` | Theme name — currently `material` |

## Theme Customization

### Logo and Favicon

The logo and favicon shown in the sidebar are set in `mkdocs.yml`:

```yaml
theme:
  name: material
  logo: assets/my-logo.svg
  favicon: assets/my-favicon.png
```

### Colour Palette

Add a `palette` block to the `theme` section of `mkdocs.yml`:

```yaml
theme:
  name: material
  palette:
    primary: indigo
    accent: indigo
```

See the [Material colour reference](https://squidfunk.github.io/mkdocs-material/setup/changing-the-colors/) for the full list of named colours. You can also supply a hex value via CSS (see below).

### Fonts

```yaml
theme:
  name: material
  font:
    text: Roboto
    code: Roboto Mono
```

Set `font: false` to use system fonts and avoid loading anything from Google Fonts.

### Custom CSS and JavaScript

Create override files and reference them in `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/extra.css

extra_javascript:
  - javascripts/extra.js
```

Place the files under `docs/stylesheets/` and `docs/javascripts/` respectively. For example, `docs/stylesheets/extra.css`:

```css
:root {
  --md-primary-fg-color: #1a73e8;
  --md-primary-fg-color--light: #e8f0fe;
  --md-primary-fg-color--dark: #1557b0;
}
```

### Overriding Theme Templates

Material supports a `custom_dir` override mechanism. Create a `docs/overrides/` directory and point to it in `mkdocs.yml`:

```yaml
theme:
  name: material
  custom_dir: docs/overrides
```

Any file placed in `docs/overrides/` that matches a path from the Material theme will replace the original. For example, to customise the footer, copy `partials/footer.html` from the Material theme source into `docs/overrides/partials/footer.html` and edit it there.

See the [Material theme documentation on template overrides](https://squidfunk.github.io/mkdocs-material/customization/#extending-the-theme) for the full list of available partials.

## Navigation

The page tree is defined under the `nav` key in `mkdocs.yml`:

```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Quick Reference: QUICK_REFERENCE.md
    - Demo: DEMO.md
  - Reference:
    - Architecture: ARCHITECTURE.md
```

Omitting the `nav` key causes MkDocs to generate navigation automatically from the `docs/` directory structure.

## Makefile Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOK_OUTPUT` | `_book` | Output directory for `make book` |
| `MKDOCS_CONFIG` | `mkdocs.yml` | Path to the MkDocs config file |

## Deployment

The reusable `rhiza_book.yml` workflow builds `_book/`, uploads it as a generic
`book` workflow artifact, and — by default — packages it as a GitHub Pages
artifact and deploys it to Pages from the repository's default branch.

### GitHub Pages (default)

The `github-book` overlay bundle wires this up out of the box: adopt the bundle
and the workflow deploys to Pages with no further configuration.

### Artifact-only mode

GitHub Pages requires GitHub Enterprise Cloud for private repositories, which
may be disproportionate for a small private project. The book output is a
portable static site, so the reusable workflow accepts a `deploy-pages` input
that turns off the Pages-specific artifact upload and deploy job. The generic
`book` artifact is still uploaded, so a consumer-owned job can download it and
deploy anywhere.

GitHub validates permissions requested by every job in a reusable workflow
before evaluating job conditions. Consequently, an artifact-only caller must
still grant the `book` job `pages: write` and `id-token: write`, even though
the disabled deploy job never receives them at runtime:

```yaml
permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  book:
    uses: jebel-quant/rhiza/.github/workflows/rhiza_book.yml@<version>
    with:
      deploy-pages: false
    secrets:
      GH_PAT: ${{ secrets.GH_PAT }}
      UV_EXTRA_INDEX_URL: ${{ secrets.UV_EXTRA_INDEX_URL }}
    permissions:
      contents: read
      pages: write
      id-token: write

  deploy:
    needs: book
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v8
        with:
          name: book
          path: _book

      # Consumer-specific deployment to Cloudflare, Azure, S3, ...
```

Rhiza does not implement provider-specific deployment: its responsibility is to
build, validate and expose the portable `book` artifact. Deployment credentials
and provider-specific configuration stay in the consumer repository, which
keeps the interface general and avoids coupling Rhiza to any one host.

### Consumer-owned build setup (opt-in)

Set `book-setup: true` to run your own composite action at
`.github/actions/rhiza-book-setup/action.yml`. Rhiza checks out the caller's
`github.sha`, not the Rhiza workflow revision or a configurable branch. Setup runs
in the build job before dependency resolution, cache restoration, and book
generation. Values exported through `GITHUB_ENV` are available to subsequent
steps in that job, not to a separate deployment job.

The only setup credential Rhiza accepts is the optional `BOOK_SETUP_TOKEN`
secret, passed as the action's `token` input. Map just the credential your action
needs; do not use `secrets: inherit` or serialize the secrets context. Keep
non-secret configuration in your consumer-owned action. Rhiza does not sync or
provide this action. If you customize the template-owned caller stub, exclude
`.github/workflows/rhiza_book.yml` in `.rhiza/template.yml` so a sync preserves it.

For example, a notebook can read a private API using a read-only token. In your
consumer caller (with the permissions shown above):

```yaml
jobs:
  book:
    uses: jebel-quant/rhiza/.github/workflows/rhiza_book.yml@<version>
    with:
      deploy-pages: false
      book-setup: true
    secrets:
      BOOK_SETUP_TOKEN: ${{ secrets.PRIVATE_API_READ_TOKEN }}
```

Create the consumer-owned `.github/actions/rhiza-book-setup/action.yml`:

```yaml
name: Prepare private API access
description: Configure the documentation notebook's read-only API access
inputs:
  token:
    description: Read-only private API credential
    required: true
runs:
  using: composite
  steps:
    - shell: bash
      env:
        API_TOKEN: ${{ inputs.token }}
      run: |
        if [ -z "$API_TOKEN" ] || [[ "$API_TOKEN" == *$'\n'* || "$API_TOKEN" == *$'\r'* ]]; then
          echo "::error::A single-line private API token is required."
          exit 1
        fi
        # Escape workflow-command characters before masking.
        masked="${API_TOKEN//%/%25}"
        masked="${masked//$'\r'/%0D}"
        masked="${masked//$'\n'/%0A}"
        printf '::add-mask::%s\n' "$masked"
        printf 'PRIVATE_API_TOKEN=%s\n' "$API_TOKEN" >> "$GITHUB_ENV"
        echo 'PRIVATE_API_URL=https://api.example.invalid' >> "$GITHUB_ENV"
```

The notebook reads the environment without displaying credentials:

```python
import os
from urllib.request import Request, urlopen

request = Request(
    os.environ["PRIVATE_API_URL"] + "/public-summary",
    headers={"Authorization": "Bearer " + os.environ["PRIVATE_API_TOKEN"]},
)
with urlopen(request, timeout=30) as response:
    summary = response.read()  # Publish only data approved for documentation.
```

Use a released workflow version that includes this extension. The example URL
and secret name are placeholders; provision the token in your own repository.
GitHub masks passed secrets, but your action must also mask any derived
credentials before logging or exporting them. Never enable shell tracing, echo
tokens, embed them in notebook output, or write them into artifacts, caches, or
committed configuration. Masking logs does **not** redact generated files.

Setup is disabled by default; existing consumers need no action or token.
Opting in without the action, or failing any setup step (including checking for
a required token), fails the build and prevents artifact upload and deployment.
The optional secret may be empty, so actions needing it must check it explicitly:
an action's `required: true` input alone is not a runtime check.

When setup is enabled, fork `pull_request` events and **all**
`pull_request_target` events are rejected before checkout or secret delivery to
the action. This remains true even if repository settings allow sending secrets
to fork workflows. Do not work around it by checking out PR code in a privileged
event. Use a separate uncredentialed validation call with `book-setup: false`
(and `deploy-pages: false`) for fork PRs, or build credentialed documentation
only on trusted pushes. Same-repository PRs may run setup: protect write access
and review changes to the action and notebooks as credential-bearing code.
Runs in fork repositories remain skipped by the existing build-job guard.

### Trying an unreleased Rhiza workflow

To test an unreleased workflow change, exclude
`.github/workflows/rhiza_book.yml` in `.rhiza/template.yml`, add a
consumer-owned replacement workflow, and point its `uses:` reference at the
branch under test. This limits the experiment to one file. Pointing
`template.yml` at a work-in-progress branch and running a full sync instead
updates every managed file from that branch.

Remove the exclusion and restore a released Rhiza reference once the feature
is available in a release.

### Example: Cloudflare Pages

One-time Cloudflare setup:

1. In **Workers & Pages → Create application**, select **Continue to Pages**,
   then create a **Direct Upload** project. Do not use **Upload your static
   files** from the initial screen: it creates a Workers static-assets project,
   which `wrangler pages deploy` cannot deploy to. Give the Pages project a
   name such as `my-project-book`; upload a placeholder file for its first
   deployment.
2. Optionally attach a custom domain such as `docs.example.com`.
3. At `dash.cloudflare.com/profile/api-tokens`, create a custom scoped token
   with `Account → Cloudflare Pages → Edit` for the relevant account.
4. Find the account ID in the **Account details** panel of the **Workers &
   Pages** overview.
5. Add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` to the consumer
   repository's GitHub Actions secrets, and add `CLOUDFLARE_PAGES_PROJECT`
   (for example, `my-project-book`) as an Actions variable.

Then in the consumer workflow:

```yaml
name: "(RHIZA) BOOK"

on:
  push:
    branches:
      - "**"

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  book:
    uses: jebel-quant/rhiza/.github/workflows/rhiza_book.yml@<version>
    with:
      deploy-pages: false
    secrets:
      GH_PAT: ${{ secrets.GH_PAT }}
      UV_EXTRA_INDEX_URL: ${{ secrets.UV_EXTRA_INDEX_URL }}
    permissions:
      contents: read
      # GitHub validates the reusable workflow's disabled Pages job before
      # evaluating `deploy-pages`; these permissions are required to start it.
      pages: write
      id-token: write

  deploy-cloudflare:
    name: Deploy book to Cloudflare Pages
    needs: book
    # Publish only the default branch. Feature branches still build and
    # validate the book, but do not replace the production documentation.
    if: >-
      github.ref_name == github.event.repository.default_branch &&
      !github.event.repository.fork
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Download Rhiza book artifact
        uses: actions/download-artifact@v8
        with:
          name: book
          path: _book

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: >-
            pages deploy _book
            --project-name=${{ vars.CLOUDFLARE_PAGES_PROJECT }}
```

If the documentation must stay private, Cloudflare Access can be enabled for
the Pages hostname to require authentication via a corporate identity
provider, an email-domain rule or an explicit allow-list. That configuration
lives entirely on Cloudflare's side; Rhiza neither handles user authentication
nor embeds credentials in the generated book.
