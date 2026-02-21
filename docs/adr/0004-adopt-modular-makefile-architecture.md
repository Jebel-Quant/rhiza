# 4. Adopt a Modular Makefile Architecture

Date: 2024-03-01

## Status

Accepted

## Context

Rhiza provides Makefile-based task automation as a core part of its template offering.
As the number of supported features grew (testing, documentation, Docker, Marimo
notebooks, presentations, CI helpers, release management), maintaining a single
monolithic `Makefile` became unworkable:

- Adding a new feature required editing a shared file, creating merge conflicts during
  template synchronization.
- Downstream projects that only wanted a subset of features still received all targets,
  cluttering `make help` output.
- Large Makefiles are hard to navigate and understand.
- The root `Makefile` is typically owned by the downstream project; Rhiza cannot safely
  update it without overwriting project-specific customizations.

The core challenge is that the `Makefile` is simultaneously a Rhiza-managed file (it
needs to include Rhiza's logic) and a user-owned file (it is the natural place for
project-specific targets).

## Decision

We will implement a modular Makefile architecture where:

1. **Thin root `Makefile`**: The root `Makefile` contains only a single `include`
   statement pointing to `.rhiza/rhiza.mk`. Project-specific targets are added above
   this include line.
2. **Core logic in `.rhiza/rhiza.mk`**: All Rhiza infrastructure lives in
   `.rhiza/rhiza.mk`, which is synced from the template repository.
3. **Auto-loading extensions**: `rhiza.mk` ends with `-include .rhiza/make.d/*.mk`,
   which automatically loads all `.mk` files in the `make.d/` directory in lexicographic
   order.
4. **Numbered prefixes for ordering**: Makefile modules use numeric prefixes to control
   load order (e.g., `00-19` for configuration, `20-79` for tasks, `80-99` for hooks).
5. **Feature isolation**: Each feature domain lives in its own `.mk` file
   (`test.mk`, `docker.mk`, `marimo.mk`, etc.), making it easy to add or remove features.
6. **Hook system**: Double-colon targets (`pre-install::`, `post-install::`) allow
   downstream projects to inject behaviour before and after standard targets.
7. **`local.mk` escape hatch**: An optional `local.mk` file (never synced) provides a
   place for developer-local shortcuts without affecting the shared configuration.

## Consequences

### Positive

- **Clean separation**: Rhiza infrastructure is isolated in `.rhiza/make.d/`; project
  customizations live in the root `Makefile` or `local.mk`. Template sync never
  overwrites user code.
- **Selective feature adoption**: Adding a bundle to `.rhiza/template.yml` drops in
  the corresponding `.mk` file, automatically registering new targets.
- **Easy to navigate**: Each `.mk` file is focused on a single domain. Contributors
  can find relevant targets without searching a large monolithic file.
- **Extensible**: New features can be added to Rhiza without touching existing files—
  just add a new `.mk` file.
- **`make help` stays organized**: Section headers (`##@`) in each module group
  related targets, keeping the help output readable as more modules are added.

### Neutral

- **Auto-loading behaviour**: The glob include (`*.mk`) loads files in alphabetical
  order. Module authors must be aware of this when one module depends on variables
  defined in another.
- **Hidden complexity**: New contributors may be surprised to discover that `make help`
  targets come from multiple files. The `ARCHITECTURE.md` and module READMEs document
  this.

### Negative

- **Debugging Make**: Tracing the origin of a target or variable requires knowing the
  module structure. `make --print-data-base` can assist but is verbose.
- **Filename collisions**: Two modules defining the same target name will silently
  interact (or produce an error). Module authors must coordinate target naming.
