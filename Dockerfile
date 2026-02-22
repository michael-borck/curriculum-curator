# One Dockerfile for everything - build frontend, serve with backend
FROM python:3.11-slim

# Install Node.js 20, system deps, and document export tools (Pandoc + Typst)
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    git \
    lsof \
    procps \
    gosu \
    pandoc \
    xz-utils \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Typst (static binary — no LaTeX needed for PDF export, see ADR-033)
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then TYPST_ARCH="x86_64-unknown-linux-musl"; \
    elif [ "$ARCH" = "arm64" ]; then TYPST_ARCH="aarch64-unknown-linux-musl"; \
    else echo "Unsupported arch: $ARCH" && exit 1; fi && \
    TYPST_VERSION="0.12.0" && \
    curl -fsSL "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-${TYPST_ARCH}.tar.xz" \
    | tar -xJ --strip-components=1 -C /usr/local/bin "typst-${TYPST_ARCH}/typst"

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser

# Install uv for faster Python package management as root
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy everything
COPY . .

# Pre-install Python dependencies so they're available
WORKDIR /app/backend
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e ".[dev]"

# Create a basic .env file ONLY if one doesn't exist
RUN if [ ! -f .env ]; then \
    echo "# Auto-generated for Docker environment" > .env && \
    echo "SECRET_KEY=docker-dev-secret-key-$(date +%s | sha256sum | head -c 32)" >> .env && \
    echo "DATABASE_URL=sqlite:///./data/curriculum_curator.db" >> .env && \
    echo "ALGORITHM=HS256" >> .env && \
    echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env && \
    echo "DEBUG=true" >> .env && \
    echo "# EMAIL_WHITELIST is set as empty list in config.py default" >> .env; \
    else \
    echo "Using existing .env file with SMTP settings"; \
    fi

WORKDIR /app

# Build the frontend
WORKDIR /app/frontend
# Workaround for npm bug with optional dependencies (https://github.com/npm/cli/issues/4828)
# Also clear Vite cache to ensure fresh build
RUN rm -rf node_modules package-lock.json dist .vite && \
    npm install --force && \
    npm run build

WORKDIR /app/backend

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

# Run backend with reload to pick up changes
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]