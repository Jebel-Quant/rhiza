# Bundle Taxonomy

Rhiza ships development infrastructure as **bundles** — named groups of
configuration files. A downstream project adopts Rhiza by listing the bundles
(or profiles) it wants in `.rhiza/template.yml`; `/rhiza:update` then materialises
exactly those files. This page is the map of what you can choose from.

The authoritative, machine-readable definition lives in
`.rhiza/template-bundles.yml`. This document explains the *model*; that file is
the source of truth for the exact set. See
[ADR-0006](../adr/0006-organise-templates-into-bundles.md) and
[ADR-0010](../adr/0010-layered-bundle-profile-model.md) for the rationale.

## The three groups

1. **Feature bundles** — one per capability. They are *local-first*: a feature
   bundle never ships hosted-CI workflow files, so it works the same whether or
   not you use GitHub or GitLab.
2. **Platform-overlay bundles** — thin CI stubs that pair a feature with a
   hosting platform (`github-<feature>`, `gitlab-<feature>`). Each delegates to a
   reusable workflow in `jebel-quant/rhiza`.
3. **Profiles** — higher-level presets (sometimes called *meta-bundles*) that
   expand to a curated set of bundles for a stable intent (local-only,
   GitHub-hosted, GitLab-hosted).

## Feature bundles

| Bundle | Purpose |
|--------|---------|
| `core` | Required base, and language-neutral: thin Makefile, `.rhiza/` modular make system, help/logo machinery, and uv/uvx as a tool runner. Not a working repo on its own. |
| `python-core` | The Python language layer: virtualenv and `uv sync` (`install`), `.python-version`, `ruff.toml`, `.bandit`, pre-commit config, `deptry` and licence scans, and the `all` aggregate. Exactly one language layer per repo. |
| `rust-core` | The Rust language layer: rustup and `cargo fetch` (`install`), `rust-toolchain.toml`, `rustfmt.toml`, `clippy.toml`, `deny.toml`, pre-commit config, and the test/coverage/lint gates. Carries its own test targets — in Rust they are cargo subcommands with nothing to configure. |
| `go-core` | The Go language layer: `go mod download` (`install`), `.golangci.yml`, `revive.toml`, pre-commit config, a `version.Version` constant for the release flow (with the one test file that keeps `make test` from passing vacuously), and the test/coverage/lint gates. Carries its own test targets — `go test` and `go tool cover` need no configuration. |
| `tests` | Local testing: pytest, coverage, and type checking. |
| `benchmarks` | Performance benchmarking with `pytest-benchmark` and reporting (builds on `tests`). |
| `book` | Documentation site with MkDocs + zensical. |
| `marimo` | Interactive Marimo notebooks for exploration and docs. |
| `presentation` | Slides built from `PRESENTATION.md` with Marp. |
| `paper` | LaTeX paper compilation targets (`make paper`). |
| `docker` | Docker containerization support. |
| `devcontainer` | VS Code Dev Container for reproducible environments. |
| `vscode` | Recommended VS Code extensions and workspace settings for local (non-container) editing. |
| `lfs` | Git LFS installation and management. |
| `github` | GitHub repository configuration (actions, dependabot, templates, rulesets, core workflows). |
| `gitlab` | GitLab CI/CD pipeline configuration and core workflows. |
| `renovate` | Renovate bot configuration for automated dependency updates. |
| `legal` | Legal and community documentation files. |

Bundles declare relationships in `.rhiza/template-bundles.yml`:

- `requires` — hard dependencies pulled in automatically (e.g. `tests` requires
  `core` and `book`).
- `recommends` — soft companions you may want (e.g. `book` recommends `tests`
  and `marimo`).
- `standalone` — whether the bundle is usable on its own (`benchmarks` and
  `marimo` are not).

## Platform-overlay bundles

Each overlay adds the hosted-CI workflow stub for a feature. Pick the overlay
that matches your platform *and* the feature bundle it pairs with.

| Bundle | Pairs feature → platform |
|--------|--------------------------|
| `github-tests` | `tests` → GitHub Actions (CI, CodeQL, benchmark) |
| `github-book` | `book` → GitHub Pages publishing |
| `github-marimo` | `marimo` → GitHub Actions notebook publishing |
| `github-docker` | `docker` → GitHub Actions lint/build/scan |
| `github-devcontainer` | `devcontainer` → GitHub Actions image build validation |
| `github-paper` | `paper` → GitHub Actions LaTeX build + PDF publishing |
| `github-quality-review` | `core` → GitHub Actions advisory Claude design review of PR diffs (opt-in) |
| `gitlab-tests` | `tests` → GitLab CI |
| `gitlab-book` | `book` → GitLab Pages publishing |
| `gitlab-marimo` | `marimo` → GitLab CI notebook execution |
| `gitlab-quality-review` | `core` → GitLab CI advisory Claude design review of MR diffs (opt-in) |

## Profiles (meta-presets)

Profiles are the recommended entry point: pick the one that matches your hosting
context and Rhiza expands it to a sensible bundle set.

| Profile | Expands to | Use when |
|---------|-----------|----------|
| `local` | `core`, `python-core`, `tests`, `book`, `marimo` | Local-first work with no hosted CI (experiments, private/other-host repos). |
| `github-project` | the `local` set + `github` and the `github-*` overlays | A standard GitHub-hosted project. |
| `gitlab-project` | the `local` set + `gitlab` and the `gitlab-*` overlays | A standard GitLab-hosted project. |
| `rust-local` | `core`, `rust-core`, `book` | A Rust project. Hosted-CI Rust profiles arrive with the Rust workflows — the `github`/`gitlab` bundles currently ship Python CI. |
| `go-local` | `core`, `go-core`, `book` | A Go project. Hosted-CI Go profiles arrive with the Go workflows, for the same reason. |

## Adoption flow

Declare what you want in `.rhiza/template.yml`:

```yaml
# Profile-based (recommended):
profiles:
  - github-project

# ...optionally add extra bundles on top:
templates:
  - paper
  - github-paper
```

or take full manual control with bundles only:

```yaml
templates:
  - core
  - tests
  - github
  - github-tests
```

Then run `/rhiza:update` to materialise the selected files. Required bundles
(`core`) and any `requires` dependencies are pulled in automatically, so you only
list the capabilities you care about.

**Pick exactly one language layer.** `core` deliberately defines no `install` and no
`all` — those names belong to a layer, so that `book.mk`, `test.mk` and the CI
workflows can call `make install` without knowing the language. Every profile pairs
`core` with `python-core`; a bundles-only config must name a layer itself, and naming
two is a file-ownership conflict the sync rejects.
