## .rhiza/make.d/bundles.mk - Bundle exploration and onboarding
# Provides make explain-bundles for new contributors unfamiliar with the bundle model.
# Mother-repo-only fragment: no bundle ships it, so it is never synced downstream.

.PHONY: explain-bundles sync-self sync-self-check

##@ Bundles
explain-bundles: ## print all bundles and profiles with descriptions and dependencies
	@uv run utils/explain_bundles.py

sync-self: ## relink root dogfood copies as symlinks into bundles/ (mother repo only)
	@uv run utils/link_dogfood.py

sync-self-check: ## fail if any dogfood symlink is stale/missing without writing (CI drift guard, mother repo only)
	@uv run utils/link_dogfood.py --check
