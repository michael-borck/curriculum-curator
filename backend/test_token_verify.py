#!/usr/bin/env python3
"""Test JWT token verification with different options"""

import time
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from app.core.security import create_access_token

def test_verification_options():
    print("Testing JWT verification options...")
    
    # Create a token
    data = {"sub": "test-user", "email": "test@example.com"}
    token = create_access_token(
        data=data,
        expires_delta=timedelta(minutes=30),
        client_ip="127.0.0.1",
        user_role="admin"
    )
    
    print("Token created")
    
    # Try different verification options
    tests = [
        ("Standard decode", {}),
        ("No expiry check", {"verify_exp": False}),
        ("With leeway", {"leeway": 10}),
        ("No expiry + leeway", {"verify_exp": False, "leeway": 10}),
    ]
    
    for test_name, options in tests:
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM],
                options=options
            )
            print(f"✓ {test_name}: SUCCESS")
            if not options.get("verify_exp", True):
                # Check expiration manually
                exp = payload.get("exp")
                now = datetime.utcnow().timestamp()
                if exp < now:
                    print(f"  Note: Token is expired (exp: {exp}, now: {now})")
        except jwt.ExpiredSignatureError:
            print(f"✗ {test_name}: ExpiredSignatureError")
        except Exception as e:
            print(f"✗ {test_name}: {e}")
    
    # Check the raw timestamps
    print("\nRaw token data:")
    unverified = jwt.get_unverified_claims(token)
    iat = unverified.get("iat")
    exp = unverified.get("exp")
    now = datetime.utcnow().timestamp()
    
    print(f"  iat: {iat}")
    print(f"  exp: {exp}")
    print(f"  now: {now}")
    print(f"  exp - now: {exp - now:.2f} seconds")
    print(f"  Token valid for: {(exp - now) / 60:.2f} minutes")

if __name__ == "__main__":
    test_verification_options()