## .rhiza/make.d/bundles.mk - Bundle exploration and onboarding
# Provides make explain-bundles for new contributors unfamiliar with the bundle model.
# Mother-repo-only fragment: no bundle ships it, so it is never synced downstream.

.PHONY: explain-bundles sync-self sync-self-check sync-precommit sync-precommit-check e2e

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

# The layers' .pre-commit-config.yaml files are rendered, not written: pre-commit
# hard-codes the filename, so every language layer ships the same path and the
# neutral two thirds of it were duplicated per layer. pre-commit/base.yaml holds
# that half once and each layer fragment declares where its rendered config goes.
#
# Unlike the sync-self pair above these go through ${UV_BIN} and depend on install-uv:
# the CI job that runs the drift check is the pre-commit job, which installs no uv of
# its own and would otherwise fail on `uv: command not found` rather than on drift.
sync-precommit: install-uv ## render each layer's .pre-commit-config.yaml from pre-commit/*.yaml (mother repo only)
	@${UV_BIN} run --with pyyaml utils/render_precommit.py

sync-precommit-check: install-uv ## fail if any rendered .pre-commit-config.yaml is stale (CI drift guard, mother repo only)
	@${UV_BIN} run --with pyyaml utils/render_precommit.py --check

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
