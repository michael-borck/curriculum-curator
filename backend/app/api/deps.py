"""
Authentication dependencies for FastAPI routes

Uses SQLAlchemy ORM for database access via dependency injection.
"""

import logging
from collections.abc import Generator
from typing import Annotated, Any, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.assessment import Assessment
from app.models.learning_design import LearningDesign
from app.models.learning_outcome import UnitLearningOutcome
from app.models.unit import Unit
from app.models.weekly_material import WeeklyMaterial
from app.repositories import unit_repo, user_repo
from app.schemas.unit import UnitResponse
from app.schemas.user import UserResponse

# Set up logger
logger = logging.getLogger(__name__)

# Well-known local user constants
LOCAL_USER_ID = "00000000-0000-0000-0000-000000000001"
LOCAL_USER_EMAIL = "local@curriculum-curator.app"

# Use HTTPBearer for JWT authentication
# In LOCAL_MODE, make it optional (auto_error=False) so requests without
# Authorization header don't get rejected before reaching get_current_user
security = HTTPBearer(auto_error=not settings.LOCAL_MODE)

# User role constants
ROLE_ADMIN = "admin"
ROLE_LECTURER = "lecturer"
ROLE_STUDENT = "student"


def get_db() -> Generator[Session]:
    """Get SQLAlchemy database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
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

    from app.core import security as security_module  # noqa: PLC0415

    # Extract client IP for token IP-binding verification
    client_ip: str | None = None
    if request.client:
        client_ip = request.client.host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    payload = security_module.decode_access_token(token, verify_ip=client_ip)
    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

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


# =============================================================================
# Resource Ownership Seam
# =============================================================================
#
# One helper (load_owned_or_404) holds the load + ownership + admin-bypass +
# archived + 404 logic. The per-resource dependencies (get_user_unit,
# get_user_material, get_user_assessment, ...) are thin adapters that name their
# path param and ownership path: a direct owner column (owner_attr), or
# `via_unit=True` for resources owned transitively through their Unit. Ownership
# failures always return 404 (never 403 — don't leak existence) and admins
# always bypass. See ADR-066.


def _verify_owner_or_404(
    owner_id: object,
    current_user: UserResponse,
    *,
    archived: bool,
    detail: str,
) -> None:
    """Raise 404 unless the user owns the resource (admins bypass) and it (or
    its parent unit) is not archived."""
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    if str(owner_id) != str(current_user.id) and current_user.role != ROLE_ADMIN:
        raise not_found
    if archived:
        raise not_found


def load_owned_or_404[T](
    db: Session,
    model: type[T],
    resource_id: str,
    current_user: UserResponse,
    *,
    owner_attr: str = "owner_id",
    via_unit: bool = False,
    detail: str = "Resource not found or access denied",
) -> T:
    """Load a resource by id and enforce ownership, or raise 404.

    Args:
        owner_attr: the resource's direct-owner column (e.g. ``owner_id`` or
            ``user_id``). Ignored when ``via_unit`` is True.
        via_unit: when True, ownership is transitive — the resource has a
            ``unit_id`` and the owning Unit's ``owner_id`` (and archived status)
            is checked. When False, ``owner_attr`` on the resource itself is.
    """
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    resource = db.get(model, resource_id)
    if resource is None:
        raise not_found

    res = cast("Any", resource)
    if via_unit:
        unit = unit_repo.get_unit_by_id(db, str(res.unit_id))
        if unit is None:
            raise not_found
        owner_id: object = unit.owner_id
        archived = unit.status == "archived"
    else:
        owner_id = getattr(res, owner_attr)
        archived = getattr(res, "status", None) == "archived"

    _verify_owner_or_404(owner_id, current_user, archived=archived, detail=detail)
    return resource


def get_user_unit(
    unit_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> UnitResponse:
    """Get a unit the current user owns (admins bypass), or 404.

    Returns the API schema (``UnitResponse``) — many callers depend on that — so
    it loads via the repo but shares the ownership check.
    """
    unit = unit_repo.get_unit_by_id(db, unit_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied",
        )
    _verify_owner_or_404(
        unit.owner_id,
        current_user,
        archived=unit.status == "archived",
        detail="Unit not found or access denied",
    )
    return unit


# Alias for path parameter usage
get_user_unit_by_path = get_user_unit


def get_user_material(
    material_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> WeeklyMaterial:
    """Get a weekly material whose owning unit belongs to the current user, or 404."""
    return load_owned_or_404(
        db,
        WeeklyMaterial,
        material_id,
        current_user,
        via_unit=True,
        detail="Material not found or access denied",
    )


def get_user_assessment(
    assessment_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> Assessment:
    """Get an assessment whose owning unit belongs to the current user, or 404."""
    return load_owned_or_404(
        db,
        Assessment,
        assessment_id,
        current_user,
        via_unit=True,
        detail="Assessment not found or access denied",
    )


def get_user_ulo(
    ulo_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> UnitLearningOutcome:
    """Get a learning outcome whose owning unit belongs to the current user, or 404."""
    return load_owned_or_404(
        db,
        UnitLearningOutcome,
        ulo_id,
        current_user,
        via_unit=True,
        detail="Learning outcome not found or access denied",
    )


def get_user_design(
    design_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
) -> LearningDesign:
    """Get a learning design whose owning unit belongs to the current user, or 404."""
    return load_owned_or_404(
        db,
        LearningDesign,
        design_id,
        current_user,
        via_unit=True,
        detail="Learning design not found or access denied",
    )


def require_unit_owner(
    db: Session, unit_id: str, current_user: UserResponse
) -> Unit:
    """Verify the current user owns ``unit_id`` (admins bypass), else 404; return it.

    For handlers where the unit_id is in the request body (not the path), so it
    can't be a route-level dependency. Callers using it purely as a guard can
    ignore the return value.
    """
    return load_owned_or_404(
        db, Unit, unit_id, current_user, detail="Unit not found or access denied"
    )


def filter_owned_unit_ids(
    db: Session, unit_ids: list[str], current_user: UserResponse
) -> list[str]:
    """Return the subset of ``unit_ids`` the current user owns (admins get all).

    The collection analogue of :func:`get_user_unit`, for batch endpoints that
    take a list of unit ids in the body. Non-owned ids are silently dropped (no
    existence leak), preserving order.
    """
    if current_user.role == ROLE_ADMIN:
        return list(unit_ids)
    if not unit_ids:
        return []
    rows = (
        db.query(Unit.id)
        .filter(Unit.id.in_(unit_ids), Unit.owner_id == current_user.id)
        .all()
    )
    owned = {str(row[0]) for row in rows}
    return [uid for uid in unit_ids if str(uid) in owned]
