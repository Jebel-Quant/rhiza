## .rhiza/make.d/rust.mk - the Rust language layer (bundle: rust-core)
#
# The Rust sibling of python.mk. `core` provides the make framework and uv/uvx as
# a tool runner (pre-commit, mkdocs and semgrep run through uvx whatever the
# project is written in); this file turns that into a Rust project.
#
# It keeps the language-layer contract: `install` and `all` mean the same thing
# they do in python.mk, so book.mk and the CI workflows can call them without
# knowing the language. Only one language layer is ever synced into a repo.
#
# Unlike Python, the test targets live here rather than in a separate `tests`
# bundle: pytest, coverage and type checking each need configuration files, while
# their Rust counterparts are cargo subcommands with nothing to configure.

# Declare phony targets (they don't produce files)
.PHONY: all cargo-tools coverage deps docs-coverage doctor install license security test typecheck

CARGO ?= cargo
RUSTC ?= rustc
RUSTUP ?= rustup

# Extra flags for the whole gate set — e.g. CARGO_FLAGS="--all-features".
CARGO_FLAGS ?=

# Coverage floor, mirroring COVERAGE_FAIL_UNDER in the Python layer.
COVERAGE_FAIL_UNDER ?= 90

# Tools installed on demand by `cargo-tools`. cargo-binstall fetches prebuilt
# binaries where a project publishes them and falls back to a source build, which
# turns a multi-minute `cargo install` into seconds on CI.
CARGO_TOOLS ?= cargo-nextest cargo-llvm-cov cargo-deny cargo-machete

# Where `cargo install` puts a subcommand's binary — and it is *not* necessarily on
# PATH. `brew install rustup` (which install's error above suggests) leaves the
# shims in Homebrew's bin and never links ~/.cargo/bin, and `cargo install` only
# warns about that rather than failing. Cargo resolves `cargo <sub>` by searching
# this directory as well as PATH, so every gate below is fine either way; what is
# not fine is `command -v cargo-nextest` or a bare `cargo-binstall`, which see only
# PATH. So `cargo-tools` probes both, and invokes binstall as a cargo subcommand.
# Honours the two variables cargo itself reads, in the order cargo reads them.
CARGO_BIN_DIR ?= $(if $(CARGO_INSTALL_ROOT),$(CARGO_INSTALL_ROOT),$(if $(CARGO_HOME),$(CARGO_HOME),$(HOME)/.cargo))/bin

##@ Rust
install: pre-install ## install the toolchain and fetch dependencies
	@if ! command -v $(RUSTUP) >/dev/null 2>&1; then \
	  printf "${RED}[ERROR] rustup not found.${RESET}\n"; \
	  printf "${YELLOW}       Install it by following https://rustup.rs${RESET}\n"; \
	  printf "${YELLOW}       (or your platform's package manager: brew install rustup)${RESET}\n"; \
	  exit 1; \
	fi

	# rust-toolchain.toml pins the channel and components; `rustup show` is what
	# materialises them, because rustup installs a pinned toolchain lazily.
	@if [ -f "rust-toolchain.toml" ]; then \
	  printf "${BLUE}[INFO] Installing the toolchain pinned in rust-toolchain.toml${RESET}\n"; \
	  $(RUSTUP) show >/dev/null; \
	else \
	  printf "${YELLOW}[WARN] No rust-toolchain.toml found, using the active default toolchain${RESET}\n"; \
	fi

	@if [ -f "Cargo.toml" ]; then \
	  printf "${BLUE}[INFO] Fetching dependencies${RESET}\n"; \
	  $(CARGO) fetch --locked 2>/dev/null || $(CARGO) fetch; \
	else \
	  printf "${YELLOW}[WARN] No Cargo.toml found, skipping fetch${RESET}\n"; \
	fi

	# Install pre-commit hooks (skip when core.hooksPath is set, e.g. by an
	# external hook manager — pre-commit refuses to install in that case)
	#
	# `-c` for the reason quality.mk's `fmt` passes `--config`, and it must be repeated
	# here: prek bakes the flag into the generated shim, so without it the commit-time
	# gate rediscovers nested projects and stops meaning what `make fmt` means. A
	# consumer who wants prek's monorepo behaviour drops the flag from both places.
	@if [ -f ".pre-commit-config.yaml" ]; then \
	  if [ -n "$$(git config --get core.hooksPath 2>/dev/null)" ]; then \
	    printf "${BLUE}[INFO] Skipping pre-commit hook install: core.hooksPath is set${RESET}\n"; \
	  else \
	    printf "${BLUE}[INFO] Installing pre-commit hooks...${RESET}\n"; \
	    ${UVX_BIN} prek install -c .pre-commit-config.yaml || { printf "${YELLOW}[WARN] Failed to install pre-commit hooks${RESET}\n"; }; \
	  fi; \
	fi

	@$(MAKE) post-install

	@printf "\n${GREEN}[SUCCESS] Installation complete!${RESET}\n\n"

cargo-tools: ## install the cargo subcommands the gates need (idempotent)
	@if ! command -v cargo-binstall >/dev/null 2>&1 && [ ! -x "$(CARGO_BIN_DIR)/cargo-binstall" ]; then \
	  printf "${BLUE}[INFO] Installing cargo-binstall${RESET}\n"; \
	  $(CARGO) install cargo-binstall --locked || { printf "${RED}[ERROR] Failed to install cargo-binstall${RESET}\n"; exit 1; }; \
	fi
	@missing=""; \
	for tool in $(CARGO_TOOLS); do \
	  command -v $$tool >/dev/null 2>&1 || [ -x "$(CARGO_BIN_DIR)/$$tool" ] || missing="$$missing $$tool"; \
	done; \
	if [ -n "$$missing" ]; then \
	  printf "${BLUE}[INFO] Installing:${RESET}$$missing\n"; \
	  $(CARGO) binstall --no-confirm --locked $$missing || { printf "${RED}[ERROR] Failed to install cargo tools${RESET}\n"; exit 1; }; \
	else \
	  printf "${BLUE}[INFO] All cargo tools already installed${RESET}\n"; \
	fi

all: fmt test docs-coverage security deps license typecheck rhiza-test ## run all CI targets locally

# Double-colon, matching test.mk: book.mk declares `test:: ; @:` as a no-op default
# so `make book` works without a test bundle, and make rejects a target that has both
# a `:` and a `::` rule.
test:: install cargo-tools ## run the test suite with nextest
	@printf "${BLUE}[INFO] Running tests${RESET}\n"
	@rm -rf _tests
	@mkdir -p _tests
	@$(CARGO) nextest run --all-targets $(CARGO_FLAGS)
	# nextest does not run doctests — cargo test does, and they are real tests.
	@printf "${BLUE}[INFO] Running doctests${RESET}\n"
	@$(CARGO) test --doc $(CARGO_FLAGS)

coverage: install cargo-tools ## measure coverage and emit the reports book.mk consumes
	@printf "${BLUE}[INFO] Measuring coverage (floor: $(COVERAGE_FAIL_UNDER)%%)${RESET}\n"
	@mkdir -p _tests/html-coverage
	# Cobertura XML at exactly the path book.mk's badge step reads, so the docs
	# site gets a measured coverage badge on Rust projects too.
	@$(CARGO) llvm-cov nextest \
		--all-targets $(CARGO_FLAGS) \
		--fail-under-lines $(COVERAGE_FAIL_UNDER) \
		--cobertura --output-path _tests/coverage.xml
	@$(CARGO) llvm-cov report --html --output-dir _tests/html-coverage

typecheck: install ## lint with clippy, warnings as errors (rustc already type-checks)
	@printf "${BLUE}[INFO] Running clippy${RESET}\n"
	@$(CARGO) clippy --all-targets $(CARGO_FLAGS) -- -D warnings

docs-coverage: install ## fail on any undocumented public item
	@printf "${BLUE}[INFO] Building docs with missing_docs denied${RESET}\n"
	@RUSTDOCFLAGS="-D missing_docs -D rustdoc::broken_intra_doc_links" \
		$(CARGO) doc --no-deps $(CARGO_FLAGS)

security: install cargo-tools ## scan dependencies for known advisories
	@printf "${BLUE}[INFO] Running cargo-deny advisories${RESET}\n"
	@$(CARGO) deny check advisories

deps: install cargo-tools ## report unused dependencies (the deptry analogue)
	@printf "${BLUE}[INFO] Checking for unused dependencies${RESET}\n"
	@$(CARGO) machete

license: install cargo-tools ## run license compliance scan (allow-list in deny.toml)
	@printf "${BLUE}[INFO] Running license compliance scan${RESET}\n"
	@$(CARGO) deny check licenses


# A second `doctor::` rule — core's checks uv/make/git, this adds the two Rust facts no
# version check would catch. Both have already cost real debugging time.
#
# 1. A cargo that is not rustup-managed. `brew install rust` and `brew install rustup`
#    can coexist, and Homebrew links the *formula's* cargo into /opt/homebrew/bin while
#    rustup's shims sit unlinked in /opt/homebrew/opt/rustup/bin. `cargo --version` looks
#    perfectly healthy; what breaks is everything depending on rustup semantics.
#    `rust-toolchain.toml`'s pinned components go to rustup's toolchain while the active
#    cargo reads a different sysroot — so `make coverage` fails with "failed to find
#    llvm-tools-preview" while `rustup component list` cheerfully shows it installed.
#    Detected by asking where the sysroot is, not by matching version strings.
#
# 2. The llvm-tools binaries themselves, which is what `cargo llvm-cov` actually needs.
#    Checked directly, so a rustup-managed toolchain whose components were never
#    materialised reports the same way — the symptom is what matters, not the cause.
#
# Advisory by design: it exits 0. A Rust developer who never runs `make coverage` is not
# blocked by a missing component, and `doctor` is a diagnostic rather than a gate.
doctor:: ## report Rust toolchain problems the version checks cannot see
	@if ! command -v $(CARGO) >/dev/null 2>&1; then \
	  printf "${YELLOW}[WARN]${RESET} %-11s not found - install: https://rustup.rs\n" "cargo"; \
	else \
	  sysroot="$$($(RUSTC) --print sysroot 2>/dev/null)"; \
	  rustup_home="$${RUSTUP_HOME:-$$HOME/.rustup}"; \
	  case "$$sysroot" in \
	    "$$rustup_home"*) \
	      printf "${GREEN}[ OK ]${RESET} %-11s rustup-managed\n" "cargo" ;; \
	    *) \
	      printf "${YELLOW}[WARN]${RESET} %-11s not rustup-managed (sysroot: %s)\n" "cargo" "$$sysroot"; \
	      printf "         rust-toolchain.toml's components go to %s, which this cargo does not read.\n" "$$rustup_home"; \
	      if command -v $(RUSTUP) >/dev/null 2>&1; then \
	        printf "         rustup is installed but shadowed. Put its shims first on PATH, or remove\n"; \
	        printf "         the duplicate toolchain (on Homebrew: brew uninstall rust).\n"; \
	      else \
	        printf "         Install rustup so the pinned toolchain and its components are honoured.\n"; \
	      fi ;; \
	  esac; \
	  if [ -n "$$sysroot" ]; then \
	    host="$$($(RUSTC) -vV 2>/dev/null | awk '/^host:/ {print $$2}')"; \
	    if [ -x "$$sysroot/lib/rustlib/$$host/bin/llvm-cov" ]; then \
	      printf "${GREEN}[ OK ]${RESET} %-11s present (make coverage)\n" "llvm-tools"; \
	    else \
	      printf "${YELLOW}[WARN]${RESET} %-11s missing - `make coverage` will fail\n" "llvm-tools"; \
	      printf "         rustup component add llvm-tools-preview\n"; \
	    fi; \
	  fi; \
	fi
