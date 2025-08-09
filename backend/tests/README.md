# Backend Test Suite

This directory contains the test suite for the Curriculum Curator backend API.

## Test Structure

```
tests/
├── conftest.py          # Pytest fixtures and configuration
├── test_auth.py         # Authentication endpoint tests
├── test_admin.py        # Admin endpoint tests
├── test_security.py     # Security utilities tests
├── test_models.py       # Database model tests
├── api/                 # Additional API tests (future)
├── core/                # Core functionality tests (future)
├── models/              # Extended model tests (future)
└── services/            # Service layer tests (future)
```

## Running Tests

### Run all tests with coverage:
```bash
./run_tests.sh
# or
uv run pytest
```

### Run specific test categories:
```bash
./run_tests.sh auth      # Authentication tests only
./run_tests.sh admin     # Admin tests only
./run_tests.sh security  # Security tests only
./run_tests.sh models    # Model tests only
./run_tests.sh coverage  # Detailed coverage report
./run_tests.sh quick     # Quick run without coverage
```

### Run specific test file:
```bash
uv run pytest tests/test_auth.py -v
```

### Run specific test class or method:
```bash
uv run pytest tests/test_auth.py::TestRegistration -v
uv run pytest tests/test_auth.py::TestRegistration::test_register_new_user_success -v
```

## Test Coverage

The test suite aims for at least 70% code coverage. Current coverage includes:

- ✅ **Authentication**: Registration, login, email verification, password reset
- ✅ **Admin APIs**: User management, email whitelist, system settings
- ✅ **Security**: Password validation, JWT tokens, rate limiting, account lockout
- ✅ **Models**: User, EmailWhitelist, SecurityLog, LoginAttempt

## Test Fixtures

Key fixtures available in `conftest.py`:

- `db`: Fresh database session for each test
- `client`: FastAPI test client
- `test_user`: Regular verified user
- `test_admin`: Admin user
- `unverified_user`: Unverified user
- `email_whitelist`: Email whitelist patterns
- `auth_headers`: Authentication headers for regular user
- `admin_auth_headers`: Authentication headers for admin

## Mocking

The test suite automatically mocks:
- Email sending (prevents actual emails during tests)
- CSRF protection (disabled for easier testing)

## Writing New Tests

1. Create test file following naming convention: `test_*.py`
2. Import required fixtures from conftest
3. Group related tests in classes
4. Use descriptive test names
5. Follow AAA pattern: Arrange, Act, Assert

Example:
```python
def test_feature_description(self, client: TestClient, test_user: User):
    """Test that feature works correctly"""
    # Arrange
    data = {"key": "value"}
    
    # Act
    response = client.post("/api/endpoint", json=data)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["success"] is True
```

## Environment

Tests use an in-memory SQLite database that is created fresh for each test function, ensuring test isolation.

## CI/CD Integration

The test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    cd backend
    uv run pytest --cov=app --cov-fail-under=70
```