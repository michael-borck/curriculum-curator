#!/usr/bin/env python3
"""
Systematic API endpoint testing to identify mismatches
"""

import requests
import json
from typing import Dict, List, Tuple

# Configuration
API_URL = "http://localhost:8000"
FRONTEND_ENDPOINTS = [
    ("GET", "/api/admin/settings"),
    ("GET", "/api/admin/users"),
    ("GET", "/api/admin/users/stats"),
    ("GET", "/api/admin/whitelist"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/register"),
    ("POST", "/api/auth/request-password-reset"),
    ("POST", "/api/auth/resend-verification"),
    ("POST", "/api/auth/reset-password"),
    ("POST", "/api/auth/verify-email"),
    ("POST", "/api/auth/verify-reset-code"),
    ("GET", "/api/content/workflow/sessions"),
    ("GET", "/api/content/workflow/stages"),
    ("POST", "/api/llm/enhance"),
    ("POST", "/api/llm/generate"),
    ("GET", "/api/units"),
    ("POST", "/api/units"),
]

def get_auth_token() -> str:
    """Get authentication token"""
    response = requests.post(
        f"{API_URL}/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_endpoint(method: str, endpoint: str, token: str = None) -> Tuple[str, int, str]:
    """Test a single endpoint"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(f"{API_URL}{endpoint}", headers=headers, json={}, timeout=5)
        elif method == "PUT":
            response = requests.put(f"{API_URL}{endpoint}", headers=headers, json={}, timeout=5)
        elif method == "DELETE":
            response = requests.delete(f"{API_URL}{endpoint}", headers=headers, timeout=5)
        else:
            return endpoint, 0, "Unknown method"
        
        return endpoint, response.status_code, "OK" if response.status_code < 400 else response.text[:100]
    except requests.exceptions.ConnectionError:
        return endpoint, 0, "Connection refused - backend not running"
    except requests.exceptions.Timeout:
        return endpoint, 0, "Timeout"
    except Exception as e:
        return endpoint, 0, str(e)[:100]

def check_backend_routes() -> List[str]:
    """Get all routes from FastAPI backend"""
    try:
        response = requests.get(f"{API_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi = response.json()
            return list(openapi.get("paths", {}).keys())
    except:
        pass
    return []

def main():
    print("🔍 Systematic API Endpoint Testing\n")
    print("=" * 60)
    
    # Check if backend is running
    try:
        requests.get(f"{API_URL}/", timeout=2)
        print("✅ Backend is running\n")
    except:
        print("❌ Backend is not running! Start it with ./backend.sh\n")
        return
    
    # Get auth token
    token = get_auth_token()
    if token:
        print("✅ Authentication successful\n")
    else:
        print("⚠️  Authentication failed - will test public endpoints only\n")
    
    # Get actual backend routes
    backend_routes = check_backend_routes()
    if backend_routes:
        print(f"📋 Found {len(backend_routes)} routes in backend\n")
    
    # Test each endpoint
    print("Testing Frontend API Calls:")
    print("-" * 60)
    
    issues = []
    for method, endpoint in FRONTEND_ENDPOINTS:
        _, status, message = test_endpoint(method, endpoint, token)
        
        # Check status
        if status == 0:
            print(f"❌ {method:6} {endpoint:40} - {message}")
            issues.append((endpoint, "Connection/Backend issue"))
        elif status == 404:
            print(f"⚠️  {method:6} {endpoint:40} - Not Found (404)")
            issues.append((endpoint, "Endpoint doesn't exist"))
        elif status == 422:
            print(f"⚠️  {method:6} {endpoint:40} - Validation Error (422)")
            issues.append((endpoint, "Field mismatch or validation"))
        elif status == 500:
            print(f"❌ {method:6} {endpoint:40} - Server Error (500)")
            issues.append((endpoint, "Backend error"))
        elif status >= 400:
            print(f"⚠️  {method:6} {endpoint:40} - Error {status}")
        else:
            print(f"✅ {method:6} {endpoint:40} - OK ({status})")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"   Total endpoints tested: {len(FRONTEND_ENDPOINTS)}")
    print(f"   Issues found: {len(issues)}")
    
    if issues:
        print("\n⚠️  Issues to fix:")
        for endpoint, issue in issues:
            print(f"   - {endpoint}: {issue}")
    
    # Check for routes in backend not used by frontend
    if backend_routes:
        frontend_paths = {ep for _, ep in FRONTEND_ENDPOINTS}
        unused = set(backend_routes) - frontend_paths
        if unused:
            print(f"\n📝 Backend routes not used by frontend ({len(unused)}):")
            for route in sorted(unused)[:10]:
                print(f"   - {route}")

if __name__ == "__main__":
    main()