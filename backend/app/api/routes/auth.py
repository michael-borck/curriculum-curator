"""
Authentication routes with complete user registration and verification system
"""

import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models import EmailWhitelist, User, UserRole
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
from app.utils.auth_helpers import auth_helpers

router = APIRouter()

@router.post("/register", response_model=UserRegistrationResponse)
async def register(
    request: UserRegistrationRequest,
    db: Session = Depends(deps.get_db)
):
    """Register a new user with email verification"""

    # Check if email is whitelisted
    if not EmailWhitelist.is_email_whitelisted(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not authorized for registration. Please contact your administrator."
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email.lower()).first()
    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists"
            )
        # User exists but not verified - resend verification
        success, verification_code = await auth_helpers.create_and_send_verification(
            db, existing_user
        )
        if success:
            return UserRegistrationResponse(
                message="Verification email sent. Please check your inbox for the 6-digit code.",
                user_email=existing_user.email
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )

    try:
        # Create new user
        new_user = User(
            id=uuid.uuid4(),
            email=request.email.lower().strip(),
            password_hash=security.get_password_hash(request.password),
            name=request.name.strip(),
            role=UserRole.USER.value,
            is_verified=False,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Send verification email
        success, verification_code = await auth_helpers.create_and_send_verification(
            db, new_user
        )

        if success:
            return UserRegistrationResponse(
                message="Registration successful! Please check your email for the verification code.",
                user_email=new_user.email
            )
        # Registration failed - remove user
        db.delete(new_user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Could not send verification email."
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(deps.get_db)
):
    """Verify email with 6-digit code"""

    success, user, error_message = auth_helpers.verify_email_code(
        db, request.email, request.code
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message or "Email verification failed"
        )

    # Send welcome email
    await email_service.send_welcome_email(user)

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
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
            created_at=user.created_at.isoformat()
        )
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(deps.get_db)
):
    """Resend verification email"""

    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user:
        # Don't reveal if user exists or not for security
        return ResendVerificationResponse(
            message="If an account with this email exists and is unverified, a verification code has been sent."
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is already verified"
        )

    success, verification_code = await auth_helpers.create_and_send_verification(db, user)

    return ResendVerificationResponse(
        message="If an account with this email exists and is unverified, a verification code has been sent."
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db)
):
    """OAuth2 compatible token login"""

    user = db.query(User).filter(User.email == form_data.username.lower()).first()

    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Please check your email for the verification code."
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
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
            created_at=user.created_at.isoformat()
        )
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(deps.get_db)
):
    """Send password reset code to email"""

    user = db.query(User).filter(User.email == request.email.lower()).first()

    if user and user.is_verified and user.is_active:
        success, reset_code = await auth_helpers.create_and_send_password_reset(db, user)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email. Please try again."
            )

    # Always return success message to prevent email enumeration
    return ForgotPasswordResponse(
        message="If an account with this email exists, a password reset code has been sent."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(deps.get_db)
):
    """Reset password with verification code"""

    success, user, error_message = auth_helpers.verify_reset_code(
        db, request.email, request.code
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message or "Invalid or expired reset code"
        )

    try:
        # Update password
        user.password_hash = security.get_password_hash(request.new_password)

        # Mark reset code as used
        auth_helpers.mark_reset_code_used(db, request.email, request.code)

        db.commit()

        return ResetPasswordResponse(
            message="Password reset successfully. You can now log in with your new password."
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again."
        )


@router.get("/me", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )
