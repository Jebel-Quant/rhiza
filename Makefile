## Makefile for jebel-quant/rhiza
# (https://github.com/jebel-quant/rhiza)
#
# Purpose: Developer tasks using uv/uvx (install, test, docs, marimushka, book).
# Lines with `##` after a target are parsed into help text,
# and lines starting with `##@` create section headers in the help output.
#
# Colors for pretty output in help messages
BLUE := \033[36m
BOLD := \033[1m
GREEN := \033[32m
RED := \033[31m
YELLOW := \033[33m
RESET := \033[0m

# Default goal when running `make` with no target
.DEFAULT_GOAL := help

# Declare phony targets (they don't produce files)
.PHONY: \
	bump \
	customisations \
	help \
	post-release \
	release \
	update-readme \
	version-matrix

INSTALL_DIR ?= ./bin
UV_BIN ?= $(shell command -v uv 2>/dev/null || echo ${INSTALL_DIR}/uv)
UVX_BIN ?= $(shell command -v uvx 2>/dev/null || echo ${INSTALL_DIR}/uvx)
VENV ?= .venv

export UV_NO_MODIFY_PATH := 1
export UV_VENV_CLEAR := 1

# Load .rhiza/.env (if present) and export its variables so recipes see them.
-include .rhiza/.env

# Include split Makefiles
-include .rhiza/Makefile.rhiza
-include tests/Makefile.tests
-include book/Makefile.marimo
-include book/Makefile.book
-include presentation/Makefile.presentation
-include .rhiza/customisations/Makefile.customisations
-include .rhiza/agentic/Makefile.agentic
-include .github/Makefile.gh

help: print-logo ## Display this help message
	+@printf "$(BOLD)Usage:$(RESET)\n"
	+@printf "  make $(BLUE)<target>$(RESET)\n\n"
	+@printf "$(BOLD)Targets:$(RESET)\n"
	+@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	+@printf "\n"

##@ Releasing and Versioning
bump: ## bump version
	@if [ -f "pyproject.toml" ]; then \
		$(MAKE) install; \
		${UVX_BIN} "rhiza[tools]>=0.8.6" tools bump; \
		printf "${BLUE}[INFO] Updating uv.lock file...${RESET}\n"; \
		${UV_BIN} lock; \
	else \
		printf "${YELLOW}[WARN] No pyproject.toml found, skipping bump${RESET}\n"; \
	fi

release: install-uv ## create tag and push to remote with prompts
	@UV_BIN="${UV_BIN}" /bin/sh "${SCRIPTS_FOLDER}/release.sh"

post-release:: install-uv ## perform post-release tasks
	@:

customisations: ## list available customisation scripts
	@printf "${BLUE}${BOLD}Customisation scripts available in ${CUSTOM_SCRIPTS_FOLDER}:$(RESET)\n"
	@if [ -d "${CUSTOM_SCRIPTS_FOLDER}" ]; then \
		ls -1 "${CUSTOM_SCRIPTS_FOLDER}"/*.sh 2>/dev/null || printf "  (none)\n"; \
	else \
		printf "${YELLOW}[INFO] No customisations found in ${CUSTOM_SCRIPTS_FOLDER}${RESET}\n"; \
	fi

update-readme: ## update README.md with current Makefile help output
	@/bin/sh "${SCRIPTS_FOLDER}/update-readme-help.sh"

version-matrix: install-uv ## Emit the list of supported Python versions from pyproject.toml
	@${UV_BIN} run .rhiza/utils/version_matrix.py

print-% : ## print the value of a variable (usage: make print-VARIABLE)
	@printf "${BLUE}[INFO] Printing value of variable '$*':${RESET}\n"
	@printf "${BOLD}Value of $*:${RESET}\n"
	@printf "${GREEN}"
	@printf "%s\n" "$($*)"
	@printf "${RESET}"
	@printf "${BLUE}[INFO] End of value for '$*'${RESET}\n"
