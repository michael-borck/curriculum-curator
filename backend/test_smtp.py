#!/usr/bin/env python3
"""
Quick SMTP connection test
Tests your email configuration without the full application
"""

import smtplib
import ssl
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    print("✅ Loaded .env file")
else:
    print("❌ No .env file found")
    sys.exit(1)

# Get configuration
smtp_host = os.getenv("SMTP_HOST")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_username = os.getenv("SMTP_USERNAME")
smtp_password = os.getenv("SMTP_PASSWORD")
use_ssl = os.getenv("USE_SSL", "false").lower() == "true"
use_tls = os.getenv("USE_TLS", "true").lower() == "true"
from_email = os.getenv("FROM_EMAIL")

print("\n📧 Email Configuration:")
print(f"   Host: {smtp_host}")
print(f"   Port: {smtp_port}")
print(f"   Username: {smtp_username}")
print(f"   From: {from_email}")
print(f"   SSL: {use_ssl}")
print(f"   TLS: {use_tls}")

if not all([smtp_host, smtp_username, smtp_password]):
    print("\n❌ Missing required configuration")
    sys.exit(1)

print("\n🔍 Testing SMTP connection...")

try:
    # Create SMTP connection based on security settings
    if use_ssl:
        # Port 465 - SSL from the start
        print("   Using SSL connection (port 465 typical)...")
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
    else:
        # Port 587 or 25 - Start plain, then STARTTLS if needed
        print(f"   Using {'TLS' if use_tls else 'plain'} connection...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        if use_tls:
            print("   Starting TLS...")
            context = ssl.create_default_context()
            server.starttls(context=context)

    print("   Logging in...")
    server.login(smtp_username, smtp_password)

    print("\n✅ SMTP connection successful!")

    # Ask if user wants to send a test email
    send_test = input("\nSend a test email? (y/N): ").strip().lower() == "y"

    if send_test:
        to_email = input("Recipient email: ").strip()
        if to_email:
            message = MIMEMultipart()
            message["From"] = from_email or smtp_username
            message["To"] = to_email
            message["Subject"] = "Test Email from Curriculum Curator"

            body = """
            This is a test email from your Curriculum Curator installation.
            
            If you received this email, your SMTP configuration is working correctly!
            
            Configuration used:
            - Host: {}
            - Port: {}
            - Security: {}
            """.format(
                smtp_host,
                smtp_port,
                "SSL" if use_ssl else "TLS" if use_tls else "Plain",
            )

            message.attach(MIMEText(body, "plain"))

            print(f"\n📨 Sending test email to {to_email}...")
            server.sendmail(from_email or smtp_username, to_email, message.as_string())
            print("✅ Test email sent successfully!")

    server.quit()

except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication failed: {e}")
    print("\n💡 Tips:")
    print("   - Check your username and password")
    print("   - For Gmail, use an App Password, not your regular password")
    print("   - Some providers require app-specific passwords")

except smtplib.SMTPConnectError as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n💡 Tips:")
    print("   - Check your SMTP host and port")
    print("   - Port 465 typically uses SSL")
    print("   - Port 587 typically uses TLS")
    print("   - Check firewall settings")

except smtplib.SMTPServerDisconnected as e:
    print(f"\n❌ Server disconnected: {e}")
    print("\n💡 Tips:")
    print("   - Try switching between SSL and TLS")
    print("   - Port 465 → USE_SSL=true, USE_TLS=false")
    print("   - Port 587 → USE_SSL=false, USE_TLS=true")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 50)
