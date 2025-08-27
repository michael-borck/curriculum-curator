#!/bin/bash
set -e

echo "Starting Curriculum Curator..."

# Run database migrations
echo "Running database migrations..."
cd /app/backend
alembic upgrade head

# Create initial directories if they don't exist
mkdir -p /app/backend/uploads /app/backend/logs /app/backend/data /app/backend/content_repo

# Start supervisor
echo "Starting services..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf