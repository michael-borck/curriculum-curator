"""
Security utilities for authentication and password handling
"""

import hashlib
import hmac
import time as _time
import uuid
import warnings
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Suppress bcrypt version warning (known issue with bcrypt 4.2.0 and passlib)
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory JTI blacklist for token revocation
# Maps JTI → expiration timestamp; entries are cleaned up lazily
_blacklisted_jtis: dict[str, float] = {}


def blacklist_token(jti: str, exp: float) -> None:
    """Add a token JTI to the blacklist. It will be cleaned up after expiry."""
    _blacklisted_jtis[jti] = exp
    # Lazy cleanup: remove expired entries
    now = _time.time()
    expired = [k for k, v in _blacklisted_jtis.items() if v < now]
    for k in expired:
        _blacklisted_jtis.pop(k, None)


def is_token_blacklisted(jti: str) -> bool:
    """Check if a token JTI has been blacklisted."""
    if jti in _blacklisted_jtis:
        # Check if it's still valid (not expired)
        if _blacklisted_jtis[jti] >= _time.time():
            return True
        # Expired, clean it up
        _blacklisted_jtis.pop(jti, None)
    return False


def hash_one_time_code(code: str) -> str:
    """Keyed hash for short-lived verification/reset codes.

    A plain 6-digit code has only a million possibilities, so an unkeyed hash
    is reversible offline. HMAC with SECRET_KEY means the database alone is
    not enough to recover or brute-force the code.
    """
    normalized = code.strip().upper()
    return hmac.new(
        settings.SECRET_KEY.encode(), normalized.encode(), hashlib.sha256
    ).hexdigest()


def verify_one_time_code(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_one_time_code(code), code_hash)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    client_ip: str | None = None,
    user_role: str | None = None,
    session_id: str | None = None,
    token_version: int | None = None,
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
    now = datetime.now(UTC)

    # Set expiration
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Enhanced JWT payload as per Phase B specification
    to_encode.update(
        {
            "exp": expire,  # PyJWT converts datetimes to timestamps
            "iat": now,  # PyJWT converts datetimes to timestamps
            "jti": str(uuid.uuid4()),  # Unique token ID for blacklisting
            "ip": client_ip,  # Bind to IP address
            "role": user_role,  # Include role for authorization
            "sid": session_id or str(uuid.uuid4()),  # Session ID
        }
    )
    if token_version is not None:
        to_encode["tv"] = token_version

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_mfa_token(
    user_id: str,
    token_version: int | None = None,
    client_ip: str | None = None,
) -> str:
    """Short-lived token proving the password step succeeded."""
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "type": "mfa",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "jti": str(uuid.uuid4()),
        "ip": client_ip,
    }
    if token_version is not None:
        payload["tv"] = token_version
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_mfa_token(
    token: str, verify_ip: str | None = None
) -> dict[str, Any] | None:
    """Decode an MFA challenge token; rejects access/refresh tokens."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "mfa":
        return None
    if verify_ip and payload.get("ip") and payload.get("ip") != verify_ip:
        return None
    jti = payload.get("jti", "")
    if jti and is_token_blacklisted(jti):
        return None
    return payload


def create_webauthn_challenge(
    kind: str, challenge_b64: str, user_id: str | None = None
) -> str:
    """Short-lived signed challenge for a WebAuthn options/verify round-trip."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "type": f"webauthn:{kind}",
        "challenge": challenge_b64,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if user_id:
        payload["sub"] = user_id
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_webauthn_challenge(token: str, kind: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except jwt.PyJWTError:
        return None
    if payload.get("type") != f"webauthn:{kind}":
        return None
    jti = payload.get("jti", "")
    if jti and is_token_blacklisted(jti):
        return None
    return payload


def create_refresh_token(user_id: str, client_ip: str | None = None) -> str:
    """
    Create a refresh token for JWT token renewal.

    Args:
        user_id: User identifier
        client_ip: Client IP address

    Returns:
        str: Encoded refresh token
    """
    now = datetime.now(UTC)
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


def decode_access_token(
    token: str, verify_ip: str | None = None
) -> dict[str, Any] | None:
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

        # Check if token has been revoked
        jti = payload.get("jti", "")
        if jti and is_token_blacklisted(jti):
            return None

        # Access tokens only — refresh/MFA challenges are not access tokens.
        if payload.get("type") in ("refresh", "mfa"):
            return None

        # Verify IP binding if both token IP and verify IP are provided
        if verify_ip and payload.get("ip") and payload.get("ip") != verify_ip:
            return None  # IP mismatch - token stolen/hijacked

        return payload
    except jwt.PyJWTError:
        return None


def validate_token_security(
    payload: dict[str, Any], client_ip: str | None = None
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
    now = datetime.now(UTC).timestamp()
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


def extract_token_info(payload: dict[str, Any]) -> dict[str, Any]:
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
