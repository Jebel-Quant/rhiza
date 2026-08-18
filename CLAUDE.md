# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Rhiza?

Rhiza is a **collection of reusable configuration templates** for Python projects — not a runtime library. It has no `src/` directory and no runtime dependencies. Its purpose is to provide and continuously synchronize development infrastructure (Makefiles, CI workflows, linting configs, test setups) into downstream projects via the separate `rhiza-cli` tool.

Downstream projects adopt Rhiza by adding a `.rhiza/template.yml` that lists which bundles to sync from this repository.

## Commands

```bash
make install      # Full setup: installs uv, downloads Python version from .python-version, creates .venv, installs deps
make test         # Run all tests with coverage (90% minimum required)
make fmt          # Run all hooks via prek (ruff format/check, markdownlint, bandit, etc.)
make deps         # Check for unused/missing dependencies
make docs-coverage  # Check docstring coverage with interrogate (100% required)
make typecheck    # Static type checking with ty and mypy --strict (TYPECHECKER=ty|mypy|both)
make benchmark    # Performance benchmarks
make hypothesis-test  # Property-based tests only
make stress       # Load/concurrency tests
make security     # bandit security scan
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
  `.bandit`, the pre-commit config, `pytest.ini`, and `.rhiza/make.d/python.mk`
  (`install`, `all`, `deps`, `license`, plus `test`, `typecheck`, `security` and
  `docs-coverage` — see **Language layers**). Ships no bump-my-version config — see
  **Where the version config lives**.
- `rust-core` (the Rust **language layer**): `rust-toolchain.toml`, `rustfmt.toml`,
  `clippy.toml`, `deny.toml`, a Rust pre-commit config, `.bumpversion.toml`, and
  `.rhiza/make.d/rust.mk`. Carries its own test targets, as every layer now does —
  see **Language layers**.
- `go-core` (the Go **language layer**): `.golangci.yml`, `revive.toml`, a Go
  pre-commit config, `.bumpversion.toml`, a starter `internal/version/version.go`
  with its `version_test.go`, and `.rhiza/make.d/go.mk`. Carries its own test
  targets, like the other two.
- `tests`: optional Python testing extras — `benchmark`, `hypothesis-test`, `stress`,
  `mutation` (requires `python-core`; the gates `all` names live in the layer)
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

Plus intentional mother-repo overrides that deliberately diverge from their bundle source: root `.gitignore`, `.pre-commit-config.yaml`, `.python-version`, `SECURITY.md`, `renovate.json`. The exclusion list lives in `utils/link_dogfood.py`. Downstream consumers are unaffected: `rhiza-cli` sparse-checks-out a bundle and dereferences symlinks on copy, so synced projects always receive real files (guarded by `test_no_symlinks_in_*`).

**What guards the invariant in CI is `tests/bundles/test_bundle_dogfood_symlinks.py`, not `make sync-self-check`.** The test runs inside `make test` on every push and PR, and it reuses `link_dogfood`'s own carve-out predicate and bundle index, so the guard and the linker cannot disagree about the rules. `sync-self-check` is the *local* equivalent — the same `--check` pass, for running before you commit a new bundle file — and no workflow invokes it. It was described as "the CI drift guard" in four places until #1532, which is the kind of claim that stops anyone checking whether the real guard still exists.

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
  pytest-rhiza's `test_pyproject` check — which the layer names in `RHIZA_CHECKS` — fails
  when it is missing or when it sets `commit`/`tag` to true.
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
| `security` | bandit | `cargo deny check advisories` | `govulncheck` |
| `license` | pip-licenses | `cargo deny check licenses` | `go-licenses check` |
| `deps` | `deptry` | `cargo machete` | `go mod tidy -diff` |

Every row is a **shared target name** with a different engine behind it — including
`deps`, which until #1474 was the one exception: python-core named it `deptry`, after the
tool, so `make deps` failed on Python and `make deptry` on the other two. The tool-named
`DEPTRY_FOLDERS`/`DEPTRY_IGNORE` variables stay, because they name deptry's *arguments*
(marimo.mk appends `--ignore DEP004`) and are the accumulator interface a downstream
`local.mk` writes to. `make deptry` survives as a deprecated alias that warns.
`tests/bundles/test_layer_contract.py::TestEveryLayerDefinesTheSameGateNames` now fails on
the next divergence rather than documenting it.

**Where each Python gate looks, and how to add a folder.** python-core's four path-scoped
gates take their folder list from an accumulator, all seeded from `SOURCE_FOLDER` when it
exists: `TYPECHECK_FOLDERS`, `BANDIT_FOLDERS`, `DOCSTRING_FOLDERS` and the older
`DEPTRY_FOLDERS`/`DEPTRY_IGNORE` pair. A bundle or a consuming `Makefile`/`local.mk` adds
a folder by appending, the way marimo.mk contributes its notebooks.

Only `deps` had that shape before #1505; the other three hard-coded `SOURCE_FOLDER`, so
Python kept *outside* the source root was unreachable by three of the four static gates.
The mother repo was the extreme case — it ships configuration, not a library, so it has no
`src/` at all and `typecheck`, `security` and `deps` each exited **0** having measured
nothing, on the very repo that ships those gates to everyone else. `utils/` (the tooling
behind `make sync-self` and the `sync-self-check` drift check) was contributed from
`.rhiza/make.d/bundles.mk`, a mother-repo-only fragment, because the root `Makefile` could
not hold it while it was a dogfood symlink into `bundles/core/`.

**All of that is now history for this repo**, though the accumulators still ship. rhiza runs
on the rhiza-task shim, whose config has no accumulators at all: every path-scoped gate reads
one `source_folder`, and `pyproject.toml` declares `source-folder = "utils"`. Six `+=` lines
became one setting. `tests/utils/test_gate_scope.py` still asserts the outcome rather than the
wiring — the folder must exist and hold Python — which is why it survived the migration when
the assertions it made did not.

One consequence worth knowing when reading `make -n`: the folder list is expanded by
**make**, not by the recipe's shell, so a dry run shows the real scope. The `[ -d ... ]`
form it replaced printed its warning whether or not the branch would fire, which made a
dry run's warnings meaningless as evidence either way. Note that this cuts both ways when
writing an assertion: a dry run prints *both* arms of an `if`, so the presence of a skip
message proves nothing — only the expanded folder list does.

**The `SOURCE_FOLDER` seed is deferred, and where you set the variable no longer matters.**
Each accumulator appends `$(wildcard $(SOURCE_FOLDER))` rather than sitting inside an
`ifneq ($(wildcard $(SOURCE_FOLDER)),)`. `?=` makes these *recursive* variables, so the
appended text is expanded when a gate reads it — after every makefile has been parsed —
whereas an `ifneq` is decided where it is written, while python.mk is still being read.

That difference was load-bearing until #1534, because the root `Makefile` reads `local.mk`
*after* `include .rhiza/rhiza.mk`. A project whose source root is not `src/` and which set
`SOURCE_FOLDER` there had the conditional already decided against it on the `?= src`
default, so `deps`, `typecheck`, `security`, `docs-coverage` and `test` all fell through to
their empty-list branch and exited **0** having measured nothing — the same silent
measure-nothing failure as #1505, #1511 and #1516, but reached through a documented
configuration surface rather than a hard-coded path. It survived because every channel the
override tests cover — the command line, `.rhiza/.env`, the root `Makefile` above the
include — is read *before* python.mk is parsed, so none of them could see it.
`tests/api/test_make_variable_overrides.py::TestSourceFolderFromLocalMk` now pins all five
gates against a `local.mk`-declared source root.

Appending has always worked from `local.mk` and still does; it was only *setting*
`SOURCE_FOLDER` that was position-dependent.

**Where a project's settings live — and why core ships no `.rhiza/.env`.** It used to,
and the file was pure liability. Its entire payload was `SOURCE_FOLDER=src` and
`MARIMO_FOLDER=docs/notebooks`, both *identical* to the `?=` defaults in `rhiza.mk`
directly below the include — so it carried no information any reader could act on. What it
did carry was precedence: a makefile assignment outranks an exported environment variable
in GNU make (only a command-line `make VAR=...` beats it), so naming a variable in that
file took it out of reach of every caller that exported it. That is the whole mechanism of
#1545 — `RHIZA_CI_OS_MATRIX` was pinned there, and `rhiza_ci.yml`'s per-caller export was
silently discarded for the mother repo and consumers alike. Deleting the file changes no
resolved value and removes the mechanism, which is why the guard is now
`test_core_ships_no_env_file_at_all` rather than an assertion about one line inside it.

The documented home is a `[tool.rhiza-task]` table in `pyproject.toml`: layer 3 of
rhiza-task's five-layer order (defaults → `.rhiza/.env` → `pyproject.toml` → `RHIZA_*`
environment → CLI flags), typed by TOML rather than parsed out of strings. Two caveats
worth knowing before moving anything there:

- **`rhiza.mk` does not read it.** A repo on the synced make layer resolves settings
  through `?=`, the root `Makefile` and `.rhiza/.env`; the table is inert until the repo
  moves to `uvx rhiza-task shim`. So this repo's own `MKDOCS_EXTRA_PACKAGES` override stays
  in the root `Makefile` — relocating it to `pyproject.toml` today would silently break
  `make book`. Only the CI `generate-matrix` step reads the table here, because that step
  is the one caller already going through the CLI.
- **It is Python-only.** `_from_pyproject` reads `pyproject.toml` and nothing else, so
  `rust-core` and `go-core` have no equivalent — a crate has `Cargo.toml`, a Go module has
  no manifest at all. Those layers keep `.rhiza/.env` and the root `Makefile` as their only
  settings surfaces until rhiza-task grows a language-neutral source.

`.rhiza/.env` itself stays supported and `rhiza.mk` still `-include`s it — what changed is
that the file is now unambiguously **repo-owned**, which also resolves the standing
contradiction with "never modify files in `.rhiza/`".

All three layers carry `test`/`coverage`/`typecheck` themselves. Python's used to live
in the separate `tests` bundle, and that was a real inconsistency rather than a
considered asymmetry: `python.mk`'s own `all` named them while `tests` defined them, and
nothing made `tests` arrive — the dependency runs the other way, so `core + python-core`
alone had an `all` that died on a missing rule (#1475). No shipped profile reached it,
which is why it survived; `tests/bundles/test_layer_contract.py::TestALayersAllIsSatisfiableOnItsOwn`
now pins the property for every layer.

What `tests` still owns is what is genuinely optional — `benchmark`, `hypothesis-test`,
`stress` and `mutation`, each needing its own tool and folder convention, and none named
by any `all`. There is still no `rust-tests` or `go-tests` bundle, for the original
reason: `cargo nextest` and `go test` need no configuration, so such a bundle would own
nothing at all.

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

**Two of the three layers ship a starter test, for the same reason.** Python had the
identical hole (#1476): `make test` searches `TESTS_FOLDER` for `test_*.py`, and finding
none it warns and **exits 0**, so a freshly synced Python repo passed `make test` — and
`make all` — measuring nothing. Note that the rhiza checks do not help, since they run
under the separate `rhiza-test` gate and none of them looks at `TESTS_FOLDER`. So
`python-core` ships `tests/test_rhiza_packaging.py`, asserting that the version installed
into the environment matches `[project].version` — a real invariant (it catches a stale
editable install or a build backend pointed at the wrong tree), distinct from the
`test_pyproject` check's pyproject-versus-tag assertion, and one that skips cleanly on a
repo with no distribution of its own, such as this one.

Both layers' e2e assertions name the **shipped** file rather than the scaffold's own
test, and that is the load-bearing part: `scaffolds.py` writes a test into every
scaffold, so an item-count assertion stays green even if the layer ships no starter at
all. That is precisely how the Go hole survived until #1467. The Python check reads the
gate's HTML report rather than stdout, because `test` runs pytest under xdist, which
prints a bare progress line and never names a file — and reading the report lets it
require *Passed* rather than merely collected, since a silently skipped starter measures
nothing either.

Its `install` is also the thinnest of the
three — go.mod's `go`/`toolchain` directives make the go command fetch a matching
compiler on demand, so there is no rustup step to mirror.

`uv` sits in core, not in the Python layer, because rhiza runs prek, mkdocs and
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

### The rhiza checks are a dependency, not synced files

`make rhiza-test` runs rhiza's **conformance checks** — the assertions about a consuming
repository, as distinct from the mother repo's own `tests/` suite. They validate the
README's fences, the release tags, and whichever manifest the project has, with its
bump-my-version wiring.

Until #1540 they were **code distributed by file-copy**: seven modules plus a `conftest.py`
synced into `.rhiza/tests/`, one file per bundle that owned an assertion. They are now
[pytest-rhiza](https://github.com/jebel-quant/pytest-rhiza), installed by the gate. What
changed is only the delivery — the ownership model is identical, and deliberately so.

**Ownership still lives with the bundle, as a `RHIZA_CHECKS` accumulator.** core's
`quality.mk` declares it and seeds the two language-neutral checks; `python-core`,
`rust-core`, `go-core` and `tests` each append their own. One `+=` line per bundle replaces
one synced file per bundle, so which checks apply is still resolved *at sync time* by which
bundles a project selected — nothing sniffs the manifest at runtime to decide, which is
what keeps a misconfigured repo going red instead of quietly skipping a check.

| check | contributed by | replaces |
| --- | --- | --- |
| `test_readme` | core | `.rhiza/tests/test_readme.py` |
| `test_release_tags` | core | `.rhiza/tests/test_release_tags.py` |
| `test_pyproject` | python-core | `.rhiza/tests/test_pyproject.py` |
| `test_docstrings` | python-core | `.rhiza/tests/test_docstrings.py` |
| `test_readme_validation` | tests | `.rhiza/tests/test_readme_validation.py` |
| `test_cargo_toml` | rust-core | `.rhiza/tests/test_cargo_toml.py` |
| `test_go_module` | go-core | `.rhiza/tests/test_go_module.py` |

Five costs of the copy went with it: seven template-owned files in every consumer's tree;
`pythonpath = .rhiza/tests` in `pytest.ini`, which existed only so the synced suite could
import itself; `.rhiza/tests` folded into `docs-coverage`'s interrogate paths, holding
*template* code to the project's 100% docstring bar; the four `--with` flags the recipe
spelled out, because a copied file carries no dependency metadata; and the duplication the
copy imposed — `SKIP_FLAG`/`_should_skip` existed twice because bundles are copied
independently, so a shared helper had no third home.

Three details are worth knowing before editing this:

- **The accumulator's `?= ` empty / `+=` seed shape is load-bearing, not cosmetic.**
  `rhiza.mk` includes `make.d/*.mk` alphabetically, so `go.mk` and `python.mk` are read
  *before* `quality.mk`. In make, `+=` on an undefined variable defines it — so a bare
  `RHIZA_CHECKS ?= <core's two>` would be skipped as already-defined on exactly those two
  layers, and a Python or Go project would run its own checks while silently losing the
  neutral pair. Each layer's `test_rhiza_test_selects_this_layers_checks_and_cores` asserts
  both halves resolve.
- **The version is pinned, and the pin travels in the template.** File-copy delivery had
  one virtue: a repo synced at a release ran exactly that release's assertions.
  `RHIZA_CHECKS_VERSION` in `quality.mk` keeps that property — one number, bumped here and
  delivered by the next sync — rather than letting the checks and the template drift on two
  independent version axes. A consumer who wants to lead or lag overrides it.
- **The gate prints its resolved check list, and the tests assert on that line.** Under
  `--pyargs`, pytest reports node ids with **no file name at all**, so grepping a run's
  output for a module's filename proves nothing either way — which is what the e2e and
  layer-contract assertions used to do against the synced files.

A consumer that syncs past #1540 keeps its old `.rhiza/tests/` on disk, because a sync
ceasing to deliver a file does not delete it. Nothing runs it — the gate names modules, not
paths — so it is inert rather than duplicated, and `rhiza-test` warns while the folder is
still there.

### Modular Makefile System — shipped, but no longer run here

> **This repo no longer runs the synced make layer.** rhiza migrated to
> [rhiza-task](https://github.com/Jebel-Quant/rhiza-task): the root `Makefile` is now a
> repo-owned shim (`uvx rhiza-task shim`) whose `%:` catch-all forwards any target to the
> pinned CLI, so `make test` still works and no longer *contains* anything. There is no root
> `.rhiza/rhiza.mk` and no root `.rhiza/make.d/`.
>
> The bundles still ship the layer described below, so this section documents what a
> **consumer** receives until they migrate too. Three consequences worth knowing:
>
> - **`.rhiza/make.d/` files are no longer dogfood symlinks.** They are bundle-only, which
>   costs the byte-for-byte guard in `tests/bundles/test_bundle_rhiza_sync.py`; the
>   `_NOT_DOGFOODED_PATHS` carve-out there records it, and `utils/link_dogfood.py` carries
>   the matching `_MAKE_LAYER_PREFIXES` so `make sync-self` does not helpfully recreate the
>   whole layer at the root.
> - **The fragments are still tested**, by assembly rather than by dogfooding:
>   `tests/api/` and `tests/integration/` build their sandbox with `sync_bundles`, and
>   `tests/e2e/` runs the assembled gates against real toolchains.
> - **Not everything has a CLI equivalent yet.** `paper`, `presentation`, `install-uv` and
>   the `deptry` alias exist only in the fragments, so those bundles cannot retire until
>   rhiza-task grows tasks for them.

The root `Makefile` a consumer receives is intentionally thin and only `include`s `.rhiza/rhiza.mk`. That file auto-loads everything in `.rhiza/make.d/*.mk` alphabetically.

**Each `*.mk` is owned by exactly one bundle** and syncs only when that bundle is adopted — so the file count reflects the bundle model, not accidental sprawl (a project without Docker never receives `docker.mk`). Edit the bundle source (`bundles/<owner>/.rhiza/make.d/<file>`). Mapping:

| `.rhiza/make.d/` file | owner bundle | provides |
| --- | --- | --- |
| `bootstrap.mk` | core | `install-uv` tool bootstrap, install hooks, `clean` |
| `python.mk` | python-core | `install`, `all`, `deps`, `license`, and the pytest-backed gates |
| `rust.mk` | rust-core | `install`, `all`, and the cargo-backed gates |
| `go.mk` | go-core | `install`, `all`, and the go-backed gates |
| `doctor.mk` | core | `make doctor` environment checks |
| `quality.mk` | core | `fmt`, `todos`, `semgrep`, `rhiza-test` (and the `RHIZA_CHECKS` accumulator) — the language-neutral gates |
| `custom-env.mk` | core | example stub: project variables |
| `custom-task.mk` | core | example stub: project targets/hooks |
| `test.mk` | tests | `benchmark`, `hypothesis-test`, `stress`, `mutation` — the optional extras |
| `book.mk` | book | `make book` docs build |
| `docker.mk` | docker | container build/run |
| `marimo.mk` | marimo | `make marimo` notebooks |
| `presentation.mk` | presentation | Marp slide build |
| `paper.mk` | paper | LaTeX paper compilation |
| `lfs.mk` | lfs | Git LFS install/track/status |
| `github.mk` | github | GitHub repo/workflow helpers |

Hook targets use double-colon syntax (`pre-install::`, `post-install::`) and can be defined multiple times to chain behaviour. Add project-specific hooks directly in the root `Makefile` above the include line. Developer-local shortcuts go in `local.mk` (not committed).

**The `::` hooks have no equivalent under the shim**, and this is the one documented capability the migration costs. `bootstrap.mk` anchors `pre-install::`/`post-install::` as no-ops precisely so a consumer can chain onto them; `uvx rhiza-task install` knows nothing about make targets, so a `post-install::` rule in a shim'd repo never runs. The workaround is to shadow the target instead of chaining onto it — an explicit `install:` rule beats the `%:` pattern rule, so it can call the CLI and then the extra step. This repo does exactly that for `rhiza-test` (see below).

**Where `bundles.mk` went.** The mother-repo-only fragment that used to sit in this table — `explain-bundles`, `sync-self`, `sync-self-check`, `e2e`, `gitlab-docker-test` — is now a section of the root `Makefile`. Not `local.mk`, which is gitignored: CI invokes `make e2e` (`rhiza_e2e.yml`) and `make gitlab-docker-test` (`rhiza_weekly.yml`), so they need a committed home. Its six `*_FOLDERS += utils` accumulators became one `source-folder = "utils"` in `pyproject.toml`'s `[tool.rhiza-task]`.

**And why `rhiza-test` is wrapped rather than delegated.** pytest-rhiza's `test_docstrings` reads its scope from the `RHIZA_DOCTEST_FOLDERS` environment variable; `quality.mk` exported it from `DOCSTRING_FOLDERS`, and rhiza-task does not (Jebel-Quant/rhiza-task#18). On a bare delegation the check reported `SKIPPED  No doctest folder found (looked for: src)` while the gate still said `ok rhiza-test` — #1517 exactly, this repo's only doctest examples unchecked behind a green gate. `.rhiza/.env` cannot carry the value because that file is gitignored. `tests/utils/test_gate_scope.py::test_rhiza_test_actually_runs_the_doctest_check` fails if the skip returns.

### Dependency Management

`uv` manages all Python/dependency concerns:
- `.python-version` is the single source of truth for the Python version
- `uv.lock` pins all transitive dependencies — keep it in sync via `uv lock` or `uv sync`
- `uv run` transparently uses the project venv without manual activation

### Code Quality Requirements

- **Ruff** (`ruff.toml`): see `ruff.toml` for the authoritative and current enabled rule set (rule-prefix reference: https://docs.astral.sh/ruff/rules/)
- **Docstring coverage**: 100% (interrogate) — all public functions, classes, and modules require docstrings
- **Test coverage**: 90% minimum
- **Hooks**: `make fmt` runs ruff, markdownlint, bandit, actionlint, interrogate, jsonschema, and uv-lock validation

> **The hook runner is [prek](https://github.com/j178/prek), not pre-commit.** It reads the
> same `.pre-commit-config.yaml` — all four of them are unchanged, and Renovate still
> manages hook versions from that file — so this is a runner swap, not a config change
> (ADR 0009 carries the amendment). Two things are worth knowing before editing
> `quality.mk`:
>
> - **`make fmt` passes `--config .pre-commit-config.yaml` deliberately.** prek otherwise
>   treats *every* nested `.pre-commit-config.yaml` as a separate project and runs each
>   one's hooks. That is a feature in a monorepo and wrong here: `bundles/python-core`,
>   `bundles/rust-core` and `bundles/go-core` each ship one as **template content**.
>   Without the flag, go-core's hooks run `go vet ./...` in a directory that has no
>   `go.mod` — because a synced project brings its own — and `make fmt` fails on the
>   mother repo. `.prekignore` is documented for this job but is not honoured by prek
>   0.4.12.
> - **Every layer's `install` repeats it as `prek install -c .pre-commit-config.yaml`**,
>   because prek bakes `--config` into the git shim it generates. Passing it only to
>   `run` fixed the gate and left the *hook* unpinned, so `git commit` ran a different
>   set of hooks than `make fmt` — and in this repo failed outright on the nested
>   go-core config (#1488). The two halves are one invariant, so
>   `test_both_prek_entry_points_name_the_config` asserts them together, per layer. A
>   consumer wanting prek's monorepo behaviour drops the flag from *both* places.
> - **`fmt` no longer pins an interpreter.** `uvx pre-commit` needed one to run
>   pre-commit itself on, so a Rust or Go repo — which ships no `.python-version` — rested
>   on `rhiza.mk`'s `PYTHON_VERSION` fallback. prek is a binary that provisions each
>   hook's toolchain itself. `test_fmt_target_no_longer_needs_python_version` pins the
>   absence, so the coupling cannot creep back.
> - **The root config's interrogate hook is scoped differently from the bundle's, and
>   that is the override doing its job (#1535).** The bundle ships `files: ^src/`, right
>   for a downstream project and inert here, so the hook reported
>   `(no files to check)Skipped` on every `make fmt` — a line that reads like a check, in
>   the output of the gate this repo runs most. The root copy points instead at the folders
>   `make docs-coverage` resolves. Its `--config=pyproject.toml` also named a
>   `[tool.interrogate]` table that did not exist; interrogate falls back to its own
>   defaults for a missing table rather than failing, so the hook was quietly enforcing 80%
>   where the gate enforces 100%. `tests/utils/test_gate_scope.py` now pins both halves —
>   that the pattern matches files the gate measures, and that the table and the recipe
>   agree on the threshold.
>
> The CI job keeps its id `pre-commit` and its display name "Pre-commit hooks": that name
> is a required status check in `.github/rulesets/main-branch-protection.json`, so
> renaming it would leave every PR waiting on a context that never reports.

> **Coverage in this repo (mother-repo specifics).** Rhiza has no `src/`, so the default
> `source_folder` matches nothing and the scope has to be declared: `pyproject.toml`'s
> `[tool.rhiza-task]` sets `source-folder = "utils"`, the tooling behind `make sync-self` and
> the `sync-self-check` drift check. `make test` measures `utils` and enforces the standard
> 90% bar, which it currently passes at 100%.
>
> Leave that setting alone. Without it the folder resolves to `src`, which does not exist, and
> the CLI's gates *skip* a missing folder rather than failing — so `typecheck`, `security`,
> `docs-coverage`, `deps` and `semgrep` would all report success having measured nothing. That
> is the same silent failure the six `COVERAGE_FOLDERS`-style accumulators were introduced to
> fix (#1505, #1511, #1516), reachable again through a one-line config change.
>
> **That is recent, and the previous behaviour is worth knowing** because it is the bug the
> accumulators exist to prevent: until #1516 `test` passed `--cov=$(SOURCE_FOLDER)` behind a
> `[ -d ... ]`, so on a repo with no `src/` the suite ran and measured no coverage at all —
> silently, since a missing source folder warns rather than fails. `utils/` was reachable by
> four gates and invisible to the fifth.
>
> What has *not* changed is where this repo's assurance actually comes from. 166 statements
> of `utils` is a small fraction of it; the `tests/` suite and `make rhiza-test` mostly
> exercise Make targets, YAML and bundle invariants behaviourally, and no statement-coverage
> number describes that. A high percentage here is a check on the tooling, not a summary of
> the suite. Downstream consumers on the `python-core` layer have a real `src/` and get the
> same 90% gate over it.

### CI/CD

This repo runs on **GitHub Actions only**: `.github/workflows/` — CI, e2e, release, docker, CodeQL, weekly, sync. There is no root `.gitlab-ci.yml` here.

`rhiza_release.yml`'s `Validate Tag` job is the only gate the release path has, so all three of its checks are behavioural, not advisory: the release must not already exist, the version must be strictly newer than every published tag (#1126), and the tagged commit must be reachable from a branch (#1454). The last one exists because a release cut on a branch that is then squash-merged leaves its tag on the pre-squash commit, which nothing contains — `git describe` skips the release and a git-cliff regeneration *deletes* that version's CHANGELOG section, silently. A tag on a non-default branch (a maintenance release) warns rather than fails; only a genuinely orphaned commit is refused. `tests/api/test_release_tag_reachability.py` lifts that guard's shell out of the YAML and runs it against purpose-built repositories, so the logic is tested rather than the step name.

`rhiza_e2e.yml` is separate from `rhiza_ci.yml` rather than more jobs inside it: it installs three toolchains CI does not otherwise need, costs minutes per layer against CI's ≤20 min test budget, and is the only place the Rust and Go layers execute at all (see **Language layers** above).

GitLab support ships as a **template for downstream consumers**, not as active CI in this repo: the `gitlab` bundle (`bundles/gitlab/`) materializes a `.gitlab-ci.yml` plus `.gitlab/` pipelines into projects that adopt the `gitlab-project` profile, mirroring the GitHub Actions coverage there.

Because no GitLab pipeline runs here, `tests/bundles/test_gitlab_ci.py` validates the GitLab templates without a GitLab host: it assembles a `gitlab-project` and (1) checks every container image the pipeline/Dockerfiles reference actually exists on its registry (the guard that catches a retired tag like the removed `uv:*-bookworm`), (2) runs `gitlab-ci-local` (pinned, via `npx`) to resolve every `include:` and validate the merged pipeline against GitLab's JSON schema. A third test actually runs a job in Docker against the pinned `$UV_IMAGE` — it needs Docker and Node and is opt-in behind `RHIZA_GITLAB_DOCKER`, reached as **`make gitlab-docker-test`**. All three skip cleanly when their dependency (network / Node / Docker) is absent, so `make test` stays green offline.

That third one is the reason the target exists (#1528). Opt-in was correct — it pulls a large image — but the variable was set by no workflow, no target and no `.env`, so the only check that the pinned image still pulls and runs was skipped in *every* environment while reading as covered. `.github/workflows/rhiza_weekly.yml` now calls the target on the weekly schedule, and asserts `docker`/`npx` are present first so a runner image that drops either fails the job instead of quietly reinstating the skip. Weekly matches the cost, and matches the risk: no GitLab pipeline runs here, so a retired image tag would otherwise surface first in a downstream consumer.
