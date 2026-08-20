## local.mk (repo-owned) -- rhiza's own targets, which the shim `-include`s.
#
# These were `.rhiza/make.d/bundles.mk`, a fragment no bundle shipped, and then a block
# appended below the shim in the `Makefile`. They live here so that file can be exactly
# what `uvx rhiza-task shim` prints, making a bump an overwrite rather than a merge.
#
# Committed, unlike in a consumer repo: `local.mk` is in core's `.gitignore`, and this repo
# carves that file out (utils/link_dogfood.py `_EXCLUDE`) because `make e2e` is what
# .github/workflows/rhiza_e2e.yml runs in all three language jobs. An explicit rule beats
# the shim's `%:` catch-all, so these win over CLI delegation; `install` as a prerequisite
# still resolves through it, and the `##` comments are what put them in `make help`.
#
# The folder accumulators this fragment also carried (TYPECHECK_FOLDERS, BANDIT_FOLDERS,
# DOCSTRING_FOLDERS, DEPTRY_FOLDERS, SEMGREP_FOLDERS, COVERAGE_FOLDERS += utils) are gone,
# replaced by `source-folder = "utils"` in pyproject.toml's [tool.rhiza-task]. They existed
# because this repo ships configuration and has no src/, so SOURCE_FOLDER matched nothing
# and five gates measured nothing (#1505, #1511, #1516). The CLI reads a single
# source_folder, and `utils` is this repo's only non-test Python, so one setting replaces
# six appends. tests/utils/test_gate_scope.py pins the outcome either way.

.PHONY: explain-bundles sync-self sync-self-check e2e rhiza-test

# `uv` as well as `uvx`: the astral installer writes both into the same directory, so once
# $(UVX) exists this does too. The empty recipe satisfies make's remake attempt, the same
# trick the shim uses for `local.mk`.
UV ?= $(shell command -v uv 2>/dev/null || echo $(INSTALL_DIR)/uv)
$(UV): $(UVX) ;

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

# `rhiza-test` is wrapped rather than delegated. As of 0.3.1 the wrapper no longer *fixes*
# anything; it is what makes the fix assertable here.
#
# pytest-rhiza's `test_docstrings` takes its scope from the RHIZA_DOCTEST_FOLDERS
# environment variable, falling back to SOURCE_FOLDER in `.rhiza/.env` and then to `src`.
# `quality.mk` used to export it from DOCSTRING_FOLDERS; rhiza-task 0.3.0 did not, so on a
# bare delegation the check reported
#
#   SKIPPED  No doctest folder found (looked for: src)
#
# and the gate still said `ok rhiza-test` — #1517 exactly: this repo's only doctest examples
# unchecked, silently, behind a green gate. `.rhiza/.env` cannot carry the value because that
# file is gitignored, so CI would never see it.
#
# rhiza-task 0.3.1 passes `source_folder` through as that variable itself
# (Jebel-Quant/rhiza-task#18), so this recipe now exports the value the CLI would export
# anyway — same folder, from the same setting. It stays because it is where the property can
# be checked cheaply: tests/utils/test_gate_scope.py reads the expanded variable out of a
# `make -n`, needing no network, no lockfile and no tags, and fails if the export goes. A
# bare delegation moves the property inside the pin, where only a real run reveals it.
rhiza-test: $(UVX) ## run the rhiza repository checks, with this repo's doctest scope
	@RHIZA_DOCTEST_FOLDERS="$(shell $(UVX) $(RHIZA_TASK) print source_folder)" \
		$(UVX) $(RHIZA_TASK) rhiza-test
