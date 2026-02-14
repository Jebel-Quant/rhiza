## .rhiza/make.d/releasing.mk - Releasing and Versioning
# This file provides targets for version bumping and release management.

# Declare phony targets (they don't produce files)
.PHONY: bump release publish release-status pre-bump post-bump pre-release post-release

# Hook targets (double-colon rules allow multiple definitions)
pre-bump:: ; @:
post-bump:: ; @:
pre-release:: ; @:
post-release:: ; @:

##@ Releasing and Versioning
bump: pre-bump ## bump version of the project
	@if [ -f "pyproject.toml" ]; then \
		$(MAKE) install; \
		PATH="$(abspath ${VENV})/bin:$$PATH" ${UVX_BIN} "rhiza-tools>=0.3.1" bump; \
		printf "${BLUE}[INFO] Checking uv.lock file...${RESET}\n"; \
		${UV_BIN} lock; \
	else \
		printf "${YELLOW}[WARN] No pyproject.toml found, skipping bump${RESET}\n"; \
	fi
	@$(MAKE) post-bump

release: pre-release install-uv ## create tag and push to remote repository triggering release workflow
	${UVX_BIN} "rhiza-tools>=0.3.1" release;
	@$(MAKE) post-release

publish: pre-release install-uv ## bump version, create tag and push in one step
	${UVX_BIN} "rhiza-tools>=0.3.1" release --with-bump;
	@$(MAKE) post-release

release-status: ## show release workflow status and latest release information
ifeq ($(FORGE_TYPE),github)
	@{ $(MAKE) --no-print-directory workflow-status; printf "\n"; $(MAKE) --no-print-directory latest-release; } 2>&1 | $${PAGER:-less -R}
else ifeq ($(FORGE_TYPE),gitlab)
	@printf "${YELLOW}[WARN] GitLab detected — release-status is not yet supported for GitLab repositories.${RESET}\n"
	@printf "${BLUE}[INFO] Please check your pipeline status in the GitLab UI.${RESET}\n"
else
	@printf "${RED}[ERROR] Could not detect forge type (.github/workflows/ or .gitlab-ci.yml not found)${RESET}\n"
endif



