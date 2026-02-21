# 6. Organise Templates into Bundles

Date: 2025-01-01

## Status

Accepted

## Context

Rhiza started with a flat list of files that downstream projects could include or exclude
using glob patterns in `.rhiza/template.yml`. As the template library grew to cover CI/CD,
testing, documentation, Docker, Marimo notebooks, presentations, GitLab CI, DevContainers,
and more, the file-pattern approach had several drawbacks:

- **High cognitive load**: Users had to know the exact file paths they wanted. The list
  of available files was not self-documenting.
- **Fragile configuration**: Adding a new file to a feature (e.g., a new workflow for the
  Docker integration) required every downstream project to manually update its
  `include` patterns.
- **No dependency enforcement**: Some features depend on others (e.g., `book` requires
  `tests` for coverage reports). There was no mechanism to express or enforce these
  relationships.
- **Undiscoverable**: Without a catalogue, users could not easily explore what Rhiza
  offered without reading the repository source.

## Decision

We will organise all Rhiza templates into named **bundles** defined in
`.rhiza/template-bundles.yml`. Downstream projects select bundles by name in their
`.rhiza/template.yml`:

```yaml
templates:
  - core
  - tests
  - github
  - docker
```

**Key aspects:**

1. **Bundle definition file**: `.rhiza/template-bundles.yml` is the single source of
   truth listing every bundle name, its description, the files it includes, its
   `standalone` status, and its `requires`/`recommends` relationships.
2. **Coarse-grained selection**: A bundle is the minimum unit of adoption. Users select
   feature areas, not individual files.
3. **Dependency metadata**: Each bundle declares hard dependencies (`requires`) and
   soft suggestions (`recommends`), enabling the CLI to validate configurations and
   warn about missing dependencies.
4. **Standalone flag**: Bundles marked `standalone: false` cannot be used alone (e.g.,
   `book` requires `tests`). The CLI enforces this.
5. **Backward compatibility**: Explicit `include`/`exclude` file patterns continue to
   work alongside bundle selection for advanced use cases.
6. **Bundle versioning**: The `template-bundles.yml` file carries a `version` field
   matching the Rhiza release, allowing the CLI to detect version mismatches.

## Consequences

### Positive

- **Self-documenting**: `template-bundles.yml` serves as a catalogue of everything
  Rhiza offers. Users can browse it to understand available features.
- **Automatic file inclusion**: When a new file is added to a bundle, all downstream
  projects using that bundle receive it automatically on next sync—no manual
  `include` pattern update required.
- **Dependency safety**: Hard `requires` relationships are validated by the CLI,
  preventing incomplete configurations (e.g., enabling `book` without `tests`).
- **Simpler downstream config**: A short list of bundle names is easier to read and
  review in a pull request than a long list of file paths.
- **Renovate compatibility**: Renovate can update the `ref` in `template.yml`, and
  the bundle-to-file mapping is resolved at sync time using the new ref.

### Neutral

- **Coarser control**: Users who want only a specific file from a bundle must use
  explicit `exclude` patterns to remove unwanted files after enabling the bundle.
- **Bundle granularity decisions**: Deciding what belongs in a bundle versus a new
  bundle requires judgment. The current grouping reflects feature domains
  (testing, documentation, CI/CD) rather than individual tools.

### Negative

- **Bundle maintenance**: Adding a new file to Rhiza requires updating
  `template-bundles.yml`, which is an extra step. Automated tests validate that
  all files referenced in bundles exist.
