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

- Pull request required, with **1 approving review** and stale-review dismissal on new pushes.
- **No force-pushes** (`non_fast_forward`) and **no deletion** of the default branch.
- **Required status checks** must pass before merge (strict — the branch must be up to date).

The `required_status_checks` list ships **empty** on purpose: check names ("contexts") differ per project and
change as workflows evolve. Populate it for this repo once (see below) so superseded merges are blocked on red CI.

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

## Adding required status checks

Find the exact check names from a recent run on `main`, then add them under `required_status_checks`:

```bash
# List check/context names from the latest main commit
gh api repos/Jebel-Quant/rhiza/commits/main/check-runs --jq '.check_runs[].name' | sort -u
```

```jsonc
"required_status_checks": [
  { "context": "test (3.13, ubuntu-latest)" },
  { "context": "Type checking (Python 3.13)" },
  { "context": "Pre-commit hooks" }
]
```

Re-apply with the `PUT` command above.

## Notes

- The score updates on the **next** Scorecard run after the ruleset is active — trigger it via
  **Actions → "(RHIZA) SCORECARD" → Run workflow**, or wait for the weekly schedule.
- **Code-Review** also looks back at recently merged PRs, so its score climbs as new PRs land with approvals;
  historical self-merges still count against it until they age out of the window.
- Scorecard's Branch-Protection check needs a token with admin read to inspect settings. The Scorecard action
  reads this via its `repo_token`; without it the check reports an internal error rather than a real score.
