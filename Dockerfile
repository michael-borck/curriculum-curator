# Single container Dockerfile for Curriculum Curator
# Runs both frontend (nginx) and backend (FastAPI) in one container
# Includes Quarto, R, and Git for advanced content creation

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gcc \
    g++ \
    git \
    nginx \
    supervisor \
    # R dependencies
    r-base \
    r-base-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Quarto (includes Pandoc)
RUN wget https://github.com/quarto-dev/quarto-cli/releases/download/v1.5.57/quarto-1.5.57-linux-amd64.deb && \
    dpkg -i quarto-*.deb && \
    rm quarto-*.deb

# Install R packages for Quarto
RUN R -e "install.packages(c('rmarkdown', 'knitr', 'tidyverse', 'plotly', 'DT'), repos='https://cran.rstudio.com/')"

# Install TinyTeX for better LaTeX support (optional, lighter than full texlive)
RUN quarto install tinytex --no-prompt

# Install uv and Python dependencies in one step to ensure uv is available
WORKDIR /app

# Backend setup
COPY backend/pyproject.toml ./backend/
WORKDIR /app/backend

# Install uv and use it immediately in the same RUN command
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:${PATH}" && \
    uv lock && \
    uv pip install --system --no-cache -r pyproject.toml

# Install Python packages for Quarto computational documents
RUN pip install --no-cache-dir \
    jupyter \
    matplotlib \
    pandas \
    plotly \
    seaborn \
    numpy

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

# Set environment variables for Quarto and tools
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