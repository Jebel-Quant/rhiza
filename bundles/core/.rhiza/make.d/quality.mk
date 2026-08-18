## .rhiza/make.d/quality.mk - Quality and Formatting
# The language-neutral gates: pre-commit, the TODO sweep, semgrep, and the runner for
# the template's own test suite. Everything that needs to know how the project declares
# its dependencies — `deptry`, the licence-compliance scan — and the `all` aggregate that
# names the per-language gates live in the language layer (python.mk, from the
# python-core bundle).

# Declare phony targets (they don't produce files)
.PHONY: fmt todos semgrep rhiza-test

##@ Quality and Formatting
# prek rather than pre-commit: a Rust reimplementation that reads the same
# `.pre-commit-config.yaml` and needs no Python of its own. Two consequences, one
# gained and one that has to be asked for.
#
# Gained: the `-p ${PYTHON_VERSION}` this recipe used to carry is gone. That flag
# existed because `uvx pre-commit` had to choose an interpreter to run pre-commit
# *itself* on, and a Rust or Go project ships no `.python-version` — so the whole
# language-neutral half of the template rested on rhiza.mk's fallback resolving to
# something real. prek is a binary and provisions each hook's toolchain itself, so the
# coupling is removed rather than merely satisfied.
#
# Asked for: `--config`. By default prek treats every directory below the root that
# holds a `.pre-commit-config.yaml` as a separate *project* and runs each one's hooks —
# useful in a monorepo, surprising anywhere else, and wrong in rhiza's own repo, where
# `bundles/{python,rust,go}-core` each ship one as template content. (go-core's hooks
# then run `go vet ./...` in a directory with no `go.mod` and fail.) Naming the config
# explicitly disables that discovery, so `make fmt` means exactly what it meant under
# pre-commit: this repo's config, once. A consumer who wants the monorepo behaviour
# drops the flag. `.prekignore` is documented for the same job but is not honoured by
# prek 0.4.12, so it is not what this relies on.
fmt: install-uv ## check the pre-commit hooks and the linting
	@${UVX_BIN} prek run --all-files --config .pre-commit-config.yaml

todos: ## search and report all TODO/FIXME/HACK comments in the codebase
	@printf "${BLUE}[INFO] Searching for TODO, FIXME, and HACK comments...${RESET}\n"
	@printf "${BOLD}Found the following items:${RESET}\n\n"
	@find . -type f \( -name "*.py" -o -name "*.mk" -o -name "*.sh" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" \) \
		-not -path "./.venv/*" \
		-not -path "./.git/*" \
		-not -path "./node_modules/*" \
		-not -path "./.tox/*" \
		-not -path "./build/*" \
		-not -path "./dist/*" \
		-print0 | xargs -0 grep -nHE "(TODO|FIXME|HACK):" 2>/dev/null | \
		grep -v "make todos" | \
		awk -F: '{ printf "${YELLOW}%s${RESET}:${GREEN}%s${RESET}: %s\n", $$1, $$2, substr($$0, index($$0,$$3)) }' || \
		printf "${GREEN}[SUCCESS] No TODO/FIXME/HACK comments found!${RESET}\n"
	@printf "\n${BLUE}[INFO] Search complete.${RESET}\n"

# semgrep takes its folder list from an accumulator, exactly as `typecheck`, `security`,
# `docs-coverage` and `deps` do since #1505. It was left on the old `[ -d $(SOURCE_FOLDER) ]`
# form by that change because it is the one static gate owned by *core* rather than by
# python.mk, so it sat outside the file being edited — and outside the guard, whose
# `_SCOPED_GATES` list named only the four (#1511).
#
# The consequence was the same one #1505 existed to remove: on a repo with no `src/` the
# recipe printed a warning and exited 0 having analysed nothing. That is a silent pass in
# the mother repo, where `.github/workflows/rhiza_weekly.yml` runs `make semgrep` on a
# schedule, and in any downstream project keeping Python outside its source root.
#
# The accumulator is declared here, in core, and seeded from SOURCE_FOLDER when that
# folder exists — SOURCE_FOLDER is a core variable (rhiza.mk), not a Python-layer one, so
# nothing about this reaches across the language-layer boundary. A project with no `src/`
# contributes its folders by appending, the way .rhiza/make.d/bundles.mk contributes
# `utils` here.
SEMGREP_FOLDERS ?=
ifneq ($(wildcard $(SOURCE_FOLDER)),)
SEMGREP_FOLDERS += $(SOURCE_FOLDER)
endif

semgrep: install ## run Semgrep static analysis
	@semgrep_paths="$(strip $(SEMGREP_FOLDERS))"; \
	if [ -n "$${semgrep_paths}" ]; then \
		printf "${BLUE}[INFO] Running Semgrep in:$${semgrep_paths}${RESET}\n"; \
		${UVX_BIN} semgrep --config .rhiza/semgrep.yml $${semgrep_paths}; \
	else \
		printf "${YELLOW}[WARN] No semgrep folders found (SEMGREP_FOLDERS is empty and SOURCE_FOLDER='${SOURCE_FOLDER}' does not exist), skipping semgrep.${RESET}\n"; \
	fi

# Owned by core, not by a language layer, because nothing about it is language-specific:
# The conformance suite validates the *template* — READMEs, release config, YAML — and runs
# under pytest whatever the project is written in. `uv` lives in core for the same
# reason. Each layer contributes its own modules to the suite (test_pyproject.py,
# test_cargo_toml.py, test_go_module.py) while the runner stays here, so the recipe
# exists once rather than identically in all three (#1471).
#
# `install` is a deliberate exception to core's rule of never naming a layer-owned
# target. It is a *prerequisite* here, not a definition, and the suite needs it: the
# shipped test_docstrings.py imports the project's own packages to run their doctests,
# which requires the dependencies installed. Make resolves it because every fragment is
# included into one namespace, and every profile selects exactly one language layer —
# `test_a_profile_never_selects_two_bundles_from_one_layer` and
# `test_every_profile_selects_a_language_layer` bracket that from both sides. A
# core-only tree is not a shipped configuration; there, this fails naming `install`.
#
# RHIZA_DOCTEST_FOLDERS carries the doctest scope to the shipped test_docstrings.py, which
# had resolved `src` and nothing else — so a project keeping Python outside its source root
# had its docstring examples skipped rather than checked (#1517). DOCSTRING_FOLDERS is the
# same accumulator `make docs-coverage` reads, so "has a docstring" and "the example in it
# still works" cannot end up scoped differently.
#
# Naming a python-core variable from core is safe in the way `install` above is: on a Rust
# or Go layer the variable is simply undefined, the value is empty, and the suite falls
# back to SOURCE_FOLDER exactly as before.
# The suite is a package now, not a copied folder, and it runs two different ways.
#
# `packages/rhiza-test/` present -> the local working tree: the mother repo, and any
# project the e2e suite points at it. It runs the suite *straight from source* on
# PYTHONPATH, with no build at all. Both `uvx --from <path>` and `uv run --with <path>`
# key their cached environment on the distribution name and version, so an edit that does
# not bump the version is served from a stale archive and the gate silently checks the
# previous code — `uv cache clean`, `--reinstall` and `--refresh` all failed to dislodge
# it. That is a bad failure for any gate and an absurd one here, where the thing being
# cached is the assertions. The local branch must win in any case, or rhiza would gate its
# own PRs on the last *released* suite and never test a change to it.
#
# Otherwise -> the synced ref from .rhiza/template.yml, so the gate runs exactly the
# assertions matching the template version in use. Caching is correct here because a ref
# is immutable. uvx needs a tag, branch or SHA; `HEAD` is not resolvable.
RHIZA_TEST_REPO ?= https://github.com/Jebel-Quant/rhiza
RHIZA_TEST_REF  ?= $(shell sed -n 's/^[[:space:]]*ref:[[:space:]]*//p' .rhiza/template.yml 2>/dev/null | head -1)
# `#` opens a comment in make, so the URL fragment has to be escaped rather than inlined.
RHIZA_TEST_SUBDIR := \#subdirectory=packages/rhiza-test
# Overridable so the e2e suite can point a scaffolded project at *this* checkout's
# package: a scaffold has no template.yml, so without it the gate would take the no-ref
# branch and the e2e assertions would pass while running nothing.
RHIZA_TEST_PATH  ?= packages/rhiza-test
# The suite's own dependencies, named here only for the source-tree branch. The packaged
# branch gets them from the distribution's metadata; running from source has no metadata
# to read, so they have to be listed. Keep in step with packages/rhiza-test/pyproject.toml.
RHIZA_TEST_DEPS  := --with pytest --with pytest-timeout --with python-dotenv --with packaging
RHIZA_TEST_LOCAL := $(wildcard $(RHIZA_TEST_PATH)/pyproject.toml)

rhiza-test: install ## run rhiza's conformance suite against this repo
	@if [ -n '$(RHIZA_TEST_LOCAL)' ]; then \
		printf "${BLUE}[INFO] Running rhiza-test from the local working tree${RESET}\n"; \
		RHIZA_DOCTEST_FOLDERS="$(strip $(DOCSTRING_FOLDERS))" \
		PYTHONPATH="$(RHIZA_TEST_PATH)/src" \
		${UV_BIN} run $(RHIZA_TEST_DEPS) python -m rhiza_test; \
	elif [ -n '$(RHIZA_TEST_REF)' ]; then \
		printf "${BLUE}[INFO] Running rhiza-test from $(RHIZA_TEST_REPO)@$(RHIZA_TEST_REF)${RESET}\n"; \
		RHIZA_DOCTEST_FOLDERS="$(strip $(DOCSTRING_FOLDERS))" \
		${UVX_BIN} --from 'git+$(RHIZA_TEST_REPO)@$(RHIZA_TEST_REF)$(RHIZA_TEST_SUBDIR)' rhiza-test; \
	else \
		printf "${YELLOW}[WARN] no ref: in .rhiza/template.yml and no local packages/rhiza-test — skipping rhiza-test${RESET}\n"; \
	fi
