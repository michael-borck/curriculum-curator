#!/usr/bin/env python3
"""
Quick test script to verify Brevo email configuration
Run with: python test_email.py
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.email_service import email_service


async def test_email_service():
    """Test the email service configuration"""

    print("🧪 Testing Brevo Email Service Configuration")
    print(f"📧 SMTP Host: {settings.BREVO_SMTP_HOST}")
    print(f"📧 SMTP Port: {settings.BREVO_SMTP_PORT}")
    print(f"📧 From Email: {settings.BREVO_FROM_EMAIL}")
    print(f"📧 From Name: {settings.BREVO_FROM_NAME}")

    if (
        not settings.BREVO_API_KEY
        or settings.BREVO_API_KEY == "your_brevo_api_key_here"
    ):
        print("❌ BREVO_API_KEY not configured! Please update your .env file.")
        print("   Get your API key from: https://app.brevo.com/settings/keys/api")
        return False

    print(f"🔑 API Key: {'✅ Configured' if settings.BREVO_API_KEY else '❌ Missing'}")

    # Test email address - change this to your email
    test_email = input(
        "Enter your email address to test (or press Enter to skip): "
    ).strip()

    if not test_email:
        print("⏭️  Skipping email test")
        return True

    # Create a test user object
    test_user = type(
        "TestUser", (), {"id": "12345", "name": "Test User", "email": test_email}
    )()

    print(f"\n📤 Sending test verification email to {test_email}...")

    try:
        success = await email_service.send_verification_email(
            user=test_user, verification_code="123456", expires_minutes=15
        )

        if success:
            print("✅ Test email sent successfully!")
            print("📬 Check your inbox (and spam folder) for the verification email")
            return True
        print("❌ Failed to send test email")
        return False

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    result = asyncio.run(test_email_service())
    print("=" * 60)

    if result:
        print("🎉 Email service is configured correctly!")
    else:
        print("🔧 Please check your Brevo configuration and try again.")
