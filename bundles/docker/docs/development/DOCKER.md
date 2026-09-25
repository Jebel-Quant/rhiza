# Docker Build Configuration

The `docker/` folder at the repository root holds the Dockerfile and related configuration
for building container images.

## Files

- `docker/Dockerfile` — Multi-stage Docker build configuration
- `docker/Dockerfile.dockerignore` — Build-context ignore rules scoped to that Dockerfile (see Notes)

The folder is not cosmetic: `rhiza-task docker-build` builds `<docker_folder>/Dockerfile`
with `docker_folder` defaulting to `docker`, and `rhiza_docker.yml` names the same path. Both
*skip* a Dockerfile they cannot find rather than failing, so a copy kept anywhere else is
linted, built and scanned by nothing — which is what #1641 was.

## Python Version

The Python version is controlled by the `.python-version` file in the repository root (single source of truth).

### Building with Make (Recommended)

The Makefile automatically reads `.python-version` and passes it to Docker:

```bash
make docker-build
```

### Building Manually

If building manually, pass the version from `.python-version`:

```bash
docker buildx build \
  --file docker/Dockerfile \
  --build-arg PYTHON_VERSION=$(cat .python-version) \
  --tag <image-name> \
  --load \
  .
```

## Building the Image

Build from the repository root, using the root directory as the build context:

```bash
# Recommended: Use make target (reads .python-version automatically)
make docker-build

# Or manually with explicit version
docker buildx build \
  --file docker/Dockerfile \
  --build-arg PYTHON_VERSION=$(cat .python-version) \
  --tag <image-name> \
  --load \
  .
```

This is the same approach used by the CI workflow (see .github/workflows/rhiza_docker.yml).

## Private dependencies

A dependency fetched from a private Git repository or a private package index needs a
credential *inside* the build, because `uv sync` runs in the builder stage and nothing the
host has configured -- a `git config --global`, a `~/.netrc` -- is visible there. The
Dockerfile therefore accepts two BuildKit secrets, `gh_pat` and `uv_extra_index_url`, and
mounts them for the single `RUN` that installs dependencies. A secret is never a
`--build-arg`: an argument is baked into the image and readable with `docker history`,
whereas a secret mount exists only while that instruction runs and lands in no layer.

`rhiza_docker.yml` passes the `GH_PAT` and `UV_EXTRA_INDEX_URL` repository secrets this way
(#1691). Locally, export the same variables and pass them as secrets:

```bash
export GH_PAT=<token>                      # a PAT with read access to the private repositories
docker buildx build \
  --file docker/Dockerfile \
  --build-arg PYTHON_VERSION=$(cat .python-version) \
  --secret id=gh_pat,env=GH_PAT \
  --secret id=uv_extra_index_url,env=UV_EXTRA_INDEX_URL \
  --tag <image-name> \
  --load \
  .
```

Both are optional. An unset variable is mounted as an empty file, the Dockerfile's guard
does not fire, and the build runs exactly as it does for a project with no private
dependencies. The builder stage also installs `git`, which a Git source needs and the slim
base image does not carry; the runtime stage is unaffected.

## Notes on Dockerfile.dockerignore

- Docker/BuildKit supports a per-Dockerfile ignore file located next to the Dockerfile, named `Dockerfile.dockerignore`.
- This file applies only when building that specific Dockerfile and allows us to keep all Docker-related files together inside the `docker/` folder.
- No repository-root `.dockerignore` or symlink is required.
- The ignore rules are evaluated relative to the build context (here: the repository root `.`). Use paths accordingly.
- You need BuildKit-enabled Docker (e.g., `docker buildx`, which is enabled by default in modern Docker versions).
