# Coding Standards and Exception Guidelines

## When Adding Exceptions

### Type Ignore Comments

When you must add a `# type: ignore` comment:

```python
# BAD - No context
result = complex_function()  # type: ignore

# GOOD - Explain why
result = complex_function()  # type: ignore[attr-defined] - MyPy doesn't understand dynamic attributes from SQLAlchemy

# BETTER - Add tracking reference
result = complex_function()  # type: ignore[attr-defined] - DEBT-001: SQLAlchemy dynamic attributes
```

### Skipping Tests

When skipping tests:

```python
# BAD
@pytest.mark.skip
def test_something():
    pass

# GOOD
@pytest.mark.skip(reason="OAuth2PasswordRequestForm incompatible with TestClient - see KNOWN_ISSUES.md")
def test_something():
    pass

# BETTER - Add ticket reference
@pytest.mark.skip(reason="DEBT-002: OAuth2PasswordRequestForm issue - see KNOWN_ISSUES.md")
def test_something():
    pass
```

### TODO Comments

Use standardized format:

```python
# TODO(username, YYYY-MM-DD): Brief description
# TODO(michael, 2024-01-09): Implement proper error handling for rate limit exceptions

# FIXME(username, YYYY-MM-DD): What's broken
# FIXME(team, 2024-01-09): Email service mock doesn't match actual interface

# HACK(username, YYYY-MM-DD): Why this workaround exists
# HACK(michael, 2024-01-09): Monkeypatch sys.modules due to optional dependencies
```

### Disabling Security Features

Always document why and scope:

```python
# BAD
csrf_enabled = False

# GOOD
csrf_enabled = False  # Disabled only for test environment - DO NOT USE IN PRODUCTION

# BETTER
# SECURITY-EXCEPTION: CSRF disabled for tests only
# Risk: None (test environment isolated)
# Tracked in: TECHNICAL_DEBT.md
csrf_enabled = False
```

## Tracking References

Use these prefixes for easy searching:
- `DEBT-XXX`: Technical debt items
- `SEC-XXX`: Security exceptions
- `PERF-XXX`: Performance workarounds
- `TEST-XXX`: Test-specific issues

## Regular Audits

1. Run monthly: `./scripts/audit_exceptions.sh > reports/debt_$(date +%Y%m%d).txt`
2. Review in sprint planning
3. Create tickets for HIGH/CRITICAL items
4. Update TECHNICAL_DEBT.md when fixing issues

## Acceptance Criteria for New Code

Before merging:
1. No new type ignores without documentation
2. No skipped tests without reason and tracking
3. No disabled security features in production code
4. All TODOs must have owner and date

## Exception Budget

Suggested limits (adjust per team size):
- Type ignores: < 20 total
- Skipped tests: < 10% of total tests  
- Security exceptions: 0 in production code
- TODOs older than 3 months: 0

When limits are exceeded, next sprint must include debt reduction.