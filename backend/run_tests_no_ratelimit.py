#!/usr/bin/env python3
"""
Run tests with rate limiting disabled
"""

import os
import subprocess
import sys


def run_tests_without_rate_limit():
    """Run pytest with rate limiting effectively disabled"""

    print("=" * 60)
    print("Running tests with rate limiting disabled...")
    print("=" * 60)

    # Set environment variables to disable rate limiting
    env = os.environ.copy()
    env["TESTING"] = "true"
    env["DISABLE_RATE_LIMIT"] = "true"

    # Clear any existing login attempts from the database
    print("\nClearing login attempts and security logs...")
    clear_script = """
from app.core.database import SessionLocal
from app.models import LoginAttempt, SecurityLog
import time

db = SessionLocal()

# Clear all login attempts
db.query(LoginAttempt).delete()
db.query(SecurityLog).delete()
db.commit()
db.close()

print("✓ Cleared security records")
time.sleep(2)  # Give database time to commit
"""

    subprocess.run([sys.executable, "-c", clear_script], check=False, env=env)

    # Run pytest with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=app",
        "--cov-report=term-missing:skip-covered",
        "--cov-report=html",
        "--tb=short",
        "-v",
        "--maxfail=5",  # Stop after 5 failures
        "-x",  # Stop on first failure
    ]

    result = subprocess.run(cmd, check=False, env=env)

    print("\n" + "=" * 60)
    print("Test run complete!")
    print("Coverage report available in htmlcov/index.html")
    print("=" * 60)

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests_without_rate_limit())
