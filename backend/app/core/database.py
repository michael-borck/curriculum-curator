"""
SQLAlchemy database configuration for Curriculum Curator

Provides database engine, session management, and Base class for ORM models.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
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

if "sqlite" in settings.DATABASE_URL:

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        """SQLite ignores foreign keys unless enabled per connection."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


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


def _ensure_sqlite_schema() -> None:
    """Add columns/rebuild tables that predate the current models.

    ``create_all`` never alters existing tables, and desktop installs keep a
    long-lived SQLite file. This keeps an upgraded app working without asking
    users to delete their data.
    """
    if "sqlite" not in settings.DATABASE_URL:
        return

    from sqlalchemy import text

    user_columns = {
        "token_version": "INTEGER NOT NULL DEFAULT 0",
        "totp_secret": "TEXT",
        "totp_enabled": "BOOLEAN NOT NULL DEFAULT 0",
        "totp_recovery_hashes": "JSON",
        "totp_last_counter": "INTEGER NOT NULL DEFAULT 0",
    }

    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        existing = {row[1] for row in rows}
        for name, ddl in user_columns.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))

    # Verification/reset codes changed from plaintext to hashes; the data is
    # short-lived, so rebuilding these tables is safe and simpler than a
    # multi-step column rename in SQLite.
    for table_name, legacy_column, new_column in (
        ("email_verifications", "code", "code_hash"),
        ("password_resets", "token", "token_hash"),
    ):
        with engine.begin() as conn:
            rows = conn.execute(
                text(f"PRAGMA table_info({table_name})")
            ).fetchall()
            columns = {row[1] for row in rows}
            if not columns:
                continue
            if legacy_column in columns and new_column not in columns:
                conn.execute(text(f"DROP TABLE {table_name}"))
                columns = set()
            if new_column in columns and "attempts" not in columns:
                conn.execute(
                    text(
                        f"ALTER TABLE {table_name} ADD COLUMN attempts "
                        "INTEGER NOT NULL DEFAULT 0"
                    )
                )
        if not columns:
            Base.metadata.tables[table_name].create(bind=engine)


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
    from app.models.login_token import LoginToken
    from app.models.password_reset import PasswordReset
    from app.models.plugin_configuration import PluginConfiguration
    from app.models.security_log import SecurityLog
    from app.models.unit import Unit
    from app.models.user import User
    from app.models.webauthn_credential import WebAuthnCredential

    # Reference all models to satisfy linters (imports have side effects)
    _ = (
        EmailVerification,
        EmailWhitelist,
        LoginAttempt,
        LoginToken,
        PasswordReset,
        WebAuthnCredential,
        PluginConfiguration,
        SecurityLog,
        Unit,
        User,
    )

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_schema()
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
