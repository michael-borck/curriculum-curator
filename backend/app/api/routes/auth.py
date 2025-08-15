"""
Authentication routes with complete user registration and verification system
"""

import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.password_validator import PasswordValidator
from app.core.rate_limiter import RateLimits, limiter
from app.core.security_utils import SecurityManager
from app.models import EmailWhitelist, User, UserRole
from app.models.security_log import SecurityEventType
from app.schemas import (
    EmailVerificationRequest,
    EmailVerificationResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
    UserResponse,
)
from app.services.email_service import email_service
from app.services.security_logger import SecurityLogger
from app.utils.auth_helpers import auth_helpers

router = APIRouter()


@router.post("/register", response_model=UserRegistrationResponse)
@limiter.limit(RateLimits.REGISTER)
async def register(
    request: Request,
    user_request: UserRegistrationRequest,
    db: Session = Depends(deps.get_db),
):
    """Register a new user with email verification"""

    # No CSRF needed - protected by CORS + rate limiting

    # Check if email is whitelisted
    if not EmailWhitelist.is_email_whitelisted(db, user_request.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not authorized for registration. Please contact your administrator.",
        )

    # Enhanced password validation
    is_valid, password_errors = PasswordValidator.validate_password(
        user_request.password, user_request.name, user_request.email
    )

    if not is_valid:
        # Calculate password strength for user feedback
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
    existing_user = (
        db.query(User).filter(User.email == user_request.email.lower()).first()
    )
    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )
        # User exists but not verified - resend verification
        success, verification_code = await auth_helpers.create_and_send_verification(
            db, existing_user
        )
        if success:
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
        user_count = db.query(User).count()
        is_first_user = user_count == 0

        # Determine role - first user becomes admin
        user_role = UserRole.ADMIN.value if is_first_user else UserRole.LECTURER.value

        # Create new user
        new_user = User(
            id=uuid.uuid4(),
            email=user_request.email.lower().strip(),
            password_hash=security.get_password_hash(user_request.password),
            name=user_request.name.strip(),
            role=user_role,
            is_verified=False,
            is_active=True,
        )

        # If first user, auto-verify them (admin doesn't need email verification)
        if is_first_user:
            new_user.is_verified = True

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Send verification email (skip for first user/admin)
        if is_first_user:
            # First user is auto-verified and becomes admin
            SecurityLogger.log_authentication_event(
                db=db,
                event_type=SecurityEventType.LOGIN_SUCCESS,
                request=request,
                user=new_user,
                success=True,
                description=f"First user registered as admin: {new_user.email}",
            )

            return UserRegistrationResponse(
                message="Registration successful! You are the first user and have been granted admin privileges. You can now log in.",
                user_email=new_user.email,
            )
        # Regular user - send verification email
        success, verification_code = await auth_helpers.create_and_send_verification(
            db, new_user
        )

        if success:
            # Log successful registration
            SecurityLogger.log_authentication_event(
                db=db,
                event_type=SecurityEventType.LOGIN_SUCCESS,
                request=request,
                user=new_user,
                success=True,
                description=f"User registration successful for {new_user.email}",
            )

            return UserRegistrationResponse(
                message="Registration successful! Please check your email for the verification code.",
                user_email=new_user.email,
            )
        # Registration failed - remove user
        db.delete(new_user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Could not send verification email.",
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
@limiter.limit(RateLimits.VERIFY_EMAIL)
async def verify_email(
    request: Request,
    verification_request: EmailVerificationRequest,
    db: Session = Depends(deps.get_db),
):
    """Verify email with 6-digit code"""

    success, user, error_message = auth_helpers.verify_email_code(
        db, verification_request.email, verification_request.code
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message or "Email verification failed",
        )

    # Send welcome email
    await email_service.send_welcome_email(user)

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires,
    )

    return EmailVerificationResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            is_verified=user.is_verified,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        ),
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
@limiter.limit(RateLimits.RESEND_VERIFICATION)
async def resend_verification(
    request: Request,
    resend_request: ResendVerificationRequest,
    db: Session = Depends(deps.get_db),
):
    """Resend verification email"""

    user = db.query(User).filter(User.email == resend_request.email.lower()).first()
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

    success, verification_code = await auth_helpers.create_and_send_verification(
        db, user
    )

    return ResendVerificationResponse(
        message="If an account with this email exists and is unverified, a verification code has been sent."
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(RateLimits.LOGIN)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db),
):
    """OAuth2 compatible token login"""

    # NO CSRF on login endpoint - protected by CORS + rate limiting
    # Removing CSRF from login to fix authentication issues

    # Get client information for security tracking
    client_ip = SecurityManager.get_client_ip(request)
    user_agent = SecurityManager.get_user_agent(request)
    email = form_data.username.lower().strip()

    # Check for account lockout or IP rate limiting
    is_locked, lockout_reason, minutes_remaining = (
        SecurityManager.check_account_lockout(db, email, client_ip)
    )

    if is_locked:
        lockout_message = SecurityManager.get_lockout_status_message(
            is_locked, lockout_reason, minutes_remaining
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=lockout_message,
            headers={"Retry-After": str((minutes_remaining or 15) * 60)},
        )

    # Check for suspicious activity
    is_suspicious, suspicion_reason = SecurityManager.is_suspicious_activity(
        db, email, client_ip, user_agent
    )

    user = db.query(User).filter(User.email == email).first()
    login_success = user and security.verify_password(
        form_data.password, user.password_hash
    )

    # Record login attempt (success or failure)
    SecurityManager.record_login_attempt(
        db=db,
        email=email,
        ip_address=client_ip,
        user_agent=user_agent,
        success=login_success,
        user=user,
        failure_reason="Invalid credentials" if not login_success else None,
    )

    if not login_success:
        # Log failed login attempt
        SecurityLogger.log_authentication_event(
            db=db,
            event_type=SecurityEventType.LOGIN_FAILED,
            request=request,
            user=user,
            success=False,
            description=f"Login failed for {email}",
            details={"reason": "Invalid credentials", "email": email},
        )

        # Use generic message to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )

    if not user.is_verified:
        # Return a special status that frontend can handle to redirect to verification
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "email_not_verified",
                "message": "Email address not verified. Please check your email for the verification code.",
                "email": user.email,
                "action": "redirect_to_verification"
            }
        )

    # Create access token with enhanced security
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires,
        client_ip=client_ip,
        user_role=user.role,
        session_id=None,  # Could be generated if needed
    )

    # Log successful login
    SecurityLogger.log_authentication_event(
        db=db,
        event_type=SecurityEventType.LOGIN_SUCCESS,
        request=request,
        user=user,
        success=True,
        description=f"Login successful for {user.email}",
        details={"user_role": user.role},
    )

    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            is_verified=user.is_verified,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        ),
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit(RateLimits.FORGOT_PASSWORD)
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
    db: Session = Depends(deps.get_db),
):
    """Send password reset code to email"""

    user = db.query(User).filter(User.email == forgot_request.email.lower()).first()

    if user and user.is_verified and user.is_active:
        success, reset_code = await auth_helpers.create_and_send_password_reset(
            db, user
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email. Please try again.",
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
    db: Session = Depends(deps.get_db),
):
    """Reset password with verification code"""

    success, user, error_message = auth_helpers.verify_reset_code(
        db, reset_request.email, reset_request.code
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message or "Invalid or expired reset code",
        )

    try:
        # Update password
        user.password_hash = security.get_password_hash(reset_request.new_password)

        # Mark reset code as used
        auth_helpers.mark_reset_code_used(db, reset_request.email, reset_request.code)

        db.commit()

        return ResetPasswordResponse(
            message="Password reset successfully. You can now log in with your new password."
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again.",
        )


@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(deps.get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )
