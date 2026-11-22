"""
User repository - database operations for users

Handles all user-related database queries using SQLAlchemy ORM.
"""

import secrets
import string
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import (
    get_password_hash,
    hash_one_time_code,
    verify_one_time_code,
)
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
        totp_enabled=bool(getattr(user, "totp_enabled", False)),
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
        totp_enabled=bool(getattr(user, "totp_enabled", False)),
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


_UPDATABLE_USER_FIELDS = frozenset(
    {
        "name",
        "institution",
        "department",
        "position_title",
        "teaching_philosophy",
        "language_preference",
        "education_sector",
        "teaching_preferences",
        "content_generation_context",
        "llm_config",
        "role",
        "is_verified",
        "is_active",
        "token_version",
    }
)


def update_user(db: Session, user_id: str, **fields) -> UserResponse | None:
    """Update a user's profile fields (mass-assignment safe)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    for key, value in fields.items():
        if key in _UPDATABLE_USER_FIELDS:
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
    """Create 6-digit email verification code.

    Invalidates any existing unused codes for the user first, so exactly one
    code is valid at a time (mirrors ``create_password_reset_code`` and means a
    resend supersedes the previous code).
    """
    db.query(EmailVerification).filter(
        EmailVerification.user_id == user_id,
        EmailVerification.used == False,  # noqa: E712
    ).update({"used": True})

    code = _generate_code(6)

    verification = EmailVerification(
        user_id=user_id,
        code=code,
        expires_minutes=expires_minutes,
    )
    db.add(verification)
    db.commit()
    return code


_MAX_CODE_ATTEMPTS = 5


def verify_email_code(db: Session, user_id: str, code: str) -> bool:
    """Verify email code, marking it used on success or after too many misses."""
    now = datetime.now(UTC)

    verification = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.user_id == user_id,
            EmailVerification.used == False,  # noqa: E712
            EmailVerification.expires_at > now,
        )
        .order_by(EmailVerification.created_at.desc())
        .first()
    )

    if verification is None:
        return False
    if not verify_one_time_code(code, verification.code_hash):
        verification.attempts += 1
        if verification.attempts >= _MAX_CODE_ATTEMPTS:
            verification.used = True
        db.commit()
        return False

    verification.used = True
    db.commit()
    return True


def get_pending_verifications(
    db: Session,
) -> list[tuple[User, EmailVerification]]:
    """Return unverified users paired with their newest still-valid code.

    Powers the admin relay fallback for instances without SMTP. Users whose
    codes have all expired or been used are omitted — they need to request a
    resend to appear here again. Newest sign-ups first.
    """
    now = datetime.now(UTC)
    users = (
        db.query(User)
        .filter(User.is_verified == False)  # noqa: E712
        .order_by(User.created_at.desc())
        .all()
    )

    pending: list[tuple[User, EmailVerification]] = []
    for user in users:
        verification = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.user_id == user.id,
                EmailVerification.used == False,  # noqa: E712
                EmailVerification.expires_at > now,
            )
            .order_by(EmailVerification.created_at.desc())
            .first()
        )
        if verification is not None:
            pending.append((user, verification))
    return pending


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
    """Verify a password reset code (does not mark it used on success)."""
    now = datetime.now(UTC)

    reset = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.user_id == user_id,
            PasswordReset.used == False,  # noqa: E712
            PasswordReset.expires_at > now,
        )
        .order_by(PasswordReset.created_at.desc())
        .first()
    )

    if reset is None:
        return False
    if not verify_one_time_code(code, reset.token_hash):
        reset.attempts += 1
        if reset.attempts >= _MAX_CODE_ATTEMPTS:
            reset.used = True
        db.commit()
        return False
    return True


def mark_password_reset_used(db: Session, user_id: str, code: str) -> bool:
    """Mark password reset code as used"""
    rows = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.user_id == user_id,
            PasswordReset.token_hash == hash_one_time_code(code),
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

    # No active patterns means no one is authorised: fail closed rather than
    # silently allowing open registration. An enabled-but-empty whitelist is
    # almost always a configuration mistake.
    if not patterns:
        return False

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
