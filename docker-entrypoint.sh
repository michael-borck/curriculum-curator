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

# Show resolved DATABASE_URL for debugging (mask any credentials)
mask_url() { printf '%s' "$1" | sed -E 's#(://)[^/@]+@#\1***@#'; }
echo "DATABASE_URL=$(mask_url "${DATABASE_URL:-<not set, using config default>}")"
echo "Working directory: $(pwd)"
ls -la /app/backend/data/ 2>/dev/null || echo "   /app/backend/data/ not listable"

# Initialize database schema (tables only, no sample data)
echo "Initializing database..."
cd /app/backend
gosu appuser .venv/bin/python -c "
import re
from app.core.database import Base, engine, settings
print('Resolved DATABASE_URL: ' + re.sub(r'(://)[^/@]+@', r'\1***@', settings.DATABASE_URL))
from app.models import *  # register all models
Base.metadata.create_all(bind=engine)
print('Tables ready')
"
echo "Database ready"

# Verify the DB file exists after init
ls -la /app/backend/data/curriculum_curator.db 2>/dev/null || echo "WARNING: DB file not found at expected path!"

# Drop to non-root user and execute the CMD
echo "Starting application..."
exec gosu appuser "$@"
