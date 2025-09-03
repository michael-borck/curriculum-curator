# Simple Dockerfile that mirrors local development exactly
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

# Create a basic .env file if needed for Docker environment
RUN echo "# Auto-generated for Docker environment" > .env && \
    echo "SECRET_KEY=docker-dev-secret-key-$(date +%s | sha256sum | head -c 32)" >> .env && \
    echo "DATABASE_URL=sqlite:///./data/curriculum_curator.db" >> .env && \
    echo "ALGORITHM=HS256" >> .env && \
    echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env && \
    echo "DEBUG=true" >> .env && \
    echo "# EMAIL_WHITELIST is set as empty list in config.py default" >> .env

WORKDIR /app

# Make scripts executable
RUN chmod +x backend.sh frontend.sh

# Create a simple start script that runs both
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Export environment variables for scripts\n\
export TERM=xterm  # Set TERM for scripts that need it\n\
export HOST=0.0.0.0  # Bind to all interfaces so Docker can access\n\
export VITE_HOST=0.0.0.0  # Frontend needs to be accessible from outside\n\
export VITE_API_URL=http://localhost:8000  # Frontend talks to backend internally\n\
\n\
# Start backend in background\n\
echo "Starting backend..."\n\
cd /app && ./backend.sh &\n\
BACKEND_PID=$!\n\
\n\
# Give backend time to start\n\
echo "Waiting for backend to start..."\n\
sleep 10\n\
\n\
# Start frontend in foreground\n\
echo "Starting frontend..."\n\
cd /app && ./frontend.sh\n\
\n\
# If frontend exits, kill backend\n\
kill $BACKEND_PID 2>/dev/null || true' > /app/start-both.sh && chmod +x /app/start-both.sh

# Expose frontend port (Vite dev server)
# Backend doesn't need to be exposed since frontend proxies to it
EXPOSE 5173

# Run both scripts
CMD ["/app/start-both.sh"]