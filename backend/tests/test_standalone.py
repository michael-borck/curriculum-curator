"""
Standalone test to isolate the issue
"""

import sys
import os
from unittest.mock import MagicMock

# Mock langchain modules before any imports
sys.modules['langchain'] = MagicMock()
sys.modules['langchain.callbacks'] = MagicMock()
sys.modules['langchain.schema'] = MagicMock()
sys.modules['langchain_anthropic'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()

from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient


def test_standalone_form():
    """Test form data in complete isolation"""
    # Create minimal app
    app = FastAPI()
    
    @app.post("/login")
    async def login(form_data: OAuth2PasswordRequestForm = Depends()):
        return {
            "username": form_data.username,
            "status": "ok"
        }
    
    # Create client
    client = TestClient(app)
    
    # Test different ways
    print("Method 1 - data parameter:")
    response1 = client.post("/login", data={"username": "test", "password": "pass"})
    print(f"  Status: {response1.status_code}")
    print(f"  Response: {response1.json() if response1.status_code == 200 else response1.text}")
    
    print("\nMethod 2 - with content-type:")
    response2 = client.post(
        "/login",
        data={"username": "test", "password": "pass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"  Status: {response2.status_code}")
    print(f"  Response: {response2.json() if response2.status_code == 200 else response2.text}")
    
    print("\nMethod 3 - content as string:")
    response3 = client.post(
        "/login",
        content="username=test&password=pass",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"  Status: {response3.status_code}")
    print(f"  Response: {response3.json() if response3.status_code == 200 else response3.text}")
    
    # At least one should work
    assert any(r.status_code == 200 for r in [response1, response2, response3])


def test_our_app_form():
    """Test our app's form handling"""
    # Import our app
    from app.main import app
    
    client = TestClient(app)
    
    # Test our debug endpoint
    print("\nTesting our app's /test-form endpoint:")
    response = client.post(
        "/test-form",
        data={"username": "test@example.com", "password": "testpass"}
    )
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json() if response.status_code == 200 else response.text}")
    
    # Test with explicit encoding
    print("\nWith explicit form encoding:")
    response2 = client.post(
        "/test-form",
        content="username=test@example.com&password=testpass",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"  Status: {response2.status_code}")
    print(f"  Response: {response2.json() if response2.status_code == 200 else response2.text}")


if __name__ == "__main__":
    test_standalone_form()
    print("\n" + "="*50 + "\n")
    test_our_app_form()