"""
Security utilities for authentication and password handling
"""

import uuid
import warnings
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Suppress bcrypt version warning (known issue with bcrypt 4.2.0 and passlib)
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    client_ip: str | None = None,
    user_role: str | None = None,
    session_id: str | None = None,
) -> str:
    """
    Create a JWT access token with enhanced security fields.

    Args:
        data: Base token data (must include 'sub' for user_id)
        expires_delta: Token expiration time
        client_ip: Client IP address to bind token to
        user_role: User role for authorization
        session_id: Session identifier

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    now = datetime.utcnow()

    # Set expiration
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Enhanced JWT payload as per Phase B specification
    to_encode.update(
        {
            "exp": expire,  # Let python-jose handle the timestamp conversion
            "iat": now,  # Let python-jose handle the timestamp conversion
            "jti": str(uuid.uuid4()),  # Unique token ID for blacklisting
            "ip": client_ip,  # Bind to IP address
            "role": user_role,  # Include role for authorization
            "sid": session_id or str(uuid.uuid4()),  # Session ID
        }
    )

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str, client_ip: str | None = None) -> str:
    """
    Create a refresh token for JWT token renewal.

    Args:
        user_id: User identifier
        client_ip: Client IP address

    Returns:
        str: Encoded refresh token
    """
    now = datetime.utcnow()
    expire = now + timedelta(days=7)  # Refresh tokens last 7 days

    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
        "ip": client_ip,
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str, verify_ip: str | None = None) -> dict | None:
    """
    Decode and verify a JWT access token with enhanced security checks.

    Args:
        token: JWT token to decode
        verify_ip: Client IP to verify against token IP binding

    Returns:
        dict: Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Verify IP binding if both token IP and verify IP are provided
        if verify_ip and payload.get("ip") and payload.get("ip") != verify_ip:
            return None  # IP mismatch - token stolen/hijacked

        return payload
    except JWTError:
        return None


def validate_token_security(
    payload: dict, client_ip: str | None = None
) -> tuple[bool, str]:
    """
    Validate JWT token security aspects.

    Args:
        payload: Decoded JWT payload
        client_ip: Current client IP address

    Returns:
        tuple[bool, str]: (is_valid, error_reason)
    """
    if not payload:
        return False, "Invalid token"

    # Check if token is expired (redundant but explicit)
    now = datetime.utcnow().timestamp()
    if payload.get("exp", 0) < now:
        return False, "Token expired"

    # Check IP binding
    token_ip = payload.get("ip")
    if client_ip and token_ip and token_ip != client_ip:
        return False, "IP address mismatch - potential token theft"

    # Validate required fields
    required_fields = ["sub", "iat", "exp", "jti"]
    for field in required_fields:
        if field not in payload:
            return False, f"Missing required field: {field}"

    return True, ""


def extract_token_info(payload: dict) -> dict:
    """
    Extract security-relevant information from token payload.

    Args:
        payload: Decoded JWT payload

    Returns:
        dict: Token security information
    """
    return {
        "user_id": payload.get("sub"),
        "user_email": payload.get("email"),
        "user_role": payload.get("role"),
        "token_id": payload.get("jti"),
        "session_id": payload.get("sid"),
        "client_ip": payload.get("ip"),
        "issued_at": datetime.fromtimestamp(payload.get("iat", 0)),
        "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
        "is_refresh_token": payload.get("type") == "refresh",
    }
