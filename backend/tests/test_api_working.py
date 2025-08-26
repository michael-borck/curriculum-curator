"""
Simple test to verify API authentication is working
Handles rate limiting and redirect issues
"""

import base64
import json
import sys
import time

import requests
from jose import jwt as jose_jwt

# Add backend to path for settings import
sys.path.insert(
    0, "/home/michael/Downloads/curriculum-curator/generated_project/backend"
)
from app.core.config import settings


def test_authentication_flow():
    """Test that authentication works correctly with the API"""

    # Wait a bit to avoid rate limiting from previous tests
    print("Waiting to avoid rate limit...")
    time.sleep(5)

    # Step 1: Login and get token
    print("\n1. Testing login...")
    login_resp = requests.post(
        "http://localhost:8000/api/auth/login",
        data={"username": "admin@curriculum-curator.com", "password": "Admin123!Pass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if login_resp.status_code == 429:
        print("Rate limited. Waiting 60 seconds...")
        time.sleep(60)
        login_resp = requests.post(
            "http://localhost:8000/api/auth/login",
            data={
                "username": "admin@curriculum-curator.com",
                "password": "Admin123!Pass",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert login_resp.status_code == 200, (
        f"Login failed: {login_resp.status_code} - {login_resp.text}"
    )

    token_data = login_resp.json()
    token = token_data["access_token"]
    print("✓ Login successful")

    # Examine token
    claims = jose_jwt.get_unverified_claims(token)
    print(f"  Token IP: {claims.get('ip')}")
    print(f"  Token role: {claims.get('role')}")
    print(f"  Token sub: {claims.get('sub')}")

    # Step 2: Test authenticated endpoints
    headers = {"Authorization": f"Bearer {token}"}

    print("\n2. Testing authenticated endpoints...")

    # Test /api/auth/me
    me_resp = requests.get("http://localhost:8000/api/auth/me", headers=headers)
    print(f"  /api/auth/me: {me_resp.status_code}")
    if me_resp.status_code == 200:
        user = me_resp.json()
        print(f"    User: {user.get('email')}, Role: {user.get('role')}")
    else:
        print(f"    Error: {me_resp.text}")

    # Test admin endpoint (with trailing slash to avoid redirect)
    admin_resp = requests.get(
        "http://localhost:8000/api/admin/users/stats", headers=headers
    )
    print(f"  /api/admin/users/stats: {admin_resp.status_code}")
    if admin_resp.status_code == 200:
        stats = admin_resp.json()
        print(f"    Total users: {stats.get('total_users')}")
    else:
        print(f"    Error: {admin_resp.text}")

    # Test courses endpoint (with trailing slash)
    courses_resp = requests.get(
        "http://localhost:8000/api/courses/",  # Note the trailing slash
        headers=headers,
    )
    print(f"  /api/courses/: {courses_resp.status_code}")
    if courses_resp.status_code == 200:
        courses = courses_resp.json()
        print(
            f"    Number of courses: {len(courses) if isinstance(courses, list) else 'N/A'}"
        )
    else:
        print(f"    Error: {courses_resp.text[:100]}")

    # Step 3: Test creating a resource
    print("\n3. Testing resource creation...")
    course_data = {
        "title": f"API Test Course {int(time.time())}",
        "description": "Testing API authentication",
        "objectives": ["Test API"],
        "duration_weeks": 1,
    }

    create_resp = requests.post(
        "http://localhost:8000/api/courses/",  # Trailing slash
        json=course_data,
        headers=headers,
    )
    print(f"  Create course: {create_resp.status_code}")
    if create_resp.status_code == 200:
        course = create_resp.json()
        print(f"    Created course ID: {course.get('id')}")

        # Clean up
        delete_resp = requests.delete(
            f"http://localhost:8000/api/courses/{course['id']}", headers=headers
        )
        print(f"    Cleanup: {delete_resp.status_code}")
    else:
        print(f"    Error: {create_resp.text[:200]}")

    print("\n✓ API authentication test completed!")
    return True


def diagnose_jwt_issue():
    """Diagnose why JWT validation might be failing"""

    print("\nDiagnosing JWT validation...")

    # Get a fresh token
    time.sleep(5)  # Avoid rate limit
    login_resp = requests.post(
        "http://localhost:8000/api/auth/login",
        data={"username": "admin@curriculum-curator.com", "password": "Admin123!Pass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.status_code}")
        return

    token = login_resp.json()["access_token"]

    # Decode token
    # Get header and payload
    parts = token.split(".")
    if len(parts) == 3:
        # Decode header
        header_padding = "=" * (4 - len(parts[0]) % 4)
        header = json.loads(base64.urlsafe_b64decode(parts[0] + header_padding))
        print(f"  Header: {header}")

        # Decode payload
        payload_padding = "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + payload_padding))
        print(f"  Payload fields: {list(payload.keys())}")
        print(f"  IP in token: {payload.get('ip')}")
        print(f"  Role: {payload.get('role')}")

        # Try to validate with the same secret
        try:
            # Try to decode with verification
            jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            print("  ✓ Token validates with secret key")
        except Exception as e:
            print(f"  ✗ Token validation failed: {e}")

    # Test with different IP headers
    print("\n  Testing with different headers...")
    test_headers = [
        {"Authorization": f"Bearer {token}"},
        {"Authorization": f"Bearer {token}", "X-Forwarded-For": "127.0.0.1"},
        {"Authorization": f"Bearer {token}", "X-Real-IP": "127.0.0.1"},
    ]

    for i, headers in enumerate(test_headers):
        resp = requests.get("http://localhost:8000/api/auth/me", headers=headers)
        extra = f" with {list(headers.keys())}" if len(headers) > 1 else ""
        print(f"    Test {i + 1}{extra}: {resp.status_code}")


if __name__ == "__main__":
    print("=" * 60)
    print("API Authentication Test")
    print("=" * 60)

    try:
        test_authentication_flow()
        print("\n" + "=" * 60)
        diagnose_jwt_issue()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
