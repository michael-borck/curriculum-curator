# Multi-stage Dockerfile for Curriculum Curator
# Includes Git, Quarto, and Pandoc for content management and export

# Stage 1: Frontend Build
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Runtime
FROM python:3.11-slim

# Install system dependencies including Git and other tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    gdebi-core \
    && rm -rf /var/lib/apt/lists/*

# Install Quarto (includes Pandoc)
RUN wget https://github.com/quarto-dev/quarto-cli/releases/download/v1.4.549/quarto-1.4.549-linux-amd64.deb && \
    gdebi --non-interactive quarto-1.4.549-linux-amd64.deb && \
    rm quarto-1.4.549-linux-amd64.deb

# Verify installations
RUN git --version && \
    quarto --version && \
    pandoc --version

# Set working directory
WORKDIR /app

# Copy backend requirements
COPY backend/pyproject.toml backend/README.md ./

# Install Python dependencies using pip (uv not needed in container)
RUN pip install --no-cache-dir -e .

# Copy backend code
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./

# Copy frontend build from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create directories for data persistence
RUN mkdir -p /app/data /app/content /app/exports

# Configure Git for content repository
RUN git config --global user.name "Curriculum Curator" && \
    git config --global user.email "system@curriculum-curator.local" && \
    git config --global init.defaultBranch main

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////app/data/curriculum_curator.db \
    CONTENT_REPO_PATH=/app/content \
    GIT_PATH=/usr/bin/git \
    QUARTO_PATH=/usr/local/bin/quarto \
    PANDOC_PATH=/usr/bin/pandoc

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Create entrypoint script
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Initialize Git repository if not exists
if [ ! -d "/app/content/.git" ]; then
    echo "Initializing Git repository..."
    cd /app/content
    git init
    echo "# Content Repository" > README.md
    git add README.md
    git commit -m "Initial commit"
    cd /app
fi

# Start the application
echo "Starting Curriculum Curator..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF

RUN chmod +x /app/entrypoint.sh

# Run the application
CMD ["/app/entrypoint.sh"]