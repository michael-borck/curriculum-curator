#!/bin/bash
# Run tests with rate limiting disabled

echo "=================================================="
echo "Running tests with rate limiting disabled"
echo "=================================================="

# Export environment variables
export TESTING=true
export DISABLE_RATE_LIMIT=true

# Clear security logs first
uv run python -c "
from app.core.database import SessionLocal
from app.models import LoginAttempt, SecurityLog
db = SessionLocal()
db.query(LoginAttempt).delete()
db.query(SecurityLog).delete()
db.commit()
db.close()
print('✓ Cleared security records')
"

# Run tests
if [ "$1" == "coverage" ]; then
    echo "Running with coverage report..."
    uv run pytest --cov=app --cov-report=term-missing --cov-report=html "${@:2}"
elif [ "$1" == "quick" ]; then
    echo "Running quick test (first failure stops)..."
    uv run pytest -x "${@:2}"
else
    echo "Running all tests..."
    uv run pytest "$@"
fi

echo ""
echo "=================================================="
echo "Test run complete!"
echo "=================================================="