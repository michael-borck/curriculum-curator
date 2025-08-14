# Technical Debt Tracking

## Overview

This project uses automated technical debt tracking to monitor suppressed linting violations across both backend (Python) and frontend (TypeScript) code.

## Current Status

As of 2025-08-14:
- **Total Suppressions**: 8
  - Backend (Python): 7 suppressions
  - Frontend (TypeScript): 1 suppression
- **Zero type checking errors** maintained
- **Zero linting errors** (except explicitly suppressed)

## Tools

### Technical Debt Report Generator

Generate comprehensive reports of all suppressed violations:

```bash
# View report in terminal
./tech_debt.sh

# Save markdown report
./tech_debt.sh --output reports/tech-debt.md

# Generate JSON for automation
./tech_debt.sh --json --output debt.json

# Get help
./tech_debt.sh --help
```

### Quick Commands

```bash
# Find Python noqa comments
grep -rn '# noqa:' backend/ --include='*.py'

# Find TypeScript/ESLint suppressions
grep -rn '// eslint-disable' frontend/src/ --include='*.ts*'

# Show specific violation type
ruff check backend/ --select=PLR0911
```

## Suppression Guidelines

### When to Suppress

1. **Legitimate edge cases** where the rule doesn't apply
2. **Interface requirements** (e.g., unused arguments required by framework)
3. **Pattern matching** functions with many returns
4. **SQLAlchemy requirements** (e.g., `!= None` for SQL generation)

### How to Suppress

**Python (ruff):**
```python
# Suppress for entire function
def complex_function():  # noqa: PLR0911
    ...

# Suppress for single line
result = value != None  # noqa: E711  # SQLAlchemy requires this
```

**TypeScript (ESLint):**
```typescript
// Suppress next line
// eslint-disable-next-line react-hooks/exhaustive-deps
useEffect(() => { ... }, []);

// Suppress with explanation
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- External API type
```

## Current Suppressions

### Backend (7 total)
- `PLR0911` (2): Too many return statements - Pattern matching functions
- `ARG004` (2): Unused arguments - Required for interface compatibility
- `ERA001` (1): Commented code - Example usage documentation
- `PLR0912` (1): Too many branches - Complex validation logic
- `E711` (1): Identity comparison - SQLAlchemy requirement

### Frontend (1 total)
- `react-hooks/exhaustive-deps` (1): Pagination reset logic

## Best Practices

1. **Always document why** - Add a comment explaining the suppression
2. **Use specific codes** - Never use bare `# noqa` or `// eslint-disable`
3. **Limit scope** - Use line-specific suppressions, not file-wide
4. **Review regularly** - Run `./tech_debt.sh` during sprint planning
5. **Track trends** - Ensure debt count doesn't grow over time

## Migration from Old System

Previously, the project used:
- Manual `TECHNICAL_DEBT.md` file
- `# type: ignore` comments (now all resolved)
- `scripts/generate_debt_report.py` (replaced)

The new system automatically tracks all suppressions and generates reports on demand.

## Quality Gates

Before committing code:
```bash
# Backend
cd backend
ruff check .              # Must show 0 errors
basedpyright             # Must show 0 errors

# Frontend
cd frontend
npm run lint             # Must show 0 errors
npm run type-check       # Must show 0 errors

# Check technical debt
cd ..
./tech_debt.sh           # Review any new suppressions
```

## Goals

- Maintain < 10 total suppressions
- Document all suppressions with clear explanations
- Review and reduce debt quarterly
- Never suppress security-related warnings