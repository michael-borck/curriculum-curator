"""
Admin routes for user management and system configuration
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core.rate_limiter import RateLimits, limiter
from app.models import EmailWhitelist, User, UserRole
from app.services.security_logger import SecurityLogger
from app.schemas.admin import (
    EmailWhitelistCreate,
    EmailWhitelistResponse,
    EmailWhitelistUpdate,
    SystemSettingsResponse,
    SystemSettingsUpdate,
    UserListResponse,
    UserStatsResponse,
)
from app.schemas.user import UserResponse
from app.services.security_logger import SecurityLogger

router = APIRouter()


def get_current_admin_user(
    current_user: User = Depends(deps.get_current_active_user)
) -> User:
    """Dependency to ensure current user is an admin"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/users", response_model=UserListResponse)
# @limiter.limit(RateLimits.DEFAULT)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    role: str | None = None,
    is_verified: bool | None = None,
    is_active: bool | None = None,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """List all users with optional filtering and pagination"""
    query = db.query(User)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) |
            (User.name.ilike(search_term))
        )

    if role:
        query = query.filter(User.role == role)

    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # Get total count
    total = query.count()

    # Apply pagination
    users = query.offset(skip).limit(limit).all()

    # Convert to response model
    user_responses = [
        UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            is_verified=user.is_verified,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
        for user in users
    ]

    return UserListResponse(
        users=user_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/users/{user_id}/toggle-status")
# @limiter.limit(RateLimits.DEFAULT)
async def toggle_user_status(
    user_id: str,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Toggle user active status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from disabling themselves
    if str(user.id) == str(admin_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account"
        )

    user.is_active = not user.is_active
    db.commit()

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"{'Disabled' if not user.is_active else 'Enabled'} user {user.email}",
        target_user_id=user.id
    )

    return {
        "message": f"User {user.email} has been {'disabled' if not user.is_active else 'enabled'}",
        "is_active": user.is_active
    }


@router.delete("/users/{user_id}")
# @limiter.limit(RateLimits.DEFAULT)
async def delete_user(
    user_id: str,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Delete a user (soft delete by marking inactive)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from deleting themselves
    if str(user.id) == str(admin_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Soft delete - just mark as inactive
    user.is_active = False
    db.commit()

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"Deleted user {user.email}",
        target_user_id=user.id
    )

    return {"message": f"User {user.email} has been deleted"}


@router.get("/users/stats", response_model=UserStatsResponse)
# @limiter.limit(RateLimits.DEFAULT)
async def get_user_statistics(
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get user statistics"""
    total_users = db.query(User).count()
    verified_users = db.query(User).filter(User.is_verified).count()
    active_users = db.query(User).filter(User.is_active).count()
    admin_users = db.query(User).filter(User.role == UserRole.ADMIN.value).count()

    # Get users by role
    role_counts = db.query(
        User.role,
        func.count(User.id)
    ).group_by(User.role).all()

    users_by_role = dict(role_counts)

    # Get recent registrations (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_registrations = db.query(User).filter(
        User.created_at >= seven_days_ago
    ).count()

    return UserStatsResponse(
        total_users=total_users,
        verified_users=verified_users,
        active_users=active_users,
        admin_users=admin_users,
        users_by_role=users_by_role,
        recent_registrations=recent_registrations
    )


# Email Whitelist CRUD endpoints
@router.get("/whitelist", response_model=list[EmailWhitelistResponse])
# @limiter.limit(RateLimits.DEFAULT)
async def list_email_whitelist(
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """List all email whitelist patterns"""
    patterns = db.query(EmailWhitelist).all()
    return [
        EmailWhitelistResponse(
            id=str(pattern.id),
            pattern=pattern.pattern,
            description=pattern.description,
            is_active=pattern.is_active,
            created_at=pattern.created_at.isoformat(),
            updated_at=pattern.updated_at.isoformat()
        )
        for pattern in patterns
    ]


@router.post("/whitelist", response_model=EmailWhitelistResponse)
# @limiter.limit(RateLimits.DEFAULT)
async def create_whitelist_pattern(
    pattern_data: EmailWhitelistCreate,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Create a new email whitelist pattern"""
    # Check if pattern already exists
    existing = db.query(EmailWhitelist).filter(
        EmailWhitelist.pattern == pattern_data.pattern.lower()
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pattern already exists"
        )

    new_pattern = EmailWhitelist(
        pattern=pattern_data.pattern.lower(),
        description=pattern_data.description,
        is_active=pattern_data.is_active
    )

    db.add(new_pattern)
    db.commit()
    db.refresh(new_pattern)

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"Created email whitelist pattern: {new_pattern.pattern}"
    )

    return EmailWhitelistResponse(
        id=str(new_pattern.id),
        pattern=new_pattern.pattern,
        description=new_pattern.description,
        is_active=new_pattern.is_active,
        created_at=new_pattern.created_at.isoformat(),
        updated_at=new_pattern.updated_at.isoformat()
    )


@router.put("/whitelist/{pattern_id}", response_model=EmailWhitelistResponse)
# @limiter.limit(RateLimits.DEFAULT)
async def update_whitelist_pattern(
    pattern_id: str,
    pattern_data: EmailWhitelistUpdate,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Update an email whitelist pattern"""
    pattern = db.query(EmailWhitelist).filter(
        EmailWhitelist.id == pattern_id
    ).first()

    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found"
        )

    # Update fields if provided
    if pattern_data.pattern is not None:
        pattern.pattern = pattern_data.pattern.lower()
    if pattern_data.description is not None:
        pattern.description = pattern_data.description
    if pattern_data.is_active is not None:
        pattern.is_active = pattern_data.is_active

    db.commit()
    db.refresh(pattern)

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"Updated email whitelist pattern: {pattern.pattern}"
    )

    return EmailWhitelistResponse(
        id=str(pattern.id),
        pattern=pattern.pattern,
        description=pattern.description,
        is_active=pattern.is_active,
        created_at=pattern.created_at.isoformat(),
        updated_at=pattern.updated_at.isoformat()
    )


@router.delete("/whitelist/{pattern_id}")
# @limiter.limit(RateLimits.DEFAULT)
async def delete_whitelist_pattern(
    pattern_id: str,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Delete an email whitelist pattern"""
    pattern = db.query(EmailWhitelist).filter(
        EmailWhitelist.id == pattern_id
    ).first()

    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found"
        )

    pattern_str = pattern.pattern
    db.delete(pattern)
    db.commit()

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action=f"Deleted email whitelist pattern: {pattern_str}"
    )

    return {"message": f"Pattern {pattern_str} has been deleted"}


# System settings endpoints (placeholder for now)
@router.get("/settings", response_model=SystemSettingsResponse)
# @limiter.limit(RateLimits.DEFAULT)
async def get_system_settings(
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get system settings"""
    # TODO: Implement actual system settings retrieval
    return SystemSettingsResponse(
        password_min_length=8,
        password_require_uppercase=True,
        password_require_lowercase=True,
        password_require_numbers=True,
        password_require_special=True,
        max_login_attempts=5,
        lockout_duration_minutes=15,
        session_timeout_minutes=30,
        enable_user_registration=True,
        enable_email_whitelist=True
    )


@router.put("/settings", response_model=SystemSettingsResponse)
# @limiter.limit(RateLimits.DEFAULT)
async def update_system_settings(
    settings_data: SystemSettingsUpdate,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Update system settings"""
    # TODO: Implement actual system settings update
    # For now, just return the provided settings

    # Log the action
    SecurityLogger.log_admin_action(
        db=db,
        admin_user=admin_user,
        action="Updated system settings"
    )

    return SystemSettingsResponse(
        password_min_length=settings_data.password_min_length or 8,
        password_require_uppercase=settings_data.password_require_uppercase if settings_data.password_require_uppercase is not None else True,
        password_require_lowercase=settings_data.password_require_lowercase if settings_data.password_require_lowercase is not None else True,
        password_require_numbers=settings_data.password_require_numbers if settings_data.password_require_numbers is not None else True,
        password_require_special=settings_data.password_require_special if settings_data.password_require_special is not None else True,
        max_login_attempts=settings_data.max_login_attempts or 5,
        lockout_duration_minutes=settings_data.lockout_duration_minutes or 15,
        session_timeout_minutes=settings_data.session_timeout_minutes or 30,
        enable_user_registration=settings_data.enable_user_registration if settings_data.enable_user_registration is not None else True,
        enable_email_whitelist=settings_data.enable_email_whitelist if settings_data.enable_email_whitelist is not None else True
    )

