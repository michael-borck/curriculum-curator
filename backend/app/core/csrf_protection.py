"""
CSRF Protection configuration for FastAPI
"""

from fastapi import HTTPException, Request
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic_settings import BaseSettings

from app.core.config import settings


class CsrfSettings(BaseSettings):
    """CSRF protection settings"""
    secret_key: str = settings.SECRET_KEY
    cookie_secure: bool = False  # Set to True in production with HTTPS
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None
    httponly: bool = True
    max_age: int = 3600  # 1 hour


# CSRF protection instance
csrf_protect = CsrfProtect()


def init_csrf_protection():
    """Initialize CSRF protection with settings"""
    @csrf_protect.load_config
    def get_config():  # type: ignore[reportUnusedFunction]
        return CsrfSettings()


async def validate_csrf_token(request: Request, csrf_protect_instance: CsrfProtect):
    """
    Validate CSRF token for state-changing operations

    Args:
        request: FastAPI request object
        csrf_protect_instance: CSRF protection instance

    Raises:
        HTTPException: If CSRF validation fails
    """
    try:
        await csrf_protect_instance.validate_csrf(request)
    except CsrfProtectError as e:
        raise HTTPException(
            status_code=403,
            detail=f"CSRF validation failed: {e!s}",
            headers={"WWW-Authenticate": "CSRF"}
        )


def get_csrf_token(request: Request, csrf_protect_instance: CsrfProtect) -> str:
    """
    Generate CSRF token for client use

    Args:
        request: FastAPI request object
        csrf_protect_instance: CSRF protection instance

    Returns:
        str: CSRF token
    """
    return csrf_protect_instance.generate_csrf(request)


# Exception handler for CSRF errors
def csrf_exception_handler(request: Request, exc: CsrfProtectError):
    """Handle CSRF protection errors"""
    return HTTPException(
        status_code=403,
        detail={
            "error": "CSRF Protection",
            "message": "CSRF token validation failed. Please refresh the page and try again.",
            "type": "csrf_error"
        }
    )
