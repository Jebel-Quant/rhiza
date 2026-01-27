## security.mk - Security scanning targets
# This file is included by the main Makefile.
# It provides targets for security vulnerability scans.

# Declare phony targets (they don't produce files)
.PHONY: security

##@ Security

# The 'security' target performs security vulnerability scans.
# 1. Runs pip-audit to check for known vulnerabilities in dependencies.
# 2. Runs bandit to find common security issues in the source code.
security: install ## run security scans (pip-audit and bandit)
	@printf "${BLUE}[INFO] Running pip-audit for dependency vulnerabilities...${RESET}\n"
	@${UVX_BIN} pip-audit
	@printf "${BLUE}[INFO] Running bandit security scan...${RESET}\n"
	@${UVX_BIN} bandit -r ${SOURCE_FOLDER} -ll -q
