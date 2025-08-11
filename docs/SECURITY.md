# Security Overview

This document provides a quick reference for security features and best practices in Curriculum Curator.

## 🛡️ Built-in Security Features

### Authentication & Authorization
- ✅ PBKDF2 password hashing (100k iterations)
- ✅ Secure session management
- ✅ Domain-restricted registration
- ✅ Email verification required
- ✅ Admin role separation

### Attack Prevention
- ✅ Rate limiting (login & password reset)
- ✅ CSRF protection on all forms
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS protection via security headers
- ✅ Session fixation prevention

### Security Headers
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'...
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### Audit & Monitoring
- ✅ Login attempt logging
- ✅ Security event tracking
- ✅ Failed authentication alerts
- ✅ Rate limit violation logging

## 🚀 Deployment Security Checklist

### Before Going Live
- [ ] Change default admin password
- [ ] Set strong SESSION_SECRET in .env
- [ ] Configure HTTPS/SSL certificate
- [ ] Set up firewall rules
- [ ] Configure automated backups
- [ ] Review file permissions
- [ ] Enable monitoring/alerting
- [ ] Test rate limiting

### Infrastructure Security
- [ ] Use HTTPS only (redirect HTTP)
- [ ] Keep database outside web root
- [ ] Run application as non-root user
- [ ] Regular security updates
- [ ] Implement backup encryption
- [ ] Monitor disk space
- [ ] Set up log rotation

## 🔒 Password Requirements

Users must create passwords that meet these criteria:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- Not in common password list

## ⚡ Rate Limits

### Login Attempts
- 5 attempts per email per 15 minutes
- 10 attempts per IP per 15 minutes
- 60-minute block after exceeding

### Password Reset
- 3 requests per email per hour
- 5 requests per IP per hour
- Prevents email bombing

## 🐛 Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Email: security@your-institution.edu
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We aim to respond within 48 hours and provide a fix within 7 days for critical issues.

## 📚 Security Documentation

For detailed information, see:
- [ADR-0010: Security Hardening](docs/adr/0010-security-hardening.md)
- [ADR-0011: Deployment Best Practices](docs/adr/0011-deployment-best-practices.md)
- [Authentication & Security Guide](docs/guides/authentication-security.md)
- [Production Deployment Guide](docs/guides/production-deployment.md)

## 🔄 Regular Security Tasks

### Daily
- Review security logs
- Check backup completion

### Weekly
- Review failed login attempts
- Update dependencies with security fixes

### Monthly
- Full security log audit
- Test backup restoration
- Review user permissions

### Quarterly
- Security assessment
- Penetration testing (if applicable)
- Update security documentation

## 💡 Security Tips for Users

1. **Use strong, unique passwords**
2. **Don't share your account**
3. **Log out when done** (especially on shared computers)
4. **Report suspicious activity** to administrators
5. **Keep your email secure** (used for password reset)

## 🚨 Incident Response

If a security incident occurs:

1. **Identify**: Check logs, determine scope
2. **Contain**: Block attacker IP, disable affected accounts
3. **Investigate**: Preserve evidence, find root cause
4. **Remediate**: Fix vulnerability, reset passwords
5. **Document**: Record lessons learned
6. **Communicate**: Notify affected users if needed

## 📈 Security Metrics

Track these metrics:
- Failed login attempts per day
- Rate limit violations
- Password reset requests
- New user registrations
- Security incidents per month

---

Remember: Security is everyone's responsibility. Stay vigilant and report concerns promptly.