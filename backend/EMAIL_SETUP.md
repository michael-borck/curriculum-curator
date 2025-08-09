# Email Service Setup

The application uses Brevo (formerly SendinBlue) for sending emails. This document explains how to configure email sending.

## Development Mode (Default)

By default, the application runs in **Email Development Mode** where emails are logged to the console instead of being sent. This allows you to develop and test without configuring SMTP.

### Enable Dev Mode
In your `.env` file:
```
EMAIL_DEV_MODE=true
```

When registering or resetting passwords, you'll see output like:
```
📧 [DEV MODE] Email Verification
To: jane.doe@curtin.edu.au
Name: Jane Doe
Verification Code: 123456
Expires in: 15 minutes
Subject: Welcome to Curriculum Curator - Verify Your Email
```

## Production Mode (Brevo SMTP)

To send real emails, you need to:

1. **Get Brevo SMTP Credentials**
   - Go to https://app.brevo.com/settings/keys/smtp
   - Generate an SMTP key (NOT an API key)
   - Note: The SMTP key is different from the API key

2. **Update .env Configuration**
   ```
   # Disable dev mode
   EMAIL_DEV_MODE=false
   
   # Brevo SMTP Configuration
   BREVO_API_KEY=your-smtp-password-here  # This is the SMTP password
   BREVO_SMTP_LOGIN=93b634001@smtp-brevo.com  # Your SMTP login
   BREVO_FROM_EMAIL=noreply@yourdomain.com
   BREVO_FROM_NAME=Your App Name
   ```

3. **Brevo SMTP Settings**
   - Host: `smtp-relay.brevo.com`
   - Port: `587`
   - Username: Your SMTP login (e.g., `93b634001@smtp-brevo.com`)
   - Password: Your SMTP password from step 1

## Troubleshooting

### Authentication Failed (535 error)
- You're using an API key instead of SMTP key
- The SMTP key is invalid or expired
- Your Brevo account doesn't have SMTP enabled

### Test Email Configuration
Run the debug script:
```bash
python debug_email.py
```

This will test your email configuration and show any errors.

## Email Templates

The application sends these emails:
1. **Verification Email** - 6-digit code for email verification
2. **Password Reset** - 6-digit code for password reset
3. **Welcome Email** - Sent after successful verification

All templates are inline HTML with responsive design and fallback plain text versions.