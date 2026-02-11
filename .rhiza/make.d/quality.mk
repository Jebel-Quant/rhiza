## .rhiza/make.d/quality.mk - Quality and Formatting
# This file provides targets for code quality checks, linting, and formatting.

# Declare phony targets (they don't produce files)
.PHONY: deptry fmt fmt-rhiza fmt-src mypy

##@ Quality and Formatting
deptry: install-uv ## Run deptry
	@if [ -d ${SOURCE_FOLDER} ]; then \
		$(UVX_BIN) -p ${PYTHON_VERSION} deptry ${SOURCE_FOLDER}; \
	fi

	@if [ -d ${MARIMO_FOLDER} ]; then \
		if [ -d ${SOURCE_FOLDER} ]; then \
			$(UVX_BIN) -p ${PYTHON_VERSION} deptry ${MARIMO_FOLDER} ${SOURCE_FOLDER} --ignore DEP004; \
		else \
		  	$(UVX_BIN) -p ${PYTHON_VERSION} deptry ${MARIMO_FOLDER} --ignore DEP004; \
		fi \
	fi

fmt: install-uv ## check the pre-commit hooks and the linting
	@${UVX_BIN} -p ${PYTHON_VERSION} pre-commit run --all-files

fmt-rhiza: install-uv ## run formatting checks on rhiza framework code only
	@printf "${BLUE}[INFO] Running formatting checks on rhiza framework code (.rhiza/)...${RESET}\n"
	@if [ -d .rhiza ]; then \
		files=$$(git ls-files .rhiza/ | tr '\n' ' '); \
		if [ -n "$$files" ]; then \
			${UVX_BIN} -p ${PYTHON_VERSION} pre-commit run --files $$files; \
		else \
			printf "${YELLOW}[WARN] No files found in .rhiza/, skipping fmt-rhiza${RESET}\n"; \
		fi \
	else \
		printf "${YELLOW}[WARN] .rhiza/ directory not found, skipping fmt-rhiza${RESET}\n"; \
	fi

fmt-src: install-uv ## run formatting checks on user source code only
	@if [ -d ${SOURCE_FOLDER} ]; then \
		printf "${BLUE}[INFO] Running formatting checks on user source code (${SOURCE_FOLDER}/)...${RESET}\n"; \
		files=$$(git ls-files ${SOURCE_FOLDER}/ | tr '\n' ' '); \
		if [ -n "$$files" ]; then \
			${UVX_BIN} -p ${PYTHON_VERSION} pre-commit run --files $$files; \
		else \
			printf "${YELLOW}[WARN] No files found in ${SOURCE_FOLDER}/, skipping fmt-src${RESET}\n"; \
		fi \
	else \
		printf "${YELLOW}[WARN] Source folder ${SOURCE_FOLDER} not found, skipping fmt-src${RESET}\n"; \
	fi

mypy: install ## run mypy analysis
	@if [ -d ${SOURCE_FOLDER} ]; then \
		${UV_BIN} run mypy ${SOURCE_FOLDER} --strict --config-file=pyproject.toml; \
	fi
