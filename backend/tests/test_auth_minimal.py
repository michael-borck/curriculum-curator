"""
Minimal test to debug auth issues
"""

from fastapi.testclient import TestClient


def test_login_form_data(client: TestClient, test_user):
    """Test login with different form data approaches"""

    # Try 1: Using data parameter (should work for form data)
    response = client.post(
        "/api/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )
    print(f"Try 1 - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Try 1 - Response: {response.json()}")

    # Try 2: Using headers and data
    response2 = client.post(
        "/api/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    print(f"\nTry 2 - Status: {response2.status_code}")
    if response2.status_code != 200:
        print(f"Try 2 - Response: {response2.json()}")

    # Try 3: Using urlencoded string
    import urllib.parse

    form_data = urllib.parse.urlencode(
        {"username": test_user.email, "password": "testpassword123"}
    )
    response3 = client.post(
        "/api/auth/login",
        content=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    print(f"\nTry 3 - Status: {response3.status_code}")
    if response3.status_code != 200:
        print(f"Try 3 - Response: {response3.json()}")

    # One of these should work
    assert any(r.status_code == 200 for r in [response, response2, response3])
