#!/usr/bin/env python3
"""
Email Configuration Setup Tool
Helps configure and test email settings for Curriculum Curator
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.smtp_config import (
    EmailProvider,
    GmailHelper,
    PersonalSMTPHelper,
)
from app.models import User
from app.services.email_service import EmailService


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(text.center(60))
    print("=" * 60)


def print_section(text: str):
    """Print a section header"""
    print(f"\n{text}")
    print("-" * len(text))


class EmailSetup:
    """Interactive email configuration setup"""

    def __init__(self):
        self.env_file = Path(".env")
        self.env_vars = {}
        self.load_existing_env()

    def load_existing_env(self):
        """Load existing .env file"""
        if self.env_file.exists():
            with self.env_file.open() as f:
                for line in f:
                    line_content = line.strip()
                    if (
                        line_content
                        and not line_content.startswith("#")
                        and "=" in line_content
                    ):
                        key, value = line_content.split("=", 1)
                        self.env_vars[key.strip()] = value.strip().strip('"').strip("'")

    def save_env(self):
        """Save environment variables to .env file"""
        # Read existing file to preserve other settings
        existing_lines = []
        email_keys = {
            "EMAIL_PROVIDER",
            "SMTP_HOST",
            "SMTP_PORT",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
            "GMAIL_APP_PASSWORD",
            "FROM_EMAIL",
            "FROM_NAME",
            "USE_TLS",
            "USE_SSL",
            "BREVO_API_KEY",
            "SENDGRID_API_KEY",
            "MAILGUN_API_KEY",
            "MAILGUN_DOMAIN",
            "POSTMARK_SERVER_TOKEN",
            "EMAIL_DEV_MODE",
            "TEST_EMAIL_RECIPIENT",
        }

        if self.env_file.exists():
            with self.env_file.open() as f:
                for line in f:
                    # Skip email-related settings - we'll add them at the end
                    if any(line.startswith(key) for key in email_keys):
                        continue
                    existing_lines.append(line.rstrip())

        # Add email configuration section
        existing_lines.append("")
        existing_lines.append("# Email Configuration (configured by setup_email.py)")
        existing_lines.append("# =" * 30)

        for key in sorted(email_keys):
            if key in self.env_vars:
                value = self.env_vars[key]
                # Quote values with spaces
                if " " in value and not value.startswith(('"', "'")):
                    value = f'"{value}"'
                existing_lines.append(f"{key}={value}")

        # Write back to file
        with self.env_file.open("w") as f:
            f.write("\n".join(existing_lines) + "\n")

        print(f"✅ Configuration saved to {self.env_file}")

    def choose_provider(self) -> EmailProvider:
        """Interactive provider selection"""
        print_section("Choose Email Provider")

        providers = [
            ("1", EmailProvider.GMAIL, "Gmail (recommended for personal use)"),
            ("2", EmailProvider.CUSTOM_SMTP, "Custom SMTP Server (your own domain)"),
            ("3", EmailProvider.BREVO, "Brevo (formerly SendinBlue)"),
            ("4", EmailProvider.SENDGRID, "SendGrid"),
            ("5", EmailProvider.MAILGUN, "Mailgun"),
            ("6", EmailProvider.POSTMARK, "Postmark"),
            ("7", EmailProvider.DEV_MODE, "Development Mode (console output only)"),
        ]

        for num, _, desc in providers:
            print(f"  {num}. {desc}")

        while True:
            choice = input("\nSelect provider (1-7): ").strip()
            for num, provider, _ in providers:
                if choice == num:
                    return provider
            print("❌ Invalid choice. Please select 1-7.")

    def configure_gmail(self):
        """Configure Gmail settings"""
        print_header("Gmail Configuration")

        print(GmailHelper.get_setup_instructions())

        print_section("Enter Gmail Settings")

        email = input("Gmail address: ").strip()
        if not email:
            print("❌ Email address is required")
            return False

        print("\n📝 App Password (16 characters, spaces will be removed)")
        print("   Get one at: https://myaccount.google.com/apppasswords")
        app_password = input("App Password: ").strip().replace(" ", "")

        if not app_password:
            print("❌ App password is required")
            return False

        # Validate configuration
        valid, message = GmailHelper.validate_config(email, app_password)
        if not valid:
            print(f"❌ {message}")
            return False

        print(f"✅ {message}")

        # Optional settings
        from_name = input("From Name (default: Curriculum Curator): ").strip()

        # Save configuration
        self.env_vars["EMAIL_PROVIDER"] = "gmail"
        self.env_vars["SMTP_USERNAME"] = email
        self.env_vars["GMAIL_APP_PASSWORD"] = app_password
        self.env_vars["FROM_EMAIL"] = email
        self.env_vars["FROM_NAME"] = from_name or "Curriculum Curator"
        self.env_vars["EMAIL_DEV_MODE"] = "false"

        return True

    def configure_custom_smtp(self):
        """Configure custom SMTP server"""
        print_header("Custom SMTP Server Configuration")

        print(PersonalSMTPHelper.get_setup_instructions())

        print_section("Enter SMTP Settings")

        # Check if we can guess settings from email domain
        email = input("Your email address: ").strip()
        if "@" in email:
            domain = email.split("@")[1]
            suggested = PersonalSMTPHelper.test_common_providers(domain)
            if suggested:
                print(f"\n💡 Suggested settings for {domain}:")
                for key, value in suggested.items():
                    if key != "note":
                        print(f"   {key}: {value}")
                if "note" in suggested:
                    print(f"   ⚠️ {suggested['note']}")

        host = input("\nSMTP Host: ").strip()
        if not host:
            print("❌ SMTP host is required")
            return False

        port = input("SMTP Port (default: 587): ").strip() or "587"
        username = input("SMTP Username (often your email): ").strip()
        password = input("SMTP Password: ").strip()

        if not username or not password:
            print("❌ Username and password are required")
            return False

        # Security settings
        print("\nSecurity Settings:")
        use_tls = input("Use TLS/STARTTLS? (Y/n): ").strip().lower() != "n"
        use_ssl = False
        if not use_tls:
            use_ssl = input("Use SSL? (y/N): ").strip().lower() == "y"

        # Email settings
        from_email = input(f"From Email (default: {email}): ").strip() or email
        from_name = input("From Name (default: Curriculum Curator): ").strip()

        # Save configuration
        self.env_vars["EMAIL_PROVIDER"] = "custom"
        self.env_vars["SMTP_HOST"] = host
        self.env_vars["SMTP_PORT"] = port
        self.env_vars["SMTP_USERNAME"] = username
        self.env_vars["SMTP_PASSWORD"] = password
        self.env_vars["FROM_EMAIL"] = from_email
        self.env_vars["FROM_NAME"] = from_name or "Curriculum Curator"
        self.env_vars["USE_TLS"] = str(use_tls).lower()
        self.env_vars["USE_SSL"] = str(use_ssl).lower()
        self.env_vars["EMAIL_DEV_MODE"] = "false"

        return True

    def configure_brevo(self):
        """Configure Brevo settings"""
        print_header("Brevo Configuration")

        print("\n📝 Brevo Setup:")
        print("1. Sign up at https://www.brevo.com")
        print("2. Go to SMTP & API → SMTP settings")
        print("3. Generate an SMTP key")

        print_section("Enter Brevo Settings")

        api_key = input("Brevo SMTP Key: ").strip()
        if not api_key:
            print("❌ API key is required")
            return False

        login = input("SMTP Login (e.g., 93b634001@smtp-brevo.com): ").strip()
        if not login:
            print("❌ SMTP login is required")
            return False

        from_email = input("From Email: ").strip()
        from_name = input("From Name (default: Curriculum Curator): ").strip()

        # Save configuration
        self.env_vars["EMAIL_PROVIDER"] = "brevo"
        self.env_vars["BREVO_API_KEY"] = api_key
        self.env_vars["SMTP_USERNAME"] = login
        self.env_vars["FROM_EMAIL"] = from_email
        self.env_vars["FROM_NAME"] = from_name or "Curriculum Curator"
        self.env_vars["EMAIL_DEV_MODE"] = "false"

        return True

    def configure_dev_mode(self):
        """Configure development mode"""
        print_header("Development Mode")

        print("\n📝 Development mode will:")
        print("  • Print emails to console instead of sending")
        print("  • No SMTP configuration required")
        print("  • Perfect for testing without email setup")

        self.env_vars["EMAIL_PROVIDER"] = "dev"
        self.env_vars["EMAIL_DEV_MODE"] = "true"

        # Optional test recipient
        test_email = input("\nTest recipient email (optional): ").strip()
        if test_email:
            self.env_vars["TEST_EMAIL_RECIPIENT"] = test_email

        return True

    async def test_configuration(self):
        """Test email configuration"""
        print_header("Testing Email Configuration")

        # Reload environment with new settings
        for key, value in self.env_vars.items():
            os.environ[key] = value

        # Initialize email service
        email_service = EmailService()

        # Test SMTP connection
        print("\n🔍 Testing SMTP connection...")
        success, message = email_service.test_smtp_connection()

        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            return False

        # Send test email if requested
        if email_service.smtp_config.provider != EmailProvider.DEV_MODE:
            send_test = input("\nSend a test email? (y/N): ").strip().lower() == "y"
            if send_test:
                test_email = input("Test email recipient: ").strip()
                if test_email:
                    # Create dummy user for test
                    test_user = User(email=test_email, name="Test User", id=1)

                    print("\n📧 Sending test verification email...")
                    success = await email_service.send_verification_email(
                        test_user, "TEST123", 15
                    )

                    if success:
                        print("✅ Test email sent successfully!")
                        print(
                            f"   Check {test_email} for the verification code: TEST123"
                        )
                    else:
                        print("❌ Failed to send test email")
                        return False

        return True

    async def run(self):
        """Run the setup process"""
        print_header("Email Configuration Setup")
        print("Configure email settings for Curriculum Curator")

        # Show current configuration
        current_provider = self.env_vars.get("EMAIL_PROVIDER", "not configured")
        print(f"\nCurrent provider: {current_provider}")

        # Choose provider
        provider = self.choose_provider()

        # Configure based on provider
        success = False
        if provider == EmailProvider.GMAIL:
            success = self.configure_gmail()
        elif provider == EmailProvider.CUSTOM_SMTP:
            success = self.configure_custom_smtp()
        elif provider == EmailProvider.BREVO:
            success = self.configure_brevo()
        elif provider == EmailProvider.DEV_MODE:
            success = self.configure_dev_mode()
        else:
            print(f"❌ Configuration for {provider.value} not yet implemented")
            return

        if not success:
            print("\n❌ Configuration failed")
            return

        # Save configuration
        self.save_env()

        # Test configuration
        await self.test_configuration()

        print_header("Setup Complete!")
        print("\n📝 Next steps:")
        print("1. Restart your backend server to use new settings")
        print("2. Register a new user to test email verification")
        print("3. Check setup_email.log for any issues")

        if provider == EmailProvider.GMAIL:
            print("\n⚠️ Gmail Security Note:")
            print("  If emails aren't sending, check:")
            print("  • 2-Factor Authentication is enabled")
            print("  • App Password (not regular password) is used")
            print("  • Less secure app access is NOT needed with App Passwords")


async def main():
    """Main entry point"""
    setup = EmailSetup()
    await setup.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
