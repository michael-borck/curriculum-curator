# Email Configuration Guide

This guide explains how to set up and configure the email service for Curriculum Curator.

## Quick Start

1. **Get a Brevo Account** (free tier is sufficient):
   - Sign up at https://www.brevo.com
   - Verify your sender domain/email
   - Get your API key from Settings → Keys → API Keys

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your values:
   # BREVO_API_KEY=your-actual-api-key
   # SENDER_EMAIL=noreply@your-domain.edu.au
   ```

3. **Test Email**:
   - Register a new account
   - Check console output for verification code (if email fails)
   - Check your email for the verification message

## Email Features

### 1. Email Verification
When users register, they receive an email with:
- **6-digit verification code** - for cross-device workflows
- **Verification link** - for same-device convenience

Both methods work equally well. The code is especially useful when:
- Registering on a shared/lab computer
- Email is checked on a different device (phone)
- Users can't or don't want to click links

### 2. Password Reset
Users can reset their own passwords:
- Click "Forgot password?" on login page
- Enter registered email address
- Receive reset link (valid for 1 hour)
- Set new password

### 3. Development Mode
When `BREVO_API_KEY` is not set:
- Email service runs in "disabled" mode
- Verification codes print to console
- Reset tokens print to console
- Perfect for local development

## Configuration Options

### Environment Variables

```env
# Required for email functionality
BREVO_API_KEY=xkeysib-xxx...

# Sender configuration
SENDER_EMAIL=noreply@curtin.edu.au
SENDER_NAME=Curriculum Curator

# Application URL (for links in emails)
APP_BASE_URL=https://curriculum.curtin.edu.au

# Development: use localhost
APP_BASE_URL=http://localhost:5000
```

### Domain Whitelisting

Edit `core/auth.py` to change allowed email domains:

```python
# Single domain (default)
WHITELISTED_DOMAINS = ['@curtin.edu.au']

# Multiple domains
WHITELISTED_DOMAINS = ['@curtin.edu.au', '@murdoch.edu.au', '@uwa.edu.au']

# Any .edu.au domain
WHITELISTED_DOMAINS = ['.edu.au']
```

## Email Templates

The email templates are defined in `core/email_service.py`. They include:

### Verification Email
- Subject: "Verify your Curriculum Curator account"
- Contains 6-digit code and verification link
- 24-hour expiration
- Mobile-responsive design

### Password Reset Email
- Subject: "Reset your Curriculum Curator password"
- Contains reset link only (no code)
- 1-hour expiration
- Security notice about ignoring if not requested

## Troubleshooting

### Email Not Sending

1. **Check API Key**:
   ```bash
   echo $BREVO_API_KEY  # Should show your key
   ```

2. **Check Sender Verification**:
   - Log into Brevo dashboard
   - Go to Senders & IP
   - Ensure your sender email is verified

3. **Check Console Output**:
   - Look for "Email sent successfully" or error messages
   - In dev mode, look for "Email service disabled" messages

### Emails Going to Spam

1. **Sender Reputation**:
   - Use an official university email domain
   - Verify domain with Brevo (SPF/DKIM records)

2. **Content**:
   - Avoid spam trigger words
   - Keep templates simple and professional

3. **User Education**:
   - Tell users to check spam folder
   - Ask them to mark as "not spam"

### Rate Limits

Brevo free tier limits:
- 300 emails/day
- No hourly limit

For higher volume:
- Upgrade Brevo plan
- Implement rate limiting in code
- Use batch sending for announcements

## Security Considerations

1. **Never Log Sensitive Data**:
   - Don't log full tokens or passwords
   - Don't log complete email addresses in production

2. **Token Security**:
   - Tokens are single-use
   - Tokens expire (configurable)
   - Tokens are cryptographically random

3. **Email Enumeration**:
   - Password reset shows same message for any email
   - Prevents discovering registered emails

## Testing

### Manual Testing

1. **Registration Flow**:
   ```
   - Register with valid @curtin.edu.au email
   - Check email received
   - Try both verification methods
   - Confirm login works
   ```

2. **Password Reset Flow**:
   ```
   - Click "Forgot password?"
   - Enter registered email
   - Check reset email received
   - Reset password
   - Confirm old password no longer works
   - Confirm new password works
   ```

### Automated Testing

See `tests/test_email.py` for examples:
```python
def test_verification_email():
    # Test with mocked email service
    pass

def test_cross_device_flow():
    # Test code-based verification
    pass
```

## Future Enhancements

1. **Email Notifications**:
   - Login from new device
   - Important content updates
   - Admin announcements

2. **Template Customization**:
   - University branding
   - Multi-language support
   - A/B testing templates

3. **Alternative Channels**:
   - SMS verification option
   - Microsoft Teams integration
   - Push notifications