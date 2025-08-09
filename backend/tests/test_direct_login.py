"""
Test login directly to isolate issue
"""

from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient


# Create a minimal app to test OAuth2PasswordRequestForm
app = FastAPI()


@app.post("/test-login")
async def test_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Test OAuth2 form handling"""
    return {
        "username": form_data.username,
        "password": form_data.password,
        "status": "received"
    }


def test_oauth2_form():
    """Test OAuth2PasswordRequestForm directly"""
    client = TestClient(app)
    
    # Method 1: Using data parameter
    response = client.post(
        "/test-login",
        data={"username": "test@example.com", "password": "testpass"}
    )
    print(f"Method 1 - Status: {response.status_code}")
    print(f"Method 1 - Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json()["username"] == "test@example.com"