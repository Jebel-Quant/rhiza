## .rhiza/make.d/go.mk - the Go language layer (bundle: go-core)
#
# The third sibling of python.mk and rust.mk. `core` provides the make framework
# and uv/uvx as a tool runner (pre-commit, mkdocs and semgrep run through uvx
# whatever the project is written in); this file turns that into a Go project.
#
# It keeps the language-layer contract: `install` and `all` mean the same thing
# they do in the other layers, so book.mk and the CI workflows can call them
# without knowing the language. Only one language layer is ever synced into a repo.
#
# Like rust.mk and unlike python.mk, the test targets live here rather than in a
# separate `tests` bundle: pytest, coverage and type checking each need
# configuration files, while `go test` and `go tool cover` need none.

# Declare phony targets (they don't produce files)
.PHONY: all coverage deps docs-coverage go-tools install license rhiza-test security test typecheck

GO ?= go

# Extra flags for the test-running gates — e.g. GO_FLAGS="-tags integration".
GO_FLAGS ?=

# `-race` is the Go idiom for a CI test run and `-shuffle=on` catches tests that
# depend on declaration order. Override to drop them on a slow machine.
GO_TEST_FLAGS ?= -race -shuffle=on

# Coverage floor, mirroring COVERAGE_FAIL_UNDER in the other layers.
COVERAGE_FAIL_UNDER ?= 90

# Tool binaries land in the same ./bin core installs uv into, so a gate never
# depends on what happens to be in the developer's global GOPATH.
GO_BIN_DIR ?= $(INSTALL_DIR)

# Tools installed on demand by `go-tools`. Pinning happens through these
# variables rather than inline, so Renovate (or a human) has one line to bump.
GOLANGCI_LINT_VERSION ?= latest
GOVULNCHECK_VERSION ?= latest
GO_LICENSES_VERSION ?= latest
GOCOVER_COBERTURA_VERSION ?= latest
REVIVE_VERSION ?= latest

GO_TOOLS ?= \
	github.com/golangci/golangci-lint/v2/cmd/golangci-lint@$(GOLANGCI_LINT_VERSION) \
	golang.org/x/vuln/cmd/govulncheck@$(GOVULNCHECK_VERSION) \
	github.com/google/go-licenses@$(GO_LICENSES_VERSION) \
	github.com/boumenot/gocover-cobertura@$(GOCOVER_COBERTURA_VERSION) \
	github.com/mgechev/revive@$(REVIVE_VERSION)

##@ Go
install: pre-install ## install the toolchain and download dependencies
	@if ! command -v $(GO) >/dev/null 2>&1; then \
	  printf "${RED}[ERROR] go not found.${RESET}\n"; \
	  printf "${YELLOW}       Install it by following https://go.dev/doc/install${RESET}\n"; \
	  printf "${YELLOW}       (or your platform's package manager: brew install go)${RESET}\n"; \
	  exit 1; \
	fi

	# go.mod's `go` and `toolchain` directives pin the language and compiler
	# version, and the go command downloads a matching toolchain on demand — so
	# there is no rustup step to mirror here.
	@if [ -f "go.mod" ]; then \
	  printf "${BLUE}[INFO] Downloading dependencies${RESET}\n"; \
	  $(GO) mod download; \
	else \
	  printf "${YELLOW}[WARN] No go.mod found, skipping download${RESET}\n"; \
	fi

	# Install pre-commit hooks (skip when core.hooksPath is set, e.g. by an
	# external hook manager — pre-commit refuses to install in that case)
	@if [ -f ".pre-commit-config.yaml" ]; then \
	  if [ -n "$$(git config --get core.hooksPath 2>/dev/null)" ]; then \
	    printf "${BLUE}[INFO] Skipping pre-commit hook install: core.hooksPath is set${RESET}\n"; \
	  else \
	    printf "${BLUE}[INFO] Installing pre-commit hooks...${RESET}\n"; \
	    ${UVX_BIN} -p ${PYTHON_VERSION} pre-commit install || { printf "${YELLOW}[WARN] Failed to install pre-commit hooks${RESET}\n"; }; \
	  fi; \
	fi

	@$(MAKE) post-install

	@printf "\n${GREEN}[SUCCESS] Installation complete!${RESET}\n\n"

go-tools: ## install the Go tools the gates need (idempotent)
	@mkdir -p $(GO_BIN_DIR)
	@for tool in $(GO_TOOLS); do \
	  name=$$(basename $${tool%@*}); \
	  if [ -x "$(GO_BIN_DIR)/$$name" ]; then \
	    continue; \
	  fi; \
	  printf "${BLUE}[INFO] Installing $$name${RESET}\n"; \
	  GOBIN="$(GO_BIN_DIR)" $(GO) install "$$tool" || { printf "${RED}[ERROR] Failed to install $$name${RESET}\n"; exit 1; }; \
	done
	@printf "${BLUE}[INFO] All Go tools available in $(GO_BIN_DIR)${RESET}\n"

all: fmt test docs-coverage security deps license typecheck rhiza-test ## run all CI targets locally

# Double-colon, matching test.mk and rust.mk: book.mk declares `test:: ; @:` as a
# no-op default so `make book` works without a test bundle, and make rejects a
# target that has both a `:` and a `::` rule.
test:: install ## run the test suite
	@printf "${BLUE}[INFO] Running tests${RESET}\n"
	@rm -rf _tests
	@mkdir -p _tests
	@$(GO) test ./... $(GO_TEST_FLAGS) $(GO_FLAGS)

coverage: install go-tools ## measure coverage and emit the reports book.mk consumes
	@printf "${BLUE}[INFO] Measuring coverage (floor: $(COVERAGE_FAIL_UNDER)%%)${RESET}\n"
	@mkdir -p _tests/html-coverage
	# -covermode=atomic because the default `set` mode is not race-safe and the
	# test run above is a race build.
	@$(GO) test ./... -covermode=atomic -coverprofile=_tests/coverage.out $(GO_FLAGS)
	# Cobertura XML at exactly the path book.mk's badge step reads, so the docs
	# site gets a measured coverage badge on Go projects too.
	@$(GO_BIN_DIR)/gocover-cobertura < _tests/coverage.out > _tests/coverage.xml
	@$(GO) tool cover -html=_tests/coverage.out -o _tests/html-coverage/index.html
	# `go test` has no --fail-under; the total line from `go tool cover -func` is
	# where the number lives, so the floor is enforced here.
	@$(GO) tool cover -func=_tests/coverage.out | awk -v floor=$(COVERAGE_FAIL_UNDER) ' \
		/^total:/ { \
			pct = $$3; sub(/%/, "", pct); \
			if (pct + 0 < floor + 0) { \
				printf "[ERROR] Coverage %s%% is below the %s%% floor\n", pct, floor; \
				exit 1; \
			} \
			printf "[INFO] Coverage %s%% (floor: %s%%)\n", pct, floor; \
		}'

typecheck: install go-tools ## vet and lint (the compiler already type-checks)
	@printf "${BLUE}[INFO] Running go vet${RESET}\n"
	@$(GO) vet ./... $(GO_FLAGS)
	@printf "${BLUE}[INFO] Running golangci-lint${RESET}\n"
	@$(GO_BIN_DIR)/golangci-lint run

docs-coverage: install go-tools ## fail on any undocumented exported item
	# revive's `exported` rule is the closest analogue of interrogate: it is
	# pass/fail on missing doc comments rather than a percentage, exactly as
	# rust-core's `-D missing_docs` is. revive.toml enables that rule and no other.
	@printf "${BLUE}[INFO] Checking doc comments on exported items${RESET}\n"
	@$(GO_BIN_DIR)/revive -config revive.toml -set_exit_status ./...

security: install go-tools ## scan dependencies for known vulnerabilities
	@printf "${BLUE}[INFO] Running govulncheck${RESET}\n"
	@$(GO_BIN_DIR)/govulncheck ./...

deps: install ## report dependency drift (the deptry analogue)
	# `go mod tidy -diff` (Go 1.23+) reports what tidy *would* change and exits
	# non-zero, which is both the unused-dependency and the missing-dependency
	# check in one command. No tool to install.
	@printf "${BLUE}[INFO] Checking that go.mod and go.sum are tidy${RESET}\n"
	@$(GO) mod tidy -diff

license: install go-tools ## run license compliance scan
	@printf "${BLUE}[INFO] Running license compliance scan${RESET}\n"
	@$(GO_BIN_DIR)/go-licenses check ./...

rhiza-test: install ## run rhiza's own tests (if any)
	# The template's self-tests validate READMEs and YAML, not Go code, so they
	# stay Python and run through uv here rather than being ported.
	@if [ -d ".rhiza/tests" ]; then \
		${UV_BIN} run --with pytest --with pytest-timeout --with python-dotenv --with packaging pytest .rhiza/tests; \
	else \
		printf "${YELLOW}[WARN] No .rhiza/tests directory found, skipping rhiza-tests${RESET}\n"; \
	fi
