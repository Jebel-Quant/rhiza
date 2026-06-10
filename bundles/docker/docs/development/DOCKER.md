# Docker Build Configuration

This directory contains the Dockerfile and related configuration for building container images.

## Files

- Dockerfile — Multi-stage Docker build configuration
- Dockerfile.dockerignore — Build-context ignore rules scoped to this Dockerfile (see Notes)

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

## Notes on Dockerfile.dockerignore

- Docker/BuildKit supports a per-Dockerfile ignore file located next to the Dockerfile, named `Dockerfile.dockerignore`.
- This file applies only when building that specific Dockerfile and allows us to keep all Docker-related files together inside the `docker/` folder.
- No repository-root `.dockerignore` or symlink is required.
- The ignore rules are evaluated relative to the build context (here: the repository root `.`). Use paths accordingly.
- You need BuildKit-enabled Docker (e.g., `docker buildx`, which is enabled by default in modern Docker versions).
