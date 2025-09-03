# One Dockerfile for everything - build frontend, serve with backend
FROM python:3.11-slim

# Install Node.js 20, curl, and other dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    lsof \
    procps \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
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
RUN npm install && npm run build

WORKDIR /app/backend

# Expose backend port ONLY (it serves everything)
EXPOSE 8000

# Run backend which serves both API and built frontend
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]