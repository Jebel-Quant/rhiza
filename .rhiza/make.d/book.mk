## book.mk - Book-building targets (MkDocs-based)

ROOT := $(shell git rev-parse --show-toplevel)

.PHONY: book serve test benchmark stress hypothesis-test _book-reports _book-notebooks

# No-op stubs — overridden by test.mk / bench.mk when present
test:: ; @:
benchmark:: ; @:
stress:: ; @:
hypothesis-test:: ; @:

BOOK_OUTPUT ?= _book

# Additional uvx --with packages to inject into mkdocs build and serve.
# Projects can extend the package list without editing this template, e.g.:
#   MKDOCS_EXTRA_PACKAGES = --with "mkdocs-graphviz"
MKDOCS_EXTRA_PACKAGES ?=

##@ Book

_book-reports: test benchmark stress hypothesis-test
	@mkdir -p docs/reports
	@for src_dir in \
	  "_tests/html-coverage:reports/coverage" \
	  "_tests/html-report:reports/test-report" \
	  "_tests/benchmarks:reports/benchmarks" \
	  "_tests/stress:reports/stress" \
	  "_tests/hypothesis:reports/hypothesis"; do \
	  src=$${src_dir%%:*}; dest=docs/$${src_dir#*:}; \
	  if [ -d "$$src" ] && [ -n "$$(ls -A "$$src" 2>/dev/null)" ]; then \
	    printf "${BLUE}[INFO] Copying $$src -> $$dest${RESET}\n"; \
	    mkdir -p "$$dest"; cp -r "$$src/." "$$dest/"; \
	  else \
	    printf "${YELLOW}[WARN] $$src not found, skipping${RESET}\n"; \
	  fi; \
	done
	@printf "# Reports\n\n" > docs/reports.md
	@[ -f "docs/reports/test-report/report.html" ] && echo "- [Test Report](reports/test-report/report.html)"       >> docs/reports.md || true
	@[ -f "docs/reports/hypothesis/report.html" ]  && echo "- [Hypothesis Report](reports/hypothesis/report.html)" >> docs/reports.md || true
	@[ -f "docs/reports/benchmarks/report.html" ]  && echo "- [Benchmarks](reports/benchmarks/report.html)"        >> docs/reports.md || true
	@[ -f "docs/reports/stress/report.html" ]      && echo "- [Stress Report](reports/stress/report.html)"          >> docs/reports.md || true
	@[ -f "docs/reports/coverage/index.html" ]     && echo "- [Coverage Report](reports/coverage/index.html)"      >> docs/reports.md || true

_book-notebooks:
	@if [ -d "$(MARIMO_FOLDER)" ]; then \
	  for nb in $(MARIMO_FOLDER)/*.py; do \
	    name=$$(basename "$$nb" .py); \
	    printf "${BLUE}[INFO] Exporting $$nb${RESET}\n"; \
	    abs_output="$$(pwd)/docs/notebooks/$$name.html"; \
	    mkdir -p docs/notebooks; \
	    (cd "$$(dirname "$$nb")" && ${UV_BIN} run marimo export html --sandbox "$$(basename "$$nb")" -o "$$abs_output"); \
	  done; \
	  printf "# Marimo Notebooks\n\n" > docs/notebooks.md; \
	  for html in docs/notebooks/*.html; do \
	    name=$$(basename "$$html" .html); \
	    echo "- [$$name]($$name.html)" >> docs/notebooks.md; \
	  done; \
	fi

# Serve the built book locally on port 8000.
# Uses Python's built-in HTTP server so the JetBrains built-in server (which
# refuses to serve gitignored directories like _book) is not needed.
serve: book ## build and serve the book at http://localhost:8000
	@printf "${BLUE}[INFO] Serving book at http://localhost:8000 (Ctrl-C to stop)${RESET}\n"
	@cd $(BOOK_OUTPUT) && python3 -m http.server 8000

book:: _book-reports _book-notebooks ## compile the companion book via MkDocs
	@rm -rf "$(BOOK_OUTPUT)"
	@${UVX_BIN} --with "mkdocs-material<10.0" --with "pymdown-extensions>=10.0" --with "mkdocs<2.0" $(MKDOCS_EXTRA_PACKAGES) mkdocs build -f "${ROOT}/mkdocs.yml" -d "$$(pwd)/$(BOOK_OUTPUT)"
	@touch "$(BOOK_OUTPUT)/.nojekyll"
	@printf "${GREEN}[SUCCESS] Book built at $(BOOK_OUTPUT)/${RESET}\n"
	@tree $(BOOK_OUTPUT)

