
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Curriculum Curator"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "sqlite:///./curriculum_curator.db"

    # Email - General
    EMAIL_WHITELIST: list[str] = []

    # Brevo Email Service Configuration
    BREVO_API_KEY: str | None = None
    BREVO_SMTP_HOST: str = "smtp-relay.sendinblue.com"
    BREVO_SMTP_PORT: int = 587
    BREVO_FROM_EMAIL: str = "noreply@curriculum-curator.com"
    BREVO_FROM_NAME: str = "Curriculum Curator"

    # Email rate limiting
    EMAIL_RATE_LIMIT_PER_HOUR: int = 50  # Brevo free tier limit

    # LLM Configuration
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    DEFAULT_LLM_MODEL: str = "gpt-4"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list[str] = [".md", ".docx", ".pptx", ".pdf", ".txt"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
