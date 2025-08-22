#!/usr/bin/env python3
"""
Reset the database - removes all data and recreates tables
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.unit import Unit
from app.models.system_config import SystemConfig  
from app.models.email_whitelist import EmailWhitelist
# Import all models to ensure tables are created
import app.models
import uuid

def backup_database():
    """Create a backup of the current database"""
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    return None

def reset_database():
    """Reset the database"""
    print("\n🔄 Resetting Database...")
    print("=" * 60)
    
    # Ask for confirmation
    response = input("\n⚠️  This will DELETE ALL DATA in the database. Continue? (yes/no): ")
    if response.lower() != 'yes':
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
    
    # Create default admin user
    print("\n👤 Creating default admin user...")
    from sqlalchemy.orm import Session
    
    with Session(engine) as db:
        # Create admin user
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@example.com",
            name="System Administrator",
            password_hash=get_password_hash("admin123"),
            is_active=True,
            is_verified=True,
            role="admin"
        )
        db.add(admin_user)
        
        # Create test lecturer user
        lecturer_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            name="Test Lecturer",
            password_hash=get_password_hash("testpassword123"),
            is_active=True,
            is_verified=True,
            role="lecturer"
        )
        db.add(lecturer_user)
        
        # Add default system configuration
        default_config = SystemConfig(
            id=uuid.uuid4(),
            key="default_credit_points",
            value=25,  # JSON value - integer
            category="unit_defaults",
            description="Default credit points for new units"
        )
        db.add(default_config)
        
        default_duration = SystemConfig(
            id=uuid.uuid4(),
            key="default_duration_weeks",
            value=12,  # JSON value - integer
            category="unit_defaults", 
            description="Default duration in weeks for new units"
        )
        db.add(default_duration)
        
        db.commit()
        print(f"✅ Created admin user: admin@example.com (password: admin123)")
        print(f"✅ Created test user: test@example.com (password: testpassword123)")
        print(f"✅ Added default configurations")
    
    # Run any pending migrations
    print("\n🔄 Checking for database migrations...")
    try:
        from alembic import command
        from alembic.config import Config
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✅ Database migrations applied")
    except Exception as e:
        print(f"⚠️  Could not run migrations: {e}")
        print("   You may need to run 'alembic upgrade head' manually")
    
    print("\n" + "=" * 60)
    print("✅ Database reset complete!")
    print("\nDefault users created:")
    print("  Admin: admin@example.com / admin123")
    print("  Test:  test@example.com / testpassword123")
    
    if backup_path:
        print(f"\n💾 Your old database is backed up at: {backup_path}")
        print("   To restore: cp {backup_path} {db_path}")
    
    print("\n🚀 You can now start fresh with a clean database!")

if __name__ == "__main__":
    reset_database()