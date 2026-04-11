"""
User repository - database operations for users

Handles all user-related database queries using SQLAlchemy ORM.
"""

import secrets
import string
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.email_verification import EmailVerification
from app.models.email_whitelist import EmailWhitelist
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.schemas.user import UserCreate, UserInDB, UserResponse


def _generate_code(length: int = 6) -> str:
    """Generate a secure random numeric code"""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def _user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse schema"""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        is_verified=user.is_verified,
        is_active=user.is_active,
        institution=user.institution,
        department=user.department,
        education_sector=user.education_sector,
        teaching_philosophy=user.teaching_philosophy,
        teaching_preferences=user.teaching_preferences,
        created_at=user.created_at,
    )


def _user_to_db(user: User) -> UserInDB:
    """Convert User model to UserInDB schema (includes password_hash)"""
    return UserInDB(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        is_verified=user.is_verified,
        is_active=user.is_active,
        institution=user.institution,
        department=user.department,
        education_sector=user.education_sector,
        teaching_philosophy=user.teaching_philosophy,
        teaching_preferences=user.teaching_preferences,
        created_at=user.created_at,
        password_hash=user.password_hash,
    )


def create_user(db: Session, data: UserCreate) -> UserResponse:
    """Create a new user"""
    user = User(
        id=str(uuid.uuid4()),
        email=data.email.lower().strip(),
        password_hash=get_password_hash(data.password),
        name=data.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_to_response(user)


def get_user_by_email(db: Session, email: str) -> UserInDB | None:
    """Get user by email (includes password_hash for auth)"""
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    return _user_to_db(user) if user else None


def get_user_by_id(db: Session, user_id: str) -> UserResponse | None:
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    return _user_to_response(user) if user else None


def get_user_with_hash(db: Session, user_id: str) -> UserInDB | None:
    """Get user by ID including password hash (for password change)"""
    user = db.query(User).filter(User.id == user_id).first()
    return _user_to_db(user) if user else None


def update_user(db: Session, user_id: str, **fields) -> UserResponse | None:
    """Update user fields"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    for key, value in fields.items():
        if hasattr(user, key):
            setattr(user, key, value)

    user.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)
    return _user_to_response(user)


def update_password(db: Session, user_id: str, new_password: str) -> bool:
    """Update user's password"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.now(UTC)
    db.commit()
    return True


def verify_user(db: Session, user_id: str) -> bool:
    """Mark user as verified"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    user.is_verified = True
    user.updated_at = datetime.now(UTC)
    db.commit()
    return True


def user_exists(db: Session, email: str) -> bool:
    """Check if user with email exists"""
    return (
        db.query(User).filter(User.email == email.lower().strip()).first() is not None
    )


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[UserResponse]:
    """Get all users with pagination"""
    users = (
        db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    )
    return [_user_to_response(user) for user in users]


# Email verification functions
def create_verification_code(
    db: Session, user_id: str, expires_minutes: int = 60
) -> str:
    """Create 6-digit email verification code"""
    code = _generate_code(6)

    verification = EmailVerification(
        user_id=user_id,
        code=code,
        expires_minutes=expires_minutes,
    )
    db.add(verification)
    db.commit()
    return code


def verify_email_code(db: Session, user_id: str, code: str) -> bool:
    """Verify email code and mark as used if valid"""
    now = datetime.now(UTC)

    verification = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.user_id == user_id,
            EmailVerification.code == code,
            EmailVerification.used == False,  # noqa: E712
            EmailVerification.expires_at > now,
        )
        .order_by(EmailVerification.created_at.desc())
        .first()
    )

    if verification:
        verification.used = True
        db.commit()
        return True

    return False


# Password reset functions
def create_password_reset_code(
    db: Session, user_id: str, expires_minutes: int = 30
) -> str:
    """Create 6-digit password reset code"""
    code = _generate_code(6)
    expires_at = datetime.now(UTC) + timedelta(minutes=expires_minutes)

    # Invalidate any existing unused reset codes for this user
    db.query(PasswordReset).filter(
        PasswordReset.user_id == user_id,
        PasswordReset.used == False,  # noqa: E712
    ).update({"used": True})

    reset = PasswordReset(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token=code,
        expires_at=expires_at,
    )
    db.add(reset)
    db.commit()
    return code


def verify_password_reset_code(db: Session, user_id: str, code: str) -> bool:
    """Verify password reset code (does not mark as used)"""
    now = datetime.now(UTC)

    reset = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.user_id == user_id,
            PasswordReset.token == code,
            PasswordReset.used == False,  # noqa: E712
            PasswordReset.expires_at > now,
        )
        .first()
    )

    return reset is not None


def mark_password_reset_used(db: Session, user_id: str, code: str) -> bool:
    """Mark password reset code as used"""
    rows = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.user_id == user_id,
            PasswordReset.token == code,
        )
        .update({"used": True})
    )
    db.commit()
    return rows > 0


# Email whitelist functions
def is_email_whitelisted(db: Session, email: str) -> bool:
    """Check if an email is whitelisted for registration"""
    email = email.lower().strip()

    patterns = (
        db.query(EmailWhitelist.pattern)
        .filter(EmailWhitelist.is_active == True)  # noqa: E712
        .all()
    )

    # If no active patterns, allow all emails (open registration)
    if not patterns:
        return True

    for (pattern,) in patterns:
        # Full email match
        if "@" in pattern and not pattern.startswith("@"):
            if email == pattern:
                return True
        # Domain match
        elif pattern.startswith("@") and email.endswith(pattern):
            return True

    return False


def add_whitelist_pattern(
    db: Session, pattern: str, description: str | None = None
) -> bool:
    """Add an email pattern to the whitelist"""
    # Normalize pattern
    pattern = pattern.lower().strip()
    if not pattern.startswith("@") and "@" not in pattern:
        pattern = "@" + pattern

    try:
        whitelist = EmailWhitelist(
            id=str(uuid.uuid4()),
            pattern=pattern,
            description=description,
        )
        db.add(whitelist)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def count_users(db: Session) -> int:
    """Count total number of users"""
    return db.query(User).count()
