"""
Database configuration and session management for Curriculum Curator
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.DATABASE_URL
    else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator:
    """
    Database dependency to be used in FastAPI routes.
    Yields a database session and closes it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Called on application startup.
    """
    # Import all models here to ensure they're registered with Base
    # These imports are used by SQLAlchemy to register models with Base.metadata
    from app.models import (  # pyright: ignore[reportUnusedImport]
        EmailVerification,
        EmailWhitelist,
        PasswordReset,
        SystemSettings,
        User,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")
