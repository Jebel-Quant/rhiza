# CI Enforcement Model

Not every Rhiza workflow is a merge gate. Some **block** a pull request when they
fail; others are **report-only** — they publish results for inspection but never
fail CI. This page records which is which, so the intent is discoverable rather
than buried in each workflow's header.

## Blocking gates

These fail the pull request when they fail. They run on every PR via
`rhiza_ci.yml` (and the equivalent GitLab pipeline):

| Check | Workflow / target | Notes |
|-------|-------------------|-------|
| Format, lint, hooks | `make fmt` | ruff, markdownlint, bandit, actionlint, shellcheck, jsonschema, uv-lock. |
| Type checking | `make typecheck` | `ty` + `mypy --strict` over the project's Python source (set `TYPECHECKER=ty` or `TYPECHECKER=mypy` to run only one). |
| Tests | `make test`, `make rhiza-test` | Full suites; `rhiza-test` runs the rhiza repository checks, installed from `pytest-rhiza` and selected per bundle through `RHIZA_CHECKS`. |
| Dependency hygiene | `make deps` | Unused/missing dependency scan. |
| Docstring coverage | `make docs-coverage` | interrogate at 100%. |
| Security | `make security` | bandit over the folders in `BANDIT_FOLDERS`. |
| CodeQL | `rhiza_codeql.yml` | Code scanning on PR and push. |

## Conditional / opt-in gates

None in CI. `rhiza_mutation.yml` was the only one: a reusable workflow here plus a
stub in `github-tests`, both gated on a `MUTATION_ENABLED` repository variable that
was unset in this repo and, as far as we can tell, in every consumer — so the whole
path ran nowhere while carrying badge publishing, a Pages deploy and two test
modules.

The gate behind it went too. This page used to say `make mutation` still worked
locally for anyone who wanted it, and that was **false**: mutmut 3 removed
`--paths-to-mutate`, `--tests-dir` and the `html` subcommand, and the recipe
installed mutmut unpinned, so the target had been failing immediately in every
consumer since the day mutmut 3 was released (#1492). Nothing caught it, because
nothing ran it — which is exactly what removing the workflow had established. Rhiza
no longer offers mutation testing at all; removing the task from the pinned CLI is
Jebel-Quant/rhiza-task#135.

## Report-only (monitoring) workflows

These never fail a PR by design — they exist to publish security/quality signals.

### OpenSSF Scorecard (`rhiza_scorecard.yml`)

- Runs on push to `main`/`master`, weekly, on branch-protection changes, and
  manual dispatch — **not** on `pull_request`.
- Uploads SARIF to GitHub code scanning and (on public repos) publishes to the
  OpenSSF REST API that powers the README badge.
- There is no step that fails the run on a low score; a dropping score surfaces
  as a code-scanning alert and a lower badge, not a red check. Auto-detect runs
  on public repos; force it with the `SCORECARD_ENABLED` variable (`'true'` /
  `'false'`).

### Other periodic scans

`rhiza_weekly.yml` runs on a schedule to surface drift; it is diagnostic and is
not a PR merge gate.

## Summary

- **PR merge gates:** `fmt`, `typecheck`, `test`, `rhiza-test`, `deptry`,
  `docs-coverage`, `security`, CodeQL.
- **Report-only:** Scorecard, weekly.
