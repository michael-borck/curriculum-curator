#!/usr/bin/env python3
"""
Migration script to remove Course model and use Unit consistently
"""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.core.database import SessionLocal

def migrate_database():
    """Clean up database to use Unit model consistently"""
    db = SessionLocal()
    
    try:
        print("Starting migration from Course to Unit model...")
        
        # Check if we have any data in courses table
        result = db.execute(text("SELECT COUNT(*) FROM courses"))
        course_count = result.scalar()
        print(f"Found {course_count} courses in database")
        
        if course_count > 0:
            print("ERROR: Courses table has data. Please handle migration manually.")
            return False
            
        # Drop foreign key constraints and tables that reference courses
        print("Dropping Course-related foreign keys and tables...")
        
        # Tables that reference courses
        tables_to_update = [
            "lrds",
            "materials", 
            "course_modules",
            "conversations",
            "task_lists"
        ]
        
        for table in tables_to_update:
            try:
                # Check if table exists
                result = db.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"))
                if result.scalar():
                    print(f"  Dropping table {table}...")
                    db.execute(text(f"DROP TABLE IF EXISTS {table}"))
            except Exception as e:
                print(f"  Warning: Could not drop {table}: {e}")
        
        # Drop courses table
        print("Dropping courses table...")
        db.execute(text("DROP TABLE IF EXISTS courses"))
        
        # Drop course_search_results if it exists
        db.execute(text("DROP TABLE IF EXISTS course_search_results"))
        
        db.commit()
        print("Migration completed successfully!")
        print("\nNext steps:")
        print("1. Remove app/models/course.py file")
        print("2. Remove app/models/course_search_result.py file") 
        print("3. Update all imports from 'Course' to 'Unit'")
        print("4. Run alembic to create new migrations for Unit-based models")
        
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if migrate_database():
        sys.exit(0)
    else:
        sys.exit(1)