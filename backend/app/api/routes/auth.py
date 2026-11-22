"""
Authentication routes with complete user registration and verification system.

Uses SQLAlchemy ORM via repositories.
"""

import logging
import secrets
from datetime import timedelta
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pyotp.totp import TOTP
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core import totp as totp_utils
from app.core.config import settings
from app.core.password_validator import PasswordValidator
from app.core.rate_limiter import RateLimits, limiter
from app.core.secret_crypto import decrypt_secret, encrypt_secret
from app.core.security import hash_one_time_code
from app.core.security_settings import get_security_settings
from app.core.setup_token import rotate_setup_token, verify_setup_token
from app.models.login_token import LoginToken
from app.models.user import User
from app.repositories import security_repo, user_repo
from app.schemas import (
    EmailVerificationRequest,
    EmailVerificationResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    MagicLinkVerifyRequest,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TOTPDisableRequest,
    TOTPEnableRequest,
    TOTPSetupResponse,
    TOTPStatusResponse,
    TOTPVerifyRequest,
    UserRegistrationRequest,
    UserRegistrationResponse,
    UserResponse,
)
from app.schemas.auth import ChangePasswordRequest, ChangePasswordResponse
from app.schemas.user import ProfileUpdateRequest, UserCreate
from app.services.email_service import email_service
from app.utils.request_ip import get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter()

# Used to equalise bcrypt work when the account does not exist, so login
# timing does not reveal which emails are registered.
_DUMMY_PASSWORD_HASH = security.get_password_hash(secrets.token_urlsafe(32))

# Serialises first-user bootstrap; see register().
_FIRST_USER_LOCK = Lock()


# =========================================================================
# Public configuration endpoint (no auth required)
# =========================================================================


@router.get("/config")
async def get_auth_config(
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Public endpoint to discover app configuration (e.g. local mode, setup status)."""
    has_users = user_repo.count_users(db) > 0
    return {"localMode": settings.LOCAL_MODE, "hasUsers": has_users}


@router.get("/local-session")
async def get_local_session(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """
    Get a JWT token and user profile for the local default user.
    Only works when LOCAL_MODE=true; returns 404 otherwise.
    """
    if not settings.LOCAL_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    local_user = user_repo.get_user_by_id(db, deps.LOCAL_USER_ID)
    if not local_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Local user not found. Ensure LOCAL_MODE startup completed.",
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    access_token = security.create_access_token(
        data={"sub": deps.LOCAL_USER_ID, "email": deps.LOCAL_USER_EMAIL},
        expires_delta=access_token_expires,
        client_ip=_get_client_ip(request),
        user_role=local_user.role,
        token_version=getattr(local_user, "token_version", 0),
    )

    _set_session_cookies(
        response,
        request,
        access_token,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return LoginResponse(
        access_token=access_token,
        user=local_user,
    )


# =========================================================================
# Standard auth endpoints
# =========================================================================


def _get_client_ip(request: Request) -> str:
    """Get client IP address from request.

    Proxy headers are honoured only when ``TRUST_PROXY_HEADERS`` is set, so
    lockout and JWT IP-binding can't be bypassed by spoofing them.
    """
    return get_client_ip(request)


def _get_user_agent(request: Request) -> str:
    """Get user agent from request"""
    return request.headers.get("User-Agent", "Unknown")[:500]


def _is_https(request: Request) -> bool:
    forwarded = request.headers.get("x-forwarded-proto", "").lower()
    return request.url.scheme == "https" or forwarded == "https"


def _set_session_cookies(
    response: Response, request: Request, token: str, minutes: int
) -> None:
    """Store the access token in an httpOnly cookie plus a readable CSRF token."""
    secure = _is_https(request)
    max_age = minutes * 60
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=secrets.token_urlsafe(32),
        max_age=max_age,
        httponly=False,
        samesite="lax",
        secure=secure,
        path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")


@router.post("/register", response_model=UserRegistrationResponse)
@limiter.limit(RateLimits.REGISTER)
async def register(
    request: Request,
    user_request: UserRegistrationRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Register a new user with email verification"""
    email = user_request.email.lower().strip()
    security_settings = get_security_settings(db)

    if not security_settings.enable_user_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User registration is currently disabled. Please contact your administrator.",
        )

    # Check if email is whitelisted (unless the whitelist is disabled).
    # The first user is the bootstrap admin and has no whitelist to consult.
    user_count = user_repo.count_users(db)
    is_first_user = user_count == 0
    if (
        not is_first_user
        and security_settings.enable_email_whitelist
        and not user_repo.is_email_whitelisted(db, email)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not authorized for registration. Please contact your administrator.",
        )

    if is_first_user and not verify_setup_token(user_request.setup_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "This is the first account and it becomes the administrator. "
                "Enter the setup token from the server (SETUP_TOKEN or the "
                "setup_token file beside the database)."
            ),
        )

    # Enhanced password validation
    is_valid, password_errors = PasswordValidator.validate_password(
        user_request.password, user_request.name, email, policy=security_settings
    )

    if not is_valid:
        strength_score, strength_desc = PasswordValidator.get_password_strength_score(
            user_request.password
        )
        suggestions = PasswordValidator.suggest_improvements(
            user_request.password, password_errors
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Password validation failed",
                "issues": password_errors,
                "suggestions": suggestions,
                "strength_score": strength_score,
                "strength": strength_desc,
                "message": "Password does not meet security requirements. Please choose a stronger password.",
            },
        )

    # Enumeration-resistant: the response never reveals whether the address
    # already has an account. A verified account simply gets no new email.
    generic_message = (
        "If this email address can be registered, a verification code has "
        "been sent to it."
    )

    existing_user = user_repo.get_user_by_email(db, email)
    if existing_user:
        if not existing_user.is_verified:
            verification_code = user_repo.create_verification_code(
                db, existing_user.id
            )
            await email_service.send_verification_email(
                existing_user, verification_code, expires_minutes=60
            )
        return UserRegistrationResponse(
            message=generic_message, user_email=existing_user.email
        )

    try:
        # Serialise first-user promotion so two concurrent registrations cannot
        # both become admin, and re-check after taking the lock.
        with _FIRST_USER_LOCK:
            is_first_user = user_repo.count_users(db) == 0
            if is_first_user and not verify_setup_token(user_request.setup_token):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="The setup token is no longer valid.",
                )

            # Create new user
            user_data = UserCreate(
                email=email,
                password=user_request.password,
                name=user_request.name.strip(),
            )
            new_user = user_repo.create_user(db, user_data)

            # Update role if first user
            if is_first_user:
                user_repo.update_user(db, new_user.id, role="admin", is_verified=True)
                rotate_setup_token()

            # Log security event
            security_repo.log_security_event(
                db,
                event_type="login_success",
                ip_address=_get_client_ip(request),
                user_id=new_user.id,
                user_email=email,
                user_role="admin",
                user_agent=_get_user_agent(request),
                request_path=str(request.url.path),
                request_method=request.method,
                description=f"First user registered as admin: {email}",
                severity="info",
                success="success",
            )
            return UserRegistrationResponse(
                message="Registration successful! You are the first user and have been granted admin privileges. You can now log in.",
                user_email=email,
            )

        # Send verification email
        verification_code = user_repo.create_verification_code(db, new_user.id)
        email_sent = await email_service.send_verification_email_by_address(
            email=email,
            name=user_request.name.strip(),
            verification_code=verification_code,
            expires_minutes=60,
        )

        if email_sent:
            security_repo.log_security_event(
                db,
                event_type="registration_success",
                ip_address=_get_client_ip(request),
                user_id=new_user.id,
                user_email=email,
                user_role="lecturer",
                user_agent=_get_user_agent(request),
                request_path=str(request.url.path),
                request_method=request.method,
                description=f"User registration successful for {email}",
                severity="info",
                success="success",
            )
        else:
            logger.warning("Verification email delivery failed for a new sign-up")

        return UserRegistrationResponse(message=generic_message, user_email=email)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        ) from None


@router.post("/verify-email", response_model=EmailVerificationResponse)
@limiter.limit(RateLimits.VERIFY_EMAIL)
async def verify_email(
    request: Request,
    response: Response,
    verification_request: EmailVerificationRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Verify email with 6-digit code"""
    email = verification_request.email.lower().strip()

    # Find user by email
    user = user_repo.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Verify the code
    if not user_repo.verify_email_code(db, user.id, verification_request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    # Mark user as verified
    user_repo.verify_user(db, user.id)

    # Send welcome email
    user_data = user_repo.get_user_by_id(db, user.id)
    if user_data:
        await email_service.send_welcome_email(user_data)

    # Create access token (admin-configured session timeout)
    access_token_expires = timedelta(
        minutes=get_security_settings(db).session_timeout_minutes
    )
    access_token = security.create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires,
        client_ip=_get_client_ip(request),
        user_role=user.role,
        token_version=getattr(user, "token_version", 0),
    )

    # Refresh user data after verification
    verified_user = user_repo.get_user_by_id(db, user.id)
    if not verified_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve verified user",
        )

    _set_session_cookies(
        response,
        request,
        access_token,
        get_security_settings(db).session_timeout_minutes,
    )
    return EmailVerificationResponse(
        access_token=access_token,
        user=verified_user,
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
@limiter.limit(RateLimits.RESEND_VERIFICATION)
async def resend_verification(
    request: Request,
    resend_request: ResendVerificationRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Resend verification email"""
    email = resend_request.email.lower().strip()
    user = user_repo.get_user_by_email(db, email)

    if not user:
        # Don't reveal if user exists or not for security
        return ResendVerificationResponse(
            message="If an account with this email exists and is unverified, a verification code has been sent."
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is already verified",
        )

    verification_code = user_repo.create_verification_code(db, user.id)
    await email_service.send_verification_email(
        user, verification_code, expires_minutes=60
    )

    return ResendVerificationResponse(
        message="If an account with this email exists and is unverified, a verification code has been sent."
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(RateLimits.LOGIN)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Simple JSON-based login endpoint"""
    client_ip = _get_client_ip(request)
    user_agent = _get_user_agent(request)
    email = login_data.email.lower().strip()
    security_settings = get_security_settings(db)

    # Check for account lockout
    is_locked, lockout_reason, minutes_remaining = security_repo.check_account_lockout(
        db, email, client_ip
    )

    if is_locked:
        lockout_message = security_repo.get_lockout_message(
            is_locked, lockout_reason, minutes_remaining
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=lockout_message,
            headers={"Retry-After": str((minutes_remaining or 15) * 60)},
        )

    user = user_repo.get_user_by_email(db, email)
    password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
    password_ok = security.verify_password(login_data.password, password_hash)
    login_success = bool(user) and password_ok

    if login_success and user is not None and user.totp_enabled:
        public_user = user_repo.get_user_by_id(db, user.id)
        if public_user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user data",
            )
        return LoginResponse(
            access_token=None,
            user=public_user,
            mfa_required=True,
            mfa_token=security.create_mfa_token(
                user.id,
                token_version=getattr(user, "token_version", 0),
                client_ip=client_ip,
            ),
        )

    if login_success:
        security_repo.record_login_success(db, email, client_ip, user_agent)
    else:
        security_repo.record_login_failure(
            db,
            email,
            client_ip,
            user_agent,
            "Invalid credentials",
            max_attempts=security_settings.max_login_attempts,
            lockout_minutes=security_settings.lockout_duration_minutes,
        )

    if not login_success:
        security_repo.log_security_event(
            db,
            event_type="login_failed",
            ip_address=client_ip,
            user_id=user.id if user else None,
            user_email=email,
            user_agent=user_agent,
            request_path=str(request.url.path),
            request_method=request.method,
            description=f"Login failed for {email}",
            severity="warning",
            success="failure",
            details={"reason": "Invalid credentials", "email": email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # User exists at this point
    assert user is not None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect email or password",
        )

    # Create access token (admin-configured session timeout)
    access_token_expires = timedelta(minutes=security_settings.session_timeout_minutes)
    access_token = security.create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires,
        client_ip=client_ip,
        user_role=user.role,
        session_id=None,
        token_version=getattr(user, "token_version", 0),
    )

    # Log successful login
    security_repo.log_security_event(
        db,
        event_type="login_success",
        ip_address=client_ip,
        user_id=user.id,
        user_email=user.email,
        user_role=user.role,
        user_agent=user_agent,
        request_path=str(request.url.path),
        request_method=request.method,
        description=f"Login successful for {user.email}",
        severity="info",
        success="success",
        details={"user_role": user.role},
    )

    # Get public user response (without password_hash)
    public_user = user_repo.get_user_by_id(db, user.id)
    if not public_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user data",
        )

    _set_session_cookies(
        response, request, access_token, security_settings.session_timeout_minutes
    )
    return LoginResponse(
        access_token=access_token,
        user=public_user,
    )


@router.post("/magic-link", response_model=MagicLinkResponse)
@limiter.limit(RateLimits.FORGOT_PASSWORD)
async def request_magic_link(
    request: Request,
    body: MagicLinkRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Email a one-time sign-in link. Never reveals whether the account exists."""
    email = body.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user and user.is_active and user.is_verified:
        token = secrets.token_urlsafe(32)
        db.query(LoginToken).filter(
            LoginToken.user_id == user.id,
            LoginToken.used == False,  # noqa: E712
        ).update({"used": True})
        db.add(
            LoginToken(
                user_id=user.id,
                token_hash=hash_one_time_code(token),
                expires_minutes=15,
            )
        )
        db.commit()
        link = f"{settings.frontend_url}/auth/magic#token={token}"
        await email_service.send_magic_link_email(user, link, expires_minutes=15)

    return MagicLinkResponse(
        message="If that email can sign in, a one-time link has been sent."
    )


@router.post("/magic-link/verify", response_model=LoginResponse)
@limiter.limit(RateLimits.LOGIN)
async def verify_magic_link(
    request: Request,
    response: Response,
    body: MagicLinkVerifyRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Consume a magic-link token and start a session (or the TOTP step)."""
    from datetime import UTC, datetime  # noqa: PLC0415

    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="This link is invalid or has expired",
    )
    row = (
        db.query(LoginToken)
        .filter(
            LoginToken.token_hash == hash_one_time_code(body.token),
            LoginToken.used == False,  # noqa: E712
            LoginToken.expires_at > datetime.now(UTC),
        )
        .order_by(LoginToken.created_at.desc())
        .first()
    )
    if row is None:
        raise invalid
    user = db.query(User).filter(User.id == row.user_id).first()
    if user is None or not user.is_active or not user.is_verified:
        raise invalid

    row.used = True
    db.commit()

    public_user = user_repo.get_user_by_id(db, user.id)
    if public_user is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve user data")

    if user.totp_enabled:
        return LoginResponse(
            access_token=None,
            user=public_user,
            mfa_required=True,
            mfa_token=security.create_mfa_token(
                user.id,
                token_version=getattr(user, "token_version", 0),
                client_ip=_get_client_ip(request),
            ),
        )

    client_ip = _get_client_ip(request)
    security_repo.record_login_success(
        db, user.email, client_ip, _get_user_agent(request)
    )
    access_token_expires = timedelta(
        minutes=get_security_settings(db).session_timeout_minutes
    )
    access_token = security.create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires,
        client_ip=client_ip,
        user_role=user.role,
        token_version=getattr(user, "token_version", 0),
    )
    _set_session_cookies(
        response,
        request,
        access_token,
        get_security_settings(db).session_timeout_minutes,
    )
    return LoginResponse(access_token=access_token, user=public_user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit(RateLimits.FORGOT_PASSWORD)
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Send password reset code to email"""
    email = forgot_request.email.lower().strip()
    user = user_repo.get_user_by_email(db, email)

    if user and user.is_verified and user.is_active:
        reset_code = user_repo.create_password_reset_code(db, user.id)
        await email_service.send_password_reset_email(
            user, reset_code, expires_minutes=30
        )

    # Always return success message to prevent email enumeration
    return ForgotPasswordResponse(
        message="If an account with this email exists, a password reset code has been sent."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit(RateLimits.RESET_PASSWORD)
async def reset_password(
    request: Request,
    reset_request: ResetPasswordRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Reset password with verification code"""
    email = reset_request.email.lower().strip()

    # Find user by email
    user = user_repo.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code",
        )

    # Verify the reset code
    if not user_repo.verify_password_reset_code(db, user.id, reset_request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code",
        )

    # Validate new password strength
    is_valid, password_errors = PasswordValidator.validate_password(
        reset_request.new_password, "", email, policy=get_security_settings(db)
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Password validation failed",
                "issues": password_errors,
                "message": "New password does not meet security requirements.",
            },
        )

    try:
        # Update password
        user_repo.update_password(db, user.id, reset_request.new_password)

        # Invalidate every token issued before this reset.
        orm_user = db.query(User).filter(User.id == user.id).first()
        if orm_user is not None:
            orm_user.token_version = (orm_user.token_version or 0) + 1
            db.commit()

        # Mark reset code as used
        user_repo.mark_password_reset_used(db, user.id, reset_request.code)

        return ResetPasswordResponse(
            message="Password reset successfully. You can now log in with your new password."
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again.",
        ) from None


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    change_request: ChangePasswordRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    """Change password for the currently authenticated user"""
    # Look up the full user record (with password_hash)
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not security.verify_password(
        change_request.current_password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Ensure new password is different
    if change_request.current_password == change_request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Validate new password strength
    is_valid, password_errors = PasswordValidator.validate_password(
        change_request.new_password,
        "",
        current_user.email,
        policy=get_security_settings(db),
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Password validation failed",
                "issues": password_errors,
                "message": "New password does not meet security requirements.",
            },
        )

    try:
        user_repo.update_password(db, user.id, change_request.new_password)
        # Invalidate outstanding tokens on every other device.
        user.token_version = (user.token_version or 0) + 1
        db.commit()
        return ChangePasswordResponse(message="Password changed successfully")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password. Please try again.",
        ) from None


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    _current_user: UserResponse = Depends(deps.get_current_active_user),
):
    """Revoke the caller's access token immediately."""
    _clear_session_cookies(response)
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        payload = security.decode_access_token(header[7:])
        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                security.blacklist_token(jti, float(exp))
    return {"message": "Logged out"}


@router.get("/totp/status", response_model=TOTPStatusResponse)
async def totp_status(
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    user = db.query(User).filter(User.id == str(current_user.id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return TOTPStatusResponse(
        enabled=bool(user.totp_enabled),
        recovery_codes_remaining=len(user.totp_recovery_hashes or []),
    )


@router.post("/totp/setup", response_model=TOTPSetupResponse)
@limiter.limit(RateLimits.API_WRITE)
async def totp_setup(
    request: Request,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    """Create a pending TOTP secret and one-time recovery codes."""
    user = db.query(User).filter(User.id == str(current_user.id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP is already enabled. Disable it before setting up again.",
        )

    secret = totp_utils.generate_secret()
    recovery_codes = totp_utils.generate_recovery_codes()
    user.totp_secret = encrypt_secret(secret)
    user.totp_recovery_hashes = totp_utils.hash_recovery_codes(recovery_codes)
    user.totp_enabled = False
    user.totp_last_counter = 0
    db.commit()

    return TOTPSetupResponse(
        secret=secret,
        otpauth_url=totp_utils.provisioning_uri(secret, user.email, settings),
        recovery_codes=recovery_codes,
    )


@router.post("/totp/enable", response_model=TOTPStatusResponse)
@limiter.limit(RateLimits.API_WRITE)
async def totp_enable(
    request: Request,
    body: TOTPEnableRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    user = db.query(User).filter(User.id == str(current_user.id)).first()
    if not user or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start TOTP setup first",
        )
    secret = decrypt_secret(user.totp_secret)
    if not secret or not TOTP(secret).verify(body.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code"
        )

    user.totp_enabled = True
    db.commit()
    return TOTPStatusResponse(
        enabled=True,
        recovery_codes_remaining=len(user.totp_recovery_hashes or []),
    )


@router.post("/totp/disable", response_model=TOTPStatusResponse)
@limiter.limit(RateLimits.API_WRITE)
async def totp_disable(
    request: Request,
    body: TOTPDisableRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    user = db.query(User).filter(User.id == str(current_user.id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not security.verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if user.totp_enabled:
        valid = False
        secret = decrypt_secret(user.totp_secret)
        if secret and body.code and body.code.isdigit():
            valid, _ = totp_utils.verify_totp(
                secret, body.code, user.totp_last_counter
            )
        if not valid and body.code:
            valid, remaining = totp_utils.consume_recovery_code(
                user.totp_recovery_hashes, body.code
            )
            if valid:
                user.totp_recovery_hashes = remaining
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A current TOTP or recovery code is required",
            )

    user.totp_secret = None
    user.totp_enabled = False
    user.totp_recovery_hashes = None
    user.totp_last_counter = 0
    db.commit()
    return TOTPStatusResponse(enabled=False, recovery_codes_remaining=0)


@router.post("/totp/verify", response_model=LoginResponse)
@limiter.limit(RateLimits.VERIFY_EMAIL)
async def totp_verify(
    request: Request,
    response: Response,
    body: TOTPVerifyRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Complete a password login that requires TOTP."""
    payload = security.decode_mfa_token(
        body.mfa_token, verify_ip=_get_client_ip(request)
    )
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification session",
        )
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if (
        user is None
        or not user.is_active
        or not user.is_verified
        or payload.get("tv", 0) != getattr(user, "token_version", 0)
        or not user.totp_enabled
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification session",
        )

    valid = False
    secret = decrypt_secret(user.totp_secret)
    if secret and body.code.isdigit():
        valid, counter = totp_utils.verify_totp(
            secret, body.code, user.totp_last_counter
        )
        if valid:
            user.totp_last_counter = counter
    if not valid:
        valid, remaining = totp_utils.consume_recovery_code(
            user.totp_recovery_hashes, body.code
        )
        if valid:
            user.totp_recovery_hashes = remaining

    if not valid:
        security_repo.record_login_failure(
            db,
            user.email,
            _get_client_ip(request),
            _get_user_agent(request),
            "Invalid TOTP code",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid code",
        )

    db.commit()
    client_ip = _get_client_ip(request)
    security_repo.record_login_success(
        db, user.email, client_ip, _get_user_agent(request)
    )
    access_token_expires = timedelta(
        minutes=get_security_settings(db).session_timeout_minutes
    )
    access_token = security.create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires,
        client_ip=client_ip,
        user_role=user.role,
        token_version=getattr(user, "token_version", 0),
    )
    public_user = user_repo.get_user_by_id(db, user.id)
    if not public_user:
        raise HTTPException(status_code=500, detail="Failed to retrieve user data")
    _set_session_cookies(
        response,
        request,
        access_token,
        get_security_settings(db).session_timeout_minutes,
    )
    return LoginResponse(access_token=access_token, user=public_user)


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    db: Annotated[Session, Depends(deps.get_db)],
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    """Update current user profile fields"""
    update_fields: dict[str, object] = {}
    for field_name in (
        "name",
        "institution",
        "department",
        "teaching_philosophy",
        "language_preference",
        "education_sector",
    ):
        value = getattr(profile_data, field_name)
        if value is not None:
            update_fields[field_name] = value

    # Merge teaching_preferences with existing JSON rather than replace
    if profile_data.teaching_preferences is not None:
        existing = current_user.teaching_preferences or {}
        merged = {**existing, **profile_data.teaching_preferences}
        update_fields["teaching_preferences"] = merged

    if not update_fields:
        return current_user

    updated_user = user_repo.update_user(db, current_user.id, **update_fields)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )
    return updated_user


@router.get("/me", response_model=UserResponse)
async def get_user_profile(
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    """Get current user information"""
    return current_user
