# Production Deployment Guide

This guide walks through deploying Curriculum Curator in a production environment with proper security and reliability.

## Quick Start (Ubuntu/Debian)

### 1. System Requirements

- Ubuntu 20.04+ or Debian 11+
- Python 3.9+
- 2GB RAM minimum
- 10GB disk space
- Domain name with SSL certificate

### 2. Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv nginx sqlite3 certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash curriculum
sudo usermod -aG www-data curriculum

# Create directory structure
sudo mkdir -p /opt/curriculum-curator
sudo mkdir -p /var/lib/curriculum-curator/data
sudo mkdir -p /var/log/curriculum-curator
sudo chown -R curriculum:curriculum /opt/curriculum-curator
sudo chown -R curriculum:curriculum /var/lib/curriculum-curator
sudo chown -R curriculum:curriculum /var/log/curriculum-curator
```

### 3. Install Application

```bash
# Switch to app user
sudo su - curriculum
cd /opt/curriculum-curator

# Clone repository (or copy files)
git clone https://github.com/your-org/curriculum-curator.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file
cp .env.example .env
```

### 4. Configure Environment

Edit `/opt/curriculum-curator/.env`:

```env
# Generate strong secret: openssl rand -hex 32
SESSION_SECRET=your-very-strong-random-secret-here

# Email settings
BREVO_API_KEY=your-brevo-api-key
SENDER_EMAIL=noreply@university.edu
SENDER_NAME=Curriculum Curator
APP_BASE_URL=https://curriculum.university.edu

# Database path (outside web root)
DB_PATH=/var/lib/curriculum-curator/data/curriculum.db

# Production settings
ENVIRONMENT=production
LOG_LEVEL=warning
```

### 5. Initialize Database

```bash
# Still as curriculum user
cd /opt/curriculum-curator
source venv/bin/activate

# Initialize database and create admin
python init_db.py

# IMPORTANT: Change the default admin password immediately!
```

### 6. Configure Gunicorn

Create `/opt/curriculum-curator/gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "/var/log/curriculum-curator/access.log"
errorlog = "/var/log/curriculum-curator/error.log"
loglevel = "info"
user = "curriculum"
group = "curriculum"
```

### 7. Create Systemd Service

Create `/etc/systemd/system/curriculum-curator.service`:

```ini
[Unit]
Description=Curriculum Curator
After=network.target

[Service]
Type=notify
User=curriculum
Group=curriculum
WorkingDirectory=/opt/curriculum-curator
Environment="PATH=/opt/curriculum-curator/venv/bin"
Environment="PYTHONPATH=/opt/curriculum-curator"
ExecStart=/opt/curriculum-curator/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/curriculum-curator/data /var/log/curriculum-curator

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

### 8. Configure Nginx

Create `/etc/nginx/sites-available/curriculum-curator`:

```nginx
server {
    listen 80;
    server_name curriculum.university.edu;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name curriculum.university.edu;

    # SSL configuration (update paths)
    ssl_certificate /etc/letsencrypt/live/curriculum.university.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/curriculum.university.edu/privkey.pem;
    
    # Modern SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/curriculum-curator.access.log;
    error_log /var/log/nginx/curriculum-curator.error.log;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=general:10m rate=30r/m;

    location / {
        # Apply rate limiting
        limit_req zone=general burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /login {
        # Stricter rate limiting for login
        limit_req zone=login burst=5 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/curriculum-curator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Set Up SSL Certificate

```bash
# Using Let's Encrypt
sudo certbot --nginx -d curriculum.university.edu

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

### 10. Configure Firewall

```bash
# Using UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 11. Set Up Backups

Create `/usr/local/bin/backup-curriculum.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/curriculum-curator"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/var/lib/curriculum-curator/data/curriculum.db"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Backup database
sqlite3 ${DB_PATH} ".backup ${BACKUP_DIR}/curriculum_${DATE}.db"

# Compress backup
gzip ${BACKUP_DIR}/curriculum_${DATE}.db

# Keep only last 30 days
find ${BACKUP_DIR} -name "curriculum_*.db.gz" -mtime +30 -delete

# Optional: Copy to remote backup location
# rsync -av ${BACKUP_DIR}/curriculum_${DATE}.db.gz backup-server:/backups/
```

Make executable and add to cron:

```bash
sudo chmod +x /usr/local/bin/backup-curriculum.sh
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-curriculum.sh
```

### 12. Monitoring Setup

Create `/usr/local/bin/check-curriculum.sh`:

```bash
#!/bin/bash
# Simple health check

# Check if service is running
if ! systemctl is-active --quiet curriculum-curator; then
    echo "Curriculum Curator service is down!"
    systemctl start curriculum-curator
    # Send alert (email, Slack, etc.)
fi

# Check disk space
DISK_USAGE=$(df -h /var/lib/curriculum-curator | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage is above 80%!"
    # Send alert
fi

# Check if web is responding
if ! curl -f -s https://curriculum.university.edu/health > /dev/null; then
    echo "Web interface not responding!"
    # Send alert
fi
```

Add to cron:

```bash
*/5 * * * * /usr/local/bin/check-curriculum.sh
```

## Security Checklist

Before going live:

- [ ] Changed default admin password
- [ ] Configured strong SESSION_SECRET
- [ ] SSL certificate installed and working
- [ ] Firewall configured and enabled
- [ ] Database permissions set correctly (600)
- [ ] Backups configured and tested
- [ ] Monitoring in place
- [ ] Rate limiting configured in Nginx
- [ ] Removed any debug/development settings
- [ ] Tested login and core functionality

## Maintenance Tasks

### Daily
- Check application logs for errors
- Verify backups completed

### Weekly
- Review security logs for suspicious activity
- Check disk space usage
- Test backup restoration (staging environment)

### Monthly
- Update system packages: `sudo apt update && sudo apt upgrade`
- Review and update Python dependencies
- Check SSL certificate expiration
- Review user accounts and permissions

### Quarterly
- Full backup restoration test
- Security audit of logs
- Performance review and tuning
- Documentation updates

## Troubleshooting

### Application Won't Start

```bash
# Check service status
sudo systemctl status curriculum-curator

# Check logs
sudo journalctl -u curriculum-curator -f
tail -f /var/log/curriculum-curator/error.log

# Common issues:
# - Wrong Python version
# - Missing dependencies
# - Database permissions
# - Port already in use
```

### Database Locked

```bash
# Check for stuck processes
sudo fuser /var/lib/curriculum-curator/data/curriculum.db

# Ensure correct permissions
sudo chown curriculum:curriculum /var/lib/curriculum-curator/data/curriculum.db
sudo chmod 600 /var/lib/curriculum-curator/data/curriculum.db
```

### High Memory Usage

```bash
# Restart service
sudo systemctl restart curriculum-curator

# Adjust workers in gunicorn_config.py
# Reduce from 4 to 2 for low-memory systems
```

### SSL Certificate Issues

```bash
# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal

# Check certificate
sudo openssl x509 -in /etc/letsencrypt/live/curriculum.university.edu/cert.pem -text -noout
```

## Performance Tuning

### For Small Deployments (< 50 users)
- 2 Gunicorn workers
- 1GB RAM
- SQLite default settings

### For Medium Deployments (50-500 users)
- 4-8 Gunicorn workers
- 4GB RAM
- Consider PostgreSQL migration
- Add Redis for session storage

### For Large Deployments (500+ users)
- Multiple application servers
- PostgreSQL database
- Redis for sessions and caching
- Load balancer (HAProxy/Nginx)
- CDN for static assets

## Disaster Recovery

### Backup Restoration

```bash
# Stop service
sudo systemctl stop curriculum-curator

# Restore database
cd /var/lib/curriculum-curator/data
gunzip -c /var/backups/curriculum-curator/curriculum_20250108_020000.db.gz > curriculum.db
chown curriculum:curriculum curriculum.db
chmod 600 curriculum.db

# Start service
sudo systemctl start curriculum-curator
```

### Full Server Recovery

1. Provision new server
2. Follow installation steps
3. Restore latest database backup
4. Update DNS if needed
5. Test all functionality

## Support

For issues:
1. Check logs first
2. Review this guide
3. Search existing issues on GitHub
4. Create new issue with:
   - Error messages
   - Steps to reproduce
   - Environment details
   - Relevant log excerpts