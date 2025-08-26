#!/usr/bin/env python3
"""
Script to add composite unique constraint to units table
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings


def add_unit_constraint():
    """Add composite unique constraint for code+year+semester+owner_id"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        try:
            # First, check if constraint already exists
            result = conn.execute(
                text("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='_unit_code_year_semester_owner_uc'
            """)
            )

            if result.fetchone():
                print("✅ Constraint already exists")
                return

            # Create unique index (SQLite doesn't support ALTER TABLE ADD CONSTRAINT)
            conn.execute(
                text("""
                CREATE UNIQUE INDEX IF NOT EXISTS _unit_code_year_semester_owner_uc
                ON units(code, year, semester, owner_id)
            """)
            )
            conn.commit()
            print("✅ Added composite unique constraint to units table")

        except IntegrityError as e:
            print(f"⚠️  Warning: Some existing units may violate the constraint: {e}")
            print("   You may need to resolve duplicate units first")
        except Exception as e:
            print(f"❌ Error adding constraint: {e}")


if __name__ == "__main__":
    add_unit_constraint()
