## docs.mk - API documentation generation targets
# This file is included by the main Makefile.
# It provides targets for generating API documentation using pdoc.

# Declare phony targets (they don't produce files)
.PHONY: docs

##@ Documentation

# The 'docs' target generates API documentation using pdoc.
# 1. Identifies Python packages within the source folder.
# 2. Detects the docformat (google, numpy, or sphinx) from ruff.toml or defaults to google.
# 3. Installs pdoc and generates HTML documentation in _pdoc.
docs:: install ## create documentation with pdoc
	# Clean up previous docs
	rm -rf _pdoc;

	@if [ -d "${SOURCE_FOLDER}" ]; then \
	  PKGS=""; for d in "${SOURCE_FOLDER}"/*; do [ -d "$$d" ] && PKGS="$$PKGS $$(basename "$$d")"; done; \
	  if [ -z "$$PKGS" ]; then \
	    printf "${YELLOW}[WARN] No packages found under ${SOURCE_FOLDER}, skipping docs${RESET}\n"; \
	  else \
	    TEMPLATE_ARG=""; \
	    if [ -d "$(PDOC_TEMPLATE_DIR)" ]; then \
	      TEMPLATE_ARG="-t $(PDOC_TEMPLATE_DIR)"; \
	      printf "$(BLUE)[INFO] Using pdoc templates from $(PDOC_TEMPLATE_DIR)$(RESET)\n"; \
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
	    if [ -n "$(LOGO_FILE)" ]; then \
	      if [ -f "$(LOGO_FILE)" ]; then \
	        MIME=$$(file --mime-type -b "$(LOGO_FILE)"); \
	        DATA=$$(base64 < "$(LOGO_FILE)" | tr -d '\n'); \
	        LOGO_ARG="--logo data:$$MIME;base64,$$DATA"; \
	        printf "${BLUE}[INFO] Embedding logo: $(LOGO_FILE)${RESET}\n"; \
	      else \
	        printf "${YELLOW}[WARN] Logo file $(LOGO_FILE) not found, skipping${RESET}\n"; \
	      fi; \
	    fi; \
	    ${UV_BIN} pip install pdoc && \
	    PYTHONPATH="${SOURCE_FOLDER}" ${UV_BIN} run pdoc --docformat $$DOCFORMAT --output-dir _pdoc $$TEMPLATE_ARG $$LOGO_ARG $$PKGS; \
	  fi; \
	else \
	  printf "${YELLOW}[WARN] Source folder ${SOURCE_FOLDER} not found, skipping docs${RESET}\n"; \
	fi
