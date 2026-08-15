## .rhiza/make.d/bundles.mk - Bundle exploration and onboarding
# Provides make explain-bundles for new contributors unfamiliar with the bundle model.
# Mother-repo-only fragment: no bundle ships it, so it is never synced downstream.

.PHONY: explain-bundles sync-self sync-self-check e2e

# Bring utils/ into the five path-scoped gates.
#
# Rhiza ships configuration, not a runtime library, so it has no src/ and SOURCE_FOLDER
# matches nothing. That left `typecheck`, `security` and `deps` exiting 0 having measured
# nothing, and `docs-coverage` seeing only the test folders (#1505) — on the one repo that
# ships those gates to everyone else. But real Python does live here: utils/ holds the
# mother-repo tooling behind `make sync-self` and the sync-self-check CI drift guard.
#
# `semgrep` joined them in #1511. It has the same shape and had the same hole, but was
# missed by #1505 because it is owned by core's quality.mk rather than by python.mk — and
# it is the one of the five that runs on a schedule (rhiza_weekly.yml) rather than from
# `all`, so the silent pass was a green weekly job rather than a fast local one.
#
# These are the accumulators python.mk and quality.mk expose for exactly this. This
# fragment is loaded before both (make.d is read alphabetically), so each `+=` creates the
# variable and the owning fragment's `?=` then leaves it alone.
#
# It belongs here rather than in the root Makefile because that file is a dogfood symlink
# into bundles/core/ — editing it would ship rhiza's own layout to every consumer.
#
# DEP004 ("imported but declared as a dev dependency") is ignored on the grounds marimo.mk
# ignores it for notebooks: utils/ *is* development tooling, so importing a dev dependency
# there is correct rather than misplaced. marimo.mk contributes the same flag when its
# folder exists; deptry accepts the repeat, and stating it here keeps utils/ from silently
# depending on the marimo bundle staying adopted.
TYPECHECK_FOLDERS += utils
BANDIT_FOLDERS    += utils
DOCSTRING_FOLDERS += utils
DEPTRY_FOLDERS    += utils
SEMGREP_FOLDERS   += utils
DEPTRY_IGNORE     += --ignore DEP004

# Which end-to-end modules `make e2e` runs. One per language layer, so CI can give
# each its own job (and its own toolchain) by narrowing this:
#   make e2e E2E_ARGS=tests/e2e/test_go_layer_e2e.py
E2E_ARGS ?= tests/e2e

##@ Bundles
explain-bundles: ## print all bundles and profiles with descriptions and dependencies
	@uv run utils/explain_bundles.py

sync-self: ## relink root dogfood copies as symlinks into bundles/ (mother repo only)
	@uv run utils/link_dogfood.py

sync-self-check: ## fail if any dogfood symlink is stale/missing without writing (CI drift guard, mother repo only)
	@uv run utils/link_dogfood.py --check

# The language-layer end-to-end suite: assemble a profile into a temp directory,
# scaffold the smallest project the layer should be green on, and run every gate
# for real. Opt-in because it drives real toolchains and takes minutes per layer;
# a layer whose compiler is absent skips rather than fails, so `make e2e` on a
# machine with no Go installed still exercises the layers it can.
#
# `make test` deliberately does not include it: the matrix would pay for it on
# every OS and Python version. .github/workflows/rhiza_e2e.yml is where all three
# actually run.
#
# No xdist and no -o timeout override: each module builds one project and runs its
# gates against it in order, and the suite's own `pytest.mark.timeout` supersedes
# the 60s pytest.ini default (sized for unit tests, not for a gate that provisions
# pre-commit from scratch).
#
# pytest-timeout is provisioned here the way test.mk provisions its plugins: it is
# not a declared project dependency, and without it pytest ignores both pytest.ini's
# `timeout` and the suite's marker — silently, so a hung gate would run until the
# CI job's own timeout killed it with no indication of which gate hung.
e2e: install ## run the language-layer end-to-end suite against real toolchains (opt-in, mother repo only)
	@printf "${BLUE}[INFO] Running end-to-end suite: $(E2E_ARGS)${RESET}\n"
	@RHIZA_E2E=1 ${UV_BIN} run --with pytest-timeout pytest $(E2E_ARGS) -v
