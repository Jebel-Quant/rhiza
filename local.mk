## local.mk (repo-owned) -- rhiza's own targets, which the `Makefile` `-include`s.
#
# These were `.rhiza/make.d/bundles.mk`, a fragment no bundle shipped, and then a block
# appended below the shim in the `Makefile`. They live here because the `Makefile` is
# template-owned -- `core` ships it and every sync overwrites it -- so this is the only
# place in the repo a make target of its own can survive a `/rhiza:update`.
#
# Committed, like in any consumer repo: core's `.gitignore` leaves `local.mk` tracked for
# exactly this reason (#1574), and `make e2e` is what .github/workflows/rhiza_e2e.yml runs
# in all three language jobs. An explicit rule beats the shim's `%:` catch-all, so these
# win over CLI delegation; `install` as a prerequisite still resolves through it, and the
# `##` comments are what put them in `make help`.
#
# `$(UV)` comes from the shim, which provisions it alongside `$(UVX)`.
#
# The folder accumulators this fragment also carried (TYPECHECK_FOLDERS, BANDIT_FOLDERS,
# DOCSTRING_FOLDERS, DEPTRY_FOLDERS, SEMGREP_FOLDERS, COVERAGE_FOLDERS += utils) are gone,
# replaced by `source-folder = "utils"` in pyproject.toml's [tool.rhiza-task]. They existed
# because this repo ships configuration and has no src/, so SOURCE_FOLDER matched nothing
# and five gates measured nothing (#1505, #1511, #1516). The CLI reads a single
# source_folder, and `utils` is this repo's only non-test Python, so one setting replaces
# six appends. tests/utils/test_gate_scope.py pins the outcome either way.

.PHONY: explain-bundles sync-self sync-self-check e2e

# Which end-to-end modules `make e2e` runs. One per language layer, so CI can give each its
# own job (and its own toolchain) by narrowing this:
#   make e2e E2E_ARGS=tests/e2e/test_go_layer_e2e.py
E2E_ARGS ?= tests/e2e

explain-bundles: $(UV) ## print all bundles and profiles with descriptions and dependencies
	@$(UV) run utils/explain_bundles.py

sync-self: $(UV) ## relink root dogfood copies as symlinks into bundles/ (mother repo only)
	@$(UV) run utils/link_dogfood.py

# The local drift check, for use before committing a new bundle file. In CI the same
# invariant is asserted by tests/bundles/test_bundle_dogfood_symlinks.py inside `make test`
# — using link_dogfood's own carve-out predicate and bundle index, so the two cannot
# disagree. No workflow runs this target (#1532).
sync-self-check: $(UV) ## fail if any dogfood symlink is stale/missing without writing (local drift check)
	@$(UV) run utils/link_dogfood.py --check

# The language-layer end-to-end suite: assemble a profile into a temp directory, scaffold
# the smallest project the layer should be green on, and run every gate for real. Opt-in
# because it drives real toolchains and takes minutes per layer; a layer whose compiler is
# absent skips rather than fails, so `make e2e` on a machine with no Go installed still
# exercises the layers it can.
#
# `make test` deliberately excludes it: the matrix would pay for it on every OS and Python
# version. .github/workflows/rhiza_e2e.yml is where all three actually run.
#
# pytest-timeout is provisioned here rather than declared: without it pytest ignores both
# pytest.ini's `timeout` and the suite's marker — silently, so a hung gate would run until
# the CI job's own timeout killed it with no indication of which gate hung.
e2e: install $(UV) ## run the language-layer end-to-end suite against real toolchains (opt-in)
	@printf "\033[36m[INFO] Running end-to-end suite: $(E2E_ARGS)\033[0m\n"
	@RHIZA_E2E=1 $(UV) run --with pytest-timeout pytest $(E2E_ARGS) -v
