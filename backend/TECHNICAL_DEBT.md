# Technical Debt Tracker

This file tracks all exceptions, workarounds, and bypasses in the codebase. Each entry should be reviewed periodically and addressed when possible.

## Type Checking Exceptions (`# type: ignore`)

### Current Count: 13

| File | Line | Context | Reason | Added |
|------|------|---------|--------|-------|
| app/models/generation_history.py | 91-92 | token_usage assignment | Type inference issue with JSON field | 2024-01-09 |
| app/models/course_search_result.py | 60-61, 66-67 | results/summary assignment | Type inference issue with JSON field | 2024-01-09 |
| app/models/quiz_question.py | 91-92 | partial_credit assignment | Type inference issue with JSON field | 2024-01-09 |
| app/models/validation_result.py | 75-76 | suggestions assignment | Type inference issue with JSON field | 2024-01-09 |
| app/core/security_utils.py | 234 | LoginAttempt.locked_until comparison | DateTime comparison type issue | 2024-01-09 |

## Linting Exceptions

### Ruff/Flake8 Ignores

| File | Pattern | Reason | Added |
|------|---------|--------|-------|
| app/api/routes/*.py | B008 (Depends in defaults) | False positive - FastAPI's Depends pattern is correct | 2025-01-10 |
| app/core/security_utils.py | ARG004 (unused email arg) | Email param kept for future use | 2025-01-10 |

## Test Exceptions

### Current Test Strategy
- Simple integration tests against running backend
- No mocks - tests real functionality
- 10 tests, all passing

### Test Coverage
- Not measured for integration tests (they don't import app code directly)
- Integration tests cover:
  - Health checks
  - Registration flow  
  - Login flow
  - CORS headers
  - Email whitelist validation

## Security Exceptions

### Removed Security Features

| Feature | Removal Date | Reason | Alternative |
|---------|--------------|--------|-------------|
| CSRF Protection | 2025-01-10 | Unnecessary with JWT + CORS | CORS + JWT tokens |

### Disabled Security Features (Test Only)

| Feature | Location | Reason | Risk Level |
|---------|----------|--------|------------|
| Rate limiting | tests (via fixture) | Disabled for tests | None (test only) |

## Import/Dependency Workarounds

| Module | Workaround | Location | Reason |
|--------|------------|----------|--------|
| langchain modules | Optional imports with try/except | app/services/llm_service.py | Optional dependencies |

## Database Migration Exceptions

| Issue | Location | Status |
|-------|----------|--------|
| Empty models | Several model files | Models defined but relationships not fully implemented |
| No migrations | alembic/versions/ | No migrations created yet |

## TODO/FIXME Comments

### High Priority
| File | Line | TODO | Priority |
|------|------|------|----------|
| app/api/routes/admin.py | 369 | Implement actual system settings retrieval | HIGH |
| app/api/routes/admin.py | 392 | Implement actual system settings update | HIGH |

## Empty Implementations

| Component | Location | Impact |
|-----------|----------|--------|
| Plugin base classes | app/plugins/base.py | LOW - Not used yet |
| Some schema classes | app/schemas/admin.py | LOW - Placeholder classes |

## Configuration Workarounds

| Setting | Current Value | Proper Value | Location |
|---------|--------------|--------------|----------|
| EMAIL_DEV_MODE | True | False (production) | .env |
| SECRET_KEY | Example key | Strong random key | .env |

## How to Update This File

1. When adding any exception/workaround, add an entry here
2. Run `python scripts/generate_debt_report.py` to update counts
3. Review in sprint planning to prioritize debt reduction
4. Remove entries when fixed

## Metrics Summary

- Total Type Ignores: 13
- Total Tests: 10 (all passing)
- Security Features Removed: 1 (CSRF - intentionally)
- Empty Implementations: 5
- High Priority TODOs: 2
- Risk Score: LOW (clean test suite, minimal workarounds)

Last Updated: 2025-01-10