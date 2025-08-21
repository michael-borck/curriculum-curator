from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Curriculum Curator"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Testing
    TESTING: bool = False
    DISABLE_RATE_LIMIT: bool = False

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "sqlite:///./curriculum_curator.db"

    # Email - General
    EMAIL_WHITELIST: list[str] = []

    # Flexible Email Configuration (supports multiple providers)
    EMAIL_PROVIDER: str = "dev"  # Options: gmail, custom, brevo, sendgrid, mailgun, postmark, dev - default fallback only

    # Common SMTP Settings
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None

    # Email Settings
    FROM_EMAIL: str = "noreply@curriculum-curator.com"
    FROM_NAME: str = "Curriculum Curator"

    # Security Settings
    USE_TLS: bool = True
    USE_SSL: bool = False
    VALIDATE_CERTS: bool = True

    # Provider-specific Settings
    GMAIL_APP_PASSWORD: str | None = None
    SENDGRID_API_KEY: str | None = None
    MAILGUN_API_KEY: str | None = None
    MAILGUN_DOMAIN: str | None = None
    POSTMARK_SERVER_TOKEN: str | None = None

    # Brevo (legacy support)
    BREVO_API_KEY: str | None = None
    BREVO_SMTP_HOST: str = "smtp-relay.brevo.com"
    BREVO_SMTP_PORT: int = 587
    BREVO_SMTP_LOGIN: str = "93b634001@smtp-brevo.com"
    BREVO_FROM_EMAIL: str = "noreply@curriculum-curator.com"
    BREVO_FROM_NAME: str = "Curriculum Curator"

    # Email rate limiting
    EMAIL_RATE_LIMIT_PER_HOUR: int = 100
    EMAIL_RATE_LIMIT_PER_DAY: int = 1000

    # Development/Testing
    EMAIL_DEV_MODE: bool = (
        False  # Changed default to False - will be overridden by .env
    )
    TEST_EMAIL_RECIPIENT: str | None = None

    # LLM Configuration
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    DEFAULT_LLM_MODEL: str = "gpt-4"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list[str] = [".md", ".docx", ".pptx", ".pdf", ".txt"]

    # Git Content Repository
    CONTENT_REPO_PATH: str = "./content"  # Default to local content directory

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
