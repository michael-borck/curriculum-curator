#!/usr/bin/env python3
"""Test JWT token timing to debug expiration issues"""

import time
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from app.core.security import create_access_token


def test_token_timing():
    print("Testing JWT token timing...")
    print(f"Current UTC time: {datetime.utcnow()}")
    print(f"Current local time: {datetime.now()}")
    print(f"Token expiration minutes: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")

    # Create a token
    data = {"sub": "test-user", "email": "test@example.com"}
    token = create_access_token(
        data=data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        client_ip="127.0.0.1",
        user_role="admin",
    )

    print(f"\nToken created: {token[:50]}...")

    # Decode immediately
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        print("\n✓ Token decoded successfully!")

        # Check timestamps
        iat = payload.get("iat")
        exp = payload.get("exp")

        iat_dt = datetime.fromtimestamp(iat)
        exp_dt = datetime.fromtimestamp(exp)

        print(f"Issued at (iat): {iat} => {iat_dt}")
        print(f"Expires at (exp): {exp} => {exp_dt}")
        print(f"Duration: {(exp_dt - iat_dt).total_seconds() / 60:.1f} minutes")

        # Check if expired
        now = datetime.utcnow()
        print(f"\nCurrent UTC: {now}")
        print(f"Token expires in: {(exp_dt - now).total_seconds() / 60:.1f} minutes")

        if now > exp_dt:
            print("⚠️ Token is already expired!")
        else:
            print("✓ Token is valid")

    except jwt.ExpiredSignatureError as e:
        print(f"\n✗ Token expired: {e}")

        # Decode without verification to see the timestamps
        unverified = jwt.get_unverified_claims(token)
        iat = unverified.get("iat")
        exp = unverified.get("exp")

        iat_dt = datetime.fromtimestamp(iat)
        exp_dt = datetime.fromtimestamp(exp)

        print(f"Token was issued at: {iat_dt}")
        print(f"Token expired at: {exp_dt}")
        print(f"Current time: {datetime.utcnow()}")

    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    test_token_timing()
