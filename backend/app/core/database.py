"""
SQLAlchemy database configuration for Curriculum Curator

Provides database engine, session management, and Base class for ORM models.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine
# For SQLite, we need check_same_thread=False for FastAPI's async handling
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.DATABASE_URL
    else {},
    echo=False,  # Set True temporarily to debug SQL queries
)

# Session factory - creates new database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db() -> Iterator[Session]:
    """
    FastAPI dependency that provides a database session.

    Usage in routes:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables defined in models.

    This should be called on application startup or via a setup script.
    Import all models before calling this to ensure they're registered.
    """
    # Import all models to register them with Base.metadata
    # These imports have side effects (registering tables), so we use them here
    from app.models.email_verification import EmailVerification
    from app.models.email_whitelist import EmailWhitelist
    from app.models.login_attempt import LoginAttempt
    from app.models.password_reset import PasswordReset
    from app.models.plugin_configuration import PluginConfiguration
    from app.models.security_log import SecurityLog
    from app.models.unit import Unit
    from app.models.user import User

    # Reference all models to satisfy linters (imports have side effects)
    _ = (
        EmailVerification,
        EmailWhitelist,
        LoginAttempt,
        PasswordReset,
        PluginConfiguration,
        SecurityLog,
        Unit,
        User,
    )

    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {settings.DATABASE_URL}")


def reset_db() -> None:
    """
    Drop and recreate all tables. USE WITH CAUTION.

    This is useful for development and testing only.
    """
    # Import all models to register them with Base.metadata
    from app.models.content import Content
    from app.models.email_verification import EmailVerification
    from app.models.email_whitelist import EmailWhitelist
    from app.models.login_attempt import LoginAttempt
    from app.models.password_reset import PasswordReset
    from app.models.plugin_configuration import PluginConfiguration
    from app.models.security_log import SecurityLog
    from app.models.unit import Unit
    from app.models.user import User

    # Reference all models to satisfy linters
    _ = (
        Content,
        EmailVerification,
        EmailWhitelist,
        LoginAttempt,
        PasswordReset,
        PluginConfiguration,
        SecurityLog,
        Unit,
        User,
    )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset complete")
