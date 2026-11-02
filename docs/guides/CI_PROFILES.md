# CI profiles (prototype)

Rhiza's GitHub CI supports three presets for choosing how often compatibility
checks run. This can help private projects manage Actions usage while retaining
supported Python versions, coverage thresholds and quality checks.

The presets currently apply to `rhiza_ci.yml`. Other workflows retain their
existing triggers and bundle selection.

## Select a profile

Add this consumer-owned setting to `pyproject.toml`:

```toml
[tool.rhiza.ci]
profile = "lean"
```

Supported values are `lean`, `standard` and `comprehensive`. Omitting the setting
selects `comprehensive`, preserving the existing set of CI checks. Unknown profiles
or unknown keys in this table fail CI planning rather than silently reducing checks.

This setting is separate from the bundle `profiles` in `.rhiza/template.yml`:
those choose which files Rhiza supplies; this preset controls execution of the
GitHub CI workflow. Consumers keep the template-owned workflow stub and receive
workflow updates normally.

This is an unreleased prototype. To try it in a consumer before release, the
`github-tests` stub must call the reusable workflow at this prototype's commit
instead of its existing release tag. The new `full-validation` input is not
available in that older release. A normal release will update the template pin.

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
it does not activate optional workflows.

## Branch protection and migration

`CI gate` is the aggregate check across profiles. In a consumer using the shipped
`ci` caller job, GitHub displays it as `ci / CI gate`. Require that context for
branch protection rather than individual matrix legs or the Lean quality job.
The existing branch-protection files are unchanged by this prototype; review
repository settings when switching profiles.

The gate requires every job selected by the planner to finish successfully.
Intentional profile or documentation skips are allowed; failed, cancelled or
unexpectedly skipped required jobs fail the gate. A failed planner also fails the
gate, so an invalid configuration cannot produce a successful empty test run.

## Scope and usage implications

Fewer matrix jobs and shared runner setup should reduce routine Actions usage for
Lean projects, but actual usage depends on suite duration, caching, operating
systems and the other installed workflows. The presets make no fixed cost or
savings guarantee. A weekly full matrix may still consume substantial minutes.

This prototype does not change CodeQL, documentation publishing, notebooks,
benchmarks, release automation or GitLab pipelines. Those retain their existing
bundle and workflow controls. Making optional capabilities consistently opt-in
across presets remains follow-up work for issue [#1744](https://github.com/Jebel-Quant/rhiza/issues/1744).
