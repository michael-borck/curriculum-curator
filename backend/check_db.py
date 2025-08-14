#!/usr/bin/env python3
"""
Database verification script
Checks the current state of the database
"""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models import (
    LRD,
    Course,
    CourseModule,
    Material,
    TaskList,
    User,
)


def check_db():
    """Check database contents"""
    db = SessionLocal()

    try:
        print("📊 Database Status Report")
        print("=" * 50)

        # Check users
        users = db.query(User).all()
        print(f"\n👥 Users ({len(users)} total):")
        for user in users[:5]:  # Show first 5
            print(f"  - {user.name} ({user.email}) - {user.role}")
        if len(users) > 5:
            print(f"  ... and {len(users) - 5} more")

        # Check courses
        courses = db.query(Course).all()
        print(f"\n📚 Courses ({len(courses)} total):")
        for course in courses:
            modules = db.query(CourseModule).filter_by(course_id=course.id).count()
            materials = db.query(Material).filter_by(course_id=course.id).count()
            print(f"  - {course.code}: {course.title}")
            print(
                f"    Status: {course.status}, Modules: {modules}, Materials: {materials}"
            )
            print(f"    Owner: {course.user.name}")
            print(f"    Teaching Philosophy: {course.teaching_philosophy}")

        # Check LRDs
        lrds = db.query(LRD).all()
        print(f"\n📋 LRDs ({len(lrds)} total):")
        for lrd in lrds:
            course = db.query(Course).filter_by(id=lrd.course_id).first()
            print(
                f"  - Version {lrd.version} for {course.code if course else 'Unknown'}"
            )
            print(f"    Status: {lrd.status}")

        # Check materials
        materials = db.query(Material).all()
        print(f"\n📄 Materials ({len(materials)} total):")
        # Group by type
        material_types = {}
        for material in materials:
            if material.type not in material_types:
                material_types[material.type] = 0
            material_types[material.type] += 1
        for m_type, count in material_types.items():
            print(f"  - {m_type}: {count}")

        # Check versioning
        versioned = db.query(Material).filter(Material.version > 1).count()
        if versioned > 0:
            print(f"  - Materials with multiple versions: {versioned}")

        # Check task lists
        task_lists = db.query(TaskList).all()
        print(f"\n✓ Task Lists ({len(task_lists)} total):")
        for task_list in task_lists:
            course = db.query(Course).filter_by(id=task_list.course_id).first()
            progress = task_list.progress_percentage
            print(
                f"  - {course.code if course else 'Unknown'}: {progress:.0f}% complete"
            )
            print(
                f"    Status: {task_list.status}, Tasks: {task_list.completed_tasks}/{task_list.total_tasks}"
            )

        print("\n" + "=" * 50)
        print("✅ Database check complete")

    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    check_db()
