---
description: Run the full code-quality gate (format, lint, types, tests, deps, docs, security)
---

Run the project's quality gates in order and report results. These mirror the
requirements in `CLAUDE.md`. Follow the command-execution policy: always prefer
`make <target>`; never invoke `.venv/bin/...` directly.

Run each of the following, in order:

1. `make fmt` — pre-commit hooks (ruff format/check, markdownlint, bandit, actionlint, interrogate, jsonschema, uv-lock)
2. `make typecheck` — static type checking with `ty`
3. `make deptry` — unused/missing dependency check
4. `make docs-coverage` — docstring coverage (100% required)
5. `make test` — full test suite with coverage (90% minimum)
6. `make security` — pip-audit + bandit scans

Guidelines:

- Run the gates and let earlier failures inform the later ones, but run all of
  them so the user sees the complete picture rather than stopping at the first
  failure.
- If something fails, show the relevant output, diagnose the root cause, and
  propose (or apply, if clearly correct and low-risk) a fix.
- If `$ARGUMENTS` is non-empty, treat it as a scope hint (e.g. a subset of gates
  to run, or specific files/paths to focus the checks on) and adjust accordingly.
- End with a concise PASS/FAIL summary per gate.
