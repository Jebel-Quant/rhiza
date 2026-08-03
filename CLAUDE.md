# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Rhiza?

Rhiza is a **collection of reusable configuration templates** for Python projects — not a runtime library. It has no `src/` directory and no runtime dependencies. Its purpose is to provide and continuously synchronize development infrastructure (Makefiles, CI workflows, linting configs, test setups) into downstream projects via the separate `rhiza-cli` tool.

Downstream projects adopt Rhiza by adding a `.rhiza/template.yml` that lists which bundles to sync from this repository.

## Commands

```bash
make install      # Full setup: installs uv, downloads Python version from .python-version, creates .venv, installs deps
make test         # Run all tests with coverage (90% minimum required)
make fmt          # Run all pre-commit hooks (ruff format/check, markdownlint, bandit, etc.)
make deptry       # Check for unused/missing dependencies
make docs-coverage  # Check docstring coverage with interrogate (100% required)
make typecheck    # Static type checking with pyright
make benchmark    # Performance benchmarks
make hypothesis-test  # Property-based tests only
make stress       # Load/concurrency tests
make security     # pip-audit + bandit security scans
make e2e          # Language-layer end-to-end suite (opt-in, real toolchains; see below)
make book         # Build documentation
make marimo       # Start Marimo notebook server
make clean        # Remove build artifacts and stale branches
```

**Running a single test:**
```bash
uv run pytest tests/api/test_makefile_targets.py -v
uv run pytest tests/api/test_makefile_targets.py::TestClass::test_method -v
uv run pytest -m "not stress" tests/   # Exclude stress tests
```

## Command Execution Policy

Follow this order strictly:

1. If a `make` target exists → use `make <target>`
2. No `make` target → use `uv run <command>`
3. Never invoke `.venv/bin/python`, `.venv/bin/pytest`, etc. directly

The virtual environment is managed automatically by `make` and `uv run`. No manual activation is needed.

## Architecture

### Template Bundles

The core abstraction is the **bundle** — a named group of configuration files. All bundles are defined in `.rhiza/template-bundles.yml` (the authoritative list) and fall into three groups:

**Feature bundles** — one per capability:

- `core` (required, **language-neutral**): the thin Makefile, the `.rhiza/make.d` system,
  help/logo machinery, and uv/uvx as a *tool runner*. It deliberately defines no
  `install` and no `all` — see **Language layers** below.
- `python-core` (the Python **language layer**): `.python-version`, `ruff.toml`,
  `.bandit`, the pre-commit config, and `.rhiza/make.d/python.mk` (`install`, `all`,
  `deptry`, `license`, `rhiza-test`). Ships no bump-my-version config — see
  **Where the version config lives**.
- `rust-core` (the Rust **language layer**): `rust-toolchain.toml`, `rustfmt.toml`,
  `clippy.toml`, `deny.toml`, a Rust pre-commit config, `.bumpversion.toml`, and
  `.rhiza/make.d/rust.mk`. Carries its own test targets, unlike Python — see
  **Language layers**.
- `go-core` (the Go **language layer**): `.golangci.yml`, `revive.toml`, a Go
  pre-commit config, `.bumpversion.toml`, a starter `internal/version/version.go`
  with its `version_test.go`, and `.rhiza/make.d/go.mk`. Carries its own test
  targets, like Rust.
- `tests`: pytest, coverage, type checking (Python; requires `python-core`)
- `benchmarks`: pytest-benchmark infrastructure and reporting
- `github`: GitHub repository configuration (actions, dependabot, core workflows)
- `gitlab`: GitLab CI/CD pipeline configuration and core workflows
- `docker`, `devcontainer`: containerisation
- `vscode`: recommended VS Code extensions and workspace settings for local (non-container) editing
- `marimo`: interactive notebooks
- `book`: documentation with [MkDocs](https://www.mkdocs.org/) + [zensical](https://pypi.org/project/zensical/)
- `presentation`: Marp slides
- `paper`: LaTeX paper compilation
- `lfs`, `legal`, `renovate`: miscellaneous tooling

**Platform overlay bundles** — CI workflow stubs that pair a feature with a platform: `github-tests`, `github-book`, `github-marimo`, `github-docker`, `github-devcontainer`, `github-paper`, `github-quality-review`, `gitlab-tests`, `gitlab-book`, `gitlab-marimo`, `gitlab-quality-review`.

**Meta-bundles** — curated compositions of other bundles: `github-project`, `gitlab-project`, `local` (no hosted CI), and the single-language local profiles `rust-local` and `go-local`.

### Dogfooding (root files ↔ bundle sources)

Rhiza dogfoods its own templates: the files it ships in `bundles/<name>/...` also live at the repo root so the mother repo runs on its own infrastructure. `bundles/` is the **single source of truth**, and each root dogfood file is a **relative symlink into its owning bundle** (e.g. `.rhiza/rhiza.mk` → `bundles/core/.rhiza/rhiza.mk`). Edit the bundle file; the root reflects it automatically — no second edit. Run `make sync-self` (mother-repo-only, `utils/link_dogfood.py`) to (re)create links after adding a bundle file.

A few files **cannot** be symlinks and stay as **real copies**, kept in sync by tests (`tests/bundles/test_bundle_*_sync.py`) rather than by symlink:

- `.github/*` platform config (Dependabot, release notes, secret scanning, PR template, rulesets) — GitHub reads these blobs directly and does not resolve symlinks. **Live `.github/workflows/*` are also real** (Actions won't run a symlinked workflow) and differ from the bundle stubs by design. So does **`rulesets/main-branch-protection.json`**, and for a subtler reason (#1448): here `rhiza_ci.yml` has `push:`/`pull_request:` triggers, so its jobs run top-level and report bare check-run names, while downstream the `github-tests` stub delegates via `jobs.ci` and GitHub reports them as `ci / <job name>`. The bundle copy therefore prefixes all six required contexts; `tests/bundles/test_bundle_github_sync.py` pins that relationship, including the coupling to the stub's job id.
- `.rhiza/.gitignore` (and any `.gitignore`/`.gitattributes`) — git opens these with `O_NOFOLLOW`, so a symlink yields an ELOOP warning and the rules are ignored.

Plus intentional mother-repo overrides that deliberately diverge from their bundle source: root `.gitignore`, `.pre-commit-config.yaml`, `.python-version`, `SECURITY.md`, `renovate.json`. The exclusion list lives in `utils/link_dogfood.py`.

Downstream consumers are unaffected: `rhiza-cli` sparse-checks-out a bundle and dereferences symlinks on copy, so synced projects always receive real files (guarded by `test_no_symlinks_in_*`).

### Rendered pre-commit configs

`.pre-commit-config.yaml` is the one dogfood override that is **generated** rather than
hand-maintained, and so is every layer's copy of it. pre-commit hard-codes the filename,
so `python-core`, `rust-core` and `go-core` each ship the same path and are alternatives
rather than files that coexist — which used to mean the neutral two thirds of the config
(markdownlint, actionlint, schema validation, secret scanning, the rhiza hooks) were
duplicated per layer and kept in step by hand.

The fragments in `pre-commit/` invert that. `base.yaml` holds the neutral hooks once and
is a **mixin** — it declares no `output:`, so it is only ever pulled in via `extends:`.
Each other fragment holds only what it adds and declares where its rendered config goes:

| fragment | extends | renders to |
| --- | --- | --- |
| `base.yaml` | — | *(mixin — nothing)* |
| `python.yaml` | `base.yaml` | `bundles/python-core/.pre-commit-config.yaml` |
| `rhiza.yaml` | `python.yaml` | `.pre-commit-config.yaml` (this repo's own) |

`utils/render_precommit.py` merges a chain: `repos` dedupe by URL, hooks by `id`, and a
later hook replaces an earlier one with the same id — which is how `python.yaml` narrows
base's `check-yaml`. A later entry may omit `rev:` to inherit the pin; two fragments
pinning the same repo to *different* revs is an error rather than a silent pick. A
fragment may also `remove:` hooks or repos it does not want from its base. So a rev bump
in `base.yaml` reaches every layer through one edit.

**Never hand-edit a `.pre-commit-config.yaml`** — the header says so and the next render
would overwrite it. Edit the fragment, then:

```bash
make sync-precommit        # render every fragment that declares an output
make sync-precommit-check  # fail on drift without writing (CI drift guard)
```

Because the deployed configs are generated, `make fmt` is only as current as the last
render: **run `make sync-precommit` before `make fmt`**. CI enforces the same ordering —
the `pre-commit` job runs `sync-precommit-check` immediately before `make fmt`, so a
fragment edited without re-rendering fails there rather than quietly linting an older
hook set.

### Language layers

`core` used to be a Python project in disguise: it created a virtualenv, ran `uv sync`
and named Python gates in `all`. That half now lives in a **language layer** bundle,
and every profile pairs `core` with exactly one: `python-core`, `rust-core` or
`go-core`.

The contract between them is a set of **target names**. `book.mk`, `test.mk`, the CI
workflows and the release pipeline all call `make install` without knowing what the
project is written in, so a layer must define:

| target | owned by | means |
| --- | --- | --- |
| `install` | the layer | make the project's dependencies available |
| `all` | the layer | run the language's full gate set locally |
| `install-uv`, `fmt`, `todos`, `semgrep`, `doctor`, `clean` | core | language-neutral, whatever the project is |

Two rules follow. **Core must never define `install` or `all`** — `tests/api/test_language_layer.py`
asserts both halves behaviourally, for every layer. And **layers claim the same
deployment paths on purpose**: `.pre-commit-config.yaml` exists in all of them, and
`.bumpversion.toml` in the two non-Python ones, because those paths are fixed by the tools
that read them. A bundle declares
`layer: language` in `template-bundles.yml` to say so; the ownership tests then permit
overlap *within* a layer and still reject it everywhere else, and a separate test
fails any profile that selects two layers at once.

**Where the version config lives.** bump-my-version auto-discovers exactly four
filenames — `.bumpversion.toml`, `.bumpversion.cfg`, `setup.cfg`, `pyproject.toml` — and
reads nothing else without an explicit `--config-file`. Finding none it does not fail: it
falls back to `git describe`, so a release gets cut against the last reachable tag instead
of the project's version. That is why the block rhiza used to ship at `.rhiza/.cfg.toml`
was inert in every downstream repo (#1453), and the placement now differs by layer:

- **python-core ships nothing.** A Python project already owns `pyproject.toml`, where a
  `[tool.bumpversion]` table rewrites PEP 621 `[project].version` natively — no
  `current_version`, no `[[files]]` entry for pyproject itself. A synced
  `.bumpversion.toml` would *shadow* that table, so the repo declares its own block and
  the shipped `.rhiza/tests/test_pyproject.py` fails when it is missing or when it sets
  `commit`/`tag` to true.
- **rust-core and go-core ship a root `.bumpversion.toml`.** Neither language owns a
  discoverable file, so the layer must provide one. It deliberately omits
  `current_version` — a synced file cannot hold a value only the consuming repo can
  maintain — which makes bump-my-version read the version from the newest tag matching
  `tag_name`. For Go that is not a fallback but the definition; for Rust it is the
  invariant `Cargo.toml` is expected to satisfy anyway.

Both non-Python configs set `commit = false` and `tag = false`: `/rhiza:release` commits
and tags itself so the changelog lands in the bump commit.

**Gate parity between layers.** Same target names, different engines:

| target | python-core | rust-core | go-core |
| --- | --- | --- | --- |
| `install` | `uv venv` + `uv sync` | `rustup show` + `cargo fetch` | `go mod download` |
| `test` | pytest | `cargo nextest` + doctests | `go test ./...` |
| `coverage` | pytest-cov | `cargo llvm-cov` (same `_tests/coverage.xml` path) | `go test -coverprofile` + `gocover-cobertura` (same path) |
| `typecheck` | ty / mypy | `cargo clippy -D warnings` (rustc already type-checks) | `go vet` + golangci-lint (the compiler already type-checks) |
| `docs-coverage` | interrogate (%) | `RUSTDOCFLAGS=-D missing_docs` (pass/fail) | revive `exported` rule (pass/fail) |
| `security` | bandit + pip-audit | `cargo deny check advisories` | `govulncheck` |
| `license` | pip-licenses | `cargo deny check licenses` | `go-licenses check` |
| unused deps | `deptry` | `deps` → `cargo machete` | `deps` → `go mod tidy -diff` |

The Rust and Go layers also carry `test`/`coverage`/`typecheck`, which on the Python side
live in the separate `tests` bundle. That is not an inconsistency: pytest, coverage
and mypy each need configuration files worth bundling, while `cargo nextest` and
`go test` need no configuration at all — so a `rust-tests` or `go-tests` bundle would
own nothing but the gates themselves.

**Where Go differs from both.** A Go module has no manifest: its version *is* the git
tag, so unlike `pyproject.toml` and `Cargo.toml` there is no file in the tree for
bump-my-version to write to. `go-core` therefore ships a starter
`internal/version/version.go` holding a `Version` constant and anchors the release
config to it, which keeps the release commit and its tag in step. Delete that file and
the `/rhiza:release` flow has no version location to write to.

It ships that file's `version_test.go` too, and that one is about the test gate rather
than the release. `go test ./...` prints `[no test files]` for a package without one and
exits 0, so a freshly synced Go repo passed `make test` — and therefore `make all` —
while running nothing at all. Rust never had the hole: `cargo init --lib` leaves an
`it_works` test behind and the skeleton step preserves it. `go mod init` writes no Go
file whatsoever, so the layer has to bring the first test itself. What it asserts is the
release invariant next door — that `Version` matches the shape `.bumpversion.toml`
parses — never the literal shipped `0.0.0`, which bump-my-version rewrites in
`version.go` and not in the test.

Its `install` is also the thinnest of the
three — go.mod's `go`/`toolchain` directives make the go command fetch a matching
compiler on demand, so there is no rustup step to mirror.

`uv` sits in core, not in the Python layer, because rhiza runs pre-commit, mkdocs and
semgrep through `uvx` regardless of the project's language. What moved is the
*project* virtualenv and the `uv sync` of its declared dependencies.

**How a layer is tested — two suites, on purpose.** `tests/api/test_language_layer.py`
asserts the *contract* from `make -n` output: that a layer defines `install` and `all`,
that core defines neither, and that each gate name expands to the intended command.
That is fast, runs everywhere, and catches a renamed target or a gate dropped from
`all` — but it never invokes cargo, go or uv, so a recipe whose flags are wrong passes
it happily.

`tests/e2e/` closes that gap. For each layer it copies the bundles into a temp
directory (standing in for a `rhiza-cli` sync), writes the smallest project the layer
should be green on (`tests/e2e/scaffolds.py`), commits it, and runs every gate for
real — `install`, `test`, `coverage`, `typecheck`, `docs-coverage`, `security`,
`license`, `deps`, `fmt` and the `all` aggregate. The failure mode it exists for is
already on record: go-core's licence gate needs `--ignore $(go list -m)` because
go-licenses otherwise fails a freshly synced project *for having no LICENSE of its
own*, which no dry-run assertion could have found.

Two properties keep it from being merely expensive:

- **Opt-in.** Nothing runs without `RHIZA_E2E=1`; `make e2e` sets it. `make test` stays
  fast and green offline, and the whole matrix does not pay for it on every OS and
  Python version.
- **Toolchain-gated.** A layer whose compiler is absent skips with a reason rather than
  failing, so a developer with no Rust installed is not blocked by the Rust layer. The
  corollary matters: a green local run proves nothing on its own —
  `.github/workflows/rhiza_e2e.yml` (one job per layer, each installing only its own
  toolchain) is the only place all three actually execute.

Narrow the run with `make e2e E2E_ARGS=tests/e2e/test_go_layer_e2e.py`, which is how
each CI job selects its layer.

### Modular Makefile System

The root `Makefile` is intentionally thin (~10 lines) and only `include`s `.rhiza/rhiza.mk`. That file auto-loads everything in `.rhiza/make.d/*.mk` alphabetically.

**Each `*.mk` is owned by exactly one bundle** and syncs only when that bundle is adopted — so the file count reflects the bundle model, not accidental sprawl (a project without Docker never receives `docker.mk`). Edit the bundle source (`bundles/<owner>/.rhiza/make.d/<file>`); the root file is a dogfood symlink into it. Mapping:

| `.rhiza/make.d/` file | owner bundle | provides |
| --- | --- | --- |
| `bootstrap.mk` | core | `install-uv` tool bootstrap, install hooks, `clean` |
| `python.mk` | python-core | `install`, `all`, `deptry`, `license`, `rhiza-test` |
| `rust.mk` | rust-core | `install`, `all`, and the cargo-backed gates |
| `go.mk` | go-core | `install`, `all`, and the go-backed gates |
| `doctor.mk` | core | `make doctor` environment checks |
| `quality.mk` | core | `fmt`, `todos`, `semgrep` — the language-neutral gates |
| `custom-env.mk` | core | example stub: project variables |
| `custom-task.mk` | core | example stub: project targets/hooks |
| `test.mk` | tests | `test`, coverage, typecheck, stress, mutation |
| `book.mk` | book | `make book` docs build |
| `docker.mk` | docker | container build/run |
| `marimo.mk` | marimo | `make marimo` notebooks |
| `presentation.mk` | presentation | Marp slide build |
| `paper.mk` | paper | LaTeX paper compilation |
| `lfs.mk` | lfs | Git LFS install/track/status |
| `github.mk` | github | GitHub repo/workflow helpers |
| `bundles.mk` | *(mother-repo only — no bundle ships it)* | `explain-bundles`, `sync-self`, `sync-self-check`, `sync-precommit`, `sync-precommit-check`, `e2e` |

Hook targets use double-colon syntax (`pre-install::`, `post-install::`) and can be defined multiple times to chain behaviour. Add project-specific hooks directly in the root `Makefile` above the include line. Developer-local shortcuts go in `local.mk` (not committed).

### Dependency Management

`uv` manages all Python/dependency concerns:
- `.python-version` is the single source of truth for the Python version
- `uv.lock` pins all transitive dependencies — keep it in sync via `uv lock` or `uv sync`
- `uv run` transparently uses the project venv without manual activation

### Code Quality Requirements

- **Ruff** (`ruff.toml`): see `ruff.toml` for the authoritative and current enabled rule set (rule-prefix reference: https://docs.astral.sh/ruff/rules/)
- **Docstring coverage**: 100% (interrogate) — all public functions, classes, and modules require docstrings
- **Test coverage**: 90% minimum
- **Pre-commit hooks**: `make fmt` runs ruff, markdownlint, bandit, actionlint, interrogate, jsonschema, and uv-lock validation

> **Coverage in this repo (mother-repo specifics).** Rhiza has no `src/` and ships no
> runtime Python, so `make test` prints `Source folder src not found, running tests without
> coverage` and the main `tests/` suite runs *without* a Python coverage number — by design.
> Both that suite and `make rhiza-test` (which runs the shipped `.rhiza/tests/` suite) exercise
> Make targets, YAML, and bundle invariants behaviourally, where there is no Python module to
> cover. So "no coverage on `make test`" is expected here and does not mean anything is
> unmeasured. Downstream
> consumers that adopt the `tests` bundle *do* have a `src/` and get the full 90% `make test` gate.

### CI/CD

This repo runs on **GitHub Actions only**: `.github/workflows/` — CI, e2e, release, docker, CodeQL, weekly, sync. There is no root `.gitlab-ci.yml` here.

`rhiza_release.yml`'s `Validate Tag` job is the only gate the release path has, so all three of its checks are behavioural, not advisory: the release must not already exist, the version must be strictly newer than every published tag (#1126), and the tagged commit must be reachable from a branch (#1454). The last one exists because a release cut on a branch that is then squash-merged leaves its tag on the pre-squash commit, which nothing contains — `git describe` skips the release and a git-cliff regeneration *deletes* that version's CHANGELOG section, silently. A tag on a non-default branch (a maintenance release) warns rather than fails; only a genuinely orphaned commit is refused. `tests/api/test_release_tag_reachability.py` lifts that guard's shell out of the YAML and runs it against purpose-built repositories, so the logic is tested rather than the step name.

`rhiza_e2e.yml` is separate from `rhiza_ci.yml` rather than more jobs inside it: it installs three toolchains CI does not otherwise need, costs minutes per layer against CI's ≤20 min test budget, and is the only place the Rust and Go layers execute at all (see **Language layers** above).

GitLab support ships as a **template for downstream consumers**, not as active CI in this repo: the `gitlab` bundle (`bundles/gitlab/`) materializes a `.gitlab-ci.yml` plus `.gitlab/` pipelines into projects that adopt the `gitlab-project` profile, mirroring the GitHub Actions coverage there.

Because no GitLab pipeline runs here, `tests/bundles/test_gitlab_ci.py` validates the GitLab templates without a GitLab host: it assembles a `gitlab-project` and (1) checks every container image the pipeline/Dockerfiles reference actually exists on its registry (the guard that catches a retired tag like the removed `uv:*-bookworm`), (2) runs `gitlab-ci-local` (pinned, via `npx`) to resolve every `include:` and validate the merged pipeline against GitLab's JSON schema. A third test actually runs a job in Docker against the pinned `$UV_IMAGE` — it needs Docker and is opt-in: `RHIZA_GITLAB_DOCKER=1 make test` (or run it directly). All three skip cleanly when their dependency (network / Node / Docker) is absent, so `make test` stays green offline.
