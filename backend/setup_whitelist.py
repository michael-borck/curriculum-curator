#!/usr/bin/env python3
"""Setup email whitelist for testing"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import SessionLocal, init_db
from app.models import EmailWhitelist


def add_to_whitelist(email: str):
    """Add an email to the whitelist"""
    init_db()
    db = SessionLocal()

    try:
        # Check if already exists
        existing = (
            db.query(EmailWhitelist).filter(EmailWhitelist.pattern == email).first()
        )

        if existing:
            print(f"Email {email} is already whitelisted")
            return

        # Add to whitelist
        whitelist_entry = EmailWhitelist(
            pattern=email, description=f"Added for testing - {email}", is_active=True
        )
        db.add(whitelist_entry)
        db.commit()
        print(f"Added {email} to whitelist")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # To whitelist a specific email, use:
    #   add_to_whitelist("user@example.com")  # noqa: ERA001

    # Add domain - this will whitelist ALL @curtin.edu.au emails
    add_to_whitelist("@curtin.edu.au")
    print(
        "\nDomain @curtin.edu.au whitelisted - all emails from this domain can register!"
    )
