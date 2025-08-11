"""
Simple pytest configuration - no mocks, test against running backend
"""

import time

import pytest
import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the API"""
    return BASE_URL


@pytest.fixture(scope="session")
def api_url():
    """API URL for the backend"""
    return API_URL


@pytest.fixture(scope="session", autouse=True)
def ensure_backend_running():
    """Ensure backend is running before tests"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=2)
        if response.status_code != 200:
            pytest.exit("Backend is not running! Start it with ./backend.sh")
    except requests.exceptions.RequestException:
        pytest.exit("Backend is not running! Start it with ./backend.sh")


@pytest.fixture
def unique_email():
    """Generate a unique test email"""
    timestamp = int(time.time() * 1000)
    return f"test{timestamp}@example.com"
