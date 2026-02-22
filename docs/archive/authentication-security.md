# Authentication and Security Guide

## Overview

Curriculum Curator uses a simple, session-based authentication system designed for deployment within university networks. This guide explains the security model and how to configure authentication.

## Current Authentication Model

### Design Principles
- **Simplicity First**: Easy to deploy and maintain within trusted networks
- **Self-Service**: Users can register themselves with valid university email
- **Minimal Dependencies**: No external services required
- **Appropriate Security**: Suitable for internal university deployment

### Features
- Email/password authentication
- Domain-restricted registration (@curtin.edu.au)
- Email verification for new accounts (via Brevo)
- Self-service password reset via email
- Session-based login with secure cookies
- Admin functionality for user management
- Password hashing with PBKDF2

### Limitations
- No two-factor authentication (yet)
- Single domain whitelist (easily configurable)
- Basic email templates (can be customized)

## Security Considerations

### Deployment Environment
This authentication system assumes:
1. **Internal Network**: Application deployed within university firewall
2. **Network Security**: Protected by institutional security measures
3. **Trusted Users**: Only university staff/faculty have network access
4. **Not Internet-Facing**: Application not accessible from public internet

### Current Security Measures

#### Password Security
- Passwords hashed with PBKDF2-HMAC-SHA256 (100,000 iterations)
- Enforced password requirements:
  - Minimum 8 characters
  - Must contain uppercase and lowercase letters
  - Must contain at least one number
  - Rejected if in common password list
- Secure password reset with time-limited tokens

#### Rate Limiting
- **Login attempts**: 5 failures per email in 15 minutes (then 60-minute block)
- **IP-based limits**: 10 login attempts per IP in 15 minutes
- **Password reset**: 3 requests per email per hour
- Automatic unblocking after timeout period

#### Session Management
- Cryptographically secure random session tokens
- HTTP-only cookies (prevents JavaScript access)
- Sessions expire after 7 days of inactivity
- All sessions invalidated on password reset
- Admin accounts can only be created by other admins

#### CSRF Protection
- Unique tokens generated per session
- Required for all POST/PUT/DELETE operations
- Tokens expire after 4 hours
- Automatic validation on form submissions

#### Security Headers
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Content-Security-Policy` - Restricts resource loading
- `Referrer-Policy` - Controls referrer information

#### Audit Logging
- Failed login attempts tracked with IP address
- Successful logins logged
- Rate limit violations recorded
- Security events stored in database
- Password reset attempts logged

## Configuration

### Email Service Setup (Brevo)
1. Sign up for a free Brevo account at https://www.brevo.com
2. Get your API key from Settings → Keys → API Keys
3. Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

4. Add your Brevo API key:

```env
BREVO_API_KEY=your-actual-api-key-here
SENDER_EMAIL=noreply@curtin.edu.au
SENDER_NAME=Curriculum Curator
APP_BASE_URL=http://localhost:5000
```

### Domain Whitelisting
Edit `core/auth.py` to modify allowed domains:

```python
# Current configuration
WHITELISTED_DOMAINS = ['@curtin.edu.au']

# To add more domains
WHITELISTED_DOMAINS = ['@curtin.edu.au', '@murdoch.edu.au', '@uwa.edu.au']
```

### Admin Account Setup
The first admin account is created during initialization:

```bash
python init_db.py
# Creates admin@curtin.edu.au with password 'admin123'
# CHANGE THIS PASSWORD IMMEDIATELY!
# Admin account is auto-verified (no email verification needed)
```

### Session Configuration
Modify session duration in `core/auth.py`:

```python
# Current: 7 days
expires_at = datetime.now() + timedelta(days=7)

# For shorter sessions (e.g., 1 day)
expires_at = datetime.now() + timedelta(days=1)
```

## Security Best Practices

### For Deployment
1. **Change Default Admin Password**: First login action should be password change
2. **Use HTTPS**: Even on internal networks, use SSL/TLS
3. **Regular Backups**: Backup the SQLite database regularly
4. **Monitor Access**: Review user registrations periodically
5. **Update Dependencies**: Keep FastHTML and other packages updated

### For Users
1. **Strong Passwords**: Use unique, strong passwords
2. **Don't Share Accounts**: Each user should have their own account
3. **Report Issues**: Report suspicious activity to IT

## Future Enhancements

### Phase 1: Email Integration (COMPLETED)
- ✅ Email verification for new accounts
- ✅ Password reset via email
- ✅ Cross-device verification support
- Future: Email notifications for important actions

### Phase 2: SSO Integration (6-12 months)
- University Single Sign-On integration
- Support for SAML/OAuth2
- Automatic user provisioning

### Phase 3: Enhanced Security (12+ months)
- Two-factor authentication
- Audit logging
- Role-based access control
- API key authentication

## Email Verification Process

### For New Users
1. Register with your @curtin.edu.au email
2. Check your email for a 6-digit verification code
3. Choose one of these options:
   - **Option A**: Enter the 6-digit code on the registration success page
   - **Option B**: Click the verification link in your email
4. Login with your credentials

### Cross-Device Workflow
Perfect for when you register on one device but check email on another:
- Register on classroom/lab computer
- Check email on your phone
- See the 6-digit code (e.g., 123456)
- Enter code on the computer where you registered
- Account verified - ready to login!

### Resending Verification
If you didn't receive the email:
1. Try to login
2. Click "Resend verification email" link
3. New code and link will be sent
4. Check your spam folder
5. Contact admin if issues persist

## Password Reset Process

### Self-Service Reset (New!)
1. Click "Forgot password?" on login page
2. Enter your registered email address
3. Check your email for reset link
4. Click the link (expires in 1 hour)
5. Enter your new password twice
6. Login with new password

### Admin Password Reset
Administrators can still reset passwords manually:
1. Login with admin account
2. Go to Admin Panel
3. Find the user in the table
4. Click "Reset Password" button
5. Enter new password twice
6. Inform the user of their new password

**Security Notes:**
- Password reset links expire after 1 hour
- Each link can only be used once
- All existing sessions are invalidated after reset
- Email is sent to registered address only

## Troubleshooting

### Common Issues

**User can't register**
- Check email domain is whitelisted
- Verify database is writable
- Check for existing account with same email

**User can't login**
- Verify password is correct
- Check if account is locked due to rate limiting (wait 60 minutes)
- Ensure email is verified
- Check session hasn't expired
- Clear browser cookies and try again
- Contact admin for password reset if needed

**"Too many login attempts" error**
- Wait 60 minutes for automatic unblock
- Use different email if you have multiple accounts
- Contact admin if urgent access needed
- Check if someone else is trying to access your account

**Forgot password**
- No self-service option currently
- Contact administrator with registered email
- Admin will reset password manually

**Admin functions not working**
- Verify user has is_admin=True in database
- Check session is valid
- Ensure proper permissions on database file

### Database Access
View users directly (for debugging only):

```bash
sqlite3 data/curriculum.db
sqlite> SELECT email, name, is_admin FROM users;
sqlite> .quit
```

## Security Disclosure

If you discover a security vulnerability:
1. Do NOT post publicly
2. Email IT security team
3. Include details and steps to reproduce
4. Allow time for patching before disclosure

Remember: This authentication system is designed for **internal university use only**. Do not deploy on public internet without implementing additional security measures.