"""
Script to add research source and citation tables to the database.
Run this after dropping the database to create the new tables.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, engine


def create_research_tables():
    """Create research source and citation tables."""
    print("Creating research source and citation tables...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("Research source and citation tables created successfully!")
    print("")
    print("Tables created:")
    print("  - research_sources")
    print("  - content_citations")
    print("")
    print("Relationships added:")
    print("  - User.research_sources")
    print("  - Unit.research_sources")
    print("  - Content.citations")


if __name__ == "__main__":
    create_research_tables()
