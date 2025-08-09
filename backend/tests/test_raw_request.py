"""
Test raw request handling
"""

import httpx
from fastapi.testclient import TestClient


def test_raw_form_request(client: TestClient):
    """Test with raw httpx request"""
    # Using httpx directly to ensure form data is sent correctly
    with httpx.Client(base_url="http://testserver", app=client.app) as http_client:
        response = http_client.post(
            "/test-form", data={"username": "test@example.com", "password": "testpass"}
        )
        print(f"Raw request status: {response.status_code}")
        print(f"Raw request headers: {dict(response.request.headers)}")
        print(f"Raw request content: {response.request.content}")
        print(f"Response: {response.json()}")


def test_inspect_middleware(client: TestClient):
    """Inspect what middleware might be interfering"""
    # Print app middleware
    print("\nApp middleware stack:")
    for middleware in client.app.middleware_stack:
        print(f"  - {middleware}")

    # Try a simple GET request first
    response = client.get("/")
    print(f"\nGET / status: {response.status_code}")

    # Try the test-form endpoint
    response = client.post(
        "/test-form", data={"username": "test@example.com", "password": "testpass"}
    )
    print(f"\nPOST /test-form status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.json()}")
