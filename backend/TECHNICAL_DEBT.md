# Technical Debt Tracker

This file tracks all exceptions, workarounds, and bypasses in the codebase. Each entry should be reviewed periodically and addressed when possible.

## Type Checking Exceptions (`# type: ignore`)

### Current Count: [Run `./scripts/audit_exceptions.sh` to update]

| File | Line | Context | Reason | Added |
|------|------|---------|--------|-------|
| app/core/csrf_protection.py | 30 | @csrf_protect.load_config | Decorator type inference issue | 2024-01-09 |
| app/core/database.py | ~50 | get_db() function | Type annotation for generator | 2024-01-09 |

## Linting Exceptions

### Ruff/Flake8 Ignores

| File | Pattern | Reason | Added |
|------|---------|--------|-------|
| app/api/routes/admin.py | rate limiter decorators | Commented out due to request parameter issue | 2024-01-09 |

## Test Exceptions

### Skipped Tests (`@pytest.mark.skip`)

| Test File | Test Count | Reason | Workaround |
|-----------|------------|--------|------------|
| tests/test_auth.py | 6 | OAuth2PasswordRequestForm + TestClient issue | See test_fixtures_workaround.py |
| tests/test_auth_simple.py | 1 | Form data handling | None yet |

### Mocked Dependencies

| Component | Mock Location | Reason |
|-----------|---------------|--------|
| LLM Service (langchain) | tests/conftest.py | Missing dependencies in test env | tests/test_mocks.py |
| Email Service | tests/conftest.py | Prevent sending emails in tests | Fixture mocks |
| CSRF Protection | tests/conftest.py | Simplified for testing | Mock functions |

## Security Exceptions

### Disabled Security Features

| Feature | Location | Reason | Risk Level |
|---------|----------|--------|------------|
| Rate limiting | tests/conftest.py | Disabled for tests | None (test only) |
| CSRF validation | tests/conftest.py | Mocked for tests | None (test only) |

## Import/Dependency Workarounds

| Module | Workaround | Location | Reason |
|--------|------------|----------|--------|
| langchain modules | sys.modules mocking | tests/conftest.py | Optional dependencies |

## Database Migration Exceptions

| Issue | Location | Status |
|-------|----------|--------|
| Empty models | app/models/*.py | Models defined but not implemented |
| No migrations | alembic/versions/ | No migrations created yet |

## TODO/FIXME Comments

### Run `grep -r "TODO\|FIXME\|HACK\|XXX" app/` to find all

## Configuration Workarounds

| Setting | Current Value | Proper Value | Location |
|---------|--------------|--------------|----------|
| require_user_agent | False | True (production) | app/main.py:76 |
| SECRET_KEY | Hardcoded example | Environment variable | .env.example |

## How to Update This File

1. When adding any exception/workaround, add an entry here
2. Run `./scripts/audit_exceptions.sh` monthly to update counts
3. Review in sprint planning to prioritize debt reduction
4. Remove entries when fixed

## Metrics

- Total Type Ignores: [Run audit script]
- Total Skipped Tests: 7
- Total Security Exceptions: 2 (test only)
- Risk Score: MEDIUM (due to number of skipped tests)

Last Updated: 2024-01-09