#!/usr/bin/env python3
"""
Database initialization script for Curriculum Curator
Creates tables and loads sample data for development
"""

import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models import (
    LRD,
    Course,
    CourseModule,
    CourseStatus,
    LRDStatus,
    Material,
    MaterialType,
    ModuleType,
    TaskList,
    TaskStatus,
    TeachingPhilosophy,
    User,
    UserRole,
)


def init_db():
    """Initialize database with tables and sample data"""
    print("🚀 Initializing Curriculum Curator Database...")

    # Create all tables
    print("📊 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

    # Create a session
    db = SessionLocal()

    try:
        # Check if we already have data
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(
                f"INFO: Database already contains {existing_users} users. Skipping initialization."
            )
            return

        print("\n📝 Creating sample data...")

        # Create sample users
        print("👥 Creating users...")

        # Admin user
        admin = User(
            id=uuid.uuid4(),
            email="admin@curriculum-curator.edu.au",
            password_hash=get_password_hash("admin123"),
            name="System Administrator",
            role=UserRole.ADMIN.value,
            is_verified=True,
            is_active=True,
            institution="Curriculum Curator",
            teaching_philosophy=TeachingPhilosophy.MIXED_APPROACH.value,
            language_preference="en-AU",
        )
        db.add(admin)

        # Sample lecturer 1
        lecturer1 = User(
            id=uuid.uuid4(),
            email="sarah.chen@university.edu.au",
            password_hash=get_password_hash("password123"),
            name="Dr. Sarah Chen",
            role=UserRole.LECTURER.value,
            is_verified=True,
            is_active=True,
            institution="University of Technology",
            department="Computer Science",
            position_title="Senior Lecturer",
            teaching_philosophy=TeachingPhilosophy.FLIPPED_CLASSROOM.value,
            language_preference="en-AU",
        )
        db.add(lecturer1)

        # Sample lecturer 2
        lecturer2 = User(
            id=uuid.uuid4(),
            email="michael.roberts@college.edu.au",
            password_hash=get_password_hash("password123"),
            name="Prof. Michael Roberts",
            role=UserRole.LECTURER.value,
            is_verified=True,
            is_active=True,
            institution="Technical College",
            department="Information Technology",
            position_title="Professor",
            teaching_philosophy=TeachingPhilosophy.PROJECT_BASED.value,
            language_preference="en-GB",
        )
        db.add(lecturer2)

        db.commit()
        print("✅ Users created")

        # Create sample courses
        print("\n📚 Creating courses...")

        # Course 1: Introduction to Python (Flipped Classroom)
        course1 = Course(
            id=uuid.uuid4(),
            user_id=lecturer1.id,
            title="Introduction to Python Programming",
            code="CS101",
            description="Learn Python fundamentals through hands-on practice",
            teaching_philosophy=TeachingPhilosophy.FLIPPED_CLASSROOM.value,
            language_preference="en-AU",
            status=CourseStatus.ACTIVE.value,
            semester="2024-S1",
            credits=3,
            learning_objectives=[
                "Understand Python syntax and data types",
                "Write functions and modules",
                "Handle files and exceptions",
                "Create simple applications",
            ],
            prerequisites=["Basic computer skills"],
            assessment_structure={
                "assignments": 40,
                "midterm": 20,
                "final": 30,
                "participation": 10,
            },
        )
        db.add(course1)

        # Course 2: Web Development (Project-Based)
        course2 = Course(
            id=uuid.uuid4(),
            user_id=lecturer2.id,
            title="Modern Web Development",
            code="IT202",
            description="Build dynamic web applications with modern frameworks",
            teaching_philosophy=TeachingPhilosophy.PROJECT_BASED.value,
            language_preference="en-GB",
            status=CourseStatus.PLANNING.value,
            semester="2024-S2",
            credits=4,
            learning_objectives=[
                "Design responsive web interfaces",
                "Implement RESTful APIs",
                "Use modern JavaScript frameworks",
                "Deploy web applications",
            ],
            prerequisites=["CS101", "Basic HTML/CSS"],
        )
        db.add(course2)

        db.commit()
        print("✅ Courses created")

        # Create modules for course 1
        print("\n📖 Creating course modules...")

        module1 = CourseModule(
            id=uuid.uuid4(),
            course_id=course1.id,
            number=1,
            title="Python Basics",
            description="Introduction to Python syntax and basic concepts",
            type=ModuleType.FLIPPED.value,
            duration_minutes=120,
            pre_class_content={
                "videos": ["Introduction to Python", "Setting up environment"],
                "reading": "Chapter 1: Getting Started",
                "duration": "45 minutes",
            },
            in_class_content={
                "activities": ["Live coding session", "Pair programming exercises"],
                "duration": "90 minutes",
            },
            post_class_content={
                "exercises": "Practice problems 1-10",
                "reflection": "Learning journal entry",
            },
            is_complete=True,
            materials_count=3,
        )
        db.add(module1)

        module2 = CourseModule(
            id=uuid.uuid4(),
            course_id=course1.id,
            number=2,
            title="Control Flow and Functions",
            description="Learn about conditionals, loops, and functions",
            type=ModuleType.FLIPPED.value,
            duration_minutes=120,
            is_complete=False,
            materials_count=2,
        )
        db.add(module2)

        db.commit()
        print("✅ Modules created")

        # Create LRD for course 1
        print("\n📋 Creating LRDs...")

        lrd1 = LRD(
            id=uuid.uuid4(),
            course_id=course1.id,
            version="1.0",
            status=LRDStatus.APPROVED.value,
            content={
                "topic": "Introduction to Python Programming",
                "objectives": [
                    "Understand Python syntax",
                    "Write basic programs",
                    "Debug common errors",
                ],
                "target_audience": {
                    "level": "Beginner",
                    "prerequisites": "Basic computer skills",
                    "class_size": 30,
                },
                "structure": {
                    "pre_class": "Video lectures and reading",
                    "in_class": "Hands-on coding exercises",
                    "post_class": "Practice problems and reflection",
                },
                "assessment": {
                    "formative": "Weekly quizzes",
                    "summative": "Programming assignments",
                },
            },
            approval_history=[
                {
                    "date": datetime.utcnow().isoformat(),
                    "approver": "Dr. Sarah Chen",
                    "status": "approved",
                    "comments": "Ready for implementation",
                }
            ],
        )
        db.add(lrd1)

        db.commit()
        print("✅ LRDs created")

        # Create materials
        print("\n📄 Creating materials...")

        material1 = Material(
            id=uuid.uuid4(),
            course_id=course1.id,
            module_id=module1.id,
            type=MaterialType.LECTURE.value,
            title="Introduction to Python",
            description="First lecture introducing Python programming",
            content={
                "slides": [
                    "Welcome to Python",
                    "Why Python?",
                    "Python Philosophy",
                    "Basic Syntax",
                ],
                "duration": "45 minutes",
                "format": "presentation",
            },
            raw_content="# Introduction to Python\n\n## Welcome\n\nPython is a powerful, versatile programming language...",
            version=1,
            is_latest=True,
            teaching_philosophy=TeachingPhilosophy.FLIPPED_CLASSROOM.value,
            quality_score=85,
        )
        db.add(material1)

        material2 = Material(
            id=uuid.uuid4(),
            course_id=course1.id,
            module_id=module1.id,
            type=MaterialType.WORKSHEET.value,
            title="Python Basics Exercises",
            description="Practice exercises for Python fundamentals",
            content={
                "exercises": [
                    {"question": "Write a hello world program", "difficulty": "easy"},
                    {
                        "question": "Calculate the area of a circle",
                        "difficulty": "medium",
                    },
                    {"question": "Create a simple calculator", "difficulty": "hard"},
                ],
                "estimated_time": "60 minutes",
            },
            version=1,
            is_latest=True,
            teaching_philosophy=TeachingPhilosophy.FLIPPED_CLASSROOM.value,
        )
        db.add(material2)

        # Create a version 2 of material1
        material1_v2 = Material(
            id=uuid.uuid4(),
            course_id=course1.id,
            module_id=module1.id,
            type=MaterialType.LECTURE.value,
            title="Introduction to Python (Updated)",
            description="Updated lecture with more examples",
            content={
                "slides": [
                    "Welcome to Python",
                    "Why Python?",
                    "Python Philosophy",
                    "Basic Syntax",
                    "Real-world Examples",  # New slide
                ],
                "duration": "50 minutes",
                "format": "presentation",
            },
            version=2,
            parent_version_id=material1.id,
            is_latest=True,
            teaching_philosophy=TeachingPhilosophy.FLIPPED_CLASSROOM.value,
            quality_score=90,
        )
        material1.is_latest = False  # Mark v1 as not latest
        db.add(material1_v2)

        db.commit()
        print("✅ Materials created")

        # Create task list
        print("\n✓ Creating task lists...")

        task_list1 = TaskList(
            id=uuid.uuid4(),
            lrd_id=lrd1.id,
            course_id=course1.id,
            tasks={
                "parent_tasks": [
                    {
                        "id": "1",
                        "title": "Create pre-class materials",
                        "status": "completed",
                        "subtasks": [
                            {
                                "id": "1.1",
                                "title": "Record video lecture",
                                "completed": True,
                            },
                            {
                                "id": "1.2",
                                "title": "Prepare reading materials",
                                "completed": True,
                            },
                        ],
                    },
                    {
                        "id": "2",
                        "title": "Develop in-class activities",
                        "status": "in_progress",
                        "subtasks": [
                            {
                                "id": "2.1",
                                "title": "Create coding exercises",
                                "completed": True,
                            },
                            {
                                "id": "2.2",
                                "title": "Design group activities",
                                "completed": False,
                            },
                        ],
                    },
                    {
                        "id": "3",
                        "title": "Prepare assessments",
                        "status": "pending",
                        "subtasks": [
                            {
                                "id": "3.1",
                                "title": "Write quiz questions",
                                "completed": False,
                            },
                            {
                                "id": "3.2",
                                "title": "Design assignment",
                                "completed": False,
                            },
                        ],
                    },
                ],
            },
            status=TaskStatus.IN_PROGRESS.value,
            total_tasks=6,
            completed_tasks=3,
            progress={
                "last_updated": datetime.utcnow().isoformat(),
                "completion_percentage": 50,
            },
        )
        db.add(task_list1)

        db.commit()
        print("✅ Task lists created")

        print("\n🎉 Database initialization complete!")
        print("\n📊 Summary:")
        print(f"  - Users: {db.query(User).count()}")
        print(f"  - Courses: {db.query(Course).count()}")
        print(f"  - Modules: {db.query(CourseModule).count()}")
        print(f"  - LRDs: {db.query(LRD).count()}")
        print(f"  - Materials: {db.query(Material).count()}")
        print(f"  - Task Lists: {db.query(TaskList).count()}")

        print("\n🔑 Test Credentials:")
        print("  Admin: admin@curriculum-curator.edu.au / admin123")
        print("  Lecturer 1: sarah.chen@university.edu.au / password123")
        print("  Lecturer 2: michael.roberts@college.edu.au / password123")

    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize Curriculum Curator database"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (delete all data and recreate)",
    )
    args = parser.parse_args()

    if args.reset:
        print("⚠️  WARNING: This will delete all existing data!")
        response = input("Are you sure? Type 'yes' to continue: ")
        if response.lower() == "yes":
            print("🗑️  Dropping all tables...")
            Base.metadata.drop_all(bind=engine)
            print("✅ Tables dropped")

    init_db()
