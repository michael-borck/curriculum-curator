# Email Configuration Guide

This guide will help you set up proper email validation for Curriculum Curator using Gmail, your personal SMTP server, or other email providers.

## Quick Setup

Run the interactive setup tool:

```bash
cd backend
./setup_email.py
```

This will guide you through configuring your email provider.

## Supported Providers

### 1. Gmail (Recommended for Personal Use)

Gmail is the easiest to set up if you have a Gmail account.

**Prerequisites:**
- Gmail account with 2-Factor Authentication enabled
- App Password (not your regular password)

**Setup Steps:**
1. Enable 2FA: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Run `./setup_email.py` and select Gmail
4. Enter your Gmail address and App Password

### 2. Personal SMTP Server

Use your own domain's email server.

**Required Information:**
- SMTP server hostname
- SMTP port (usually 587)
- Username and password
- Security settings (TLS/SSL)

**Common SMTP Settings:**
- **Outlook/Hotmail**: smtp-mail.outlook.com:587 (TLS)
- **Yahoo**: smtp.mail.yahoo.com:587 (TLS)
- **iCloud**: smtp.mail.me.com:587 (TLS)
- **Zoho**: smtp.zoho.com:587 (TLS)

### 3. Brevo (Free Tier Available)

Good for production use with free tier.

**Setup Steps:**
1. Sign up at https://www.brevo.com
2. Go to SMTP & API → SMTP settings
3. Generate SMTP key
4. Run `./setup_email.py` and select Brevo

### 4. Development Mode

For testing without actual email sending.

**Features:**
- Prints emails to console
- No SMTP configuration needed
- Perfect for development

## Manual Configuration

If you prefer to configure manually, add these to your `.env` file:

### Gmail Configuration
```env
EMAIL_PROVIDER=gmail
SMTP_USERNAME=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Your Name
EMAIL_DEV_MODE=false
```

### Custom SMTP Configuration
```env
EMAIL_PROVIDER=custom
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=you@yourdomain.com
SMTP_PASSWORD=your-password
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Your Organization
USE_TLS=true
USE_SSL=false
EMAIL_DEV_MODE=false
```

### Development Mode
```env
EMAIL_PROVIDER=dev
EMAIL_DEV_MODE=true
```

## Testing Your Configuration

After setup, test your configuration:

```bash
# Run the setup tool and choose to send a test email
./setup_email.py

# Or test via Python
python -c "
from app.services.email_service import EmailService
service = EmailService()
success, message = service.test_smtp_connection()
print(message)
"
```

## Troubleshooting

### Gmail Issues

**"Authentication failed"**
- Ensure 2FA is enabled on your Google account
- Use App Password, not your regular password
- App Password should be 16 characters (no spaces)

**"Less secure app access"**
- NOT needed when using App Passwords
- App Passwords are the secure method

### SMTP Connection Issues

**"Connection refused"**
- Check firewall settings
- Verify SMTP host and port
- Try alternative ports: 25, 465, 587, 2525

**"Certificate verification failed"**
- Set `VALIDATE_CERTS=false` in .env (less secure)
- Or install proper certificates

### University/Corporate Networks

If your IT department blocks external SMTP:

1. **Use Development Mode** for testing
2. **Request SMTP access** from IT
3. **Use internal SMTP server** if available
4. **Consider API-based providers** (SendGrid, Mailgun)

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for all secrets
3. **Enable 2FA** on email accounts when possible
4. **Use App Passwords** instead of regular passwords
5. **Rotate credentials** regularly
6. **Monitor for** unauthorized access

## Alternative Solutions

If email delivery continues to be problematic:

### Local Development
- Use development mode (console output)
- Use MailCatcher or MailHog for local SMTP testing

### Production Alternatives
- Implement SMS verification (Twilio)
- Use OAuth providers (Google, GitHub)
- Implement magic links instead of codes
- Use QR codes for mobile verification

## Getting Help

If you encounter issues:

1. Check the logs: `tail -f backend.log`
2. Run connection test: `./setup_email.py`
3. Verify credentials are correct
4. Check spam folders for test emails
5. Contact your email provider's support

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| EMAIL_PROVIDER | Provider type | gmail, custom, brevo, dev |
| SMTP_HOST | SMTP server hostname | smtp.gmail.com |
| SMTP_PORT | SMTP server port | 587 |
| SMTP_USERNAME | SMTP username | user@example.com |
| SMTP_PASSWORD | SMTP password | your-password |
| GMAIL_APP_PASSWORD | Gmail App Password | 16-char-password |
| FROM_EMAIL | Sender email | noreply@example.com |
| FROM_NAME | Sender name | Curriculum Curator |
| USE_TLS | Enable TLS | true |
| USE_SSL | Enable SSL | false |
| EMAIL_DEV_MODE | Development mode | false |
| TEST_EMAIL_RECIPIENT | Test mode recipient | test@example.com |

## Next Steps

After configuring email:

1. Restart the backend server
2. Register a new user to test verification
3. Check that verification emails are received
4. Test password reset functionality

Remember: The first user to register becomes an admin automatically!