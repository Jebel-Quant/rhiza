# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Rhiza?

Rhiza is a **collection of reusable configuration templates** for Python, Rust and Go projects — not a runtime library. It has no `src/` directory and no runtime dependencies. Its purpose is to provide and continuously synchronize development infrastructure (the `Makefile` front door, CI workflows, linting configs, test setups) into downstream projects. The sync is performed by the `rhiza` Claude Code plugin ([rhiza-claude](https://github.com/Jebel-Quant/rhiza-claude)) — `/rhiza:update`. The `rhiza-cli` package that used to do it is unpublished and its repository archived; nothing in this repo depends on it any more.

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

- `core` (required, **language-neutral**): the language-neutral configuration —
  `.editorconfig`, `cliff.toml`, `.gitignore`, `.rhiza/semgrep.yml` — the `Makefile` front
  door, and uv/uvx as a *tool runner*. It ships no make *fragments* at all: the Makefile is a
  71-line shim forwarding to a pinned CLI, and the gates are CLI tasks. It deliberately
  provides no `install` and no `all` — see **Language layers** below.
- `python-core` (the Python **language layer**): `.python-version`, `ruff.toml`,
  `.bandit`, the pre-commit config and `pytest.ini`. Its gate set — `install`, `all`,
  `deps`, `license`, `test`, `typecheck`, `security`, `docs-coverage` — is rhiza-task's
  `python` layer rather than a synced fragment (see **Language layers**). Ships no
  bump-my-version config — see **Where the version config lives**.
- `rust-core` (the Rust **language layer**): `rust-toolchain.toml`, `rustfmt.toml`,
  `clippy.toml`, `deny.toml`, a Rust pre-commit config and `.bumpversion.toml`. Its gates
  are rhiza-task's `rust` layer, test targets included, as every layer now does —
  see **Language layers**.
- `go-core` (the Go **language layer**): `.golangci.yml`, `revive.toml`, a Go
  pre-commit config, `.bumpversion.toml`, and a starter `internal/version/version.go`
  with its `version_test.go`. Its gates are rhiza-task's `go` layer, test targets
  included, like the other two.
- `tests`: optional Python testing extras — `benchmark`, `hypothesis-test`, `stress`
  (requires `python-core`; the gates `all` names live in the layer)
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

Rhiza dogfoods its own templates: the files it ships in `bundles/<name>/...` also live at the repo root so the mother repo runs on its own infrastructure. `bundles/` is the **single source of truth**, and each root dogfood file is a **relative symlink into its owning bundle** (e.g. `Makefile` → `bundles/core/Makefile`). Edit the bundle file; the root reflects it automatically — no second edit. Run `make sync-self` (mother-repo-only, `utils/link_dogfood.py`) to (re)create links after adding a bundle file.

A few files **cannot** be symlinks and stay as **real copies**, kept in sync by tests (`tests/bundles/test_bundle_*_sync.py`) rather than by symlink:

- `.github/*` platform config (Dependabot, release notes, secret scanning, PR template, rulesets) — GitHub reads these blobs directly and does not resolve symlinks. **Live `.github/workflows/*` are also real** (Actions won't run a symlinked workflow) and differ from the bundle stubs by design. So does **`rulesets/main-branch-protection.json`**, and for a subtler reason (#1448): here `rhiza_ci.yml` has `push:`/`pull_request:` triggers, so its jobs run top-level and report bare check-run names, while downstream the `github-tests` stub delegates via `jobs.ci` and GitHub reports them as `ci / <job name>`. The bundle copy therefore prefixes all six required contexts; `tests/bundles/test_bundle_github_sync.py` pins that relationship, including the coupling to the stub's job id.
- `.rhiza/.gitignore` (and any `.gitignore`/`.gitattributes`) — git opens these with `O_NOFOLLOW`, so a symlink yields an ELOOP warning and the rules are ignored.

Plus intentional mother-repo overrides that deliberately diverge from their bundle source: root `.gitignore`, `.pre-commit-config.yaml`, `.python-version`, `SECURITY.md`, `renovate.json`. The exclusion list lives in `utils/link_dogfood.py`. Downstream consumers are unaffected: the sync checks out a bundle and dereferences symlinks on copy, so synced projects always receive real files (guarded by `test_no_symlinks_in_*`).

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
`deps`, which until #1474 was the one exception: python-core named that target after the tool
itself, so the shared name failed on Python and the tool-named one failed on the other two. The
deprecated alias that reconciled them retired with `python.mk`; rhiza-task exposes `deps` only.

The tool-named *variables* went the same way. `DEPTRY_FOLDERS` was the accumulator interface a
downstream `local.mk` appended to, and the CLI has no accumulators — `deps` derives its folder
list instead (the source folder, plus the marimo folder when the marimo tasks are registered),
and `DEPTRY_IGNORE` survives as the `deptry-ignore` setting because it names deptry's own
arguments rather than a scope.

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

- **`rhiza.mk` does not read it**, so the table is inert in a repo still on the synced make
  layer — it resolves settings through `?=`, its `Makefile` and `.rhiza/.env` — and only
  starts working when that repo syncs past #1556. The mirror image applies once it has: the
  `Makefile` is template-owned, so a setting cannot live *there* either, and the surfaces are
  this table, `.rhiza/.env` (gitignored, so developer-local only) and `RHIZA_*` in the
  environment — which `local.mk` can `export` for anything that must be committed. This
  repo's own `MKDOCS_EXTRA_PACKAGES` override made that trip: it sat above the include in the
  old root `Makefile`, was lost silently when the shim replaced that file, and is
  `mkdocs-extra-packages` in `pyproject.toml` now.
- **It is no longer Python-only.** It was: `_from_pyproject` read `pyproject.toml` and
  nothing else, so `rust-core` and `go-core` had no equivalent — a crate has `Cargo.toml`, a
  Go module has no manifest at all — and those layers were left with `.rhiza/.env` and an
  exported `RHIZA_*` in `local.mk`. The pinned CLI reads a root **`rhiza.toml`** as well, in
  either the `[tool.rhiza-task]` or a flat top-level form, which is the language-neutral
  source that was missing. Where both files exist `pyproject.toml` wins, so a Python repo
  cannot be surprised by one. Verified against the pin rather than read off a changelog:
  `uvx rhiza-task print <setting>` in a directory holding only a `rhiza.toml` resolves from
  it.

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

What `tests` still owns is what is genuinely optional — `benchmark`, `hypothesis-test`
and `stress`, each needing its own tool and folder convention, and none named by any
`all`. There is still no `rust-tests` or `go-tests` bundle, for the original reason:
`cargo nextest` and `go test` need no configuration, so such a bundle would own nothing
at all.

**The benchmark gate measures something here now, and both halves of why it did not are
worth knowing.** `rhiza_benchmark.yml` runs `benchmark` on every push to `main`, and the
task's guard globs `tests_folder` for `benchmarks/*.py` — so with no `tests/benchmarks/`
in this repo it printed `skipped  benchmark  no benchmarks folder`, exited 0, and wrote a
duration into the step summary for a run that measured nothing. Same silent-green shape as
#1505, #1511, #1516 and #1535, reached through an absent folder.
`tests/benchmarks/test_dogfood_linker.py` fills it, and deliberately not with the bundle's
blueprint: those placeholders time string concatenation and `dict` insertion, so a
regression in them would be a story about CPython. What it times instead is
`utils/link_dogfood.py` — the index walk over `bundles/`, the carve-out predicate, and the
classification pass — the only code here whose cost grows with the template. Each
benchmark asserts the size of its own workload, because an input that narrows to nothing
gets *faster*, and faster reads as an improvement in the very report meant to catch
regressions.

The second half is that the `benchmarks` bundle's `conftest.py` broke the gate it ships
with, in every consumer. It defined `pytest_html_report_title` while `benchmark` injects
only `pytest-benchmark` and `pygal` — it writes a histogram and a JSON file, not an HTML
report — and pluggy validates hook *names* at collection, so pytest raised
`PluginValidationError: unknown hook` as an INTERNALERROR and exited 3 before collecting a
thing. `make book` went with it, since `book` needs `benchmark`. Two things hid it: the
`test` gate passes `--ignore=$(tests_folder)/benchmarks`, so the file is never collected by
the gate everything else runs, and the mother repo had no benchmarks folder, so dogfooding
never reached it either. The fix keeps the path rather than deleting the file — a sync that
stops delivering a file does not remove a consumer's copy, so overwriting it is what
repairs a repo that already has the broken one. `test_bundle_combinations.py`'s
`test_the_synced_scaffolding_declares_no_hook_the_gate_cannot_provide` asserts the rule and
not that one name, deriving pytest's own hookspec list rather than restating it.

A related trap for anyone adding to `tests/benchmarks/`: **do not reuse the bundle's
filenames.** `conftest.py` and `test_benchmarks.py` are paths the `benchmarks` bundle
claims, and a root file whose path has a bundle twin must be a symlink into it
(`test_bundle_dogfood_symlinks.py`). A same-path copy that merely diverges is classified as
an undeclared mother-repo override and left alone — silently.

**Mutation testing is not part of the ecosystem, and that is now a decision rather than
an omission (#1492).** `mutation` was a fourth extra, and it had been broken in every
consumer since mutmut 3 shipped: the recipe passed `--paths-to-mutate` and `--tests-dir`
and called `mutmut html`, all three removed, and installed mutmut unpinned — so the
breakage was time-triggered, arriving on the day of a release rather than on a sync. It
survived because nothing invoked it. No `all` names it, and `rhiza_mutation.yml` was
removed in #1583 after `MUTATION_ENABLED` turned out to be unset here and in every
consumer we could see, so the only signal was someone invoking `mutation` by hand.

What settled it against a port is that mutmut 3.x resolves source paths *during config
loading*, with no CLI path at all — so a task cannot pass them, and would instead have to
require a `[tool.mutmut]` table in every consumer's `pyproject.toml` or write one behind
their back. On top of that `tests_dir` is itself already deprecated in favour of
`pytest_add_cli_args_test_selection`, the HTML report the recipe relocated does not exist
any more (artifacts land in `mutants/`, and `export-cicd-stats` writes the JSON that
replaces it), and `results` prints nothing when nothing survived. A new config contract
with consumers, for a gate none of them had switched on. That removal landed as
rhiza-task **v1.2.0** (Jebel-Quant/rhiza-task#135), and this repo's pin reached it at
v1.3.1. Asking the shim for `mutation` now falls through its `%:` catch-all to the CLI's
unknown-task error, which is the intended outcome rather than a regression.

Both sentences above deliberately name the task rather than spelling the invocation, and
that is the house answer rather than a stylistic tic: `tests/docs/test_doc_consistency.py`
scans code spans for `make <target>` and requires the target to exist, so writing the
retired one out would fail the suite. The exemption list is not the way out -- its own
test keeps it from re-accumulating, and the entries it lost went by rewriting the prose,
which is what this is.

**The `mutation` row in README.md went with it, and it went the way this paragraph said it
would.** That block lives between the `MAKE_HELP_START`/`MAKE_HELP_END` markers and is
regenerated from `make help` by the `update-readme-help` hook on every `make fmt`, so it
reports the pinned CLI's task list rather than this repo's policy — deleting the row by
hand only ever made the hook put it straight back. Moving the pin is what removed it, and
that is the shape to expect for anything else the generated block carries.

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
directory (standing in for a `/rhiza:update` sync), writes the smallest project the layer
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

- **The accumulator's `?= ` empty / `+=` seed shape was load-bearing, not cosmetic.**
  (Historical: the accumulator is a derivation from the layer set in rhiza-task now.)
  `rhiza.mk` included `make.d/*.mk` alphabetically, so `go.mk` and `python.mk` were read
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

### What is left of the Makefile system

The synced make layer is **gone**, bundles included: `core` ships no `.rhiza/rhiza.mk`,
`.rhiza/make.d/` no longer exists in any bundle or at the root, and all sixteen fragments —
1481 lines — retired with them.

What survives is the front door, `bundles/core/Makefile`, 71 lines of it. `make` therefore
still works and still is what a stranger types, but it no longer *contains* anything: a `%:`
catch-all forwards every unmatched target to a pinned CLI, and `RHIZA_TASK` is the whole
version contract. Bumping it is the migration that used to be `/rhiza:update` re-syncing
sixteen fragments and reconciling whatever had been shadowed — except that the bump now
*arrives* by sync, because the file is template-owned like the rest of the bundle.

**It was repo-owned for one release, and that half is worth knowing.** rhiza-task printed the
file (`uvx rhiza-task shim > Makefile`) and each repo owned the copy, which put a template
inside the task runner: the CLI had to know about `local.mk`, the `##` help convention and the
./bin/uvx bootstrap, and this repo then hand-carried a variant of that output anyway (the `UV`
alias, `FORCE`, the `help` extension that lists `local.mk`'s targets). The worse half was the
pin. `shim` wrote the version of whichever CLI printed it, into a file no sync would touch —
so moving a consumer's gates forward was a per-repo hand edit `/rhiza:update` could not make,
and every consumer lagged silently. Template ownership restores the property
`RHIZA_CHECKS_VERSION` already had: a repo synced at a tag runs that tag's gates.

Two things make that safe, and both are recent. Repo-owned *targets* have somewhere to live —
`local.mk`, which the Makefile `-include`s and core deliberately leaves un-gitignored (#1574),
so appending below the shim is no longer the only way to commit one. And nothing repo-specific
is in the file: `tests/api/test_makefile_targets.py::test_makefile_carries_no_repo_owned_rule`
holds it to the shim's seven rules, which is what makes an overwrite lossless. The root copy is
a dogfood symlink into `bundles/core/`, so there is one copy of it in this repo, not two.

**The last five went in two steps, and the second is worth knowing about.** Eleven fragments
retired with rhiza-task 0.2.0. `github.mk`, `docker.mk`, `lfs.mk`, `paper.mk` and
`presentation.mk` could not, because the CLI had no task for `view-prs`, `docker-build`,
`lfs-pull`, `paper` or `presentation-pdf` — none of them a gate, so deleting them would have
removed working behaviour to tidy a folder. rhiza-task 0.3.0 added all eighteen targets under
their original names (Jebel-Quant/rhiza-task#22), which is what let the folder go.

Three consequences of *that* step, all of them things a reader will otherwise trip over:

- **A consumer's stale fragments now shadow the CLI, silently.** A sync that stops delivering a
  file does not delete it, so a repo that synced `github` before this keeps
  `.rhiza/make.d/github.mk` on disk. That is only inert if nothing includes it — and an explicit
  rule beats the `%:` catch-all, so a repo whose Makefile still carries the `-include` runs the
  *old* recipe. This is the `.rhiza/tests/` situation from #1540 with the sign flipped: there the
  leftovers were unreachable, here they win. `/rhiza:update` should delete the folder; until it
  does, a migrating repo removes `.rhiza/make.d/` by hand.
- **Three targets changed behaviour** when they became tasks, deliberately, and are documented in
  their rhiza-task module docstrings: `lfs-install` configures the repository and reports how to
  install git-lfs rather than downloading a binary into `.local/bin` (which never ended up on
  `PATH`, so the macOS branch left nothing working); `presentation` reaches Marp through
  `npx --yes` rather than `npm install -g`; and `paper` picks its root document by
  `main.tex` → `paper.tex` → alphabetical instead of preferring one downstream repo's
  `basanos.tex`.
- **The `paper` bundle's only file was its fragment.** It ships `docs/paper/README.md` now — the
  folder convention, the root-document rule and the `paper-folder` setting — which is the shape
  `docker`, `lfs` and `presentation` already had. Without it the bundle would be an empty
  directory, and `test_all_bundle_dirs_are_non_empty` says so.

**Hook targets are gone**, and that predates this step. `bootstrap.mk` anchored
`pre-install::`/`post-install::` as no-ops so a consumer could chain onto them, and that was *the*
documented way to add project hooks. `uvx rhiza-task install` knows nothing about make targets.
Shadow the target instead: an explicit `install:` rule in `local.mk` beats the catch-all, so it can
call the CLI and then the extra step. This repo did exactly that for `rhiza-test` until 0.3.1 made
the wrapper redundant; nothing here shadows a CLI task now.

**What guards the pin.** `RHIZA_TASK` being the whole version contract cuts both ways: a bump that
dropped a task would remove `make view-prs` from every consumer on the `github-project` profile,
and nothing in the shim would notice — it resolves any target, and the CLI's "unknown task" error
appears only when someone runs it. `tests/api/test_bundle_cli_targets.py` reads the pin out of the
root `Makefile`, asks that exact version what tasks it has, and requires every retired target to
be in the answer. It needs uv and the network and skips without them, so `make test` stays green
offline while CI does the real check.

**Where the mother-repo-only targets live.** `explain-bundles`, `sync-self`, `sync-self-check`
and `e2e` were `.rhiza/make.d/bundles.mk`, a fragment no bundle shipped, then a section appended
below the shim in the root `Makefile`. They are `local.mk` now, and that move is what let the
`Makefile` become template-owned at all — `tests/api/test_makefile_targets.py` pins both halves.
It also needed `local.mk` to be committable, which is why `bundles/core/.gitignore` stopped
ignoring it (#1574): CI invokes `make e2e` in all three language jobs, so this repo's copy has to
be committed, and a consumer whose CI calls its own target is in exactly the same position. A
fifth, `gitlab-docker-test`, lived there too and is gone — see **CI/CD** below.

**And why `rhiza-test` is no longer wrapped.** pytest-rhiza's `test_docstrings` reads its scope
from the `RHIZA_DOCTEST_FOLDERS` environment variable; `quality.mk` exported it from
`DOCSTRING_FOLDERS`, and rhiza-task 0.3.0 did not (Jebel-Quant/rhiza-task#18). On a bare delegation
the check reported `SKIPPED  No doctest folder found (looked for: src)` while the gate still said
`ok rhiza-test` — #1517 exactly, this repo's only doctest examples unchecked behind a green gate.
`.rhiza/.env` cannot carry the value because that file is gitignored, so this repo wrapped the gate
to export it.

**0.3.1 passes it through itself**, so the wrapper stopped fixing anything and survived only as a
probe — an export `tests/utils/test_gate_scope.py` could read out of a `make -n`. It went with the
move to `local.mk`, since a wrapper whose recipe restates what the CLI already does is exactly the
duplication that file is meant not to accumulate. The property now lives inside the pin, asserted
upstream against the resolved config; what is left here is a floor on the pinned version, because
that is the half upstream cannot see. The two other mother-repo workarounds 0.3.1 retired are gone
the same way: the shim ships the `PATH` export (rhiza-task#19), and `mkdocstrings[python]` is the
default for `mkdocs-extra-packages`, which this repo's `pyproject.toml` now merely restates.

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

### Enforcing template ownership

Every managed repo's `CLAUDE.md` opens with the same rule — *managed files are overwritten
by the next sync* — and from the removal of the `validate` gate after v1.1.3 until #1462
nothing enforced it. (Deliberately not written as a `make` code span: it is a retired
target, and `test_doc_consistency.py` holds every such span in the docs to a target that
still resolves.) The failure that leaves is silent and total: the edit works, is
reviewed, is merged, and disappears at the next sync with no error at any point.

rhiza-hooks' `check-managed-files` closes it, and all three language layers now run it. It
reads `.rhiza/template.lock`'s `files:` list minus anything under `exclude:` in
`.rhiza/template.yml`, and reports only paths that **differ from HEAD** — not merely paths
that are managed and present. That narrowing is what keeps `make fmt` and CI green: both
pass every tracked file with `--all-files`, and without it the hook would report every
managed file in the repo on a clean tree.

**Adoption was gated on the sync path first, and the order is not optional.** A sync
commit rewrites template-owned files wholesale — that is its whole purpose — so it is
precisely the commit this hook is built to reject, and `/rhiza:update`'s `stage_synced.py`
stages *exactly* the list the hook reads. The bypass is `SKIP=check-managed-files git
commit`, landed in rhiza-claude#211 before this was adopted here. Two things are worth
knowing about that sequencing:

- **The break would have been immediate, not merely future.** prek's git shim reads
  `.pre-commit-config.yaml` fresh at commit time, so the config is already on disk when
  the sync commits it. Without the bypass in the plugin, the very sync that *delivers*
  the hook is the one it rejects. What decouples the two is that the plugin updates
  independently of a template sync, so consumers can have the fix before this ships.
- **`SKIP` is honoured by prek, not just pre-commit.** Worth checking rather than
  assuming, since prek differs from pre-commit elsewhere in this repo (it bakes
  `--config` into the shim it generates). It works in both `prek run` and the installed
  shim. One edge: if `SKIP` filters out *every* hook, prek exits non-zero with
  `No hooks found after filtering with the given selectors` — irrelevant for these
  twenty-hook configs, but it would bite a minimal one.

**The bypass belongs to the sync commit and nowhere else.** `/rhiza:remote` commits CI
fixes with `git commit -am`, and in a managed repo the likeliest thing such a fix touches
is `.github/workflows/*` or `.gitlab-ci.yml` — both template-owned. The hook refusing that
commit is it working: the fix really would vanish at the next sync. So that flow reports
the managed path and says the change belongs upstream (or under `exclude:`), rather than
reaching for `SKIP` and committing an edit with a known expiry date.

**The mother repo's root override deliberately does not carry it.** rhiza has no
`template.lock` — it *is* the template — so the hook can never fire here, and unlike
`check-rhiza-config` (kept in `test_precommit_hook_reachability.py`'s `_INERT_BY_DESIGN`
so a future `template.yml` starts being checked) that will not change. It also declares no
`files:` pattern, so it would print **Passed** rather than **Skipped**: its inertness would
be invisible in the output of the gate this repo runs most, which is the shape of #1535 and
#1581. `TestLayerPreCommitConfig` asserts the three layers carry it and the root does not.

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

`rhiza_paper.yml` **implements no LaTeX driver.** It used to: an apt install of four guessed `texlive-*` packages, a root-document rule that preferred `basanos.tex` (one downstream repo's paper, in a template every consumer syncs), and a `latexmk` call with its own flag set. All three already existed in rhiza-task's `paper` task — the one `make paper` runs and the one `book` takes as a prerequisite — so the workflow was a second definition of how a paper gets built, free to diverge. It had already diverged: the task drives **tectonic**, not latexmk, so the two halves of this repo disagreed about the engine. What is left is `uvx "$RHIZA_TASK" paper --strict`, plus getting the engine onto the runner.

Three details in that, each of which the tests pin:

- **`--strict` is not decoration.** The task guards on tectonic being present and on the folder existing, and a failed guard is a *skip that exits 0*. Without the flag, a runner that never got the engine would print `skipped  paper` under a green tick — for the one workflow whose entire purpose is that a PDF got built. Same silent-green shape as #1505, #1511, #1516 and #1535.
- **The engine is a pinned static binary, not a distribution.** tectonic resolves what a document cites out of its own web bundle, so there is no package list to keep in step with anyone's `\usepackage` lines. The musl build is the one downloaded, because it is statically linked; the gnu tarball needs `libgraphite2.so.3`, which no runner image or `$UV_IMAGE` guarantees. `TECTONIC_VERSION` has a Renovate custom manager for the reason `RHIZA_TASK` now does — an unmanaged pin only ages (#1579, #1582) — and deliberately no checksum, since nothing could keep a digest in step with an automated bump and a stale digest would go red in every consumer.
- **The paper folder comes from `print paper-folder`.** `paper-folder` is a documented setting, so a hard-coded `docs/paper` would compile nothing in a repo that moved it. Only the `paths:` trigger and the cache key stay literal, because neither takes an expression; both fail safe.

**The PDF is published on the `paper` branch again**, by request, after #1494 removed that push. The collision it was removed for is real and unchanged — git refs are paths, so `refs/heads/paper` cannot exist while `refs/heads/paper/overview` does, which is the branch prefix a paper-writing team reaches for first. What is different is that it is now *diagnosed* rather than hit: a preflight step lists any `paper/*` ref and fails naming it, where git's own error on the push names neither branch. It sits deliberately **after** the artifact upload, so a repo in that state still collects its PDF while it decides which branch to rename.

So the PDF has three homes, and they fail differently: the run artifact (immediate, expires), the book's site asset (`paper_folder` sits inside `docs_dir`, guarded by `book-nav` and `test_the_compiled_paper_is_reachable_from_the_book`), and the branch (stable path, needs no build and no unexpired run; it carries the PDF plus a README the workflow generates, and nothing else). `contents: write` is back with it — granted at the *job* level, with the workflow-level default left at `read`, and repeated in the `github-paper` stub because a caller cannot grant a called workflow less than it needs. The two halves stay in step because the same release that ships the stub rewrites its `@vX.Y.Z` ref (`[[tool.bumpversion.files]]` globs `bundles/**/.github/workflows/*.yml`).

**The compile pins `SOURCE_DATE_EPOCH`, and that is what makes the branch history mean anything.** tectonic stamps the PDF `/ID` field from the build time, so two runs over an unchanged document produce different bytes — measured, not assumed: identical source, identical engine, identical runner, two hashes. The consequence was that `git diff --staged` in the publish step could *never* hold, every publish committed, and the branch recorded runs rather than revisions. The value is the source commit's own committer time, which makes the output a property of the revision rather than of when a runner happened to build it, and needs no deeper checkout than the default. `rhiza_book.yml` sets it too — there the cost was not commit churn but a site asset whose bytes changed for no reason, defeating caching and making two builds of one revision impossible to compare.

**The branch carries a generated `README.md`**, and two things about it are deliberate. It is written by the workflow rather than committed once by hand, because a hand-written one would be overwritten by the next run anyway — which is the main thing it has to say about itself. And it embeds **no per-run value**: no run number, no timestamp, no source SHA. The step commits only when `git diff --staged` reports a change, which is what stops a rebuild of an unchanged paper adding an empty commit; a README that differs on every run would retire that guard and grow the branch a commit per push. Provenance goes in the commit message, which is only written when there *is* something to commit. `test_the_branch_readme_carries_no_per_run_value` asserts both halves, because either one alone is the wrong trade — and it is worth nothing at all without the reproducibility above: keeping a timestamp out of the README while the PDF beside it changes every run buys exactly nothing.

One more detail in that step: the branch switch is `-f`. The compile has just written a PDF into the working tree, and while the template gitignores `docs/paper/*.pdf` — so for a synced project the file is untracked and the switch is quiet — a project that commits its PDF instead has a *modified tracked* file, and git refuses to switch branches at all. That failed the publish immediately after a successful compile. Discarding is safe there and nowhere else, because the PDFs were copied to a temp directory first.

`TestPaperWorkflow` in `tests/api/test_workflow_stubs.py` reads the shell rather than the parsed YAML for the push assertions, because a `run:` block is an opaque string to a YAML loader — and it asserts the collision check *precedes* the push by step position, since a check that runs afterwards prints its diagnosis only after the failure it explains.

**`rhiza_book.yml` installs the engine too, and runs `book-nav`.** This is where the paper publish was actually broken, and it had nothing to do with the paper workflow: `book` takes `paper` as a prerequisite, but the book workflow installed no tectonic, so every run on `main` printed `skipped  paper  tectonic not found`, reported `ok  book`, and deployed a site whose nav claimed `paper/rhiza.pdf` with no such asset. A 404 in the book's own navigation, green on every run.

`book-nav` exists precisely for that and **was invoked by nothing** — upstream's own docstring says it is "named by `rhiza_book.yml`", which was the claim rather than the fact, and this file repeated it. zensical reports `No issues found` for a nav entry whose target is missing, so nothing anywhere asked the question. Both halves are wired now, on both platforms, and `TestBookWorkflow` asserts them — including by step order, since a `book-nav` that runs before the build skips for want of a built site, which is a pass that measures nothing. The engine install is conditional on a `*.tex` actually being there, so a consumer with no paper pays nothing for it.

**Two nav entries had to be renamed for that gate to be honest**, and the reason is worth knowing before pointing a nav entry at a `README.md` again. mkdocs builds `README.md` to `index.html`; the pinned `book-nav` resolves a markdown target only as `<stem>.html` or `<stem>/index.html`, so `adr/README.md` and `presentations/README.md` were reported missing from a site that did contain them, at `/adr/` and `/presentations/`. That is a false positive in the check rather than a defect in the site — worth reporting upstream — and both files are `index.md` now, which is the mkdocs-native spelling, keeps the published URL identical, and makes the source name match the built one under either tool.

The GitLab twin got the same delegation and had the same leak in the other direction — it preferred `rhiza.tex`, *this* repo's filename. It publishes no branch: pushing back needs a token `CI_JOB_TOKEN` cannot stand in for, and inventing a project-secret contract for one job is not a parity gap worth closing that way.

GitLab support ships as a **template for downstream consumers**, not as active CI in this repo: the `gitlab` bundle (`bundles/gitlab/`) materializes a `.gitlab-ci.yml` plus `.gitlab/` pipelines into projects that adopt the `gitlab-project` profile, mirroring the GitHub Actions coverage there.

Because no GitLab pipeline runs here, `tests/bundles/test_gitlab_ci.py` validates the GitLab templates without a GitLab host: it assembles a `gitlab-project` and (1) checks every container image the pipeline/Dockerfiles reference actually exists on its registry (the guard that catches a retired tag like the removed `uv:*-bookworm`), (2) runs `gitlab-ci-local` (pinned, via `npx`) to resolve every `include:` and validate the merged pipeline against GitLab's JSON schema. Both skip cleanly when their dependency (network / Node) is absent, so `make test` stays green offline.

**Neither of them runs a job**, and that is a deliberate reduction in coverage. A third test used to pull the pinned `$UV_IMAGE` and execute a single-job pipeline in Docker — the only proof the pipeline's default image still *works* rather than merely resolving. It reached CI through a mother-repo-only `gitlab-docker-test` target and a weekly job, both added by #1528 precisely because `RHIZA_GITLAB_DOCKER` was set nowhere and the check had been skipping in every environment while reading as covered. Test, marker, target and weekly job were all removed together, so nothing is left half-wired: an image tag that exists on the registry but is broken inside now surfaces first in a downstream `gitlab-project` consumer, not here.
