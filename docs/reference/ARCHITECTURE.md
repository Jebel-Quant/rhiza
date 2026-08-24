# Rhiza Architecture

Visual diagrams of Rhiza's architecture and component interactions.

## System Overview

```mermaid
flowchart TB
    subgraph User["User Interface"]
        make[make commands]
        local[local.mk]
    end

    subgraph Core["Task layer"]
        shim[Makefile<br/>template-owned shim]
        cli[rhiza-task<br/>pinned CLI]
        template[template-bundles.yml<br/>Bundle Config]
    end

    subgraph Config["Configuration"]
        pyproject[pyproject.toml]
        ruff[ruff.toml]
        precommit[.pre-commit-config.yaml]
        editorconfig[.editorconfig]
    end

    subgraph CI["GitHub Actions"]
        ci[CI Workflow]
        release[Release Workflow]
        e2e[E2E Workflow]
        weekly[Weekly Workflow]
    end

    make --> shim
    local -.-> shim
    shim --> cli
    cli --> pyproject
    ci --> make
    release --> make
    e2e --> make
    weekly --> make
```

## Makefile Hierarchy

```mermaid
flowchart TD
    subgraph Entry["Entry Point"]
        Makefile[Makefile<br/>template-owned shim]
    end

    subgraph CLI["Pinned CLI"]
        rhizatask[rhiza-task@X.Y.Z<br/>uvx-provisioned]
        registry[task registry<br/>layer:name]
    end

    subgraph Settings["Settings"]
        table["[tool.rhiza-task]<br/>pyproject.toml / rhiza.toml"]
        env[.rhiza/.env<br/>developer-local]
    end

    subgraph Local["Local Customization"]
        localmk[local.mk<br/>Repo-owned]
        shadow[explicit rules<br/>shadow a task]
    end

    Makefile -->|"%: forwards to"| rhizatask
    Makefile -.->|includes| localmk
    Makefile -.->|beats the catch-all| shadow
    rhizatask --> registry
    registry -->|resolves against| table
    registry -.-> env
```

There is no make layer left to load. `core` ships no `.rhiza/rhiza.mk` and `.rhiza/make.d/`
no longer exists: every fragment it once held retired into
[rhiza-task](https://github.com/Jebel-Quant/rhiza-task), a pinned CLI, in two steps —
eleven at 0.2.0 and the last five at 0.3.0.

What `core` does still ship is the front door, `Makefile`, at 71 lines instead of 1481. It
pins `RHIZA_TASK`, bootstraps uv if the runner has none, and forwards every unmatched target
to the CLI through a `%:` catch-all. What used to be "which fragments were synced?" is now
"which tasks does the pinned version have, for the language layers this repository has?" —
`uvx rhiza-task list` answers it.

For one release the CLI printed that file itself (`uvx rhiza-task shim > Makefile`) and each
repo owned the copy. That put a template inside the task runner, and the pin inside a
generated file: bumping a repo's gates was a hand edit `/rhiza:update` could not make. The
template owns it again, so `RHIZA_TASK` travels with the sync — the property
`RHIZA_CHECKS_VERSION` already had. Repo-owned targets live in `local.mk`, which the
`Makefile` `-include`s and no sync touches.

| was | is |
| --- | --- |
| `bootstrap.mk` — `install`, uv bootstrap | the `install` task, plus three lines of the shim |
| `test.mk` — test, coverage, typecheck, stress, mutation | the `python`/`rust`/`go` layers and the testing extras — except `mutation`, dropped rather than carried (#1492) |
| `quality.mk` — `fmt`, lint, `rhiza-test` | the neutral quality tasks |
| `book.mk`, `marimo.mk` | the `book` and `marimo` tasks |
| `doctor.mk` | the `doctor` task |
| `releasing.mk` | `/rhiza:release` and bump-my-version |
| `docker.mk`, `github.mk`, `lfs.mk`, `paper.mk`, `presentation.mk` | tasks of the same names, added in rhiza-task 0.3.0 |
| `custom-env.mk`, `custom-task.mk` — example stubs | `local.mk`, which core ships un-ignored so a repo can commit its own targets (#1574) |
| `bundles.mk` — mother-repo only | rhiza's own `local.mk` |

Bundles still own capabilities; what a bundle contributes is now configuration and
documentation rather than make recipes. The `docker` bundle ships the `Dockerfile`, `paper`
ships the `docs/paper/` convention, and their targets come from the CLI whatever bundles a
project selected.

## Extending a Task

```mermaid
flowchart LR
    subgraph Local["local.mk (repo-owned)"]
        rule["install:<br/>explicit rule"]
        extra[the extra step]
    end

    subgraph CLI["Pinned CLI"]
        task["uvx rhiza-task install"]
    end

    invocation[make install] --> rule
    rule -->|calls| task
    rule -->|then| extra
```

An explicit rule beats the shim's `%:` catch-all, so a rule of the same name in `local.mk`
intercepts the invocation and decides what the task is wrapped in. This replaces the
double-colon anchors of the make layer — see [Hook Naming](#hook-naming).

## Release Pipeline

```mermaid
flowchart TD
    tag[Push Tag v*] --> validate[Validate Tag]
    validate --> build[Build Package]
    build --> draft[Draft GitHub Release]
    draft --> pypi[Publish to PyPI]
    pypi --> conda[Generate Conda Recipe<br/>with grayskull]
    draft --> devcontainer[Publish Devcontainer]
    pypi --> finalize[Finalize Release]
    conda --> finalize
    devcontainer --> finalize

    subgraph Conditions
        pypi_cond{Has dist/ &<br/>not Private?}
        conda_cond{PyPI publish<br/>succeeded?}
        dev_cond{PUBLISH_DEVCONTAINER<br/>= true?}
    end

    draft --> pypi_cond
    pypi_cond -->|yes| pypi
    pypi_cond -->|no| finalize
    pypi --> conda_cond
    conda_cond -->|yes| conda
    conda_cond -->|no| finalize
    draft --> dev_cond
    dev_cond -->|yes| devcontainer
    dev_cond -->|no| finalize
```

## Template Sync Flow

```mermaid
flowchart LR
    upstream[Upstream Rhiza<br/>jebel-quant/rhiza] -->|template.yml| sync[/rhiza:update]
    sync -->|updates| downstream[Downstream Project]

    subgraph Synced["Synced Files"]
        workflows[.github/workflows/]
        rhiza[.rhiza/]
        configs[Config Files]
    end

    subgraph Preserved["Preserved"]
        localmk[local.mk]
        src[src/]
        tests[tests/]
    end

    sync --> Synced
    downstream --> Preserved
```

## Directory Structure

```mermaid
flowchart TD
    root[Project Root]

    root --> rhiza[.rhiza/]
    root --> github[.github/]
    root --> src[src/]
    root --> tests[tests/]
    root --> docs[docs/]
    root --> book[_book/<br/>build output]

    root --> shim[Makefile<br/>rhiza-task shim]
    rhiza --> semgrep[semgrep.yml]
    rhiza --> env[.env]

    github --> workflows[workflows/]
    workflows --> ci[rhiza_ci.yml]
    workflows --> release[rhiza_release.yml]
    workflows --> e2e[rhiza_e2e.yml]
    workflows --> more[... one per feature]

    shim --> tasks[uvx rhiza-task &lt;task&gt;]
```

## .rhiza/ Directory Structure and Dependencies

```mermaid
flowchart TB
    subgraph rhiza[".rhiza/ (template-owned)"]
        direction TB
        pointer[template.yml<br/>which bundles to sync]
        lock[template.lock<br/>what was synced]
        semgrep[semgrep.yml<br/>static analysis rules]
        env[".env (optional, gitignored)<br/>developer-local settings"]
    end

    subgraph project["Project Files (repo-owned)"]
        direction TB
        Makefile[Makefile<br/>template-owned shim]
        localmk[local.mk<br/>own targets]
        pyproject["pyproject.toml<br/>[tool.rhiza-task] settings"]
        ruff_toml[ruff.toml<br/>linting]
        pytest_ini[pytest.ini<br/>test config]
        python_version[.python-version<br/>the Python to fetch]
    end

    cli[uvx rhiza-task]

    Makefile -->|forwards to| cli
    localmk -.->|shadows a task| cli
    cli -->|reads| pyproject
    cli -.->|reads| env
    cli -->|reads| python_version
    cli -->|uses| pytest_ini
    cli -->|uses| ruff_toml
    pointer -->|drives| sync[/rhiza:update]
    sync -->|records| lock
```

Two directories that earlier versions of this diagram showed are gone, and both went for the
same reason — code and dependency lists distributed by file-copy became dependencies:

- **`.rhiza/requirements/`** — retired: four `.txt` files that pinned per-target tooling.
  Every tool is provisioned where it is used now (`uv run --with`, `uvx`), so a target's
  tooling travels with the target (#1380).
- **`.rhiza/tests/`** — retired: the conformance checks a consumer's repository is held to,
  formerly synced as seven modules plus a `conftest.py`. They are the `pytest-rhiza` dependency of
  `make rhiza-test` now, pinned by `[tool.rhiza-task]`'s `pytest-rhiza` (#1540). A repo that
  synced before that keeps the folder on disk, inert — the gate names modules, not paths.

## CI/CD Workflow Triggers

```mermaid
flowchart TD
    subgraph Triggers
        push[Push]
        pr[Pull Request]
        schedule[Schedule]
        manual[Manual]
        tag[Tag v*]
    end

    subgraph Workflows
        ci[CI]
        e2e[E2E]
        codeql[CodeQL]
        release[Release]
        weekly[Weekly]
        scorecard[Scorecard]
    end

    push --> ci
    push --> e2e
    push --> codeql
    pr --> ci
    pr --> e2e
    pr --> codeql
    schedule --> weekly
    schedule --> scorecard
    manual --> ci
    tag --> release
```

Every gate a pull request must pass is a **job** of `rhiza_ci.yml` — the pre-commit hooks,
`deptry`, `docs-coverage`, the security scan, the licence scan — not a workflow of its own.
That is what the required status checks in `.github/rulesets/main-branch-protection.json`
name, and why renaming a job breaks branch protection.

## Python Execution Model

```mermaid
flowchart LR
    subgraph Commands
        make[make test]
        direct[Direct Python]
    end

    subgraph UV["uv Layer"]
        uv_run[uv run]
        uvx[uvx]
    end

    subgraph Tools
        pytest[pytest]
        prek[prek]
        deptry[deptry]
    end

    make --> uv_run
    uv_run --> pytest
    uvx --> prek
    uvx --> deptry

    direct -.->|Never| pytest

    style direct stroke-dasharray: 5 5
```

## Naming Conventions and Organization Patterns

### Task Naming (rhiza-task)

Task names follow these conventions:

1. **Lowercase with hyphens**: `docs-coverage`, `view-prs`, `marimo-validate` — never
   `docsCoverage` or `Docs_Coverage`.

2. **The same name means the same thing in every language**: `test` is pytest in a Python
   project, `cargo nextest` in a crate and `go test` in a module. That parity is what lets
   the CI workflows call `make typecheck` without knowing the language.

3. **Sections group them**: `Python`, `Rust`, `Go`, `Quality`, `Book`, `Dev`, `Testing extras`
   and one per bundle-owned group (`Docker`, `Git LFS`, `Paper`, `Presentation`,
   `GitHub Helpers`). `uvx rhiza-task list` prints them grouped.

### Target Naming

Make targets follow consistent patterns:

1. **Lowercase with hyphens**: Target names use lowercase with hyphens
   - ✅ `install-uv`, `docker-build`, `view-prs`
   - ❌ `installUv`, `docker_build`, `viewPRs`

2. **Verb-noun pattern**: Action-oriented targets use verb-noun format
   - `install-uv` - Install the uv tool
   - `docker-build` - Build Docker image
   - `view-prs` - View pull requests

3. **Namespace prefixes**: Related targets share a common prefix
   - Docker: `docker-build`, `docker-run`, `docker-clean`
   - LFS: `lfs-install`, `lfs-pull`, `lfs-track`, `lfs-status`
   - GitHub: `view-prs`, `view-issues`, `failed-workflows`, `workflow-status`

### Help Text

`make help` is the shim's one non-delegating rule, and it prints two lists:

1. **The CLI's tasks**, grouped by the section each declares, from `uvx rhiza-task list`.
   Nothing in the repository states those groups — see [Task Naming](#task-naming-rhiza-task).

2. **Repo-owned targets**, scraped from a `##` comment on the rule itself:

   ```makefile
   e2e: install $(UV) ## run the language-layer end-to-end suite against real toolchains
   ```

   The shim greps `$(MAKEFILE_LIST)`, so this is what lets a repo move its targets into
   `local.mk` without losing them from `make help`. The `##@` section headers of the make
   layer are gone with the layer that parsed them.

### Hook Naming

**Retired with the make layer.** `bootstrap.mk` anchored `pre-install::`/`post-install::`
and their `sync` counterparts as double-colon no-ops so a consumer could chain onto them,
and that was the documented way to add project hooks. `uvx rhiza-task install` knows nothing
about make targets, so there is nothing to chain onto.

Shadow the target instead: an explicit `install:` rule in `local.mk` beats the shim's `%:`
catch-all, so it can call the CLI and then the extra step.

### File Organization Patterns

1. **Directory naming**:
   - Lowercase with hyphens: `template-bundles.yml`, `docs/reference/`
   - Plural for collections: `requirements/`, `templates/`, `tests/`

2. **Test organization** (`tests/`):
   - Tests grouped by **purpose**, not by feature
   - `api/` - Makefile API tests
   - `bundles/` - the bundle contract and per-bundle sync
   - `structure/` - Project structure validation
   - `integration/` - End-to-end workflows
   - `e2e/` - one real toolchain run per language layer
   - `deps/` - Dependency validation

   No bundle ships test code any more. The conformance checks a consumer's repository is
   held to used to be synced into `.rhiza/tests/`; they are the `pytest-rhiza` dependency
   of `make rhiza-test` now (#1540).

3. **Dependency provisioning** (the `.rhiza/requirements/` lists are gone):
   - Libraries the test suite imports live in `pyproject.toml` `[dependency-groups]`
   - Per-target tooling (pytest plugins, interrogate, marimo, zensical, …)
     is installed on the fly by its `make` target via `uv run --with` / `uvx`

### Template Bundle and Profile Naming

`template-bundles.yml` defines two layers: **bundles** (file-owning building blocks) and **profiles** (user-facing presets). See [ADR-0010](../adr/0010-layered-bundle-profile-model.md) for the rationale.

#### Bundles

1. **Lowercase, hyphen-separated**: `core`, `github`, `tests`, `github-tests`
2. **Feature bundles are local-first**: they do not own hosted workflow files
3. **Platform overlays use a `<platform>-` prefix**: `github-tests`, `github-book`, `gitlab`
   - ✅ `github-tests` (GitHub Actions for the `tests` feature)
   - ✅ `github-book` (GitHub Actions for the `book` feature)
   - ❌ embedding workflow files directly in `tests` or `book`

4. **Bundle metadata**:
   - `description` - Clear, concise explanation
   - `standalone` - Whether bundle can be used independently
   - `requires` - Hard dependencies on other bundles
   - `recommends` - Soft dependencies that enhance functionality

#### Profiles

1. **Lowercase, hyphen-separated**: `local`, `github-project`, `gitlab-project`
2. **Intent-focused**: Named after the hosting and automation context, not the tool
   - ✅ `local` (no hosted automation)
   - ✅ `github-project` (standard GitHub project)
   - ❌ `no-workflows`, `full-setup`

3. **Profile metadata**:
   - `description` - Clear summary of the intended context
   - `bundles` - Ordered list of bundles this profile expands to

### Setting Naming

The make layer's forty-odd `SCREAMING_SNAKE_CASE` variables — the `_BIN` paths, the
`_FOLDER` accumulators, the colour codes — are settings of the pinned CLI now, and the
naming follows the surface they are written on:

1. **`kebab-case` in TOML**: `source-folder`, `pytest-rhiza`, `mkdocs-extra-packages` in
   `[tool.rhiza-task]` (`pyproject.toml`, or `rhiza.toml` for a project with no Python
   manifest).

2. **`RHIZA_`-prefixed `SCREAMING_SNAKE_CASE` in the environment**: the same setting, upper
   cased and prefixed — `RHIZA_SOURCE_FOLDER`, `RHIZA_CI_OS_MATRIX`. This is the surface a
   CI job or a `local.mk` `export` uses.

3. **Resolution order**: defaults → `.rhiza/.env` → the TOML table → `RHIZA_*` → CLI flags.

Three make variables survive, all in the shim and all about reaching the CLI at all:
`RHIZA_TASK` (the pin), `INSTALL_DIR` and `UVX`/`UV`.

### Documentation Naming

Documentation files use SCREAMING_SNAKE_CASE:

- `README.md` - Directory/project overview
- `ARCHITECTURE.md` - Architecture diagrams
- `EXTENDING_RHIZA.md` - Customization and extension guide
- `QUICK_REFERENCE.md` - Command reference
- `SECURITY.md` - Security policy

### Workflow Naming (`.github/workflows/`)

GitHub Actions workflows use the pattern `rhiza_<feature>.yml`:

- `rhiza_ci.yml` - Continuous integration
- `rhiza_release.yml` - Release automation
- `rhiza_e2e.yml` - One real toolchain run per language layer
- `rhiza_codeql.yml` - CodeQL analysis

**Rationale**: The `rhiza_` prefix clearly identifies template-managed workflows, distinguishing them from user-defined workflows.

## Key Design Principles

### 1. Single Source of Truth

- **Python version**: `.python-version` file (not hardcoded)
- **Dependencies**: `pyproject.toml` (not duplicated in makefiles)
- **Bundle definitions**: `template-bundles.yml` (not scattered)

### 2. Catch-All Delegation

The `Makefile` forwards anything it cannot resolve itself:

```makefile
%: $(UVX) FORCE
	@$(UVX) $(RHIZA_TASK) $(RHIZA_TASK_GOAL)
```

`FORCE` is what keeps every task phony — `.PHONY` takes no patterns, but a phony
prerequisite is never up to date, so `make book` still runs next to a `book/` directory.

This allows:
- New tasks to arrive with a version bump, not a file sync
- No include lists, and no ordering to get wrong
- An explicit rule to shadow any task, which is how a project extends one

### 3. Extension Points

Users can extend Rhiza without modifying template files — and the `Makefile` is now one of
the files they must not modify, since `core` ships it and every sync overwrites it:

1. **`local.mk`**: own targets, and wrapping a task by shadowing its name. The `Makefile`
   `-include`s it and `core` leaves it un-ignored, so it is committed like any source file.
   Shadowing reaches a task make resolves — not one the CLI reaches internally, and not CI,
   which never runs make.
2. **`local-setup.sh`**: a native binary the project needs before any gate. Every layer's
   `install` runs it, which is what puts it on the path of local make, both CI platforms and
   the devcontainer at once. Committed, un-ignored by `core` for the same reason `local.mk` is.
3. **`[tool.rhiza-task]`**: settings, in `pyproject.toml` or `rhiza.toml`.
4. **`RHIZA_*` in the environment**: the same settings for a CI job, or for a `local.mk`
   `export` when the value must be committed.
5. **`exclude:` in `.rhiza/template.yml`**: opting a managed file out of the sync entirely.

The full account, with the failure mode of each, is the
[Customization Guide](../guides/CUSTOMIZATION.md).

### 4. Fail-Safe Defaults

- Missing `uv` is installed by the shim, into `./bin`, before any task runs
- A layer's toolchain absence skips the e2e suite with a reason rather than failing it
- Graceful degradation when optional features are unavailable

The one place that principle is deliberately *not* applied: a path-scoped gate skips a
`source_folder` that does not exist, so it reports success having measured nothing. That is
why a repository whose source root is not `src/` must declare it — see #1505, #1511, #1516,
and the `source-folder` line in this repository's own `pyproject.toml`.

### 5. Documentation as Code

- Every repo-owned target carries a `##` help comment, enforced by a pre-commit hook
- Every architectural decision has an [ADR](../adr/index.md)
- README files in every major directory
- Docs are gated: links resolve, bundles are documented, and every `make` target a document
  names must exist (`tests/docs/test_doc_consistency.py`)
