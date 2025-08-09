"""
Email service using Brevo (formerly SendinBlue) via fastapi-mail
"""

import secrets
import string
import traceback
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Template

from app.core.config import settings
from app.models import User


class EmailService:
    """Email service for sending verification and reset emails via Brevo"""

    def __init__(self):
        """Initialize email service with Brevo configuration"""
        if not settings.BREVO_API_KEY:
            # For development, we'll use SMTP without API key
            # In production, you should set BREVO_API_KEY environment variable
            pass

        template_dir = str(Path(__file__).parent / "../templates/email")

        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.BREVO_SMTP_LOGIN,  # Use SMTP login, not FROM email
            MAIL_PASSWORD=settings.BREVO_API_KEY or "dummy-for-dev",
            MAIL_FROM=settings.BREVO_FROM_EMAIL,
            MAIL_FROM_NAME=settings.BREVO_FROM_NAME,
            MAIL_PORT=settings.BREVO_SMTP_PORT,
            MAIL_SERVER=settings.BREVO_SMTP_HOST,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=template_dir,
        )

        self.fast_mail = FastMail(self.config)

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

    async def send_verification_email(
        self, user: User, verification_code: str, expires_minutes: int = 15
    ) -> bool:
        """Send email verification code to user"""
        # Development mode - log instead of sending
        if settings.EMAIL_DEV_MODE:
            print("\n📧 [DEV MODE] Email Verification")
            print(f"To: {user.email}")
            print(f"Name: {user.name}")
            print(f"Verification Code: {verification_code}")
            print(f"Expires in: {expires_minutes} minutes")
            print(f"Subject: Welcome to {settings.APP_NAME} - Verify Your Email\n")
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

            message = MessageSchema(
                subject=f"Welcome to {settings.APP_NAME} - Verify Your Email",
                recipients=[user.email],
                body=text_body,
                html=html_body,
                subtype=MessageType.html,
            )

            await self.fast_mail.send_message(message)
            return True

        except Exception as e:
            print(f"❌ Failed to send verification email to {user.email}: {e}")
            # Add more detailed error logging
            print("Full error traceback:")
            traceback.print_exc()
            return False

    async def send_password_reset_email(
        self, user: User, reset_code: str, expires_minutes: int = 30
    ) -> bool:
        """Send password reset code to user"""
        # Development mode - log instead of sending
        if settings.EMAIL_DEV_MODE:
            print("\n🔐 [DEV MODE] Password Reset Email")
            print(f"To: {user.email}")
            print(f"Name: {user.name}")
            print(f"Reset Code: {reset_code}")
            print(f"Expires in: {expires_minutes} minutes")
            print(f"Subject: Password Reset - {settings.APP_NAME}\n")
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

            message = MessageSchema(
                subject=f"Password Reset - {settings.APP_NAME}",
                recipients=[user.email],
                body=text_body,
                html=html_body,
                subtype=MessageType.html,
            )

            await self.fast_mail.send_message(message)
            return True

        except Exception as e:
            print(f"❌ Failed to send password reset email to {user.email}: {e}")
            return False

    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email after successful verification"""
        # Development mode - log instead of sending
        if settings.EMAIL_DEV_MODE:
            print("\n🎉 [DEV MODE] Welcome Email")
            print(f"To: {user.email}")
            print(f"Name: {user.name}")
            print(f"Subject: 🎉 Account Activated - Welcome to {settings.APP_NAME}!\n")
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

            message = MessageSchema(
                subject=f"🎉 Account Activated - Welcome to {settings.APP_NAME}!",
                recipients=[user.email],
                body=text_body,
                html=html_body,
                subtype=MessageType.html,
            )

            await self.fast_mail.send_message(message)
            return True

        except Exception as e:
            print(f"❌ Failed to send welcome email to {user.email}: {e}")
            return False


# Global email service instance
email_service = EmailService()
