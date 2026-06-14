---
description: Run the full code-quality gate (format, lint, types, tests, deps, docs, security, rhiza-test, validate)
---

Run the project's quality gates in order and report results. These mirror the
requirements in `CLAUDE.md`. Follow the command-execution policy: always prefer
`make <target>`; never invoke `.venv/bin/...` directly.

This is the **mother Rhiza repo** (`jebel-quant/rhiza`) — a collection of reusable
configuration templates, not a runtime library. It has **no `src/` directory** and
no runtime source code. Everything in this repo is locally owned and authored here;
downstream projects sync their dev infrastructure *from* this repo, so there is no
"upstream" to defer to. Score the whole repo.

Run each of the following, in order:

1. `make fmt` — pre-commit hooks (ruff format/check, markdownlint, bandit, actionlint, jsonschema, uv-lock)
2. `make typecheck` — static type checking with `ty` (being repointed from `src` to `.rhiza/utils`)
3. `make deptry` — unused/missing dependency check
4. `make docs-coverage` — docstring coverage (being repointed from `src` to `.rhiza/utils`)
5. `make test` — full test suite (runs **without** a coverage gate here, since there is no `src/` to measure with `--cov`)
6. `make security` — pip-audit + bandit scans
7. `make rhiza-test` — rhiza's own suite under `.rhiza/tests/` (the templates, Makefile-target, sync, and `.rhiza/utils/` tests that travel downstream), distinct from the root `tests/` suite collected by `make test`
8. `make validate` — validate project structure against the template repository defined in `.rhiza/template.yml`

Guidelines:

- Run the gates and let earlier failures inform the later ones, but run all of
  them so the user sees the complete picture rather than stopping at the first
  failure.
- If something fails, show the relevant output, diagnose the root cause, and
  propose (or apply, if clearly correct and low-risk) a fix.
- If `$ARGUMENTS` is non-empty, treat it as a scope hint (e.g. a subset of gates
  to run, or specific files/paths to focus the checks on) and adjust accordingly.
- End with a concise PASS/FAIL summary per gate.

Expected skips are not failures. While `make typecheck` and `make docs-coverage`
are being repointed from `src` to `.rhiza/utils`, they may still print a
`[WARN] Source folder src not found, skipping…` and exit clean; once repointed
they run against `.rhiza/utils`. `make test` runs without a coverage gate (there
is no `src/` to measure with `--cov`). `make validate` **skips its
structure-validation step by design in this repo** — the mother repo ships no
`.rhiza/template.yml`, so it prints `[INFO] Skipping validate in rhiza repository
(no template.yml by design)` and exits clean; note that `validate` depends on
`rhiza-test`, so it re-runs that suite as a prerequisite. Report any of these as
**SKIP (by design)** — do not score them as failures or gaps.

Test depth (replaces line-coverage scoring). Since there is no runtime source,
there is no line-coverage percentage to hit. Judge the test suite by **behavioural
breadth**: how thoroughly `.rhiza/tests/` and `tests/` exercise the templates,
Makefile targets, bundle composition, sync/README validation, and the Python
utilities under `.rhiza/utils/`. A gap here means a template behaviour or Makefile
target that ships unverified — flag the specific bundle/target and the test that
would close it.

Dependency hygiene (`make deptry`). A clean run is positive evidence; any
missing/unused/transitive findings are an in-scope gap to flag against
`pyproject.toml`.

Then report:

A pass/fail summary per step (use SKIP for the by-design skips above).
Failures grouped by file, with the specific rule/error and line.
A prioritized list of what to fix first (blocking errors before style nits).
Then analyse the repo and give marks on a scale of 1 to 10 for all relevant subcategories. Pick the subcategories that fit what you actually observe — e.g. linting/style, test pass rate, test depth & coverage of templates, template & config correctness, code structure & readability, documentation, dependency & security hygiene, CI/tooling health. For each: the score, a one-line justification grounded in evidence from the checks above (and a quick look at the code/templates where needed), and what would raise it. Close with an overall score and the single highest-leverage improvement.

Scope. Score everything this repo controls: `bundles/` (the shipped templates), `.rhiza/` (the modular Makefile system in `make.d/*.mk`, `rhiza.mk`, the authoritative bundle list in `template-bundles.yml`, utilities in `utils/`, and the test suite in `tests/`), the root `tests/`, `pyproject.toml`, `pytest.ini`, `ruff.toml`, `.pre-commit-config.yaml`, `Makefile`, `README.md`, `docs/`, and the CI workflows in `.github/workflows/` and `.gitlab-ci.yml`. All of this is authored here — there is nothing "Rhiza-owned but external". If a file is machine-generated (e.g. README sections injected by the `make`-help hook, or `.lock.yml` compiled from agentic-workflow `.md` sources), note that it is generated and score the source, not the artifact.

Then, from the scorecard above, identify actionable issues to improve the score — one per subcategory scoring below 10 (skip any that are maxed). For each, give: a concrete title, the subcategory and current→target score it moves, the specific file(s)/lines or config to change, and a crisp acceptance criterion ("done when…"). Order them by leverage (biggest score gain for least effort first). This is a list of recommendations only — do not create GitHub issues or change code unless I explicitly ask.

If everything passes, say so plainly — but still produce the 1–10 subcategory marks. Do not fix anything unless I ask — this command only assesses.
