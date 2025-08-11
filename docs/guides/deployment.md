# Deployment Guide

This guide covers deploying Curriculum Curator in various environments.

## Prerequisites

- Python 3.12+
- pip
- Virtual environment tool (venv, virtualenv, or conda)
- Web server (nginx, Apache) for production
- SSL certificate for HTTPS

## Development Deployment

### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/curriculum-curator.git
cd curriculum-curator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from core.database import init_db; init_db()"

# Run development server
python app.py
```

Access at: `http://localhost:5001`

### Development Configuration

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///data/curriculum.db
CONTENT_DIR=data/courses
```

## Production Deployment

### System Requirements

- Ubuntu 20.04+ or similar Linux distribution
- 2GB RAM minimum (4GB recommended)
- 10GB disk space
- Python 3.12+
- nginx or Apache
- systemd for service management

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.12 python3.12-venv python3-pip nginx git -y

# Create application user
sudo useradd -m -s /bin/bash curriculum
sudo su - curriculum
```

### Step 2: Application Setup

```bash
# Clone application
cd /home/curriculum
git clone https://github.com/yourusername/curriculum-curator.git
cd curriculum-curator

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server

# Create data directories
mkdir -p data/courses data/uploads data/exports
chmod 755 data
```

### Step 3: Environment Configuration

```bash
# /home/curriculum/curriculum-curator/.env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key-here
DATABASE_URL=sqlite:////home/curriculum/curriculum-curator/data/curriculum.db
CONTENT_DIR=/home/curriculum/curriculum-curator/data/courses
UPLOAD_DIR=/home/curriculum/curriculum-curator/data/uploads
EXPORT_DIR=/home/curriculum/curriculum-curator/data/exports
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Step 4: Gunicorn Configuration

```python
# /home/curriculum/curriculum-curator/gunicorn_config.py
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "/home/curriculum/curriculum-curator/logs/access.log"
errorlog = "/home/curriculum/curriculum-curator/logs/error.log"
loglevel = "info"
```

### Step 5: Systemd Service

```ini
# /etc/systemd/system/curriculum-curator.service
[Unit]
Description=Curriculum Curator FastHTML Application
After=network.target

[Service]
Type=notify
User=curriculum
Group=curriculum
WorkingDirectory=/home/curriculum/curriculum-curator
Environment="PATH=/home/curriculum/curriculum-curator/venv/bin"
ExecStart=/home/curriculum/curriculum-curator/venv/bin/gunicorn \
    --config /home/curriculum/curriculum-curator/gunicorn_config.py \
    app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable curriculum-curator
sudo systemctl start curriculum-curator
sudo systemctl status curriculum-curator
```

### Step 6: Nginx Configuration

```nginx
# /etc/nginx/sites-available/curriculum-curator
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/curriculum-curator.access.log;
    error_log /var/log/nginx/curriculum-curator.error.log;
    
    # File upload size
    client_max_body_size 50M;
    
    # Static files
    location /static {
        alias /home/curriculum/curriculum-curator/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media/uploaded files
    location /media {
        alias /home/curriculum/curriculum-curator/data/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for HTMX SSE
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/curriculum-curator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 7: SSL Certificate

Using Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 curriculum

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY --chown=curriculum:curriculum . .

# Create data directories
RUN mkdir -p data/courses data/uploads data/exports logs \
    && chown -R curriculum:curriculum data logs

# Switch to non-root user
USER curriculum

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "app:app"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=sqlite:////app/data/curriculum.db
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./data/uploads:/app/data/uploads:ro
    depends_on:
      - web
    restart: unless-stopped
```

### Build and Run

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Cloud Deployment

### AWS EC2

1. **Launch Instance**
   - Ubuntu 20.04 AMI
   - t3.small or larger
   - 20GB EBS volume
   - Security group: ports 22, 80, 443

2. **Follow Production Deployment Steps**

3. **Additional AWS Configuration**
   ```bash
   # Install AWS CLI
   sudo apt install awscli
   
   # Configure S3 for backups
   aws configure
   
   # Backup script
   #!/bin/bash
   aws s3 sync /home/curriculum/curriculum-curator/data \
       s3://your-backup-bucket/curriculum-curator/
   ```

### DigitalOcean Droplet

1. **Create Droplet**
   - Ubuntu 20.04
   - 2GB RAM minimum
   - Regular Intel with SSD

2. **Initial Setup**
   ```bash
   # Create swap file for small droplets
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

3. **Follow Production Deployment Steps**

### Heroku

```python
# Procfile
web: gunicorn app:app --worker-class uvicorn.workers.UvicornWorker
```

```python
# runtime.txt
python-3.12.0
```

```bash
# Deploy
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

## Database Management

### Backup Strategy

```bash
#!/bin/bash
# /home/curriculum/backup.sh

BACKUP_DIR="/home/curriculum/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/home/curriculum/curriculum-curator/data/curriculum.db"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/curriculum_$DATE.db'"

# Backup course files
tar -czf "$BACKUP_DIR/courses_$DATE.tar.gz" \
    -C /home/curriculum/curriculum-curator/data courses/

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Automated Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /home/curriculum/backup.sh
```

### Database Migration

```python
# migrate_db.py
import sqlite3
from pathlib import Path

def migrate_database():
    """Apply database migrations."""
    db_path = Path("data/curriculum.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Example migration: Add column
    try:
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN last_login TIMESTAMP
        """)
        print("Added last_login column")
    except sqlite3.OperationalError:
        print("Column already exists")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_database()
```

## Monitoring

### Application Monitoring

```python
# monitoring.py
import psutil
import logging
from datetime import datetime

def check_system_health():
    """Check system resources."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    health = {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "status": "healthy"
    }
    
    # Alert if resources are high
    if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
        health["status"] = "warning"
        logging.warning(f"System resources high: {health}")
    
    return health
```

### Log Rotation

```ini
# /etc/logrotate.d/curriculum-curator
/home/curriculum/curriculum-curator/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 curriculum curriculum
    sharedscripts
    postrotate
        systemctl reload curriculum-curator > /dev/null 2>&1 || true
    endscript
}
```

## Security Hardening

### Application Security

```python
# security_config.py

# Security headers
SECURITY_HEADERS = {
    "X-Frame-Options": "SAMEORIGIN",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'"
}

# Session configuration
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
```

### Firewall Configuration

```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### Fail2ban Configuration

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[curriculum-curator]
enabled = true
port = http,https
filter = curriculum-curator
logpath = /var/log/nginx/curriculum-curator.access.log
maxretry = 10
```

## Performance Optimization

### Caching Configuration

```python
# cache_config.py
from functools import lru_cache
import redis

# Redis for production caching
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

@lru_cache(maxsize=100)
def get_teaching_style(user_id: str):
    """Cache teaching style lookups."""
    # Check Redis first
    cached = redis_client.get(f"teaching_style:{user_id}")
    if cached:
        return cached
    
    # Load from database
    style = load_from_db(user_id)
    
    # Cache for 1 hour
    redis_client.setex(
        f"teaching_style:{user_id}",
        3600,
        style
    )
    
    return style
```

### Static File Optimization

```bash
# Compress static files
find static/ -type f \( -name "*.js" -o -name "*.css" \) \
    -exec gzip -9 -k {} \;

# Generate WebP images
for img in static/images/*.{jpg,png}; do
    cwebp -q 80 "$img" -o "${img%.*}.webp"
done
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   sudo lsof -i :5001
   # Kill process
   sudo kill -9 <PID>
   ```

2. **Permission Denied**
   ```bash
   # Fix ownership
   sudo chown -R curriculum:curriculum /home/curriculum/curriculum-curator
   # Fix permissions
   chmod 755 /home/curriculum/curriculum-curator/data
   ```

3. **Database Locked**
   ```python
   # Add to database config
   pragma journal_mode=WAL;
   pragma busy_timeout=5000;
   ```

4. **Memory Issues**
   ```bash
   # Check memory usage
   free -h
   # Clear cache if needed
   sudo sync && sudo sysctl -w vm.drop_caches=3
   ```

### Health Check Endpoint

```python
# In app.py
@rt("/health")
def get():
    """Health check endpoint."""
    try:
        # Check database
        db.execute("SELECT 1")
        
        # Check filesystem
        Path("data/courses").exists()
        
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500
```

## Maintenance

### Regular Tasks

1. **Weekly**
   - Check disk space
   - Review error logs
   - Verify backups

2. **Monthly**
   - Update dependencies
   - Review security updates
   - Clean old exports

3. **Quarterly**
   - Performance audit
   - Security scan
   - Database optimization

### Update Procedure

```bash
#!/bin/bash
# update.sh

# Backup first
./backup.sh

# Pull latest code
cd /home/curriculum/curriculum-curator
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Run migrations if any
python migrate_db.py

# Restart service
sudo systemctl restart curriculum-curator

# Verify health
curl https://yourdomain.com/health
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer Setup**
   - Use nginx or HAProxy
   - Sticky sessions for user state
   - Health check endpoints

2. **Shared Storage**
   - NFS for course files
   - S3-compatible object storage
   - CDN for static assets

3. **Database Scaling**
   - PostgreSQL for multi-server
   - Read replicas for performance
   - Connection pooling

### Vertical Scaling

1. **Resource Monitoring**
   - CPU usage patterns
   - Memory consumption
   - Disk I/O metrics

2. **Optimization Points**
   - Database queries
   - File operations
   - LLM API calls

## Support

For deployment issues:
- Check logs: `/home/curriculum/curriculum-curator/logs/`
- Review documentation
- Submit GitHub issues
- Community forum