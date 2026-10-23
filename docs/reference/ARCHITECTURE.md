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
    draft --> publisher{RELEASE_PUBLISHER}
    publisher -->|pypi - default| pypi[PyPI-compatible upload]
    publisher -->|custom| custom[Repository-owned publisher]
    publisher -->|none| finalize[Finalize Release]
    pypi -->|Public PyPI only| conda[Generate Conda Recipe<br/>with grayskull]
    draft --> devcontainer[Publish Devcontainer]
    pypi --> finalize
    custom --> finalize
    conda --> finalize
    devcontainer --> finalize
```

### Choosing a publisher

The GitHub release workflow separates building from publishing: tag validation, package
building, version verification, SBOM and provenance generation remain Rhiza-owned. The
publisher uploads the existing `dist` artifact rather than rebuilding the release.
This extends **destinations and authentication**, not the build system: the standard
package build still produces Python wheels and source distributions.

Set the GitHub Actions repository variable `RELEASE_PUBLISHER`:

| Value | Behaviour |
| --- | --- |
| Unset or `pypi` | Publish through the existing PyPI action. With no feed overrides, use public PyPI Trusted Publishing (OIDC), without stored credentials. |
| `custom` | Invoke the repository-owned action at `.github/actions/release-publish/action.yml` (or `action.yaml`). Never invoke the PyPI publisher as a fallback. |
| `none` | Skip package publication while retaining the other release outputs. |

Unknown values fail the publishing job rather than silently selecting PyPI.
The existing `PYPI_REPOSITORY_URL` **variable** and `PYPI_TOKEN` **secret** remain
supported under `pypi` for compatible upload endpoints. Changing a URL does not make
that publisher support another upload protocol or a provider's login sequence.

`Private :: Do Not Upload` continues to suppress the built-in PyPI publisher,
including its legacy custom-endpoint path. Explicit `custom` selection permits
private distributions; the repository-owned action is responsible for choosing a safe
destination. With the default publisher, a project without a buildable distribution
continues to skip publication. Selecting `custom` without a buildable package, a
publishing action, or actual distribution files is an error. An expected artifact
that fails to download is also an error, not a successful skip.

Publisher selection, distribution-presence checks and public artifact-URL validation
are implemented in `bundles/github/.rhiza/scripts/release_publish.py`; the mother
repository's `.rhiza/scripts/release_publish.py` is a relative symlink to that source.
Both release workflows independently sparse-check out an already-published, immutable
Rhiza commit into `.rhiza-release-tools`, with credentials persistence disabled, and
invoke its helper without changing the caller's working directory. Old release tags
and callers that have not synced the helper therefore remain supported; a caller's
own helper is never used. To upgrade the guards, first publish the new script revision,
then update the tooling checkout SHA in both workflows. This pin is deliberately not
an automatically bumped self-referential release tag.

The dependency-free module is directly unit-tested and scanned as ordinary Python.
Workflow integration tests exercise the commands with absent or incompatible caller
helpers and verify the independent checkout contract.

### Repository-owned publishing action

Commit a composite action at `.github/actions/release-publish/action.yml` in the
consuming repository, then select `RELEASE_PUBLISHER=custom`. No bundle owns this
path, so subsequent template updates leave it intact. The
release job checks out the validated release tag: the action must exist in that
revision, not just on the default branch.

The workflow calls the action with these inputs:

| Input | Contract |
| --- | --- |
| `artifacts-dir` | Absolute path to the downloaded `dist` directory containing the verified release artifacts. |
| `tag` | Validated release tag, including its leading `v`. |
| `version` | Tag with the leading `v` removed, not a separately resolved package version. |
| `credentials` | Optional opaque value from the `RELEASE_PUBLISH_CREDENTIALS` secret; its format is owned by the extension. |

The custom-publisher step also provides `RHIZA_RELEASE_PUBLISH_VARS`, a JSON
object containing the Actions `vars` context, because composite action metadata
cannot reference that context directly. This is **non-secret configuration**, not
the `secrets` context; keep credentials in secrets or obtain them through OIDC.

The action owns tool installation, provider configuration, authentication and upload.
It may invoke provider-specific actions, request short-lived credentials through OIDC,
or consume the optional credentials input. For example, a CodeArtifact extension can
assume a publisher role, obtain and immediately mask a short-lived authorization
token, then upload the downloaded distributions. No provider-specific dependencies or
long-lived cloud access keys are required by Rhiza.

The job runs on Ubuntu in the `release` environment with `contents: read` and
`id-token: write`. Configure the provider's trust policy for the appropriate
repository and release environment, and protect release tags and environment access.
Authentication happens **in the publishing job**, not in a prerequisite job.
The extension does not receive all repository secrets: only the explicit credentials
input is forwarded. When invoking the workflow through `workflow_call`, pass that
secret explicitly if needed. Mask generated secrets immediately, keep credentials
out of logs and public outputs, and pin external actions used by the extension.

Upload only the intended distribution files; `artifacts-dir` can also contain
provenance. Do not rebuild or silently ignore authentication/upload failures.
The action must fail when any required upload fails. If it publishes to several
destinations, it must wait for all required uploads before reporting success.

An optional `artifact-url` output may name a **public HTTPS page** for the published
artifact. Rhiza validates it and appends it to the GitHub release notes. It must not
contain credentials, signed access tokens, or private endpoints. Omit it when no safe
public link exists; Rhiza does not infer a custom feed URL or expose credentials in
release notes.

### CodeArtifact follow-up

No managed CodeArtifact publisher ships with this contract. That follow-up requires
pre-write ownership collision protection in
[rhiza-claude#267](https://github.com/Jebel-Quant/rhiza-claude/issues/267)
and real AWS OIDC/upload validation before adoption. The removed provider and its tests
remain recoverable from [PR #1694](https://github.com/Jebel-Quant/rhiza/pull/1694)'s
[earlier commit](https://github.com/Jebel-Quant/rhiza/commit/52580cd1908aac769310421e08b6fc1105b86e98).
Private dependency consumption uses the separate setup contract below; remaining validation
is tracked in [#1732](https://github.com/Jebel-Quant/rhiza/issues/1732).

### Completion and platform scope

Release finalization waits for the selected publisher and the devcontainer job;
neither may fail and still allow the release to be finalized. Explicit package skips
remain successful, and cancellation never finalizes the release.
Conda recipe generation remains optional and only follows successful **public PyPI**
publication with no `PYPI_REPOSITORY_URL` override. A custom or legacy private-feed
upload must not trigger a lookup on public PyPI. A failed optional Conda recipe does
not prevent finalization.

This extension contract is **GitHub Actions-only**. The GitLab release template retains
its existing token/URL publishing behaviour. It also does not configure private-feed
**consumption** in build, test or documentation jobs: those jobs need their own
authentication before resolving dependencies, because job credentials are not shared.

### Consumer-owned dependency setup

Dependency consumption is independent of `RELEASE_PUBLISHER`: `pypi` remains the
default, and `custom` and `none` retain their existing behaviour. To authenticate
private installs, set the repository variable `RHIZA_SETUP_ENABLED=true` and commit
`.github/actions/rhiza-setup/action.yml` (or `action.yaml`). No bundle owns this path.
The action receives `purpose` (the consuming job ID) and `credentials` (only the
optional `RHIZA_SETUP_CREDENTIALS` secret). No complete variables or secrets context
is forwarded. Keep non-secret provider configuration in the consumer action, or
call a pinned organisation action with explicit inputs. Export credentials through
`GITHUB_ENV`; they are fresh per job/matrix leg and never shared through job outputs.
The legacy `UV_EXTRA_INDEX_URL` secret takes precedence only when populated.

The trust and action-presence guard is inlined in each reusable workflow, so it is
versioned with that workflow rather than depending on a synced dispatcher. Enabled
setup fails on fork PRs and all `pull_request_target` events before invoking the
action. Missing actions and failed authentication fail the job and block dependent
uploads/deployments. Disabled setup needs no local action or credentials. Run trusted
pushes for credentialed validation; fork PRs need uncredentialed checks with setup
disabled. Never check out untrusted PR code in a privileged event to bypass the guard.

#### Caller permissions

The shipped CI, book, benchmark, notebook and weekly workflows declare explicit
read-only defaults and job permissions. CI also retains `actions: read`. Setup is
available with the explicit `RHIZA_SETUP_CREDENTIALS` secret, but these default
jobs cannot obtain an OIDC token. In particular, the book `build` job has only
`contents: read`: it never inherits `pages: write` or `id-token: write` from the
calling Pages stub. Those permissions remain confined to the `deploy` job.
Release build attestation and publishing retain their existing OIDC permissions.

**OIDC opt-in requires permission in both the consuming job and its caller.** Adding
`id-token: write` to a caller alone cannot override the called job's read-only
scope. GitHub permissions are static; `RHIZA_SETUP_ENABLED=true` enables the action,
not an OIDC grant. To opt in without widening default consumers' permissions:

1. Copy the desired version of the reusable workflow into a consumer-owned path,
   such as `.github/workflows/dependency-ci.yml`. Retain `workflow_call`; remove any
   direct push, PR or scheduled triggers if those remain in your calling wrapper.
2. In that copy, add `id-token: write` only to each dependency-consuming job that
   needs OIDC, alongside its existing read permissions. For the book `build` job,
   the complete set is `contents: read` and `id-token: write`; never add
   `pages: write`. Keep the separate deployment permissions unchanged.
3. Grant the matching OIDC permission in the calling wrapper, and point it at the
   consumer-owned workflow. Install the setup action and enable it as described above.

For example, after preparing the consumer-owned CI workflow:

```yaml
jobs:
  ci:
    uses: ./.github/workflows/dependency-ci.yml
    permissions:
      contents: read
      actions: read
      id-token: write
    secrets:
      RHIZA_SETUP_CREDENTIALS: ${{ secrets.RHIZA_SETUP_CREDENTIALS }}
```

**Upgrade responsibility:** exclude customized template-owned wrappers from sync
so updates preserve the opt-in. Excluded wrappers no longer receive automatic
`@vX.Y.Z` reference updates from `/rhiza:update`; bump any retained version references
by hand. A consumer-owned workflow copy also requires manual review and application
of upstream fixes. Adding only a caller grant to an otherwise unchanged upstream
workflow does not enable OIDC. A maintained opt-in overlay or reusable OIDC variant
could remove this copying and upgrade burden; that remains follow-up work under
[#1732](https://github.com/Jebel-Quant/rhiza/issues/1732).

#### CodeArtifact example

Copy `examples/dependency-setup/codeartifact/action.yml` to the consumer action path
and replace its explicit configuration placeholders. It assumes a read-only role,
obtains and immediately masks a short-lived token, and exports uv's named-index
username/password. Configure the credential-free URL and explicit package mapping
in the project, then commit the generated lockfile:

```toml
[[tool.uv.index]]
name = "private"
url = "https://example-123456789012.d.codeartifact.eu-west-2.amazonaws.com/python/packages/simple/"
explicit = true

[tool.uv.sources]
private-package = { index = "private" }
```

Use a reader role separate from publishing. Allow `codeartifact:GetAuthorizationToken`
on the domain and `codeartifact:GetRepositoryEndpoint` plus
`codeartifact:ReadFromRepository` on the required repository. Allow
`sts:GetServiceBearerToken` with `sts:AWSServiceName=codeartifact.amazonaws.com`.
The role trust must allow `sts:AssumeRoleWithWebIdentity` through GitHub's OIDC provider,
require audience `sts.amazonaws.com`, and restrict the subject to your repository and
trusted refs, such as `repo:ORG/REPO:ref:refs/heads/main`. The release build job
declares no environment, so reader trust must also allow approved release-tag
subjects, such as `repo:ORG/REPO:ref:refs/tags/v1.2.3`. The publishing job uses the
`release` environment subject (`repo:ORG/REPO:environment:release`); restrict that
subject to the separate publisher role and protect the environment's allowed refs.
These examples use GitHub's default subject format; if your organisation customizes
OIDC subjects, use the corresponding configured format in both roles' trust policies.
Do not grant the reader role package publishing permissions. See AWS's
[token permissions](https://docs.aws.amazon.com/codeartifact/latest/ug/tokens-authentication.html)
and [repository permissions](https://docs.aws.amazon.com/codeartifact/latest/ug/repo-policies.html).

#### Workflow support and remaining validation

| Workflow/job | First dependency consumer after setup |
| --- | --- |
| CI metadata | Build-and-inspect package action (build dependencies) |
| CI test, lowest, typecheck, deptry, repository checks, docs coverage, security, license | Task invocation or project install |
| Book build | Frozen environment sync, followed by notebooks/book generation |
| Marimo | Notebook execution and its script environment |
| Benchmark | Benchmark task |
| Weekly compatibility / Semgrep | Fresh dependency resolution / task invocation |
| Release build | Package build and frozen SBOM sync in the same job |
| CI pre-commit | No hook: installs public tooling only |
| Docker / devcontainer | Generic setup unsupported inside isolated builds; deferred under [#1732](https://github.com/Jebel-Quant/rhiza/issues/1732) |

Runner `GITHUB_ENV` does not enter container builds. The existing Docker GitHub-token
secret path is not CodeArtifact forwarding; private-feed support needs separate BuildKit
secret mounts. Local devcontainer bootstrap also needs its own authentication.
Do not pass feed credentials through build arguments or bake them into image layers.

The loopback authenticated-index test verifies setup exports, rejected unauthenticated
access, frozen private dependency installation and import without changing the lockfile.
It does not prove AWS OIDC or reusable-workflow execution. Keep
[#1732](https://github.com/Jebel-Quant/rhiza/issues/1732) open for the trusted AWS run
(role assumption, fresh token, locked install/import, credential-free logs/artifacts)
and container forwarding work. This PR is a partial delivery of that issue.

**Book migration:** rename `.github/actions/rhiza-book-setup` to
`.github/actions/rhiza-setup`, rename its `token` input to `credentials`, replace
`BOOK_SETUP_TOKEN` with `RHIZA_SETUP_CREDENTIALS`, remove `with.book-setup`, and set
`RHIZA_SETUP_ENABLED=true`. The old input and secret are removed. Use `purpose` to
limit book-only work within an action shared across dependency jobs.

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
