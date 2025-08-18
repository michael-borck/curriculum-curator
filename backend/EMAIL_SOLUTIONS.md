# Email Delivery Solutions for University Domains

## Problem
University email systems (especially Outlook/Office 365) often block transactional email services like Brevo because:
- They're commonly used for marketing emails
- SPF/DKIM/DMARC records may not align with university expectations
- IP reputation of shared sending pools
- Content filtering rules

## Solutions

### 1. ✅ Development Bypass (Implemented)
- Auto-verifies users from `@curtin.edu.au` domains
- Edit `/backend/app/core/dev_config.py` to add more domains
- Users from these domains skip email verification entirely

### 2. Use University SMTP Server (Recommended)
Contact your IT department to get SMTP credentials for the university mail server:

```python
# In .env file
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.curtin.edu.au  # Or your university SMTP
SMTP_PORT=587
SMTP_USERNAME=your-service-account@curtin.edu.au
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
EMAIL_FROM_ADDRESS=noreply@curtin.edu.au
EMAIL_FROM_NAME=Curriculum Curator
```

Then update `/backend/app/services/email_service.py` to use SMTP directly:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_smtp_email(to_email: str, subject: str, html_content: str):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
    msg['To'] = to_email
    
    msg.attach(MIMEText(html_content, 'html'))
    
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
```

### 3. Alternative Verification Methods

#### A. Admin Manual Verification
Add an admin endpoint to manually verify users:

```python
@router.post("/admin/verify-user/{user_id}")
async def admin_verify_user(
    user_id: UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    user.is_verified = True
    db.commit()
    
    return {"message": f"User {user.email} verified by admin"}
```

#### B. Magic Link Instead of Code
Instead of 6-digit codes, use unique verification links that work better with spam filters:

```python
# Generate unique token
verification_token = secrets.token_urlsafe(32)

# Email contains link like:
verification_link = f"https://your-domain.com/verify?token={verification_token}"
```

#### C. Alternative Channels
- **Microsoft Teams Webhook**: Send verification codes via Teams
- **SMS**: Use Twilio for SMS verification
- **QR Code**: Display QR code that users scan with authenticator app

### 4. Email Service Alternatives Better for Universities

#### Amazon SES (Recommended)
- Better reputation with educational institutions
- Can use dedicated IP
- More control over sending configuration

```python
# pip install boto3
import boto3

ses_client = boto3.client(
    'ses',
    region_name='us-east-1',
    aws_access_key_id='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET'
)

ses_client.send_email(
    Source='noreply@your-domain.edu.au',
    Destination={'ToAddresses': [user_email]},
    Message={
        'Subject': {'Data': subject},
        'Body': {'Html': {'Data': html_content}}
    }
)
```

#### SendGrid Education Program
- Free credits for educational institutions
- Better deliverability to .edu domains
- Dedicated IP options

#### Postmark
- Focused on transactional email only
- Better reputation than marketing-focused services
- Excellent deliverability

### 5. Whitelist Configuration
Ask your IT department to:
1. Whitelist Brevo's IP ranges
2. Add Brevo to allowed senders
3. Create mail flow rule to bypass spam filtering for your sender address

Brevo IP ranges to whitelist:
- Check: https://help.brevo.com/hc/en-us/articles/360019522479

### 6. Improve Email Deliverability

#### SPF/DKIM/DMARC Setup
```dns
; SPF Record
v=spf1 include:spf.brevo.com include:curtin.edu.au ~all

; DKIM - Get from Brevo dashboard
default._domainkey IN TXT "v=DKIM1; k=rsa; p=MIGfMA0..."

; DMARC
_dmarc IN TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@your-domain.edu.au"
```

#### Email Content Best Practices
- Avoid spam trigger words
- Include plain text version
- Use proper headers
- Include unsubscribe link (even for transactional)
- Keep HTML simple

### 7. Monitoring & Debugging

Add email tracking to see what's happening:

```python
# In email_service.py
async def send_verification_email_with_tracking(user: User, code: str):
    # Log attempt
    logger.info(f"Attempting to send verification to {user.email}")
    
    try:
        result = await send_email(...)
        
        # Log success with message ID
        logger.info(f"Email sent successfully to {user.email}, ID: {result.message_id}")
        
        # Store in database for tracking
        db.add(EmailLog(
            user_id=user.id,
            email_type="verification",
            status="sent",
            message_id=result.message_id,
            sent_at=datetime.utcnow()
        ))
        
    except Exception as e:
        logger.error(f"Failed to send to {user.email}: {str(e)}")
        
        # Store failure
        db.add(EmailLog(
            user_id=user.id,
            email_type="verification", 
            status="failed",
            error_message=str(e),
            attempted_at=datetime.utcnow()
        ))
```

## Immediate Action Items

1. **For Development**: The bypass is already implemented for `@curtin.edu.au`
2. **Contact IT**: Request SMTP credentials or IP whitelisting
3. **Consider Alternative**: Switch to university SMTP or Amazon SES
4. **Add Admin Tool**: Implement manual verification endpoint for stuck users

## Testing Email Delivery

Use these tools to test:
- https://www.mail-tester.com/ - Check spam score
- https://mxtoolbox.com/ - Check DNS/SPF/DKIM
- https://www.gmass.co/deliverability - Test deliverability

## Environment Variables for Alternative Providers

```bash
# University SMTP
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.curtin.edu.au
SMTP_PORT=587
SMTP_USERNAME=service-account@curtin.edu.au
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true

# Amazon SES
EMAIL_PROVIDER=ses
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# SendGrid
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG...

# Development bypass (auto-verify these domains)
BYPASS_VERIFICATION_DOMAINS=@curtin.edu.au,@localhost
DEV_MODE=true
```