# 5. Separate rhiza Template Repository from rhiza-cli

Date: 2024-05-01

## Status

Accepted

## Context

The initial Rhiza concept combined two concerns in a single repository: the curated
collection of template files that downstream projects receive, and the CLI tooling that
fetches and applies those files. As the project matured, keeping these concerns together
created friction:

- **Tight coupling**: Any change to the CLI logic required a release of the entire
  template repository, even if no template files had changed (and vice versa).
- **Version confusion**: Downstream projects pin a specific version of Rhiza in their
  `.rhiza/template.yml`. If CLI behaviour and template content share the same version
  number, a CLI bug fix forces a bump that causes Renovate to open unnecessary sync PRs.
- **Install overhead**: The CLI is invoked ephemerally via `uvx rhiza` (no persistent
  install). Bundling it with the template repository would require downloading the full
  template content just to run CLI commands.
- **Discoverability**: Packaging the CLI separately on PyPI (`rhiza-cli`) makes it
  straightforward for developers to discover and install the tool independently of any
  particular template version.
- **Custom template repositories**: A core Rhiza use case is allowing teams to fork the
  template repository and maintain their own variant. These forks should not need to also
  fork or maintain the CLI code.

## Decision

We will maintain two distinct components:

1. **[rhiza](https://github.com/Jebel-Quant/rhiza)** (this repository) — the *template
   content*: the curated set of configuration files, Makefile modules, CI/CD workflows,
   and tooling files that downstream projects sync from. Versioned with Git tags (e.g.,
   `v0.7.1`).
2. **[rhiza-cli](https://pypi.org/project/rhiza-cli/)** — the *CLI engine*: a separate
   Python package published to PyPI, invoked ephemerally via `uvx rhiza`. Implements
   the `init`, `materialize`, `bump`, and `release` operations.

**Interaction model:**

- Downstream projects specify the template source and version in `.rhiza/template.yml`
  (`repository: Jebel-Quant/rhiza`, `ref: v0.7.1`).
- When `uvx rhiza materialize` is run, `rhiza-cli` reads this file, fetches the matching
  files from the specified repository at the given ref, and applies them to the project.
- The CLI version and the template version are independent; either can be updated without
  forcing an update of the other.

**Custom template repositories:**

Because the CLI is decoupled, teams can set `repository` to any GitHub repository
(their own fork or an entirely independent template) without needing to ship their own
CLI. The CLI is generic; the template content is specific.

## Consequences

### Positive

- **Independent release cadence**: Template improvements and CLI bug fixes can be
  released independently, without coupling.
- **Smaller surface area**: Downstream projects only interact with template files; they
  never need to understand CLI internals.
- **Fork-friendly**: Teams can create their own template repository and point
  `rhiza-cli` at it without forking the CLI.
- **Ephemeral invocation**: `uvx rhiza` downloads and caches the CLI on first use with
  no persistent installation required.
- **PyPI discoverability**: `pip install rhiza-cli` or `uvx rhiza` is a familiar,
  standard pattern for Python developers.

### Neutral

- **Two repositories to follow**: Contributors interested in the full system need to
  track both repositories. The README clearly documents this two-component model.
- **Version coordination**: Occasionally, a new CLI feature requires a minimum template
  version (or vice versa). Compatibility constraints are documented in release notes.

### Negative

- **Distributed codebase**: Bugs that span both components (e.g., a sync issue caused
  by CLI logic interacting with a specific template structure) require debugging across
  two repositories.
