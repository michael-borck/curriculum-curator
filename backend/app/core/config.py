from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Curriculum Curator"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Testing
    TESTING: bool = False
    DISABLE_RATE_LIMIT: bool = False

    # Local Mode - privacy-first local deployment (no login required)
    LOCAL_MODE: bool = False

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "sqlite:///./data/curriculum_curator.db"

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

    # Image Upload
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    IMAGE_EXTENSIONS: list[str] = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]

    # Export Templates
    TEMPLATE_UPLOAD_DIR: str = "./user_templates"
    TEMPLATE_MAX_SIZE: int = 5 * 1024 * 1024  # 5MB
    TEMPLATE_EXTENSIONS: list[str] = [".pptx", ".docx"]

    # Git Content Repository
    CONTENT_REPO_PATH: str = "./content"  # Default to local content directory

    # Ollama (Local AI)
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Web Search (SearXNG)
    SEARXNG_URL: str = "http://localhost:8080"  # SearXNG instance URL
    SEARXNG_TIMEOUT: int = 30  # Search timeout in seconds

    # Tier 3 Search APIs (user can also set per-account via research settings)
    GOOGLE_CSE_API_KEY: str | None = None
    GOOGLE_CSE_ENGINE_ID: str | None = None
    BRAVE_SEARCH_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
