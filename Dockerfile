# One Dockerfile for everything - build frontend, serve with backend.
# Base images are pinned by digest so a rebuilt image uses the same bases.

# ---------- Frontend build ----------
FROM node:20-slim@sha256:2cf067cfed83d5ea958367df9f966191a942351a2df77d6f0193e162b5febfc0 AS frontend

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- Runtime ----------
FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90

# OCI labels for GHCR metadata
LABEL org.opencontainers.image.source="https://github.com/michael-borck/curriculum-curator"
LABEL org.opencontainers.image.description="Curriculum Curator - AI-powered curriculum design tool"
LABEL org.opencontainers.image.licenses="MIT"

# Install system deps and document export tools (Pandoc + Typst)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    lsof \
    procps \
    gosu \
    pandoc \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Typst (static binary — no LaTeX needed for PDF export, see ADR-033).
# The tarball is checksum-verified before extraction.
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        TYPST_ARCH="x86_64-unknown-linux-musl"; \
        TYPST_SHA="605130a770ebd59a4a579673079cb913a13e75985231657a71d6239a57539ec3"; \
    elif [ "$ARCH" = "arm64" ]; then \
        TYPST_ARCH="aarch64-unknown-linux-musl"; \
        TYPST_SHA="e81ae98e6b12db5a36c2276e5a9890da48f7a339b92476dd22daf90de3699e11"; \
    else echo "Unsupported arch: $ARCH" && exit 1; fi && \
    TYPST_VERSION="0.12.0" && \
    curl -fsSL "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-${TYPST_ARCH}.tar.xz" \
        -o /tmp/typst.tar.xz && \
    echo "${TYPST_SHA}  /tmp/typst.tar.xz" | sha256sum -c - && \
    tar -xJ --strip-components=1 -C /usr/local/bin -f /tmp/typst.tar.xz "typst-${TYPST_ARCH}/typst" && \
    rm -f /tmp/typst.tar.xz

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

# Install uv for faster Python package management as root
RUN pip install --no-cache-dir uv
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy backend sources and install the exact locked dependency set
COPY backend/ ./backend/
WORKDIR /app/backend
RUN uv sync --frozen --no-dev

# Create a basic .env file ONLY if one doesn't exist. SECRET_KEY is supplied
# at runtime; without it the app fails to start.
RUN if [ ! -f .env ]; then \
    echo "# Auto-generated for Docker environment" > .env && \
    echo "DATABASE_URL=sqlite:////app/backend/data/curriculum_curator.db" >> .env && \
    echo "ALGORITHM=HS256" >> .env && \
    echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env && \
    echo "DEBUG=false" >> .env && \
    echo "# EMAIL_WHITELIST is set as empty list in config.py default" >> .env; \
    else \
    echo "Using existing .env file with SMTP settings"; \
    fi

# Copy the built frontend from the builder stage
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Copy and setup entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Change ownership of app directory to non-root user
RUN chown -R appuser:appuser /app

# NOTE: We don't switch to appuser here - the entrypoint script will do it
# This allows the entrypoint to fix permissions first (needs root)

# Disable Python bytecode caching to ensure changes are picked up
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose backend port ONLY (it serves everything)
EXPOSE 8000

# Use entrypoint script to fix permissions then drop to appuser
ENTRYPOINT ["docker-entrypoint.sh"]

# Run backend (no --reload in production; use volume mounts + restart for dev)
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
