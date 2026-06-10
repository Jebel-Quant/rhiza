# 10. Introduce a Layered Bundle and Profile Model

Date: 2026-05-02

## Status

Accepted

## Context

Rhiza's bundle model (ADR-0006) maps named groups of files to a `files:` list and lets
downstream projects select bundles by name. This works well for feature adoption, but
over time a structural problem emerged:

**Feature bundles conflate local tooling with hosted automation.**

Several bundles that represent stand-alone local features also directly own
`.github/workflows/*` files:

- `tests` owns `rhiza_ci.yml`, `rhiza_codeql.yml`, `rhiza_weekly.yml`
- `book` owns `rhiza_book.yml`
- `marimo` owns `rhiza_marimo.yml`
- `docker` owns `rhiza_docker.yml`
- `devcontainer` owns `rhiza_devcontainer.yml`

This makes it impossible to adopt, say, the testing tooling without also syncing GitHub
Actions workflows into the project. Projects that are:

- local-only experiments or research codebases
- hosted on GitLab, not GitHub
- private repositories that do not use GitHub Actions
- early-stage projects not yet ready for hosted automation

...have no clean way to express "give me the tooling but not the workflows". They must
either accept unwanted files or manually add `exclude:` patterns in their
`.rhiza/template.yml`.

A second problem is discoverability at init time. There is no concept of a recommended
starting set. Users running `rhiza init` see a flat list of bundle names with no
guidance about which bundles are typically used together, what a sensible first setup
looks like for their hosting context, or which combinations are known to work well.

## Decision

We will introduce a two-layer model separating file ownership from user-facing intent.

### Layer 1: Bundles (unchanged role, refined boundaries)

Bundles remain the atomic sync unit. Every synced file belongs to a bundle. Bundles
own files via `files:`, declare hard dependencies via `requires:`, and declare soft
suggestions via `recommends:`.

**Key rule change**: feature bundles must be local-first. A feature bundle should
include only the files needed to use that feature locally. Platform-specific automation
files (`.github/workflows/*`, `.gitlab/`) belong in dedicated platform overlay bundles,
not in the feature bundle itself.

Concretely, GitHub workflow files are moved out of feature bundles and into new
GitHub-specific overlay bundles:

- `github-tests`: CI/CodeQL/weekly workflows for the `tests` feature
- `github-book`: book publishing workflow for the `book` feature
- `github-marimo`: Marimo notebook workflow for the `marimo` feature
- `github-docker`: Docker build and publish workflow for the `docker` feature
- `github-devcontainer`: DevContainer publish workflow for the `devcontainer` feature

These overlay bundles have `standalone: false` and `requires:` the corresponding feature
bundle and the `github` bundle.

The existing `github` bundle keeps base GitHub repository automation: the sync and
release workflows, `dependabot.yml`, issue and discussion templates, and secret scanning.

### Layer 2: Profiles (new)

A new top-level `profiles:` section in `template-bundles.yml` defines named presets that
expand to a set of bundles.

Rules:

- profiles do not own files directly
- profiles reference bundles only, not raw file paths
- profiles represent stable, tested user intents rather than every possible combination
- selecting a profile is equivalent to selecting all its constituent bundles
- users may combine profile selection with additional manual bundle selection

Initial profiles:

- `local`: local-first development with no hosted workflow files
- `github-project`: GitHub-hosted project with CI/CD and release automation
- `gitlab-project`: GitLab-hosted project with GitLab CI pipelines

### Config

Downstream projects will be able to express profile selection in `.rhiza/template.yml`:

```yaml
repository: Jebel-Quant/rhiza
ref: v0.9.0

profiles:
  - local

templates:
  - presentation    # any extra bundles beyond the profile
```

`rhiza-cli` is responsible for expanding profiles to bundles, merging manual bundle
selections, deduplicating, and validating the result. The CLI implementation is a
separate concern; this ADR covers the template repository structure and metadata.

## Consequences

### Positive

- **Clean local mode**: Selecting the `local` profile installs no `.github/workflows/*`
  files. Projects that do not use GitHub Actions get exactly what they need.
- **Explicit platform separation**: It is now clear which files belong to the feature
  and which belong to its GitHub automation. Bundle names reflect this — `tests` is
  the feature; `github-tests` is the GitHub automation layer for that feature.
- **Better onboarding**: Profiles give `rhiza init` a recommended starting path without
  forcing users to understand every bundle upfront.
- **Composable**: Power users retain full control by selecting individual bundles.
  Profiles are an addition, not a replacement.
- **GitLab parity**: The split makes it straightforward to produce matching
  `gitlab-tests`, `gitlab-book`, and similar overlay bundles for GitLab CI in a
  follow-on step, without restructuring feature bundles again.

### Neutral

- **More bundles**: The total bundle count increases as each feature bundle gets one or
  more platform overlay siblings. The `template-bundles.yml` file grows. The existing
  automated structure tests mitigate risk.
- **Migration for existing consumers**: Downstream projects using bundles such as
  `tests` today will need to explicitly add `github-tests` if they want the CI
  workflows. The `github-project` profile bundles both, so profile users are unaffected.

### Negative

- **CLI changes required**: Profiles are defined in the template repository, but
  consumed by `rhiza-cli`. Until the CLI supports the `profiles:` key in
  `.rhiza/template.yml`, users can approximate local mode by selecting only local
  bundles manually, or the CLI can expand profiles at `init` time and write the
  resulting bundle list.
- **Profile maintenance overhead**: Profiles must be kept current as bundles are added
  or renamed. Automated tests enforce that every bundle referenced in a profile exists.
