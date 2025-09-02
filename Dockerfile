# Single container Dockerfile for Curriculum Curator
# Runs both frontend (nginx) and backend (FastAPI) in one container
# Uses rocker/verse for R + Quarto + LaTeX + Git pre-installed

FROM rocker/verse:4.3

# Switch to root for system installations
USER root

# Install system packages and remove conflicting Node.js packages
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    nginx \
    supervisor \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get remove -y libnode-dev nodejs npm \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install Python packages for Jupyter + ML (for lecturers who want Python)
# Note: rocker/verse already has R + tidyverse + Quarto + TinyTeX + Git + Pandoc
RUN pip install --no-cache-dir \
    jupyter \
    matplotlib \
    pandas \
    plotly \
    seaborn \
    numpy

# Setup application directory
WORKDIR /app

# Backend setup - Install Python dependencies
COPY backend/pyproject.toml ./backend/
WORKDIR /app/backend

# Use uv for fast Python dependency installation
RUN uv lock && \
    uv pip install --system --no-cache -r pyproject.toml

# Copy backend code
COPY backend/ .
# Ensure alembic.ini is in the right place
RUN if [ -f alembic.ini ]; then echo "alembic.ini found"; else echo "Warning: alembic.ini not found"; fi
RUN mkdir -p uploads logs data content_repo

# Frontend setup
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend code and build
COPY frontend/ .
RUN npm run build

# Setup nginx configuration
RUN rm -f /etc/nginx/sites-enabled/default
COPY docker/nginx.conf /etc/nginx/sites-enabled/curriculum-curator

# Setup supervisor to manage both processes
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create startup script
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

WORKDIR /app

# Environment variables - rocker/verse already has most of these configured
ENV QUARTO_PATH=/usr/local/bin/quarto
ENV PANDOC_PATH=/usr/bin/pandoc
ENV GIT_PATH=/usr/bin/git
ENV R_HOME=/usr/lib/R

# Expose port 80 for nginx
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

# Start supervisor which manages nginx and uvicorn
CMD ["/app/start.sh"]