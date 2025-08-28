#!/bin/bash
set -e

echo "Starting Curriculum Curator..."

# Create all necessary directories
mkdir -p /app/backend/uploads /app/backend/logs /app/backend/data /app/backend/content_repo
mkdir -p /app/logs  # For supervisor logs

# Run database migrations if alembic.ini exists
if [ -f /app/backend/alembic.ini ]; then
    echo "Running database migrations..."
    cd /app/backend
    alembic upgrade head || echo "Migration failed, but continuing..."
else
    echo "No alembic.ini found, skipping migrations"
fi

# Start supervisor
echo "Starting services..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf