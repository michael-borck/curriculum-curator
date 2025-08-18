"""
Email service using Brevo (formerly SendinBlue) via fastapi-mail
"""

import os
import secrets
import smtplib
import string
import traceback
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Template

from app.core.config import settings
from app.core.smtp_config import (
    EmailProvider,
    GmailHelper,
    PersonalSMTPHelper,
    SMTPConfig,
)
from app.models import User


class EmailService:
    """Flexible email service supporting multiple providers"""

    def __init__(self):
        """Initialize email service with flexible provider configuration"""
        self.smtp_config = self._load_smtp_config()
        self.fast_mail = None
        self.template_dir = str(Path(__file__).parent / "../templates/email")

        # Initialize FastMail if not in dev mode
        if self.smtp_config.provider != EmailProvider.DEV_MODE:
            self._initialize_fastmail()

    def _load_smtp_config(self) -> SMTPConfig:
        """Load SMTP configuration from environment variables"""
        provider = os.getenv("EMAIL_PROVIDER", "dev").lower()

        # Map provider string to enum
        provider_map = {
            "gmail": EmailProvider.GMAIL,
            "brevo": EmailProvider.BREVO,
            "custom": EmailProvider.CUSTOM_SMTP,
            "sendgrid": EmailProvider.SENDGRID,
            "mailgun": EmailProvider.MAILGUN,
            "postmark": EmailProvider.POSTMARK,
            "dev": EmailProvider.DEV_MODE,
        }

        config = SMTPConfig(
            provider=provider_map.get(provider, EmailProvider.DEV_MODE),
            # Common SMTP settings
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            # Email settings
            from_email=os.getenv("FROM_EMAIL", settings.BREVO_FROM_EMAIL),
            from_name=os.getenv("FROM_NAME", settings.BREVO_FROM_NAME),
            # Security settings
            use_tls=os.getenv("USE_TLS", "true").lower() == "true",
            use_ssl=os.getenv("USE_SSL", "false").lower() == "true",
            validate_certs=os.getenv("VALIDATE_CERTS", "true").lower() == "true",
            # Provider-specific settings
            gmail_app_password=os.getenv("GMAIL_APP_PASSWORD"),
            brevo_api_key=os.getenv("BREVO_API_KEY", settings.BREVO_API_KEY),
            sendgrid_api_key=os.getenv("SENDGRID_API_KEY"),
            mailgun_api_key=os.getenv("MAILGUN_API_KEY"),
            mailgun_domain=os.getenv("MAILGUN_DOMAIN"),
            postmark_server_token=os.getenv("POSTMARK_SERVER_TOKEN"),
            # Development/Testing
            dev_mode=os.getenv("EMAIL_DEV_MODE", str(settings.EMAIL_DEV_MODE)).lower()
            == "true",
            test_recipient=os.getenv("TEST_EMAIL_RECIPIENT"),
            # Rate limiting
            rate_limit_per_hour=int(os.getenv("EMAIL_RATE_LIMIT_PER_HOUR", "100")),
            rate_limit_per_day=int(os.getenv("EMAIL_RATE_LIMIT_PER_DAY", "1000")),
        )

        # Print configuration status
        if config.provider == EmailProvider.DEV_MODE or config.dev_mode:
            print("📧 Email Service: Running in DEVELOPMENT mode (console output only)")
        elif config.is_configured():
            print(f"✅ Email Service: Configured with {config.provider.value} provider")
        else:
            print("⚠️ Email Service: Not properly configured, falling back to dev mode")
            config.provider = EmailProvider.DEV_MODE
            config.dev_mode = True

        return config

    def _initialize_fastmail(self):
        """Initialize FastMail with current configuration"""
        try:
            smtp_settings = self.smtp_config.get_smtp_settings()

            self.config = ConnectionConfig(
                MAIL_USERNAME=smtp_settings["username"],
                MAIL_PASSWORD=smtp_settings["password"],
                MAIL_FROM=self.smtp_config.from_email,
                MAIL_FROM_NAME=self.smtp_config.from_name,
                MAIL_PORT=smtp_settings["port"],
                MAIL_SERVER=smtp_settings["host"],
                MAIL_STARTTLS=smtp_settings["use_tls"],
                MAIL_SSL_TLS=smtp_settings["use_ssl"],
                USE_CREDENTIALS=bool(smtp_settings["username"]),
                VALIDATE_CERTS=self.smtp_config.validate_certs,
                TEMPLATE_FOLDER=self.template_dir,
            )

            self.fast_mail = FastMail(self.config)

        except Exception as e:
            print(f"❌ Failed to initialize email service: {e}")
            self.smtp_config.provider = EmailProvider.DEV_MODE
            self.smtp_config.dev_mode = True

    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """Generate a random verification code"""
        digits = string.digits
        return "".join(secrets.choice(digits) for _ in range(length))

    def get_verification_email_template(self) -> str:
        """Get email verification template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Welcome to {{ app_name }}</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .code-box { background: #fff; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }
                .code { font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 4px; }
                .footer { text-align: center; margin-top: 20px; color: #666; font-size: 12px; }
                .btn { display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {{ app_name }}!</h1>
                    <p>Please verify your email address</p>
                </div>
                <div class="content">
                    <p>Hello {{ user_name }},</p>
                    <p>Thank you for registering with {{ app_name }}. To complete your registration and activate your account, please use the verification code below:</p>

                    <div class="code-box">
                        <div class="code">{{ verification_code }}</div>
                    </div>

                    <p><strong>Important:</strong> This code will expire in {{ expiry_minutes }} minutes for security reasons.</p>

                    <p>If you didn't create an account with us, please ignore this email.</p>

                    <p>Welcome aboard!<br>
                    The {{ app_name }} Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def get_password_reset_email_template(self) -> str:
        """Get password reset email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Password Reset - {{ app_name }}</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .code-box { background: #fff; border: 2px dashed #f5576c; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }
                .code { font-size: 32px; font-weight: bold; color: #f5576c; letter-spacing: 4px; }
                .footer { text-align: center; margin-top: 20px; color: #666; font-size: 12px; }
                .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin: 15px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                    <p>{{ app_name }}</p>
                </div>
                <div class="content">
                    <p>Hello {{ user_name }},</p>
                    <p>We received a request to reset the password for your {{ app_name }} account ({{ user_email }}).</p>

                    <div class="code-box">
                        <div class="code">{{ reset_code }}</div>
                    </div>

                    <div class="warning">
                        <strong>Security Notice:</strong> This reset code will expire in {{ expiry_minutes }} minutes. If you didn't request a password reset, please ignore this email and your password will remain unchanged.
                    </div>

                    <p>For security reasons, please:</p>
                    <ul>
                        <li>Do not share this code with anyone</li>
                        <li>Use this code only on the {{ app_name }} website</li>
                        <li>Contact support if you suspect unauthorized access</li>
                    </ul>

                    <p>Best regards,<br>
                    The {{ app_name }} Security Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated security message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def test_smtp_connection(self) -> tuple[bool, str]:
        """Test SMTP connection with current configuration"""
        if self.smtp_config.provider == EmailProvider.DEV_MODE:
            return True, "Development mode - no SMTP connection needed"

        try:
            smtp_settings = self.smtp_config.get_smtp_settings()

            # Create SMTP connection
            if smtp_settings["use_ssl"]:
                server = smtplib.SMTP_SSL(smtp_settings["host"], smtp_settings["port"])
            else:
                server = smtplib.SMTP(smtp_settings["host"], smtp_settings["port"])
                if smtp_settings["use_tls"]:
                    server.starttls()

            # Authenticate if credentials provided
            if smtp_settings["username"] and smtp_settings["password"]:
                server.login(smtp_settings["username"], smtp_settings["password"])

            server.quit()
            return (
                True,
                f"Successfully connected to {self.smtp_config.provider.value} SMTP server",
            )

        except smtplib.SMTPAuthenticationError as e:
            return False, f"Authentication failed: {e!s}. Check your credentials."
        except smtplib.SMTPConnectError as e:
            return False, f"Connection failed: {e!s}. Check server and port."
        except Exception as e:
            return False, f"Connection test failed: {e!s}"

    def get_setup_instructions(self) -> str:
        """Get setup instructions for current provider"""
        if self.smtp_config.provider == EmailProvider.GMAIL:
            return GmailHelper.get_setup_instructions()
        if self.smtp_config.provider == EmailProvider.CUSTOM_SMTP:
            return PersonalSMTPHelper.get_setup_instructions()
        return f"Setup instructions for {self.smtp_config.provider.value} provider"

    async def send_verification_email(
        self, user: User, verification_code: str, expires_minutes: int = 15
    ) -> bool:
        """Send email verification code to user"""
        # Development mode - log instead of sending
        if (
            self.smtp_config.dev_mode
            or self.smtp_config.provider == EmailProvider.DEV_MODE
        ):
            print("\n📧 [DEV MODE] Email Verification")
            print(f"To: {user.email}")
            print(f"Name: {user.name}")
            print(f"Verification Code: {verification_code}")
            print(f"Expires in: {expires_minutes} minutes")
            print(f"Subject: Welcome to {settings.APP_NAME} - Verify Your Email")
            print(f"Provider: {self.smtp_config.provider.value}\n")
            return True

        try:
            template = Template(self.get_verification_email_template())

            html_body = template.render(
                app_name=settings.APP_NAME,
                user_name=user.name,
                user_email=user.email,
                verification_code=verification_code,
                expiry_minutes=expires_minutes,
            )

            # Plain text version for email clients that don't support HTML
            text_body = f"""
Welcome to {settings.APP_NAME}!

Hello {user.name},

Thank you for registering with {settings.APP_NAME}. Please use this verification code to complete your registration:

Verification Code: {verification_code}

This code will expire in {expires_minutes} minutes.

If you didn't create an account with us, please ignore this email.

Welcome aboard!
The {settings.APP_NAME} Team
            """.strip()

            # Override recipient in test mode
            recipients = (
                [self.smtp_config.test_recipient]
                if self.smtp_config.test_recipient
                else [user.email]
            )

            message = MessageSchema(
                subject=f"Welcome to {settings.APP_NAME} - Verify Your Email",
                recipients=recipients,
                body=text_body,
                html=html_body,
                subtype=MessageType.html,
            )

            if self.fast_mail:
                await self.fast_mail.send_message(message)
                print(
                    f"✅ Verification email sent to {recipients[0]} via {self.smtp_config.provider.value}"
                )
                return True
            print("❌ Email service not initialized. Check configuration.")
            return False

        except Exception as e:
            print(f"❌ Failed to send verification email to {user.email}: {e}")
            print(f"Provider: {self.smtp_config.provider.value}")
            print("Full error traceback:")
            traceback.print_exc()

            # Provide helpful error messages for common issues
            if "authentication" in str(e).lower():
                print(
                    "\n💡 Tip: Check your email credentials. For Gmail, use an App Password."
                )
                if self.smtp_config.provider == EmailProvider.GMAIL:
                    print(
                        "   Visit https://myaccount.google.com/apppasswords to generate one."
                    )
            elif "connection" in str(e).lower():
                print(
                    "\n💡 Tip: Check your firewall settings and SMTP host/port configuration."
                )

            return False

    async def send_password_reset_email(
        self, user: User, reset_code: str, expires_minutes: int = 30
    ) -> bool:
        """Send password reset code to user"""
        # Development mode - log instead of sending
        if (
            self.smtp_config.dev_mode
            or self.smtp_config.provider == EmailProvider.DEV_MODE
        ):
            print("\n🔐 [DEV MODE] Password Reset Email")
            print(f"To: {user.email}")
            print(f"Name: {user.name}")
            print(f"Reset Code: {reset_code}")
            print(f"Expires in: {expires_minutes} minutes")
            print(f"Subject: Password Reset - {settings.APP_NAME}")
            print(f"Provider: {self.smtp_config.provider.value}\n")
            return True

        try:
            template = Template(self.get_password_reset_email_template())

            html_body = template.render(
                app_name=settings.APP_NAME,
                user_name=user.name,
                user_email=user.email,
                reset_code=reset_code,
                expiry_minutes=expires_minutes,
            )

            # Plain text version
            text_body = f"""
Password Reset Request - {settings.APP_NAME}

Hello {user.name},

We received a request to reset the password for your {settings.APP_NAME} account ({user.email}).

Reset Code: {reset_code}

This code will expire in {expires_minutes} minutes.

If you didn't request a password reset, please ignore this email.

Best regards,
The {settings.APP_NAME} Security Team
            """.strip()

            # Override recipient in test mode
            recipients = (
                [self.smtp_config.test_recipient]
                if self.smtp_config.test_recipient
                else [user.email]
            )

            message = MessageSchema(
                subject=f"Password Reset - {settings.APP_NAME}",
                recipients=recipients,
                body=text_body,
                html=html_body,
                subtype=MessageType.html,
            )

            if self.fast_mail:
                await self.fast_mail.send_message(message)
                print(
                    f"✅ Password reset email sent to {recipients[0]} via {self.smtp_config.provider.value}"
                )
                return True
            print("❌ Email service not initialized. Check configuration.")
            return False

        except Exception as e:
            print(f"❌ Failed to send password reset email to {user.email}: {e}")
            return False

    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email after successful verification"""
        # Development mode - log instead of sending
        if (
            self.smtp_config.dev_mode
            or self.smtp_config.provider == EmailProvider.DEV_MODE
        ):
            print("\n🎉 [DEV MODE] Welcome Email")
            print(f"To: {user.email}")
            print(f"Name: {user.name}")
            print(f"Subject: 🎉 Account Activated - Welcome to {settings.APP_NAME}!")
            print(f"Provider: {self.smtp_config.provider.value}\n")
            return True

        try:
            welcome_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Account Activated - {{ app_name }}</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                    .footer { text-align: center; margin-top: 20px; color: #666; font-size: 12px; }
                    .btn { display: inline-block; padding: 12px 24px; background: #4facfe; color: white; text-decoration: none; border-radius: 6px; margin: 10px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Account Activated!</h1>
                        <p>Welcome to {{ app_name }}</p>
                    </div>
                    <div class="content">
                        <p>Hello {{ user_name }},</p>
                        <p>Congratulations! Your {{ app_name }} account has been successfully verified and activated.</p>
                        <p>You can now access all features of the platform and start creating amazing educational content.</p>
                        <p>Here's what you can do next:</p>
                        <ul>
                            <li>Explore the course creation tools</li>
                            <li>Set up your profile and preferences</li>
                            <li>Browse available pedagogical frameworks</li>
                            <li>Start building your first course</li>
                        </ul>
                        <p>If you have any questions or need assistance, our support team is here to help.</p>
                        <p>Happy creating!<br>
                        The {{ app_name }} Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message, please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            template = Template(welcome_template)
            html_body = template.render(app_name=settings.APP_NAME, user_name=user.name)

            text_body = f"""
Account Activated - {settings.APP_NAME}

Hello {user.name},

Congratulations! Your {settings.APP_NAME} account has been successfully verified and activated.

You can now access all features of the platform and start creating amazing educational content.

Happy creating!
The {settings.APP_NAME} Team
            """.strip()

            # Override recipient in test mode
            recipients = (
                [self.smtp_config.test_recipient]
                if self.smtp_config.test_recipient
                else [user.email]
            )

            message = MessageSchema(
                subject=f"🎉 Account Activated - Welcome to {settings.APP_NAME}!",
                recipients=recipients,
                body=text_body,
                html=html_body,
                subtype=MessageType.html,
            )

            if self.fast_mail:
                await self.fast_mail.send_message(message)
                print(
                    f"✅ Welcome email sent to {recipients[0]} via {self.smtp_config.provider.value}"
                )
                return True
            print("❌ Email service not initialized. Check configuration.")
            return False

        except Exception as e:
            print(f"❌ Failed to send welcome email to {user.email}: {e}")
            return False


# Global email service instance
email_service = EmailService()
