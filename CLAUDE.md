# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

It describes the repository **as it is today**. The reasons behind each rule — which
mechanisms were retired, what broke, and which test now pins the lesson — live in
[`docs/development/HISTORY.md`](docs/development/HISTORY.md). Read that before undoing a
rule that looks arbitrary; most of them were learned the hard way.

## What is Rhiza?

Rhiza is a **collection of reusable configuration templates** for Python, Rust and Go projects — not a runtime library. It has no `src/` directory and no runtime dependencies. Its purpose is to provide and continuously synchronize development infrastructure (the `Makefile` front door, CI workflows, linting configs, test setups) into downstream projects. The sync is performed by the `rhiza` Claude Code plugin ([rhiza-claude](https://github.com/Jebel-Quant/rhiza-claude)) — `/rhiza:update`. Nothing in this repo depends on the archived `rhiza-cli` package.

Downstream projects adopt Rhiza by adding a `.rhiza/template.yml` that lists which bundles to sync from this repository.

## Commands

```bash
make install      # Full setup: installs uv, Python from .python-version, creates .venv, installs deps
make test         # Run all tests with the coverage gate
make fmt          # Run all hooks via prek (ruff, markdownlint, bandit, actionlint, interrogate, ...)
make deps         # Check for unused/missing dependencies (deptry)
make docs-coverage  # Docstring coverage with interrogate (100% required)
make typecheck    # ty and mypy --strict over utils/
make security     # bandit security scan
make rhiza-test   # Conformance checks from pytest-rhiza
make benchmark    # Performance benchmarks
make e2e          # Language-layer end-to-end suite (opt-in, real toolchains)
make book         # Build documentation
make sync-self    # Relink root dogfood files as symlinks into bundles/
```

Run a single test with `uv run pytest tests/api/test_makefile_targets.py::TestClass::test_method -v`.

## Command Execution Policy

Follow this order strictly:

1. If a `make` target exists → use `make <target>`
2. No `make` target → use `uv run <command>`
3. Never invoke `.venv/bin/python`, `.venv/bin/pytest`, etc. directly

The virtual environment is managed automatically by `make` and `uv run`. No manual activation is needed.

## Architecture

### Template bundles

The core abstraction is the **bundle** — a named group of configuration files. All bundles
are defined in `.rhiza/template-bundles.yml` (the authoritative list) and live under
`bundles/<name>/`.

**Feature bundles:**

- `core` (required, language-neutral): `.editorconfig`, `cliff.toml`, `.gitignore`,
  `.rhiza/semgrep.yml`, and the `Makefile` front door. It defines no `install` and no `all`.
- `python-core`, `rust-core`, `go-core`: the **language layers** (see below).
- `benchmarks`: pytest-benchmark infrastructure and reporting.
- `github`, `gitlab`: platform configuration and core workflows.
- `docker`, `devcontainer`: containerisation.
- `vscode`: recommended extensions and workspace settings for local editing.
- `book`: documentation with MkDocs + zensical.
- `presentation`: Marp slides.
- `lfs`, `legal`, `renovate`: miscellaneous tooling.

**Platform overlay bundles** pair a feature with a CI platform: `github-tests`,
`github-book`, `github-marimo`, `github-docker`, `github-devcontainer`, `github-paper`,
`github-quality-review`, `gitlab-tests`, `gitlab-book`, `gitlab-marimo`,
`gitlab-quality-review`. They ship workflow stubs and require the language layer whose
gates they run.

**Profiles** (meta-bundles) are curated compositions: `github-project`, `gitlab-project`,
`local` (no hosted CI), `rust-local` and `go-local`.

### Dogfooding: `bundles/` is the single source of truth

The files rhiza ships also live at the repo root so this repo runs on its own
infrastructure. Each root dogfood file is a **relative symlink into its owning bundle**
(e.g. `Makefile` → `bundles/core/Makefile`).

- **Edit the bundle file**, never the root path. The root follows automatically.
- After adding a bundle file, run `make sync-self` to create its root link;
  `make sync-self-check` is the local dry-run.
- In CI the invariant is guarded by `tests/bundles/test_bundle_dogfood_symlinks.py`, which
  reuses `utils/link_dogfood.py`'s own carve-out predicate.

Some files **cannot** be symlinks and stay real copies, kept in sync by
`tests/bundles/test_bundle_*_sync.py`:

- `.github/*` platform config and live `.github/workflows/*` — GitHub does not resolve
  symlinks there. Live workflows deliberately differ from the bundle stubs.
- `rulesets/main-branch-protection.json` — the bundle copy prefixes its required context
  with `ci /` because downstream stubs delegate through a `ci` job. Both copies require
  the aggregate `CI gate` check; the root copy also requires `E2E gate`, which consumers
  never run. Changing the file changes no live setting; re-apply
  it (see `docs/ops/BRANCH_PROTECTION.md`). `rhiza_weekly.yml`'s `ruleset-drift` job fails
  when the live required checks differ from the file (`tests/api/test_weekly_ruleset_drift.py`).
- `.gitignore` / `.gitattributes` files — git opens these with `O_NOFOLLOW`.

Intentional mother-repo overrides that diverge from their bundle source: root `.gitignore`,
`.pre-commit-config.yaml`, `.python-version`, `SECURITY.md`, `renovate.json`. The
exclusion list lives in `utils/link_dogfood.py`. Synced consumers always receive real
files, never symlinks.

### Language layers

Every profile pairs `core` with exactly one language layer. CI workflows and the release
pipeline call targets by name without knowing the language, so the contract is a set of
target names:

| target | owned by | means |
| --- | --- | --- |
| `install` | the layer | make the project's dependencies available |
| `all` | the layer | run the language's full gate set locally |
| `install-uv`, `fmt`, `todos`, `semgrep`, `doctor`, `clean` | core | language-neutral |

Rules:

- **Core never defines `install` or `all`** (`tests/api/test_language_layer.py`).
- Layers share deployment paths on purpose (`.pre-commit-config.yaml`, `.bumpversion.toml`)
  and declare `layer: language` in `template-bundles.yml`. A profile selecting two layers
  fails the tests.
- Each layer owns `test`, `coverage`, `typecheck`, `docs-coverage`, `security`, `license`
  and `deps` — same names, different engines:

| target | python-core | rust-core | go-core |
| --- | --- | --- | --- |
| `install` | `uv venv` + `uv sync` | `rustup show` + `cargo fetch` | `go mod download` |
| `test` | pytest | `cargo nextest` + doctests | `go test ./...` |
| `coverage` | pytest-cov | `cargo llvm-cov` | `go test -coverprofile` + `gocover-cobertura` |
| `typecheck` | ty / mypy | `cargo clippy -D warnings` | `go vet` + golangci-lint |
| `docs-coverage` | interrogate | `RUSTDOCFLAGS=-D missing_docs` | revive `exported` rule |
| `security` | bandit | `cargo deny check advisories` | `govulncheck` |
| `license` | pip-licenses | `cargo deny check licenses` | `go-licenses check` |
| `deps` | `deptry` | `cargo machete` | `go mod tidy -diff` |

- `python-core` and `go-core` ship a **starter test** (`tests/test_rhiza_packaging.py`,
  `internal/version/version_test.go`), because a freshly synced repo with no tests would
  otherwise pass `make test` while running nothing.

**Two test suites cover the layers.** `tests/api/test_language_layer.py` asserts the
contract from dry-run output — fast, offline, never invokes a toolchain. `tests/e2e/`
syncs each layer into a temp scaffold and runs every gate for real. It is opt-in
(`RHIZA_E2E=1`, set by `make e2e`) and skips a layer whose toolchain is absent, so only
`.github/workflows/rhiza_e2e.yml` proves all three. Narrow a run with
`make e2e E2E_ARGS=tests/e2e/test_go_layer_e2e.py`.

### Where the version config lives

bump-my-version reads only `.bumpversion.toml`, `.bumpversion.cfg`, `setup.cfg` or
`pyproject.toml`; finding none it silently falls back to `git describe`.

- **python-core ships none.** The project's own `pyproject.toml` carries a
  `[tool.bumpversion]` table; pytest-rhiza's `test_pyproject` fails without it or when it
  sets `commit`/`tag` to true.
- **rust-core and go-core ship `.bumpversion.toml`** without `current_version`, so the
  version is read from the newest matching tag. go-core also ships
  `internal/version/version.go` as the file the release rewrites.
- `commit = false` and `tag = false` everywhere: `/rhiza:release` commits and tags itself.
- A Python project may derive its version from the tag (`dynamic = ["version"]`). This
  repo does. Any job building a distribution then needs `fetch-depth: 0`.
- `rhiza_release.yml` verifies a release in two steps: the declared version (skipped when
  dynamic), then the version of what `dist-check --strict` actually built in `dist/`.
  `tests/api/test_release_version_verification.py` runs both against fixture projects.

### The Makefile is a shim over a pinned CLI

There is no synced make layer: no `.rhiza/rhiza.mk`, no `.rhiza/make.d/`. The only make
file shipped is `bundles/core/Makefile`, a short shim whose `%:` catch-all forwards every
target to a pinned `rhiza-task` CLI. `RHIZA_TASK` in that file is the whole version
contract, and the file is template-owned, so a pin bump arrives with a sync.

- Repo-owned targets go in **`local.mk`**, which the Makefile `-include`s and core does
  not gitignore. This repo's `explain-bundles`, `sync-self`, `sync-self-check` and `e2e`
  live there. `tests/api/test_makefile_targets.py` keeps the shim free of repo-owned rules.
- To add a hook around a CLI task, shadow the target with an explicit rule in `local.mk`.
- `tests/api/test_bundle_cli_targets.py` asks the pinned CLI version which tasks it has
  and requires every target the retired make fragments provided (needs network; skips
  offline).
- Docs must not spell a retired target as a `make <target>` code span:
  `tests/docs/test_doc_consistency.py` requires every such span to resolve.

### Settings

Project settings live in `[tool.rhiza-task]` in `pyproject.toml` (or a root `rhiza.toml`
for non-Python layers; `pyproject.toml` wins where both exist). Resolution order:
defaults → `.rhiza/.env` → `pyproject.toml` → `RHIZA_*` environment → CLI flags.

- `.rhiza/.env` is gitignored and developer-local; core ships none.
- This repo sets `source-folder = "utils"` and `layers = ["python"]`. **Leave
  `source-folder` alone**: without it gates resolve `src`, which does not exist, and the
  CLI *skips* a missing folder — `typecheck`, `security`, `docs-coverage`, `deps` and
  `semgrep` would all pass having measured nothing. `tests/utils/test_gate_scope.py`
  asserts the folder exists and holds Python.

### The rhiza checks are a dependency

`make rhiza-test` runs [pytest-rhiza](https://github.com/jebel-quant/pytest-rhiza)
conformance checks against the repo — README fences, release tags, manifest and
bump-my-version wiring. The check set is derived from the `layers` setting: neutral
checks (`test_readme`, `test_release_tags`, `test_readme_validation`) plus the active
layer's (`test_pyproject`, `test_docstrings` for Python; `test_cargo_toml` for Rust;
`test_go_module` for Go). The version is pinned through the `pytest-rhiza` setting.

### Dependencies and code quality

- `.python-version` is the single source of truth for the Python version; `uv.lock` pins
  everything else. A dependency group earns its place only if `tests/` or a notebook
  imports it — tools run through `uvx` or `--with` are not declared.
- **Ruff**: `ruff.toml` holds the authoritative rule set.
- **Docstrings**: 100% interrogate coverage over `utils` and `tests`.
- **Tests**: the coverage floor `make test` enforces, measured over `utils`.
- **Hooks**: the runner is [prek](https://github.com/j178/prek), reading
  `.pre-commit-config.yaml`. `make fmt` and every layer's `install` pass
  `--config .pre-commit-config.yaml` explicitly, because prek otherwise also runs the
  template configs nested under `bundles/*-core/`.
- prek's `--all-files` only sees tracked files: `git add` new files before `make fmt`.

### Template ownership in consumers

All three layers run rhiza-hooks' `check-managed-files`, which rejects a commit changing a
file listed in `.rhiza/template.lock` (minus `exclude:` entries). Only the sync commit in
`/rhiza:update` bypasses it, with `SKIP=check-managed-files`; nothing else should. The
mother repo's root `.pre-commit-config.yaml` does not carry the hook, because there is no
lock here.

### CI/CD

This repo runs on **GitHub Actions only** (`.github/workflows/`). There is no root
`.gitlab-ci.yml`; GitLab support ships as the `gitlab` bundle for downstream consumers,
validated by `tests/bundles/test_gitlab_ci.py` without a GitLab host.

- `rhiza_ci.yml` runs every gate, plus `dist-check` and `license`, and rolls them into one
  `CI gate` job — a required check.
- `rhiza_e2e.yml` is the only place the Rust and Go layers execute. Its `E2E gate` job is
  the mother repo's second required check, passing only when every layer succeeded.
- Python dependency advisories are audited **weekly**, not gated: `rhiza_weekly.yml`'s
  `advisories` job (and GitLab's `weekly:advisories`) runs `pip-audit` over the committed
  `uv.lock`. The Python `security` task stays bandit-only, so an advisory published today
  never fails a pull request (`tests/api/test_weekly_advisories.py`).
- `rhiza_release.yml`'s `Validate Tag` job refuses an existing release, a version not
  newer than every tag, and a tag on a commit no branch contains.
  `tests/api/test_release_tag_reachability.py` runs that guard's shell.
- Workflow stubs forward secrets **by name**; `secrets: inherit` is banned. Every secret a
  reusable workflow reads must be declared under `workflow_call.secrets` and mapped in its
  stub (`TestSecretForwarding` in `tests/api/test_workflow_hygiene.py`).
- `rhiza_docker.yml` passes `GH_PAT` and `UV_EXTRA_INDEX_URL` as BuildKit **secrets**,
  never build args (`tests/bundles/test_docker_build_secrets.py`).
- `rhiza_paper.yml` runs rhiza-task's `paper` task with `--strict`, using a pinned static
  tectonic binary. `rhiza_book.yml` installs the same engine when a `*.tex` exists (the
  `book` task builds the paper) and runs `book-nav` after the build.
- [zizmor](https://docs.zizmor.sh) audits the live and bundle workflows, actions, dependabot
  and pre-commit configs as a root `.pre-commit-config.yaml` hook, so a finding fails
  `CI gate`. Fix findings at the source; an exception goes in `.github/zizmor.yml` with
  its reason (`tests/api/test_zizmor_gate.py`). Mother repo only, not shipped. The hook runs
  `--offline`; `rhiza_weekly.yml`'s `zizmor-online` job adds the audits that need the GitHub
  API, with the hook's version and file set (`tests/api/test_weekly_zizmor.py`).
- When adding a gate, make sure it cannot pass by skipping: a green run that measured
  nothing is the failure this repo has hit most often (see
  [`docs/development/HISTORY.md`](docs/development/HISTORY.md)).
