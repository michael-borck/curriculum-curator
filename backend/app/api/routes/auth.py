"""
Authentication routes with complete user registration and verification system.

Uses SQLAlchemy ORM via repositories.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.password_validator import PasswordValidator
from app.core.rate_limiter import RateLimits, limiter
from app.repositories import security_repo, user_repo
from app.schemas import (
    EmailVerificationRequest,
    EmailVerificationResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
    UserResponse,
)
from app.schemas.user import UserCreate
from app.services.email_service import email_service

router = APIRouter()


# =========================================================================
# Public configuration endpoint (no auth required)
# =========================================================================


@router.get("/config")
async def get_auth_config():
    """Public endpoint to discover app configuration (e.g. local mode)."""
    return {"local_mode": settings.LOCAL_MODE}


@router.get("/local-session")
async def get_local_session(
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
    )

    return LoginResponse(
        access_token=access_token,
        user=local_user,
    )


# =========================================================================
# Standard auth endpoints
# =========================================================================


def _get_client_ip(request: Request) -> str:
    """Get client IP address from request, handling proxies"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def _get_user_agent(request: Request) -> str:
    """Get user agent from request"""
    return request.headers.get("User-Agent", "Unknown")[:500]


@router.post("/register", response_model=UserRegistrationResponse)
@limiter.limit(RateLimits.REGISTER)
async def register(
    request: Request,
    user_request: UserRegistrationRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Register a new user with email verification"""
    email = user_request.email.lower().strip()

    # Check if email is whitelisted
    if not user_repo.is_email_whitelisted(db, email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not authorized for registration. Please contact your administrator.",
        )

    # Enhanced password validation
    is_valid, password_errors = PasswordValidator.validate_password(
        user_request.password, user_request.name, email
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

    # Check if user already exists
    existing_user = user_repo.get_user_by_email(db, email)
    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )
        # User exists but not verified - resend verification
        verification_code = user_repo.create_verification_code(db, existing_user.id)
        email_sent = await email_service.send_verification_email(
            existing_user, verification_code, expires_minutes=60
        )
        if email_sent:
            return UserRegistrationResponse(
                message="Verification email sent. Please check your inbox for the 6-digit code.",
                user_email=existing_user.email,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again.",
        )

    try:
        # Check if this is the first user (becomes admin)
        user_count = user_repo.count_users(db)
        is_first_user = user_count == 0

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
            return UserRegistrationResponse(
                message="Registration successful! Please check your email for the verification code.",
                user_email=email,
            )

        # Email failed - we should still allow the user to exist
        # They can request resend
        return UserRegistrationResponse(
            message="Registration successful but email delivery failed. Please use 'Resend Verification' to get your code.",
            user_email=email,
        )

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

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires,
    )

    # Refresh user data after verification
    verified_user = user_repo.get_user_by_id(db, user.id)
    if not verified_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve verified user",
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
    login_data: LoginRequest,
    db: Annotated[Session, Depends(deps.get_db)],
):
    """Simple JSON-based login endpoint"""
    client_ip = _get_client_ip(request)
    user_agent = _get_user_agent(request)
    email = login_data.email.lower().strip()

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
    login_success = user and security.verify_password(
        login_data.password, user.password_hash
    )

    if login_success:
        security_repo.record_login_success(db, email, client_ip, user_agent)
    else:
        security_repo.record_login_failure(
            db, email, client_ip, user_agent, "Invalid credentials"
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
            detail={
                "error": "email_not_verified",
                "message": "Email address not verified. Please check your email for the verification code.",
                "email": user.email,
                "action": "redirect_to_verification",
            },
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires,
        client_ip=client_ip,
        user_role=user.role,
        session_id=None,
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

    return LoginResponse(
        access_token=access_token,
        user=public_user,
    )


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

    try:
        # Update password
        user_repo.update_password(db, user.id, reset_request.new_password)

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


@router.get("/me", response_model=UserResponse)
async def get_user_profile(
    current_user: UserResponse = Depends(deps.get_current_active_user),
):
    """Get current user information"""
    return current_user
