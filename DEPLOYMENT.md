# Deployment Instructions

This guide will help you deploy Curriculum Curator using Docker on your VPS with Caddy reverse proxy.

## Prerequisites

- VPS with Docker and Docker Compose installed
- Caddy installed on your VPS (for reverse proxy)
- Domain name pointing to your VPS (optional but recommended)

## Quick Start

### 1. Clone the repository on your VPS

```bash
git clone https://github.com/yourusername/curriculum-curator.git
cd curriculum-curator
```

### 2. Configure environment variables

```bash
cp .env.example .env
nano .env
```

Update at minimum:
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `FRONTEND_URL` - Your domain (e.g., `https://curriculum.yourdomain.com`)
- LLM API keys (optional - users can configure their own in the app)

### 3. Build and start the container

```bash
# Build the Docker image
docker-compose build

# Start the container in detached mode
docker-compose up -d

# Check logs
docker-compose logs -f
```

The app will be available on port 8080 by default.

### 4. Configure Caddy reverse proxy

Add this to your Caddyfile:

```caddy
curriculum.yourdomain.com {
    reverse_proxy localhost:8080
    
    # Optional: Add rate limiting
    @api {
        path /api/*
    }
    rate_limit @api {
        zone dynamic 10r/m
    }
}
```

Then reload Caddy:

```bash
caddy reload
```

## Port Configuration

By default, the container exposes port 8080. To change this:

1. Edit `docker-compose.yml`
2. Change the ports mapping from `"8080:80"` to your desired port
3. Update your Caddy configuration accordingly

## Data Persistence

All data is stored in the `./data` directory:
- `data/db/` - SQLite database
- `data/uploads/` - User uploaded files
- `data/logs/` - Application logs
- `data/content_repo/` - Git repository for content versioning

**Important:** Back up the `./data` directory regularly!

## Managing the Container

```bash
# Stop the container
docker-compose down

# View logs
docker-compose logs -f

# Restart the container
docker-compose restart

# Update to latest code
git pull
docker-compose build
docker-compose up -d
```

## Initial Setup

1. Access your app at your domain
2. Create the first admin account
3. Configure LLM providers in Settings (if not set via environment)
4. Start creating courses!

## Security Considerations

1. **Always change the SECRET_KEY** in production
2. Use HTTPS (Caddy handles this automatically with Let's Encrypt)
3. Consider adding rate limiting in Caddy
4. Regularly update the container with security patches
5. Back up your data directory

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Check if port 8080 is already in use
sudo lsof -i :8080
```

### Database issues
```bash
# Backup existing database
cp data/db/curriculum_curator.db data/db/curriculum_curator.db.backup

# Reset database (WARNING: deletes all data)
docker-compose exec app bash
cd /app/backend
alembic downgrade base
alembic upgrade head
```

### Permission issues
```bash
# Fix permissions on data directory
sudo chown -R $(whoami):$(whoami) ./data
```

## Advanced Configuration

### Using PostgreSQL instead of SQLite

1. Add PostgreSQL service to docker-compose.yml
2. Update DATABASE_URL in .env:
   ```
   DATABASE_URL=postgresql://user:password@postgres:5432/curriculum_curator
   ```

### Custom domain with SSL

Caddy automatically handles SSL certificates. Just ensure:
1. Your domain points to your VPS IP
2. Ports 80 and 443 are open
3. Caddy is configured with your domain

### Resource Limits

Add to docker-compose.yml to limit resources:

```yaml
services:
  app:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Support

For issues or questions:
- Check the logs: `docker-compose logs`
- Review the [README.md](README.md)
- Check existing issues on GitHub