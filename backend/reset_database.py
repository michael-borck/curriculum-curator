#!/usr/bin/env python3
"""
Reset the database - removes all data and recreates tables
"""

import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import Base
from app.models.system_config import SystemConfig


def backup_database():
    """Create a backup of the current database"""
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if Path(db_path).exists():
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    return None


def reset_database():
    """Reset the database"""
    print("\n🔄 Resetting Database...")
    print("=" * 60)

    # Ask for confirmation
    response = input(
        "\n⚠️  This will DELETE ALL DATA in the database. Continue? (yes/no): "
    )
    if response.lower() != "yes":
        print("❌ Database reset cancelled")
        return

    # Backup existing database
    backup_path = backup_database()

    # Get database URL
    db_url = settings.DATABASE_URL
    engine = create_engine(db_url)

    # Drop all tables
    print("\n📝 Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")

    # Create all tables fresh
    print("\n📝 Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created")

    # Add default system configuration only (no users)
    print("\n⚙️  Adding default system configuration...")

    with Session(engine) as db:
        # Add default system configuration
        default_config = SystemConfig(
            id=uuid.uuid4(),
            key="default_credit_points",
            value=25,  # JSON value - integer
            category="unit_defaults",
            description="Default credit points for new units",
        )
        db.add(default_config)

        default_duration = SystemConfig(
            id=uuid.uuid4(),
            key="default_duration_weeks",
            value=12,  # JSON value - integer
            category="unit_defaults",
            description="Default duration in weeks for new units",
        )
        db.add(default_duration)

        db.commit()
        print("✅ Added default configurations")
        print("ℹ️  No users created - first registered user will become admin")  # noqa: RUF001

    # Run any pending migrations
    print("\n🔄 Checking for database migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✅ Database migrations applied")
    except Exception as e:
        print(f"⚠️  Could not run migrations: {e}")
        print("   You may need to run 'alembic upgrade head' manually")

    print("\n" + "=" * 60)
    print("✅ Database reset complete!")
    print("\n📝 Notes:")
    print("  • No users created")
    print("  • First user to register will automatically become admin")
    print("  • Default credit points: 25")
    print("  • Default duration: 12 weeks")

    if backup_path:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        print(f"\n💾 Your old database is backed up at: {backup_path}")
        print(f"   To restore: cp {backup_path} {db_path}")

    print("\n🚀 You can now start fresh with a clean database!")
    print("   Register your first user to become the system administrator.")


if __name__ == "__main__":
    reset_database()
