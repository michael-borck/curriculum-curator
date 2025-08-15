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

    # Brevo Email Service Configuration
    BREVO_API_KEY: str | None = None  # This is actually the SMTP password
    BREVO_SMTP_HOST: str = "smtp-relay.brevo.com"
    BREVO_SMTP_PORT: int = 587
    BREVO_SMTP_LOGIN: str = "93b634001@smtp-brevo.com"  # Your SMTP login
    BREVO_FROM_EMAIL: str = "noreply@curriculum-curator.com"
    BREVO_FROM_NAME: str = "Curriculum Curator"

    # Email rate limiting
    EMAIL_RATE_LIMIT_PER_HOUR: int = 50  # Brevo free tier limit

    # Development mode - log emails instead of sending
    EMAIL_DEV_MODE: bool = True

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
