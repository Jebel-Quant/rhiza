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
4. **PyPI** - Publishes to PyPI or custom feed such as CodeArtifact (if not marked private)
5. **Devcontainer** - Publishes devcontainer image (if `PUBLISH_DEVCONTAINER=true`)
6. **Finalizes** - Publishes the GitHub release with links to PyPI and container images

## Configuration Options

### PyPI Publishing

- Automatic if package is registered as a Trusted Publisher
- Use `PYPI_REPOSITORY_URL` and `PYPI_TOKEN` for custom feeds
- Mark as private with `Private :: Do Not Upload` in `pyproject.toml`

### AWS CodeArtifact Publishing

Publish Python packages to an AWS CodeArtifact repository. This is useful for private packages
or organisations that use CodeArtifact as their internal package registry.

CodeArtifact publishing is handled through the same `pypi` job by setting `PYPI_REPOSITORY_URL`
to the CodeArtifact endpoint and providing AWS credentials. The workflow automatically detects
CodeArtifact URLs and handles token exchange.

> **Note:** The `Private :: Do Not Upload` classifier only blocks publishing to the default
> PyPI. When `PYPI_REPOSITORY_URL` is set (e.g. to a CodeArtifact endpoint), private packages
> will still be published.

#### Setup Instructions

1. **Get your CodeArtifact repository endpoint** (the `PYPI_REPOSITORY_URL`):
   ```bash
   aws codeartifact get-repository-endpoint \
     --domain my-domain \
     --repository my-repo \
     --format pypi \
     --query repositoryEndpoint --output text
   ```
   This returns a URL like:
   `https://my-domain-123456789012.d.codeartifact.us-east-1.amazonaws.com/pypi/my-repo/`

2. **Create an IAM user** (or use an existing one) with the following permissions:
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

3. **Set repository secrets and variables:**

   **GitHub** (Settings → Secrets and variables → Actions):
   | Type | Name | Value |
   |---|---|---|
   | Secret | `AWS_ACCESS_KEY_ID` | IAM user access key |
   | Secret | `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
   | Variable | `PYPI_REPOSITORY_URL` | CodeArtifact endpoint URL from step 1 |

   **GitLab** (Settings → CI/CD → Variables):
   | Name | Value | Protected | Masked |
   |---|---|---|---|
   | `AWS_ACCESS_KEY_ID` | IAM user access key | ✅ | ✅ |
   | `AWS_SECRET_ACCESS_KEY` | IAM user secret key | ✅ | ✅ |
   | `PYPI_REPOSITORY_URL` | CodeArtifact endpoint URL from step 1 | ✅ | ❌ |

That's it — no additional configuration needed. The release workflow automatically:
- Detects the CodeArtifact URL from `PYPI_REPOSITORY_URL`
- Uses `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to obtain a temporary auth token
- Publishes the package with `twine`

### Devcontainer Publishing

- Set repository variable `PUBLISH_DEVCONTAINER=true` to enable
- Override registry with `DEVCONTAINER_REGISTRY` variable (defaults to ghcr.io)
- Requires `.devcontainer/devcontainer.json` to exist
- Image published as `{registry}/{owner}/{repository}/devcontainer:vX.Y.Z`
