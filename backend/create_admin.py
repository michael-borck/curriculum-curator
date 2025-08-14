#!/usr/bin/env python3
"""Create an admin user for testing"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uuid

from app.core import security
from app.core.database import SessionLocal, init_db
from app.models import User, UserRole


def create_admin(email: str, password: str, name: str):
    """Create an admin user"""
    init_db()
    db = SessionLocal()

    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            # Update to admin
            existing.role = UserRole.ADMIN.value
            existing.is_verified = True
            existing.is_active = True
            db.commit()
            print(f"User {email} updated to admin!")
            return

        # Create admin user
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=name,
            password_hash=security.get_password_hash(password),
            is_active=True,
            is_verified=True,  # Pre-verified for admin
            role=UserRole.ADMIN.value,
        )

        db.add(user)
        db.commit()
        print(f"Admin user {email} created successfully!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin("admin@curriculum-curator.com", "Admin123!Pass", "Admin User")
    # Also update Michael's account
    create_admin("michael.borck@curtin.edu.au", "Test123!Pass", "Michael Borck")
