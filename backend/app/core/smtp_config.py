"""
SMTP Configuration for multiple email providers
Supports Gmail, personal SMTP servers, Brevo, and other providers
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class EmailProvider(str, Enum):
    """Supported email providers"""

    GMAIL = "gmail"
    BREVO = "brevo"
    CUSTOM_SMTP = "custom"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    POSTMARK = "postmark"
    DEV_MODE = "dev"  # Console output only


class SMTPConfig(BaseModel):
    """SMTP configuration for email providers"""

    provider: EmailProvider = Field(default=EmailProvider.DEV_MODE)

    # Common SMTP settings
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None

    # Email settings
    from_email: str = "noreply@example.com"
    from_name: str = "Curriculum Curator"

    # Security settings
    use_tls: bool = True
    use_ssl: bool = False
    validate_certs: bool = True

    # Provider-specific settings
    gmail_app_password: str | None = None  # For Gmail 2FA accounts
    brevo_api_key: str | None = None
    sendgrid_api_key: str | None = None
    mailgun_api_key: str | None = None
    mailgun_domain: str | None = None
    postmark_server_token: str | None = None

    # Rate limiting
    rate_limit_per_hour: int = 100
    rate_limit_per_day: int = 1000

    # Development/Testing
    dev_mode: bool = False
    test_recipient: str | None = None  # Override all recipients in test mode

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v):
        """Validate provider selection"""
        if not v:
            return EmailProvider.DEV_MODE
        return v

    def get_smtp_settings(self) -> dict:  # noqa: PLR0911
        """Get SMTP settings based on provider"""

        if self.provider == EmailProvider.GMAIL:
            return {
                "host": "smtp.gmail.com",
                "port": 587,
                "username": self.smtp_username or self.from_email,
                "password": self.gmail_app_password or self.smtp_password,
                "use_tls": True,
                "use_ssl": False,
            }

        if self.provider == EmailProvider.BREVO:
            return {
                "host": "smtp-relay.brevo.com",
                "port": 587,
                "username": self.smtp_username or "your-login@smtp-brevo.com",
                "password": self.brevo_api_key or self.smtp_password,
                "use_tls": True,
                "use_ssl": False,
            }

        if self.provider == EmailProvider.SENDGRID:
            return {
                "host": "smtp.sendgrid.net",
                "port": 587,
                "username": "apikey",  # SendGrid requires "apikey" as username
                "password": self.sendgrid_api_key or self.smtp_password,
                "use_tls": True,
                "use_ssl": False,
            }

        if self.provider == EmailProvider.MAILGUN:
            return {
                "host": "smtp.mailgun.org",
                "port": 587,
                "username": f"postmaster@{self.mailgun_domain}"
                if self.mailgun_domain
                else self.smtp_username,
                "password": self.mailgun_api_key or self.smtp_password,
                "use_tls": True,
                "use_ssl": False,
            }

        if self.provider == EmailProvider.POSTMARK:
            return {
                "host": "smtp.postmarkapp.com",
                "port": 587,
                "username": self.postmark_server_token,
                "password": self.postmark_server_token,  # Postmark uses token for both
                "use_tls": True,
                "use_ssl": False,
            }

        if self.provider == EmailProvider.CUSTOM_SMTP:
            return {
                "host": self.smtp_host,
                "port": self.smtp_port,
                "username": self.smtp_username,
                "password": self.smtp_password,
                "use_tls": self.use_tls,
                "use_ssl": self.use_ssl,
            }

        # DEV_MODE
        return {
            "host": "localhost",
            "port": 1025,
            "username": None,
            "password": None,
            "use_tls": False,
            "use_ssl": False,
        }

    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        if self.dev_mode or self.provider == EmailProvider.DEV_MODE:
            return True

        settings = self.get_smtp_settings()
        return bool(
            settings.get("host")
            and settings.get("username")
            and settings.get("password")
        )


class GmailHelper:
    """Helper for Gmail configuration"""

    @staticmethod
    def get_setup_instructions() -> str:
        """Get Gmail setup instructions"""
        return """
        Gmail Setup Instructions:

        1. Enable 2-Factor Authentication (required for App Passwords):
           - Go to https://myaccount.google.com/security
           - Click on "2-Step Verification" and follow the setup

        2. Generate an App Password:
           - Go to https://myaccount.google.com/apppasswords
           - Select "Mail" as the app
           - Select "Other" as the device and enter "Curriculum Curator"
           - Copy the generated 16-character password

        3. Configure in .env file:
           EMAIL_PROVIDER=gmail
           SMTP_USERNAME=your-email@gmail.com
           GMAIL_APP_PASSWORD=your-16-char-app-password
           FROM_EMAIL=your-email@gmail.com
           FROM_NAME=Your Name or Organization

        Note: Regular Gmail passwords won't work with SMTP. You must use an App Password.
        """

    @staticmethod
    def validate_config(username: str, app_password: str) -> tuple[bool, str]:
        """Validate Gmail configuration"""
        if not username or "@gmail.com" not in username.lower():
            return False, "Username must be a valid Gmail address"

        if not app_password:
            return False, "App password is required for Gmail"

        # Remove spaces from app password (Gmail shows it with spaces)
        clean_password = app_password.replace(" ", "")

        if len(clean_password) != 16:
            return (
                False,
                "Gmail app password should be 16 characters (excluding spaces)",
            )

        return True, "Gmail configuration appears valid"


class PersonalSMTPHelper:
    """Helper for personal SMTP server configuration"""

    @staticmethod
    def get_setup_instructions() -> str:
        """Get personal SMTP setup instructions"""
        return """
        Personal SMTP Server Setup:

        1. Get your SMTP settings from your email provider or server admin:
           - SMTP server hostname (e.g., mail.yourdomain.com)
           - SMTP port (usually 587 for TLS, 465 for SSL, 25 for unencrypted)
           - Username (often your full email address)
           - Password

        2. Configure in .env file:
           EMAIL_PROVIDER=custom
           SMTP_HOST=mail.yourdomain.com
           SMTP_PORT=587
           SMTP_USERNAME=you@yourdomain.com
           SMTP_PASSWORD=your-password
           FROM_EMAIL=noreply@yourdomain.com
           FROM_NAME=Your Organization
           USE_TLS=true
           USE_SSL=false

        Common SMTP Ports:
        - 25: Default SMTP (often blocked by ISPs)
        - 465: SMTP over SSL
        - 587: SMTP with STARTTLS (recommended)
        - 2525: Alternative SMTP port

        Security Notes:
        - Use TLS (port 587) when possible
        - Avoid unencrypted connections
        - Consider using app-specific passwords if available
        """

    @staticmethod
    def test_common_providers(domain: str) -> dict:
        """Get common SMTP settings for known domains"""
        domain = domain.lower()

        common_providers = {
            "outlook.com": {
                "host": "smtp-mail.outlook.com",
                "port": 587,
                "use_tls": True,
            },
            "hotmail.com": {
                "host": "smtp-mail.outlook.com",
                "port": 587,
                "use_tls": True,
            },
            "yahoo.com": {"host": "smtp.mail.yahoo.com", "port": 587, "use_tls": True},
            "icloud.com": {"host": "smtp.mail.me.com", "port": 587, "use_tls": True},
            "zoho.com": {"host": "smtp.zoho.com", "port": 587, "use_tls": True},
            "protonmail.com": {
                "host": "smtp.protonmail.com",
                "port": 587,
                "use_tls": True,
                "note": "Requires ProtonMail Bridge",
            },
        }

        for provider, settings in common_providers.items():
            if provider in domain:
                return settings

        # Generic settings for unknown domains
        return {
            "host": f"mail.{domain}",
            "port": 587,
            "use_tls": True,
            "note": "These are generic settings. Check with your email provider for exact settings.",
        }
