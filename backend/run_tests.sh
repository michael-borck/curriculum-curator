#!/bin/bash

# Script to run tests with various options

echo "🧪 Running Curriculum Curator Backend Tests"
echo "=========================================="

# Default to running all tests
TEST_PATH=${1:-tests}

# Check if we're running specific test categories
case "$1" in
    "unit")
        echo "Running unit tests only..."
        uv run pytest -m unit
        ;;
    "integration")
        echo "Running integration tests only..."
        uv run pytest -m integration
        ;;
    "auth")
        echo "Running authentication tests..."
        uv run pytest tests/test_auth.py -v
        ;;
    "admin")
        echo "Running admin tests..."
        uv run pytest tests/test_admin.py -v
        ;;
    "security")
        echo "Running security tests..."
        uv run pytest tests/test_security.py -v
        ;;
    "models")
        echo "Running model tests..."
        uv run pytest tests/test_models.py -v
        ;;
    "coverage")
        echo "Running tests with detailed coverage report..."
        uv run pytest --cov=app --cov-report=html --cov-report=term
        echo "Coverage report generated in htmlcov/index.html"
        ;;
    "quick")
        echo "Running quick tests (no coverage)..."
        uv run pytest -x --tb=short --disable-warnings
        ;;
    *)
        echo "Running all tests..."
        uv run pytest
        ;;
esac