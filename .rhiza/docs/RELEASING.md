# Release Guide

This guide covers the release process for Rhiza-based projects.

## 🚀 The Release Process

The release process can be done in two separate steps (**Bump** then **Release**), or in a single step using **Publish**.

### Option A: One-Step Publish (Recommended)

Bump the version and release in a single flow:

```bash
make publish
```

This combines the bump and release steps below into one interactive command.

### Option B: Two-Step Process

#### 1. Bump Version

First, update the version in `pyproject.toml`:

```bash
make bump
```

This command will interactively guide you through:
1. Selecting a bump type (patch, minor, major) or entering a specific version
2. Warning you if you're not on the default branch
3. Showing the current and new version
4. Prompting whether to commit the changes
5. Prompting whether to push the changes

The script ensures safety by:
- Checking for uncommitted changes before bumping
- Validating that the tag doesn't already exist
- Verifying the version format

#### 2. Release

Once the version is bumped and committed, run the release command:

```bash
make release
```

This command will interactively guide you through:
1. Checking if your branch is up-to-date with the remote
2. If your local branch is ahead, showing the unpushed commits and prompting you to push them
3. Creating a git tag (e.g., `v1.2.4`)
4. Pushing the tag to the remote, which triggers the GitHub Actions release workflow

The script provides safety checks by:
- Warning if you're not on the default branch
- Verifying no uncommitted changes exist
- Checking if the tag already exists locally or on remote
- Showing the number of commits since the last tag

### Checking Release Status

After releasing, you can check the status of the release workflow and the latest release:

```bash
make release-status
```

This will display:
- The last 5 release workflow runs with their status and conclusion
- The latest GitHub release details (tag, author, published time, status, URL)

> **Note:** `release-status` is currently supported for GitHub repositories only. GitLab support is planned for a future release.

## What Happens After Release

The release workflow (`.github/workflows/rhiza_release.yml`) triggers on the tag push and:

1. **Validates** - Checks the tag format and ensures no duplicate releases
2. **Builds** - Builds the Python package (if `pyproject.toml` exists)
3. **Drafts** - Creates a draft GitHub release with artifacts
4. **PyPI** - Publishes to PyPI (if not marked private)
5. **CodeArtifact** - Publishes to AWS CodeArtifact (if `AWS_CODEARTIFACT_DOMAIN` is set)
6. **Devcontainer** - Publishes devcontainer image (if `PUBLISH_DEVCONTAINER=true`)
7. **Finalizes** - Publishes the GitHub release with links to PyPI, CodeArtifact, and container images

## Configuration Options

### PyPI Publishing

- Automatic if package is registered as a Trusted Publisher
- Use `PYPI_REPOSITORY_URL` and `PYPI_TOKEN` for custom feeds
- Mark as private with `Private :: Do Not Upload` in `pyproject.toml`

### AWS CodeArtifact Publishing

Publish Python packages to an AWS CodeArtifact repository. This is useful for private packages
or organisations that use CodeArtifact as their internal package registry.

> **Note:** The `Private :: Do Not Upload` classifier only affects PyPI publishing. Packages
> marked as private can still be published to CodeArtifact, which is the typical use case
> for internal packages.

#### Required Repository Variables

| Variable | Description | Example |
|---|---|---|
| `AWS_CODEARTIFACT_DOMAIN` | CodeArtifact domain name | `my-company` |
| `AWS_CODEARTIFACT_REPOSITORY` | CodeArtifact repository name | `python-packages` |
| `AWS_ROLE_ARN` | IAM role ARN for GitHub OIDC (**GitHub only**) | `arn:aws:iam::123456789012:role/github-release` |

#### Optional Repository Variables

| Variable | Default | Description |
|---|---|---|
| `AWS_REGION` | `us-east-1` | AWS region for CodeArtifact |
| `AWS_CODEARTIFACT_OWNER` | *(current account)* | Domain owner AWS account ID (for cross-account access) |

#### Setup Instructions (GitHub)

1. **Create an IAM OIDC identity provider** for GitHub Actions in your AWS account:
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`

2. **Create an IAM role** with a trust policy allowing GitHub OIDC:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" },
       "Action": "sts:AssumeRoleWithWebIdentity",
       "Condition": {
         "StringEquals": {
           "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
         },
         "StringLike": {
           "token.actions.githubusercontent.com:sub": "repo:YOUR-ORG/YOUR-REPO:*"
         }
       }
     }]
   }
   ```

3. **Attach a policy** granting CodeArtifact access:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "codeartifact:GetAuthorizationToken",
           "codeartifact:GetRepositoryEndpoint",
           "codeartifact:PublishPackageVersion",
           "codeartifact:PutPackageMetadata"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": "sts:GetServiceBearerToken",
         "Resource": "*",
         "Condition": {
           "StringEquals": { "sts:AWSServiceName": "codeartifact.amazonaws.com" }
         }
       }
     ]
   }
   ```

4. **Set repository variables** in GitHub (Settings → Secrets and variables → Actions → Variables):
   - `AWS_CODEARTIFACT_DOMAIN` = your domain name
   - `AWS_CODEARTIFACT_REPOSITORY` = your repository name
   - `AWS_ROLE_ARN` = the IAM role ARN from step 2
   - `AWS_REGION` = your AWS region (e.g., `eu-west-2`)

#### Setup Instructions (GitLab)

1. **Configure AWS credentials** as CI/CD variables:
   - `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or configure GitLab OIDC with AWS)

2. **Set CI/CD variables**:
   - `AWS_CODEARTIFACT_DOMAIN` = your domain name
   - `AWS_CODEARTIFACT_REPOSITORY` = your repository name
   - `AWS_REGION` = your AWS region
   - `AWS_CODEARTIFACT_OWNER` = domain owner account ID (if cross-account)

### Devcontainer Publishing

- Set repository variable `PUBLISH_DEVCONTAINER=true` to enable
- Override registry with `DEVCONTAINER_REGISTRY` variable (defaults to ghcr.io)
- Requires `.devcontainer/devcontainer.json` to exist
- Image published as `{registry}/{owner}/{repository}/devcontainer:vX.Y.Z`
