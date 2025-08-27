# Single container Dockerfile for Curriculum Curator
# Runs both frontend (nginx) and backend (FastAPI) in one container

FROM python:3.11-slim

# Install Node.js, nginx, supervisor and build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    nginx \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Backend setup
COPY backend/pyproject.toml backend/uv.lock ./backend/
WORKDIR /app/backend
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy backend code
COPY backend/ .
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

# Expose port 80 for nginx
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

# Start supervisor which manages nginx and uvicorn
CMD ["/app/start.sh"]