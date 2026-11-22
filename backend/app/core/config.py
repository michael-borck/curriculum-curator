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
    # When set, LOCAL_MODE requests must also present this token in the
    # X-Desktop-Token header. The desktop app generates a fresh one per launch
    # so other local processes cannot use the unauthenticated API.
    DESKTOP_TOKEN: str | None = None

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    # One-time token required to create the first (admin) account on a fresh
    # deployment. When unset, a random token is written to a 0600 file beside
    # the database so the operator can read it on the server.
    SETUP_TOKEN: str | None = None
    # Optional dedicated key for encrypting stored secrets (LLM API keys).
    # A Fernet key or any long random string; derived from SECRET_KEY if unset.
    ENCRYPTION_KEY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # httpOnly session cookie (web) + readable double-submit CSRF cookie.
    SESSION_COOKIE_NAME: str = "cc_session"
    CSRF_COOKIE_NAME: str = "cc_csrf"

    # Public domain(s) the app is served from — bare hostnames, comma-separated
    # (e.g. "curriculum.example.com" or "app.example.com,www.example.com").
    # Each domain is added to the trusted-host allowlist and its https:// origin
    # to the CORS allowlist. Localhost is always allowed, so this can stay empty
    # for local development.
    PUBLIC_DOMAIN: str = ""
    # Where the browser app is served, used for magic-link URLs.
    # Defaults to the first PUBLIC_DOMAIN, else local Vite.
    FRONTEND_URL: str = ""

    @property
    def frontend_url(self) -> str:
        if self.FRONTEND_URL.strip():
            return self.FRONTEND_URL.strip().rstrip("/")
        domains = self.public_domains
        if domains:
            return f"https://{domains[0]}"
        return "http://localhost:5173"

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
    # misbehaving clients). Only sent when the operator sets it explicitly —
    # it is never derived from FROM_EMAIL, so user search terms are not
    # linkable to the operator's sign-in address by default.
    CONTACT_EMAIL: str | None = None

    @property
    def api_contact_email(self) -> str | None:
        contact = self.CONTACT_EMAIL
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
    GEMINI_API_KEY: str | None = None
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
    def validate_security_settings(self) -> "Settings":
        # TESTING is the only exemption: the test suite uses throwaway keys.
        if not self.TESTING:
            known = {
                "dev-secret-key-change-in-production",
                "your-secret-key-change-this-in-production",
                "change-me-to-a-random-string",
                "ci-test-secret",
                "test-secret-key-for-testing",
                "your-secret-key",
                "secret",
            }
            secret = self.SECRET_KEY or ""
            if (
                secret in known
                or secret.startswith("docker-dev-secret-key-")
                or len(secret) < 32
            ):
                raise ValueError(
                    "SECRET_KEY is missing, a known placeholder, or shorter "
                    "than 32 characters. Generate one with: openssl rand -hex 32"
                )
            if self.LOCAL_MODE and self.public_domains:
                raise ValueError(
                    "LOCAL_MODE disables authentication and must never be "
                    "combined with PUBLIC_DOMAIN (public deployment)."
                )
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
