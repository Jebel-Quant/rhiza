## src.mk - Source code targets
# This file is included by the main Makefile.
# It provides targets for type checking, documentation, and security analysis.

# Contribute to deptry folders
DEPTRY_FOLDERS += src

# Declare phony targets (they don't produce files)
.PHONY: mypy docs security typecheck

# Logo file for pdoc (relative to project root).
# 1. Defaults to the Rhiza logo if present.
# 2. Can be overridden in Makefile or local.mk (e.g. LOGO_FILE := my-logo.png)
# 3. If set to empty string, no logo will be used.
LOGO_FILE ?= assets/rhiza-logo.svg

##@ src

# The 'mypy' target runs static type analysis using pyproject.toml config.
mypy: install ## run mypy type checking
	@printf "${BLUE}[INFO] Running mypy type checking...${RESET}\n"
	@${UVX_BIN} -p ${PYTHON_VERSION} mypy "src" --strict --config-file=pyproject.toml

# The 'docs' target generates API documentation using pdoc.
# Finds Python packages by locating __init__.py files under the source folder.
# Detects docformat from ruff.toml or defaults to google.
docs:: install ## create documentation with pdoc
	@rm -rf _pdoc
	@PKGS=$$(find "src" -name "__init__.py" -type f | \
	  sed "s|^src/||" | \
	  sed 's|/[^/]*$$||' | \
	  cut -d'/' -f1 | \
	  sort -u | \
	  tr '\n' ' '); \
	if [ -z "$$PKGS" ]; then \
	  printf "${YELLOW}[WARN] No packages found under src, skipping docs${RESET}\n"; \
	else \
	  TEMPLATE_ARG=""; \
	  if [ -d "${PDOC_TEMPLATE_DIR}" ]; then \
	    TEMPLATE_ARG="-t ${PDOC_TEMPLATE_DIR}"; \
	    printf "${BLUE}[INFO] Using pdoc templates from ${PDOC_TEMPLATE_DIR}${RESET}\n"; \
	  fi; \
	  DOCFORMAT="$(DOCFORMAT)"; \
	  if [ -z "$$DOCFORMAT" ]; then \
	    if [ -f "ruff.toml" ]; then \
	      DOCFORMAT=$$(${UV_BIN} run python -c "import tomllib; print(tomllib.load(open('ruff.toml', 'rb')).get('lint', {}).get('pydocstyle', {}).get('convention', ''))"); \
	    fi; \
	    if [ -z "$$DOCFORMAT" ]; then \
	      DOCFORMAT="google"; \
	    fi; \
	    printf "${BLUE}[INFO] Detected docformat: $$DOCFORMAT${RESET}\n"; \
	  else \
	    printf "${BLUE}[INFO] Using provided docformat: $$DOCFORMAT${RESET}\n"; \
	  fi; \
	  LOGO_ARG=""; \
	  if [ -n "$(LOGO_FILE)" ] && [ -f "$(LOGO_FILE)" ]; then \
	    MIME=$$(file --mime-type -b "$(LOGO_FILE)"); \
	    DATA=$$(base64 < "$(LOGO_FILE)" | tr -d '\n'); \
	    LOGO_ARG="--logo data:$$MIME;base64,$$DATA"; \
	    printf "${BLUE}[INFO] Embedding logo: $(LOGO_FILE)${RESET}\n"; \
	  fi; \
	  ${UV_BIN} pip install pdoc && \
	  PYTHONPATH="src" ${UV_BIN} run pdoc --docformat $$DOCFORMAT --output-dir _pdoc $$TEMPLATE_ARG $$LOGO_ARG $$PKGS; \
	fi

# The 'security' target performs security vulnerability scans.
# Runs pip-audit for dependencies and bandit for source code.
security: install ## run security scans (pip-audit and bandit)
	@printf "${BLUE}[INFO] Running pip-audit for dependency vulnerabilities...${RESET}\n"
	@${UVX_BIN} pip-audit
	@printf "${BLUE}[INFO] Running bandit security scan...${RESET}\n"
	@${UVX_BIN} bandit -r "src" -ll -q

# The 'typecheck' target runs static type analysis using mypy.
# 1. Checks if the source directory exists.
# 2. Runs mypy on the source folder using the configuration in pyproject.toml.
typecheck: install ## run mypy type checking
	printf "${BLUE}[INFO] Running mypy type checking...${RESET}\n";
	${UVX_BIN} mypy src --config-file pyproject.toml;

