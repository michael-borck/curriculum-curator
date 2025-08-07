"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core import security
from app.core.config import settings
from app.api import deps

router = APIRouter()

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db)
):
    """
    OAuth2 compatible token login.
    """
    # Mock user verification for testing
    if form_data.username == "test@example.com" and form_data.password == "test":
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": "user123", "email": form_data.username},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/register")
async def register(
    email: str,
    password: str,
    name: str,
    db: Session = Depends(deps.get_db)
):
    """
    Register a new user.
    """
    hashed_password = security.get_password_hash(password)
    
    return {
        "message": "User registered successfully",
        "email": email,
        "name": name
    }

@router.get("/me")
async def get_current_user(
    current_user: dict = Depends(deps.get_current_active_user)
):
    """
    Get current user info.
    """
    return current_user
