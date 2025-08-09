"""
Debug form data handling
"""

from fastapi.testclient import TestClient


def test_debug_form_endpoint(client: TestClient):
    """Test the debug form endpoint"""
    response = client.post(
        "/test-form",
        data={"username": "test@example.com", "password": "testpass"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json()["username"] == "test@example.com"