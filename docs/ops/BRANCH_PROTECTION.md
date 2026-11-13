# Branch Protection as Code

This document explains how Rhiza manages branch protection for the default branch as a version-controlled
GitHub ruleset, and how that maps to OpenSSF Scorecard.

## Why a ruleset (and not the Settings UI)

GitHub does not read branch protection from a file in the repository by default. Clicking through
**Settings → Rules** leaves no audit trail and drifts over time. Instead, the protection lives in
[`.github/rulesets/main-branch-protection.json`](../../.github/rulesets/main-branch-protection.json) and is
applied with a single `gh api` call, so changes are reviewed like any other diff.

This directly improves two Scorecard checks that cannot be fixed by workflow files alone:

- **Code-Review** — requires every change to land via a pull request with at least one approving review.
- **Branch-Protection** — blocks force-pushes and branch deletion on the default branch and requires status
  checks to pass before merge.

## What the ruleset enforces

- Pull request required, with **1 approving review**, **code-owner review** (see
  [`.github/CODEOWNERS`](../../.github/CODEOWNERS)), **last-push approval**, and stale-review dismissal on new
  pushes.
- **Required status check** — `CI gate`, the aggregate job of `rhiza_ci.yml`, must pass before merge. It needs
  every other CI job and fails when any job the CI profile planned failed, was cancelled or was unexpectedly
  skipped, so the pre-commit, deptry, docs-coverage, security, licence and test jobs all block a merge through it.
- **No force-pushes** (`non_fast_forward`) and **no deletion** of the default branch.

Repository **admins can bypass** (`bypass_actors` → `RepositoryRole` id 5, `bypass_mode: always`) so a solo
maintainer can still self-merge. This is the one remaining gap Scorecard flags (`'branch protection settings
apply to administrators' is disabled`) and the main reason **Code-Review** stays low while admins self-merge.
Drop the `bypass_actors` entry for the strictest posture (admins included), at the cost of needing a second
approver on every PR.

The required status checks are deliberately limited to **one single-instance job that runs on every PR**. Until
#1744 the file also named five per-job contexts (`Pre-commit hooks`, `Check dependencies with deptry`,
`docs-coverage`, `Security scanning`, `License compliance scan`). The `lean` [CI profile](../guides/CI_PROFILES.md)
runs those gates in one consolidated `quality` job, so those contexts never report on a lean PR and would wedge it;
`CI gate` reports under every profile and already rolls them up. The matrix jobs (`test (3.x, <os>)`,
`Type checking (Python 3.x)`) are **not** hard-required either: their context names change whenever the Python/OS
matrix or the profile changes. The optional workflows (CodeQL, book, docker, paper, marimo, devcontainer) are
excluded because they only run on relevant changes, and CodeQL and marimo skip on pull requests under the `lean`
and `standard` profiles.

**Migrating.** Editing the JSON changes nothing on GitHub. A repository whose live ruleset still lists the five
per-job contexts keeps requiring them until it is re-applied with the `PUT` command below. That is harmless under
`standard` and `comprehensive`, where those jobs still run, but blocks every PR under `lean`. Downstream projects
receive the file as `bundles/github/.github/rulesets/main-branch-protection.json`, whose context is `ci / CI gate`
because the `github-tests` stub's `ci` job prefixes every check it calls; they apply it to their own repository the
same way.

## Apply it

Requires admin on the repository and a token with the `repo`/`administration` scope (`gh auth login` is enough
for a maintainer).

```bash
# Create the ruleset (first time)
gh api --method POST repos/Jebel-Quant/rhiza/rulesets \
  --input .github/rulesets/main-branch-protection.json

# List rulesets to find the id
gh api repos/Jebel-Quant/rhiza/rulesets --jq '.[] | "\(.id)\t\(.name)"'

# Update an existing ruleset after editing the JSON
gh api --method PUT repos/Jebel-Quant/rhiza/rulesets/<RULESET_ID> \
  --input .github/rulesets/main-branch-protection.json
```

## Tuning required status checks

The ruleset already requires the always-on aggregate gate (see above). To adjust the list, edit the
`required_status_checks` rule and re-apply with the `PUT` command above. List context names from a recent PR
head (PRs exercise the full matrix, unlike `main`):

```bash
gh api repos/Jebel-Quant/rhiza/commits/<PR_HEAD_SHA>/check-runs --jq '.check_runs[].name' | sort -u
```

Prefer **stable single-instance contexts**. Avoid matrix contexts such as `test (3.13, ubuntu-latest)` or
`Type checking (Python 3.13)`: their names change with the matrix and would wedge PRs until the ruleset is
edited. The list must be non-empty — the API returns `422` for `"required_status_checks": []`.

## Notes

- The score updates on the **next** Scorecard run after the ruleset is active — trigger it via
  **Actions → "(RHIZA) SCORECARD" → Run workflow**, or wait for the weekly schedule.
- **Code-Review** also looks back at recently merged PRs, so its score climbs as new PRs land with approvals;
  historical self-merges still count against it until they age out of the window.
- Scorecard's Branch-Protection check needs a token with admin read to inspect settings. The Scorecard action
  reads this via its `repo_token`; without it the check reports an internal error rather than a real score.
