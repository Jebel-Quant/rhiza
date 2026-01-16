# Contributing

This document is a guide to contributing to the project.

We welcome all contributions. You don't need to be an expert
to help out.

## Checklist

Contributions are made through
[pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests).
Before sending a pull request, make sure you do the following:

- Run `make fmt` to make sure your code adheres to our [coding style](#code-style)
and all tests pass.
- [Write unit tests](#writing-unit-tests) for new functionality added.

## Building from source

You'll need to build the project locally to start editing code.
To install from source, clone the repository from GitHub, 
navigate to its root, and run the following command:

```bash
make install
```

## Contributing code

To contribute to the project, send us pull requests.
For those new to contributing, check out GitHub's
[guide](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests).

Once you've made your pull request, a member of the
development team will assign themselves to review it.
You might have a few
back-and-forths with your reviewer before it is accepted,
which is completely normal.
Your pull request will trigger continuous integration tests
for many different
Python versions and different platforms. If these tests start failing,
please
fix your code and send another commit, which will re-trigger the tests.

If you'd like to add a new feature, please propose your
change in a GitHub issue to make sure
that your priorities align with ours.

If you'd like to contribute code but don't know where to start,
try one of the
following:

- Read the source and enhance the documentation,
  or address TODOs
- Browse the open issues,
  and look for the issues tagged "help wanted".

## Code style

We use ruff to enforce our Python coding style.
Before sending us a pull request, navigate to the project 
root and run

```bash
make fmt
```

to make sure that your changes abide by our style conventions.
Please fix any errors that are reported before sending
the pull request.

## Writing unit tests

Most code changes will require new unit tests.
Even bug fixes require unit tests,
since the presence of bugs usually indicates insufficient tests.
When adding tests, try to find a file in which your tests should belong;
if you're testing a new feature, you might want to create a new test file.

We use the popular Python [pytest](https://docs.pytest.org/en/) framework for our
tests.

## Running unit tests

We use `pytest` to run our unit tests.
To run all unit tests run the following command:

```bash
make test
```

Please make sure that your change doesn't cause any
of the unit tests to fail.

## Repository Configuration

### Required Secrets

These secrets must be configured in your repository settings for full CI/CD functionality:

| Secret | Required For | Description |
|--------|--------------|-------------|
| `PAT_TOKEN` | Template sync workflow | Personal Access Token with `workflow` scope. Required when template sync modifies workflow files. |
| `PYPI_TOKEN` | Release (custom feeds only) | Token for custom PyPI feed authentication. Not needed for PyPI with OIDC trusted publishing. |

### Repository Variables

These variables control workflow behavior:

| Variable | Used By | Description |
|----------|---------|-------------|
| `PUBLISH_COMPANION_BOOK` | Book workflow | Set to `false` to disable documentation deployment. Default: deploys to GitHub Pages. |
| `PUBLISH_DEVCONTAINER` | Release workflow | Set to `true` to publish devcontainer images on release. |
| `DEVCONTAINER_REGISTRY` | Release workflow | Container registry URL. Default: `ghcr.io` |
| `DEVCONTAINER_IMAGE_NAME` | Release workflow | Custom image name component. Default: `{repo-name}/devcontainer` |
| `PYPI_REPOSITORY_URL` | Release workflow | Custom PyPI feed URL for private registries. |

### Setting Up Secrets

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each required secret with its value

### Creating a PAT_TOKEN

The `PAT_TOKEN` is needed for the sync workflow to update workflow files:

1. Go to GitHub **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens**
2. Click **Generate new token**
3. Set expiration and select the repository
4. Under **Repository permissions**, grant:
   - **Contents**: Read and write
   - **Workflows**: Read and write
5. Copy the token and add it as `PAT_TOKEN` secret

### PyPI Trusted Publishing (Recommended)

For PyPI releases, we recommend using OIDC trusted publishing instead of tokens:

1. Go to [pypi.org](https://pypi.org) → Your project → **Publishing**
2. Add a new trusted publisher with:
   - Owner: `{your-github-org}`
   - Repository: `{your-repo-name}`
   - Workflow: `rhiza_release.yml`
   - Environment: `release`

This eliminates the need for stored PyPI credentials.

### Branch Protection Rules

We recommend configuring branch protection rules for the `main` branch to ensure code quality and prevent accidental changes.

**To configure branch protection:**

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Branches**
3. Click **Add branch protection rule**
4. Set **Branch name pattern** to `main`

**Recommended settings:**

| Setting | Recommended | Description |
|---------|-------------|-------------|
| **Require a pull request before merging** | ✅ Yes | Prevents direct pushes to main |
| **Require approvals** | 1+ | Number of required review approvals |
| **Dismiss stale pull request approvals** | ✅ Yes | Re-review required after new commits |
| **Require status checks to pass** | ✅ Yes | CI must pass before merge |
| **Require branches to be up to date** | ✅ Yes | Branch must be current with main |
| **Require conversation resolution** | ✅ Yes | All review comments must be resolved |
| **Require signed commits** | Optional | Enforce GPG-signed commits |
| **Include administrators** | ✅ Yes | Rules apply to admins too |
| **Allow force pushes** | ❌ No | Prevent history rewriting |
| **Allow deletions** | ❌ No | Prevent branch deletion |

**Required status checks:**

Add these workflows as required status checks:

- `(RHIZA) CI` - Tests must pass on all Python versions
- `(RHIZA) PRE-COMMIT` - Code formatting and linting
- `(RHIZA) DEPTRY` - Dependency hygiene

**For organizations using GitHub Enterprise:**

Consider also enabling:
- **Require code owner reviews** - CODEOWNERS file determines reviewers
- **Restrict who can push** - Limit to specific teams
- **Require linear history** - Enforce squash or rebase merges
