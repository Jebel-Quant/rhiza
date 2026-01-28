## src.mk - Documentation targets
# This file is included by the main Makefile.
# It provides targets for ...

# Declare phony targets (they don't produce files)
.PHONY: mypy

##@ src
mypy: install-uv ## run mypy analysis
	@if [ -d ${SOURCE_FOLDER} ]; then \
		${UVX_BIN} -p ${PYTHON_VERSION} mypy ${SOURCE_FOLDER} --strict --config-file=pyproject.toml; \
	fi
