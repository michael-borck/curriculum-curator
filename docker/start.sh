#!/bin/bash
set -e

echo "Starting Curriculum Curator..."

# Create initial directories if they don't exist
mkdir -p /app/backend/uploads /app/backend/logs /app/backend/data /app/backend/content_repo

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