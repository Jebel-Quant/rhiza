# CI profiles

Rhiza's GitHub CI supports three presets for choosing how often compatibility
checks and optional workflows run. This can help private projects manage Actions
usage while retaining supported Python versions, coverage thresholds and quality
checks.

The presets govern `rhiza_ci.yml` and the pull-request runs of the optional
CodeQL and marimo workflows. Every other workflow keeps its own triggers and
switches; the [per-workflow table](#what-runs-where) lists them all.

## Select a profile

Add this consumer-owned setting to `pyproject.toml`:

```toml
[tool.rhiza.ci]
profile = "lean"
```

Supported values are `lean`, `standard` and `comprehensive`. Omitting the setting
selects `comprehensive`, preserving the existing set of CI checks. Unknown profiles
or unknown keys in this table fail CI planning — and the profile gate of each
optional workflow — rather than silently reducing checks.

This setting is separate from the bundle `profiles` in `.rhiza/template.yml`:
those choose which files Rhiza supplies; this preset controls when the GitHub
workflows run. Consumers keep the template-owned workflow stubs and receive
workflow updates normally.

## Validation scope

| Profile | PRs and default-branch pushes | Scheduled compatibility validation |
| --- | --- | --- |
| Lean | Tests and coverage on the primary Python version, on Ubuntu; consolidated quality checks | Tests across supported Python versions and configured operating systems; lowest-direct dependencies |
| Standard | Tests and typing across supported Python versions; separate quality jobs | Full matrix and lowest-direct dependencies |
| Comprehensive (default) | Full test and typing matrices, lowest-direct dependencies, separate quality jobs | Full matrix and lowest-direct dependencies |

Every profile runs formatting and lint hooks, dependency hygiene, type checking,
repository checks, docstring coverage, security scanning and license compliance.
Lean invokes the same pinned task gates in one job. A failure stops that job and
fails the aggregate check. Standard and Comprehensive retain the existing separate
jobs and their artifacts. Lean does not generate the separate `LICENSES.md` artifact.

The primary Python version comes from `.python-version`, with patch versions
normalised to major/minor for the matrix. If the file is absent, CI uses the first
version returned by the package classifier metadata. The primary version must
appear in the supported Python classifiers. The full matrix still comes from
those classifiers and the existing Rhiza OS configuration. Lean uses Ubuntu for
routine checks and restores the configured OS matrix on scheduled or full manual
runs. The configured primary Python version supplies the coverage upload and
clean-working-tree check on Ubuntu.

The CI compatibility schedule runs on Monday at 07:17 UTC. The existing weekly
workflow separately checks latest compatible dependencies at 08:00 UTC. Consumers
need the `github` bundle's weekly workflow as well as `github-tests` to receive
both; selecting Lean alone does not install missing bundles. Scheduled runs use
the default branch and report results separately from PR checks.

## What runs where

A workflow only runs if its bundle is synced. The table shows, for each workflow
the GitHub bundles ship, what each profile runs on a pull request and what runs
regardless of profile.

| Workflow (bundle) | PR: Lean | PR: Standard | PR: Comprehensive | Default-branch push, schedule, manual | Other switches |
| --- | --- | --- | --- | --- | --- |
| `rhiza_ci.yml` (`github-tests`) | Primary Python on Ubuntu, one `quality` job | Full matrix, separate quality jobs | Full matrix, lowest-direct dependencies, separate quality jobs | Push follows the profile; Monday 07:17 UTC schedule and **full-validation** dispatch run everything | `RHIZA_SETUP_ENABLED` |
| `rhiza_codeql.yml` (`github-tests`) | Skipped | Skipped | Runs | Push to `main`/`master`, Monday 01:27 UTC schedule, manual dispatch | `CODEQL_ENABLED` (`false` disables; `true` forces it on a private repo; unset runs on public repos only) |
| `rhiza_benchmark.yml` (`github-tests`) | Never runs on PRs | Never runs on PRs | Never runs on PRs | Push to `main`, manual dispatch | `RHIZA_SETUP_ENABLED` |
| `rhiza_marimo.yml` (`github-marimo`) | Skipped | Skipped | Runs | Push to `main`/`master`, manual dispatch | Notebook folder (`marimo-folder` setting); an empty folder runs nothing |
| `rhiza_book.yml` (`github-book`) | Never runs on PRs | Never runs on PRs | Never runs on PRs | Builds on every branch push; deploys to Pages only from the default branch and never from a fork | `deploy-pages` input; `RHIZA_SETUP_ENABLED` |
| `rhiza_docker.yml` (`github-docker`) | Runs | Runs | Runs | Push to `main`/`master` | Bundle selection |
| `rhiza_devcontainer.yml` (`github-devcontainer`) | Runs on `.devcontainer/` changes | Same | Same | Push touching `.devcontainer/` | `DEVCONTAINER_REGISTRY`, `DEVCONTAINER_IMAGE_NAME` |
| `rhiza_paper.yml` (`github-paper`) | Runs on `docs/paper/` changes | Same | Same | Push to `main`/`master` touching `docs/paper/` | Bundle selection |
| `rhiza_quality_review.yml` (`github-quality-review`) | Runs | Runs | Runs | — | `CLAUDE_QUALITY_REVIEW_ENABLED` |
| `rhiza_weekly.yml` (`github`) | Never runs on PRs | Never runs on PRs | Never runs on PRs | Monday 08:00 UTC schedule, manual dispatch | `RHIZA_SETUP_ENABLED` |
| `rhiza_scorecard.yml` (`github`) | Never runs on PRs | Never runs on PRs | Never runs on PRs | Push to `main`/`master`, Tuesday schedule, ruleset changes, manual dispatch | `SCORECARD_ENABLED` |
| `rhiza_release.yml` (`github`) | Never runs on PRs | Never runs on PRs | Never runs on PRs | Version tags only | `PUBLISH_CONDA`, `PUBLISH_DEVCONTAINER`, `RELEASE_PUBLISHER`, `PYPI_REPOSITORY_URL` |

"Skipped" means the workflow still starts: a small **CI profile** job reads
`[tool.rhiza.ci].profile`, because GitHub's `on:` triggers cannot read
`pyproject.toml`, and the expensive jobs that need it are skipped. A skipped job
reports as skipped, not failed, and none of these jobs is a required status
check. The profile job itself fails on an invalid profile, exactly as the CI
planner does. Under CodeQL it carries the `CODEQL_ENABLED` condition too, so a
repository with CodeQL switched off starts no runner at all.

Two consequences of skipping CodeQL on PRs are worth knowing before choosing Lean
or Standard. Code-scanning alerts for a change appear only after it reaches the
default branch, not on the pull request. And a repository that adds GitHub's
*code scanning* merge-protection rule to its own ruleset would wait on results a
skipped PR never produces; the shipped ruleset does not include that rule.

Mutation testing is not offered in any profile; the workflow and the task were
removed (see the CI enforcement page).

## Triggers and documentation changes

CI runs for pull requests targeting any branch and for pushes to the repository's
actual default branch. Other branch pushes skip CI, avoiding a second full run for
the same change when a PR is open. A branch without a PR receives no automatic
application validation; use manual dispatch when needed.

For PRs and default-branch pushes, CI examines the complete Git diff. Changes
limited to top-level Markdown files or recognised documentation files under
`docs/` skip the application test matrix, separate typing matrix and dependency
floor tests. The quality checks still run, including README and repository
validation; Lean's consolidated job also retains primary-version typing. This does
not build or publish a documentation site.

The recognised documentation extensions are `.md`, `.rst`, `.txt`, `.png`, `.jpg`,
`.jpeg`, `.gif`, `.svg` and `.webp`. Code, workflow, dependency and documentation
configuration changes trigger application validation. Missing history, an empty
diff or an unknown file type also retains application validation. Scheduled and
full manual runs always run application tests regardless of the diff.

## Full validation on demand

Use **Actions → (RHIZA) CI → Run workflow** and enable **full-validation** to run
the complete test matrix and lowest-direct dependency tests for any profile.
Leaving it disabled uses the chosen profile. This expands compatibility testing;
it does not start the optional workflows. Run **(RHIZA) CODEQL**, **(RHIZA)
MARIMO** or **(RHIZA) BENCHMARK** the same way to exercise one on demand: a
manual run is not a pull request, so the profile never skips it.

## Branch protection and migration

`CI gate` is the aggregate check across profiles. In a consumer using the shipped
`ci` caller job, GitHub displays it as `ci / CI gate`. The `github` bundle's
`rulesets/main-branch-protection.json` requires exactly that context and nothing
else.

Earlier releases required six contexts: `ci / CI gate` plus `ci / Pre-commit hooks`,
`ci / Check dependencies with deptry`, `ci / docs-coverage`, `ci / Security scanning`
and `ci / License compliance scan`. Lean runs those five gates inside one `quality`
job, so their contexts never report and a Lean PR waits on them forever. The
aggregate loses nothing by standing alone: it needs every CI job, and it fails when
any job the planner selected failed, was cancelled or was unexpectedly skipped.

**The synced file is not the live setting.** GitHub does not read rulesets from the
repository, so syncing the new file changes no protection. A repository that applied
the old file keeps requiring all six contexts until it re-applies the new one, for
example:

```bash
gh api repos/<owner>/<repo>/rulesets --jq '.[] | "\(.id)\t\(.name)"'
gh api --method PUT repos/<owner>/<repo>/rulesets/<RULESET_ID> \
  --input .github/rulesets/main-branch-protection.json
```

Under Standard or Comprehensive the old contexts still report, so the stale ruleset
is redundant but harmless; under Lean it blocks every PR. Re-apply before switching
to Lean.

The gate requires every job selected by the planner to finish successfully.
Intentional profile or documentation skips are allowed; failed, cancelled or
unexpectedly skipped required jobs fail the gate. A failed planner also fails the
gate, so an invalid configuration cannot produce a successful empty test run.

## Scope and usage implications

Fewer matrix jobs, shared runner setup and skipped optional workflows on PRs
should reduce routine Actions usage for Lean and Standard projects, but actual
usage depends on suite duration, caching, operating systems and the other installed
workflows. The presets make no fixed cost or savings guarantee. A weekly full
matrix may still consume substantial minutes, and the book still builds on every
branch push.

The profiles do not change documentation publishing, benchmarks, release
automation or GitLab pipelines. Those keep the bundle selection and repository
variables listed in the table above; leaving a bundle out of `.rhiza/template.yml`
remains the way to stop a workflow running at all.
