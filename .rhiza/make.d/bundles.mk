## .rhiza/make.d/bundles.mk - Bundle exploration and onboarding
# Provides make explain-bundles for new contributors unfamiliar with the bundle model.

.PHONY: explain-bundles

##@ Bundles
explain-bundles: ## print all bundles and profiles with descriptions and dependencies
	@uv run python .rhiza/utils/explain_bundles.py
