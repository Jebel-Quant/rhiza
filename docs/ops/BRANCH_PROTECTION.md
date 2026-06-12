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

Repository **admins can bypass** (`bypass_actors` → `RepositoryRole` id 5, `bypass_mode: always`) so a solo
maintainer can still self-merge. Drop the `bypass_actors` entry for the strictest posture (admins included), at
the cost of needing a second approver on every PR.

There is intentionally **no `required_status_checks` rule**: the GitHub API rejects an empty check list, and a
single config can't safely hard-require checks across projects — conditional workflows (book, docker, paper,
marimo, devcontainer) only run on relevant changes, so requiring them would wedge unrelated PRs that never
trigger them. Add the checks that run on *every* PR for your repo (see below) when you want red CI to block merges.

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

Pick checks that run on **every** PR (not the conditional overlay workflows), then add a
`required_status_checks` rule to the `rules` array and re-apply with the `PUT` command above:

```bash
# List context names from a recent PR head (PRs exercise the full matrix, unlike main)
gh api repos/Jebel-Quant/rhiza/commits/<PR_HEAD_SHA>/check-runs --jq '.check_runs[].name' | sort -u
```

```jsonc
{
  "type": "required_status_checks",
  "parameters": {
    "strict_required_status_checks_policy": true,
    "do_not_enforce_on_create": false,
    "required_status_checks": [
      { "context": "test (3.13, ubuntu-latest)" },
      { "context": "Type checking (Python 3.13)" },
      { "context": "Pre-commit hooks" }
    ]
  }
}
```

The list must be non-empty — the API returns `422` for `"required_status_checks": []`.

## Notes

- The score updates on the **next** Scorecard run after the ruleset is active — trigger it via
  **Actions → "(RHIZA) SCORECARD" → Run workflow**, or wait for the weekly schedule.
- **Code-Review** also looks back at recently merged PRs, so its score climbs as new PRs land with approvals;
  historical self-merges still count against it until they age out of the window.
- Scorecard's Branch-Protection check needs a token with admin read to inspect settings. The Scorecard action
  reads this via its `repo_token`; without it the check reports an internal error rather than a real score.
