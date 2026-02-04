## Makefile.src - Source folder configuration
# This file is included by the main Makefile

# Add SOURCE_FOLDER to deptry configuration if it exists
ifneq ($(wildcard $(SOURCE_FOLDER)),)
DEPTRY_FOLDERS += $(SOURCE_FOLDER)
endif

##@ Quality and Formatting
deptry: install-uv ## Run deptry
	@printf "${BLUE}[INFO] DEPTRY_FOLDERS: ${DEPTRY_FOLDERS}${RESET}\n"
	@if [ -n "$(strip ${DEPTRY_FOLDERS})" ]; then \
		printf "${BLUE}[INFO] Running: $(UVX_BIN) -p ${PYTHON_VERSION} deptry ${DEPTRY_FOLDERS} ${DEPTRY_IGNORE}${RESET}\n"; \
		$(UVX_BIN) -p ${PYTHON_VERSION} deptry ${DEPTRY_FOLDERS} ${DEPTRY_IGNORE}; \
	fi
