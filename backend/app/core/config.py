from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Curriculum Curator"
    DEBUG: bool = False
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

    # Public domain(s) the app is served from — bare hostnames, comma-separated
    # (e.g. "curriculum.example.com" or "app.example.com,www.example.com").
    # Each domain is added to the trusted-host allowlist and its https:// origin
    # to the CORS allowlist. Localhost is always allowed, so this can stay empty
    # for local development.
    PUBLIC_DOMAIN: str = ""

    @property
    def public_domains(self) -> list[str]:
        return [d.strip() for d in self.PUBLIC_DOMAIN.split(",") if d.strip()]

    # Trust X-Forwarded-For / X-Real-IP headers for the client IP used in rate
    # limiting, account lockout, and JWT IP-binding. Leave False unless the app
    # runs behind a trusted reverse proxy (e.g. Caddy/nginx) that sets these —
    # otherwise a client can spoof them to bypass those controls.
    TRUST_PROXY_HEADERS: bool = False

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
    FROM_EMAIL: str = "noreply@example.com"
    FROM_NAME: str = "Curriculum Curator"

    # Contact email advertised to third-party APIs (CrossRef/OpenAlex "polite
    # pool" identifiers, which those services use to reach the operator about
    # misbehaving clients). Falls back to FROM_EMAIL; omitted while both are
    # unset or still the example.com placeholder.
    CONTACT_EMAIL: str | None = None

    @property
    def api_contact_email(self) -> str | None:
        contact = self.CONTACT_EMAIL or self.FROM_EMAIL
        if not contact or contact.strip().lower().endswith("@example.com"):
            return None
        return contact.strip()

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
    RESEND_API_KEY: str | None = None  # For EMAIL_PROVIDER=resend (Resend HTTP API)

    # Brevo (SMTP relay; set SMTP_USERNAME to your Brevo SMTP login)
    BREVO_API_KEY: str | None = None

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
    DEFAULT_LLM_PROVIDER: str | None = None
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

    # Tier 1 extended: CORE API (free with registration, 10K/month)
    CORE_API_KEY: str | None = None

    # Tier 3 Search APIs (user can also set per-account via research settings)
    GOOGLE_CSE_API_KEY: str | None = None
    GOOGLE_CSE_ENGINE_ID: str | None = None
    BRAVE_SEARCH_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
    SERPER_API_KEY: str | None = None

    # Search quality filters — domains dropped from every tier's results.
    # Override via env: EXCLUDED_SEARCH_DOMAINS="youtube.com,pinterest.com,example.com"
    EXCLUDED_SEARCH_DOMAINS: list[str] = [
        "youtube.com",
        "pinterest.com",
        "quora.com",
    ]

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        if not self.DEBUG and self.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed from default in production")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
