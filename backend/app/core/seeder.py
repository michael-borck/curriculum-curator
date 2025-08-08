"""
Database seeder for initial data
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import EmailWhitelist, SystemSettings, User, UserRole


def seed_admin_user(db: Session):
    """Create initial admin user"""
    admin_email = "admin@localhost"
    admin_password = "admin123"  # Change this in production!

    # Check if admin already exists
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if existing_admin:
        print(f"⚠️  Admin user already exists: {admin_email}")
        return existing_admin

    # Create admin user
    admin_user = User(
        id=uuid.uuid4(),
        email=admin_email,
        password_hash=get_password_hash(admin_password),
        name="System Administrator",
        role=UserRole.ADMIN.value,
        is_verified=True,
        is_active=True,
    )

    try:
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"✅ Created admin user: {admin_email}")
        print(f"📝 Admin password: {admin_password} (CHANGE IN PRODUCTION!)")
        return admin_user
    except IntegrityError:
        db.rollback()
        print(f"❌ Failed to create admin user: {admin_email}")
        return None


def seed_system_settings(db: Session):
    """Create default system settings"""
    default_settings = SystemSettings.get_default_settings()
    created_count = 0

    for setting_data in default_settings:
        # Check if setting already exists
        existing = (
            db.query(SystemSettings)
            .filter(SystemSettings.key == setting_data["key"])
            .first()
        )

        if existing:
            print(f"⚠️  Setting already exists: {setting_data['key']}")
            continue

        # Create new setting
        setting = SystemSettings(
            id=uuid.uuid4(),
            key=setting_data["key"],
            value=setting_data["value"],
            description=setting_data["description"],
        )

        try:
            db.add(setting)
            created_count += 1
        except IntegrityError:
            db.rollback()
            print(f"❌ Failed to create setting: {setting_data['key']}")

    if created_count > 0:
        db.commit()
        print(f"✅ Created {created_count} system settings")
    else:
        print("⚠️  All system settings already exist")


def seed_email_whitelist(db: Session):
    """Create default email whitelist entries"""
    default_whitelist = EmailWhitelist.get_default_whitelist()
    created_count = 0

    for whitelist_data in default_whitelist:
        # Check if entry already exists
        existing = (
            db.query(EmailWhitelist)
            .filter(EmailWhitelist.pattern == whitelist_data["pattern"])
            .first()
        )

        if existing:
            print(f"⚠️  Whitelist entry already exists: {whitelist_data['pattern']}")
            continue

        # Create new whitelist entry
        try:
            entry = EmailWhitelist(
                id=uuid.uuid4(),
                pattern=whitelist_data["pattern"],
                description=whitelist_data["description"],
                is_active=whitelist_data["is_active"],
            )
            print(f"✓ Created whitelist entry: {whitelist_data['pattern']}")
        except ValueError as e:
            print(f"❌ Validation error for {whitelist_data['pattern']}: {e}")
            continue

        try:
            db.add(entry)
            created_count += 1
        except IntegrityError:
            db.rollback()
            print(f"❌ Failed to create whitelist entry: {whitelist_data['pattern']}")

    if created_count > 0:
        db.commit()
        print(f"✅ Created {created_count} email whitelist entries")
    else:
        print("⚠️  All email whitelist entries already exist")


def seed_database():
    """Run all database seeders"""
    print("🌱 Starting database seeding...")

    # Create database session
    db = SessionLocal()

    try:
        # Run seeders
        seed_admin_user(db)
        seed_system_settings(db)
        seed_email_whitelist(db)

        print("✅ Database seeding completed successfully!")

    except Exception as e:
        print(f"❌ Database seeding failed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
