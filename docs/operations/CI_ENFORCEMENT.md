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
| Type checking | `make typecheck` | `ty` + `mypy --strict` over `.rhiza/utils`. |
| Tests | `make test`, `make rhiza-test` | Full suites; rhiza-test enforces 90% coverage on `.rhiza/utils`. |
| Dependency hygiene | `make deptry` | Unused/missing dependency scan. |
| Docstring coverage | `make docs-coverage` | interrogate at 100%. |
| Security | `make security` | pip-audit + bandit. |
| CodeQL | `rhiza_codeql.yml` | Code scanning on PR and push. |

## Conditional / opt-in gates

### Mutation testing (`rhiza_mutation.yml`)

- **Enforcing when enabled.** `make mutation` exits non-zero on any surviving
  mutant, and the workflow's *Enforce mutation gate* step propagates that failure,
  so it is a hard gate equivalent to a 100% mutation-score threshold.
- **Opt-in, OFF by default.** The `mutation` job only runs when the repository
  variable `MUTATION_ENABLED` is set to `'true'`; otherwise it skips cleanly and
  CI stays green. This keeps downstream repos from being forced into mutation
  testing.
- **Status in this repo:** `MUTATION_ENABLED` is currently unset, so mutation
  runs are skipped on `jebel-quant/rhiza` PRs. To turn it into an active gate
  here, set the variable:

  ```bash
  gh variable set MUTATION_ENABLED --body true --repo Jebel-Quant/rhiza
  ```

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

`rhiza_weekly.yml` and `rhiza_fuzzing.yml` run on a schedule to surface drift and
robustness issues; they are diagnostic and are not PR merge gates.

## Summary

- **PR merge gates:** `fmt`, `typecheck`, `test`, `rhiza-test`, `deptry`,
  `docs-coverage`, `security`, CodeQL — plus mutation **iff** `MUTATION_ENABLED=true`.
- **Report-only:** Scorecard, weekly, fuzzing.
