# ================================
# Stage 1: Builder
# ================================
FROM ghcr.io/astral-sh/uv:0.9.18-python3.14-trixie-slim AS builder

WORKDIR /app

# Create non-root user
RUN useradd -m app_user && chown app_user:app_user /app

# Copy dependency files (for caching)
COPY pyproject.toml uv.lock README.md ./

# Use non-root user
USER app_user

# Install dependencies into .venv (no dev deps)
RUN uv sync --frozen --no-dev --no-cache

# Copy application code
COPY --chown=app_user:app_user src ./src

# Install the package itself (non-editable, so src/ is not required afterwards)
RUN uv pip install --no-deps .

# Remove source to shrink image
RUN rm -rf ./src/ ~/.cache/ && \
    rm -rf /app/.venv/CACHEDIR.TAG && \
    rm -rf /app/.venv/bin/activate* && \
    rm -rf /app/.venv/bin/deactivate.bat && \
    rm -rf /app/.venv/bin/pydoc.bat && \
    rm -rf /app/.venv/.gitignore /app/.venv/.lock && \
    find /app/.venv -path "*/site-packages/*dist-info" -type d -exec rm -rf {} + && \
    find /app/.venv -path "*/site-packages/*egg-info" -type d -exec rm -rf {} + && \
    rm -f /app/.venv/lib/python3.12/site-packages/_virtualenv.* && \
    find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -name "*.pyc" -delete


# ================================
# Stage 2: Runtime
# ================================
FROM python:3.14-slim AS runtime

WORKDIR /app

# Install small system tools (pin versions and avoid recommends for smaller image)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nano=8.* tree=2.* && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m app_user && chown app_user:app_user /app

# Copy stripped .venv and app from builder
COPY --from=builder --chown=app_user:app_user /app/.venv /app/.venv

# Set virtual environment PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root
USER app_user

