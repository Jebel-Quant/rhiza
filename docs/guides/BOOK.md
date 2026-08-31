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

```yaml
jobs:
  book:
    uses: jebel-quant/rhiza/.github/workflows/rhiza_book.yml@<version>
    with:
      deploy-pages: false
    secrets: inherit

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

### Example: Cloudflare Pages

One-time Cloudflare setup:

1. Create a Cloudflare Pages project using **Direct Upload** (do not ask
   Cloudflare to build the repository). Give it a name such as
   `my-project-book`.
2. Optionally attach a custom domain such as `docs.example.com`.
3. Create a scoped Cloudflare API token with `Account → Cloudflare Pages →
   Edit` on the relevant account.
4. Add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` to the consumer
   repository's GitHub Actions secrets.

Then in the consumer workflow:

```yaml
name: "(RHIZA) BOOK"

on:
  push:
    branches:
      - "**"

permissions:
  contents: read

jobs:
  book:
    uses: jebel-quant/rhiza/.github/workflows/rhiza_book.yml@<version>
    with:
      deploy-pages: false
    secrets: inherit
    permissions:
      contents: read

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
