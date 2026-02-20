"""
Authentication dependencies for FastAPI routes

Uses SQLAlchemy ORM for database access via dependency injection.
"""

import logging
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories import content_repo, unit_repo, user_repo
from app.schemas.content import ContentResponse
from app.schemas.unit import UnitResponse
from app.schemas.user import UserResponse

# Set up logger
logger = logging.getLogger(__name__)

# Well-known local user constants
LOCAL_USER_ID = "00000000-0000-0000-0000-000000000001"
LOCAL_USER_EMAIL = "local@curriculum-curator.local"

# Use HTTPBearer for JWT authentication
# In LOCAL_MODE, make it optional (auto_error=False) so requests without
# Authorization header don't get rejected before reaching get_current_user
security = HTTPBearer(auto_error=not settings.LOCAL_MODE)

# User role constants
ROLE_ADMIN = "admin"
ROLE_LECTURER = "lecturer"
ROLE_STUDENT = "student"


def get_db() -> Generator[Session, None, None]:
    """Get SQLAlchemy database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Get current user from JWT token, or return local user in LOCAL_MODE."""
    # LOCAL_MODE: bypass JWT, return the local default user
    if settings.LOCAL_MODE:
        local_user = user_repo.get_user_by_id(db, LOCAL_USER_ID)
        if local_user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Local user not found. Ensure LOCAL_MODE startup completed.",
            )
        return local_user

    # Normal mode: require valid JWT
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        logger.exception("[AUTH] JWT decode failed")
        raise credentials_exception from None

    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        logger.error(f"[AUTH] User not found for id: {user_id}")
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> UserResponse:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current user and verify admin role."""
    if current_user.role != ROLE_ADMIN:
        logger.error(
            f"[ADMIN DENIED] {current_user.email} role '{current_user.role}' != '{ROLE_ADMIN}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user


def get_user_or_admin_override(
    resource_owner_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> bool:
    """
    Check if user owns resource or is admin.
    Returns True if access should be granted.
    """
    if current_user.role == ROLE_ADMIN:
        return True
    return current_user.id == resource_owner_id


# =============================================================================
# Resource Ownership Dependencies
# =============================================================================


def get_user_unit(
    unit_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> UnitResponse:
    """
    Get a unit that belongs to the current user.
    Raises 404 if unit not found or user doesn't own it.
    """
    unit = unit_repo.get_unit_by_id(db, unit_id)

    if not unit or (
        unit.owner_id != current_user.id and current_user.role != ROLE_ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )

    return unit


def get_user_content(
    content_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> ContentResponse:
    """
    Get content that belongs to the current user (via unit ownership).
    Raises 404 if content not found or user doesn't own the parent unit.
    """
    content = content_repo.get_content_by_id(db, content_id)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    # Check unit ownership
    unit = unit_repo.get_unit_by_id(db, content.unit_id)
    if not unit or (
        unit.owner_id != current_user.id and current_user.role != ROLE_ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found or access denied",
        )

    return content


# Alias for path parameter usage
get_user_unit_by_path = get_user_unit
