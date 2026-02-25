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

# Initialize database (creates tables if they don't exist, idempotent)
echo "Initializing database..."
cd /app/backend
gosu appuser .venv/bin/python init_db.py
echo "Database ready"

# Drop to non-root user and execute the CMD
echo "Starting application..."
exec gosu appuser "$@"
