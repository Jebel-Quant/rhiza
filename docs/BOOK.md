# Book (Documentation Site)

The Rhiza documentation site — referred to as the **book** — is built with [MkDocs](https://www.mkdocs.org/) using the [Material theme](https://squidfunk.github.io/mkdocs-material/). This page explains how to customise its look and feel.

## Building and Serving

```bash
# Build the full book (runs tests, exports notebooks, then builds MkDocs)
make book

# Serve the docs locally with live reload (useful while editing)
make mkdocs-serve

# Build only the MkDocs site (skips test reports and notebooks)
make mkdocs-build
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

The logo shown in the sidebar is controlled by the `LOGO_FILE` Makefile variable:

```makefile
# In your root Makefile or local.mk
LOGO_FILE := assets/my-logo.svg
```

To change the logo and favicon directly in `mkdocs.yml`:

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
| `MKDOCS_OUTPUT` | `_mkdocs` | Output directory for `make mkdocs-build` |
| `MKDOCS_CONFIG` | `mkdocs.yml` | Path to the MkDocs config file |
| `LOGO_FILE` | `.rhiza/assets/rhiza-logo.svg` | Logo used in the sidebar |
