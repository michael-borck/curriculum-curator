#!/bin/bash
set -e

# Docker entrypoint script for Curriculum Curator
# This ensures data directories exist and have correct permissions

echo "Starting Curriculum Curator..."

# Ensure data directories exist with correct permissions
echo "Checking data directories..."
for dir in /app/backend/data /app/backend/uploads /app/backend/logs /app/backend/content_repo /app/backend/content_repos /app/backend/user_templates; do
    if [ ! -d "$dir" ]; then
        echo "   Creating $dir"
        mkdir -p "$dir"
    fi

    # Fix ownership to appuser (UID 1000)
    chown -R appuser:appuser "$dir"
done

echo "Data directories ready"

# Initialize database schema (tables only, no sample data)
echo "Initializing database..."
cd /app/backend
gosu appuser .venv/bin/python -c "
from app.core.database import Base, engine
from app.models import *  # register all models
Base.metadata.create_all(bind=engine)
print('Tables ready')
"
echo "Database ready"

# Drop to non-root user and execute the CMD
echo "Starting application..."
exec gosu appuser "$@"
