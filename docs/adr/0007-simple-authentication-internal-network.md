# 7. Simple Authentication for Internal Network Deployment

Date: 2024-01-15

## Status

Accepted

## Context

The Curriculum Curator is designed to be deployed within university networks (specifically Curtin University). The application needs user authentication to:
- Track individual users' content and preferences
- Maintain teaching philosophy profiles
- Provide personalized experiences
- Allow administrative functions

Given the internal deployment context, we need to balance security with usability and implementation complexity.

## Decision

We will implement a simple session-based authentication system with:
- Email/password registration limited to whitelisted domains (@curtin.edu.au)
- Self-registration with email verification (using Brevo)
- Self-service password reset via email
- Basic admin functionality for user management
- Session cookies for maintaining login state
- SQLite storage for users and sessions

We explicitly chose NOT to implement:
- Two-factor authentication (for now)
- External authentication providers (OAuth/SSO) - planned for future
- Complex password policies beyond minimum length

## Consequences

### Positive
- **Reduced admin workload**: Self-service registration and password reset
- **Better security**: Email verification prevents unauthorized registrations
- **User-friendly**: Users can reset passwords without waiting for admin
- **Professional appearance**: Email verification is expected behavior
- **Suitable for internal use**: Still appropriate for university network
- **Scalable**: Can handle more users without admin bottleneck

### Negative
- **Email service dependency**: Requires Brevo API to be available
- **Configuration needed**: Must set up and maintain email templates
- **Potential email delays**: Users might experience delays in receiving emails
- **Spam folder issues**: Verification emails might go to spam
- **No SSO benefits**: Users still need separate credentials

### Security Assumptions
1. **Network security**: University network provides perimeter security
2. **Trusted users**: Only university staff with valid emails will register
3. **Physical security**: Servers are in secure data centers
4. **Limited exposure**: Application not accessible from public internet

## Implementation Details

### Current Implementation
```python
# Domain whitelisting
WHITELISTED_DOMAINS = ['@curtin.edu.au']

# Simple registration check
def is_email_whitelisted(self, email: str) -> bool:
    for domain in self.WHITELISTED_DOMAINS:
        if email.endswith(domain):
            return True
    return False

# Basic password hashing
password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                   salt.encode('utf-8'), 100000)
```

### Admin Features
- Toggle admin status for users
- View all registered users
- Delete user accounts
- No built-in password reset (future feature)

## Future Enhancements

When ready to deploy more broadly or enhance security:

### Phase 1: Email Verification
- Add email verification for registration
- Implement password reset via email
- Add email notifications for important actions

### Phase 2: OAuth/SSO Integration
- Integrate with university's SSO system (likely SAML or OAuth)
- Support for Microsoft Azure AD (common in universities)
- Maintain simple auth as fallback

### Phase 3: Enhanced Security
- Two-factor authentication options
- Password complexity requirements
- Account lockout policies
- Security audit logging

## Example Future Configuration
```python
# Future OAuth configuration
AUTH_PROVIDERS = {
    'curtin_sso': {
        'type': 'oauth2',
        'client_id': 'curriculum-curator',
        'authorize_url': 'https://login.curtin.edu.au/oauth/authorize',
        'token_url': 'https://login.curtin.edu.au/oauth/token',
        'scope': ['email', 'profile']
    },
    'microsoft': {
        'type': 'azure_ad',
        'tenant_id': 'curtin.edu.au',
        'client_id': 'app-id-here'
    }
}
```

## Related Decisions
- ADR-0006: Pure FastHTML Without JavaScript (simplifies auth flow)
- ADR-0002: Validation and Remediation Design (affects user permissions model)
- ADR-0008: Email Verification with Cross-Device Support (extends this design)
- ADR-0009: Self-Service Password Reset (implements Phase 1 enhancement)