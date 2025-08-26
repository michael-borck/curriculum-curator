#!/usr/bin/env python3
"""Direct password verification test"""

from app.core.database import SessionLocal
from app.models import User
from app.core.security import verify_password, get_password_hash


def test_password():
    db = SessionLocal()

    # Get admin user
    admin = db.query(User).filter(User.email == "admin@curriculum-curator.com").first()
    if not admin:
        print("Admin user not found!")
        return

    print(f"Testing admin user: {admin.email}")
    print(
        f"Role: {admin.role}, Active: {admin.is_active}, Verified: {admin.is_verified}"
    )

    # Test password
    test_password = "Admin123!Pass"

    # Generate new hash
    new_hash = get_password_hash(test_password)
    print(f"\nNew hash generated: {new_hash[:30]}...")

    # Test with new hash
    verify_new = verify_password(test_password, new_hash)
    print(f"Verification with new hash: {verify_new}")

    # Test with existing hash
    print(f"\nExisting hash: {admin.password_hash[:30]}...")
    verify_existing = verify_password(test_password, admin.password_hash)
    print(f"Verification with existing hash: {verify_existing}")

    if not verify_existing:
        print("\nPassword doesn't match. Resetting...")
        admin.password_hash = new_hash
        db.commit()
        print("Password reset complete")

        # Verify again
        verify_after = verify_password(test_password, admin.password_hash)
        print(f"Verification after reset: {verify_after}")

    db.close()


if __name__ == "__main__":
    test_password()
