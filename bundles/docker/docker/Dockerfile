# ================================
# Build Arguments
# ================================
# Python version from .python-version (single source of truth)
# MUST be passed via --build-arg PYTHON_VERSION=$(cat .python-version)
# Docker cannot read files before FROM, so the build process must pass this.
# Use: make docker-build (reads .python-version automatically)
ARG PYTHON_VERSION=3.12

# ================================
# Stage 1: Builder
# ================================
FROM ghcr.io/astral-sh/uv:0.11.16-python${PYTHON_VERSION}-trixie-slim AS builder

WORKDIR /app

# A dependency declared as a Git source in `[tool.uv.sources]` is fetched by shelling out
# to git, and the slim base image ships none -- so without this, `uv sync` fails on such a
# project with `git: command not found` before any credential is even consulted. Builder
# stage only; the runtime stage below never sees it.
RUN apt-get update && \
    apt-get install -y --no-install-recommends git=1:2.47.* && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user. The UID is numeric and explicit because a name only exists inside
# the image: hadolint's DL3066 -- reported by rhiza_docker.yml's lint step -- asks for a
# number, and Kubernetes' runAsNonRoot refuses to admit a pod whose image names a
# non-numeric user because the kubelet cannot verify it is not root.
RUN useradd -m -u 10001 app_user && chown app_user:app_user /app

# Use non-root user
USER 10001

# Copy the manifest, then the source tree if there is one. Two instructions rather than
# one, because docker copies a directory's *contents* and not the directory: with `src*`
# among several sources and `./` as the destination, `src/pkg/` landed at `/app/pkg/` and
# every src-layout build backend then failed with `Expected a Python module at
# src/pkg/__init__.py`. A trailing `./src/` puts the contents back where the manifest says
# they are, and a `src*` that matches nothing is still not an error, which is what keeps a
# project without one building.
COPY --chown=app_user:app_user pyproject.toml uv.lock README.md ./
COPY --chown=app_user:app_user src* ./src/

# Install dependencies into .venv (no dev deps).
#
# Private dependencies: `rhiza_docker.yml` passes GH_PAT and UV_EXTRA_INDEX_URL as BuildKit
# *secrets* (`--secret id=gh_pat,env=GH_PAT`), which exist only for this instruction and land
# in no layer -- a `--build-arg` would be baked into the image and readable with
# `docker history` (#1691). The mounts carry the build user's uid because BuildKit mounts a
# secret root-owned and mode 0400 by default, which `USER 10001` cannot read. Git is
# configured through its GIT_CONFIG_* environment rather than a file, so there is nothing to
# scrub afterwards. An absent secret is an empty (or missing) file: neither branch fires and
# the build behaves exactly as it did before, which is what a project with no private
# dependencies needs -- and what a fork PR gets, since forks receive no secrets.
RUN --mount=type=secret,id=gh_pat,uid=10001 \
    --mount=type=secret,id=uv_extra_index_url,uid=10001 \
    if [ -s /run/secrets/gh_pat ]; then \
      GIT_CONFIG_KEY_0="url.https://$(cat /run/secrets/gh_pat)@github.com/.insteadOf"; \
      export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0 GIT_CONFIG_VALUE_0="https://github.com/"; \
    fi && \
    if [ -s /run/secrets/uv_extra_index_url ]; then \
      UV_EXTRA_INDEX_URL="$(cat /run/secrets/uv_extra_index_url)"; \
      export UV_EXTRA_INDEX_URL; \
    fi && \
    uv sync --frozen --no-dev --no-cache && \
    # Install the package itself (non-editable, so src/ is not required afterwards) \
    uv pip install --no-deps .

# Remove source to shrink image
RUN rm -rf ./src/ ~/.cache/ && \
    rm -rf /app/.venv/CACHEDIR.TAG && \
    rm -rf /app/.venv/bin/activate* && \
    rm -rf /app/.venv/bin/deactivate.bat && \
    rm -rf /app/.venv/bin/pydoc.bat && \
    rm -rf /app/.venv/.gitignore /app/.venv/.lock && \
    find /app/.venv -path "*/site-packages/*dist-info" -type d -exec rm -rf {} + && \
    find /app/.venv -path "*/site-packages/*egg-info" -type d -exec rm -rf {} + && \
    find /app/.venv -name "_virtualenv.*" -delete && \
    find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -name "*.pyc" -delete


# ================================
# Stage 2: Runtime
# ================================
FROM python:${PYTHON_VERSION}-slim AS runtime

WORKDIR /app

# Install small system tools and update packages to fix security vulnerabilities
# Fixes CVE-2025-38248, CVE-2025-40170, CVE-2025-68800, CVE-2025-68811, CVE-2025-71085
# CVE-2025-71116, CVE-2026-22984, CVE-2026-22990, CVE-2026-23001, CVE-2026-23010
# CVE-2026-23050, CVE-2026-23054, CVE-2026-23074, CVE-2026-23084, CVE-2026-23097
RUN apt-get update && \
    apt-get install -y --no-install-recommends nano=8.* tree=2.* && \
    apt-get upgrade -y linux-libc-dev && \
    rm -rf /var/lib/apt/lists/*

# Update pip and setuptools to fix security vulnerabilities
# CVE-2025-8869 (pip: missing checks on symbolic link extraction)
# CVE-2026-1703 (pip: information disclosure via path traversal)
# CVE-2026-23949 (jaraco.context: path traversal)
# CVE-2026-24049 (wheel: privilege escalation)
# CVE-2026-6357 (pip: arbitrary code execution or information disclosure via malicious wheel)
RUN pip install --no-cache-dir --upgrade pip==26.1 && \
    pip install --no-cache-dir setuptools==82.0.0

# Create non-root user, with the same numeric UID as the builder stage so the files copied
# from it keep their owner.
RUN useradd -m -u 10001 app_user && chown app_user:app_user /app

# Copy stripped .venv and app from builder
COPY --from=builder --chown=app_user:app_user /app/.venv /app/.venv

# Set virtual environment PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root
USER 10001

# Default application start command (replace module/script as appropriate)
CMD ["python", "-m", "src"]

