# 10. Security Hardening for Open Source Deployment

Date: 2025-01-08

## Status

Accepted

## Context

While Curriculum Curator is designed for deployment within university networks, as an open source project under MIT license, it may be deployed in various environments. We need basic security protections that work well for internal deployments but also provide reasonable security for other use cases.

Key concerns:
1. Script kiddies and automated attacks
2. Brute force login attempts
3. Weak passwords
4. Cross-site request forgery (CSRF)
5. Security headers for browser protection
6. Audit trail for security events

## Decision

We will implement a comprehensive set of security measures appropriate for an educational web application:

### 1. Password Security
- **Storage**: PBKDF2-HMAC-SHA256 with 100,000 iterations (already implemented)
- **Validation**: Enforce minimum requirements:
  - At least 8 characters
  - Contains uppercase and lowercase letters
  - Contains at least one number
  - Not in common password list
- **Reset**: Secure token-based reset with expiration

### 2. Rate Limiting
In-memory rate limiting for:
- **Login attempts**: 5 per email/15 min, 10 per IP/15 min
- **Password reset**: 3 per email/hour, 5 per IP/hour
- **Auto-blocking**: 60 minutes after exceeding limits

### 3. Session Security
- Cryptographically secure session tokens
- HTTP-only cookies (prevents JS access)
- Session expiration (7 days)
- Invalidate all sessions on password reset

### 4. CSRF Protection
- Generate unique tokens per session
- Validate on all state-changing operations
- 4-hour token expiration

### 5. Security Headers
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;
```

### 6. Audit Logging
Track security-relevant events:
- Failed login attempts
- Successful logins
- Rate limit violations
- Password resets
- Admin actions

### 7. Input Validation
- Email format validation
- Domain whitelisting for registration
- Password strength requirements
- Safe SQL queries (parameterized)

## Implementation Details

### Security Manager (`core/security.py`)
```python
class SecurityManager:
    - Rate limiting with configurable thresholds
    - CSRF token generation/validation
    - Password strength validation
    - Security event logging
    - Login attempt tracking
```

### Integration Points
1. **Login**: Check rate limits, record attempts, log events
2. **Registration**: Validate password strength
3. **Password Reset**: Rate limit requests
4. **All Forms**: CSRF protection on POST requests
5. **All Responses**: Security headers via middleware

## Consequences

### Positive
- **Protection from automated attacks**: Rate limiting stops brute force
- **Better password security**: Users forced to use stronger passwords
- **Audit trail**: Can investigate security incidents
- **CSRF protection**: Prevents cross-site attacks
- **Browser security**: Headers prevent common client-side attacks
- **Open source ready**: Reasonable security for any deployment

### Negative
- **User friction**: Password requirements may annoy some users
- **Complexity**: More code to maintain and test
- **Performance**: Slight overhead from security checks
- **False positives**: Legitimate users might hit rate limits

### Neutral
- **In-memory rate limiting**: Simple but resets on restart (acceptable for small deployments)
- **No external dependencies**: All security features are self-contained
- **Configurable thresholds**: Can adjust based on deployment needs

## Security Not Implemented (Future Considerations)

1. **Two-Factor Authentication**: Adds complexity, not needed for internal use
2. **IP-based blocking**: Could block legitimate users behind NAT
3. **Distributed rate limiting**: Only needed for multi-server deployments
4. **Password history**: Overkill for this use case
5. **Account lockout**: Rate limiting provides similar protection

## Testing Security

```bash
# Test rate limiting
for i in {1..10}; do
  curl -X POST http://localhost:5000/login \
    -d "email=test@example.com&password=wrong" 
done

# Test password validation
curl -X POST http://localhost:5000/signup \
  -d "email=test@curtin.edu.au&password=weak"

# Check security headers
curl -I http://localhost:5000
```

## Deployment Recommendations

1. **Always use HTTPS** in production (even internal networks)
2. **Regular backups** of the database
3. **Monitor logs** for suspicious patterns
4. **Update dependencies** regularly
5. **Consider WAF** for internet-facing deployments

## Related

- Extends authentication system (ADR-0007)
- Complements email verification (ADR-0008)
- Supports password reset security (ADR-0009)
- Maintains no-JavaScript approach (ADR-0006)

## References

- OWASP Top 10 Web Application Security Risks
- NIST Password Guidelines (SP 800-63B)
- Mozilla Web Security Guidelines
- CWE/SANS Top 25 Most Dangerous Software Errors