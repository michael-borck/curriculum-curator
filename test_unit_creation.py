#!/usr/bin/env python3
"""
Test script to verify unit creation functionality
"""

import requests
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def get_auth_token():
    """Login and get authentication token"""
    response = requests.post(
        f"{API_URL}/api/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        print(response.json())
        return None

def create_test_unit(token):
    """Create a test unit"""
    headers = {"Authorization": f"Bearer {token}"}
    
    unit_data = {
        "title": f"Test Unit {datetime.now().strftime('%H%M%S')}",
        "code": f"TEST{datetime.now().strftime('%H%M%S')}",
        "description": "Test unit created via API",
        "year": 2025,
        "semester": "semester_1",
        "pedagogy_type": "inquiry-based",
        "difficulty_level": "intermediate",
        "duration_weeks": 12,
        "credit_points": 25,
        "prerequisites": "",
        "learning_hours": 150,
        "status": "draft"
    }
    
    print(f"Creating unit with data: {json.dumps(unit_data, indent=2)}")
    
    response = requests.post(
        f"{API_URL}/api/units",
        json=unit_data,
        headers=headers
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        print("✅ Unit created successfully!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    else:
        print("❌ Failed to create unit")
        print(f"Error: {response.text}")
        return None

def list_units(token):
    """List all units for the user"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_URL}/api/units",
        headers=headers
    )
    
    if response.status_code == 200:
        units = response.json()
        print(f"\n📚 Found {len(units)} unit(s):")
        for unit in units:
            print(f"  - {unit['code']}: {unit['title']} (status: {unit['status']})")
        return units
    else:
        print(f"Failed to list units: {response.status_code}")
        return []

def main():
    print("🔧 Testing Unit Creation Functionality\n")
    
    # Get auth token
    print("1. Logging in...")
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    print("✅ Login successful\n")
    
    # Create a test unit
    print("2. Creating test unit...")
    unit = create_test_unit(token)
    
    if unit:
        print(f"\n✅ Unit created with ID: {unit['id']}")
        
        # List all units to verify
        print("\n3. Verifying unit creation...")
        list_units(token)
        
        print("\n✅ Unit creation test completed successfully!")
    else:
        print("\n❌ Unit creation test failed!")

if __name__ == "__main__":
    main()