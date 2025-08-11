# 11. Deployment Best Practices and Production Security

Date: 2025-01-08

## Status

Accepted

## Context

While Curriculum Curator has built-in security measures (ADR-0010), deploying any web application requires additional considerations at the infrastructure level. As an open source project, we need to provide clear guidance for secure production deployments.

Key deployment scenarios:
1. **Internal University Network** (primary use case)
2. **Cloud/VPS Deployment** (smaller institutions)
3. **Docker/Container Deployment** (modern infrastructure)
4. **Development/Testing** (local environments)

## Decision

We will document and recommend a comprehensive set of deployment best practices that complement our application-level security measures.

### 1. HTTPS/TLS Configuration

**Requirement**: Always use HTTPS in production, even on internal networks.

```nginx
# Example Nginx configuration
server {
    listen 443 ssl http2;
    server_name curriculum.university.edu;
    
    # Modern TLS configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256...;
    ssl_prefer_server_ciphers off;
    
    # Security headers (complement app headers)
    add_header Strict-Transport-Security "max-age=63072000" always;
}
```

**Rationale**: 
- Protects credentials in transit
- Prevents session hijacking
- Required for modern security standards
- Many browser features require HTTPS

### 2. Database Security

**SQLite Considerations**:
```bash
# Secure file permissions
chmod 600 data/curriculum.db
chown appuser:appgroup data/curriculum.db

# Place database outside web root
/var/lib/curriculum-curator/
├── data/
│   └── curriculum.db  # Not in /var/www/
```

**Backup Strategy**:
```bash
# Automated daily backups with rotation
0 2 * * * /usr/local/bin/backup-curriculum.sh

# backup-curriculum.sh
#!/bin/bash
BACKUP_DIR="/var/backups/curriculum-curator"
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 /var/lib/curriculum-curator/data/curriculum.db ".backup ${BACKUP_DIR}/curriculum_${DATE}.db"
# Keep only last 30 days
find ${BACKUP_DIR} -name "curriculum_*.db" -mtime +30 -delete
```

### 3. Application Server Configuration

**Recommended: Gunicorn with Nginx**:
```python
# gunicorn_config.py
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
```

**Systemd Service**:
```ini
[Unit]
Description=Curriculum Curator
After=network.target

[Service]
Type=notify
User=appuser
Group=appgroup
WorkingDirectory=/opt/curriculum-curator
Environment="PATH=/opt/curriculum-curator/venv/bin"
ExecStart=/opt/curriculum-curator/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/curriculum-curator/data

[Install]
WantedBy=multi-user.target
```

### 4. Monitoring and Logging

**Log Aggregation**:
```python
# logging_config.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/curriculum-curator/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'standard',
        },
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/curriculum-curator/security.log',
            'maxBytes': 10485760,
            'backupCount': 30,  # Keep security logs longer
            'formatter': 'standard',
        },
    },
}
```

**Monitoring Checklist**:
- Failed login attempts (indicator of attacks)
- Rate limit violations
- Disk space for database growth
- Application errors
- Response time metrics
- SSL certificate expiration

### 5. Environment Configuration

**Production .env**:
```bash
# Strong session secret (generate with: openssl rand -hex 32)
SESSION_SECRET=your-strong-random-secret-here

# Email configuration
BREVO_API_KEY=your-production-api-key
SENDER_EMAIL=noreply@university.edu
SENDER_NAME=Curriculum Curator
APP_BASE_URL=https://curriculum.university.edu

# Database (use absolute path)
DB_PATH=/var/lib/curriculum-curator/data/curriculum.db

# Environment
ENVIRONMENT=production
LOG_LEVEL=warning
```

### 6. Security Updates

**Dependency Management**:
```bash
# Regular update schedule (monthly)
pip list --outdated
pip install --upgrade -r requirements.txt

# Security-only updates (weekly)
pip install --upgrade safety
safety check

# Automated alerts
# Consider using GitHub Dependabot or similar
```

### 7. Network Security

**Firewall Rules**:
```bash
# UFW example for Ubuntu
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 443/tcp  # HTTPS only
ufw enable
```

**Reverse Proxy Benefits**:
- Hide application server details
- Add additional security headers
- Enable rate limiting at proxy level
- SSL termination
- Load balancing (future)

### 8. Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Security: Run as non-root user
RUN useradd -m -r appuser && \
    mkdir -p /app /data && \
    chown -R appuser:appuser /app /data

WORKDIR /app

# Install dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  app:
    build: .
    restart: always
    environment:
      - ENVIRONMENT=production
    volumes:
      - ./data:/data
      - ./logs:/var/log/curriculum-curator
    networks:
      - internal
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - internal
      - external

networks:
  internal:
    internal: true
  external:
```

### 9. Pre-Deployment Checklist

- [ ] Change default admin password
- [ ] Configure HTTPS with valid certificate
- [ ] Set strong SESSION_SECRET
- [ ] Configure email service
- [ ] Set up automated backups
- [ ] Configure logging and monitoring
- [ ] Review firewall rules
- [ ] Test rate limiting
- [ ] Document recovery procedures
- [ ] Create initial admin account
- [ ] Remove debug mode
- [ ] Set appropriate file permissions

### 10. Incident Response

**Security Incident Procedure**:
1. Identify scope (check security.log)
2. Isolate if necessary (firewall rules)
3. Preserve evidence (backup logs)
4. Reset affected passwords
5. Review and patch vulnerability
6. Document lessons learned

## Consequences

### Positive
- **Defense in depth**: Multiple security layers
- **Operational resilience**: Automated backups and monitoring
- **Compliance ready**: Audit trails and secure configuration
- **Scalable**: Can grow from single server to clustered deployment
- **Recovery capability**: Documented backup/restore procedures

### Negative
- **Complexity**: More components to manage
- **Cost**: Requires proper infrastructure
- **Maintenance**: Regular updates needed
- **Learning curve**: Admins need DevOps knowledge

## Implementation Priority

1. **Critical** (Day 1):
   - HTTPS configuration
   - Change default passwords
   - Basic firewall rules
   - Database backups

2. **Important** (Week 1):
   - Monitoring setup
   - Log rotation
   - Automated updates
   - Documentation

3. **Nice to Have** (Month 1):
   - Container deployment
   - Advanced monitoring
   - Load balancing
   - CI/CD pipeline

## Related

- Implements security from ADR-0010
- Supports authentication system (ADR-0007, 0008, 0009)
- Complements open source release strategy

## References

- OWASP Deployment Security Guide
- CIS Benchmarks for Linux/Docker
- NIST Cybersecurity Framework
- PCI DSS (if handling payments in future)